"""Unit tests for the Framework Mapping Matrix (Section 27, validated per Mayank's KPI)."""
from app.services.mapping_engine import normalize_and_map


def test_mfa_finding_maps_to_pr_aa_05():
    raw = {"resource_type": "iam_user", "resource_identifier": "test-user", "check": "mfa_enabled", "compliant": False}
    mapped = normalize_and_map(raw)
    assert mapped["subcategory_id"] == "PR.AA-05"
    assert mapped["finding_status"] == "non_compliant"
    assert mapped["severity"] == "critical"


def test_compliant_finding_has_no_severity():
    raw = {"resource_type": "iam_user", "resource_identifier": "test-user", "check": "mfa_enabled", "compliant": True}
    mapped = normalize_and_map(raw)
    assert mapped["finding_status"] == "compliant"
    assert mapped["severity"] is None
