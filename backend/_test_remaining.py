"""Test the remaining agents: foodchemist, fitnessCoach, healthSpecialist."""
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

cred = DefaultAzureCredential()
client = AIProjectClient(endpoint=os.environ["AZURE_AI_FOUNDRY_ENDPOINT"], credential=cred)
oc = client.get_openai_client()

agents = [
    {"name": "foodchemist-agent", "version": "3"},
    {"name": "fitnessCoach-agent", "version": "4"},
    {"name": "healthSpecialist-agent", "version": "3"},
]

for a in agents:
    print(f"Testing {a['name']} v{a['version']}...")
    try:
        r = oc.responses.create(
            input=[{"role": "user", "content": "Say hello in 5 words."}],
            extra_body={"agent_reference": {"name": a["name"], "version": a["version"], "type": "agent_reference"}},
        )
        print(f"  Response: {r.output_text[:200]}")
        print(f"  {a['name']}: OK")
    except Exception as e:
        print(f"  {a['name']} ERROR: {type(e).__name__}: {e}")
    print()

print("All agent tests complete.")
