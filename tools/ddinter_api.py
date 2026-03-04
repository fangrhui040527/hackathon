"""
tools/ddinter_api.py
DDInter2 API wrapper — drug-drug and drug-food interaction database.
Source: https://ddinter2.scbdd.com
DDInter contains 0.24M+ drug interaction pairs with severity, mechanism, and management.
"""

import requests
from typing import Optional

BASE_URL = "https://ddinter2.scbdd.com"
TIMEOUT = 15


def search_drug_interactions(drug_name: str, limit: int = 10) -> list[dict]:
    """
    Search DDInter for interactions involving a specific drug.

    Args:
        drug_name: Name of the drug (e.g., 'warfarin', 'metformin').
        limit: Max results.

    Returns:
        List of interaction records with severity, mechanism, management.
    """
    url = f"{BASE_URL}/api/search"
    params = {"query": drug_name, "limit": limit}
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT,
                            headers={"User-Agent": "HealthScan/1.0"})
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
        results = data if isinstance(data, list) else data.get("results", data.get("data", []))
        return [
            {
                "source": "DDInter2",
                "drug_a": r.get("drug_a", r.get("Drug_A", "")),
                "drug_b": r.get("drug_b", r.get("Drug_B", "")),
                "severity": r.get("level", r.get("severity", r.get("Level", "unknown"))),
                "mechanism": r.get("mechanism", r.get("Mechanism", "")),
                "management": r.get("management", r.get("Management", "")),
                "description": r.get("description", r.get("Description", "")),
            }
            for r in (results[:limit] if isinstance(results, list) else [])
        ]
    except requests.exceptions.ConnectionError:
        print(f"[DDInter] Connection error — site may be unavailable.")
        return []
    except Exception as e:
        print(f"[DDInter] Search error for '{drug_name}': {e}")
        return []


def check_drug_food_interactions(drug_name: str, food_ingredients: list[str]) -> list[dict]:
    """
    Check DDInter for interactions between a drug and a list of food ingredients.
    DDInter primarily covers drug-drug, but some entries include food-derived compounds.

    Args:
        drug_name: The drug to check.
        food_ingredients: List of food ingredient names.

    Returns:
        List of matched interactions.
    """
    all_interactions = search_drug_interactions(drug_name, limit=50)
    matches = []

    for interaction in all_interactions:
        # Check if any food ingredient appears in drug_b or description
        drug_b = str(interaction.get("drug_b", "")).lower()
        description = str(interaction.get("description", "")).lower()
        mechanism = str(interaction.get("mechanism", "")).lower()

        for ingredient in food_ingredients:
            ingredient_lower = ingredient.lower().strip()
            if (ingredient_lower in drug_b or
                ingredient_lower in description or
                ingredient_lower in mechanism):
                interaction["matched_food"] = ingredient
                matches.append(interaction)
                break

    return matches
