"""
tools/openfda_api.py
FDA openFDA API wrapper — food recalls, adverse events, enforcements, and drug labeling.
Docs: https://open.fda.gov/apis/food/ and https://open.fda.gov/apis/drug/
"""

import requests

BASE_URL = "https://api.fda.gov"
TIMEOUT = 15


def check_food_recalls(product_name: str, limit: int = 5) -> list[dict]:
    """
    Check if a product or brand has active FDA food recalls.

    Returns a list of recall records.
    """
    url = f"{BASE_URL}/food/enforcement.json"
    # Search in product_description OR recalling_firm fields
    search_query = f'product_description:"{product_name}"+OR+recalling_firm:"{product_name}"'
    params = {
        "search": search_query,
        "limit": limit,
        "sort": "report_date:desc",
    }
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        if resp.status_code == 404:
            return []  # No results
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        return [
            {
                "source": "FDA_Recall",
                "recalling_firm": r.get("recalling_firm", ""),
                "product_description": r.get("product_description", ""),
                "reason_for_recall": r.get("reason_for_recall", ""),
                "classification": r.get("classification", ""),
                "status": r.get("status", ""),
                "recall_date": r.get("report_date", ""),
                "voluntary_mandated": r.get("voluntary_mandated", ""),
            }
            for r in results
        ]
    except Exception as e:
        print(f"[openFDA] Recall check error: {e}")
        return []


def check_food_enforcement(brand_or_product: str, limit: int = 5) -> list[dict]:
    """
    Check FDA enforcement actions for a food brand or product.
    """
    url = f"{BASE_URL}/food/enforcement.json"
    params = {
        "search": f'product_description:"{brand_or_product}"',
        "limit": limit,
        "sort": "report_date:desc",
    }
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        return [
            {
                "source": "FDA_Enforcement",
                "product_description": r.get("product_description", ""),
                "reason_for_recall": r.get("reason_for_recall", ""),
                "classification": r.get("classification", ""),
                "status": r.get("status", ""),
                "city": r.get("city", ""),
                "state": r.get("state", ""),
                "report_date": r.get("report_date", ""),
            }
            for r in results
        ]
    except Exception as e:
        print(f"[openFDA] Enforcement check error: {e}")
        return []


# ── Drug API endpoints (open.fda.gov/apis/drug/) ────────────────────────

def search_drug_label(drug_name: str, limit: int = 3) -> list[dict]:
    """
    Search FDA drug labeling for a medication — returns warnings,
    food interactions, contraindications from the official label.

    Source: https://open.fda.gov/apis/drug/label/

    Args:
        drug_name: Drug name (generic or brand, e.g., 'warfarin', 'metformin').
        limit: Max results.

    Returns:
        List of drug label records with food interaction and warning fields.
    """
    url = f"{BASE_URL}/drug/label.json"
    search_query = (
        f'openfda.generic_name:"{drug_name}"'
        f'+OR+openfda.brand_name:"{drug_name}"'
    )
    params = {"search": search_query, "limit": limit}
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        return [
            {
                "source": "FDA_Drug_Label",
                "brand_name": _safe_first(r.get("openfda", {}).get("brand_name", [])),
                "generic_name": _safe_first(r.get("openfda", {}).get("generic_name", [])),
                "drug_interactions": _safe_first(r.get("drug_interactions", [])),
                "food_interactions": r.get("food_interaction", []),
                "warnings": _safe_first(r.get("warnings", [])),
                "contraindications": _safe_first(r.get("contraindications", [])),
                "precautions": _safe_first(r.get("precautions", [])),
                "adverse_reactions": _safe_first(r.get("adverse_reactions", [])),
            }
            for r in results
        ]
    except Exception as e:
        print(f"[openFDA] Drug label search error for '{drug_name}': {e}")
        return []


def get_drug_food_warnings(drug_name: str) -> list[str]:
    """
    Extract food interaction warnings from FDA drug labels.
    Convenience function that returns just the food-related text.

    Args:
        drug_name: Drug name.

    Returns:
        List of food interaction warning strings from the label.
    """
    labels = search_drug_label(drug_name, limit=1)
    warnings = []
    for label in labels:
        # Explicit food_interaction field
        fi = label.get("food_interactions", [])
        if fi:
            warnings.extend(fi if isinstance(fi, list) else [fi])
        # Check drug_interactions text for food-related mentions
        di = label.get("drug_interactions", "")
        if di and isinstance(di, str):
            food_keywords = ["food", "grapefruit", "dairy", "milk", "alcohol",
                             "vitamin k", "tyramine", "potassium", "calcium",
                             "fiber", "caffeine", "juice", "meal"]
            for kw in food_keywords:
                if kw in di.lower():
                    warnings.append(di)
                    break
    return warnings


def _safe_first(lst):
    """Safely get first element from a list, or return the value if not a list."""
    if isinstance(lst, list):
        return lst[0] if lst else ""
    return lst or ""
