# Admin Platform Roadmap

## Purpose
Define a reusable admin panel baseline for all platform-based projects.

## Design Principles
- Backend is source of truth for authorization and critical decisions.
- Frontend can hide controls, but backend must always enforce permissions.
- Every admin action must be auditable.
- Risky features should be released behind feature flags.

## Universal Admin Modules
- Users
- Roles and Permissions
- Audit Viewer
- Integrations
- Feature Flags
- I18n Manager
- System Settings
- Rate Limits and Quotas
- Jobs and Maintenance

## P1 Modules (Recommended First)

### 1. Audit Viewer
Minimum capabilities:
- Filter by actor, action, entity, date range.
- Show correlation ID and request metadata.
- Export CSV/JSON.

Suggested API:
- `GET /api/admin/audit/events`
- `GET /api/admin/audit/export`

Required permissions:
- `admin.audit.read`

### 2. Roles and Permissions Matrix
Minimum capabilities:
- List roles and permissions.
- Add or update role.
- Assign role to user.
- Change history for permission updates.

Suggested API:
- `GET /api/admin/rbac/roles`
- `POST /api/admin/rbac/roles`
- `POST /api/admin/rbac/assign`

Required permissions:
- `admin.roles.manage`

### 3. Integrations Status
Minimum capabilities:
- Show provider health (LDAP/AD, AI providers, SMTP/Webhooks).
- Test connection endpoint.
- Last error and last success timestamp.

Suggested API:
- `GET /api/admin/integrations/status`
- `POST /api/admin/integrations/test`

Required permissions:
- `admin.integrations.manage`

### 4. Feature Flags
Minimum capabilities:
- List flags with scope (`global`, `role`, `user`).
- Enable/disable flags.
- Track who changed flag and when.

Suggested API:
- `GET /api/admin/feature-flags`
- `POST /api/admin/feature-flags`

Required permissions:
- `admin.integrations.manage`

## P2 Modules (Next Phase)

### 5. System Settings
Minimum capabilities:
- Typed settings store.
- Change review and rollback.
- Validation before apply.

Suggested API:
- `GET /api/admin/settings`
- `PUT /api/admin/settings`

Required permissions:
- `admin.settings.manage`

### 6. Rate Limits and Quotas
Minimum capabilities:
- Per-role and per-provider limits.
- Current utilization and threshold alerts.
- Temporary override with expiry.

Suggested API:
- `GET /api/admin/limits`
- `PUT /api/admin/limits`

Required permissions:
- `admin.security.manage`

### 7. Jobs and Maintenance
Minimum capabilities:
- Backup/restore jobs status.
- Migration status and current schema version.
- Retry failed jobs.

Suggested API:
- `GET /api/admin/jobs`
- `POST /api/admin/jobs/{id}/retry`

Required permissions:
- `admin.operations.manage`

## P3 Modules (Optional)

### 8. Support Tools
- View as role.
- Impersonation with strict audit and time limit.
- Diagnostics bundle without secrets.

## Admin Security Checklist
- Every endpoint is permission-protected in backend.
- Sensitive actions emit audit event with actor and metadata.
- All admin forms are protected against CSRF/XSS.
- Secret values are never returned in API responses.

## Release Strategy
1. Add backend contract and tests.
2. Add minimal frontend page with safe defaults.
3. Gate risky paths by feature flags.
4. Validate with `pytest`, `lint`, `build`, and compose smoke tests.
