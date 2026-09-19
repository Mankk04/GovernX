import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api/client";

export default function Login() {
  const [email, setEmail] = useState("admin@governx.local");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await login(email, password);
      localStorage.setItem("governx_token", data.access_token);
      localStorage.setItem("governx_role", data.role);
      localStorage.setItem("governx_org_id", data.org_id);
      navigate("/");
    } catch (err) {
      setError("Invalid email or password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-card">
        <h1>GovernX</h1>
        <p style={{ color: "#64748b", marginTop: 0 }}>AI-SPM &amp; NIST CSF 2.0 Compliance Engine</p>
        <form onSubmit={handleSubmit}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <div className="error-text">{error}</div>}
          <button className="btn" type="submit" style={{ width: "100%", marginTop: 12 }} disabled={loading}>
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
        <div className="hint">
          Demo seed user: <code>admin@governx.local</code> / <code>ChangeMe123!</code>
        </div>
      </div>
    </div>
  );
}
