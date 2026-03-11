"""Test /api/analyze with user's egg image"""
import json, requests, sys, os

url = "http://localhost:8000/api/analyze"
img_path = sys.argv[1] if len(sys.argv) > 1 else "image/40214206-2_1-kelloggs-original-potato-crisps.webp"

if not os.path.exists(img_path):
    print(f"Image not found: {img_path}")
    sys.exit(1)

print(f"Testing with: {img_path} ({os.path.getsize(img_path)} bytes)")
mime = "image/webp" if img_path.endswith(".webp") else "image/jpeg"
with open(img_path, "rb") as f:
    resp = requests.post(
        url,
        files={"image": (os.path.basename(img_path), f, mime)},
        data={"healthNote": ""},
        stream=True,
    )

print(f"Status: {resp.status_code}\n")
for line in resp.iter_lines(decode_unicode=True):
    if line and line.startswith("data:"):
        d = json.loads(line[5:].strip())
        stage = d.get("stage", "")
        if stage == "done":
            result = d.get("data", {})
            print(f"--- RESULT ---")
            print(f"Product:  {result.get('product')}")
            print(f"Type:     {result.get('type')}")
            print(f"Verdict:  {result.get('conclusion', {}).get('verdict')}")
            print(f"Summary:  {result.get('conclusion', {}).get('summary', '')[:300]}")
            print(f"\nNutrition: {result.get('nutrition')}")
            print(f"\nAgents ({len(result.get('agentOutputs', []))}):")
            for ao in result.get("agentOutputs", []):
                v = ao["verdict"]
                s = ao["summary"][:120].replace("\n", " ")
                print(f"  [{v:7s}] Agent {ao['agentId']}: {s}...")
        elif stage == "error":
            print(f"ERROR: {d}")
        else:
            label = d.get("label", d.get("agent", ""))
            print(f"  [{stage}] {label}")
