"""
Authentication routes (Section 19-20). OAuth2 password flow -> JWT.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.models.models import AppUser
from app.schemas.schemas import TokenResponse
from app.services.audit_logger import write_audit_log

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(AppUser).filter(AppUser.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    token = create_access_token(subject=user.user_id, role=user.role_id, org_id=user.org_id)
    write_audit_log(db, user_id=user.user_id, action="user_login", details={"email": user.email})
    return TokenResponse(access_token=token, role=user.role_id, org_id=user.org_id)
