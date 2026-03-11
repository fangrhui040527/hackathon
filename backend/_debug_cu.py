"""Debug: inspect raw Content Understanding response structure."""
import json, os, sys
from dotenv import load_dotenv
load_dotenv()

from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.core.credentials import AzureKeyCredential

ENDPOINT = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT")
API_KEY = os.getenv("AZURE_CONTENT_UNDERSTANDING_KEY")
ANALYZER_ID = os.getenv("AZURE_CONTENT_UNDERSTANDING_ANALYZER_ID", "HealthLens")

img_path = sys.argv[1] if len(sys.argv) > 1 else "image/40214206-2_1-kelloggs-original-potato-crisps.webp"
mime = "image/webp" if img_path.endswith(".webp") else "image/jpeg"

print(f"Endpoint: {ENDPOINT}")
print(f"Analyzer: {ANALYZER_ID}")
print(f"Image: {img_path} ({os.path.getsize(img_path)} bytes)")
print()

client = ContentUnderstandingClient(endpoint=ENDPOINT, credential=AzureKeyCredential(API_KEY))

with open(img_path, "rb") as f:
    image_bytes = f.read()

poller = client.begin_analyze_binary(analyzer_id=ANALYZER_ID, binary_input=image_bytes, content_type=mime)
result = poller.result()
raw = result.as_dict() if hasattr(result, "as_dict") else result

print("=== RAW CU RESPONSE ===")
print(json.dumps(raw, indent=2, ensure_ascii=False, default=str))
