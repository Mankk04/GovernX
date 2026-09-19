"""
Financial Risk Quantifier (Section 10, Module 4).

Runs a Monte Carlo simulation for a single open finding using its asset
value, threat likelihood (derived from severity), and vulnerability
exposure, producing an Annualized Loss Expectancy (ALE) and Value-at-Risk
(VaR) figure that the Executive Dashboard and PDF reports consume.

Methodology (documented per Divyansh's KPI in Section 31.4):
  - Threat frequency ~ Poisson(lambda), lambda = annual likelihood of exploit
  - Loss magnitude per event ~ Lognormal, calibrated so the mean loss
    magnitude equals the resource's asset value
  - ALE = mean(total annual simulated loss) across N iterations
  - Value-at-Risk (95th percentile) = the loss threshold not exceeded in
    95% of simulated years — a standard VaR definition
This mirrors industry-standard FAIR / ALE modelling and should be calibrated
against published benchmarks (e.g. IBM Cost of a Data Breach Report) per the
Risk Analysis mitigation in Section 29.
"""
from dataclasses import dataclass
from typing import Dict

import numpy as np

from app.core.config import settings
from app.data.nist_csf_seed import ASSET_VALUE_BY_RESOURCE_TYPE, SEVERITY_LIKELIHOOD


@dataclass
class RiskResult:
    annualized_loss_expectancy: float
    value_at_risk_95: float
    percentile_5: float
    percentile_95: float


def run_monte_carlo(resource_type: str, severity: str, iterations: int = None) -> RiskResult:
    iterations = iterations or settings.MONTE_CARLO_ITERATIONS
    rng = np.random.default_rng()

    asset_value = ASSET_VALUE_BY_RESOURCE_TYPE.get(resource_type, 750_000)
    annual_likelihood = SEVERITY_LIKELIHOOD.get(severity, 0.10)

    # Number of loss events per year, per simulated year
    event_counts = rng.poisson(lam=annual_likelihood, size=iterations)

    # Lognormal loss magnitude per event, mean centered on asset_value,
    # sigma chosen to give realistic right-skewed tail risk.
    mu = np.log(asset_value) - 0.5 * (0.6 ** 2)
    sigma = 0.6

    total_losses = np.zeros(iterations)
    for i, n_events in enumerate(event_counts):
        if n_events > 0:
            total_losses[i] = rng.lognormal(mean=mu, sigma=sigma, size=n_events).sum()

    ale = float(np.mean(total_losses))
    p5 = float(np.percentile(total_losses, 5))
    p95 = float(np.percentile(total_losses, 95))

    return RiskResult(
        annualized_loss_expectancy=round(ale, 2),
        value_at_risk_95=round(p95, 2),
        percentile_5=round(p5, 2),
        percentile_95=round(p95, 2),
    )


def quantify_finding_risk(resource_type: str, severity: str) -> Dict:
    result = run_monte_carlo(resource_type, severity)
    return {
        "annualized_loss_expectancy": result.annualized_loss_expectancy,
        "value_at_risk": result.value_at_risk_95,
        "percentile_5": result.percentile_5,
        "percentile_95": result.percentile_95,
    }
