import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getScores, getRiskSummary, getDriftForecast, MaturityScore, RiskSummary, DriftForecast } from "../api/client";
import MaturityChart from "../components/MaturityChart";
import RiskSummaryCard from "../components/RiskSummaryCard";

const TIER_LABELS: Record<number, string> = {
  1: "Tier 1 — Partial",
  2: "Tier 2 — Risk Informed",
  3: "Tier 3 — Repeatable",
  4: "Tier 4 — Adaptive",
};

export default function Dashboard() {
  const [scores, setScores] = useState<MaturityScore[]>([]);
  const [risk, setRisk] = useState<RiskSummary | null>(null);
  const [drift, setDrift] = useState<DriftForecast[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getScores(), getRiskSummary()])
      .then(([s, r]) => {
        setScores(s);
        setRisk(r);
      })
      .catch(() => setError("Could not load dashboard data. Run a scan from the Findings page first."))
      .finally(() => setLoading(false));

    // Drift is a supplementary callout, not core dashboard data — fail
    // silently so a thin scan history doesn't block the main dashboard.
    getDriftForecast().then(setDrift).catch(() => setDrift([]));
  }, []);

  const degradingFunctions = drift.filter((d) => d.trend === "degrading");

  const overallTier = scores.length
    ? Math.round(scores.reduce((sum, s) => sum + s.tier_level, 0) / scores.length)
    : 1;

  return (
    <div>
      <div className="page-title">Executive Board Dashboard</div>
      <div className="page-subtitle">
        Current vs. target maturity profile and quantified financial risk, updated continuously.
      </div>

      {loading && <p>Loading...</p>}
      {error && <p className="error-text">{error}</p>}

      {!loading && !error && (
        <>
          <div className="card-grid">
            <div className="card">
              <div className="label">Overall Maturity</div>
              <div className="value">{TIER_LABELS[overallTier] || "—"}</div>
            </div>
            <div className="card">
              <div className="label">Total Value at Risk</div>
              <div className="value">
                ${risk ? risk.total_value_at_risk.toLocaleString(undefined, { maximumFractionDigits: 0 }) : "0"}
              </div>
            </div>
            <div className="card">
              <div className="label">Annualized Loss Expectancy</div>
              <div className="value">
                ${risk ? risk.total_annualized_loss_expectancy.toLocaleString(undefined, { maximumFractionDigits: 0 }) : "0"}
              </div>
            </div>
            <div className="card">
              <div className="label">Open High-Risk Findings</div>
              <div className="value">{risk ? risk.top_findings.length : 0}</div>
            </div>
          </div>

          {degradingFunctions.length > 0 && (
            <div className="panel" style={{ borderLeft: "4px solid var(--danger)" }}>
              <h2>Drift Outlook</h2>
              <p style={{ color: "var(--muted)", marginTop: -8 }}>
                {degradingFunctions.map((d) => d.function_name).join(", ")}{" "}
                {degradingFunctions.length === 1 ? "is" : "are"} trending toward a lower maturity tier.{" "}
                <Link to="/drift">See the full forecast →</Link>
              </p>
            </div>
          )}

          <div className="panel">
            <h2>Maturity Profile by NIST CSF 2.0 Function</h2>
            <MaturityChart scores={scores} />
          </div>

          {risk && risk.top_findings.length > 0 && <RiskSummaryCard summary={risk} />}
        </>
      )}
    </div>
  );
}
