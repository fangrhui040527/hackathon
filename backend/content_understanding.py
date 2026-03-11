"""
content_understanding.py
Sends food images to Azure Content Understanding for structured analysis.

When CU returns empty results (e.g. product photos without readable text),
falls back to GPT-4o vision for extraction.
"""

import base64
import json
import os
from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

ENDPOINT = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT")
API_KEY = os.getenv("AZURE_CONTENT_UNDERSTANDING_KEY")
ANALYZER_ID = os.getenv("AZURE_CONTENT_UNDERSTANDING_ANALYZER_ID", "HealthLens")

# GPT-4o vision fallback config
OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")


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
    Falls back to GPT-4o vision if CU returns empty results.
    """
    if not is_service_configured():
        raise ValueError(
            "AZURE_CONTENT_UNDERSTANDING_ENDPOINT and AZURE_CONTENT_UNDERSTANDING_KEY "
            "must be set in .env. Use --manual-json to provide food data directly."
        )

    # Try CU first
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
        print(f"  [ContentUnderstanding] CU failed: {e}")
        raw = None

    # Check if CU returned usable data
    if raw:
        flat = _flatten_cu_response(raw)
        # Verify it's not just the raw response with empty contents
        has_data = isinstance(flat, dict) and any(
            flat.get(k) for k in ("product_name", "name", "title", "ingredients", "Ingredients")
        )
        if has_data:
            return flat
        print("  [ContentUnderstanding] CU returned empty/unusable data, falling back to GPT-4o vision...")

    # Fallback: GPT-4o vision extraction
    return _analyze_with_vision(image_bytes, mime_type)


def _analyze_with_vision(image_bytes: bytes, mime_type: str) -> dict:
    """Use GPT-4o vision to extract food label data from an image."""
    if not OPENAI_ENDPOINT or not OPENAI_KEY:
        raise RuntimeError("Azure OpenAI not configured for vision fallback.")

    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    data_uri = f"data:{mime_type};base64,{b64_image}"

    client = AzureOpenAI(
        azure_endpoint=OPENAI_ENDPOINT,
        api_key=OPENAI_KEY,
        api_version="2024-12-01-preview",
    )

    system_prompt = (
        "You are a food label analysis expert. Analyze the food product image and extract "
        "structured data. Respond ONLY with valid JSON (no markdown fences) using these keys:\n"
        '{\n'
        '  "product_name": "Brand + Product Name + Variant",\n'
        '  "brand": "Brand name",\n'
        '  "type": "food|beverage|supplement|other",\n'
        '  "ingredients": "comma-separated ingredients list",\n'
        '  "nutrition": "Calories: X, Total Fat: Xg, Saturated Fat: Xg, Sodium: Xmg, '
        'Total Carbohydrate: Xg, Sugars: Xg, Protein: Xg, Fiber: Xg",\n'
        '  "serving_size": "serving size info",\n'
        '  "claims": "health/marketing claims, one per line",\n'
        '  "warnings": "allergen warnings"\n'
        '}\n'
        "If a field is not visible in the image, use your knowledge of the product to provide "
        "likely values. Always try to identify the product and give useful data."
    )

    response = client.chat.completions.create(
        model=OPENAI_DEPLOYMENT,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text": "Analyze this food product image and extract all label information:"},
                {"type": "image_url", "image_url": {"url": data_uri, "detail": "high"}},
            ]},
        ],
        temperature=0.1,
        max_tokens=1500,
    )

    text = response.choices[0].message.content.strip()
    # Strip markdown fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        print(f"  [Vision] Failed to parse JSON: {text[:200]}")
        data = {"product_name": "Unknown Product", "raw_response": text}

    print(f"  [Vision] Extracted product: {data.get('product_name', 'N/A')}")
    return data


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

            # Try markdown/content text from CU (extract structured data via text)
            markdown = first_content.get("markdown") or first_content.get("content") or ""
            if markdown and len(markdown) > 20:
                print(f"  [ContentUnderstanding] Found markdown content ({len(markdown)} chars), parsing...")
                return {"raw_text": markdown}

        # Try across all contents for fields
        for content_item in contents:
            if isinstance(content_item, dict):
                fields = content_item.get("fields", {})
                if isinstance(fields, dict) and fields:
                    flat = {}
                    for key, value in fields.items():
                        flat[key] = _extract_field_value(value)
                    print(f"  [ContentUnderstanding] Parsed product from content item: {flat.get('product_name', flat.get('name', 'N/A'))}")
                    return flat

    # Try "result" → "contents" → "fields" (double nested)
    inner_result = raw.get("result")
    if isinstance(inner_result, dict) and inner_result:
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
