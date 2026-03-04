"""
tools/usda_api.py
USDA FoodData Central API wrapper — detailed nutrient data for any food ingredient.
Docs: https://fdc.nal.usda.gov/api-guide
Free API key: https://fdc.nal.usda.gov/api-key-signup
"""

import os
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.nal.usda.gov/fdc/v1"
API_KEY = os.getenv("USDA_API_KEY", "DEMO_KEY")
TIMEOUT = 15


def search_foods(query: str, page_size: int = 5) -> list[dict]:
    """
    Search USDA FoodData Central for foods matching a query.

    Returns simplified nutrient data for each result.
    """
    url = f"{BASE_URL}/foods/search"
    params = {
        "api_key": API_KEY,
        "query": query,
        "pageSize": page_size,
        "dataType": ["Survey (FNDDS)", "SR Legacy", "Foundation"],
    }
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        foods = data.get("foods", [])
        return [_extract_food(f) for f in foods]
    except Exception as e:
        print(f"[USDA] Search error: {e}")
        return []


def get_food_by_id(fdc_id: int) -> Optional[dict]:
    """
    Get detailed nutrient data for a specific USDA food by FDC ID.
    """
    url = f"{BASE_URL}/food/{fdc_id}"
    params = {"api_key": API_KEY}
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return _extract_food_detail(data)
    except Exception as e:
        print(f"[USDA] Food detail error: {e}")
        return None


def get_nutrients_for_ingredient(ingredient_name: str) -> Optional[dict]:
    """
    Convenience: search for an ingredient and return the top match's nutrients.
    """
    results = search_foods(ingredient_name, page_size=1)
    if results:
        return results[0]
    return None


def _extract_food(food: dict) -> dict:
    """Extract key fields from a USDA search result."""
    nutrients = {}
    for n in food.get("foodNutrients", []):
        name = n.get("nutrientName", "")
        value = n.get("value")
        unit = n.get("unitName", "")
        if value is not None:
            nutrients[name] = {"value": value, "unit": unit}

    return {
        "source": "USDA_FoodData_Central",
        "fdc_id": food.get("fdcId"),
        "description": food.get("description", ""),
        "data_type": food.get("dataType", ""),
        "brand_owner": food.get("brandOwner", ""),
        "ingredients": food.get("ingredients", ""),
        "serving_size": food.get("servingSize"),
        "serving_size_unit": food.get("servingSizeUnit", ""),
        "nutrients": nutrients,
    }


def _extract_food_detail(food: dict) -> dict:
    """Extract detailed nutrient info from a single food item."""
    nutrients = {}
    for n in food.get("foodNutrients", []):
        nutrient = n.get("nutrient", {})
        name = nutrient.get("name", n.get("nutrientName", ""))
        value = n.get("amount", n.get("value"))
        unit = nutrient.get("unitName", n.get("unitName", ""))
        if value is not None:
            nutrients[name] = {"value": value, "unit": unit}

    return {
        "source": "USDA_FoodData_Central",
        "fdc_id": food.get("fdcId"),
        "description": food.get("description", ""),
        "data_type": food.get("dataType", ""),
        "food_class": food.get("foodClass", ""),
        "ingredients": food.get("ingredients", ""),
        "nutrients": nutrients,
        "label_nutrients": food.get("labelNutrients", {}),
    }
