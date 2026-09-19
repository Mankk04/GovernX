# GovernX

**AI Security Posture Management (AI-SPM) & NIST CSF 2.0 Automated Compliance Engine**

GovernX continuously pulls configuration telemetry from cloud accounts (AWS/Azure), maps
every finding to a NIST CSF 2.0 function/subcategory, computes a maturity tier (1–4) per
function, and runs a Monte Carlo simulation to translate open gaps into quantified
financial risk (Annualized Loss Expectancy and Value at Risk). Results are surfaced on a
React executive dashboard and as board-ready PDF reports.

This repository is a working implementation of the architecture described in the
project blueprint: FastAPI backend, PostgreSQL, Redis, a mock/real AWS+Azure poller,
a NIST CSF 2.0 mapping engine, a NumPy/SciPy-based Monte Carlo risk quantifier, a
ReportLab PDF report generator, JWT + RBAC auth, and a React + TypeScript + Recharts
dashboard.

> By default the cloud poller runs in **mock mode** (`USE_MOCK_AWS=true`) so you can run
> the entire pipeline end-to-end without real AWS credentials. Flip it off and provide a
> **read-only** IAM user/role to pull real AWS data.

---

## 1. Architecture at a glance

```
[AWS/Azure/AD] -> [Cloud Poller] -> [Mapping Engine] -> [Scoring Engine]
                                                              |
                                                              v
                                                     [Monte Carlo Risk Quantifier]
                                                              |
                                                              v
                                    [PostgreSQL] <-> [FastAPI REST API] -> [React Dashboard]
                                                              |
                                                              v
                                                  [ReportLab PDF Reports]
```

| Layer | Technology |
|---|---|
| Cloud data collection | Python + boto3 (mock mode included) |
| Backend API | FastAPI |
| Database | PostgreSQL |
| Cache / job queue | Redis |
| Risk simulation | NumPy + SciPy (Monte Carlo) |
| Frontend | React + TypeScript + Vite |
| Charts | Recharts |
| Report generation | ReportLab |
| Auth | OAuth2 + JWT |
| Containerization | Docker + Docker Compose |
| CI/CD | GitHub Actions |

Full diagrams (module, sequence, ER, DFD, deployment) are in the original project
blueprint PDF; the folder/DB layout below matches those diagrams directly.

---

## 2. Repository layout

```
governx/
├── backend/            FastAPI app, services, models, tests
├── frontend/            React + TypeScript dashboard
├── ai/risk_simulation/  Standalone Monte Carlo notebook/script
├── deployment/           Deployment notes
├── .github/workflows/    CI pipeline
├── docker-compose.yml
└── README.md
```

---

## 3. Prerequisites (Kali Linux)

Kali ships an old/managed Python, so we'll use Docker for the database/cache and a
virtualenv for the backend. Run everything below in a terminal.

### 3.1 Update the system

```bash
sudo apt update && sudo apt -y upgrade
```

### 3.2 Install Docker & Docker Compose

```bash
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker
# Allow running docker without sudo (log out/in afterwards)
sudo usermod -aG docker $USER
newgrp docker
docker --version
docker compose version
```

### 3.3 Install Git, Python 3.11+, Node.js 20+

```bash
sudo apt install -y git python3 python3-venv python3-pip

# Kali's default Node is often outdated — install Node 20 via NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node --version   # should print v20.x
npm --version
```

---

## 4. Quick start — Docker Compose (recommended)

This spins up PostgreSQL, Redis, the FastAPI backend, and the React dev server together.

```bash
git clone https://github.com/<your-org>/governx.git
cd governx

# Copy and edit backend environment variables
cp backend/.env.example backend/.env
# Generate a real JWT secret:
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
# Paste the output into JWT_SECRET_KEY inside backend/.env

# Build and start everything
docker compose up --build
```

Once containers are healthy:

- Backend API + interactive docs: **http://localhost:8000/docs**
- Frontend dashboard: **http://localhost:5173**
- PostgreSQL: `localhost:5432` (user/pass: `governx` / `governx`)
- Redis: `localhost:6379`

### 4.1 Seed the database (first run only)

In a second terminal, seed reference data (NIST CSF functions/subcategories, roles,
a demo organization, and demo users):

```bash
docker compose exec backend python -m app.db.seed
```

This prints demo login credentials, for example:

```
Login: admin@governx.local / ChangeMe123!  (role: admin)
Login: ciso@governx.local  / ChangeMe123!  (role: executive)
```

Open **http://localhost:5173**, log in with `admin@governx.local`, register a cloud
account, then click **Run Scan** on the Findings page. This triggers the full
poll → map → score → risk pipeline and populates the Executive Dashboard.

---

## 5. Manual setup (without Docker)

Useful if you want to run the backend/frontend directly on Kali for development.

### 5.1 PostgreSQL & Redis (still easiest via Docker)

```bash
docker run -d --name governx_db -e POSTGRES_USER=governx -e POSTGRES_PASSWORD=governx \
  -e POSTGRES_DB=governx -p 5432:5432 postgres:16-alpine
docker run -d --name governx_redis -p 6379:6379 redis:7-alpine
```

Or install PostgreSQL natively:

```bash
sudo apt install -y postgresql postgresql-contrib
sudo -u postgres psql -c "CREATE USER governx WITH PASSWORD 'governx';"
sudo -u postgres psql -c "CREATE DATABASE governx OWNER governx;"
```

### 5.2 Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env: set DATABASE_URL=postgresql://governx:governx@localhost:5432/governx
#            set REDIS_URL=redis://localhost:6379/0
#            set a real JWT_SECRET_KEY

python -m app.db.seed          # creates tables + seed data + demo users
uvicorn app.main:app --reload  # http://localhost:8000
```

Run the test suite:

```bash
pytest -v
```

### 5.3 Frontend

```bash
cd frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
npm run dev   # http://localhost:5173
```

---

## 6. Connecting a real AWS account (optional)

1. Create a **read-only** IAM user/role (e.g. attach `SecurityAudit` and
   `ReadOnlyAccess` managed policies — never grant write access).
2. In `backend/.env`, set:
   ```
   USE_MOCK_AWS=false
   AWS_ACCESS_KEY_ID=<your key>
   AWS_SECRET_ACCESS_KEY=<your secret>
   AWS_REGION=us-east-1
   ```
3. Restart the backend container/process. Register the account in the UI with its
   real account identifier and click **Run Scan**.

Never commit real credentials — `backend/.env` is already git-ignored.

---

## 7. Generating a compliance PDF report

From the **Reports** page in the dashboard (or via API):

```bash
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Authorization: Bearer <your JWT>"
```

The response includes a `report_id`; download it with:

```bash
curl -o report.pdf http://localhost:8000/api/v1/reports/<report_id> \
  -H "Authorization: Bearer <your JWT>"
```

---

## 8. REST API reference

Interactive OpenAPI docs are auto-generated at **`/docs`** once the backend is running.
Key endpoints (see the blueprint's Section 19 for the full table):

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/login` | Authenticate, returns JWT |
| GET/POST | `/api/v1/accounts` | List / register cloud accounts |
| POST | `/api/v1/findings/scan/{account_id}` | Trigger poll → map → score → risk cycle |
| GET | `/api/v1/findings` | List findings (filterable) |
| PATCH | `/api/v1/findings/{id}/acknowledge` | Acknowledge/override a finding |
| GET | `/api/v1/scores` | Current maturity tier per NIST function |
| GET | `/api/v1/risk/summary` | Aggregate financial risk |
| POST | `/api/v1/reports/generate` | Generate a PDF report |
| GET | `/api/v1/audit-log` | Full audit trail (admin only) |

---

## 9. CI/CD

`.github/workflows/ci.yml` runs on every push/PR to `main`/`develop`:

- Spins up a PostgreSQL service container
- Installs backend dependencies, runs a Bandit security scan, runs unit tests
- Installs frontend dependencies, lints, and builds the React app

---

## 10. Security notes

- Cloud pollers use **read-only** credentials only (Section 22).
- All API traffic should be served over HTTPS/TLS 1.2+ in production (this repo
  serves plain HTTP for local development — put it behind Nginx + TLS for real use).
- JWT secrets, DB passwords, and cloud credentials must live only in `.env` files,
  never in source control.
- Every login, scan, finding acknowledgment, and report download is written to the
  append-only `audit_log` table.

---

## 11. Team & attribution

This implementation follows the GovernX Project Blueprint prepared for an internship
project team (Group Leader: Ateeb Shaikh), covering the architecture, module
ownership, 21-day execution plan, and testing/threat-model sections described in the
original document.

Licensed under the MIT License — see `LICENSE`.
