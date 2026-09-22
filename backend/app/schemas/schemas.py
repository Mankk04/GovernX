"""
Pydantic request/response schemas for the REST API (Section 19).
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr


# ---------- Auth ----------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    org_id: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    org_id: str
    role_id: str = "engineer"


class UserOut(BaseModel):
    user_id: str
    email: EmailStr
    role_id: str
    org_id: str

    class Config:
        from_attributes = True


# ---------- Cloud accounts ----------
class CloudAccountCreate(BaseModel):
    provider: str  # aws | azure
    account_identifier: str


class CloudAccountOut(BaseModel):
    account_id: str
    provider: str
    account_identifier: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Findings ----------
class FindingOut(BaseModel):
    finding_id: str
    account_id: str
    resource_type: Optional[str]
    resource_identifier: Optional[str]
    subcategory_id: Optional[str]
    finding_status: str
    severity: Optional[str]
    scanned_at: datetime

    class Config:
        from_attributes = True


class FindingAcknowledge(BaseModel):
    justification: str


# ---------- Scores ----------
class MaturityScoreOut(BaseModel):
    function_id: str
    function_name: str
    tier_level: int
    calculated_at: datetime

    class Config:
        from_attributes = True


# ---------- Risk ----------
class RiskSummaryTopFinding(BaseModel):
    finding_id: str
    resource: str
    subcategory: str
    value_at_risk: float
    severity: Optional[str]


class RiskSummaryOut(BaseModel):
    org_id: str
    total_value_at_risk: float
    total_annualized_loss_expectancy: float
    top_findings: List[RiskSummaryTopFinding]
    generated_at: datetime


class RiskDetailOut(BaseModel):
    finding_id: str
    annualized_loss_expectancy: float
    value_at_risk: float
    percentile_5: float
    percentile_95: float
    simulation_run_at: datetime


# ---------- Reports ----------
class ReportOut(BaseModel):
    report_id: str
    org_id: str
    file_path: str
    generated_at: datetime

    class Config:
        from_attributes = True


# ---------- Drift forecast ----------
class SubcategoryDriftOut(BaseModel):
    subcategory_id: str
    description: str
    recent_non_compliant: int
    prior_non_compliant: int


class DriftForecastOut(BaseModel):
    function_id: str
    function_name: str
    method: str  # regression | velocity | insufficient_data
    trend: str  # improving | stable | degrading
    current_tier: float
    predicted_tier_30d: Optional[float]
    predicted_tier_90d: Optional[float]
    confidence: float
    at_risk_subcategories: List[SubcategoryDriftOut]
    narrative: str


# ---------- Audit ----------
class AuditLogOut(BaseModel):
    log_id: str
    seq: int
    user_id: Optional[str]
    action: str
    details: Optional[dict]
    timestamp: datetime
    prev_hash: str
    entry_hash: str

    class Config:
        from_attributes = True


class ChainVerificationOut(BaseModel):
    valid: bool
    total_entries: int
    first_broken_seq: Optional[int]
    message: str
