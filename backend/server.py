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

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
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
    {"name": "doctor-agent",              "version": "11", "label": "Dr. Chen",    "display": "🧑‍⚕️ Dr. Chen is reviewing..."},
    {"name": "nutritionist-agent",        "version": "4",  "label": "Dr. Patel",   "display": "🥗 Dr. Patel is analyzing..."},
    {"name": "foodchemist-agent",         "version": "3",  "label": "Dr. Kim",     "display": "🧪 Dr. Kim checking chemicals..."},
    {"name": "fitnessCoach-agent",        "version": "4",  "label": "Marcus",      "display": "🏋️ Marcus assessing fitness..."},
    {"name": "healthSpecialist-agent",    "version": "3",  "label": "Dr. Amara",   "display": "🏥 Dr. Amara reviewing risks..."},
]
CONCLUSION_AGENT = {"name": "conclusionAdvisor-agent", "version": "3"}


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

    return {
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
    Synchronous one-shot call to a Foundry agent via openai_client.responses.create.
    Designed to be wrapped with asyncio.to_thread for parallel execution.
    Returns a result dict; on failure returns an error marker so other agents aren't affected.
    """
    try:
        response = _openai_client.responses.create(
            input=[{"role": "user", "content": prompt}],
            extra_body={
                "agent_reference": {
                    "name": agent_def["name"],
                    "version": agent_def["version"],
                    "type": "agent_reference",
                }
            },
        )
        return {
            "agent_name": agent_def["name"],
            "label": agent_def.get("label", agent_def["name"]),
            "text": response.output_text,
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

    Flow: upload → extract (CU) → 5 agents (parallel) → conclusion → done
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

            # Fire all 5 agents in parallel using asyncio.to_thread
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
            }
            expert_sections = []
            for r in agent_results:
                role = role_map.get(r["agent_name"], r["label"])
                text = r["text"] if r["text"] else "No analysis provided."
                expert_sections.append(f"{role}: {text}")

            conclusion_prompt = (
                f"ORIGINAL SCANNED LABEL TEXT:\n{ocr_text}\n\n"
                f"EXPERT REPORTS:\n" + "\n\n".join(expert_sections) + "\n\n"
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


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
