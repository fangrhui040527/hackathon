"""
tools/agent_tools.py
API-backed @ai_function tools that agents can call during their analysis.

Each tool is a callable the Agent Framework passes to GPT-4o as a function tool.
The agent decides WHEN to call each tool based on its analysis needs.

Sources:
  1. fdc.nal.usda.gov          — USDA FoodData Central
  2. foodb.ca                  — FooDB food composition
  3. ddinter2.scbdd.com        — DDInter drug interactions
  4. open.fda.gov              — FDA food safety (recalls, enforcement)
  5. open.fda.gov/apis/drug/   — FDA drug labels & warnings
  6. dslb.od.nih.gov           — NIH Dietary Supplement Label Database
"""

import json
from agent_framework import ai_function

# Import existing API wrappers
from tools.usda_api import search_foods as _usda_search
from tools.foodb_api import search_foods as _foodb_search, get_food_nutrients as _foodb_nutrients
from tools.ddinter_api import check_drug_food_interactions as _ddinter_check
from tools.openfda_api import (
    check_food_recalls as _fda_recalls,
    get_drug_food_warnings as _fda_drug_warnings,
    search_drug_label as _fda_drug_label,
)
from tools.dslb_api import check_ingredient_in_supplements as _dslb_check


# ═══════════════════════════════════════════════════════════════════════
# 1. USDA FoodData Central (fdc.nal.usda.gov)
# ═══════════════════════════════════════════════════════════════════════

@ai_function(
    name="search_usda",
    description="Search USDA FoodData Central (fdc.nal.usda.gov) for nutrient data on a food item. Returns calories, macros, micros, serving sizes.",
)
def search_usda(query: str) -> str:
    """Search USDA for nutrient information about a food."""
    results = _usda_search(query, page_size=3)
    return json.dumps(results, default=str) if results else "No USDA results found."


# ═══════════════════════════════════════════════════════════════════════
# 2. FooDB (foodb.ca)
# ═══════════════════════════════════════════════════════════════════════

@ai_function(
    name="search_foodb",
    description="Search FooDB (foodb.ca) for chemical compounds in a food — nutrients, flavors, toxins, bioactive compounds.",
)
def search_foodb(food_name: str) -> str:
    """Search FooDB for food composition and compounds."""
    results = _foodb_nutrients(food_name)
    if not results:
        results = _foodb_search(food_name, limit=3)
    return json.dumps(results, default=str) if results else "No FooDB results found."


# ═══════════════════════════════════════════════════════════════════════
# 3. DDInter (ddinter2.scbdd.com)
# ═══════════════════════════════════════════════════════════════════════

@ai_function(
    name="check_ddinter_interactions",
    description="Check DDInter (ddinter2.scbdd.com) for drug-food interactions. Provide a drug name and comma-separated food ingredients.",
)
def check_ddinter_interactions(drug_name: str, food_ingredients: str) -> str:
    """Check DDInter for drug-food interactions."""
    ingredients_list = [i.strip() for i in food_ingredients.split(",") if i.strip()]
    results = _ddinter_check(drug_name, ingredients_list)
    return json.dumps(results, default=str) if results else "No DDInter interactions found."


# ═══════════════════════════════════════════════════════════════════════
# 5. FDA Food Safety (open.fda.gov)
# ═══════════════════════════════════════════════════════════════════════

@ai_function(
    name="check_fda_food_recalls",
    description="Check FDA (open.fda.gov) for food recalls and safety alerts related to a product or ingredient.",
)
def check_fda_food_recalls(product_name: str) -> str:
    """Check FDA for food recalls on a product."""
    results = _fda_recalls(product_name)
    return json.dumps(results, default=str) if results else "No FDA food recalls found."


# ═══════════════════════════════════════════════════════════════════════
# 6. FDA Drug Labels (open.fda.gov/apis/drug/)
# ═══════════════════════════════════════════════════════════════════════

@ai_function(
    name="check_fda_drug_warnings",
    description="Search FDA drug labels (open.fda.gov/apis/drug/) for food interaction warnings, contraindications, and precautions for a medication.",
)
def check_fda_drug_warnings(drug_name: str) -> str:
    """Get FDA drug label food interaction warnings."""
    warnings = _fda_drug_warnings(drug_name)
    if warnings:
        return json.dumps(warnings, default=str)
    # Fallback to full label search
    labels = _fda_drug_label(drug_name, limit=1)
    return json.dumps(labels, default=str) if labels else "No FDA drug label found."


# ═══════════════════════════════════════════════════════════════════════
# 7. NIH Dietary Supplement Label Database (dslb.od.nih.gov)
# ═══════════════════════════════════════════════════════════════════════

@ai_function(
    name="check_nih_supplements",
    description="Search NIH DSLD (dslb.od.nih.gov) for dietary supplement information — check if a food ingredient appears in supplements and typical dosages.",
)
def check_nih_supplements(ingredient: str) -> str:
    """Check NIH DSLD for supplement information about an ingredient."""
    results = _dslb_check(ingredient)
    return json.dumps(results, default=str) if results else "No NIH DSLD results found."


# ═══════════════════════════════════════════════════════════════════════
# Tool groups per agent
# ═══════════════════════════════════════════════════════════════════════

DOCTOR_TOOLS = [
    check_ddinter_interactions,     # ddinter2.scbdd.com
    check_fda_drug_warnings,        # open.fda.gov/apis/drug/
    check_fda_food_recalls,         # open.fda.gov
    check_nih_supplements,          # dslb.od.nih.gov
]

NUTRITIONIST_TOOLS = [
    search_usda,                    # fdc.nal.usda.gov
    search_foodb,                   # foodb.ca
    check_nih_supplements,          # dslb.od.nih.gov
]

CHEMIST_TOOLS = [
    search_foodb,                   # foodb.ca
    check_fda_food_recalls,         # open.fda.gov
]

FITNESS_TOOLS = [
    search_usda,                    # fdc.nal.usda.gov
    check_nih_supplements,          # dslb.od.nih.gov
]

HEALTH_TOOLS = [
    check_fda_food_recalls,         # open.fda.gov
    check_fda_drug_warnings,        # open.fda.gov/apis/drug/
    check_ddinter_interactions,     # ddinter2.scbdd.com
]
