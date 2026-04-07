# AI Engineering Center

Platform template for browser-based systems with a reusable platform core (higher education is one supported example vertical).

Last updated: 2026-04-05

## Current Delivery Snapshot

This repository currently delivers a strong platform-core baseline with an admin control plane.

Verified on recent Docker validation:
- Backend tests: 1161 passed, 9 skipped
- Frontend tests: 138 passed
- Backend lint: `ruff check .` passed
- Frontend lint: `next lint` passed

Important scope note:
- This repository is still a platform template baseline, not a fully finished end-user product.
- Admin console coverage is significantly deeper than role-specific end-user portals.

## Supported Vertical Profiles

This platform template is domain-neutral and can be adapted to multiple domains.

Common adaptation profiles include:

- Higher education platforms
- Internal enterprise tools
- Regulated administrative systems
- AI-enabled internal services

The repository may include example profiles (such as higher education) to demonstrate how the platform core can be adapted to specific domains.

## What This Platform Provides

Core stack:
- FastAPI backend
- Next.js frontend (App Router)
- PostgreSQL
- Docker Compose + Nginx

Platform core modules:
- Authentication: JWT + HttpOnly cookie auth flows
- CSRF protection for cookie-authenticated mutations
- RBAC with PostgreSQL persistence
- LDAP/Active Directory integration
- AI provider configuration (OpenAI, Gemini, Anthropic, custom)
- AI Gateway v1: model registry, provider adapter boundary, unified `POST /api/ai/chat`, usage logging, and audit hooks
- i18n language registry with protected system languages `kk`, `ru`, `en`
- Audit logging
- Backup management (profiles, retention, restore)
- Feature flags module (currently scaffold/in-memory)
- Example notes module (example-only CRUD reference for derived projects)
- Admin operational console

## Admin Console

Route: `/admin`

Current tabs:
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

Operational highlights:
- Overview dashboard with system, RBAC, language, integrations, backups, and audit snapshot indicators.
- Local users CRUD and password reset.
- RBAC role management and assignment/revoke flows.
- Language registry management with protected system languages.
- Integrations management for LDAP and AI providers.
- Backup profile management, retention dry-run/apply, restore dry-run/execute.
- Audit explorer with filters (`actor`, `action`, `entity`, `result`, `correlation_id`, `since`) and JSON/CSV export.
- Feature flags visibility and on/off toggle via admin API.
- Example notes CRUD tab showing DB-backed entity, migration, RBAC, audit, frontend usage, and i18n wiring in one removable example module.
- System observability tab with authenticated health snapshot (`/api/admin/system/health`) and periodic refresh while active.

## Current Frontend Scope

What is mature now:
- Admin control plane and operational workflows under `/admin` and `/(admin)/console/*`.
- Initial role-based zones are now available:
	- `/student`
	- `/faculty`
	- `/registrar`

What is not yet a complete product surface:
- No full student portal UX journey (end-to-end production-grade pages and flows).
- No full faculty portal UX journey (end-to-end production-grade pages and flows).
- Domain frontend modules exist for several areas, but not all are exposed as complete role-specific product pages.

## Quick Start

1. Prepare environment file:
```bash
cp infra/.env.example infra/.env
```

2. Start stack:
```bash
make up
```

3. Open application:
- nginx edge URL exposed by your deployment

4. Stop stack:
```bash
make down
```

## Optional DevTools (Read-Only Data Explorer for Ops)

You can enable pgAdmin in dev/stage profile:

```bash
cd infra
docker compose --env-file .env --profile devtools up -d pgadmin
```

Host loopback URL when the Docker port is published:
- `http://localhost:5050`

Credentials are configured via:
- `PGADMIN_DEFAULT_EMAIL`
- `PGADMIN_DEFAULT_PASSWORD`
- `PGADMIN_BIND_ADDRESS` (defaults to `127.0.0.1`)
- `PGADMIN_PORT`

Use read-only DB users for operational exploration.

Read-only user bootstrap template:
- `infra/sql/create_readonly_user.sql`

## Demo Auth Warning

- Demo users and demo login paths exist only for template/demo bootstrap use.
- They are not a production baseline and must be disabled, removed, or replaced before production launch.
- Every derived project must explicitly review `/api/auth/demo-users`, `/api/auth/demo-login`, and any mock/demo credential flow before go-live.

## Template Bootstrap

Use this repository as the master template, not as a finished product.

1. Copy the template into a new workspace or initialize a new repository from this directory snapshot.
2. Rename project identity in the confirmed template surfaces:
	- `README.md`
	- `docs/project-status.md`
	- `docs/templates/project-context-template.md`
	- user-facing titles/messages that still reference `AI Engineering Center`
3. Copy `infra/.env.example` to `infra/.env` and review the confirmed startup variables before the first run.
4. Fill `PROJECT_CONTEXT.md` from `docs/templates/project-context-template.md` with derived-system scope, roles, integrations, and deployment boundaries.
5. Keep platform-core modules unchanged unless the derived project explicitly approves a platform change.
6. Review demo auth flows and remove, disable, or replace them before promising production readiness.
7. Run template validation before feature work starts.

Confirmed startup variables from `infra/.env.example` that must be reviewed before first Docker start:
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `JWT_SECRET`
- `NEXT_PUBLIC_API_BASE_URL`

Variables that are strongly recommended for real deployments, but can stay empty during initial Docker bootstrap when the related module is unused:
- `INTEGRATIONS_ENCRYPTION_KEY`
- `LDAP_*`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `ANTHROPIC_API_KEY`
- `AI_CUSTOM_PROVIDER_URL`
- `AI_CUSTOM_PROVIDER_API_KEY`

Platform baseline vs scaffold summary:
- Baseline for derived systems: auth, RBAC, audit, i18n, admin console shell, LDAP/AI integration settings, backup workflows.
- Scaffold or partial modules that require explicit review before production reuse: feature flags and observability depth.
- Example-only educational modules: `example_notes` is the canonical small CRUD reference slice; `example_slice` remains a lightweight reference-only wiring example.
- Detailed maturity status is tracked in `docs/templates/platform-maturity-matrix.md`.

Production review areas before launch:
- Replace placeholder secrets and review cookie/auth settings.
- Remove, disable, or replace demo users and demo auth paths.
- Decide whether LDAP/AD is required and validate role mapping.
- Review AI provider policy, rate limits, and provider key handling.
- Confirm backup roots, retention, and restore procedures.
- Confirm TLS certificate lifecycle and rotation policy for production deployment.
- Re-run template validation plus normal backend/frontend checks.

Expected derived-project changes:
- Project identity, copy, and domain-specific UI text.
- Domain routes, services, and data model additions.
- Optional integrations and provider selections.
- Deployment overlays, hostnames, and production secret management.
- Feature-specific modules built on top of the existing platform core.

Template validation entrypoint:
```bash
make template-validate
```

## Docker Validation Commands

Full pipeline:
```bash
make pipeline
```

Host-native frontend npm scripts are intentionally blocked. Run all validation through Docker Compose.

Backend only:
```bash
cd infra
docker compose --env-file .env exec -T backend ruff check .
docker compose --env-file .env run --rm --no-deps backend-tests pytest -q
```

Frontend only:
```bash
cd infra
docker compose --env-file .env run --rm frontend-tests npm run lint
docker compose --env-file .env run --rm frontend-tests npm run test:frontend
```

i18n guardrail for frontend UI dictionaries:
- Canonical key set is `ru`.
- `en` and `kk` must have exact key parity with `ru` (no missing, no extra keys).
- CI runs `npm run i18n:check` before frontend lint/build.

Template validation only:
```bash
make template-validate
```

## Authentication and Security Model

- Signed access tokens are validated server-side.
- Browser flow uses HttpOnly auth cookie.
- Refresh-token flow is not implemented in the current template baseline.
- Legacy identity headers are disabled by default.
- CSRF uses double-submit token for cookie-authenticated `POST/PUT/PATCH/DELETE`.
- Integrations secrets are encrypted at rest in runtime settings storage.

## Configuration Model Summary

- Static baseline comes from environment variables (`infra/.env`).
- Runtime admin settings are stored in integration settings and override env defaults for supported domains (LDAP, AI providers, backup profiles/retention).
- i18n language list persists in PostgreSQL when `DATABASE_URL` is available; otherwise fallback in-memory mode is used.
- RBAC assignments/roles are persisted in PostgreSQL.

## Known Gaps

- Feature flags are scaffold-level (in-memory) and not yet productionized.
- TLS is enabled by default at nginx edge, but certificate lifecycle/rotation policy must be finalized per environment.
- AI Gateway v1 is request/response only in this phase: no streaming, no embeddings, no tools/function-calling orchestration, no RAG/vector DB, no billing/quota subsystem.
- No built-in database admin UI (for example pgAdmin/Adminer) is included in the default stack.
- Student and faculty role-based frontend portals are not fully productized yet; admin UX is currently the primary interface.
- Demo auth paths are intentionally present for local/template use and require explicit removal or replacement in derived production projects.
- `example_notes` is example-only and removable; it exists to teach patterns, not to act as a production business subsystem.
- `example_slice` remains a lightweight reference-only slice for wiring patterns.
- Top-level `tests/` directory is present but not yet populated.

## Repository Structure

```text
/home/sbs/AI/
├── backend/
├── frontend/
├── infra/
├── docs/
├── scripts/
├── tests/
├── .github/workflows/
└── Makefile
```

## Additional Docs

- `docs/project-status.md`
- `docs/configuration-model.md`
- `docs/module-boundaries.md`
- `docs/admin-information-architecture.md`
- `docs/templates/platform-maturity-matrix.md`
- `docs/templates/template-contracts.md`
