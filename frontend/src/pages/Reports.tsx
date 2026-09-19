import React, { useState } from "react";
import { generateReport } from "../api/client";
import { apiClient } from "../api/client";

export default function Reports() {
  const [generating, setGenerating] = useState(false);
  const [lastReportId, setLastReportId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const role = localStorage.getItem("governx_role") || "executive";
  const canGenerate = role === "admin" || role === "engineer";

  async function handleGenerate() {
    setGenerating(true);
    setError(null);
    try {
      const report = await generateReport();
      setLastReportId(report.report_id);
    } catch {
      setError("Report generation failed. Make sure at least one scan has been run.");
    } finally {
      setGenerating(false);
    }
  }

  function handleDownload() {
    if (!lastReportId) return;
    const token = localStorage.getItem("governx_token");
    const url = `${apiClient.defaults.baseURL}/api/v1/reports/${lastReportId}`;
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => res.blob())
      .then((blob) => {
        const link = document.createElement("a");
        link.href = window.URL.createObjectURL(blob);
        link.download = `governx_report_${lastReportId}.pdf`;
        link.click();
      });
  }

  return (
    <div>
      <div className="page-title">Compliance Reports</div>
      <div className="page-subtitle">
        Generate board-ready PDF reports summarizing maturity tiers and quantified financial risk.
      </div>

      <div className="panel">
        <h2>Generate New Report</h2>
        <p>
          Builds a PDF snapshot of the current NIST CSF 2.0 maturity profile and top financial risk
          findings for your organization, using ReportLab.
        </p>
        {canGenerate ? (
          <button className="btn" onClick={handleGenerate} disabled={generating}>
            {generating ? "Generating..." : "Generate PDF Report"}
          </button>
        ) : (
          <p className="hint">Executive/read-only accounts cannot generate reports, but can download existing ones.</p>
        )}

        {error && <p className="error-text">{error}</p>}

        {lastReportId && (
          <div style={{ marginTop: 16 }}>
            <p>Report generated successfully.</p>
            <button className="btn" onClick={handleDownload}>Download PDF</button>
          </div>
        )}
      </div>
    </div>
  );
}
