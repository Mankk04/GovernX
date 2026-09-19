"""
Maturity Scoring Engine (Section 10, Module 3).

Aggregates findings per NIST CSF 2.0 function and computes a maturity tier
(1 = Partial, 2 = Risk Informed, 3 = Repeatable, 4 = Adaptive) using a
severity-weighted pass rate.
"""
from collections import defaultdict
from typing import Dict, List

SEVERITY_WEIGHT = {"low": 1, "medium": 2, "high": 3, "critical": 4, None: 0}


def _tier_from_score(pass_rate: float) -> int:
    """Maps a weighted pass rate (0.0 - 1.0) onto a NIST maturity tier."""
    if pass_rate >= 0.90:
        return 4  # Adaptive
    if pass_rate >= 0.70:
        return 3  # Repeatable
    if pass_rate >= 0.40:
        return 2  # Risk Informed
    return 1  # Partial


def calculate_maturity_tiers(findings: List[Dict]) -> Dict[str, int]:
    """
    findings: list of dicts with keys subcategory_id (mapped to a function
    via NIST_SUBCATEGORIES), finding_status, severity.
    Returns {function_id: tier_level}.
    """
    from app.data.nist_csf_seed import NIST_SUBCATEGORIES

    subcat_to_function = {s["subcategory_id"]: s["function_id"] for s in NIST_SUBCATEGORIES}

    weighted_total = defaultdict(float)
    weighted_pass = defaultdict(float)

    for f in findings:
        function_id = subcat_to_function.get(f.get("subcategory_id"))
        if not function_id:
            continue
        weight = SEVERITY_WEIGHT.get(f.get("severity"), 1) or 1
        weighted_total[function_id] += weight
        if f["finding_status"] == "compliant":
            weighted_pass[function_id] += weight

    tiers = {}
    for function_id in {s["function_id"] for s in NIST_SUBCATEGORIES}:
        total = weighted_total[function_id]
        tiers[function_id] = _tier_from_score(weighted_pass[function_id] / total) if total > 0 else 1
    return tiers
