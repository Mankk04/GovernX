"""
Financial risk routes (Section 19).
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import RiskAssessment, ConfigFinding, CloudAccount, AppUser
from app.services.risk_quantifier import run_monte_carlo
from app.schemas.schemas import RiskSummaryOut, RiskSummaryTopFinding, RiskDetailOut

router = APIRouter(prefix="/api/v1/risk", tags=["risk"])


@router.get("/summary", response_model=RiskSummaryOut)
def risk_summary(db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    rows = (
        db.query(RiskAssessment, ConfigFinding)
        .join(ConfigFinding, RiskAssessment.finding_id == ConfigFinding.finding_id)
        .join(CloudAccount, ConfigFinding.account_id == CloudAccount.account_id)
        .filter(CloudAccount.org_id == current_user.org_id)
        .order_by(RiskAssessment.value_at_risk.desc())
        .all()
    )

    total_var = sum(float(r.RiskAssessment.value_at_risk) for r in rows)
    total_ale = sum(float(r.RiskAssessment.annualized_loss_expectancy) for r in rows)

    top = [
        RiskSummaryTopFinding(
            finding_id=r.ConfigFinding.finding_id,
            resource=r.ConfigFinding.resource_identifier or "unknown",
            subcategory=r.ConfigFinding.subcategory_id or "unmapped",
            value_at_risk=float(r.RiskAssessment.value_at_risk),
            severity=r.ConfigFinding.severity,
        )
        for r in rows[:5]
    ]

    return RiskSummaryOut(
        org_id=current_user.org_id,
        total_value_at_risk=round(total_var, 2),
        total_annualized_loss_expectancy=round(total_ale, 2),
        top_findings=top,
        generated_at=datetime.utcnow(),
    )


@router.get("/{finding_id}", response_model=RiskDetailOut)
def risk_detail(finding_id: str, db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    finding = db.query(ConfigFinding).join(CloudAccount).filter(
        ConfigFinding.finding_id == finding_id, CloudAccount.org_id == current_user.org_id
    ).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    risk = db.query(RiskAssessment).filter(RiskAssessment.finding_id == finding_id).order_by(
        RiskAssessment.simulation_run_at.desc()
    ).first()
    if not risk:
        raise HTTPException(status_code=404, detail="No risk assessment on file for this finding")

    # Re-run a fresh simulation to also surface percentile band for the detail view
    fresh = run_monte_carlo(finding.resource_type, finding.severity or "medium")

    return RiskDetailOut(
        finding_id=finding_id,
        annualized_loss_expectancy=float(risk.annualized_loss_expectancy),
        value_at_risk=float(risk.value_at_risk),
        percentile_5=fresh.percentile_5,
        percentile_95=fresh.percentile_95,
        simulation_run_at=risk.simulation_run_at,
    )
