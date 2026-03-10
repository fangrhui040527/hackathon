"""
tools/dslb_api.py
NIH Dietary Supplement Label Database (DSLB) API wrapper.
Source: https://dslb.od.nih.gov
Contains label information from dietary supplements marketed in the US.
"""

import requests
from typing import Optional

BASE_URL = "https://api.ods.od.nih.gov/dsld/v9"
TIMEOUT = 15


def search_supplements(query: str, limit: int = 5) -> list[dict]:
    """
    Search the NIH DSLD for dietary supplements by ingredient or product name.

    Args:
        query: Ingredient or product name (e.g., 'vitamin D', 'fish oil', 'caffeine').
        limit: Max results.

    Returns:
        List of supplement label records.
    """
    url = f"{BASE_URL}/browse-ingredients"
    params = {"q": query, "rows": limit, "format": "json"}
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT,
                            headers={"User-Agent": "HealthScan/1.0", "Accept": "application/json"})
        if resp.status_code in (404, 422):
            return []
        resp.raise_for_status()
        data = resp.json()
        results = data if isinstance(data, list) else data.get("results", data.get("data", data.get("list", [])))
        return [
            {
                "source": "NIH_DSLD",
                "id": r.get("dsld_id", r.get("id", "")),
                "product_name": r.get("product_name", r.get("Product_Name", "")),
                "brand_name": r.get("brand_name", r.get("Brand_Name", "")),
                "ingredient_name": r.get("ingredient_name", r.get("Ingredient_Name", query)),
                "amount": r.get("amount_per_serving", r.get("Amount_Per_Serving", "")),
                "unit": r.get("unit", r.get("Unit", "")),
                "daily_value_pct": r.get("daily_value_pct", r.get("Percent_Daily_Value", "")),
            }
            for r in (results[:limit] if isinstance(results, list) else [])
        ]
    except requests.exceptions.ConnectionError:
        print(f"[NIH-DSLD] Connection error — site may be unavailable.")
        return []
    except Exception as e:
        print(f"[NIH-DSLD] Search error for '{query}': {e}")
        return []


def check_ingredient_in_supplements(ingredient: str) -> list[dict]:
    """
    Check if a food ingredient is commonly used in dietary supplements
    and get typical dosages from the DSLD.

    Args:
        ingredient: Ingredient name (e.g., 'caffeine', 'vitamin C').

    Returns:
        List of supplement records containing the ingredient.
    """
    return search_supplements(ingredient, limit=5)
