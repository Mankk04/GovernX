import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Findings from "./pages/Findings";
import Reports from "./pages/Reports";
import DriftOutlook from "./pages/DriftOutlook";
import AuditLogPage from "./pages/AuditLog";
import Sidebar from "./components/Sidebar";

function isAuthenticated() {
  return !!localStorage.getItem("governx_token");
}

function ProtectedLayout({ children }: { children: React.ReactNode }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-content">{children}</div>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <ProtectedLayout>
            <Dashboard />
          </ProtectedLayout>
        }
      />
      <Route
        path="/findings"
        element={
          <ProtectedLayout>
            <Findings />
          </ProtectedLayout>
        }
      />
      <Route
        path="/reports"
        element={
          <ProtectedLayout>
            <Reports />
          </ProtectedLayout>
        }
      />
      <Route
        path="/drift"
        element={
          <ProtectedLayout>
            <DriftOutlook />
          </ProtectedLayout>
        }
      />
      <Route
        path="/audit-log"
        element={
          <ProtectedLayout>
            <AuditLogPage />
          </ProtectedLayout>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
