import React from "react";
import { NavLink, useNavigate } from "react-router-dom";

export default function Sidebar() {
  const navigate = useNavigate();
  const role = localStorage.getItem("governx_role") || "engineer";

  function logout() {
    localStorage.removeItem("governx_token");
    localStorage.removeItem("governx_role");
    localStorage.removeItem("governx_org_id");
    navigate("/login");
  }

  return (
    <aside className="sidebar">
      <h1>GovernX</h1>
      <div className="tagline">AI-SPM &amp; NIST CSF 2.0</div>
      <nav>
        <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
          Executive Dashboard
        </NavLink>
        <NavLink to="/findings" className={({ isActive }) => (isActive ? "active" : "")}>
          Findings
        </NavLink>
        <NavLink to="/drift" className={({ isActive }) => (isActive ? "active" : "")}>
          Drift Outlook
        </NavLink>
        <NavLink to="/reports" className={({ isActive }) => (isActive ? "active" : "")}>
          Reports
        </NavLink>
        {role === "admin" && (
          <NavLink to="/audit-log" className={({ isActive }) => (isActive ? "active" : "")}>
            Audit Log
          </NavLink>
        )}
      </nav>
      <div className="hint" style={{ marginTop: 40, color: "#a9bce0" }}>
        Signed in as: {role}
      </div>
      <button className="btn" style={{ marginTop: 12, width: "100%" }} onClick={logout}>
        Log out
      </button>
    </aside>
  );
}
