# Project Status Report

**Date:** 2026-03-16
**Workspace:** `/home/sbs/AI`
**Name:** AI Engineering Center

---

## 1. Platform Scope

The repository implements an operational platform core for browser-based systems:
- FastAPI backend
- Next.js frontend
- PostgreSQL-backed persistence for RBAC and language registry
- Docker Compose deployment with Nginx edge

Primary platform capabilities:
- JWT and HttpOnly cookie authentication
- CSRF protection for cookie-authenticated mutation requests
- LDAP/AD integration
- AI provider configuration and validation endpoints
- i18n language management with protected system languages `kk`, `ru`, `en`
- Audit event collection and export
- Backup settings, execution, retention, and restore workflows
- Feature flags admin module (scaffold/in-memory)
- Example-only `example_notes` CRUD reference module
- Admin operational console

Template honesty notes:
- demo auth users and demo login routes are present for local/template use only and require explicit removal, disablement, or replacement before production launch
- `example_notes` is the canonical educational CRUD slice and remains removable/example-only
- `example_slice` remains a lightweight reference-only wiring slice for derived projects

### Template Bootstrap Position

This repository is a reusable platform template.

What derived systems are expected to change:
- project identity and user-facing copy
- domain modules and business routes
- deployment overlays, hostnames, and secrets handling
- optional integration/provider choices

What derived systems should treat as platform baseline unless explicitly approved otherwise:
- authentication and CSRF flows
- RBAC permission enforcement
- audit logging conventions for admin/sensitive actions
- i18n registry and language switching behavior
- admin API prefixes and operational console structure

---

## 2. Backend Status

**Runtime:** FastAPI 0.116.1, Uvicorn 0.35.0
**Language:** Python 3.12 (container), Python 3.14 (local venv)
**DB driver:** psycopg 3.2.13
**Migrations:** Alembic 1.14.1

### Implemented

- Auth hardening:
  - signed access tokens (HMAC-SHA256)
  - backend token validation
  - bearer token and HttpOnly cookie auth modes
  - legacy identity headers disabled by default
- CSRF middleware:
  - active for cookie-authenticated `POST/PUT/PATCH/DELETE`
  - uses `GET /api/auth/csrf` token + readable CSRF cookie
- RBAC persistence in PostgreSQL:
  - `app_roles`, `app_permissions`, `app_role_permissions`, `app_user_roles`
  - DB-backed permission resolution with fail-closed behavior in operational mode
- Trusted identity-to-role synchronization:
  - demo and local login synchronize assignments into `app_user_roles`
  - local user lifecycle updates assignments
- Runtime settings service with encrypted secrets at rest (Fernet envelope)
- Backup service with path allowlist, profile persistence, retention, and restore paths
- Audit service with list/export and filterable event retrieval

### Demo Auth Status

- Demo and mock login paths are intentionally present for bootstrap and local template use.
- They are not a production baseline and must be reviewed explicitly in every derived project.

### Migration Inventory

Repository contains:
- `4a1817f6bc35` initial schema
- `9c6f3f3d0d7a` audit events table
- `b7d3f1a9c2e4` RBAC persistence tables

Note:
- In local runtime snapshots, an environment may still run at `9c6f3f3d0d7a` until migration upgrade is applied.

### Partially Implemented

- `feature_flags` backend module is currently scaffold/in-memory and not productionized.

### Example Slice Status

- `example_notes` demonstrates one small database-backed entity with migration, router, service layer, RBAC checks, audit logging, frontend usage, i18n wiring, and tests.
- It is intentionally example-only and should be removed or replaced by derived projects when real domain modules are introduced.
- `example_slice` remains available as a lightweight reference-only wiring example.

### Known Backend Gap

- Full HA/DR strategy for PostgreSQL is out of current repository scope.

---

## 3. Frontend Status

**Framework:** Next.js 14.2.31 (App Router) + TypeScript

### Implemented

- Pages: `/`, `/login`, `/admin`, `/profile`
- Login integration with backend auth APIs
- Cookie-authenticated backend requests
- Language provider integration with backend language registry
- Admin console tabs:
  - `overview`
  - `languages`
  - `local-users`
  - `rbac`
  - `integrations`
  - `feature-flags`
  - `example-notes`
  - `backups`
  - `audit`
  - `system`

### Admin Panel Functional State

- Overview operational dashboard with snapshot indicators
- Local users management flows
- RBAC role and assignment management flows
- Language registry operations
- Integrations management (LDAP + AI providers)
- Backup configuration and operations
- Audit explorer with advanced filters:
  - `actor`, `action`, `entity`, `result`, `correlation_id`, `since`
- Feature flags tab integrated with admin feature flags API
- System tab integrated with authenticated health snapshot and active-tab auto-refresh

### Frontend Gap

- Frontend tests exist and run, but coverage is still concentrated on shell-level flows and selected component paths.

### Frontend i18n Baseline

- Frontend UI dictionaries are maintained for `ru`, `en`, `kk` only.
- `ru` is the canonical key source for frontend dictionaries.
- Key parity is enforced by `frontend/i18n/check/i18n-check.mjs` and wired into CI.
- Local validation should enforce the same parity check before frontend lint/build.

---

## 4. Infrastructure Status

### Implemented

- Docker Compose stack: `db`, `backend`, `frontend`, `nginx`
- Health-checked startup ordering
- Nginx proxy routing:
  - `/api/` -> backend
  - `/` -> frontend
- Production overlay compose targets:
  - `make prod-up`
  - `make prod-down`

### Confirmed Runtime Checks

- `GET http://nginx/health` -> `200`
- `GET http://nginx/api/health` -> `200`
- `GET http://nginx/metrics` -> `200`

### Infrastructure Gap

- Base Nginx template remains HTTP-only (no default TLS termination).

---

## 5. Platform Maturity Matrix

Status criteria:
- `scaffold`: structure exists, but not safe for direct reuse without significant work.
- `usable`: works for development/internal use, but still has clear operational or functional gaps.
- `production_baseline`: safe reusable baseline for real projects with standard hardening and review.
- `advanced`: materially beyond baseline, with stronger operational maturity and broader reuse confidence.

Current module maturity from the repository:

| Module | Status | Notes |
| --- | --- | --- |
| auth | production_baseline | Signed tokens, cookie flow, CSRF, local login, LDAP login path. |
| rbac | production_baseline | DB-backed roles/assignments with fail-closed operational behavior. |
| audit | production_baseline | Admin action logging, filters, export, DB or memory fallback. |
| integrations | usable | LDAP and AI provider admin settings work, but broader lifecycle/governance is still light. |
| ai_gateway | usable | Provider status/validation plus AI Gateway v1 exist: model registry, provider adapter boundary, unified `/api/ai/chat`, usage logging, and audit hooks. |
| feature_flags | scaffold | Admin tab and API exist, persistence/rollout maturity is not productionized. |
| example_notes | usable | Example-only CRUD reference slice with migration, RBAC, audit, frontend usage, i18n, and tests. |
| backups | usable | Profiles, retention, run/restore flows exist, but no HA/DR baseline. |
| i18n | production_baseline | Registry, protected system languages, profile preference, admin management. |
| observability | usable | Structured logs, request IDs, and metrics exist, but operational depth is still limited. |
| infra/tls | scaffold | Base deployment is HTTP-only; production TLS must be added by derived systems. |
| example_slice | scaffold | Demonstrates namespacing, RBAC guard, and audit wiring only; kept as a lightweight reference alongside `example_notes`. |

Detailed reusable contracts are tracked in `docs/templates/template-contracts.md`.

---

## 6. Security Status

### Implemented

- Signed token validation on backend
- HttpOnly cookie auth flow
- CSRF double-submit enforcement for cookie-auth mutations
- Secure-by-default identity model (no trust in client identity headers)
- Encrypted secret storage for integration settings
- Backup path allowlist enforcement

### Remaining Security Gaps

- Production-grade secrets lifecycle/rotation governance is not fully documented in this repo.
- TLS is not enabled in base compose profile.

---

## 7. Testing and Validation Status

### Latest Confirmed Results

- Backend tests:
  - `cd /home/sbs/AI/infra && docker compose --env-file .env exec -T backend pytest -q`
  - Result: passed (`101 passed`)
- Backend lint:
  - `ruff check .`
  - Result: passed
- Frontend validation:
  - `npm run i18n:check && npm run lint && npm run build`
  - Result: passed
- Frontend tests:
  - `npm run test:frontend`
  - Result: passed (`3 files, 11 tests`)
- Template validation:
  - `make template-validate`
  - Result: passed
- Full pipeline:
  - `make pipeline`
  - Result: expected to pass when dependencies and docker runtime are available

### Notes on Historical Noise in Logs

- Some historical local runs were interrupted (`KeyboardInterrupt`, killed processes, wrong venv path from repo root).
- Final verification runs were completed successfully with clean pass status.

---

## 8. Pipeline and CI/CD Status

### Implemented

- GitHub workflows present (`ci.yml`, `security.yml`)
- Local end-to-end pipeline script wired to `make pipeline`

### Current Validation Statement

- Local pipeline completed successfully with `EXIT:0` and service health checks passing.

---

## 9. Known Gaps and Next Priorities

1. Productionize feature flags (persistence, rollout strategy, auditability).
2. Add TLS-enabled production profile and certificate handling documentation.
3. Keep `example_notes` intentionally small and example-only as derived projects replace it with real domain modules.
4. Continue test decomposition and expand operational observability around privileged admin actions.
