"""Recreate HealthLens analyzer using prebuilt-document base (has native OCR)."""
import os, json, requests, time
from dotenv import load_dotenv
load_dotenv()

endpoint = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT")
key = os.getenv("AZURE_CONTENT_UNDERSTANDING_KEY")
api_version = "2025-11-01"
headers = {"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/json"}

def analyzer_url(name):
    return f"{endpoint}/contentunderstanding/analyzers/{name}?api-version={api_version}"

# Delete old analyzer
print("Deleting old HealthLens analyzer...")
r = requests.delete(analyzer_url("HealthLens"), headers=headers)
print(f"Delete: {r.status_code}")
time.sleep(2)

# Create new analyzer with prebuilt-document base (has OCR + layout built-in)
body = {
    "description": "Food product label analyzer with OCR",
    "baseAnalyzerId": "prebuilt-document",
    "config": {
        "returnDetails": True,
        "enableOcr": True,
        "enableLayout": True,
        "enableFigureDescription": True,
    },
    "models": {"completion": "gpt-4.1"},
    "fieldSchema": {
        "fields": {
            "product_name": {
                "type": "string",
                "method": "generate",
                "description": "Extract the product title. Include brand name + product name + variant/flavor."
            },
            "brand": {
                "type": "string",
                "method": "generate",
                "description": "Extract the brand or manufacturer name."
            },
            "type": {
                "type": "string",
                "method": "generate",
                "description": "Classify the product: food, beverage, supplement, household, personal_care, medicine, or other."
            },
            "ingredients": {
                "type": "string",
                "method": "generate",
                "description": "Extract the full ingredients list exactly as printed on the label, comma-separated."
            },
            "nutrition": {
                "type": "string",
                "method": "generate",
                "description": "Extract nutrition facts as key-value pairs. Format: 'Calories: 150, Total Fat: 8g, Saturated Fat: 2.5g, Sodium: 135mg, ...' etc."
            },
            "serving_size": {
                "type": "string",
                "method": "generate",
                "description": "Extract the serving size information (e.g., '1 oz (about 16 crisps)')."
            },
            "claims": {
                "type": "string",
                "method": "generate",
                "description": "Extract any marketing, health, or nutrition claims on the label. One per line."
            },
            "warnings": {
                "type": "string",
                "method": "generate",
                "description": "Extract allergen warnings and caution statements. One per line."
            },
        }
    },
}

print("Creating HealthLens with prebuilt-document base...")
r = requests.put(analyzer_url("HealthLens"), headers=headers, json=body)
print(f"Create: {r.status_code}")
data = r.json()
print(f"enableOcr: {data.get('config', {}).get('enableOcr')}")
print(f"status: {data.get('status')}")
print(json.dumps(data, indent=2))

# Wait for ready status if needed
status = data.get("status")
if status and status != "ready":
    print(f"\nWaiting for analyzer to become ready (current: {status})...")
    for i in range(30):
        time.sleep(3)
        r = requests.get(analyzer_url("HealthLens"), headers=headers)
        d = r.json()
        s = d.get("status")
        print(f"  [{i+1}] status: {s}")
        if s == "ready":
            break

# Now test the analyzer with the image
print("\n=== Testing analyzer with Kellogg's image ===")
img_path = "image/40214206-2_1-kelloggs-original-potato-crisps.webp"
with open(img_path, "rb") as f:
    image_bytes = f.read()

analyze_url = f"{endpoint}/contentunderstanding/analyzers/HealthLens:analyze?api-version={api_version}"
r = requests.post(
    analyze_url,
    headers={"Ocp-Apim-Subscription-Key": key, "Content-Type": "image/webp"},
    data=image_bytes,
)
print(f"Analyze POST: {r.status_code}")

if r.status_code == 202:
    # Poll for result
    operation_url = r.headers.get("Operation-Location")
    print(f"Polling: {operation_url}")
    for i in range(60):
        time.sleep(3)
        r2 = requests.get(operation_url, headers={"Ocp-Apim-Subscription-Key": key})
        result = r2.json()
        status = result.get("status")
        print(f"  [{i+1}] status: {status}")
        if status in ("succeeded", "completed", "failed"):
            print(json.dumps(result, indent=2))
            break
elif r.status_code == 200:
    print(json.dumps(r.json(), indent=2))
else:
    print(r.text)
