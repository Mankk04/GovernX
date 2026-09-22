"""
Compliance drift forecast routes.

Sits alongside routes_scores: where /scores answers "what tier is each
function at right now," /drift answers "which way is it headed, and how
sure are we." See app.services.drift_forecaster for the methodology.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import AppUser, NistFunction
from app.schemas.schemas import DriftForecastOut, SubcategoryDriftOut
from app.services.drift_forecaster import DriftForecast, forecast_all_functions, forecast_function_drift

router = APIRouter(prefix="/api/v1/drift", tags=["drift"])


def _to_schema(function_name: str, forecast: DriftForecast) -> DriftForecastOut:
    return DriftForecastOut(
        function_id=forecast.function_id,
        function_name=function_name,
        method=forecast.method,
        trend=forecast.trend,
        current_tier=forecast.current_tier,
        predicted_tier_30d=forecast.predicted_tier_30d,
        predicted_tier_90d=forecast.predicted_tier_90d,
        confidence=forecast.confidence,
        at_risk_subcategories=[
            SubcategoryDriftOut(
                subcategory_id=s.subcategory_id,
                description=s.description,
                recent_non_compliant=s.recent_non_compliant,
                prior_non_compliant=s.prior_non_compliant,
            )
            for s in forecast.at_risk_subcategories
        ],
        narrative=forecast.narrative,
    )


@router.get("/forecast", response_model=List[DriftForecastOut])
def get_drift_forecast(db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)):
    """Forecast for every NIST CSF 2.0 function for the current user's org."""
    function_names = {fn.function_id: fn.function_name for fn in db.query(NistFunction).all()}
    forecasts = forecast_all_functions(db, current_user.org_id)
    return [_to_schema(function_names.get(fid, fid), forecast) for fid, forecast in forecasts.items()]


@router.get("/forecast/{function_id}", response_model=DriftForecastOut)
def get_drift_forecast_for_function(
    function_id: str, db: Session = Depends(get_db), current_user: AppUser = Depends(get_current_user)
):
    fn = db.query(NistFunction).filter(NistFunction.function_id == function_id).first()
    if not fn:
        raise HTTPException(status_code=404, detail="NIST function not found")
    forecast = forecast_function_drift(db, current_user.org_id, function_id)
    return _to_schema(fn.function_name, forecast)
