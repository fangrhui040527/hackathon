"""
tools/foodb_api.py
FooDB API wrapper — the world's largest food constituent database.
Source: https://foodb.ca
FooDB catalogs chemical compounds found in food: nutrients, flavors, additives, toxins.
"""

import requests
from typing import Optional

BASE_URL = "https://foodb.ca/api/v1"
TIMEOUT = 15


def search_foods(query: str, limit: int = 5) -> list[dict]:
    """
    Search FooDB for a food item.

    Args:
        query: Food name (e.g., 'banana', 'chicken breast', 'cheddar cheese').
        limit: Max results.

    Returns:
        List of food records with id, name, description, food_group.
    """
    url = f"{BASE_URL}/foods"
    params = {"q": query, "limit": limit}
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT,
                            headers={"User-Agent": "HealthScan/1.0", "Accept": "application/json"})
        if resp.status_code in (404, 422):
            return []
        resp.raise_for_status()
        data = resp.json()
        results = data if isinstance(data, list) else data.get("results", data.get("data", []))
        return [
            {
                "source": "FooDB",
                "id": r.get("id", ""),
                "name": r.get("name", r.get("public_id", "")),
                "description": r.get("description", ""),
                "food_group": r.get("food_group", r.get("food_subgroup", "")),
                "food_type": r.get("food_type", ""),
                "category": r.get("category", ""),
            }
            for r in (results[:limit] if isinstance(results, list) else [])
        ]
    except requests.exceptions.ConnectionError:
        print(f"[FooDB] Connection error — site may be unavailable.")
        return []
    except Exception as e:
        print(f"[FooDB] Search error for '{query}': {e}")
        return []


def get_food_compounds(food_id: str, limit: int = 20) -> list[dict]:
    """
    Get chemical compounds found in a specific food from FooDB.

    Args:
        food_id: FooDB food ID.
        limit: Max compounds to return.

    Returns:
        List of compound records (nutrients, flavors, toxins, etc.).
    """
    url = f"{BASE_URL}/foods/{food_id}/compounds"
    try:
        resp = requests.get(url, timeout=TIMEOUT,
                            headers={"User-Agent": "HealthScan/1.0", "Accept": "application/json"})
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
        results = data if isinstance(data, list) else data.get("results", data.get("data", []))
        return [
            {
                "source": "FooDB",
                "compound_name": c.get("name", c.get("compound_name", "")),
                "compound_type": c.get("compound_type", c.get("type", "")),
                "concentration": c.get("orig_content", c.get("concentration", "")),
                "unit": c.get("orig_unit", c.get("unit", "")),
                "description": c.get("description", ""),
            }
            for c in (results[:limit] if isinstance(results, list) else [])
        ]
    except Exception as e:
        print(f"[FooDB] Compound lookup error for food '{food_id}': {e}")
        return []


def get_food_nutrients(food_name: str) -> list[dict]:
    """
    Convenience: search for a food then return its nutrient compounds.

    Args:
        food_name: Name of food to look up.

    Returns:
        List of nutrient compounds in the food.
    """
    foods = search_foods(food_name, limit=1)
    if not foods:
        return []
    food_id = foods[0].get("id")
    if not food_id:
        return []
    return get_food_compounds(str(food_id), limit=30)
