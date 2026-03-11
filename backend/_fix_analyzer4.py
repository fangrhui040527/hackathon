"""Test CU via SDK with blob URL, then try GPT-4o vision fallback."""
import os, json, base64
from dotenv import load_dotenv
load_dotenv()

from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, ContentSettings
from datetime import datetime, timedelta, timezone

endpoint = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT")
cu_key = os.getenv("AZURE_CONTENT_UNDERSTANDING_KEY")
conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "hackathon")

img_path = "image/40214206-2_1-kelloggs-original-potato-crisps.webp"

# Generate SAS URL for the image
print("=== Generating blob SAS URL ===")
blob_service = BlobServiceClient.from_connection_string(conn_str)
container_client = blob_service.get_container_client(container_name)
blob_name = "cu_test/kelloggs_test.webp"
with open(img_path, "rb") as f:
    container_client.upload_blob(blob_name, f, overwrite=True,
                                 content_settings=ContentSettings(content_type="image/webp"))

account_name = blob_service.account_name
account_key = conn_str.split("AccountKey=")[1].split(";")[0]
sas_token = generate_blob_sas(
    account_name=account_name, container_name=container_name, blob_name=blob_name,
    account_key=account_key, permission=BlobSasPermissions(read=True),
    expiry=datetime.now(timezone.utc) + timedelta(hours=1),
)
blob_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
print(f"Blob URL ready")

# Test 1: SDK begin_analyze_from_url
print("\n=== Test: SDK begin_analyze_from_url ===")
cu_client = ContentUnderstandingClient(endpoint=endpoint, credential=AzureKeyCredential(cu_key))
try:
    poller = cu_client.begin_analyze(analyzer_id="HealthLens", input_source={"kind": "url", "url": blob_url})
    result = poller.result()
    raw = result.as_dict() if hasattr(result, "as_dict") else result
    print(json.dumps(raw, indent=2, default=str))
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

# Test 2: Try begin_analyze with base64
print("\n=== Test: SDK begin_analyze with base64 ===")
try:
    with open(img_path, "rb") as f:
        img_bytes = f.read()
    b64 = base64.b64encode(img_bytes).decode()
    poller = cu_client.begin_analyze(
        analyzer_id="HealthLens",
        input_source={"kind": "base64", "data": b64, "mimeType": "image/webp"}
    )
    result = poller.result()
    raw = result.as_dict() if hasattr(result, "as_dict") else result
    print(json.dumps(raw, indent=2, default=str))
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

# Test 3: SDK begin_analyze_binary (what the app currently uses)
print("\n=== Test: SDK begin_analyze_binary ===")
try:
    with open(img_path, "rb") as f:
        img_bytes = f.read()
    poller = cu_client.begin_analyze_binary(
        analyzer_id="HealthLens", binary_input=img_bytes, content_type="image/webp"
    )
    result = poller.result()
    raw = result.as_dict() if hasattr(result, "as_dict") else result
    contents = raw.get("contents", [])
    print(f"Contents count: {len(contents)}")
    if contents:
        print(json.dumps(raw, indent=2, default=str))
    else:
        print("Empty contents (same issue)")
        print(f"Full response: {json.dumps(raw, indent=2, default=str)}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
