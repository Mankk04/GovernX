"""
GovernX FastAPI application entry point.
Wires together Auth, Accounts, Findings, Scores, Risk, Drift, Reports, and
Audit routers behind a single REST API surface (Section 19).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    routes_auth, routes_accounts, routes_findings, routes_scores,
    routes_risk, routes_reports, routes_audit, routes_drift,
)
from app.db.init_db import init_db

app = FastAPI(
    title="GovernX API",
    description="AI Security Posture Management & NIST CSF 2.0 Automated Compliance Engine",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "service": "GovernX API"}


app.include_router(routes_auth.router)
app.include_router(routes_accounts.router)
app.include_router(routes_findings.router)
app.include_router(routes_scores.router)
app.include_router(routes_risk.router)
app.include_router(routes_drift.router)
app.include_router(routes_reports.router)
app.include_router(routes_audit.router)
