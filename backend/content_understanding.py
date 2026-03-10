"""
content_understanding.py
Sends food images to Azure Content Understanding for structured analysis,
then uploads the result JSON to Azure Blob Storage.

When the Azure Content Understanding service is not configured, provides
a manual-input fallback so the rest of the pipeline can still run.
"""

import os
from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

load_dotenv()

ENDPOINT = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT")
API_KEY = os.getenv("AZURE_CONTENT_UNDERSTANDING_KEY")
ANALYZER_ID = os.getenv("AZURE_CONTENT_UNDERSTANDING_ANALYZER_ID", "HealthLens")


def is_service_configured() -> bool:
    """Check whether Azure Content Understanding is configured."""
    return bool(ENDPOINT and API_KEY)


def _get_client() -> ContentUnderstandingClient:
    """Create and return a ContentUnderstandingClient instance."""
    return ContentUnderstandingClient(
        endpoint=ENDPOINT,
        credential=AzureKeyCredential(API_KEY),
    )


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

    client = _get_client()
    try:
        poller = client.begin_analyze_binary(
            analyzer_id=ANALYZER_ID,
            binary_input=image_bytes,
            content_type=mime_type,
        )
        result = poller.result()
        raw = result.as_dict() if hasattr(result, "as_dict") else result
    except Exception as e:
        raise RuntimeError(f"Content Understanding analysis failed: {e}") from e

    return _flatten_cu_response(raw)


def _extract_field_value(field: dict):
    """Extract the actual value from an Azure CU field object (e.g. {"type":"string","valueString":"Tomato"})."""
    if not isinstance(field, dict):
        return field
    field_type = field.get("type", "")
    # Try standard Azure CU value keys
    for key in ("valueString", "valueNumber", "valueInteger", "valueBoolean",
                "valueDate", "valueTime", "valueArray", "valueObject"):
        if key in field:
            val = field[key]
            # Recursively flatten valueObject
            if key == "valueObject" and isinstance(val, dict):
                return {k: _extract_field_value(v) for k, v in val.items()}
            # Recursively flatten valueArray
            if key == "valueArray" and isinstance(val, list):
                return [_extract_field_value(item) for item in val]
            return val
    # If it has a "value" key directly
    if "value" in field:
        return field["value"]
    # If it has "content" (markdown-based fields)
    if "content" in field:
        return field["content"]
    return field


def _flatten_cu_response(raw: dict) -> dict:
    """
    Flatten Azure Content Understanding response into a simple dict.

    Azure CU returns nested structures like:
      { "contents": [{ "fields": { "product_name": { "type": "string", "valueString": "Tomato" } } }] }

    This function extracts the actual values into a flat dict like:
      { "product_name": "Tomato", ... }
    """
    if not isinstance(raw, dict):
        return raw

    # If the response already has a simple 'product_name' at top level, it's already flat
    if "product_name" in raw or "name" in raw or "food_name" in raw:
        return raw

    # Try to extract from "contents" → first item → "fields"
    contents = raw.get("contents", [])
    if isinstance(contents, list) and contents:
        first_content = contents[0]
        if isinstance(first_content, dict):
            fields = first_content.get("fields", {})
            if isinstance(fields, dict) and fields:
                flat = {}
                for key, value in fields.items():
                    flat[key] = _extract_field_value(value)
                print(f"  [ContentUnderstanding] Parsed product: {flat.get('product_name', flat.get('name', 'N/A'))}")
                return flat

            # Some analyzers put data under "result" inside contents
            result_data = first_content.get("result", {})
            if isinstance(result_data, dict) and result_data:
                flat = {}
                for key, value in result_data.items():
                    flat[key] = _extract_field_value(value)
                return flat

    # Try "result" → "contents" → "fields" (double nested)
    inner_result = raw.get("result", {})
    if isinstance(inner_result, dict):
        return _flatten_cu_response(inner_result)

    # Try "fields" directly at top level
    fields = raw.get("fields", {})
    if isinstance(fields, dict) and fields:
        flat = {}
        for key, value in fields.items():
            flat[key] = _extract_field_value(value)
        return flat

    # Last resort: return raw (may already be flat from a different API version)
    print(f"  [ContentUnderstanding] Warning: Could not parse response structure. Keys: {list(raw.keys())}")
    return raw
