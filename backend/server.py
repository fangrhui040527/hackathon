"""
server.py
FastAPI backend for the HealthScan Multi-Agent Food Analyzer.
Uses Azure AI Foundry SDK (azure-ai-projects) with agent_reference pattern.

Endpoints:
  POST /api/analyze  — accepts image + healthNote, streams SSE events as pipeline progresses
  GET  /api/health   — health check

SSE event format:
  { "stage": "upload|extract|grounding|agent_done|conclude|done", "label": "...", "data": {...} }
"""

import asyncio
import json
import os
import traceback

from dotenv import load_dotenv
load_dotenv()

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

from pydantic import BaseModel
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from content_understanding import analyze_food_image, is_service_configured

# ── Azure AI Foundry client (singleton) ─────────────────────────────────
FOUNDRY_ENDPOINT = os.environ["AZURE_AI_FOUNDRY_ENDPOINT"]  # e.g. https://hackathon-srkk-resource.services.ai.azure.com/api/projects/hackathon
_credential = DefaultAzureCredential()
_project_client = AIProjectClient(endpoint=FOUNDRY_ENDPOINT, credential=_credential)
_openai_client = _project_client.get_openai_client()

app = FastAPI(title="HealthScan API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Foundry agent definitions ───────────────────────────────────────────
AGENTS = [
    {"name": "doctor-agent",              "version": "16", "label": "Dr. Chen",    "display": "🧑‍⚕️ Dr. Chen is reviewing..."},
    {"name": "nutritionist-agent",        "version": "7",  "label": "Dr. Patel",   "display": "🥗 Dr. Patel is analyzing..."},
    {"name": "foodchemist-agent",         "version": "8",  "label": "Dr. Kim",     "display": "🧪 Dr. Kim checking chemicals..."},
    {"name": "fitnessCoach-agent",        "version": "7",  "label": "Marcus",      "display": "🏋️ Marcus assessing fitness..."},
    {"name": "healthSpecialist-agent",    "version": "6",  "label": "Dr. Amara",   "display": "🏥 Dr. Amara reviewing risks..."},
    {"name": "cultural-religious-compliance-agent", "version": "7", "label": "Dr. Nixon", "display": "🕌 Dr. Nixon checking compliance..."},
]
CONCLUSION_AGENT = {"name": "conclusionAdvisor-agent", "version": "7"}


def _extract_product_name(food_data: dict) -> str:
    """Extract product name from CU food data."""
    fd_lower = {k.lower(): v for k, v in food_data.items()} if isinstance(food_data, dict) else {}
    product_name = (
        fd_lower.get("product_name")
        or fd_lower.get("name")
        or fd_lower.get("food_name")
        or fd_lower.get("title")
        or None
    )
    brand = fd_lower.get("brand") or fd_lower.get("manufacturer") or None
    if brand:
        brand = str(brand).strip()
    if brand and product_name:
        if brand.lower() not in str(product_name).lower():
            product_name = f"{brand} {product_name}"
    elif brand and not product_name:
        product_name = brand
    # Fallback: CU nested "contents[0].fields" structure
    if not product_name:
        contents = food_data.get("contents", [])
        if isinstance(contents, list) and contents:
            fields = contents[0].get("fields", {}) if isinstance(contents[0], dict) else {}
            for k in ("product_name", "name", "food_name", "title"):
                f = fields.get(k, {})
                if isinstance(f, dict):
                    product_name = f.get("valueString") or f.get("value")
                elif isinstance(f, str) and f:
                    product_name = f
                if product_name:
                    break
    return product_name or "Unknown Product"


def _parse_nutrition(food_data: dict) -> list[dict]:
    """Extract nutrition pills from CU food data."""
    fd_lower = {k.lower(): v for k, v in food_data.items()} if isinstance(food_data, dict) else {}
    nutr = fd_lower.get("nutrition") or fd_lower.get("nutrition_facts") or fd_lower.get("nutrients") or {}
    if isinstance(nutr, str):
        # Basic "key: value" parsing for CU string output
        import re
        parsed = {}
        for m in re.finditer(r'([\w\s.]+)\s*[:=]\s*([\d.,]+\s*\w*)', nutr):
            parsed[m.group(1).strip().lower().replace(" ", "_")] = m.group(2).strip()
        nutr = parsed
    pills = []
    if isinstance(nutr, dict):
        nutrient_map = [
            ("Calories", ["calories", "energy_kcal", "energy"]),
            ("Sugar", ["sugars", "sugar", "total_sugar"]),
            ("Fat", ["fat", "total_fat"]),
            ("Sat. Fat", ["saturated_fat", "sat_fat"]),
            ("Sodium", ["sodium", "salt"]),
            ("Carbs", ["carbohydrates", "carbs", "total_carbohydrate"]),
            ("Protein", ["protein"]),
            ("Fibre", ["fiber", "dietary_fiber", "fibre"]),
        ]
        for label, keys in nutrient_map:
            for k in keys:
                val = nutr.get(k)
                if val is not None:
                    pills.append({"label": label, "value": str(val)})
                    break
    return pills


def _build_result_from_responses(
    food_data: dict,
    agent_responses: list,
    summary_text: str,
    has_health_note: bool = False,
) -> dict:
    """Build the frontend-compatible result object from agent outputs."""
    product_name = _extract_product_name(food_data)
    nutrition_pills = _parse_nutrition(food_data)

    # Try to parse the conclusion agent's structured JSON response
    conclusion_json = None
    if summary_text:
        try:
            cleaned = summary_text.strip()
            # Strip markdown fences if present
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()
            conclusion_json = json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            conclusion_json = None

    # Use conclusion agent's product name if available
    if conclusion_json and conclusion_json.get("product_name"):
        product_name = conclusion_json["product_name"]

    # Build agent outputs
    agent_outputs = []
    for i, resp in enumerate(agent_responses):
        text = resp.text if resp and resp.text else ""
        verdict = "caution"
        text_lower = text.lower()
        if "avoid" in text_lower[:200] or "not recommended" in text_lower[:200]:
            verdict = "avoid"
        elif "safe" in text_lower[:200] or "generally safe" in text_lower[:200]:
            verdict = "safe"

        flags = []
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("- **") or line.startswith("\u2022 **"):
                flag = line.lstrip("-\u2022").strip().strip("*").split("**")[0].strip("* ")
                if len(flag) < 60:
                    flags.append(flag)
            if len(flags) >= 4:
                break

        agent_outputs.append({
            "agentId": i + 1,
            "verdict": verdict,
            "summary": text[:500] if text else "No analysis available.",
            "flags": flags or ["Analysis complete"],
            "confidence": 80 + (i * 2),
            "considered_health_note": has_health_note,
        })

    # Extract compliance data from conclusion JSON if available
    compliance_data = None
    if conclusion_json:
        eb = conclusion_json.get("expert_breakdown", {})
        if isinstance(eb, dict):
            compliance_data = eb.get("compliance")

    # Overall verdict — prefer conclusion agent's verdict_color
    if conclusion_json and conclusion_json.get("verdict_color"):
        color = conclusion_json["verdict_color"].lower()
        overall_verdict = {"red": "avoid", "green": "safe"}.get(color, "caution")
    else:
        verdicts = [a["verdict"] for a in agent_outputs]
        if verdicts.count("avoid") >= 3:
            overall_verdict = "avoid"
        elif verdicts.count("safe") >= 3:
            overall_verdict = "safe"
        else:
            overall_verdict = "caution"

    # Compliance override: Haram or Non-Vegan flags force AVOID
    if compliance_data and isinstance(compliance_data, dict):
        halal = (compliance_data.get("halal_status") or "").lower()
        vegan = (compliance_data.get("vegan_status") or "").lower()
        if halal in ("haram", "non-halal") or vegan in ("non-vegan", "not vegan"):
            overall_verdict = "avoid"

    # Use conclusion agent's structured fields when available
    if conclusion_json:
        conclusion_summary = conclusion_json.get("verdict_summary") or conclusion_json.get("bottom_line") or summary_text[:600]
        critical_alerts = conclusion_json.get("critical_alerts", [])
        avoid_if = critical_alerts if critical_alerts else []
    else:
        conclusion_summary = summary_text[:600] if summary_text else "Analysis complete."
        avoid_if = []

    ok_for = ["Healthy adults in moderation", "Occasional treat"]
    if not avoid_if:
        if overall_verdict == "avoid":
            avoid_if = ["Diabetes or insulin resistance", "High blood pressure", "Weight loss goals"]
        elif overall_verdict == "caution":
            avoid_if = ["Those with sensitive health conditions"]

    result = {
        "product": product_name,
        "type": "Food Product",
        "servingSize": food_data.get("serving_size", ""),
        "nutrition": nutrition_pills,
        "funFacts": [],
        "conclusion": {
            "verdict": overall_verdict,
            "summary": conclusion_summary,
            "ok_for": ok_for,
            "avoid_if": avoid_if,
            "flags": critical_alerts[:4] if conclusion_json and critical_alerts else ["Analysis complete"],
            "confidence": 82,
        },
        "agentOutputs": agent_outputs,
    }

    # Attach compliance breakdown when available
    if compliance_data and isinstance(compliance_data, dict):
        result["compliance"] = {
            "halal_status": compliance_data.get("halal_status", "Unknown"),
            "vegan_status": compliance_data.get("vegan_status", "Unknown"),
            "flagged_ingredients": compliance_data.get("flagged_ingredients", []),
            "notes": compliance_data.get("notes", ""),
        }

    return result


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "HealthScan API (Foundry SDK)"}


# ── Foundry SDK helpers ─────────────────────────────────────────────────

def _build_task_prompt(food_data: dict, health_note: str = "") -> str:
    """Build the analysis prompt for agents with food data and user health context."""
    food_json = json.dumps(food_data, indent=2, ensure_ascii=False)
    prompt = (
        "Analyze the following food item. Use your available tools to look up "
        "relevant nutrition data, safety information, and health advisories. "
        "Provide your specialized perspective based on your domain expertise.\n\n"
        f"Food Data (extracted from photo):\n```json\n{food_json}\n```"
    )
    if health_note:
        prompt += f"\n\nUser Health Note: {health_note}"
    return prompt


def _call_foundry_agent(agent_def: dict, prompt: str) -> dict:
    """
    Call a Foundry agent via openai_client.responses.create with MCP tool approval loop.
    Agents may request MCP tool access (e.g. knowledge base retrieval) which requires
    explicit approval before they can produce their analysis text.
    Designed to be wrapped with asyncio.to_thread for parallel execution.
    Returns a result dict; on failure returns an error marker so other agents aren't affected.
    """
    agent_ref = {
        "agent_reference": {
            "name": agent_def["name"],
            "version": agent_def["version"],
            "type": "agent_reference",
        }
    }
    try:
        response = _openai_client.responses.create(
            input=[{"role": "user", "content": prompt}],
            extra_body=agent_ref,
        )

        # MCP tool approval loop — agents with knowledge bases need approval
        # before they can query their tools and produce analysis text.
        for iteration in range(5):
            if response.output_text:
                break  # Agent produced text, we're done

            approvals = [
                item for item in (response.output or [])
                if item.type == "mcp_approval_request"
            ]
            if not approvals:
                break  # No pending approvals and no text — agent is done

            print(f"[Agent MCP] {agent_def['name']}: approving {len(approvals)} tool request(s) (iteration {iteration+1})")
            approval_inputs = [
                {
                    "type": "mcp_approval_response",
                    "approval_request_id": item.id,
                    "approve": True,
                }
                for item in approvals
            ]
            response = _openai_client.responses.create(
                input=approval_inputs,
                extra_body=agent_ref,
                previous_response_id=response.id,
            )

        out = response.output_text
        print(f"[Agent OK] {agent_def['name']}: output_text length={len(out) if out else 0}, first 200 chars={repr((out or '')[:200])}")
        return {
            "agent_name": agent_def["name"],
            "label": agent_def.get("label", agent_def["name"]),
            "text": out,
        }
    except Exception as e:
        print(f"[Agent Error] {agent_def['name']}: {type(e).__name__}: {e}")
        return {
            "agent_name": agent_def["name"],
            "label": agent_def.get("label", agent_def["name"]),
            "text": "",
            "error": str(e),
        }


@app.post("/api/analyze")
async def analyze(
    image: UploadFile = File(...),
    healthNote: str = Form(""),
):
    """
    Analyze a food image through the full pipeline, streaming SSE events.

    Flow: upload → extract (CU) → 6 agents (parallel) → conclusion → done
    """
    async def event_generator():
        try:
            # ── Stage: Upload ────────────────────────────────────
            yield {"event": "stage", "data": json.dumps({"stage": "upload", "label": "Photo received"})}

            image_bytes = await image.read()
            mime_type = image.content_type or "image/jpeg"

            # ── Stage: Extract ───────────────────────────────────
            yield {"event": "stage", "data": json.dumps({"stage": "extract", "label": "Reading the label..."})}

            food_data = None
            if is_service_configured():
                try:
                    food_data = analyze_food_image(image_bytes, mime_type)
                    print(f"[Analyze] CU returned keys: {list(food_data.keys()) if isinstance(food_data, dict) else type(food_data)}")
                except Exception as e:
                    yield {"event": "stage", "data": json.dumps({"stage": "extract", "label": f"CU error: {str(e)[:100]}"})}

            if not food_data:
                food_data = {
                    "product_name": "Unknown Product",
                    "note": "Content Understanding not available — using basic analysis",
                }

            # ── Stage: Agents (parallel via Foundry SDK) ─────────
            task_prompt = _build_task_prompt(food_data, healthNote)

            # Signal that agents are starting
            for agent_def in AGENTS:
                yield {"event": "stage", "data": json.dumps({"stage": "agents", "label": agent_def["display"]})}

            # Fire all 6 agents in parallel using asyncio.to_thread
            agent_futures = [
                asyncio.to_thread(_call_foundry_agent, agent_def, task_prompt)
                for agent_def in AGENTS
            ]

            agent_results: list[dict] = []
            for coro in asyncio.as_completed(agent_futures):
                result = await coro
                agent_results.append(result)
                # Stream each agent completion as soon as it finishes
                yield {
                    "event": "stage",
                    "data": json.dumps({
                        "stage": "agent_done",
                        "agent": result["agent_name"],
                        "label": f"{result['label']} done",
                    }),
                }

            # Re-order results to match AGENTS list order
            agent_order = {a["name"]: i for i, a in enumerate(AGENTS)}
            agent_results.sort(key=lambda r: agent_order.get(r["agent_name"], 99))

            # ── Stage: Conclusion ────────────────────────────────
            yield {"event": "stage", "data": json.dumps({"stage": "conclude", "label": "Summarizing findings..."})}

            # Build structured prompt with original OCR text + individual expert reports
            ocr_text = json.dumps(food_data, indent=2, ensure_ascii=False)

            # Map agent names to roles for the conclusion prompt
            role_map = {
                "doctor-agent": "Doctor",
                "nutritionist-agent": "Nutritionist",
                "foodchemist-agent": "Chemist",
                "fitnessCoach-agent": "Fitness",
                "healthSpecialist-agent": "Health Specialist",
                "cultural-religious-compliance-agent": "Compliance Specialist",
            }
            expert_sections = []
            for r in agent_results:
                role = role_map.get(r["agent_name"], r["label"])
                text = r["text"] if r["text"] else "No analysis provided."
                expert_sections.append(f"{role}: {text}")

            conclusion_prompt = (
                f"ORIGINAL SCANNED LABEL TEXT:\n{ocr_text}\n\n"
                f"EXPERT REPORTS:\n" + "\n\n".join(expert_sections) + "\n\n"
                "COMPLIANCE REPORT:\n"
                "The Compliance Specialist above has analyzed this product for "
                "religious (Halal/Haram/Kosher) and ethical (Vegan/Vegetarian) compliance. "
                "Include their findings in the expert_breakdown under the 'compliance' key.\n\n"
                "STRICT HIERARCHICAL PRIORITY FOR FINAL VERDICT:\n"
                "1. Doctor (Medical Safety) — any medical red flag → RED (AVOID).\n"
                "2. Compliance (Religious/Ethical) — if the Compliance Specialist flags a "
                "'Haram' or 'Non-Vegan' ingredient for a user with those dietary preferences, "
                "the verdict MUST be RED (AVOID) regardless of nutritional score.\n"
                "3. Nutrition/Chemistry (Quality) — factor only after 1 & 2 are clear.\n\n"
                "Include a 'compliance' key in expert_breakdown with fields: "
                "halal_status, vegan_status, flagged_ingredients (list), and notes.\n\n"
                "Please synthesize this into the final JSON verdict."
            )

            conclusion_result = await asyncio.to_thread(
                _call_foundry_agent, CONCLUSION_AGENT, conclusion_prompt
            )
            summary_text = conclusion_result["text"]

            # ── Build agent response wrappers for _build_result ──
            class _Resp:
                def __init__(self, text):
                    self.text = text

            agent_responses = [_Resp(r["text"]) for r in agent_results]

            # ── Stage: Done ──────────────────────────────────────
            result = _build_result_from_responses(food_data, agent_responses, summary_text, has_health_note=bool(healthNote))

            yield {"event": "stage", "data": json.dumps({"stage": "done", "label": "Done!", "data": result})}

        except Exception as e:
            traceback.print_exc()
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())


# ── Follow-up chat ("Cheat Sheet" + "Two Hats" pattern) ────────────────
#
# "Cheat Sheet":  We pass the full Result JSON so the agent has complete
#                  context without re-running the 6-agent pipeline.
# "Two Hats":     We dynamically swap the ConclusionAdvisor's behaviour
#                  from its default JSON-output mode to a warm, conversational
#                  "Chat Hat" via the system prompt below.
# ────────────────────────────────────────────────────────────────────────

CHAT_HAT_SYSTEM_PROMPT = (
    "You are the HealthLens Assistant, acting as the lead medical and nutritional "
    "advisor. The user has just scanned a food product. You will be provided with "
    "the 'Result JSON' (the scan context) and the 'Chat History'. "
    "Use ONLY the data within this JSON to answer the user's questions. "
    "Tone: Warm, authoritative, clear, and highly empathetic. "
    "Format: normal conversational text. DO NOT output JSON. "
    "If a question is outside the provided data, gracefully state that the "
    "initial scan did not analyze that specific metric. "
    "Safety First: Remind them to consult a physician for medical questions, "
    "referencing Dr. Chen's clinical warnings if applicable."
)


class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str


class FollowUpRequest(BaseModel):
    scan_context: dict              # The full Result JSON from the initial scan
    chat_history: list[ChatMessage] # Previous conversation turns
    new_message: str                # The user's latest question


@app.post("/api/followup")
async def followup_chat(payload: FollowUpRequest):
    """
    Follow-up Q&A powered by ConclusionAdvisor ("Chat Hat" mode).

    Instead of re-running the full pipeline, we pass the original scan result
    (the "cheat sheet") plus the conversation history so the agent has full
    context to answer the user's follow-up questions conversationally.
    """
    cheat_sheet = json.dumps(payload.scan_context, indent=2, ensure_ascii=False)

    # ── Message array construction ───────────────────────────────────
    # 1. "Chat Hat" system prompt — overrides the agent's default JSON behaviour
    # 2. Cheat sheet injected as a user→assistant exchange so the agent
    #    "remembers" the scan without the user having to repeat it
    # 3. Prior conversation turns (chat_history)
    # 4. The new user question
    messages = [
        {"role": "user",      "content": CHAT_HAT_SYSTEM_PROMPT},
        {"role": "assistant", "content": "Understood. I will answer conversationally "
                                          "using only the scan data, maintaining a "
                                          "warm and empathetic tone. I will not output JSON."},
        {"role": "user",      "content": f"Here is the scan result (cheat sheet):\n"
                                          f"```json\n{cheat_sheet}\n```"},
        {"role": "assistant", "content": "Got it — I've reviewed the full scan result and "
                                          "I'm ready to answer your questions about this product."},
    ]

    # Append prior conversation turns
    for msg in payload.chat_history:
        messages.append({"role": msg.role, "content": msg.content})

    # Append the new question
    messages.append({"role": "user", "content": payload.new_message})

    try:
        response = await asyncio.to_thread(
            _openai_client.responses.create,
            input=messages,
            extra_body={
                "agent_reference": {
                    "name": CONCLUSION_AGENT["name"],
                    "version": CONCLUSION_AGENT["version"],
                    "type": "agent_reference",
                }
            },
        )
        reply = response.output_text or "I'm sorry, I couldn't generate a response."
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=502,
            content={"error": f"Agent call failed: {str(e)}"},
        )

    return {"reply": reply}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
