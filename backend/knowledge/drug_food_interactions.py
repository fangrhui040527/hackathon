"""
knowledge/drug_food_interactions.py
Common drug-food interactions database.
Data loaded from Azure Blob Storage (knowledge/drug_food_interactions.json).

Sources:
  - DrugBank: https://go.drugbank.com/
  - NIH DailyMed: https://dailymed.nlm.nih.gov/dailymed/
  - Mayo Clinic: https://www.mayoclinic.org/drugs-supplements
"""

from knowledge.blob_loader import load_knowledge_blob

# Severity levels
CRITICAL = "critical"
HIGH = "high"
MODERATE = "moderate"
LOW = "low"

# ── Load data from Blob Storage ──
_data = load_knowledge_blob("drug_food_interactions.json", fallback={"interactions": []})
INTERACTIONS: list[dict] = _data.get("interactions", [])


def check_interactions(
    medications: list[str],
    ingredients_text: str,
) -> list[dict]:
    """
    Check for drug-food interactions between a user's medications and food ingredients.

    Args:
        medications: List of drug names the user takes.
        ingredients_text: Raw ingredient list from the food label.

    Returns:
        List of interaction warnings sorted by severity.
    """
    warnings = []
    ingredients_lower = ingredients_text.lower()

    for interaction in INTERACTIONS:
        # Check if user takes this drug
        drug_matches = [interaction["drug"].lower()]
        drug_matches.extend([a.lower() for a in interaction.get("drug_aliases", [])])

        user_takes_drug = any(
            med.lower() in drug_match or drug_match in med.lower()
            for med in medications
            for drug_match in drug_matches
        )
        if not user_takes_drug:
            continue

        # Check if food contains interacting ingredients
        matched_foods = [
            food for food in interaction["interacting_foods"]
            if food.lower() in ingredients_lower
        ]
        if not matched_foods:
            continue

        warnings.append({
            "drug": interaction["drug"],
            "drug_class": interaction["drug_class"],
            "matched_foods_in_product": matched_foods,
            "severity": interaction["severity"],
            "mechanism": interaction["mechanism"],
            "advice": interaction["advice"],
            "danger": interaction["danger"],
        })

    # Sort by severity: critical > high > moderate > low
    severity_order = {CRITICAL: 0, HIGH: 1, MODERATE: 2, LOW: 3}
    warnings.sort(key=lambda w: severity_order.get(w["severity"], 9))

    return warnings


def get_all_drugs_with_food_interactions() -> list[str]:
    """List all drugs in the database that have food interactions."""
    drugs = set()
    for interaction in INTERACTIONS:
        drugs.add(interaction["drug"])
        drugs.update(interaction.get("drug_aliases", []))
    return sorted(drugs)
