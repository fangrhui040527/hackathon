"""Connectivity check for Azure OpenAI, Blob Storage, and Content Understanding."""
import os
from dotenv import load_dotenv
load_dotenv()

# ── 1. Azure OpenAI ──
print("=" * 50)
print("1. AZURE OPENAI")
print("=" * 50)
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
key = os.getenv("AZURE_OPENAI_API_KEY", "")
deploy = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
if not endpoint or not key:
    print("  [FAIL] Missing AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_KEY in .env")
else:
    print(f"  Endpoint: {endpoint}")
    print(f"  Deployment: {deploy}")
    try:
        import requests
        url = f"{endpoint.rstrip('/')}/openai/deployments/{deploy}/chat/completions?api-version=2024-02-01"
        resp = requests.post(url, headers={"api-key": key, "Content-Type": "application/json"},
            json={"messages": [{"role": "user", "content": "Say hi"}], "max_tokens": 5}, timeout=15)
        if resp.status_code == 200:
            msg = resp.json()["choices"][0]["message"]["content"]
            print(f"  [OK] Connected! Response: {msg}")
        else:
            print(f"  [FAIL] HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"  [FAIL] {e}")

# ── 2. Azure Blob Storage ──
print()
print("=" * 50)
print("2. AZURE BLOB STORAGE")
print("=" * 50)
conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
container = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "healthlens")
if not conn_str:
    print("  [FAIL] Missing AZURE_STORAGE_CONNECTION_STRING in .env")
else:
    print(f"  Container: {container}")
    try:
        from azure.storage.blob import BlobServiceClient
        client = BlobServiceClient.from_connection_string(conn_str)
        cont = client.get_container_client(container)
        blobs = list(cont.list_blobs())
        print(f"  [OK] Connected! Found {len(blobs)} blobs:")
        for b in blobs[:10]:
            print(f"    - {b.name} ({b.size:,} bytes)")
        if len(blobs) > 10:
            print(f"    ... and {len(blobs) - 10} more")
    except Exception as e:
        print(f"  [FAIL] {e}")

# ── 3. Azure Content Understanding ──
print()
print("=" * 50)
print("3. AZURE CONTENT UNDERSTANDING")
print("=" * 50)
cu_endpoint = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT", "")
cu_key = os.getenv("AZURE_CONTENT_UNDERSTANDING_KEY", "")
cu_analyzer = os.getenv("AZURE_CONTENT_UNDERSTANDING_ANALYZER_ID", "food-analyzer")
if not cu_endpoint or not cu_key:
    print("  [FAIL] Missing AZURE_CONTENT_UNDERSTANDING_ENDPOINT or KEY in .env")
else:
    print(f"  Endpoint: {cu_endpoint}")
    print(f"  Analyzer: {cu_analyzer}")
    try:
        import requests
        url = f"{cu_endpoint}/contentunderstanding/analyzers/{cu_analyzer}?api-version=2024-12-01-preview"
        resp = requests.get(url, headers={"Ocp-Apim-Subscription-Key": cu_key}, timeout=15)
        if resp.status_code == 200:
            print(f"  [OK] Connected! Analyzer '{cu_analyzer}' found.")
        elif resp.status_code == 404:
            print(f"  [WARN] Connected but analyzer '{cu_analyzer}' not found (404)")
            print(f"         {resp.text[:200]}")
        else:
            print(f"  [WARN] HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"  [FAIL] {e}")

print()
print("=" * 50)
print("CONNECTIVITY CHECK COMPLETE")
print("=" * 50)
