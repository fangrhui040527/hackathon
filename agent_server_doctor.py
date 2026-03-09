"""
agent_server_doctor.py — Doctor Agent (mounted at /agent/doctor on port 8000)
Dr. Chen: Medical-grade analysis, drug-food interactions, clinical nutrition.
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent_framework.azure import AzureOpenAIResponsesClient
import doctor

load_dotenv()

app = FastAPI(title="Doctor Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    task: str


def _get_client() -> AzureOpenAIResponsesClient:
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
    return AzureOpenAIResponsesClient(
        base_url=f"{endpoint}/openai/v1/",
        deployment_name=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
    )


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "Doctor", "port": 8000}


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    client = _get_client()
    agent = doctor.create_agent(client)
    response = await agent.run(req.task)
    return {
        "agent": "Doctor",
        "text": response.text if response and response.text else "",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
