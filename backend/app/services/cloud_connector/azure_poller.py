"""
Cloud Connector Service — Azure Poller (stub / stretch goal, Section 30).

Mirrors aws_poller.py's interface so the Mapping/Scoring/Risk pipeline is
provider-agnostic. Real integration would use the Azure SDK
(azure-identity + azure-mgmt-*) with a read-only service principal.
"""
import random
from datetime import datetime
from typing import List, Dict

MOCK_AZURE_CATALOG = [
    {"resource_type": "aad_user", "resource_identifier": "svc-billing@corp.onmicrosoft.com", "check": "mfa_enabled"},
    {"resource_type": "storage_account", "resource_identifier": "prodstorageacct01", "check": "encryption_at_rest"},
    {"resource_type": "nsg", "resource_identifier": "nsg-app-tier", "check": "no_open_rdp"},
]


def poll_azure_account(account_identifier: str) -> List[Dict]:
    random.seed()
    results = []
    for item in MOCK_AZURE_CATALOG:
        results.append({
            "resource_type": item["resource_type"],
            "resource_identifier": item["resource_identifier"],
            "check": item["check"],
            "compliant": random.random() > 0.4,
            "polled_at": datetime.utcnow().isoformat(),
        })
    return results
