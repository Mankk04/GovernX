import React, { useEffect, useState } from "react";
import { getAuditLog, verifyAuditChain, AuditLogEntry, ChainVerification } from "../api/client";

function shortHash(h: string) {
  return `${h.slice(0, 8)}…${h.slice(-6)}`;
}

export default function AuditLog() {
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [verification, setVerification] = useState<ChainVerification | null>(null);
  const [verifying, setVerifying] = useState(false);

  useEffect(() => {
    getAuditLog()
      .then(setEntries)
      .catch(() => setError("Could not load the audit log. This page requires an admin account."))
      .finally(() => setLoading(false));
  }, []);

  function runVerification() {
    setVerifying(true);
    verifyAuditChain()
      .then(setVerification)
      .catch(() => setVerification({ valid: false, total_entries: 0, first_broken_seq: null, message: "Could not run the verification check." }))
      .finally(() => setVerifying(false));
  }

  return (
    <div>
      <div className="page-title">Audit Log</div>
      <div className="page-subtitle">
        Every security-relevant action, hash-chained so tampering with the trail itself is detectable.
      </div>

      {loading && <p>Loading...</p>}
      {error && <p className="error-text">{error}</p>}

      {!loading && !error && (
        <>
          <div className="panel">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h2>Chain Integrity</h2>
              <button className="btn" onClick={runVerification} disabled={verifying}>
                {verifying ? "Verifying…" : "Verify Integrity"}
              </button>
            </div>
            {verification && (
              <p className={verification.valid ? "" : "error-text"} style={{ marginTop: 8 }}>
                {verification.message}
              </p>
            )}
            {!verification && (
              <p className="label" style={{ marginTop: 8 }}>
                Recomputes every entry's hash from its content and its predecessor's hash — a row edited or
                removed outside this application will fail here.
              </p>
            )}
          </div>

          <div className="panel">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Time</th>
                  <th>Action</th>
                  <th>Entry hash</th>
                  <th>Prev hash</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((e) => (
                  <tr key={e.log_id}>
                    <td>{e.seq}</td>
                    <td>{new Date(e.timestamp).toLocaleString()}</td>
                    <td>{e.action}</td>
                    <td title={e.entry_hash} style={{ fontFamily: "monospace" }}>{shortHash(e.entry_hash)}</td>
                    <td title={e.prev_hash} style={{ fontFamily: "monospace" }}>{shortHash(e.prev_hash)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
