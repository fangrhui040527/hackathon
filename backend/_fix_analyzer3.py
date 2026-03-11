"""Try analyzing via blob URL + prebuilt-image base, and also test direct binary with prebuilt-image."""
import os, json, requests, time, uuid
from dotenv import load_dotenv
load_dotenv()

from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta, timezone

endpoint = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT")
key = os.getenv("AZURE_CONTENT_UNDERSTANDING_KEY")
conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "hackathon")
api_version = "2025-11-01"
headers_json = {"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/json"}

def analyzer_url(name):
    return f"{endpoint}/contentunderstanding/analyzers/{name}?api-version={api_version}"

# Step 1: Recreate as prebuilt-image
print("=== Recreating analyzer as prebuilt-image ===")
requests.delete(analyzer_url("HealthLens"), headers=headers_json)
time.sleep(1)

body = {
    "description": "Food product label analyzer",
    "baseAnalyzerId": "prebuilt-image",
    "config": {"returnDetails": True},
    "models": {"completion": "gpt-4.1"},
    "fieldSchema": {
        "fields": {
            "product_name": {"type": "string", "method": "generate", "description": "What is the product name including the brand? Extract from the image."},
            "brand": {"type": "string", "method": "generate", "description": "What brand manufactures this product?"},
            "type": {"type": "string", "method": "generate", "description": "What type of product is this? food, beverage, supplement, etc."},
            "ingredients": {"type": "string", "method": "generate", "description": "List all visible ingredients, comma-separated."},
            "nutrition": {"type": "string", "method": "generate", "description": "Extract visible nutrition facts as key: value pairs, comma-separated."},
            "serving_size": {"type": "string", "method": "generate", "description": "What is the serving size?"},
            "claims": {"type": "string", "method": "generate", "description": "What health or marketing claims are visible on the package?"},
            "warnings": {"type": "string", "method": "generate", "description": "What allergen or safety warnings are visible?"},
        }
    },
}
r = requests.put(analyzer_url("HealthLens"), headers=headers_json, json=body)
print(f"Create: {r.status_code}, status: {r.json().get('status')}")

# Wait for ready
for i in range(20):
    time.sleep(2)
    r = requests.get(analyzer_url("HealthLens"), headers=headers_json)
    if r.json().get("status") == "ready":
        print(f"Analyzer ready after {(i+1)*2}s")
        break

# Step 2: Upload image to blob and get SAS URL
print("\n=== Uploading image to blob storage ===")
blob_service = BlobServiceClient.from_connection_string(conn_str)
container_client = blob_service.get_container_client(container_name)
blob_name = f"cu_test/{uuid.uuid4().hex[:8]}.webp"
img_path = "image/40214206-2_1-kelloggs-original-potato-crisps.webp"

from azure.storage.blob import ContentSettings
with open(img_path, "rb") as f:
    container_client.upload_blob(blob_name, f, overwrite=True, content_settings=ContentSettings(content_type="image/webp"))
print(f"Uploaded to: {blob_name}")

# Generate SAS URL
account_name = blob_service.account_name
account_key = conn_str.split("AccountKey=")[1].split(";")[0]
sas_token = generate_blob_sas(
    account_name=account_name,
    container_name=container_name,
    blob_name=blob_name,
    account_key=account_key,
    permission=BlobSasPermissions(read=True),
    expiry=datetime.now(timezone.utc) + timedelta(hours=1),
)
blob_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
print(f"SAS URL generated (length: {len(blob_url)})")

# Step 3: Test with URL-based analysis
print("\n=== Test 1: Analyze via URL ===")
analyze_url = f"{endpoint}/contentunderstanding/analyzers/HealthLens:analyze?api-version={api_version}"
r = requests.post(
    analyze_url,
    headers=headers_json,
    json={"url": blob_url},
)
print(f"Analyze (URL): {r.status_code}")
if r.status_code == 202:
    op_url = r.headers.get("Operation-Location")
    print(f"Polling operation...")
    for i in range(60):
        time.sleep(3)
        r2 = requests.get(op_url, headers={"Ocp-Apim-Subscription-Key": key})
        result = r2.json()
        status = result.get("status")
        print(f"  [{i+1}] {status}")
        if status in ("succeeded", "completed", "failed"):
            print(json.dumps(result, indent=2))
            break
else:
    print(r.text)

# Step 4: Test with binary analysis
print("\n=== Test 2: Analyze via binary ===")
with open(img_path, "rb") as f:
    img_bytes = f.read()
r = requests.post(
    analyze_url,
    headers={"Ocp-Apim-Subscription-Key": key, "Content-Type": "image/webp"},
    data=img_bytes,
)
print(f"Analyze (binary): {r.status_code}")
if r.status_code == 202:
    op_url = r.headers.get("Operation-Location")
    print(f"Polling operation...")
    for i in range(60):
        time.sleep(3)
        r2 = requests.get(op_url, headers={"Ocp-Apim-Subscription-Key": key})
        result = r2.json()
        status = result.get("status")
        print(f"  [{i+1}] {status}")
        if status in ("succeeded", "completed", "failed"):
            print(json.dumps(result, indent=2))
            break
else:
    print(r.text)

# Step 5: Also try with JPEG version
print("\n=== Test 3: Analyze JPEG via binary ===")
jpg_path = "image/test_kelloggs.jpg"
if os.path.exists(jpg_path):
    with open(jpg_path, "rb") as f:
        jpg_bytes = f.read()
    r = requests.post(
        analyze_url,
        headers={"Ocp-Apim-Subscription-Key": key, "Content-Type": "image/jpeg"},
        data=jpg_bytes,
    )
    print(f"Analyze (JPEG binary): {r.status_code}")
    if r.status_code == 202:
        op_url = r.headers.get("Operation-Location")
        print(f"Polling operation...")
        for i in range(60):
            time.sleep(3)
            r2 = requests.get(op_url, headers={"Ocp-Apim-Subscription-Key": key})
            result = r2.json()
            status = result.get("status")
            print(f"  [{i+1}] {status}")
            if status in ("succeeded", "completed", "failed"):
                print(json.dumps(result, indent=2))
                break
    else:
        print(r.text)
