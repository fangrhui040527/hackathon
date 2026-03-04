"""
knowledge/additive_database.py
Food additive reference — E-numbers, regulatory status, safety ratings, and health concerns.
Data loaded from Azure Blob Storage (knowledge/additives.json).

Sources: EFSA, FDA GRAS, JECFA, CSPI Chemical Cuisine, IARC.
"""

from knowledge.blob_loader import load_knowledge_blob

# ── Risk level constants ──
SAFE = "safe"
CAUTION = "caution"
AVOID = "avoid"
BANNED = "banned"

# ── Load data from Blob Storage ──
_data = load_knowledge_blob("additives.json", fallback={"additives": {}, "aliases": {}})
ADDITIVES: dict[str, dict] = _data.get("additives", {})
ALIASES: dict[str, str] = _data.get("aliases", {})


def lookup_additive(name_or_e_number: str) -> dict | None:
    """
    Look up a food additive by E-number or common name.
    Returns the additive info dict, or None if not found.
    """
    key = name_or_e_number.strip().upper()
    # Direct E-number lookup
    if key in ADDITIVES:
        return ADDITIVES[key]
    # Alias lookup
    alias_key = ALIASES.get(name_or_e_number.strip().lower())
    if alias_key and alias_key in ADDITIVES:
        return ADDITIVES[alias_key]
    return None


def scan_ingredients_for_additives(ingredients_text: str) -> list[dict]:
    """
    Scan a full ingredients text for known additives.
    Returns a list of matched additive records with the matched term.
    """
    ingredients_lower = ingredients_text.lower()
    found = []
    seen_e_numbers = set()

    # Check all aliases and E-numbers
    for alias, e_num in ALIASES.items():
        if alias in ingredients_lower and e_num not in seen_e_numbers:
            info = ADDITIVES.get(e_num)
            if info:
                found.append({"matched_term": alias, "e_number": e_num, **info})
                seen_e_numbers.add(e_num)

    # Also check direct E-number mentions (e.g., "E211")
    for e_num, info in ADDITIVES.items():
        if e_num.lower() in ingredients_lower and e_num not in seen_e_numbers:
            found.append({"matched_term": e_num, "e_number": e_num, **info})
            seen_e_numbers.add(e_num)

    return found


def get_additives_by_risk(risk_level: str) -> list[dict]:
    """Get all additives at a specific risk level (safe/caution/avoid/banned)."""
    return [
        {"e_number": e, **info}
        for e, info in ADDITIVES.items()
        if info["risk"] == risk_level
    ]
