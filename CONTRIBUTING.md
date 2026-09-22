# Contributing to GovernX

## Branch Strategy (Section 25 of the blueprint)
- `main` — production-ready code only, protected branch.
- `develop` — integration branch; all features merge here first.
- `feature/*` — e.g. `feature/aws-poller`, `feature/risk-engine`, `feature/dashboard-ui`.
- `bugfix/*` — e.g. `bugfix/jwt-expiry`.
- `release/*` — release candidate branches cut from `develop`.

## Rules
1. No direct commits to `main` or `develop` — all changes go through a Pull Request.
2. At least one team member must review and approve a PR before merge.
3. `main` is only updated from a `release/*` branch after QA sign-off.
4. Security-sensitive PRs (auth, cloud credentials) require review from the security lead.

## Definition of Done
Code merged to `develop`, unit + integration tests passing in CI, peer-reviewed, and documented.
