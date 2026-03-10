"""
knowledge/dietary_limits.py
WHO, NIH, AHA, ADA daily intake limits for nutrients per medical condition.
Data loaded from Azure Blob Storage (knowledge/dietary_limits.json).

Sources:
  - WHO: https://www.who.int/news-room/fact-sheets/detail/healthy-diet
  - AHA: https://www.heart.org/en/healthy-living/healthy-eating
  - ADA: https://diabetes.org/food-nutrition
  - NIH DRI: https://ods.od.nih.gov/HealthInformation/Dietary-Reference-Intakes.aspx
  - KDOQI: https://www.kidney.org/professionals/kdoqi-guidelines
"""

import copy

from knowledge.blob_loader import load_knowledge_blob

# ── Load data from Blob Storage ──
_data = load_knowledge_blob("dietary_limits.json", fallback={
    "general_adult": {},
    "condition_limits": {},
    "medication_nutrient_limits": {},
})

GENERAL_ADULT: dict = _data.get("general_adult", {})
CONDITION_LIMITS: dict = _data.get("condition_limits", {})
MEDICATION_NUTRIENT_LIMITS: dict = _data.get("medication_nutrient_limits", {})


def get_limits_for_conditions(conditions: list[str]) -> dict:
    """
    Get the MOST RESTRICTIVE nutrient limits across all user conditions.

    Args:
        conditions: List of condition keys (e.g., ['diabetes', 'hypertension']).

    Returns:
        Merged dict of nutrient limits (takes the strictest from each condition).
    """
    merged = copy.deepcopy(GENERAL_ADULT)

    for condition in conditions:
        condition_key = condition.lower().replace(" ", "_")
        limits = CONDITION_LIMITS.get(condition_key, {})
        for nutrient, vals in limits.items():
            if nutrient not in merged:
                merged[nutrient] = vals
            else:
                if "max" in vals and "max" in merged[nutrient]:
                    merged[nutrient]["max"] = min(
                        vals["max"], merged[nutrient]["max"]
                    )
                if "min" in vals and "min" in merged[nutrient]:
                    merged[nutrient]["min"] = max(
                        vals["min"], merged[nutrient]["min"]
                    )
                if "critical" in vals:
                    merged[nutrient]["critical"] = vals["critical"]
                if "note" in vals:
                    merged[nutrient]["note"] = vals["note"]

    return merged


def check_nutrient_against_limits(
    nutrient_name: str, value_per_serving: float, conditions: list[str]
) -> dict:
    """
    Check if a nutrient value exceeds the limits for given conditions.

    Returns:
        {
            "status": "safe" | "caution" | "danger",
            "value": float,
            "limit": float,
            "explanation": str,
        }
    """
    limits = get_limits_for_conditions(conditions)
    nutrient_key = nutrient_name.lower().replace(" ", "_")

    if nutrient_key not in limits:
        return {"status": "unknown", "value": value_per_serving, "explanation": "No limit data available."}

    limit_info = limits[nutrient_key]
    max_val = limit_info.get("max")
    critical_val = limit_info.get("critical")

    if max_val is not None:
        if critical_val and value_per_serving >= critical_val:
            return {
                "status": "danger",
                "value": value_per_serving,
                "limit": max_val,
                "critical": critical_val,
                "explanation": f"EXCEEDS critical threshold ({critical_val}). {limit_info.get('note', '')}",
            }
        elif value_per_serving > max_val:
            return {
                "status": "caution",
                "value": value_per_serving,
                "limit": max_val,
                "explanation": f"Exceeds recommended max ({max_val}). {limit_info.get('note', '')}",
            }

    return {
        "status": "safe",
        "value": value_per_serving,
        "limit": max_val,
        "explanation": f"Within recommended limits. {limit_info.get('note', '')}",
    }


def get_medication_warnings(medications: list[str], ingredients_text: str) -> list[dict]:
    """
    Check for drug-food interactions between user medications and food ingredients.

    Args:
        medications: List of medication names (e.g., ['warfarin', 'metformin']).
        ingredients_text: Raw ingredients text from food label.

    Returns:
        List of warning dicts.
    """
    warnings = []
    ingredients_lower = ingredients_text.lower()

    for med in medications:
        med_key = med.lower().replace(" ", "_")
        interactions = MEDICATION_NUTRIENT_LIMITS.get(med_key, {})

        for nutrient_key, info in interactions.items():
            if isinstance(info, dict) and "danger_foods" in info:
                for food in info["danger_foods"]:
                    if food.lower() in ingredients_lower:
                        warnings.append({
                            "medication": med,
                            "interacting_ingredient": food,
                            "severity": "HIGH",
                            "note": info.get("note", ""),
                            "danger": info.get("danger", ""),
                        })
            elif isinstance(info, dict) and "high_vk_foods" in info:
                for food in info["high_vk_foods"]:
                    if food.lower() in ingredients_lower:
                        warnings.append({
                            "medication": med,
                            "interacting_ingredient": food,
                            "severity": "MEDIUM",
                            "note": info.get("note", ""),
                            "danger": info.get("danger", ""),
                        })

    return warnings
