"""
grounding_pipeline.py
Enriches raw food data (from Content Understanding / OCR) with grounded knowledge
from APIs and Azure Blob-backed knowledge databases before passing to the 5
specialist agents.

Knowledge Sources:
  APIs: fdc.nal.usda.gov, foodb.ca, ddinter2.scbdd.com, open.fda.gov,
        open.fda.gov/apis/drug/, dslb.od.nih.gov
  Blob: additives, dietary limits, drug-food interactions, glycemic index,
        IARC carcinogens, NOVA classification

Pipeline stages:
  1. Product lookup (Open Food Facts — barcode or name match)
  2. Nutrient enrichment (USDA FoodData Central — fdc.nal.usda.gov)
  3. Food composition (FooDB — foodb.ca)
  4. Additive analysis (Blob-backed additive DB)
  5. NOVA classification (ultra-processing assessment)
  6. Carcinogen check (Blob-backed IARC DB)
  7. Glycemic index lookup (Blob-backed GI DB)
  8. Drug-food interaction check (DDInter + FDA Drug Labels + Blob-backed DB)
  9. Dietary limit assessment (per user's health conditions)
  10. Dietary supplement cross-ref (NIH DSLB — dslb.od.nih.gov)
  11. Allergy check
  12. FDA recall + enforcement check (open.fda.gov)
"""

import json
from typing import Optional

# Tools — external API wrappers
from tools.openfoodfacts_api import lookup_by_barcode, search_by_name
from tools.usda_api import search_foods as usda_search
from tools.openfda_api import check_food_recalls, get_drug_food_warnings
from tools.ddinter_api import check_drug_food_interactions as ddinter_check
from tools.foodb_api import search_foods as foodb_search, get_food_nutrients as foodb_nutrients
from tools.dslb_api import check_ingredient_in_supplements as dslb_check

# Knowledge — embedded databases
from knowledge.additive_database import scan_ingredients_for_additives
from knowledge.dietary_limits import (
    get_limits_for_conditions,
    check_nutrient_against_limits,
    get_medication_warnings,
)
from knowledge.glycemic_index_db import scan_ingredients_for_gi
from knowledge.nova_classification import classify_nova
from knowledge.iarc_carcinogens import check_ingredients_for_carcinogens
from knowledge.drug_food_interactions import check_interactions


def enrich_food_data(
    raw_food_data: dict,
    user_conditions: Optional[list[str]] = None,
    user_medications: Optional[list[str]] = None,
    user_allergies: Optional[list[str]] = None,
) -> dict:
    """
    Run the full grounding pipeline to enrich raw food data.

    Args:
        raw_food_data: Structured food data from Azure Content Understanding (OCR).
        user_conditions: User's health conditions (e.g., ['diabetes', 'hypertension']).
        user_medications: User's current medications (e.g., ['metformin', 'lisinopril']).
        user_allergies: User's known allergies (e.g., ['peanuts', 'gluten']).

    Returns:
        Enriched food data dict with all grounding analysis attached.
    """
    user_conditions = user_conditions or []
    user_medications = user_medications or []
    user_allergies = user_allergies or []

    enriched = {
        "raw_data": raw_food_data,
        "user_profile": {
            "conditions": user_conditions,
            "medications": user_medications,
            "allergies": user_allergies,
        },
        "grounding": {},
    }

    # Extract key fields from raw data
    product_name = _extract_field(raw_food_data, ["product_name", "name", "food_name", "title"])
    brand = _extract_field(raw_food_data, ["brand", "manufacturer", "contactinfo", "company"])
    barcode = _extract_field(raw_food_data, ["barcode", "ean", "upc", "code"])
    ingredients_text = _extract_field(raw_food_data, ["ingredients", "ingredients_text", "ingredient_list"])
    nutrition = _extract_field(raw_food_data, ["nutrition", "nutrition_facts", "nutrients", "nutrition_table"])
    product_type = _extract_field(raw_food_data, ["category", "product_type", "food_type"])

    # Extract just the company name from ContactInfo (which may be a full address)
    if brand:
        brand = _extract_brand_name(str(brand))

    # Combine brand + title for a better product name (e.g. "Kellogg's Original Potato Crisps")
    if brand and product_name:
        brand_str = str(brand).strip()
        name_str = str(product_name).strip()
        if brand_str.lower() not in name_str.lower():
            product_name = f"{brand_str} {name_str}"
    elif brand and not product_name:
        product_name = str(brand).strip()
    # Append product type if name is very short/generic
    if product_name and product_type and len(str(product_name)) < 20:
        type_str = str(product_type).strip()
        if type_str.lower() not in str(product_name).lower():
            product_name = f"{product_name} {type_str}"

    # Normalize ingredients to string
    if isinstance(ingredients_text, list):
        ingredients_text = ", ".join(str(i) for i in ingredients_text)
    ingredients_text = str(ingredients_text) if ingredients_text else ""

    # Parse nutrition string into dict if it came as a text blob from CU
    if isinstance(nutrition, str) and nutrition:
        nutrition = _parse_nutrition_string(nutrition)
    elif not isinstance(nutrition, dict):
        nutrition = {}

    # ── Stage 1: Product Lookup (Open Food Facts) ────────────────────────
    print("  [Grounding] Stage 1: Product lookup (Open Food Facts)...")
    off_data = None
    if barcode:
        off_data = lookup_by_barcode(str(barcode))
    if not off_data and product_name:
        results = search_by_name(str(product_name), page_size=1)
        off_data = results[0] if results else None

    if off_data:
        enriched["grounding"]["open_food_facts"] = off_data
        # Fill in missing data from OFF
        if not ingredients_text and off_data.get("ingredients_text"):
            ingredients_text = off_data["ingredients_text"]
        if not product_name and off_data.get("product_name"):
            product_name = off_data["product_name"]

    # ── Stage 2: Nutrient Enrichment (USDA — fdc.nal.usda.gov) ─────────
    print("  [Grounding] Stage 2: Nutrient enrichment (USDA FoodData Central)...")
    if product_name:
        usda_data = usda_search(str(product_name), page_size=1)
        if usda_data:
            enriched["grounding"]["usda_nutrients"] = usda_data[0]

    # ── Stage 3: Food Composition (FooDB — foodb.ca) ─────────────────────
    print("  [Grounding] Stage 3: Food composition (FooDB)...")
    if product_name:
        foodb_data = foodb_search(str(product_name), limit=1)
        if foodb_data:
            enriched["grounding"]["foodb"] = foodb_data[0]
            # Try to get detailed compounds
            food_id = foodb_data[0].get("id")
            if food_id:
                compounds = foodb_nutrients(str(product_name))
                if compounds:
                    enriched["grounding"]["foodb_compounds"] = compounds[:15]

    # ── Stage 4: Additive Analysis (Blob-backed DB) ─────────────────────
    print("  [Grounding] Stage 4: Additive analysis (knowledge DB)...")
    if ingredients_text:
        additives_found = scan_ingredients_for_additives(ingredients_text)
        enriched["grounding"]["additives_analysis"] = {
            "additives_found": additives_found,
            "total_additives": len(additives_found),
            "avoid_additives": [a for a in additives_found if a.get("risk") == "avoid"],
            "caution_additives": [a for a in additives_found if a.get("risk") == "caution"],
            "safe_additives": [a for a in additives_found if a.get("risk") == "safe"],
        }

    # ── Stage 5: NOVA Classification ─────────────────────────────────────
    print("  [Grounding] Stage 5: NOVA ultra-processing classification...")
    if ingredients_text:
        ingredient_count = len([i.strip() for i in ingredients_text.split(",") if i.strip()])
        nova_result = classify_nova(ingredients_text, ingredient_count)
        enriched["grounding"]["nova_classification"] = nova_result

    # ── Stage 6: Carcinogen Check (IARC — monographs.iarc.who.int) ──────
    print("  [Grounding] Stage 6: IARC carcinogen screening...")
    if ingredients_text:
        carcinogens = check_ingredients_for_carcinogens(ingredients_text)
        enriched["grounding"]["iarc_carcinogens"] = {
            "found": carcinogens,
            "total_carcinogenic_agents": len(carcinogens),
            "group_1_agents": [c for c in carcinogens if c["iarc_group"] == "1"],
            "group_2A_agents": [c for c in carcinogens if c["iarc_group"] == "2A"],
            "group_2B_agents": [c for c in carcinogens if c["iarc_group"] == "2B"],
        }

    # ── Stage 7: Glycemic Index (Blob-backed GI DB) ──────────────────────
    print("  [Grounding] Stage 7: Glycemic index analysis...")
    if ingredients_text:
        gi_results = scan_ingredients_for_gi(ingredients_text)
        enriched["grounding"]["glycemic_index"] = {
            "ingredients_with_gi_data": gi_results,
            "highest_gi_ingredient": max(gi_results, key=lambda x: x["gi"]) if gi_results else None,
        }

    # ── Stage 8: Drug-Food Interactions (DDInter + FDA Drug Labels + embedded DB) ─
    if user_medications and ingredients_text:
        print("  [Grounding] Stage 8: Drug-food interaction analysis (DDInter, FDA, embedded DB)...")
        # Embedded knowledge base
        drug_warnings = check_interactions(user_medications, ingredients_text)
        med_nutrient_warnings = get_medication_warnings(user_medications, ingredients_text)

        # DDInter2 API (ddinter2.scbdd.com)
        ingredient_list = [i.strip() for i in ingredients_text.split(",") if i.strip()]
        ddinter_results = []
        for med in user_medications:
            ddinter_hits = ddinter_check(med, ingredient_list)
            ddinter_results.extend(ddinter_hits)

        # FDA Drug Labels (open.fda.gov/apis/drug/)
        fda_drug_warnings = []
        for med in user_medications:
            fda_food_warns = get_drug_food_warnings(med)
            if fda_food_warns:
                fda_drug_warnings.append({"drug": med, "fda_warnings": fda_food_warns})

        enriched["grounding"]["drug_food_interactions"] = {
            "warnings": drug_warnings,
            "medication_nutrient_warnings": med_nutrient_warnings,
            "ddinter_results": ddinter_results,
            "fda_drug_label_warnings": fda_drug_warnings,
            "total_interactions": len(drug_warnings) + len(ddinter_results),
            "critical_interactions": [w for w in drug_warnings if w["severity"] == "critical"],
        }
    else:
        print("  [Grounding] Stage 8: No medications provided — skipping drug interaction check.")
        enriched["grounding"]["drug_food_interactions"] = {"warnings": [], "total_interactions": 0}

    # ── Stage 9: Dietary Limit Assessment ────────────────────────────────
    if user_conditions:
        print("  [Grounding] Stage 9: Condition-specific dietary limit check...")
        limits = get_limits_for_conditions(user_conditions)
        enriched["grounding"]["dietary_limits"] = {
            "applicable_conditions": user_conditions,
            "condition_specific_limits": limits,
        }

        # Check specific nutrients from the scanned nutrition table
        if isinstance(nutrition, dict):
            nutrient_checks = {}
            nutrient_mappings = {
                "sodium_mg": ["sodium", "sodium_mg", "salt"],
                "total_sugar_g": ["sugars", "sugar", "total_sugar", "sugars_g"],
                "saturated_fat_g": ["saturated_fat", "sat_fat", "saturated fat"],
                "cholesterol_mg": ["cholesterol", "cholesterol_mg"],
                "fiber_g": ["fiber", "dietary_fiber", "fibre"],
            }
            for limit_key, label_keys in nutrient_mappings.items():
                for lk in label_keys:
                    val = nutrition.get(lk)
                    if val is not None:
                        try:
                            nutrient_checks[limit_key] = check_nutrient_against_limits(
                                limit_key, float(val), user_conditions
                            )
                        except (ValueError, TypeError):
                            pass
                        break
            enriched["grounding"]["nutrient_limit_checks"] = nutrient_checks
    else:
        print("  [Grounding] Stage 9: No conditions provided — using general adult limits.")
        enriched["grounding"]["dietary_limits"] = {"applicable_conditions": [], "note": "General adult limits apply."}

    # ── Stage 10: Dietary Supplement Cross-ref (NIH DSLB — dslb.od.nih.gov) ─
    if ingredients_text:
        print("  [Grounding] Stage 10: NIH DSLB supplement cross-reference...")
        # Check if any ingredients are common supplement ingredients
        supplement_keywords = ["caffeine", "vitamin", "iron", "calcium", "zinc",
                               "magnesium", "creatine", "biotin", "omega", "fish oil",
                               "coq10", "turmeric", "curcumin", "melatonin", "ginseng"]
        dslb_results = []
        for ingredient in [i.strip() for i in ingredients_text.split(",") if i.strip()]:
            if any(kw in ingredient.lower() for kw in supplement_keywords):
                supp_data = dslb_check(ingredient)
                if supp_data:
                    dslb_results.extend(supp_data[:2])
        if dslb_results:
            enriched["grounding"]["dietary_supplements"] = {
                "source": "NIH DSLD (dslb.od.nih.gov)",
                "supplements_found": dslb_results,
            }

    # ── Stage 11: Allergy Check ──────────────────────────────────────────
    if user_allergies and ingredients_text:
        print("  [Grounding] Stage 11: Allergy screening...")
        allergy_warnings = []
        ingredients_lower = ingredients_text.lower()
        for allergen in user_allergies:
            if allergen.lower() in ingredients_lower:
                allergy_warnings.append({
                    "allergen": allergen,
                    "severity": "CRITICAL",
                    "advice": f"CONTAINS {allergen.upper()} — DO NOT CONSUME if allergic.",
                })
        # Also check OFF allergen data
        if off_data and off_data.get("allergens"):
            for allergen in user_allergies:
                if allergen.lower() in off_data["allergens"].lower():
                    if not any(w["allergen"] == allergen for w in allergy_warnings):
                        allergy_warnings.append({
                            "allergen": allergen,
                            "severity": "CRITICAL",
                            "advice": f"DECLARED ALLERGEN: {allergen.upper()} found in product allergen data.",
                        })
        enriched["grounding"]["allergy_warnings"] = allergy_warnings

    # ── Stage 12: FDA Recall + Enforcement Check (open.fda.gov) ──────────
    if product_name:
        print("  [Grounding] Stage 12: FDA recall check (open.fda.gov)...")
        recalls = check_food_recalls(str(product_name), limit=3)
        enriched["grounding"]["fda_recalls"] = {
            "recalls_found": recalls,
            "total_recalls": len(recalls),
        }

    # ── Final: Compute overall risk summary ──────────────────────────────
    enriched["grounding"]["risk_summary"] = _compute_risk_summary(enriched["grounding"])

    print("  [Grounding] Pipeline complete!")
    return enriched


import re as _re


def _extract_brand_name(text: str) -> str:
    """Extract just the company/brand name from a full address string.

    E.g. 'Kellogg Asia Products Sdn Bhd, Lot 1-5, Jalan ...' → 'Kellogg'
    """
    # Take the first segment (before first comma)
    first_part = text.split(",")[0].strip()
    # Remove common corporate suffixes
    suffixes = [
        r"\s+Sdn\.?\s*Bhd\.?", r"\s+Pvt\.?\s*Ltd\.?", r"\s+Pte\.?\s*Ltd\.?",
        r"\s+Inc\.?", r"\s+Corp\.?", r"\s+LLC\.?", r"\s+Ltd\.?", r"\s+Co\.?",
        r"\s+GmbH", r"\s+S\.?A\.?", r"\s+PLC\.?", r"\s+Asia\s+Products?",
        r"\s+International", r"\s+Industries", r"\s+Manufacturing",
    ]
    brand = first_part
    for sfx in suffixes:
        brand = _re.sub(sfx, "", brand, flags=_re.IGNORECASE).strip()
    # If what remains is too long (>30 chars) or empty, just take the first word
    if len(brand) > 30 or not brand:
        brand = first_part.split()[0] if first_part else text.split()[0]
    return brand


def _parse_nutrition_string(text: str) -> dict:
    """Parse a nutrition text blob like 'Energy 523 kcal, Total Fat 27.9 g, ...' into a dict."""
    result = {}
    # Ordered from longest to shortest to avoid partial matches
    # e.g. "trans fatty acids" must match before "fat"
    label_map = [
        ("saturated fatty acids", "saturated_fat"),
        ("trans fatty acids", "trans_fat"),
        ("total carbohydrates", "carbohydrates"),
        ("dietary fiber", "fiber"),
        ("saturated fat", "saturated_fat"),
        ("total sugar", "sugars"),
        ("total fat", "fat"),
        ("trans fat", "trans_fat"),
        ("energy", "calories"),
        ("calories", "calories"),
        ("carbohydrates", "carbohydrates"),
        ("carbs", "carbohydrates"),
        ("sugars", "sugars"),
        ("sugar", "sugars"),
        ("protein", "protein"),
        ("sodium", "sodium"),
        ("cholesterol", "cholesterol"),
        ("fibre", "fiber"),
        ("fiber", "fiber"),
        ("salt", "sodium"),
        ("fat", "fat"),
    ]

    # Strip parenthetical notes like "(per 100 g)"
    text = _re.sub(r"\(per\s+\d+\s*\w*\)", "", text)

    # Split on commas or semicolons
    parts = _re.split(r"[,;]", text)
    for part in parts:
        part = part.strip()
        # Match patterns like "Total Fat 27.9 g" or "Energy 523 kcal"
        match = _re.match(r"^(.+?)\s+([\d.]+)\s*(\w+)?", part)
        if match:
            label = match.group(1).strip().lower()
            value = match.group(2)
            unit = (match.group(3) or "").lower()
            # Find the matching normalized key (longest match first)
            for pattern, key in label_map:
                if pattern in label:
                    try:
                        result[key] = float(value)
                    except ValueError:
                        result[key] = value
                    if key == "sodium" and unit == "mg":
                        result["sodium_mg"] = result[key]
                    break

    return result


def _extract_field(data: dict, possible_keys: list[str]):
    """Extract a field from a dict, trying multiple possible key names (case-insensitive)."""
    if not isinstance(data, dict):
        return None

    # Build a lowercase→original key mapping for case-insensitive lookup
    lower_map = {k.lower(): k for k in data}

    for key in possible_keys:
        actual_key = lower_map.get(key.lower())
        if actual_key and data[actual_key]:
            val = data[actual_key]
            # Handle Azure CU field objects like {"type":"string","valueString":"Tomato"}
            if isinstance(val, dict) and "type" in val:
                for vk in ("valueString", "valueNumber", "valueInteger", "valueBoolean",
                            "valueObject", "valueArray", "value", "content"):
                    if vk in val:
                        return val[vk]
            return val
    # Also check nested structures
    for key in ["result", "data", "fields", "analysis"]:
        actual_key = lower_map.get(key)
        if actual_key and isinstance(data[actual_key], dict):
            nested = data[actual_key]
            nested_lower_map = {k.lower(): k for k in nested}
            for k in possible_keys:
                nk = nested_lower_map.get(k.lower())
                if nk and nested[nk]:
                    val = nested[nk]
                    if isinstance(val, dict) and "type" in val:
                        for vk in ("valueString", "valueNumber", "valueInteger", "valueBoolean",
                                    "valueObject", "valueArray", "value", "content"):
                            if vk in val:
                                return val[vk]
                    return val
    # Check under "contents" → first item → "fields" (Azure CU format)
    contents = data.get("contents", [])
    if isinstance(contents, list) and contents:
        first = contents[0] if isinstance(contents[0], dict) else {}
        fields = first.get("fields", {})
        if isinstance(fields, dict):
            fields_lower_map = {k.lower(): k for k in fields}
            for k in possible_keys:
                fk = fields_lower_map.get(k.lower())
                if fk and fields[fk]:
                    val = fields[fk]
                    if isinstance(val, dict) and "type" in val:
                        for vk in ("valueString", "valueNumber", "valueInteger", "valueBoolean",
                                    "valueObject", "valueArray", "value", "content"):
                            if vk in val:
                                return val[vk]
                    return val
    return None


def _compute_risk_summary(grounding: dict) -> dict:
    """Compute an overall risk summary from all grounding data."""
    risks = []

    # Additive risks
    additives = grounding.get("additives_analysis", {})
    avoid_count = len(additives.get("avoid_additives", []))
    caution_count = len(additives.get("caution_additives", []))
    if avoid_count > 0:
        risks.append({"source": "additives", "level": "high", "detail": f"{avoid_count} additive(s) rated AVOID"})
    if caution_count > 0:
        risks.append({"source": "additives", "level": "medium", "detail": f"{caution_count} additive(s) rated CAUTION"})

    # NOVA risk
    nova = grounding.get("nova_classification", {})
    if nova.get("nova_group") == 4:
        risks.append({"source": "processing", "level": "high", "detail": "NOVA Group 4: Ultra-processed food"})
    elif nova.get("nova_group") == 3:
        risks.append({"source": "processing", "level": "medium", "detail": "NOVA Group 3: Processed food"})

    # Carcinogen risk
    iarc = grounding.get("iarc_carcinogens", {})
    if iarc.get("group_1_agents"):
        risks.append({"source": "carcinogens", "level": "critical", "detail": f"IARC Group 1 carcinogen(s) detected"})
    if iarc.get("group_2A_agents"):
        risks.append({"source": "carcinogens", "level": "high", "detail": f"IARC Group 2A probable carcinogen(s) detected"})

    # Drug interaction risk
    drug_int = grounding.get("drug_food_interactions", {})
    if drug_int.get("critical_interactions"):
        risks.append({"source": "drug_interactions", "level": "critical", "detail": "CRITICAL drug-food interaction detected"})
    elif drug_int.get("total_interactions", 0) > 0:
        risks.append({"source": "drug_interactions", "level": "high", "detail": f"{drug_int['total_interactions']} drug-food interaction(s)"})

    # Allergy risk
    allergies = grounding.get("allergy_warnings", [])
    if allergies:
        risks.append({"source": "allergies", "level": "critical", "detail": f"Contains {len(allergies)} declared allergen(s)"})

    # FDA recalls
    recalls = grounding.get("fda_recalls", {})
    if recalls.get("total_recalls", 0) > 0:
        risks.append({"source": "fda_recall", "level": "high", "detail": f"{recalls['total_recalls']} FDA recall(s) found"})

    # Determine overall verdict
    levels = [r["level"] for r in risks]
    if "critical" in levels:
        overall = "AVOID"
    elif "high" in levels:
        overall = "CAUTION"
    elif "medium" in levels:
        overall = "CAUTION"
    else:
        overall = "SAFE"

    return {
        "overall_verdict": overall,
        "risk_factors": risks,
        "total_risk_factors": len(risks),
    }


def format_grounding_for_agents(enriched_data: dict) -> str:
    """
    Format the enriched data as a structured text block for agent consumption.
    This is injected into the debate prompt so all agents have the grounding context.
    """
    g = enriched_data.get("grounding", {})
    raw = enriched_data.get("raw_data", {})
    profile = enriched_data.get("user_profile", {})

    sections = []

    # Header
    sections.append("=" * 70)
    sections.append("GROUNDED FOOD ANALYSIS — DATA FOR EXPERT PANEL")
    sections.append("=" * 70)

    # Raw extracted data
    sections.append("\n## RAW SCAN DATA (from food label OCR)")
    sections.append(json.dumps(raw, indent=2, ensure_ascii=False, default=str))

    # User profile
    if any(profile.values()):
        sections.append("\n## USER HEALTH PROFILE")
        if profile.get("conditions"):
            sections.append(f"  Medical Conditions: {', '.join(profile['conditions'])}")
        if profile.get("medications"):
            sections.append(f"  Current Medications: {', '.join(profile['medications'])}")
        if profile.get("allergies"):
            sections.append(f"  Known Allergies: {', '.join(profile['allergies'])}")

    # Overall risk summary
    summary = g.get("risk_summary", {})
    sections.append(f"\n## OVERALL RISK VERDICT: {summary.get('overall_verdict', 'UNKNOWN')}")
    for rf in summary.get("risk_factors", []):
        sections.append(f"  [{rf['level'].upper()}] {rf['source']}: {rf['detail']}")

    # Open Food Facts data
    off = g.get("open_food_facts")
    if off:
        sections.append("\n## OPEN FOOD FACTS PRODUCT DATA")
        sections.append(f"  Product: {off.get('product_name', 'N/A')}")
        sections.append(f"  Brand: {off.get('brands', 'N/A')}")
        sections.append(f"  Nutri-Score: {off.get('nutriscore_grade', 'N/A').upper()}")
        sections.append(f"  NOVA Group: {off.get('nova_group', 'N/A')}")
        sections.append(f"  Allergens: {off.get('allergens', 'None declared')}")
        sections.append(f"  Additives: {', '.join(off.get('additives_tags', [])) or 'None'}")
        npp = off.get("nutrition_per_100g", {})
        if npp:
            sections.append("  Nutrition per 100g:")
            for k, v in npp.items():
                if v is not None:
                    sections.append(f"    {k}: {v}")

    # USDA data
    usda = g.get("usda_nutrients")
    if usda:
        sections.append("\n## USDA FOODDATA CENTRAL")
        sections.append(f"  Description: {usda.get('description', 'N/A')}")
        nutrients = usda.get("nutrients", {})
        if nutrients:
            sections.append("  Key Nutrients:")
            for name, info in list(nutrients.items())[:20]:
                sections.append(f"    {name}: {info.get('value', '')} {info.get('unit', '')}")

    # Additive analysis
    add = g.get("additives_analysis", {})
    if add.get("total_additives", 0) > 0:
        sections.append(f"\n## ADDITIVE ANALYSIS ({add['total_additives']} additives found)")
        for a in add.get("avoid_additives", []):
            sections.append(f"  ❌ AVOID: {a.get('name', a.get('matched_term'))} ({a.get('e_number', '')}) — {'; '.join(a.get('concerns', []))}")
        for a in add.get("caution_additives", []):
            sections.append(f"  ⚠️ CAUTION: {a.get('name', a.get('matched_term'))} ({a.get('e_number', '')}) — {'; '.join(a.get('concerns', []))}")
        for a in add.get("safe_additives", []):
            sections.append(f"  ✅ SAFE: {a.get('name', a.get('matched_term'))} ({a.get('e_number', '')})")

    # NOVA
    nova = g.get("nova_classification", {})
    if nova.get("nova_group"):
        sections.append(f"\n## NOVA CLASSIFICATION: Group {nova['nova_group']} — {nova.get('nova_name', '')}")
        sections.append(f"  Risk Level: {nova.get('risk_level', 'unknown')}")
        sections.append(f"  Processing Markers Found: {nova.get('total_processing_markers', 0)}")
        if nova.get("markers_found"):
            sections.append(f"  Markers: {', '.join(nova['markers_found'])}")
        sections.append(f"  Health Advice: {nova.get('health_advice', '')}")

    # IARC Carcinogens
    iarc = g.get("iarc_carcinogens", {})
    if iarc.get("total_carcinogenic_agents", 0) > 0:
        sections.append(f"\n## IARC CARCINOGEN SCREENING ({iarc['total_carcinogenic_agents']} agents found)")
        for c in iarc.get("found", []):
            sections.append(f"  Group {c['iarc_group']}: {c['agent']} (matched: {', '.join(c['matched_in_ingredients'])})")
            sections.append(f"    Cancer sites: {', '.join(c['cancer_sites'])}")
            sections.append(f"    Advice: {c['advice']}")

    # Glycemic Index
    gi = g.get("glycemic_index", {})
    if gi.get("ingredients_with_gi_data"):
        sections.append("\n## GLYCEMIC INDEX DATA (Source: Blob-backed GI DB)")
        for item in gi["ingredients_with_gi_data"]:
            sections.append(f"  {item['food']}: GI={item['gi']} ({item['gi_category']}), GL={item['gl']} ({item['gl_category']})")
        hi = gi.get("highest_gi_ingredient")
        if hi:
            sections.append(f"  ⚡ Highest GI ingredient: {hi['food']} (GI={hi['gi']})")

    # Drug interactions
    drug = g.get("drug_food_interactions", {})
    if drug.get("total_interactions", 0) > 0:
        sections.append(f"\n## ⚠️ DRUG-FOOD INTERACTIONS ({drug['total_interactions']} found)")
        sections.append("  Sources: DDInter2 (ddinter2.scbdd.com), FDA Drug Labels (open.fda.gov/apis/drug/), knowledge DB")
        for w in drug.get("warnings", []):
            sections.append(f"  [{w['severity'].upper()}] {w['drug']} × {', '.join(w['matched_foods_in_product'])}")
            sections.append(f"    Mechanism: {w['mechanism']}")
            sections.append(f"    Advice: {w['advice']}")
            sections.append(f"    Danger: {w['danger']}")
        # DDInter results
        for dd in drug.get("ddinter_results", []):
            sections.append(f"  [DDInter] {dd.get('drug_a', '')} × {dd.get('drug_b', '')} — severity: {dd.get('severity', 'unknown')}")
            if dd.get("mechanism"):
                sections.append(f"    Mechanism: {dd['mechanism']}")
        # FDA drug label warnings
        for fda_w in drug.get("fda_drug_label_warnings", []):
            sections.append(f"  [FDA Label] {fda_w.get('drug', '')}: {'; '.join(fda_w.get('fda_warnings', []))[:200]}")

    # Allergy warnings
    allergies = g.get("allergy_warnings", [])
    if allergies:
        sections.append("\n## 🚨 ALLERGY WARNINGS")
        for a in allergies:
            sections.append(f"  [{a['severity']}] {a['allergen']}: {a['advice']}")

    # Dietary limits
    checks = g.get("nutrient_limit_checks", {})
    if checks:
        sections.append("\n## NUTRIENT vs. CONDITION-SPECIFIC LIMITS (Sources: WHO, NIH, AHA, ADA, KDOQI)")
        for nutrient, check in checks.items():
            status_icon = {"safe": "✅", "caution": "⚠️", "danger": "❌"}.get(check["status"], "❓")
            sections.append(f"  {status_icon} {nutrient}: {check.get('value', 'N/A')} (limit: {check.get('limit', 'N/A')}) — {check['status'].upper()}")
            sections.append(f"    {check.get('explanation', '')}")

    # FooDB compounds
    foodb_cmp = g.get("foodb_compounds", [])
    if foodb_cmp:
        sections.append(f"\n## FOOD COMPOSITION (Source: foodb.ca — {len(foodb_cmp)} compounds)")
        for c in foodb_cmp:
            conc = c.get("concentration", "")
            unit = c.get("unit", "")
            amount_str = f" — {conc} {unit}" if conc else ""
            sections.append(f"  {c.get('compound_name', 'N/A')} ({c.get('compound_type', '')}){amount_str}")

    # NIH DSLB supplements
    supps = g.get("dietary_supplements", {})
    if supps.get("supplements_found"):
        sections.append(f"\n## DIETARY SUPPLEMENT CROSS-REFERENCE (Source: dslb.od.nih.gov)")
        for s in supps["supplements_found"]:
            sections.append(f"  {s.get('ingredient_name', s.get('product_name', 'N/A'))}: {s.get('amount', '')} {s.get('unit', '')} (DV: {s.get('daily_value_pct', 'N/A')}%)")

    # FDA Recalls
    recalls = g.get("fda_recalls", {})
    if recalls.get("total_recalls", 0) > 0:
        sections.append(f"\n## FDA RECALLS (Source: open.fda.gov — {recalls['total_recalls']} found)")
        for r in recalls.get("recalls_found", []):
            sections.append(f"  {r.get('recall_date', 'N/A')}: {r.get('reason_for_recall', 'N/A')}")
            sections.append(f"    Classification: {r.get('classification', 'N/A')}, Status: {r.get('status', 'N/A')}")

    # Knowledge source attribution
    sections.append("\n## KNOWLEDGE SOURCES USED")
    sections.append("  APIs: fdc.nal.usda.gov | foodb.ca | ddinter2.scbdd.com")
    sections.append("  APIs: open.fda.gov | open.fda.gov/apis/drug/ | dslb.od.nih.gov")
    sections.append("  Blob: additives | dietary_limits | drug_food_interactions")
    sections.append("  Blob: glycemic_index | iarc_carcinogens | nova_classification")

    sections.append("\n" + "=" * 70)
    return "\n".join(sections)
