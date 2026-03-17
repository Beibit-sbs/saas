# AI Engineering Center

Platform template for browser-based systems with a reusable university-focused core.

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
- i18n language registry with protected system languages `kk`, `ru`, `en`
- Audit logging
- Backup management (profiles, retention, restore)
- Feature flags module (currently scaffold/in-memory)
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
- `backups`
- `audit`

Operational highlights:
- Overview dashboard with system, RBAC, language, integrations, backups, and audit snapshot indicators.
- Local users CRUD and password reset.
- RBAC role management and assignment/revoke flows.
- Language registry management with protected system languages.
- Integrations management for LDAP and AI providers.
- Backup profile management, retention dry-run/apply, restore dry-run/execute.
- Audit explorer with filters (`actor`, `action`, `entity`, `result`, `correlation_id`, `since`) and JSON/CSV export.
- Feature flags visibility and on/off toggle via admin API.

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
- `http://localhost`

4. Stop stack:
```bash
make down
```

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
6. Run template validation before feature work starts.

Confirmed startup variables from `infra/.env.example` that must be reviewed before first local use:
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `JWT_SECRET`
- `NEXT_PUBLIC_API_BASE_URL`

Variables that are strongly recommended for real deployments, but can stay empty in local bootstrap when the related module is unused:
- `INTEGRATIONS_ENCRYPTION_KEY`
- `LDAP_*`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `ANTHROPIC_API_KEY`
- `AI_CUSTOM_PROVIDER_URL`
- `AI_CUSTOM_PROVIDER_API_KEY`

Platform baseline vs scaffold summary:
- Baseline for derived systems: auth, RBAC, audit, i18n, admin console shell, LDAP/AI integration settings, backup workflows.
- Scaffold or partial modules that require explicit review before production reuse: AI gateway, feature flags, observability depth, base infra TLS.
- Detailed maturity status is tracked in `docs/templates/platform-maturity-matrix.md`.

Production review areas before launch:
- Replace placeholder secrets and review cookie/auth settings.
- Decide whether LDAP/AD is required and validate role mapping.
- Review AI provider policy, rate limits, and provider key handling.
- Confirm backup roots, retention, and restore procedures.
- Add TLS termination for production deployment.
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

## Local Validation Commands

Full pipeline:
```bash
make pipeline
```

Backend only:
```bash
cd /home/sbs/AI/backend
source .venv/bin/activate
ruff check .
pytest -q
```

Frontend only:
```bash
cd /home/sbs/AI/frontend
npm run lint
npm run build
```

Template validation only:
```bash
make template-validate
```

## Authentication and Security Model

- Signed access tokens are validated server-side.
- Browser flow uses HttpOnly auth cookie.
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
- Base Nginx profile is HTTP-only (no default TLS termination).
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
