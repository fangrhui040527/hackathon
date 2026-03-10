"""
knowledge/nova_classification.py
NOVA food classification system — classifies foods by degree of processing.
Data loaded from Azure Blob Storage (knowledge/nova_classification.json).

NOVA Groups:
  1 — Unprocessed or minimally processed foods
  2 — Processed culinary ingredients
  3 — Processed foods
  4 — Ultra-processed food products

Source: Monteiro et al., "NOVA. The star shines bright", World Nutrition 2016
"""

import re

from knowledge.blob_loader import load_knowledge_blob

# ── Load data from Blob Storage ──
_data = load_knowledge_blob("nova_classification.json", fallback={
    "nova_groups": {},
    "ultra_processed_markers": [],
})

# JSON stores keys as strings — convert back to int keys
_raw_groups = _data.get("nova_groups", {})
NOVA_GROUPS: dict[int, dict] = {int(k): v for k, v in _raw_groups.items()}

ULTRA_PROCESSED_MARKERS: list[str] = _data.get("ultra_processed_markers", [])


def classify_nova(ingredients_text: str, ingredient_count: int = 0) -> dict:
    """
    Estimate the NOVA classification of a food product based on its ingredients.

    Args:
        ingredients_text: Full ingredients list from the label.
        ingredient_count: Number of individual ingredients (if known).

    Returns:
        Dict with nova_group, confidence, reasoning, and health advice.
    """
    if not ingredients_text:
        return {
            "nova_group": None,
            "confidence": "low",
            "reasoning": "No ingredients text provided.",
            "health_advice": "Cannot classify without ingredient information.",
        }

    text_lower = ingredients_text.lower()

    # Count ultra-processed markers found
    markers_found = []
    for marker in ULTRA_PROCESSED_MARKERS:
        if marker in text_lower:
            markers_found.append(marker)

    # Count E-numbers
    e_numbers = re.findall(r'\bE\d{3,4}[a-z]?\b', ingredients_text, re.IGNORECASE)

    total_markers = len(markers_found) + len(e_numbers)

    # Classification logic
    if total_markers >= 3 or (ingredient_count > 0 and ingredient_count >= 8 and total_markers >= 2):
        group = 4
        confidence = "high" if total_markers >= 5 else "medium"
    elif total_markers >= 1 or (ingredient_count > 0 and ingredient_count >= 5):
        group = 3
        confidence = "medium"
    elif ingredient_count > 0 and ingredient_count <= 3:
        group = 1
        confidence = "medium"
    else:
        group = 2
        confidence = "low"

    nova_info = NOVA_GROUPS.get(group, {
        "name": "Unknown",
        "risk_level": "unknown",
        "health_advice": "Classification data unavailable.",
    })

    return {
        "nova_group": group,
        "nova_name": nova_info["name"],
        "risk_level": nova_info["risk_level"],
        "confidence": confidence,
        "markers_found": markers_found,
        "e_numbers_found": e_numbers,
        "total_processing_markers": total_markers,
        "reasoning": (
            f"Found {len(markers_found)} ultra-processing markers and "
            f"{len(e_numbers)} E-numbers in ingredients."
        ),
        "health_advice": nova_info["health_advice"],
    }
