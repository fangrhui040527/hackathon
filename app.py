"""
app.py
CLI backend for the Multi-Agent Food Health Analyzer.

Flow:
1. User provides a food photo path (or a JSON file with --manual-json)
2. Azure Content Understanding extracts structured food data (or skip if not configured)
3. Result is optionally stored in Azure Blob Storage (skipped if not configured)
4. **GROUNDING PIPELINE** enriches data with APIs + knowledge bases
5. 5 specialist agents analyze the food in PARALLEL (no moderator)
6. Conclusion agent synthesizes all 5 analyses into a final report
7. Final report is printed to the console

Powered by Microsoft Agent Framework + Azure OpenAI GPT-4o
Grounded with 7 APIs + 6 knowledge databases: USDA, FooDB, FDA, IARC, NOVA, GI, etc.

Usage:
    python app.py <image_path> [--conditions "diabetes,hypertension"] [--medications "metformin,lisinopril"] [--allergies "peanuts,gluten"]
    python app.py --manual-json food_data.json [--conditions "diabetes"] [--medications "metformin"]
"""

import asyncio
import json
import mimetypes
import sys
import os
import argparse

from agent_framework import ChatMessage

from content_understanding import analyze_food_image, is_service_configured
from data_retreive import upload_to_blob, retrieve_from_blob, _is_blob_configured
from grounding_pipeline import enrich_food_data
from orchestrator import run_all_agents
from conclusion_agent import summarize_debate

# Agent display labels
AGENT_ICONS = {
    "Doctor": "🧑‍⚕️ Dr. Chen",
    "Nutritionist": "🥗 Dr. Patel",
    "FoodChemist": "🧪 Dr. Kim",
    "FitnessCoach": "🏋️ Marcus",
    "HealthSpecialist": "🏥 Dr. Amara",
}


async def run_agents(food_data: dict, enriched_data: dict = None) -> tuple[list[ChatMessage], object]:
    """
    Run all 5 specialist agents in parallel and collect their analyses.

    Args:
        food_data: Raw food data from Content Understanding.
        enriched_data: Grounded data from the grounding pipeline.

    Returns:
        tuple of (agent_responses as list[ChatMessage], client)
    """
    return await run_all_agents(food_data, enriched_data)


def main():
    parser = argparse.ArgumentParser(
        description="HealthScan — AI Food Health Analyzer with Grounded Multi-Agent Debate"
    )
    parser.add_argument("image_path", nargs="?", default=None,
                        help="Path to the food product image")
    parser.add_argument(
        "--manual-json", type=str, default=None,
        help="Path to a JSON file with food data (skips Content Understanding)",
    )
    parser.add_argument(
        "--conditions", type=str, default="",
        help='Comma-separated health conditions (e.g., "diabetes,hypertension,heart_disease")',
    )
    parser.add_argument(
        "--medications", type=str, default="",
        help='Comma-separated medications (e.g., "metformin,lisinopril,warfarin")',
    )
    parser.add_argument(
        "--allergies", type=str, default="",
        help='Comma-separated allergies (e.g., "peanuts,gluten,dairy")',
    )
    args = parser.parse_args()

    user_conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    user_medications = [m.strip() for m in args.medications.split(",") if m.strip()]
    user_allergies = [a.strip() for a in args.allergies.split(",") if a.strip()]

    # Validate inputs
    if not args.manual_json and not args.image_path:
        parser.error("Either provide an image_path or use --manual-json <file.json>")

    # ── Early check: Azure OpenAI is required for agents ─────────────────
    if not os.environ.get("AZURE_OPENAI_ENDPOINT") or not os.environ.get("AZURE_OPENAI_API_KEY"):
        from dotenv import load_dotenv
        load_dotenv()
    if not os.environ.get("AZURE_OPENAI_ENDPOINT") or not os.environ.get("AZURE_OPENAI_API_KEY"):
        print("\n❌ ERROR: Azure OpenAI is not configured.")
        print("   Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in your .env file.")
        print("   See .env.example for the required variables.")
        print("   The AI agents cannot run without Azure OpenAI / AI Foundry.")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("HEALTHSCAN — AI-Powered Food Health Analyzer")
    print(f"{'='*60}")

    # ── Mode: Manual JSON input (skip Content Understanding) ─────────────
    if args.manual_json:
        json_path = args.manual_json
        if not os.path.isfile(json_path):
            print(f"Error: JSON file not found: {json_path}")
            sys.exit(1)
        print(f"Mode: Manual JSON input")
        print(f"File: {os.path.basename(json_path)}")
        if user_conditions:
            print(f"Health Conditions: {', '.join(user_conditions)}")
        if user_medications:
            print(f"Medications: {', '.join(user_medications)}")
        if user_allergies:
            print(f"Allergies: {', '.join(user_allergies)}")
        print()

        print("Step 1: Loading food data from JSON file...")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                food_data = json.load(f)
            print("  ✅ Food data loaded from JSON!")
        except Exception as e:
            print(f"  ❌ Error loading JSON: {e}")
            sys.exit(1)

        # Skip blob storage steps
        blob_name = None

    # ── Mode: Image analysis ─────────────────────────────────────────────
    else:
        image_path = args.image_path
        if not os.path.isfile(image_path):
            print(f"Error: File not found: {image_path}")
            sys.exit(1)

        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "image/jpeg"

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        file_size_kb = len(image_bytes) / 1024
        print(f"File: {os.path.basename(image_path)}")
        print(f"Size: {file_size_kb:.1f} KB | Type: {mime_type}")
        if user_conditions:
            print(f"Health Conditions: {', '.join(user_conditions)}")
        if user_medications:
            print(f"Medications: {', '.join(user_medications)}")
        if user_allergies:
            print(f"Allergies: {', '.join(user_allergies)}")
        print()

        # ── Step 1: Content Understanding ────────────────────────────────
        if is_service_configured():
            print("Step 1: Analyzing food photo with Azure Content Understanding...")
            try:
                food_data = analyze_food_image(image_bytes, mime_type)
                print("  ✅ Food data extracted successfully!")
            except Exception as e:
                print(f"  ❌ Error - Content Understanding failed: {e}")
                sys.exit(1)
        else:
            print("Step 1: Azure Content Understanding is NOT configured.")
            print("  ⚠️  To use image analysis, set AZURE_CONTENT_UNDERSTANDING_ENDPOINT")
            print("     and AZURE_CONTENT_UNDERSTANDING_KEY in your .env file.")
            print("  💡 TIP: Use --manual-json <file.json> to provide food data directly.")
            sys.exit(1)

        # ── Step 2: Store in Blob Storage ────────────────────────────────
        blob_name = None
        if _is_blob_configured():
            print("Step 2: Storing data in Azure Blob Storage...")
            try:
                blob_name = upload_to_blob(food_data)
                print(f"  ✅ Stored as '{blob_name}'")
            except Exception as e:
                print(f"  ⚠️  Blob Storage upload failed (non-fatal): {e}")
        else:
            print("Step 2: Azure Blob Storage not configured — skipping upload.")
            print("  ℹ️  Data will be processed locally (this is fine).")

        # ── Step 3: Retrieve from Blob Storage ───────────────────────────
        if blob_name:
            print("Step 3: Retrieving data from Blob Storage...")
            try:
                food_data = retrieve_from_blob(blob_name)
                print("  ✅ Data retrieved successfully!")
            except Exception as e:
                print(f"  ⚠️  Blob retrieval failed (using local data): {e}")
        else:
            print("Step 3: Using local data (Blob Storage skipped).")

    # Show extracted food data
    print("\n--- Extracted Food Data (JSON) ---")
    print(json.dumps(food_data, indent=2, default=str))
    print()

    # ── Step 4: GROUNDING PIPELINE ───────────────────────────────────────
    print("Step 4: Running Grounding Pipeline (APIs + Knowledge Bases)...")
    print("  Enriching with: Open Food Facts, USDA, FDA, IARC, NOVA, GI Database...")
    try:
        enriched_data = enrich_food_data(
            raw_food_data=food_data,
            user_conditions=user_conditions,
            user_medications=user_medications,
            user_allergies=user_allergies,
        )
        print("  ✅ Grounding pipeline complete!")

        # Show risk summary
        risk = enriched_data.get("grounding", {}).get("risk_summary", {})
        verdict = risk.get("overall_verdict", "UNKNOWN")
        total_risks = risk.get("total_risk_factors", 0)
        verdict_icon = {"SAFE": "✅", "CAUTION": "⚠️", "AVOID": "❌"}.get(verdict, "❓")
        print(f"\n  {verdict_icon} PRELIMINARY VERDICT: {verdict} ({total_risks} risk factor(s))")
        for rf in risk.get("risk_factors", []):
            rf_icon = {"critical": "🚨", "high": "❌", "medium": "⚠️", "low": "ℹ️"}.get(rf["level"], "•")
            print(f"    {rf_icon} [{rf['level'].upper()}] {rf['detail']}")
        print()

    except Exception as e:
        print(f"  ⚠️  Grounding pipeline error (falling back to raw data): {e}")
        import traceback
        traceback.print_exc()
        enriched_data = None

    # ── Step 5 & 6: Parallel Agent Analysis + Conclusion ────────────────
    async def _run_agents_and_summarize():
        """Run all 5 agents in parallel + conclusion in one event loop."""
        agent_responses, client = await run_agents(food_data, enriched_data)
        summary = await summarize_debate(client, agent_responses)
        return agent_responses, client, summary

    print("Step 5: Running 5 specialist agents in parallel...")
    print("=" * 60)
    try:
        agent_responses, client, summary = asyncio.run(_run_agents_and_summarize())
        print("  ✅ All 5 agents completed!")
    except Exception as e:
        print(f"  ❌ Error - Agent analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Display each agent's analysis
    print("\n--- Expert Agent Analyses ---")
    if agent_responses:
        for msg in agent_responses:
            if msg.text:
                author = getattr(msg, "author_name", None) or msg.role
                label = AGENT_ICONS.get(str(author), f"[{author}]")
                print(f"\n{label}")
                print(msg.text)
                print("-" * 40)
    else:
        print("No agent responses were captured.")

    print("\n" + "=" * 60)
    print("COMPREHENSIVE FOOD ANALYSIS REPORT")
    print("=" * 60)
    print(summary)

    print(
        "\n⚕️  Disclaimer: This analysis is AI-generated and grounded in public health APIs and knowledge databases. "
        "It is for INFORMATIONAL PURPOSES ONLY and is not a "
        "substitute for professional medical, dietary, or nutritional advice. Always consult "
        "qualified healthcare professionals for personal health decisions."
    )
    print(
        "\n📊 Data Sources: fdc.nal.usda.gov | foodb.ca | ddinter2.scbdd.com | "
        "open.fda.gov | open.fda.gov/apis/drug/ | dslb.od.nih.gov | "
        "openfoodfacts.org | Blob: additives, dietary_limits, drug_food_interactions, "
        "glycemic_index, iarc_carcinogens, nova_classification"
    )


if __name__ == "__main__":
    main()
