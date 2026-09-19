"""
Cloud account registration & listing (Section 19).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import require_roles, get_current_user
from app.models.models import CloudAccount, AppUser
from app.schemas.schemas import CloudAccountCreate, CloudAccountOut
from app.services.audit_logger import write_audit_log

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


@router.get("", response_model=List[CloudAccountOut])
def list_accounts(db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    return db.query(CloudAccount).filter(CloudAccount.org_id == current_user.org_id).all()


@router.post("", response_model=CloudAccountOut)
def register_account(
    payload: CloudAccountCreate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_roles("admin", "engineer")),
):
    account = CloudAccount(org_id=current_user.org_id, provider=payload.provider,
                            account_identifier=payload.account_identifier)
    db.add(account)
    db.commit()
    db.refresh(account)
    write_audit_log(db, user_id=current_user.user_id, action="cloud_account_registered",
                     details={"provider": payload.provider, "account_identifier": payload.account_identifier})
    return account
