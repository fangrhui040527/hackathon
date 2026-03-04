"""
knowledge/glycemic_index_db.py
Glycemic Index (GI) and Glycemic Load (GL) database for common food ingredients.
Data loaded from Azure Blob Storage (knowledge/glycemic_index.json).

GI Scale:
  Low:    <= 55
  Medium: 56-69
  High:   >= 70

GL Scale (per serving):
  Low:    <= 10
  Medium: 11-19
  High:   >= 20

Source: University of Sydney GI Database (https://glycemicindex.com/)
"""

from knowledge.blob_loader import load_knowledge_blob

# ── Load data from Blob Storage ──
_data = load_knowledge_blob("glycemic_index.json", fallback={"gi_database": {}})
GI_DATABASE: dict[str, dict] = _data.get("gi_database", {})


def lookup_gi(food_name: str) -> dict | None:
    """
    Look up glycemic index and glycemic load for a food.
    Returns None if not found.
    """
    key = food_name.strip().lower()
    if key in GI_DATABASE:
        data = GI_DATABASE[key]
        return {
            "food": food_name,
            **data,
            "gi_category": _classify_gi(data["gi"]),
            "gl_category": _classify_gl(data["gl"]),
        }
    # Partial match
    for db_key, data in GI_DATABASE.items():
        if key in db_key or db_key in key:
            return {
                "food": db_key,
                **data,
                "gi_category": _classify_gi(data["gi"]),
                "gl_category": _classify_gl(data["gl"]),
            }
    return None


def scan_ingredients_for_gi(ingredients_text: str) -> list[dict]:
    """
    Scan ingredient text and return GI data for any recognized ingredients.
    """
    results = []
    ingredients_lower = ingredients_text.lower()
    for food_name, data in GI_DATABASE.items():
        if food_name in ingredients_lower:
            results.append({
                "food": food_name,
                **data,
                "gi_category": _classify_gi(data["gi"]),
                "gl_category": _classify_gl(data["gl"]),
            })
    return results


def _classify_gi(gi: int) -> str:
    if gi <= 55:
        return "Low"
    elif gi <= 69:
        return "Medium"
    return "High"


def _classify_gl(gl: int) -> str:
    if gl <= 10:
        return "Low"
    elif gl <= 19:
        return "Medium"
    return "High"
