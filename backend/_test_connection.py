"""Quick connection test for HealthLens AI backend."""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

print("=== ENV CHECK ===")
env_keys = [
    "AZURE_AI_FOUNDRY_ENDPOINT",
    "AZURE_CONTENT_UNDERSTANDING_ENDPOINT",
    "AZURE_CONTENT_UNDERSTANDING_KEY",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "AZURE_STORAGE_CONNECTION_STRING",
]
for k in env_keys:
    val = os.environ.get(k)
    if val and ("KEY" in k or "API_KEY" in k or "CONNECTION" in k):
        print(f"  {k}: SET ({len(val)} chars)")
    elif val:
        print(f"  {k}: {val}")
    else:
        print(f"  {k}: NOT SET")

print("\n=== Testing Azure AI Foundry SDK connection ===")
try:
    from azure.identity import DefaultAzureCredential
    from azure.ai.projects import AIProjectClient

    cred = DefaultAzureCredential()
    endpoint = os.environ["AZURE_AI_FOUNDRY_ENDPOINT"]
    client = AIProjectClient(endpoint=endpoint, credential=cred)
    openai_client = client.get_openai_client()
    print(f"  AIProjectClient created OK (endpoint: {endpoint})")
    print(f"  OpenAI client type: {type(openai_client).__name__}")
except Exception as e:
    print(f"  ERROR creating client: {type(e).__name__}: {e}")
    sys.exit(1)

print("\n=== Testing Foundry Agent: doctor-agent ===")
try:
    resp = openai_client.responses.create(
        input=[{"role": "user", "content": "Say hello in 5 words."}],
        extra_body={
            "agent_reference": {
                "name": "doctor-agent",
                "version": "11",
                "type": "agent_reference",
            }
        },
    )
    print(f"  Response: {resp.output_text[:200]}")
    print("  doctor-agent: OK")
except Exception as e:
    print(f"  doctor-agent ERROR: {type(e).__name__}: {e}")

print("\n=== Testing Foundry Agent: nutritionist-agent ===")
try:
    resp = openai_client.responses.create(
        input=[{"role": "user", "content": "Say hello in 5 words."}],
        extra_body={
            "agent_reference": {
                "name": "nutritionist-agent",
                "version": "4",
                "type": "agent_reference",
            }
        },
    )
    print(f"  Response: {resp.output_text[:200]}")
    print("  nutritionist-agent: OK")
except Exception as e:
    print(f"  nutritionist-agent ERROR: {type(e).__name__}: {e}")

print("\n=== Testing Foundry Agent: conclusionAdvisor-agent ===")
try:
    resp = openai_client.responses.create(
        input=[{"role": "user", "content": "Say hello in 5 words."}],
        extra_body={
            "agent_reference": {
                "name": "conclusionAdvisor-agent",
                "version": "3",
                "type": "agent_reference",
            }
        },
    )
    print(f"  Response: {resp.output_text[:200]}")
    print("  conclusionAdvisor-agent: OK")
except Exception as e:
    print(f"  conclusionAdvisor-agent ERROR: {type(e).__name__}: {e}")

print("\n=== Testing Content Understanding ===")
try:
    from content_understanding import is_service_configured
    if is_service_configured():
        print("  Content Understanding: CONFIGURED")
    else:
        print("  Content Understanding: NOT CONFIGURED (missing endpoint or key)")
except Exception as e:
    print(f"  Content Understanding ERROR: {type(e).__name__}: {e}")

print("\n=== All checks complete ===")
