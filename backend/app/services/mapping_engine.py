"""
Framework Mapping Matrix (Section 9/10, Module 2).

Stateless service that takes a normalized cloud-poller finding and tags it
with the correct NIST CSF 2.0 function + subcategory, and assigns a severity.
"""
from typing import Dict, Optional

from app.data.nist_csf_seed import FRAMEWORK_MAPPING_MATRIX

# Simple severity heuristic per check type; a real system would derive this
# from asset criticality + exploitability data.
CHECK_SEVERITY = {
    "mfa_enabled": "critical",
    "mfa_required_for_access": "critical",
    "public_access_block": "high",
    "encryption_at_rest": "high",
    "security_group_open_ssh": "high",
    "no_open_rdp": "high",
    "least_privilege": "medium",
}


def map_finding_to_subcategory(resource_type: str, check: str) -> Optional[str]:
    return FRAMEWORK_MAPPING_MATRIX.get((resource_type, check))


def severity_for_check(check: str) -> str:
    return CHECK_SEVERITY.get(check, "medium")


def normalize_and_map(raw_finding: Dict) -> Dict:
    """
    Takes one raw poller finding (resource_type, resource_identifier, check,
    compliant) and returns a normalized finding record ready to persist,
    tagged with subcategory_id and severity.
    """
    subcategory_id = map_finding_to_subcategory(raw_finding["resource_type"], raw_finding["check"])
    return {
        "resource_type": raw_finding["resource_type"],
        "resource_identifier": raw_finding["resource_identifier"],
        "subcategory_id": subcategory_id,
        "finding_status": "compliant" if raw_finding["compliant"] else "non_compliant",
        "severity": None if raw_finding["compliant"] else severity_for_check(raw_finding["check"]),
    }
