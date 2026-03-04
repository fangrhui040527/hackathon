"""
export_knowledge_to_json.py
One-time script: Exports loaded knowledge data to JSON files
that you can upload to Azure Blob Storage under the knowledge/ prefix.

The knowledge modules auto-load from Azure Blob Storage or local
knowledge_json/ files. This script can be used to re-export them after
modifications, or to view the current state of the loaded data.

Usage:
    python export_knowledge_to_json.py

Output files (in knowledge_json/ folder):
    additives.json
    dietary_limits.json
    drug_food_interactions.json
    glycemic_index.json
    iarc_carcinogens.json
    nova_classification.json
"""

import json
import os


OUTPUT_DIR = "knowledge_json"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def export_all():
    # Late imports to let blob_loader initialize fully (with local fallback)
    from knowledge.additive_database import ADDITIVES, ALIASES
    from knowledge.dietary_limits import (
        GENERAL_ADULT,
        CONDITION_LIMITS,
        MEDICATION_NUTRIENT_LIMITS,
    )
    from knowledge.drug_food_interactions import INTERACTIONS
    from knowledge.glycemic_index_db import GI_DATABASE
    from knowledge.iarc_carcinogens import FOOD_RELATED_CARCINOGENS
    from knowledge.nova_classification import NOVA_GROUPS, ULTRA_PROCESSED_MARKERS

    # 1. Additives
    _write("additives.json", {
        "additives": ADDITIVES,
        "aliases": ALIASES,
    })

    # 2. Dietary limits
    _write("dietary_limits.json", {
        "general_adult": GENERAL_ADULT,
        "condition_limits": CONDITION_LIMITS,
        "medication_nutrient_limits": MEDICATION_NUTRIENT_LIMITS,
    })

    # 3. Drug-food interactions
    _write("drug_food_interactions.json", {
        "interactions": INTERACTIONS,
    })

    # 4. Glycemic index
    _write("glycemic_index.json", {
        "gi_database": GI_DATABASE,
    })

    # 5. IARC carcinogens
    _write("iarc_carcinogens.json", {
        "carcinogens": FOOD_RELATED_CARCINOGENS,
    })

    # 6. NOVA classification
    # Convert int keys to strings for JSON compatibility
    nova_groups_str = {str(k): v for k, v in NOVA_GROUPS.items()}
    _write("nova_classification.json", {
        "nova_groups": nova_groups_str,
        "ultra_processed_markers": ULTRA_PROCESSED_MARKERS,
    })

    print(f"\nDone! Upload all files from '{OUTPUT_DIR}/' to your Blob container under 'knowledge/' prefix.")
    print("Example blob paths:")
    print("  knowledge/additives.json")
    print("  knowledge/dietary_limits.json")
    print("  knowledge/drug_food_interactions.json")
    print("  knowledge/glycemic_index.json")
    print("  knowledge/iarc_carcinogens.json")
    print("  knowledge/nova_classification.json")


def _write(filename, data):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    size = os.path.getsize(path)
    print(f"  Exported {filename} ({size:,} bytes)")


if __name__ == "__main__":
    export_all()
