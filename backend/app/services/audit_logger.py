"""
Audit Logging Service (Section 21 - Logging Flow).

Writes append-only, structured audit entries for every security-relevant
action (login, role change, finding override, report download).
"""
from typing import Optional, Dict
from sqlalchemy.orm import Session

from app.models.models import AuditLog


def write_audit_log(db: Session, user_id: Optional[str], action: str, details: Optional[Dict] = None) -> AuditLog:
    entry = AuditLog(user_id=user_id, action=action, details=details or {})
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
