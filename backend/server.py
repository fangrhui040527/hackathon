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
    {"name": "doctor-agent",              "version": "18", "label": "Dr. Chen",    "display": "🧑‍⚕️ Dr. Chen is reviewing..."},
    {"name": "nutritionist-agent",        "version": "8",  "label": "Dr. Patel",   "display": "🥗 Dr. Patel is analyzing..."},
    {"name": "foodchemist-agent",         "version": "9",  "label": "Dr. Kim",     "display": "🧪 Dr. Kim checking chemicals..."},
    {"name": "fitnessCoach-agent",        "version": "8",  "label": "Marcus",      "display": "🏋️ Marcus assessing fitness..."},
    {"name": "healthSpecialist-agent",    "version": "7",  "label": "Dr. Amara",   "display": "🏥 Dr. Amara reviewing risks..."},
    {"name": "cultural-religious-compliance-agent", "version": "8", "label": "Dr. Nixon", "display": "🕌 Dr. Nixon checking compliance..."},
]
CONCLUSION_AGENT = {"name": "conclusionAdvisor-agent", "version": "8"}


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
            "summary": text if text else "No analysis available.",
            "flags": flags or ["Analysis complete"],
            "confidence": 80 + (i * 2),
            "considered_health_note": has_health_note,
        })

    # Extract compliance data from conclusion JSON if available
    # The agent may return expert_breakdown.compliance as a string or a dict
    compliance_data = None
    compliance_text = None
    if conclusion_json:
        eb = conclusion_json.get("expert_breakdown", {})
        if isinstance(eb, dict):
            raw_compliance = eb.get("compliance")
            if isinstance(raw_compliance, dict):
                compliance_data = raw_compliance
            elif isinstance(raw_compliance, str):
                compliance_text = raw_compliance

    # Overall verdict — prefer conclusion agent's verdict_color
    if conclusion_json and conclusion_json.get("verdict_color"):
        color = conclusion_json["verdict_color"].lower()
        overall_verdict = {"red": "avoid", "green": "safe", "yellow": "caution"}.get(color, "caution")
    else:
        verdicts = [a["verdict"] for a in agent_outputs]
        if verdicts.count("avoid") >= 3:
            overall_verdict = "avoid"
        elif verdicts.count("safe") >= 3:
            overall_verdict = "safe"
        else:
            overall_verdict = "caution"

    # Compliance override: Haram or Non-Vegan flags force AVOID
    # Handle structured dict format
    if compliance_data and isinstance(compliance_data, dict):
        halal = (compliance_data.get("halal_status") or "").lower()
        vegan = (compliance_data.get("vegan_status") or "").lower()
        if halal in ("haram", "non-halal") or vegan in ("non-vegan", "not vegan"):
            overall_verdict = "avoid"
    # Handle string format from expert_breakdown
    elif compliance_text:
        ct_lower = compliance_text.lower()
        if "haram" in ct_lower or "non-halal" in ct_lower or "non-vegan" in ct_lower or "not vegan" in ct_lower:
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
    elif compliance_text:
        result["compliance"] = {"summary": compliance_text}

    return result


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "HealthScan API (Foundry SDK)"}


# ── Foundry SDK helpers ─────────────────────────────────────────────────

def _build_task_prompt(food_data: dict, health_note: str = "") -> str:
    """Build the analysis prompt for agents with food data and user health context."""
    food_json = json.dumps(food_data, indent=2, ensure_ascii=False)
    prompt = (
        "Analyze the following food item. First use your built-in knowledge base "
        "tools to look up relevant data. If any external API call (such as "
        "OpenFoodFacts or barcode lookups) fails or returns no results, simply "
        "ignore it and continue your analysis using the food data provided below "
        "and your own expertise. Never let a failed tool call stop you from "
        "providing your full specialist report.\n\n"
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

    Handles two failure modes:
    1) Agent returns no output_text after MCP approvals → nudge + retry
    2) Agent's external tool call fails (e.g. OpenFoodFacts 404) → retry with
       an amended prompt telling the agent to skip external lookups.

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
    name = agent_def["name"]

    def _approve_loop(resp, max_iters=15):
        """Keep approving MCP requests until we get output_text or run out of approvals."""
        for iteration in range(max_iters):
            if resp.output_text:
                return resp
            approvals = [
                item for item in (resp.output or [])
                if item.type == "mcp_approval_request"
            ]
            if not approvals:
                return resp
            print(f"[Agent MCP] {name}: approving {len(approvals)} request(s) (iter {iteration+1})")
            resp = _openai_client.responses.create(
                input=[{
                    "type": "mcp_approval_response",
                    "approval_request_id": item.id,
                    "approve": True,
                } for item in approvals],
                extra_body=agent_ref,
                previous_response_id=resp.id,
            )
        return resp

    FALLBACK_SUFFIX = (
        "\n\nIMPORTANT: Do NOT call any external API tools (such as OpenFoodFacts, "
        "barcode lookups, or web searches). Analyze ONLY using the food data provided "
        "above and your built-in knowledge base. Provide your complete specialist "
        "analysis directly."
    )

    MAX_RETRIES = 2

    for attempt in range(1 + MAX_RETRIES):
        current_prompt = prompt if attempt == 0 else prompt + FALLBACK_SUFFIX
        try:
            if attempt > 0:
                print(f"[Agent Retry] {name}: attempt {attempt+1} (with fallback prompt)")

            response = _openai_client.responses.create(
                input=[{"role": "user", "content": current_prompt}],
                extra_body=agent_ref,
            )
            response = _approve_loop(response)

            # If still no text, nudge the agent
            if not response.output_text:
                print(f"[Agent Nudge] {name}: no text after approvals, nudging...")
                response = _openai_client.responses.create(
                    input=[{"role": "user", "content":
                        "Please provide your complete analysis now based on the food data above. "
                        "Do not attempt any external API calls."}],
                    extra_body=agent_ref,
                    previous_response_id=response.id,
                )
                response = _approve_loop(response)

            out = response.output_text
            if out:
                print(f"[Agent OK] {name}: attempt {attempt+1}, {len(out)} chars")
                return {"agent_name": name, "label": agent_def.get("label", name), "text": out}

            output_types = [item.type for item in (response.output or [])]
            print(f"[Agent Empty] {name}: attempt {attempt+1}, types={output_types}")

        except Exception as e:
            err_str = str(e)
            is_tool_error = "tool_user_error" in err_str or "404" in err_str or "tool_error" in err_str
            print(f"[Agent Error] {name}: attempt {attempt+1}, {type(e).__name__}: {err_str[:300]}")

            if is_tool_error and attempt < MAX_RETRIES:
                print(f"[Agent Error] {name}: tool error detected, will retry with fallback prompt")
                continue  # Retry with FALLBACK_SUFFIX

            if attempt == MAX_RETRIES:
                return {"agent_name": name, "label": agent_def.get("label", name), "text": "", "error": err_str[:500]}

    print(f"[Agent FAIL] {name}: all attempts exhausted")
    return {"agent_name": name, "label": agent_def.get("label", name), "text": "", "error": "All retries exhausted"}


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

            # Log agent results summary
            for r in agent_results:
                txt_len = len(r["text"]) if r["text"] else 0
                err = r.get("error", "")
                print(f"[Agent Result] {r['agent_name']}: text_len={txt_len}, error={err[:100] if err else 'none'}")

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
                "Synthesize these reports into your final JSON verdict.\n"
                "Apply the Hierarchical Priority Matrix:\n"
                "1. Doctor (Medical Safety) — any medical red flag → RED (AVOID).\n"
                "2. Compliance (Religious/Ethical) — any Haram, Non-Halal, or Non-Vegan \n"
                "   violation for the user → RED (AVOID) regardless of nutritional score.\n"
                "3. Chemist (Banned/Prohibited substances) → RED (AVOID).\n"
                "4. Nutrition/Fitness/Holistic (Quality) — factor only after 1-3 are clear.\n\n"
                "Return ONLY valid JSON, no markdown fences."
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


# ── Emergency detection ──────────────────────────────────────────────────
class EmergencyCheckRequest(BaseModel):
    message: str

@app.post("/api/check-emergency")
async def check_emergency(payload: EmergencyCheckRequest):
    """
    Lightweight LLM classification: does the user's message indicate they
    need emergency help (medical, mental health, danger)?
    Returns { "emergency": true/false }
    """
    try:
        response = await asyncio.to_thread(
            _openai_client.responses.create,
            model="gpt-4o",
            instructions=(
                "You are an emergency-intent classifier for a health app. "
                "Determine if the user's message indicates they need "
                "immediate emergency help such as: medical emergency, "
                "severe allergic reaction, poisoning, choking, chest pain, "
                "difficulty breathing, overdose, suicidal thoughts, "
                "self-harm, requesting 911, or any life-threatening situation.\n"
                "Respond with ONLY the word YES or NO. Nothing else."
            ),
            input=payload.message,
            temperature=0,
            max_output_tokens=16,
        )
        answer = response.output_text.strip().upper()
        print(f"[Emergency Check] message='{payload.message}' → answer='{answer}'")
        return {"emergency": answer == "YES"}
    except Exception as e:
        print(f"[Emergency Check Error] {e}")
        return {"emergency": False}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
