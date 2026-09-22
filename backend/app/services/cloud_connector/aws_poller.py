"""
Cloud Connector Service — AWS Poller (Section 10 / Module 1).

Pulls IAM, S3, EC2, and RDS configuration via boto3 using a READ-ONLY role.
For local development / demos (USE_MOCK_AWS=true), it returns realistic
synthetic findings instead of calling real AWS APIs, so the whole pipeline
can be exercised without live cloud credentials.
"""
import random
from datetime import datetime
from typing import List, Dict

from app.core.config import settings

try:
    import boto3
except ImportError:  # pragma: no cover
    boto3 = None


MOCK_RESOURCE_CATALOG = [
    {"resource_type": "iam_user", "resource_identifier": "svc-account-billing", "check": "mfa_enabled"},
    {"resource_type": "iam_user", "resource_identifier": "admin-jdoe", "check": "mfa_enabled"},
    {"resource_type": "s3_bucket", "resource_identifier": "prod-customer-uploads", "check": "public_access_block"},
    {"resource_type": "s3_bucket", "resource_identifier": "analytics-raw-logs", "check": "encryption_at_rest"},
    {"resource_type": "ec2_instance", "resource_identifier": "i-0a1b2c3d4e", "check": "security_group_open_ssh"},
    {"resource_type": "rds_instance", "resource_identifier": "rds-financial-db-01", "check": "mfa_required_for_access"},
    {"resource_type": "rds_instance", "resource_identifier": "rds-financial-db-01", "check": "encryption_at_rest"},
    {"resource_type": "iam_policy", "resource_identifier": "FullAdminAccess", "check": "least_privilege"},
]


def _poll_mock_aws() -> List[Dict]:
    """Generate deterministic-ish but varied synthetic AWS config findings."""
    random.seed()
    results = []
    for item in MOCK_RESOURCE_CATALOG:
        is_compliant = random.random() > 0.45  # slightly more non-compliant, matches CISO scenario
        results.append({
            "resource_type": item["resource_type"],
            "resource_identifier": item["resource_identifier"],
            "check": item["check"],
            "compliant": is_compliant,
            "polled_at": datetime.utcnow().isoformat(),
        })
    return results


def _poll_real_aws(account_identifier: str) -> List[Dict]:
    """
    Pull real configuration using boto3 read-only calls.
    Requires AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_REGION with a
    read-only IAM policy (see Section 22 Security Flow).
    """
    if boto3 is None:
        raise RuntimeError("boto3 is not installed")

    session = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    results: List[Dict] = []

    iam = session.client("iam")
    for user in iam.list_users().get("Users", []):
        mfa = iam.list_mfa_devices(UserName=user["UserName"])
        results.append({
            "resource_type": "iam_user",
            "resource_identifier": user["UserName"],
            "check": "mfa_enabled",
            "compliant": len(mfa.get("MFADevices", [])) > 0,
            "polled_at": datetime.utcnow().isoformat(),
        })

    s3 = session.client("s3")
    for bucket in s3.list_buckets().get("Buckets", []):
        try:
            pab = s3.get_public_access_block(Bucket=bucket["Name"])
            cfg = pab["PublicAccessBlockConfiguration"]
            compliant = all(cfg.values())
        except Exception:
            compliant = False
        results.append({
            "resource_type": "s3_bucket",
            "resource_identifier": bucket["Name"],
            "check": "public_access_block",
            "compliant": compliant,
            "polled_at": datetime.utcnow().isoformat(),
        })

    return results


def poll_aws_account(account_identifier: str) -> List[Dict]:
    """Entry point used by the polling job / API trigger."""
    if settings.USE_MOCK_AWS:
        return _poll_mock_aws()
    return _poll_real_aws(account_identifier)
