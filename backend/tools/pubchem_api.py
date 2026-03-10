"""
tools/pubchem_api.py
PubChem API wrapper — chemical compound lookup for food additives and chemicals.
Docs: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest
"""

import requests
from typing import Optional

BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
TIMEOUT = 15


def get_compound_by_name(compound_name: str) -> Optional[dict]:
    """
    Look up a chemical compound by name and return safety/toxicity info.
    """
    # First, get the CID
    cid = _get_cid_by_name(compound_name)
    if not cid:
        return None

    # Then get compound properties and safety
    properties = _get_compound_properties(cid)
    hazards = _get_ghs_hazards(cid)

    return {
        "source": "PubChem",
        "compound_name": compound_name,
        "cid": cid,
        "properties": properties,
        "ghs_hazards": hazards,
    }


def _get_cid_by_name(name: str) -> Optional[int]:
    """Get PubChem Compound ID (CID) from a chemical name."""
    url = f"{BASE_URL}/compound/name/{name}/cids/JSON"
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        cids = data.get("IdentifierList", {}).get("CID", [])
        return cids[0] if cids else None
    except Exception:
        return None


def _get_compound_properties(cid: int) -> dict:
    """Get molecular properties for a compound."""
    url = (
        f"{BASE_URL}/compound/cid/{cid}/property/"
        "MolecularFormula,MolecularWeight,IUPACName,IsomericSMILES/JSON"
    )
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        props = data.get("PropertyTable", {}).get("Properties", [{}])[0]
        return {
            "molecular_formula": props.get("MolecularFormula", ""),
            "molecular_weight": props.get("MolecularWeight", ""),
            "iupac_name": props.get("IUPACName", ""),
        }
    except Exception:
        return {}


def _get_ghs_hazards(cid: int) -> list[str]:
    """
    Get GHS (Globally Harmonized System) hazard classifications.
    These indicate if a substance is toxic, carcinogenic, etc.
    """
    url = (
        f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}"
        "/JSON?heading=GHS+Classification"
    )
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()

        hazards = []
        # Navigate the nested PubChem view structure
        record = data.get("Record", {})
        for section in record.get("Section", []):
            for subsection in section.get("Section", []):
                for subsubsection in subsection.get("Section", []):
                    heading = subsubsection.get("TOCHeading", "")
                    if "Hazard Statements" in heading:
                        for info in subsubsection.get("Information", []):
                            value = info.get("Value", {})
                            for sv in value.get("StringWithMarkup", []):
                                stmt = sv.get("String", "")
                                if stmt:
                                    hazards.append(stmt)
        return hazards
    except Exception:
        return []


def batch_check_compounds(compound_names: list[str]) -> dict[str, Optional[dict]]:
    """
    Check multiple compounds at once. Returns a dict mapping name -> result.
    """
    results = {}
    for name in compound_names:
        results[name] = get_compound_by_name(name)
    return results
