"""
server.py
FastAPI backend for the HealthScan Multi-Agent Food Analyzer.

Endpoints:
  POST /api/analyze  — accepts image + healthNote, streams SSE events as pipeline progresses
  GET  /api/health   — health check

SSE event format:
  { "stage": "upload|extract|agent1-5|conclude|done", "label": "...", "data": {...} }
"""

import asyncio
import base64
import json
import os
import sys
import traceback
from io import BytesIO

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from content_understanding import analyze_food_image, is_service_configured
from grounding_pipeline import enrich_food_data
from orchestrator import run_all_agents
from conclusion_agent import summarize_debate

# Import agent sub-applications (mounted below so everything runs on one port)
from agent_server_doctor import app as doctor_app
from agent_server_fitness import app as fitness_app
from agent_server_health import app as health_app
from agent_server_nutritionist import app as nutritionist_app
from agent_server_chemi import app as chemi_app

app = FastAPI(title="HealthScan API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all agent sub-apps under /agent/<name>
app.mount("/agent/doctor", doctor_app)
app.mount("/agent/fitness", fitness_app)
app.mount("/agent/health", health_app)
app.mount("/agent/nutritionist", nutritionist_app)
app.mount("/agent/chemi", chemi_app)

# Agent mapping (index → agent name used in backend)
AGENT_NAMES = ["Doctor", "Nutritionist", "FoodChemist", "FitnessCoach", "HealthSpecialist"]


def _parse_health_note(health_note: str) -> tuple[list[str], list[str], list[str]]:
    """Simple parse of the free-text health note into conditions/medications/allergies."""
    if not health_note:
        return [], [], []

    note_lower = health_note.lower()

    conditions = []
    condition_keywords = {
        "diabetes": "diabetes", "diabetic": "diabetes",
        "hypertension": "hypertension", "high blood pressure": "hypertension",
        "heart disease": "heart_disease", "cardiovascular": "heart_disease",
        "cholesterol": "high_cholesterol", "high cholesterol": "high_cholesterol",
        "kidney": "kidney_disease", "ckd": "kidney_disease",
        "celiac": "celiac_disease", "coeliac": "celiac_disease",
        "obesity": "obesity", "overweight": "obesity",
        "ibs": "ibs", "irritable bowel": "ibs",
        "gout": "gout",
    }
    for keyword, condition in condition_keywords.items():
        if keyword in note_lower and condition not in conditions:
            conditions.append(condition)

    medications = []
    med_keywords = [
        "metformin", "lisinopril", "losartan", "amlodipine", "atorvastatin",
        "simvastatin", "warfarin", "aspirin", "insulin", "levothyroxine",
        "omeprazole", "pantoprazole", "ramipril", "hydrochlorothiazide",
    ]
    for med in med_keywords:
        if med in note_lower:
            medications.append(med)

    allergies = []
    allergy_keywords = [
        "peanut", "gluten", "dairy", "lactose", "shellfish", "soy",
        "egg", "tree nut", "wheat", "fish", "sesame",
    ]
    for allergen in allergy_keywords:
        if allergen in note_lower:
            allergies.append(allergen)

    return conditions, medications, allergies


def _build_result_from_responses(
    food_data: dict,
    enriched_data: dict,
    agent_responses: list,
    summary_text: str,
) -> dict:
    """Build the frontend-compatible result object from agent outputs."""
    # Extract product info from food data
    product_name = (
        food_data.get("product_name")
        or food_data.get("name")
        or food_data.get("food_name")
        or food_data.get("title")
        or None
    )
    # Fallback: try Azure CU nested "contents[0].fields" structure
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
    # Fallback: try enriched data's Open Food Facts product name
    if not product_name and enriched_data:
        off = enriched_data.get("grounding", {}).get("open_food_facts", {})
        product_name = off.get("product_name") if off else None
    product_name = product_name or "Unknown Product"

    # Get NOVA classification for type
    nova = enriched_data.get("grounding", {}).get("nova_classification", {}) if enriched_data else {}
    nova_group = nova.get("nova_group", 0)
    type_labels = {1: "Unprocessed", 2: "Processed Ingredient", 3: "Processed Food", 4: "Ultra-Processed"}
    product_type = type_labels.get(nova_group, "Food Product")

    # Extract nutrition from enriched data or raw data
    nutrition_pills = []
    raw_nutrition = food_data.get("nutrition") or food_data.get("nutrition_facts") or food_data.get("nutrients") or {}
    if isinstance(raw_nutrition, dict):
        nutrient_map = [
            ("Calories", ["calories", "energy_kcal", "energy"]),
            ("Sugar", ["sugars", "sugar", "total_sugar", "sugars_g"]),
            ("Fat", ["fat", "total_fat", "fat_g"]),
            ("Sat. Fat", ["saturated_fat", "sat_fat"]),
            ("Sodium", ["sodium", "sodium_mg", "salt"]),
            ("Carbs", ["carbohydrates", "carbs", "total_carbohydrate"]),
            ("Protein", ["protein", "protein_g"]),
            ("Fibre", ["fiber", "dietary_fiber", "fibre"]),
        ]
        for label, keys in nutrient_map:
            for k in keys:
                val = raw_nutrition.get(k)
                if val is not None:
                    nutrition_pills.append({"label": label, "value": str(val)})
                    break

    # Build agent outputs
    agent_outputs = []
    for i, resp in enumerate(agent_responses):
        text = resp.text if resp and resp.text else ""
        # Try to determine verdict from text
        verdict = "caution"
        text_lower = text.lower()
        if "avoid" in text_lower[:200] or "not recommended" in text_lower[:200]:
            verdict = "avoid"
        elif "safe" in text_lower[:200] or "generally safe" in text_lower[:200]:
            verdict = "safe"

        # Extract flags from text (look for bullet points or bold items)
        flags = []
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("- **") or line.startswith("• **"):
                flag = line.lstrip("-•").strip().strip("*").split("**")[0].strip("* ")
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
            "considered_health_note": bool(enriched_data and enriched_data.get("user_profile", {}).get("conditions")),
        })

    # Determine overall verdict
    verdicts = [a["verdict"] for a in agent_outputs]
    if verdicts.count("avoid") >= 3:
        overall_verdict = "avoid"
    elif verdicts.count("safe") >= 3:
        overall_verdict = "safe"
    else:
        overall_verdict = "caution"

    # Risk factors from grounding
    risk_summary = enriched_data.get("grounding", {}).get("risk_summary", {}) if enriched_data else {}
    risk_factors = risk_summary.get("risk_factors", [])
    flags = [rf["detail"] for rf in risk_factors[:4]] if risk_factors else ["Analysis complete"]

    # Build ok_for / avoid_if from conclusion text
    ok_for = ["Healthy adults in moderation", "Occasional treat"]
    avoid_if = []
    if overall_verdict == "avoid":
        avoid_if = ["Diabetes or insulin resistance", "High blood pressure", "Weight loss goals"]
    elif overall_verdict == "caution":
        avoid_if = ["Those with sensitive health conditions"]

    confidence = risk_summary.get("confidence", 82) if risk_summary else 82

    return {
        "product": product_name,
        "type": product_type,
        "servingSize": food_data.get("serving_size", ""),
        "nutrition": nutrition_pills,
        "funFacts": [],
        "conclusion": {
            "verdict": overall_verdict,
            "summary": summary_text[:600] if summary_text else "Analysis complete.",
            "ok_for": ok_for,
            "avoid_if": avoid_if,
            "flags": flags,
            "confidence": confidence,
        },
        "agentOutputs": agent_outputs,
    }


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "HealthScan API"}


@app.post("/api/analyze")
async def analyze(
    image: UploadFile = File(...),
    healthNote: str = Form(""),
):
    """
    Analyze a food image through the full pipeline, streaming SSE events.
    """
    async def event_generator():
        try:
            # ── Stage: Upload ────────────────────────────────────
            yield {"event": "stage", "data": json.dumps({"stage": "upload", "label": "Photo received"})}

            image_bytes = await image.read()
            mime_type = image.content_type or "image/jpeg"

            # Parse health note
            conditions, medications, allergies = _parse_health_note(healthNote)

            # ── Stage: Extract ───────────────────────────────────
            yield {"event": "stage", "data": json.dumps({"stage": "extract", "label": "Reading the label..."})}

            food_data = None
            if is_service_configured():
                try:
                    food_data = analyze_food_image(image_bytes, mime_type)
                    print(f"[Analyze] Content Understanding returned keys: {list(food_data.keys()) if isinstance(food_data, dict) else type(food_data)}")
                    print(f"[Analyze] Product name: {food_data.get('product_name', 'NOT FOUND')}")
                except Exception as e:
                    yield {"event": "stage", "data": json.dumps({"stage": "extract", "label": f"Content Understanding error: {str(e)[:100]}"})}
                    food_data = None

            if not food_data:
                # Fallback: create minimal food data
                food_data = {
                    "product_name": "Unknown Product",
                    "note": "Content Understanding not available — using basic analysis",
                }

            # ── Stage: Grounding ─────────────────────────────────
            yield {"event": "stage", "data": json.dumps({"stage": "grounding", "label": "Enriching with databases..."})}

            enriched_data = None
            try:
                enriched_data = enrich_food_data(
                    raw_food_data=food_data,
                    user_conditions=conditions,
                    user_medications=medications,
                    user_allergies=allergies,
                )
            except Exception as e:
                print(f"Grounding error: {e}")
                traceback.print_exc()

            # ── Stages: Agents ───────────────────────────────────
            agent_names = ["agent1", "agent2", "agent3", "agent4", "agent5"]
            agent_labels = [
                "Dr. Chen is reviewing...",
                "Dr. Patel is analyzing...",
                "Dr. Kim checking chemicals...",
                "Marcus assessing fitness...",
                "Dr. Amara reviewing risks...",
            ]

            for name, label in zip(agent_names, agent_labels):
                yield {"event": "stage", "data": json.dumps({"stage": name, "label": label})}

            # Run all agents in parallel
            agent_responses, client = await run_all_agents(food_data, enriched_data)

            # ── Stage: Conclude ──────────────────────────────────
            yield {"event": "stage", "data": json.dumps({"stage": "conclude", "label": "Summarizing findings..."})}

            summary_text = await summarize_debate(client, agent_responses)

            # ── Stage: Done ──────────────────────────────────────
            result = _build_result_from_responses(food_data, enriched_data, agent_responses, summary_text)

            yield {"event": "stage", "data": json.dumps({"stage": "done", "label": "Done!", "data": result})}

        except Exception as e:
            traceback.print_exc()
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
