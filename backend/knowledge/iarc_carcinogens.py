"""
knowledge/iarc_carcinogens.py
IARC (International Agency for Research on Cancer) classifications
for food-related substances.
Data loaded from Azure Blob Storage (knowledge/iarc_carcinogens.json).

Groups:
  1   — Carcinogenic to humans (sufficient evidence)
  2A  — Probably carcinogenic (limited evidence in humans, sufficient in animals)
  2B  — Possibly carcinogenic (limited evidence in humans)
  3   — Not classifiable

Source: https://monographs.iarc.who.int/list-of-classifications/
"""

from knowledge.blob_loader import load_knowledge_blob

# ── Load data from Blob Storage ──
_data = load_knowledge_blob("iarc_carcinogens.json", fallback={"carcinogens": []})
FOOD_RELATED_CARCINOGENS: list[dict] = _data.get("carcinogens", [])


def check_ingredients_for_carcinogens(ingredients_text: str) -> list[dict]:
    """
    Scan ingredient text for IARC-classified carcinogenic substances.

    Returns:
        List of matched carcinogen records, sorted by IARC group (most dangerous first).
    """
    matches = []
    text_lower = ingredients_text.lower()

    for carcinogen in FOOD_RELATED_CARCINOGENS:
        matched_markers = [
            marker for marker in carcinogen["food_markers"]
            if marker.lower() in text_lower
        ]
        if matched_markers:
            matches.append({
                "agent": carcinogen["agent"],
                "iarc_group": carcinogen["group"],
                "cancer_sites": carcinogen["cancer_sites"],
                "matched_in_ingredients": matched_markers,
                "mechanism": carcinogen["mechanism"],
                "advice": carcinogen["advice"],
            })

    # Sort by group: 1 > 2A > 2B > 3
    group_order = {"1": 0, "2A": 1, "2B": 2, "3": 3}
    matches.sort(key=lambda m: group_order.get(m["iarc_group"], 9))

    return matches
