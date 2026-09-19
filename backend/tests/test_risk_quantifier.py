"""Unit tests for the Monte Carlo Financial Risk Quantifier (Section 27)."""
from app.services.risk_quantifier import run_monte_carlo


def test_monte_carlo_output_ranges():
    result = run_monte_carlo("rds_instance", "critical", iterations=2000)
    assert result.annualized_loss_expectancy >= 0
    assert result.value_at_risk_95 >= result.annualized_loss_expectancy * 0  # sanity, non-negative
    assert result.percentile_95 >= result.percentile_5


def test_higher_severity_increases_expected_loss():
    low = run_monte_carlo("s3_bucket", "low", iterations=3000)
    critical = run_monte_carlo("s3_bucket", "critical", iterations=3000)
    assert critical.annualized_loss_expectancy > low.annualized_loss_expectancy
