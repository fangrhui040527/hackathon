"""
content_understanding.py
Sends food images to Azure Content Understanding for structured analysis,
then uploads the result JSON to Azure Blob Storage.

When the Azure Content Understanding service is not configured, provides
a manual-input fallback so the rest of the pipeline can still run.
"""

import os
import json
import time
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

ENDPOINT = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT")
API_KEY = os.getenv("AZURE_CONTENT_UNDERSTANDING_KEY")
ANALYZER_ID = os.getenv("AZURE_CONTENT_UNDERSTANDING_ANALYZER_ID", "food-analyzer")
API_VERSION = "2024-12-01-preview"


TIMEOUT = 30  # seconds for HTTP requests


def is_service_configured() -> bool:
    """Check whether Azure Content Understanding is configured."""
    return bool(ENDPOINT and API_KEY)


def analyze_food_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """
    Send a food image to Azure Content Understanding and return structured food data.

    Args:
        image_bytes: Raw bytes of the food image.
        mime_type: MIME type of the image (e.g. image/jpeg, image/png, image/webp).

    Returns:
        dict with extracted food information (name, ingredients, nutrition, etc.)

    Raises:
        ValueError: If ENDPOINT or API_KEY env vars are not configured.
        RuntimeError: If the API request or analysis fails.
    """
    if not is_service_configured():
        raise ValueError(
            "AZURE_CONTENT_UNDERSTANDING_ENDPOINT and AZURE_CONTENT_UNDERSTANDING_KEY "
            "must be set in .env. Use --manual-json to provide food data directly."
        )

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    url = (
        f"{ENDPOINT}/contentunderstanding/analyzers/{ANALYZER_ID}"
        f":analyze?api-version={API_VERSION}"
    )

    headers = {
        "Ocp-Apim-Subscription-Key": API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "content": {
            "data": image_b64,
            "mimeType": mime_type,
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.ConnectionError as e:
        raise RuntimeError(f"Content Understanding service unreachable: {e}") from e
    except requests.Timeout:
        raise RuntimeError(f"Content Understanding request timed out after {TIMEOUT}s")
    except requests.HTTPError as e:
        raise RuntimeError(f"Content Understanding HTTP error: {e.response.status_code} — {e.response.text[:300]}") from e

    # Handle async (202) vs sync response
    if response.status_code == 202:
        operation_url = response.headers.get("Operation-Location")
        if operation_url:
            return _poll_for_result(operation_url, headers)

    return response.json()


def _poll_for_result(operation_url: str, headers: dict, max_wait: int = 120) -> dict:
    """Poll an async operation until it completes."""
    elapsed = 0
    interval = 3

    while elapsed < max_wait:
        time.sleep(interval)
        elapsed += interval
        resp = requests.get(operation_url, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        result = resp.json()
        status = result.get("status", "").lower()

        if status in ("succeeded", "completed"):
            return result.get("result", result)
        elif status in ("failed", "error"):
            raise RuntimeError(f"Content Understanding analysis failed: {result}")

    raise TimeoutError(f"Content Understanding analysis timed out after {max_wait}s")
