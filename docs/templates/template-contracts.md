# Stable Template Contracts

This document records contracts that already exist in the repository. It does not define a new architecture.

## Platform Settings Keys

Confirmed runtime settings keys stored through the integration settings service:

LDAP runtime keys:
- `ldap.enabled`
- `ldap.server_uri`
- `ldap.bind_dn`
- `ldap.bind_password`
- `ldap.base_dn`
- `ldap.user_filter`
- `ldap.display_name_attribute`
- `ldap.login_attribute`
- `ldap.group_attribute`
- `ldap.group_role_map_json`
- `ldap.default_role`
- `ldap.timeout_seconds`

AI provider runtime keys:
- `ai.openai.api_key`
- `ai.openai.validation_url`
- `ai.gemini.api_key`
- `ai.gemini.validation_url`
- `ai.anthropic.api_key`
- `ai.anthropic.validation_url`
- `ai.custom.api_key`
- `ai.custom.validation_url`

Backup runtime keys:
- `backup.profiles_json`
- `backup.active_profile`
- `backup.retention_days`
- `backup.retention_min_files`

Ownership rule:
- Environment variables provide static baseline defaults.
- Admin runtime settings override environment defaults only for domains that already use `get_runtime_value(...)`.
- Secret values saved through runtime settings are stored encrypted at rest.

## Admin API Patterns

Confirmed admin API conventions in the current backend:

- Admin routes use the `/api/admin` prefix or a nested admin prefix such as `/api/admin/rbac`, `/api/admin/integrations`, `/api/admin/audit`, `/api/admin/backups`, `/api/admin/feature-flags`, `/api/admin/ai`, `/api/admin/ldap`, `/api/admin/i18n`, `/api/admin/local-users`.
- Admin read/write routes require authenticated actor resolution plus permission checks.
- Admin responses typically return named payload objects instead of raw arrays.
- Sensitive admin mutations are expected to generate audit events.

## Audit Event Fields

Confirmed audit event schema fields:

- `event_id`
- `timestamp`
- `actor`
- `action`
- `entity`
- `path`
- `ip`
- `client_ip`
- `result`
- `correlation_id`
- `metadata`

Field conventions:
- `entity` defaults to `admin` when a route does not override it.
- `correlation_id` falls back to the generated event id when none is supplied.
- `metadata` is always stored as an object.
- Audit export surfaces preserve the same logical field set in JSON and CSV form.

## AI Gateway Contract Conventions

Current repository contract:

- Admin AI gateway routes are exposed under `/api/admin/ai`.
- Supported provider names are `openai`, `gemini`, `anthropic`, and `custom`.
- Provider status returns `provider`, `configured`, and `validation_url`.
- Provider validation returns `result` and may surface `429` when runtime rate limits are exceeded.
- Runtime provider configuration uses the stable `ai.<provider>.*` key pattern.

Current limitation:
- The repository currently exposes provider status/validation, not a full public chat/model registry gateway contract.

## Canonical Example Vertical Slice

Reference-only example module contract:

- Backend route: `/api/admin/example-slice/reference-items`.
- Route is RBAC-guarded with `admin.dashboard.read`.
- Route emits audit action `example_slice.read` with entity `example_slice`.
- Response contains `items[]` with fields: `key`, `title`, `required_permission`, `audit_action`.
- Frontend admin overview reads and displays this payload as a template reference block.

Derived-project guidance:
- Keep educational modules namespaced as `example_*`.
- Remove or replace example modules when introducing real domain modules.

## Runtime Configuration Boundaries

Environment-owned baseline configuration:
- DB connection and compose/runtime ports
- auth cookie defaults and JWT secret
- LDAP baseline values
- provider API keys or URLs when admin runtime overrides are not used
- backup allowed roots

Admin runtime-owned configuration domains already present in code:
- LDAP integration settings
- AI provider settings
- backup profiles and retention

Do not assume admin runtime ownership for unrelated domains unless code already uses the runtime settings service for that domain.