"""
Seed data for the six NIST CSF 2.0 functions and a representative set of
subcategories, plus the Framework Mapping Matrix (technical check -> NIST
subcategory). This is the "lookup table" described in Section 9.

NOTE: This is a representative subset for demo purposes, not the full,
official 100+ subcategory catalog. Mayank/Divyansh's validation task
(Section 31.2) is to confirm and extend this against the real NIST CSF 2.0
publication.
"""

NIST_FUNCTIONS = [
    {"function_id": "GV", "function_name": "Govern"},
    {"function_id": "ID", "function_name": "Identify"},
    {"function_id": "PR", "function_name": "Protect"},
    {"function_id": "DE", "function_name": "Detect"},
    {"function_id": "RS", "function_name": "Respond"},
    {"function_id": "RC", "function_name": "Recover"},
]

NIST_SUBCATEGORIES = [
    {"subcategory_id": "GV.OC-01", "function_id": "GV", "description": "Organizational mission is understood and informs cybersecurity risk management."},
    {"subcategory_id": "GV.RM-01", "function_id": "GV", "description": "Risk management objectives are established and agreed to by stakeholders."},
    {"subcategory_id": "ID.AM-02", "function_id": "ID", "description": "Software platforms and applications within the organization are inventoried."},
    {"subcategory_id": "ID.RA-01", "function_id": "ID", "description": "Vulnerabilities in assets are identified and documented."},
    {"subcategory_id": "PR.AA-05", "function_id": "PR", "description": "Access permissions and authorizations are managed, enforced (least privilege / MFA)."},
    {"subcategory_id": "PR.DS-01", "function_id": "PR", "description": "The confidentiality, integrity, and availability of data-at-rest are protected."},
    {"subcategory_id": "PR.PS-01", "function_id": "PR", "description": "Configuration management practices are established and applied."},
    {"subcategory_id": "DE.CM-01", "function_id": "DE", "description": "Networks and network services are monitored to find potentially adverse events."},
    {"subcategory_id": "DE.CM-09", "function_id": "DE", "description": "Computing hardware and software are monitored for unauthorized changes."},
    {"subcategory_id": "RS.MA-01", "function_id": "RS", "description": "The incident response plan is executed once an incident is declared."},
    {"subcategory_id": "RC.RP-01", "function_id": "RC", "description": "The recovery portion of the incident response plan is executed."},
]

# Maps a (resource_type, check) pair from a cloud poller finding to a NIST subcategory.
FRAMEWORK_MAPPING_MATRIX = {
    ("iam_user", "mfa_enabled"): "PR.AA-05",
    ("aad_user", "mfa_enabled"): "PR.AA-05",
    ("rds_instance", "mfa_required_for_access"): "PR.AA-05",
    ("iam_policy", "least_privilege"): "PR.AA-05",
    ("s3_bucket", "public_access_block"): "PR.DS-01",
    ("s3_bucket", "encryption_at_rest"): "PR.DS-01",
    ("rds_instance", "encryption_at_rest"): "PR.DS-01",
    ("storage_account", "encryption_at_rest"): "PR.DS-01",
    ("ec2_instance", "security_group_open_ssh"): "PR.PS-01",
    ("nsg", "no_open_rdp"): "PR.PS-01",
}

# Rough asset-value / severity table used as Monte Carlo simulation inputs (Section 28-29).
# In a production system these would come from an asset inventory / business-impact analysis.
ASSET_VALUE_BY_RESOURCE_TYPE = {
    "rds_instance": 5_000_000,
    "s3_bucket": 1_500_000,
    "iam_user": 800_000,
    "iam_policy": 1_000_000,
    "ec2_instance": 600_000,
    "aad_user": 800_000,
    "storage_account": 1_500_000,
    "nsg": 600_000,
}

SEVERITY_LIKELIHOOD = {
    # Annual probability of exploitation given the gap remains open
    "low": 0.05,
    "medium": 0.15,
    "high": 0.30,
    "critical": 0.45,
}
