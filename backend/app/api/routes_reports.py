"""
Compliance report routes (Section 19).
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.models import (
    ComplianceReport, MaturityScore, NistFunction, RiskAssessment, ConfigFinding, CloudAccount, Organization, AppUser
)
from app.schemas.schemas import ReportOut
from app.services.report_generator import generate_compliance_pdf
from app.services.audit_logger import write_audit_log

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.post("/generate", response_model=ReportOut)
def generate_report(db: Session = Depends(get_db), current_user: AppUser = Depends(require_roles("admin", "engineer"))):
    org = db.query(Organization).filter(Organization.org_id == current_user.org_id).first()

    functions = db.query(NistFunction).all()
    maturity_scores = []
    for fn in functions:
        latest = (
            db.query(MaturityScore)
            .filter(MaturityScore.org_id == current_user.org_id, MaturityScore.function_id == fn.function_id)
            .order_by(MaturityScore.calculated_at.desc())
            .first()
        )
        maturity_scores.append({"function_name": fn.function_name, "tier_level": latest.tier_level if latest else 1})

    rows = (
        db.query(RiskAssessment, ConfigFinding)
        .join(ConfigFinding, RiskAssessment.finding_id == ConfigFinding.finding_id)
        .join(CloudAccount, ConfigFinding.account_id == CloudAccount.account_id)
        .filter(CloudAccount.org_id == current_user.org_id)
        .order_by(RiskAssessment.value_at_risk.desc())
        .limit(10)
        .all()
    )
    top_findings = [
        {
            "resource": r.ConfigFinding.resource_identifier or "unknown",
            "subcategory": r.ConfigFinding.subcategory_id or "unmapped",
            "severity": r.ConfigFinding.severity,
            "value_at_risk": float(r.RiskAssessment.value_at_risk),
        }
        for r in rows
    ]
    total_var = sum(f["value_at_risk"] for f in top_findings)

    filepath = generate_compliance_pdf(
        org_name=org.org_name if org else "Unknown Org",
        org_id=current_user.org_id,
        maturity_scores=maturity_scores,
        top_findings=top_findings,
        total_value_at_risk=total_var,
    )

    report = ComplianceReport(org_id=current_user.org_id, file_path=filepath)
    db.add(report)
    db.commit()
    db.refresh(report)

    write_audit_log(db, user_id=current_user.user_id, action="report_generated", details={"report_id": report.report_id})
    return report


@router.get("/{report_id}")
def download_report(report_id: str, db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    report = db.query(ComplianceReport).filter(
        ComplianceReport.report_id == report_id, ComplianceReport.org_id == current_user.org_id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    write_audit_log(db, user_id=current_user.user_id, action="report_downloaded", details={"report_id": report_id})
    return FileResponse(report.file_path, media_type="application/pdf", filename=f"governx_report_{report_id}.pdf")
