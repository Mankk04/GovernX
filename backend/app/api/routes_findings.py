"""
Findings routes (Section 19): triggers a full poll->map->score->risk cycle
for an account, lists findings, and supports engineer acknowledgment.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.models import CloudAccount, ConfigFinding, RiskAssessment, MaturityScore, AppUser
from app.schemas.schemas import FindingOut, FindingAcknowledge
from app.services.cloud_connector.aws_poller import poll_aws_account
from app.services.cloud_connector.azure_poller import poll_azure_account
from app.services.mapping_engine import normalize_and_map
from app.services.scoring_engine import calculate_maturity_tiers
from app.services.risk_quantifier import quantify_finding_risk
from app.services.audit_logger import write_audit_log

router = APIRouter(prefix="/api/v1/findings", tags=["findings"])


@router.post("/scan/{account_id}")
def trigger_scan(account_id: str, db: Session = Depends(get_db),
                  current_user: AppUser = Depends(require_roles("admin", "engineer"))):
    """
    Runs the full Continuous Integration Engine cycle for one cloud account:
    poll -> normalize/map -> persist findings -> recalc maturity -> run Monte
    Carlo risk quantification on every open (non-compliant) finding.
    """
    account = db.query(CloudAccount).filter(
        CloudAccount.account_id == account_id, CloudAccount.org_id == current_user.org_id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Cloud account not found")

    raw_findings = poll_aws_account(account.account_identifier) if account.provider == "aws" \
        else poll_azure_account(account.account_identifier)

    created_findings = []
    for raw in raw_findings:
        mapped = normalize_and_map(raw)
        finding = ConfigFinding(
            account_id=account.account_id,
            resource_type=mapped["resource_type"],
            resource_identifier=mapped["resource_identifier"],
            subcategory_id=mapped["subcategory_id"],
            finding_status=mapped["finding_status"],
            severity=mapped["severity"],
        )
        db.add(finding)
        db.flush()

        if finding.finding_status == "non_compliant":
            risk = quantify_finding_risk(finding.resource_type, finding.severity)
            db.add(RiskAssessment(
                finding_id=finding.finding_id,
                annualized_loss_expectancy=risk["annualized_loss_expectancy"],
                value_at_risk=risk["value_at_risk"],
            ))
        created_findings.append(finding)

    db.commit()

    # Recalculate maturity tiers for the whole org based on all findings on record
    all_org_findings = (
        db.query(ConfigFinding)
        .join(CloudAccount)
        .filter(CloudAccount.org_id == current_user.org_id)
        .all()
    )
    findings_as_dicts = [
        {"subcategory_id": f.subcategory_id, "finding_status": f.finding_status, "severity": f.severity}
        for f in all_org_findings
    ]
    tiers = calculate_maturity_tiers(findings_as_dicts)
    for function_id, tier_level in tiers.items():
        db.add(MaturityScore(org_id=current_user.org_id, function_id=function_id, tier_level=tier_level))
    db.commit()

    write_audit_log(db, user_id=current_user.user_id, action="scan_triggered",
                     details={"account_id": account_id, "findings_created": len(created_findings)})

    return {"account_id": account_id, "findings_scanned": len(created_findings), "maturity_tiers": tiers}


@router.get("", response_model=List[FindingOut])
def list_findings(
    status: Optional[str] = Query(None, description="Filter by finding_status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    q = db.query(ConfigFinding).join(CloudAccount).filter(CloudAccount.org_id == current_user.org_id)
    if status:
        q = q.filter(ConfigFinding.finding_status == status)
    if severity:
        q = q.filter(ConfigFinding.severity == severity)
    return q.order_by(ConfigFinding.scanned_at.desc()).all()


@router.get("/{finding_id}", response_model=FindingOut)
def get_finding(finding_id: str, db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    finding = db.query(ConfigFinding).join(CloudAccount).filter(
        ConfigFinding.finding_id == finding_id, CloudAccount.org_id == current_user.org_id
    ).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@router.patch("/{finding_id}/acknowledge", response_model=FindingOut)
def acknowledge_finding(
    finding_id: str,
    payload: FindingAcknowledge,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_roles("admin", "engineer")),
):
    finding = db.query(ConfigFinding).join(CloudAccount).filter(
        ConfigFinding.finding_id == finding_id, CloudAccount.org_id == current_user.org_id
    ).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    finding.finding_status = "acknowledged"
    db.commit()
    db.refresh(finding)

    write_audit_log(db, user_id=current_user.user_id, action="finding_acknowledged",
                     details={"finding_id": finding_id, "justification": payload.justification})
    return finding
