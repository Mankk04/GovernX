"""
Audit trail routes (Section 19) -- admin only.
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.models import AppUser, AuditLog
from app.schemas.schemas import AuditLogOut, ChainVerificationOut
from app.services.audit_logger import verify_chain

router = APIRouter(prefix="/api/v1/audit-log", tags=["audit"])


@router.get("", response_model=List[AuditLogOut])
def list_audit_log(db: Session = Depends(get_db), current_user: AppUser = Depends(require_roles("admin"))):
    return db.query(AuditLog).order_by(AuditLog.seq.desc()).limit(500).all()


@router.get("/verify", response_model=ChainVerificationOut)
def verify_audit_log(db: Session = Depends(get_db), current_user: AppUser = Depends(require_roles("admin"))):
    """Walks the full hash chain and reports whether every entry's hash
    still matches what it should be given its content and its predecessor.
    A broken chain means a row was altered, deleted, or inserted outside
    of write_audit_log -- i.e. outside the application entirely.
    """
    result = verify_chain(db)
    if result.valid:
        message = f"Audit trail is intact across all {result.total_entries} entries."
    else:
        message = (
            f"Integrity check FAILED at sequence #{result.first_broken_seq}. "
            "That entry (or one before it) does not match its recorded hash -- "
            "the audit trail may have been altered outside the application."
        )
    return ChainVerificationOut(
        valid=result.valid,
        total_entries=result.total_entries,
        first_broken_seq=result.first_broken_seq,
        message=message,
    )
