"""
SQLAlchemy ORM models — mirrors the ER Diagram / Database Schema (Sections 16-17 of the blueprint).
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, ForeignKey, DateTime, Integer, Numeric, Text, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Organization(Base):
    __tablename__ = "organization"

    org_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    org_name = Column(String(255), nullable=False)
    industry = Column(String(100))

    cloud_accounts = relationship("CloudAccount", back_populates="organization")
    users = relationship("AppUser", back_populates="organization")
    maturity_scores = relationship("MaturityScore", back_populates="organization")
    compliance_reports = relationship("ComplianceReport", back_populates="organization")


class CloudAccount(Base):
    __tablename__ = "cloud_account"

    account_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    org_id = Column(UUID(as_uuid=False), ForeignKey("organization.org_id"))
    provider = Column(String(50), nullable=False)  # 'aws' | 'azure'
    account_identifier = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="cloud_accounts")
    findings = relationship("ConfigFinding", back_populates="cloud_account")


class NistFunction(Base):
    __tablename__ = "nist_function"

    function_id = Column(String(10), primary_key=True)  # GV, ID, PR, DE, RS, RC
    function_name = Column(String(100), nullable=False)

    subcategories = relationship("NistSubcategory", back_populates="function")


class NistSubcategory(Base):
    __tablename__ = "nist_subcategory"

    subcategory_id = Column(String(20), primary_key=True)  # e.g. PR.DS-01
    function_id = Column(String(10), ForeignKey("nist_function.function_id"))
    description = Column(Text)

    function = relationship("NistFunction", back_populates="subcategories")
    findings = relationship("ConfigFinding", back_populates="subcategory")


class ConfigFinding(Base):
    __tablename__ = "config_finding"

    finding_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    account_id = Column(UUID(as_uuid=False), ForeignKey("cloud_account.account_id"))
    resource_type = Column(String(100))
    resource_identifier = Column(String(255))
    subcategory_id = Column(String(20), ForeignKey("nist_subcategory.subcategory_id"))
    finding_status = Column(String(20), nullable=False)  # compliant | non_compliant | acknowledged
    severity = Column(String(20))  # low | medium | high | critical
    scanned_at = Column(DateTime, default=datetime.utcnow)

    cloud_account = relationship("CloudAccount", back_populates="findings")
    subcategory = relationship("NistSubcategory", back_populates="findings")
    risk_assessments = relationship("RiskAssessment", back_populates="finding")


class RiskAssessment(Base):
    __tablename__ = "risk_assessment"

    risk_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    finding_id = Column(UUID(as_uuid=False), ForeignKey("config_finding.finding_id"))
    annualized_loss_expectancy = Column(Numeric(14, 2))
    value_at_risk = Column(Numeric(14, 2))
    simulation_run_at = Column(DateTime, default=datetime.utcnow)

    finding = relationship("ConfigFinding", back_populates="risk_assessments")


class MaturityScore(Base):
    __tablename__ = "maturity_score"

    score_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    org_id = Column(UUID(as_uuid=False), ForeignKey("organization.org_id"))
    function_id = Column(String(10), ForeignKey("nist_function.function_id"))
    tier_level = Column(Integer)
    calculated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (CheckConstraint("tier_level BETWEEN 1 AND 4"),)

    organization = relationship("Organization", back_populates="maturity_scores")


class Role(Base):
    __tablename__ = "role"

    role_id = Column(String(20), primary_key=True)  # admin | engineer | executive
    role_name = Column(String(50), nullable=False)


class AppUser(Base):
    __tablename__ = "app_user"

    user_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    org_id = Column(UUID(as_uuid=False), ForeignKey("organization.org_id"))
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role_id = Column(String(20), ForeignKey("role.role_id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="users")


class ComplianceReport(Base):
    __tablename__ = "compliance_report"

    report_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    org_id = Column(UUID(as_uuid=False), ForeignKey("organization.org_id"))
    file_path = Column(String(500))
    generated_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="compliance_reports")


class AuditLog(Base):
    """Append-only audit trail, hash-chained so tampering is detectable.

    Each row's entry_hash covers its own content plus the previous row's
    entry_hash (prev_hash), the same construction used by blockchains and
    tamper-evident logs generally: altering or deleting any row breaks the
    hash of every row after it, which /api/v1/audit-log/verify can detect
    even though nothing stops someone with direct DB access from editing
    the table itself. See app/services/audit_logger.py.
    """
    __tablename__ = "audit_log"

    log_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    seq = Column(Integer, nullable=False, unique=True)  # chain position, assigned by write_audit_log
    user_id = Column(UUID(as_uuid=False), ForeignKey("app_user.user_id"), nullable=True)
    action = Column(String(255), nullable=False)
    details = Column(JSONB)
    timestamp = Column(DateTime, default=datetime.utcnow)
    prev_hash = Column(String(64), nullable=False)  # entry_hash of the preceding row, or genesis
    entry_hash = Column(String(64), nullable=False, unique=True)
