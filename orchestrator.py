"""
orchestrator.py
Coordinates all 5 specialist agents mounted on the same server (port 8000).

All agents are accessible via path-based routing:
  - Doctor agent:       http://localhost:8000/agent/doctor
  - Fitness agent:      http://localhost:8000/agent/fitness
  - Health agent:       http://localhost:8000/agent/health
  - Nutritionist agent: http://localhost:8000/agent/nutritionist
  - Chemi agent:        http://localhost:8000/agent/chemi

This orchestrator calls all 5 in parallel via HTTP and collects responses.
"""

import asyncio
import os
import json

import httpx
from agent_framework.azure import AzureOpenAIResponsesClient
from dotenv import load_dotenv

from grounding_pipeline import format_grounding_for_agents

load_dotenv()

# Agent microservice endpoints (order matches AGENT_NAMES in server.py)
AGENT_SERVICES = [
    ("Doctor",          "http://localhost:8000/agent/doctor"),
    ("Nutritionist",    "http://localhost:8000/agent/nutritionist"),
    ("FoodChemist",     "http://localhost:8000/agent/chemi"),
    ("FitnessCoach",    "http://localhost:8000/agent/fitness"),
    ("HealthSpecialist","http://localhost:8000/agent/health"),
]


class AgentResponse:
    """Lightweight wrapper matching the ChatMessage interface used by conclusion_agent."""
    def __init__(self, text: str, author_name: str):
        self.text = text
        self.author_name = author_name
        self.role = author_name


def _get_client() -> AzureOpenAIResponsesClient:
    """Create the Azure OpenAI Responses client (used by the conclusion agent)."""
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
    return AzureOpenAIResponsesClient(
        base_url=f"{endpoint}/openai/v1/",
        deployment_name=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
    )


def _build_task_prompt(food_data: dict, enriched_data: dict = None) -> str:
    """Build the analysis prompt with grounding data."""
    if enriched_data:
        grounding_text = format_grounding_for_agents(enriched_data)
        return (
            "Analyze the following food item using the GROUNDED DATA provided below. "
            "Provide your specialist analysis based on your domain expertise. "
            "Reference the grounding data relevant to your field and cite specific sources.\n\n"
            "The grounding data includes pre-analyzed results from: USDA FoodData Central, "
            "FooDB, Open Food Facts, FDA (food & drug), DDInter, IARC, NOVA, "
            "glycemic index database, drug-food interaction database, NIH DSLB, "
            "and Blob Storage-backed knowledge databases.\n\n"
            f"{grounding_text}"
        )
    else:
        food_json = json.dumps(food_data, indent=2, ensure_ascii=False)
        return (
            "Analyze the following food item. Provide your specialized perspective "
            "based on your domain expertise.\n\n"
            f"Food Data (extracted from photo):\n```json\n{food_json}\n```"
        )


async def _call_agent_service(
    http_client: httpx.AsyncClient, name: str, url: str, task: str
) -> AgentResponse:
    """Call a single agent microservice and return its response."""
    try:
        resp = await http_client.post(
            f"{url}/analyze", json={"task": task}, timeout=120.0
        )
        resp.raise_for_status()
        data = resp.json()
        return AgentResponse(text=data.get("text", ""), author_name=name)
    except Exception as e:
        print(f"  [Orchestrator] Agent {name} ({url}) failed: {e}")
        return AgentResponse(
            text=f"Agent {name} unavailable: {str(e)}", author_name=name
        )


async def run_all_agents(food_data: dict, enriched_data: dict = None) -> tuple[list, object]:
    """
    Call all 5 specialist agent microservices in parallel.

    Args:
        food_data: Structured food data from Content Understanding.
        enriched_data: Grounded/enriched food data from the grounding pipeline.

    Returns:
        tuple: (list of 5 AgentResponses, AzureOpenAI client for conclusion agent)
    """
    client = _get_client()
    task = _build_task_prompt(food_data, enriched_data)

    async with httpx.AsyncClient() as http_client:
        coros = [
            _call_agent_service(http_client, name, url, task)
            for name, url in AGENT_SERVICES
        ]
        responses = await asyncio.gather(*coros)

    return list(responses), client
