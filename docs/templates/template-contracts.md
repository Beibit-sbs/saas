# Stable Template Contracts

This document records contracts that already exist in the repository. It does not define a new architecture.

Template honesty note:
- This file describes confirmed platform-template contracts only.
- It does not imply that scaffold modules are production-ready.
- It does not replace project-specific architecture, threat model, or full API documentation in derived projects.

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
- Example-only reference CRUD routes may use their own namespaced admin prefix such as `/api/admin/example-notes`.
- Admin read/write routes require authenticated actor resolution plus permission checks.
- Admin responses typically return named payload objects instead of raw arrays.
- Sensitive admin mutations are expected to generate audit events.

Demo auth note:
- `/api/auth/demo-users`, `/api/auth/demo-login`, and other demo/mock auth surfaces exist for local/template bootstrap use only and must be reviewed explicitly before production launch in derived projects.

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
- Model registry admin routes are exposed under `/api/admin/ai/models` and use soft-disable (`enabled=false`) as the baseline removal behavior.
- Unified execution route is exposed under `/api/ai/chat`.
- Supported provider names are `openai`, `gemini`, `anthropic`, and `custom`.
- Provider status returns `provider`, `configured`, and `validation_url`.
- Provider validation returns `result` and may surface `429` when runtime rate limits are exceeded.
- Chat request is provider-neutral and supports `model`, `messages[]`, optional `temperature`, optional `max_tokens`.
- Chat response is normalized and provider-neutral: `model`, `provider`, `provider_model_id`, `output_text`, `finish_reason`, `usage`, `latency_ms`.
- Provider-specific execution is isolated behind an internal adapter interface (`AIProviderAdapter`) rather than router-level branching.
- Runtime provider configuration uses the stable `ai.<provider>.*` key pattern.
- AI usage logging captures actor, provider, model, outcome, latency, optional token usage, and failure reason.

Current limitation:
- AI Gateway v1 is non-streaming and text chat only in this phase.
- Embeddings, tools/function-calling orchestration, RAG/vector DB, and billing/quota subsystems are out of current scope.

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

## Frontend i18n Contracts

Confirmed frontend contract:

- UI dictionary sources are centralized under `frontend/i18n/common` and `frontend/i18n/admin`.
- UI language set for frontend dictionaries is `ru`, `en`, `kk`.
- `ru` is canonical for dictionary key sets.
- `en` and `kk` must exactly match `ru` keys (no missing and no extra keys).
- Automated parity check is implemented in `frontend/i18n/check/i18n-check.mjs` and is expected in both local validation and CI before frontend lint/build.

## Auth Session Baseline

Confirmed current repository behavior:
- the template currently implements signed access-token based auth
- browser flows use HttpOnly auth cookies
- CSRF protection applies to cookie-authenticated mutation requests

Current limitation:
- refresh-token flow is not implemented in the current template baseline and should not be assumed by derived projects

## Example Slice Baseline

Confirmed current repository behavior:
- `example_slice` is intentionally namespaced and removable
- it demonstrates RBAC-guarded read access and admin audit logging wiring
- `example_notes` is intentionally namespaced and removable
- it demonstrates the preferred small end-to-end template pattern: migration, service layer, router, RBAC, audit, frontend usage, i18n, and tests

Current limitation:
- `example_notes` is educational and intentionally small; it is not meant to become a production business subsystem
- `example_slice` remains a lightweight reference-only wiring slice rather than the canonical CRUD example