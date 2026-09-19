import React, { useEffect, useState } from "react";
import {
  getAccounts, registerAccount, triggerScan, getFindings, acknowledgeFinding,
  CloudAccount, Finding,
} from "../api/client";

export default function Findings() {
  const [accounts, setAccounts] = useState<CloudAccount[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [scanning, setScanning] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [newAccountId, setNewAccountId] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  const role = localStorage.getItem("governx_role") || "executive";
  const canManage = role === "admin" || role === "engineer";

  async function loadAll() {
    const [acc, find] = await Promise.all([
      getAccounts(),
      getFindings(statusFilter ? { status: statusFilter } : undefined),
    ]);
    setAccounts(acc);
    setFindings(find);
  }

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  async function handleAddAccount(e: React.FormEvent) {
    e.preventDefault();
    if (!newAccountId.trim()) return;
    await registerAccount("aws", newAccountId.trim());
    setNewAccountId("");
    setMessage("Cloud account registered.");
    loadAll();
  }

  async function handleScan(accountId: string) {
    setScanning(accountId);
    setMessage(null);
    try {
      const result = await triggerScan(accountId);
      setMessage(`Scan complete: ${result.findings_scanned} findings processed.`);
      loadAll();
    } catch {
      setMessage("Scan failed.");
    } finally {
      setScanning(null);
    }
  }

  async function handleAcknowledge(findingId: string) {
    const justification = window.prompt("Justification for acknowledging this finding:");
    if (!justification) return;
    await acknowledgeFinding(findingId, justification);
    loadAll();
  }

  return (
    <div>
      <div className="page-title">Compliance Findings</div>
      <div className="page-subtitle">
        Configuration gaps mapped to NIST CSF 2.0 subcategories, pulled from connected cloud accounts.
      </div>

      {message && <p className="hint">{message}</p>}

      <div className="panel">
        <h2>Connected Cloud Accounts</h2>
        <table>
          <thead>
            <tr>
              <th>Provider</th>
              <th>Account Identifier</th>
              <th>Connected</th>
              {canManage && <th>Action</th>}
            </tr>
          </thead>
          <tbody>
            {accounts.map((a) => (
              <tr key={a.account_id}>
                <td>{a.provider.toUpperCase()}</td>
                <td>{a.account_identifier}</td>
                <td>{new Date(a.created_at).toLocaleDateString()}</td>
                {canManage && (
                  <td>
                    <button
                      className="btn"
                      disabled={scanning === a.account_id}
                      onClick={() => handleScan(a.account_id)}
                    >
                      {scanning === a.account_id ? "Scanning..." : "Run Scan"}
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>

        {canManage && (
          <form onSubmit={handleAddAccount} style={{ marginTop: 16, display: "flex", gap: 8 }}>
            <input
              placeholder="new-aws-account-identifier"
              value={newAccountId}
              onChange={(e) => setNewAccountId(e.target.value)}
              style={{ flex: 1, padding: 8, borderRadius: 6, border: "1px solid #e2e8f0" }}
            />
            <button className="btn" type="submit">Register AWS Account</button>
          </form>
        )}
      </div>

      <div className="panel">
        <h2>Findings</h2>
        <div style={{ marginBottom: 12 }}>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All statuses</option>
            <option value="non_compliant">Non-compliant</option>
            <option value="compliant">Compliant</option>
            <option value="acknowledged">Acknowledged</option>
          </select>
        </div>
        <table>
          <thead>
            <tr>
              <th>Resource</th>
              <th>Type</th>
              <th>Subcategory</th>
              <th>Status</th>
              <th>Severity</th>
              <th>Scanned</th>
              {canManage && <th>Action</th>}
            </tr>
          </thead>
          <tbody>
            {findings.map((f) => (
              <tr key={f.finding_id}>
                <td>{f.resource_identifier}</td>
                <td>{f.resource_type}</td>
                <td>{f.subcategory_id || "—"}</td>
                <td><span className={`badge ${f.finding_status}`}>{f.finding_status}</span></td>
                <td>{f.severity ? <span className={`badge ${f.severity}`}>{f.severity}</span> : "—"}</td>
                <td>{new Date(f.scanned_at).toLocaleString()}</td>
                {canManage && (
                  <td>
                    {f.finding_status === "non_compliant" && (
                      <button className="btn" onClick={() => handleAcknowledge(f.finding_id)}>
                        Acknowledge
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}
            {findings.length === 0 && (
              <tr><td colSpan={7}>No findings yet — register a cloud account and run a scan.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
