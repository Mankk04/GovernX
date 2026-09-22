import React, { useEffect, useState } from "react";
import { getDriftForecast, DriftForecast } from "../api/client";

const METHOD_LABELS: Record<string, string> = {
  regression: "Projected from scan history",
  velocity: "Early warning from finding velocity",
  insufficient_data: "Not enough data yet",
};

function TierCell({ label, value }: { label: string; value: number | null }) {
  return (
    <div>
      <div className="label" style={{ fontSize: "0.72rem" }}>{label}</div>
      <div style={{ fontWeight: 600 }}>{value === null ? "—" : `Tier ${value.toFixed(1)}`}</div>
    </div>
  );
}

export default function DriftOutlook() {
  const [forecasts, setForecasts] = useState<DriftForecast[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDriftForecast()
      .then(setForecasts)
      .catch(() => setError("Could not load the drift forecast. Run a few scans first to build up history."))
      .finally(() => setLoading(false));
  }, []);

  const degradingCount = forecasts.filter((f) => f.trend === "degrading").length;

  return (
    <div>
      <div className="page-title">Compliance Drift Outlook</div>
      <div className="page-subtitle">
        Where each NIST CSF 2.0 function is headed, not just where it stands today — projected from
        your own scan history and recent finding trends.
      </div>

      {loading && <p>Loading...</p>}
      {error && <p className="error-text">{error}</p>}

      {!loading && !error && (
        <>
          {degradingCount > 0 && (
            <div className="card" style={{ borderLeft: "4px solid var(--danger)", marginBottom: 24 }}>
              <div className="label">Attention</div>
              <div className="value" style={{ fontSize: "1.1rem" }}>
                {degradingCount} function{degradingCount === 1 ? "" : "s"} trending toward a lower tier
              </div>
            </div>
          )}

          {forecasts.map((f) => (
            <div className="panel" key={f.function_id}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <h2>{f.function_name} ({f.function_id})</h2>
                <span className={`badge ${f.trend}`}>{f.trend}</span>
              </div>

              <div style={{ display: "flex", gap: 32, marginTop: 12 }}>
                <TierCell label="Current" value={f.current_tier} />
                <TierCell label="In 30 days" value={f.predicted_tier_30d} />
                <TierCell label="In 90 days" value={f.predicted_tier_90d} />
              </div>

              <div className="confidence-bar">
                <div className="confidence-bar-fill" style={{ width: `${Math.round(f.confidence * 100)}%` }} />
              </div>
              <div className="label" style={{ fontSize: "0.72rem", marginTop: 4 }}>
                {METHOD_LABELS[f.method]} · {Math.round(f.confidence * 100)}% confidence
              </div>

              <p className="drift-narrative">{f.narrative}</p>

              {f.at_risk_subcategories.length > 0 && (
                <table style={{ marginTop: 12 }}>
                  <thead>
                    <tr>
                      <th>Subcategory</th>
                      <th>Prior 14d</th>
                      <th>Last 14d</th>
                    </tr>
                  </thead>
                  <tbody>
                    {f.at_risk_subcategories.map((s) => (
                      <tr key={s.subcategory_id}>
                        <td>
                          {s.subcategory_id}
                          <div className="label" style={{ fontSize: "0.72rem", fontWeight: 400 }}>{s.description}</div>
                        </td>
                        <td>{s.prior_non_compliant}</td>
                        <td>{s.recent_non_compliant}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          ))}
        </>
      )}
    </div>
  );
}
