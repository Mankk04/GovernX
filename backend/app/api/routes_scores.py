"""
Maturity score routes (Section 19).
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import MaturityScore, NistFunction, AppUser
from app.schemas.schemas import MaturityScoreOut

router = APIRouter(prefix="/api/v1/scores", tags=["scores"])


@router.get("", response_model=List[MaturityScoreOut])
def get_current_scores(db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    """Returns the most recent maturity tier per NIST function for the user's org."""
    functions = db.query(NistFunction).all()
    results = []
    for fn in functions:
        latest = (
            db.query(MaturityScore)
            .filter(MaturityScore.org_id == current_user.org_id, MaturityScore.function_id == fn.function_id)
            .order_by(MaturityScore.calculated_at.desc())
            .first()
        )
        results.append(MaturityScoreOut(
            function_id=fn.function_id,
            function_name=fn.function_name,
            tier_level=latest.tier_level if latest else 1,
            calculated_at=latest.calculated_at if latest else fn and __import__("datetime").datetime.utcnow(),
        ))
    return results
