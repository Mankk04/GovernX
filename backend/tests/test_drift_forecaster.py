"""Unit tests for the Compliance Drift Forecaster (Section 27)."""
import numpy as np

from app.services.drift_forecaster import _linear_forecast, _trend_label


def test_degrading_trend_is_labeled_correctly():
    days = np.array([0, 10, 20, 30])
    tiers = np.array([4.0, 3.0, 2.0, 1.0])  # clearly falling
    slope, r_squared, projections = _linear_forecast(days, tiers, [30, 90])

    assert slope < 0
    assert _trend_label(slope) == "degrading"
    assert r_squared > 0.95  # near-perfect line, should fit almost exactly
    assert projections[90] < projections[30]  # further out should be worse


def test_improving_trend_is_labeled_correctly():
    days = np.array([0, 10, 20, 30])
    tiers = np.array([1.0, 2.0, 3.0, 4.0])
    slope, _, projections = _linear_forecast(days, tiers, [30, 90])

    assert slope > 0
    assert _trend_label(slope) == "improving"
    assert projections[90] >= projections[30]


def test_flat_history_is_labeled_stable():
    assert _trend_label(0.0) == "stable"
    assert _trend_label(0.005) == "stable"  # within the noise band


def test_projection_is_clamped_to_valid_tier_range():
    # A steep upward slope should not project a tier above 4.
    days = np.array([0, 5, 10])
    tiers = np.array([3.0, 3.8, 4.0])
    _, _, projections = _linear_forecast(days, tiers, [365])
    assert 1.0 <= projections[365] <= 4.0
