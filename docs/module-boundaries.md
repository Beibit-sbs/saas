# Module Boundaries

## 1. High-Level Boundaries

## Frontend (`frontend/`)

Responsibility:
- UI composition and user interaction.
- Calls backend APIs for all privileged operations.
- No authority for identity, RBAC decisions, or secret processing.

Key areas:
- `/admin` operational console
- `/login` auth entry
- `/profile` user profile/preferences
- Language provider for UI localization

## Backend (`backend/`)

Responsibility:
- Source of truth for security, authorization, runtime settings, and business operations.
- API contracts for all platform modules.
- Data access and persistence logic.

Key module groups:
- `auth`
- `rbac`
- `audit`
- `integrations`
- `ldap`
- `ai_gateway`
- `i18n`
- `backup`
- `feature_flags`
- `admin`
- `observability`

## Infrastructure (`infra/`)

Responsibility:
- Runtime orchestration and network boundaries.
- Reverse proxy routing and service startup order.

Current model:
- `db`, `backend`, `frontend`, `nginx` via Docker Compose.

---

## 2. Security Boundary Rules

1. Identity is validated only on backend.
2. Role/permission resolution is backend-owned (RBAC service).
3. Frontend cannot grant itself permissions.
4. Secret values are handled and encrypted on backend.
5. Cookie-authenticated mutation requests are CSRF-protected on backend.

---

## 3. Data Ownership

## PostgreSQL-owned

- RBAC persistence tables
- Audit events table
- Integration settings table (runtime config + encrypted secrets)
- i18n language registry (when DB mode is active)

## Memory-backed (current scaffold scope)

- Feature flags store
- Fallback settings/language/audit buffers when DB is unavailable

---

## 4. API Boundary Map

Admin-facing API prefixes:
- `/api/admin`
- `/api/admin/rbac`
- `/api/admin/audit`
- `/api/admin/i18n`
- `/api/admin/integrations`
- `/api/admin/ldap`
- `/api/admin/ai`
- `/api/admin/backups`
- `/api/admin/feature-flags`

Auth/user-facing prefixes:
- `/api/auth/*`
- `/api/health`
- `/health`
- `/metrics`

Boundary principle:
- Frontend consumes APIs only; backend modules coordinate internal services and persistence.

---

## 5. Admin Console Boundary by Tab

- `overview`: read-only operational snapshot.
- `languages`: i18n registry operations.
- `local-users`: local account lifecycle management.
- `rbac`: role and assignment management.
- `integrations`: LDAP/AI runtime settings management.
- `feature-flags`: feature flag visibility and toggles.
- `backups`: backup/retention/restore operations.
- `audit`: query and export audit events.

All tab actions requiring privilege are enforced by backend RBAC permissions.

---

## 6. Current Boundary Gaps

- Feature flags persistence boundary is not yet implemented (in-memory only).
- Base infrastructure boundary does not yet include TLS termination in default profile.
