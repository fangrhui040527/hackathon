"""
tools/openfoodfacts_api.py
Open Food Facts API wrapper — look up any food product by barcode or search by name.
Returns ingredients, nutrition facts, Nutri-Score, NOVA group, allergens, and additives.
Docs: https://wiki.openfoodfacts.org/API
"""

import requests
from typing import Optional

BASE_URL = "https://world.openfoodfacts.org"
TIMEOUT = 15


def lookup_by_barcode(barcode: str) -> Optional[dict]:
    """
    Look up a food product by its barcode (EAN/UPC).

    Returns a simplified dict with key product info, or None if not found.
    """
    url = f"{BASE_URL}/api/v2/product/{barcode}.json"
    try:
        resp = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": "HealthScan/1.0"})
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != 1:
            return None
        return _extract_product(data.get("product", {}))
    except Exception as e:
        print(f"[OpenFoodFacts] Barcode lookup error: {e}")
        return None


def search_by_name(query: str, page_size: int = 5) -> list[dict]:
    """
    Search Open Food Facts by product name.

    Returns a list of simplified product dicts.
    """
    url = f"{BASE_URL}/cgi/search.pl"
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": page_size,
    }
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT,
                            headers={"User-Agent": "HealthScan/1.0"})
        resp.raise_for_status()
        data = resp.json()
        products = data.get("products", [])
        return [_extract_product(p) for p in products if p]
    except Exception as e:
        print(f"[OpenFoodFacts] Search error: {e}")
        return []


def _extract_product(product: dict) -> dict:
    """Extract the most useful fields from a raw OFF product."""
    nutriments = product.get("nutriments", {})
    return {
        "source": "OpenFoodFacts",
        "barcode": product.get("code", ""),
        "product_name": product.get("product_name", "Unknown"),
        "brands": product.get("brands", ""),
        "categories": product.get("categories", ""),
        "ingredients_text": product.get("ingredients_text", ""),
        "allergens": product.get("allergens", ""),
        "traces": product.get("traces", ""),
        "additives_tags": product.get("additives_tags", []),
        "nutriscore_grade": product.get("nutriscore_grade", ""),
        "nova_group": product.get("nova_group", ""),
        "ecoscore_grade": product.get("ecoscore_grade", ""),
        "serving_size": product.get("serving_size", ""),
        "nutrition_per_100g": {
            "energy_kcal": nutriments.get("energy-kcal_100g"),
            "fat_g": nutriments.get("fat_100g"),
            "saturated_fat_g": nutriments.get("saturated-fat_100g"),
            "trans_fat_g": nutriments.get("trans-fat_100g"),
            "carbohydrates_g": nutriments.get("carbohydrates_100g"),
            "sugars_g": nutriments.get("sugars_100g"),
            "fiber_g": nutriments.get("fiber_100g"),
            "proteins_g": nutriments.get("proteins_100g"),
            "sodium_mg": (nutriments.get("sodium_100g") or 0) * 1000,
            "salt_g": nutriments.get("salt_100g"),
            "cholesterol_mg": nutriments.get("cholesterol_100g"),
            "potassium_mg": nutriments.get("potassium_100g"),
            "calcium_mg": nutriments.get("calcium_100g"),
            "iron_mg": nutriments.get("iron_100g"),
            "vitamin_a_ug": nutriments.get("vitamin-a_100g"),
            "vitamin_c_mg": nutriments.get("vitamin-c_100g"),
        },
        "labels": product.get("labels", ""),
        "countries": product.get("countries", ""),
        "image_url": product.get("image_url", ""),
    }
