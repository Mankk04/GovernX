"""
Compliance Drift Forecaster.

Every other module in this system answers "where do we stand right now."
The scoring engine gives a tier as of the last scan; the risk quantifier
prices out today's open findings. Neither one tells a CISO whether a
function is *about to* slip a tier before it actually happens — which is
the difference between a board deck that reports bad news and one that
gets ahead of it.

This module turns the org's own history into a leading indicator, using
whichever signal it actually has enough data for:

  1. Tier trend. Every scan appends a MaturityScore row (see
     routes_findings.trigger_scan), so over time an org builds up a real
     time series per function. Once there are at least
     MIN_POINTS_FOR_REGRESSION of these, we fit an ordinary-least-squares
     line against days-since-first-score and extrapolate it forward.
     R^2 of that fit doubles as our confidence figure — a noisy history
     shouldn't be reported with the same confidence as a clean trend.

  2. Finding velocity. New orgs (or functions that haven't had many
     scans yet) don't have enough score history to regress on. Rather
     than fabricate a trend line from two data points, we fall back to
     comparing non-compliant finding counts in the last
     VELOCITY_WINDOW_DAYS against the window before it, per subcategory.
     A subcategory accumulating non-compliant findings faster than
     before is an early warning independent of what the last computed
     tier said.

The two are never blended into one number — a caller can tell which
method produced a given forecast via DriftForecast.method, and the
narrative says so explicitly, because a regression-backed projection and
a "we don't have enough history yet, but here's a warning sign" are
different claims and shouldn't be presented identically.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
from sqlalchemy.orm import Session

from app.models.models import CloudAccount, ConfigFinding, MaturityScore, NistSubcategory

MIN_POINTS_FOR_REGRESSION = 3
FORECAST_HORIZONS_DAYS = (30, 90)
VELOCITY_WINDOW_DAYS = 14


@dataclass
class SubcategoryDrift:
    subcategory_id: str
    description: str
    recent_non_compliant: int
    prior_non_compliant: int

    @property
    def delta(self) -> int:
        return self.recent_non_compliant - self.prior_non_compliant


@dataclass
class DriftForecast:
    function_id: str
    method: str  # "regression" | "velocity" | "insufficient_data"
    trend: str  # "improving" | "stable" | "degrading"
    current_tier: float
    predicted_tier_30d: Optional[float]
    predicted_tier_90d: Optional[float]
    confidence: float  # 0.0 - 1.0
    at_risk_subcategories: List[SubcategoryDrift] = field(default_factory=list)
    narrative: str = ""


def _linear_forecast(days: np.ndarray, tiers: np.ndarray, horizons: List[int]):
    """Fits tier = slope*day + intercept by least squares and projects
    it forward by each horizon. Returns (slope, r_squared, {horizon: tier}).
    Projected tiers are clamped to the valid [1, 4] range since a raw
    extrapolation can wander outside it.
    """
    slope, intercept = np.polyfit(days, tiers, 1)
    predicted = slope * days + intercept
    ss_res = np.sum((tiers - predicted) ** 2)
    ss_tot = np.sum((tiers - tiers.mean()) ** 2)
    r_squared = max(1 - ss_res / ss_tot, 0.0) if ss_tot > 0 else 0.0

    last_day = days[-1]
    projections = {h: float(np.clip(slope * (last_day + h) + intercept, 1.0, 4.0)) for h in horizons}
    return float(slope), float(r_squared), projections


def _trend_label(slope: float) -> str:
    if slope > 0.01:
        return "improving"
    if slope < -0.01:
        return "degrading"
    return "stable"


def _subcategory_velocity(db: Session, org_id: str, function_id: str) -> List[SubcategoryDrift]:
    """Per subcategory under this function, compares non-compliant finding
    counts in the last VELOCITY_WINDOW_DAYS against the window before it.
    """
    now = datetime.utcnow()
    recent_start = now - timedelta(days=VELOCITY_WINDOW_DAYS)
    prior_start = now - timedelta(days=2 * VELOCITY_WINDOW_DAYS)

    subcats = db.query(NistSubcategory).filter(NistSubcategory.function_id == function_id).all()

    drifts = []
    for sc in subcats:
        rows = (
            db.query(ConfigFinding)
            .join(CloudAccount, ConfigFinding.account_id == CloudAccount.account_id)
            .filter(
                CloudAccount.org_id == org_id,
                ConfigFinding.subcategory_id == sc.subcategory_id,
                ConfigFinding.finding_status == "non_compliant",
                ConfigFinding.scanned_at >= prior_start,
            )
            .all()
        )
        recent = sum(1 for r in rows if r.scanned_at >= recent_start)
        prior = len(rows) - recent
        if recent or prior:
            drifts.append(
                SubcategoryDrift(
                    subcategory_id=sc.subcategory_id,
                    description=sc.description or "",
                    recent_non_compliant=recent,
                    prior_non_compliant=prior,
                )
            )

    drifts.sort(key=lambda d: d.delta, reverse=True)
    return [d for d in drifts if d.delta > 0]


def forecast_function_drift(db: Session, org_id: str, function_id: str) -> DriftForecast:
    history = (
        db.query(MaturityScore)
        .filter(MaturityScore.org_id == org_id, MaturityScore.function_id == function_id)
        .order_by(MaturityScore.calculated_at.asc())
        .all()
    )
    at_risk = _subcategory_velocity(db, org_id, function_id)
    current_tier = float(history[-1].tier_level) if history else 1.0

    if len(history) >= MIN_POINTS_FOR_REGRESSION:
        first_ts = history[0].calculated_at
        days = np.array([(h.calculated_at - first_ts).total_seconds() / 86400 for h in history])
        tiers = np.array([float(h.tier_level) for h in history])
        slope, r_squared, projections = _linear_forecast(days, tiers, list(FORECAST_HORIZONS_DAYS))
        trend = _trend_label(slope)

        narrative = (
            f"Based on {len(history)} scans since {first_ts.date()}, this function is trending "
            f"{trend} at roughly {slope:+.3f} tiers/day (fit confidence {r_squared:.0%})."
        )
        if at_risk:
            plural = "y is" if len(at_risk) == 1 else "ies are"
            narrative += f" {len(at_risk)} subcategor{plural} also seeing rising non-compliance, which may accelerate this."

        return DriftForecast(
            function_id=function_id,
            method="regression",
            trend=trend,
            current_tier=current_tier,
            predicted_tier_30d=projections[30],
            predicted_tier_90d=projections[90],
            confidence=round(r_squared, 2),
            at_risk_subcategories=at_risk,
            narrative=narrative,
        )

    # Cold start — not enough scored history to fit a trend line. Rather
    # than project from one or two points, fall back to finding velocity.
    if at_risk:
        plural = "y has" if len(at_risk) == 1 else "ies have"
        narrative = (
            f"Not enough scan history yet to project a trend line for this function. "
            f"{len(at_risk)} subcategor{plural} more non-compliant findings in the last "
            f"{VELOCITY_WINDOW_DAYS} days than the {VELOCITY_WINDOW_DAYS} before that — an early "
            f"sign this tier may slip on the next scan."
        )
        return DriftForecast(
            function_id=function_id,
            method="velocity",
            trend="degrading",
            current_tier=current_tier,
            predicted_tier_30d=None,
            predicted_tier_90d=None,
            confidence=0.35,
            at_risk_subcategories=at_risk,
            narrative=narrative,
        )

    return DriftForecast(
        function_id=function_id,
        method="insufficient_data",
        trend="stable",
        current_tier=current_tier,
        predicted_tier_30d=None,
        predicted_tier_90d=None,
        confidence=0.1,
        at_risk_subcategories=[],
        narrative=(
            "Not enough scan history to forecast a trend, and no rising non-compliance in "
            "recent findings. Run a few more scans over time to unlock a projection."
        ),
    )


def forecast_all_functions(db: Session, org_id: str) -> Dict[str, DriftForecast]:
    from app.data.nist_csf_seed import NIST_FUNCTIONS

    return {fn["function_id"]: forecast_function_drift(db, org_id, fn["function_id"]) for fn in NIST_FUNCTIONS}
