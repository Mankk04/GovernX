"""
Standalone Monte Carlo ALE/VaR notebook-style script (Section 18 folder structure).

This mirrors backend/app/services/risk_quantifier.py but is runnable
independently (e.g. from a Jupyter notebook) for research/calibration work,
without needing the full FastAPI app or a database connection.

Usage:
    python ai/risk_simulation/monte_carlo.py
"""
import numpy as np

ASSET_VALUE_BY_RESOURCE_TYPE = {
    "rds_instance": 5_000_000,
    "s3_bucket": 1_500_000,
    "iam_user": 800_000,
    "iam_policy": 1_000_000,
    "ec2_instance": 600_000,
}

SEVERITY_LIKELIHOOD = {"low": 0.05, "medium": 0.15, "high": 0.30, "critical": 0.45}


def run_monte_carlo(resource_type: str, severity: str, iterations: int = 20000):
    rng = np.random.default_rng()
    asset_value = ASSET_VALUE_BY_RESOURCE_TYPE.get(resource_type, 750_000)
    annual_likelihood = SEVERITY_LIKELIHOOD.get(severity, 0.10)

    event_counts = rng.poisson(lam=annual_likelihood, size=iterations)
    mu = np.log(asset_value) - 0.5 * (0.6 ** 2)
    sigma = 0.6

    total_losses = np.zeros(iterations)
    for i, n_events in enumerate(event_counts):
        if n_events > 0:
            total_losses[i] = rng.lognormal(mean=mu, sigma=sigma, size=n_events).sum()

    return {
        "ale": float(np.mean(total_losses)),
        "value_at_risk_95": float(np.percentile(total_losses, 95)),
        "p5": float(np.percentile(total_losses, 5)),
        "p50": float(np.percentile(total_losses, 50)),
    }


if __name__ == "__main__":
    for resource_type in ASSET_VALUE_BY_RESOURCE_TYPE:
        for severity in SEVERITY_LIKELIHOOD:
            result = run_monte_carlo(resource_type, severity)
            print(
                f"{resource_type:15s} {severity:9s} "
                f"ALE=${result['ale']:>12,.0f}  VaR95=${result['value_at_risk_95']:>13,.0f}"
            )
