"""
content_understanding.py
Sends food images to Azure Content Understanding for structured analysis,
then uploads the result JSON to Azure Blob Storage.

When the Azure Content Understanding service is not configured, provides
a manual-input fallback so the rest of the pipeline can still run.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

ENDPOINT = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT")
API_KEY = os.getenv("AZURE_CONTENT_UNDERSTANDING_KEY")
ANALYZER_ID = os.getenv("AZURE_CONTENT_UNDERSTANDING_ANALYZER_ID", "HealthLens")

CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "hackathon")


def is_service_configured() -> bool:
    """Check whether Azure Content Understanding is configured."""
    return bool(ENDPOINT and API_KEY)


def _upload_image_to_blob(image_bytes: bytes, mime_type: str) -> str:
    """Upload image to Azure Blob Storage and return a SAS URL valid for 1 hour."""
    from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, ContentSettings

    blob_service = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    container_client = blob_service.get_container_client(CONTAINER_NAME)
    try:
        container_client.create_container()
    except Exception:
        pass

    ext = mime_type.split("/")[-1].replace("jpeg", "jpg")
    blob_name = f"cu_images/{uuid.uuid4().hex[:8]}.{ext}"
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(
        image_bytes,
        overwrite=True,
        content_settings=ContentSettings(content_type=mime_type),
    )

    account_name = blob_service.account_name
    account_key = blob_service.credential.account_key
    sas_token = generate_blob_sas(
        account_name=account_name,
        container_name=CONTAINER_NAME,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    return f"https://{account_name}.blob.core.windows.net/{CONTAINER_NAME}/{blob_name}?{sas_token}"


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

    from azure.ai.contentunderstanding import ContentUnderstandingClient
    from azure.ai.contentunderstanding.models import AnalysisInput
    from azure.core.credentials import AzureKeyCredential

    # Upload image to blob storage and get a SAS URL
    image_url = _upload_image_to_blob(image_bytes, mime_type)

    client = ContentUnderstandingClient(
        endpoint=ENDPOINT,
        credential=AzureKeyCredential(API_KEY),
    )

    try:
        result = client.begin_analyze(
            analyzer_id=ANALYZER_ID,
            inputs=[AnalysisInput(url=image_url)],
        ).result()
        raw = result.as_dict()
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
