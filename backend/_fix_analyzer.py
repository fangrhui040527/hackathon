"""Recreate HealthLens analyzer with enableOcr=true via REST API."""
import os, json, requests, time
from dotenv import load_dotenv
load_dotenv()

endpoint = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT")
key = os.getenv("AZURE_CONTENT_UNDERSTANDING_KEY")
api_version = "2025-11-01"
base_url = f"{endpoint}/contentunderstanding/analyzers/HealthLens?api-version={api_version}"
headers = {"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/json"}

# Step 1: Delete
print("Deleting old analyzer...")
r = requests.delete(base_url, headers=headers)
print(f"Delete: {r.status_code}")
time.sleep(2)

# Step 2: Create with PUT
body = {
    "description": "Food product label analyzer",
    "baseAnalyzerId": "prebuilt-image",
    "config": {
        "returnDetails": True,
        "enableOcr": True,
        "disableFaceBlurring": False,
    },
    "models": {"completion": "gpt-4.1"},
    "fieldSchema": {
        "fields": {
            "title": {"type": "string", "method": "generate", "description": "Extract the product title including brand, product name, and variant."},
            "type": {"type": "string", "method": "generate", "description": "Classify: food, beverage, supplement, household, personal_care, medicine, or other."},
            "Ingredients": {"type": "string", "method": "generate", "description": "Extract the ingredients list exactly as printed, comma-separated."},
            "Nutrition": {"type": "string", "method": "generate", "description": "Extract nutrition facts as comma-separated key-value pairs."},
            "Claims": {"type": "string", "method": "generate", "description": "Extract marketing or nutrition claims. One per line."},
            "Warnings": {"type": "string", "method": "generate", "description": "Extract allergen warnings and caution statements. One per line."},
            "ContactInfo": {"type": "string", "method": "generate", "description": "Company name, address, phone, website from the label."},
        }
    },
}
print("Creating analyzer with enableOcr=true...")
r = requests.put(base_url, headers=headers, json=body)
print(f"Create: {r.status_code}")
data = r.json()
ocr_val = data.get("config", {}).get("enableOcr")
print(f"enableOcr in response: {ocr_val}")
print(json.dumps(data, indent=2))

# Step 3: If still false, try PATCH
if not ocr_val:
    print("\nOCR still false. Trying PATCH...")
    r = requests.patch(base_url, headers=headers, json={"config": {"enableOcr": True}})
    print(f"PATCH: {r.status_code}")
    if r.status_code < 300:
        print(json.dumps(r.json(), indent=2))

# Step 4: Verify
print("\n=== Verifying ===")
r = requests.get(base_url, headers=headers)
data = r.json()
print(f"enableOcr: {data.get('config', {}).get('enableOcr')}")
print(f"status: {data.get('status')}")
