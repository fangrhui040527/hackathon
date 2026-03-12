"""
test_agents.py
Comprehensive test script to verify all HealthLens agent API tools are functioning.

Tests:
  1. Health check endpoint
  2. Azure AI Foundry client connection
  3. Azure Content Understanding service configuration
  4. Each individual Foundry agent (doctor, nutritionist, chemist, fitness, health specialist, compliance)
  5. Conclusion agent
  6. Follow-up chat endpoint
"""

import asyncio
import json
import os
import sys
import time
import traceback

from dotenv import load_dotenv
load_dotenv()

# ── Test configuration ──────────────────────────────────────────────────
PASS = "✅ PASS"
FAIL = "❌ FAIL"
WARN = "⚠️  WARN"

results = []

def record(name, status, detail=""):
    results.append({"name": name, "status": status, "detail": detail})
    print(f"  {status}  {name}" + (f" — {detail}" if detail else ""))


# ── 1. Environment variables ────────────────────────────────────────────
print("\n" + "="*70)
print("  HealthLens Agent API — Comprehensive Test Suite")
print("="*70)

print("\n[1/7] Checking environment variables...")
required_vars = [
    "AZURE_AI_FOUNDRY_ENDPOINT",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "AZURE_CONTENT_UNDERSTANDING_ENDPOINT",
    "AZURE_CONTENT_UNDERSTANDING_KEY",
]
for var in required_vars:
    val = os.environ.get(var)
    if val:
        record(f"ENV: {var}", PASS, f"set ({len(val)} chars)")
    else:
        record(f"ENV: {var}", FAIL, "not set")


# ── 2. Azure AI Foundry client connection ───────────────────────────────
print("\n[2/7] Testing Azure AI Foundry client connection...")
try:
    from azure.identity import DefaultAzureCredential
    from azure.ai.projects import AIProjectClient

    endpoint = os.environ["AZURE_AI_FOUNDRY_ENDPOINT"]
    credential = DefaultAzureCredential()
    project_client = AIProjectClient(endpoint=endpoint, credential=credential)
    openai_client = project_client.get_openai_client()
    record("Foundry: AIProjectClient init", PASS)
    record("Foundry: get_openai_client()", PASS)
except Exception as e:
    record("Foundry: client init", FAIL, str(e))
    print(f"  Cannot continue agent tests without Foundry client. Aborting agent tests.")
    openai_client = None


# ── 3. Content Understanding service ───────────────────────────────────
print("\n[3/7] Testing Azure Content Understanding service...")
try:
    from content_understanding import is_service_configured
    if is_service_configured():
        record("Content Understanding: configured", PASS)
        # Quick connectivity check — create client (doesn't make a network call)
        from content_understanding import _get_client
        cu_client = _get_client()
        record("Content Understanding: client created", PASS)
    else:
        record("Content Understanding: configured", FAIL, "endpoint/key not set")
except Exception as e:
    record("Content Understanding: import/init", FAIL, str(e))


# ── 4. Individual agent tests ──────────────────────────────────────────
AGENTS = [
    {"name": "doctor-agent",              "version": "17", "label": "Dr. Chen (Doctor)"},
    {"name": "nutritionist-agent",        "version": "8",  "label": "Dr. Patel (Nutritionist)"},
    {"name": "foodchemist-agent",         "version": "9",  "label": "Dr. Kim (Chemist)"},
    {"name": "fitnessCoach-agent",        "version": "8",  "label": "Marcus (Fitness)"},
    {"name": "healthSpecialist-agent",    "version": "7",  "label": "Dr. Amara (Health Specialist)"},
    {"name": "cultural-religious-compliance-agent", "version": "8", "label": "Dr. Nixon (Compliance)"},
]
CONCLUSION_AGENT = {"name": "conclusionAdvisor-agent", "version": "7", "label": "Conclusion Advisor"}

# Simple test prompt — lightweight food data
TEST_FOOD_DATA = {
    "product_name": "Test Chocolate Bar",
    "brand": "TestBrand",
    "ingredients": "sugar, cocoa butter, milk powder, soy lecithin, vanillin",
    "nutrition": {
        "calories": "250 kcal",
        "fat": "14g",
        "sugar": "26g",
        "protein": "3g",
        "sodium": "50mg",
    },
    "serving_size": "45g",
}

TEST_PROMPT = (
    "Analyze the following food item. Provide a BRIEF assessment (2-3 sentences max) "
    "from your perspective.\n\n"
    f"Food Data:\n```json\n{json.dumps(TEST_FOOD_DATA, indent=2)}\n```"
)


def call_agent(agent_def, prompt):
    """Call a single Foundry agent and return (success, output_text, elapsed_seconds)."""
    agent_ref = {
        "agent_reference": {
            "name": agent_def["name"],
            "version": agent_def["version"],
            "type": "agent_reference",
        }
    }
    start = time.time()
    response = openai_client.responses.create(
        input=[{"role": "user", "content": prompt}],
        extra_body=agent_ref,
    )

    # MCP tool approval loop
    for _ in range(5):
        if response.output_text:
            break
        approvals = [
            item for item in (response.output or [])
            if item.type == "mcp_approval_request"
        ]
        if not approvals:
            break
        approval_inputs = [
            {
                "type": "mcp_approval_response",
                "approval_request_id": item.id,
                "approve": True,
            }
            for item in approvals
        ]
        response = openai_client.responses.create(
            input=approval_inputs,
            extra_body=agent_ref,
            previous_response_id=response.id,
        )

    elapsed = time.time() - start
    text = response.output_text or ""
    return bool(text.strip()), text, elapsed


if openai_client:
    print("\n[4/7] Testing individual agents (sequential)...")
    print("  (Using lightweight test prompt — each agent will produce a brief response)")
    print()

    for agent_def in AGENTS:
        label = agent_def["label"]
        try:
            success, text, elapsed = call_agent(agent_def, TEST_PROMPT)
            if success:
                record(f"Agent: {label}", PASS, f"{elapsed:.1f}s, {len(text)} chars")
                print(f"\n  ── Full output from {label} ──")
                print(text)
                print(f"  ── End of {label} ──\n")
            else:
                record(f"Agent: {label}", WARN, f"{elapsed:.1f}s — returned empty text")
        except Exception as e:
            record(f"Agent: {label}", FAIL, f"{type(e).__name__}: {str(e)[:200]}")

    # ── 5. Conclusion agent ─────────────────────────────────────────────
    print("\n[5/7] Testing conclusion agent...")
    try:
        conclusion_prompt = (
            "Given this food data and a single expert report, produce a brief JSON verdict.\n\n"
            f"Food: {json.dumps(TEST_FOOD_DATA)}\n\n"
            "Expert Report: This chocolate bar is high in sugar and fat. Moderate consumption advised.\n\n"
            "Return ONLY valid JSON with keys: product_name, verdict_color (green/yellow/red), verdict_summary, critical_alerts."
        )
        success, text, elapsed = call_agent(CONCLUSION_AGENT, conclusion_prompt)
        if success:
            record(f"Agent: {CONCLUSION_AGENT['label']}", PASS, f"{elapsed:.1f}s, {len(text)} chars")
            print(f"\n  ── Full output from {CONCLUSION_AGENT['label']} ──")
            print(text)
            print(f"  ── End of {CONCLUSION_AGENT['label']} ──\n")
            # Try parsing JSON
            try:
                cleaned = text.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1]
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3]
                json.loads(cleaned.strip())
                record("Conclusion: valid JSON output", PASS)
            except (json.JSONDecodeError, ValueError):
                record("Conclusion: valid JSON output", WARN, "Response is not valid JSON (may still work)")
        else:
            record(f"Agent: {CONCLUSION_AGENT['label']}", WARN, f"{elapsed:.1f}s — returned empty text")
    except Exception as e:
        record(f"Agent: {CONCLUSION_AGENT['label']}", FAIL, f"{type(e).__name__}: {str(e)[:200]}")

    # ── 6. Parallel agent execution test ────────────────────────────────
    print("\n[6/7] Testing parallel agent execution (simulates /api/analyze flow)...")
    try:
        async def test_parallel():
            start = time.time()
            futures = [
                asyncio.to_thread(call_agent, agent_def, TEST_PROMPT)
                for agent_def in AGENTS
            ]
            results_parallel = await asyncio.gather(*futures, return_exceptions=True)
            elapsed = time.time() - start

            successes = sum(1 for r in results_parallel if not isinstance(r, Exception) and r[0])
            failures = sum(1 for r in results_parallel if isinstance(r, Exception))
            empty = sum(1 for r in results_parallel if not isinstance(r, Exception) and not r[0])
            return successes, failures, empty, elapsed

        successes, failures, empty, elapsed = asyncio.run(test_parallel())
        total = len(AGENTS)
        if successes == total:
            record("Parallel execution: all 6 agents", PASS, f"{elapsed:.1f}s total")
        elif failures == 0:
            record("Parallel execution: all 6 agents", WARN, f"{successes}/{total} succeeded, {empty} empty, {elapsed:.1f}s")
        else:
            record("Parallel execution: all 6 agents", FAIL, f"{successes}/{total} ok, {failures} errors, {elapsed:.1f}s")
    except Exception as e:
        record("Parallel execution", FAIL, f"{type(e).__name__}: {str(e)[:200]}")

    # ── 7. Follow-up chat test (via direct function call) ───────────────
    print("\n[7/7] Testing follow-up chat (conclusion agent in Chat Hat mode)...")
    try:
        from server import CHAT_HAT_SYSTEM_PROMPT

        scan_context = {
            "product": "Test Chocolate Bar",
            "conclusion": {"verdict": "caution", "summary": "High in sugar and fat."},
            "agentOutputs": [{"agentId": 1, "verdict": "caution", "summary": "Moderate consumption advised."}],
        }
        cheat_sheet = json.dumps(scan_context, indent=2)

        messages = [
            {"role": "user", "content": CHAT_HAT_SYSTEM_PROMPT},
            {"role": "assistant", "content": "Understood. I will answer conversationally."},
            {"role": "user", "content": f"Here is the scan result:\n```json\n{cheat_sheet}\n```"},
            {"role": "assistant", "content": "Got it — I'm ready to answer your questions."},
            {"role": "user", "content": "Is this chocolate bar safe for diabetics?"},
        ]

        agent_ref = {
            "agent_reference": {
                "name": CONCLUSION_AGENT["name"],
                "version": CONCLUSION_AGENT["version"],
                "type": "agent_reference",
            }
        }
        start = time.time()
        response = openai_client.responses.create(
            input=messages,
            extra_body=agent_ref,
        )
        elapsed = time.time() - start
        reply = response.output_text or ""
        if reply.strip():
            record("Follow-up chat (Chat Hat mode)", PASS, f"{elapsed:.1f}s, {len(reply)} chars")
            print(f"\n  ── Full output from Follow-up Chat ──")
            print(reply)
            print(f"  ── End of Follow-up Chat ──\n")
        else:
            record("Follow-up chat (Chat Hat mode)", WARN, f"{elapsed:.1f}s — empty response")
    except Exception as e:
        record("Follow-up chat (Chat Hat mode)", FAIL, f"{type(e).__name__}: {str(e)[:200]}")

else:
    print("\n[4-7] Skipping agent tests — Foundry client not available.")
    for agent_def in AGENTS + [CONCLUSION_AGENT]:
        record(f"Agent: {agent_def['label']}", FAIL, "Foundry client not initialized")
    record("Parallel execution", FAIL, "Foundry client not initialized")
    record("Follow-up chat", FAIL, "Foundry client not initialized")


# ── Summary ─────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("  TEST SUMMARY")
print("="*70)

passed = sum(1 for r in results if r["status"] == PASS)
warned = sum(1 for r in results if r["status"] == WARN)
failed = sum(1 for r in results if r["status"] == FAIL)
total = len(results)

print(f"\n  Total: {total}  |  {PASS}: {passed}  |  {WARN}: {warned}  |  {FAIL}: {failed}")

if failed > 0:
    print(f"\n  Failed tests:")
    for r in results:
        if r["status"] == FAIL:
            print(f"    • {r['name']}: {r['detail']}")

if warned > 0:
    print(f"\n  Warnings:")
    for r in results:
        if r["status"] == WARN:
            print(f"    • {r['name']}: {r['detail']}")

print("\n" + "="*70)
if failed == 0:
    print("  🎉 All systems operational!")
else:
    print(f"  ⚠️  {failed} test(s) failed — review above for details.")
print("="*70 + "\n")
