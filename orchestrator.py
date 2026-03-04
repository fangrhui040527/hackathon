"""
orchestrator.py
Runs all 5 specialist agents in PARALLEL using Microsoft Agent Framework.

Flow:
1. All 5 agents receive the same grounded food data prompt simultaneously
2. Each agent independently produces their specialist analysis
3. All 5 responses are collected and returned for the conclusion agent to synthesize
"""

import asyncio
import os
import json

from agent_framework import ChatAgent, ChatMessage
from agent_framework.azure import AzureOpenAIResponsesClient
from dotenv import load_dotenv

# Import agent creators
import nutritionist_agent
import health_agent
import fitness_agent
import doctor as doctor_agent
import chemi_agent

# Import grounding pipeline
from grounding_pipeline import format_grounding_for_agents

load_dotenv()


def _get_client() -> AzureOpenAIResponsesClient:
    """Create the Azure OpenAI Responses client for all agents."""
    return AzureOpenAIResponsesClient(
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
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


async def _run_agent(agent: ChatAgent, task: str, client: AzureOpenAIResponsesClient) -> ChatMessage:
    """Run a single agent and return its response message."""
    response = await agent.run(task)
    return response


async def run_all_agents(food_data: dict, enriched_data: dict = None) -> tuple[list[ChatMessage], object]:
    """
    Run all 5 specialist agents in parallel on the same grounded data.

    Each agent independently analyzes the food item from their specialist perspective.
    All 5 run concurrently via asyncio.gather().

    Args:
        food_data: Structured food data from Content Understanding.
        enriched_data: Grounded/enriched food data from the grounding pipeline.

    Returns:
        tuple: (list of 5 ChatMessages, client)
    """
    client = _get_client()

    # Create all 5 specialist agents
    agents = [
        doctor_agent.create_agent(client),
        nutritionist_agent.create_agent(client),
        chemi_agent.create_agent(client),
        fitness_agent.create_agent(client),
        health_agent.create_agent(client),
    ]

    # Build the task prompt
    task = _build_task_prompt(food_data, enriched_data)

    # Run all 5 agents in parallel
    responses = await asyncio.gather(
        *[_run_agent(agent, task, client) for agent in agents]
    )

    return list(responses), client
