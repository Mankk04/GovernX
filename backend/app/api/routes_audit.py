"""
Audit trail routes (Section 19) — admin only.
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.models import AuditLog, AppUser
from app.schemas.schemas import AuditLogOut

router = APIRouter(prefix="/api/v1/audit-log", tags=["audit"])


@router.get("", response_model=List[AuditLogOut])
def list_audit_log(db: Session = Depends(get_db), current_user: AppUser = Depends(require_roles("admin"))):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(500).all()
