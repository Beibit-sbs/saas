# Configuration Model

## 1. Configuration Sources

Platform configuration is resolved from two layers:

1. Environment variables (`infra/.env` for compose runtime).
2. Runtime settings storage (`app_integration_settings`) for admin-managed values.

For supported domains, runtime settings have higher precedence than env defaults.

---

## 2. Resolution Rules

### `get_runtime_value` precedence

For keys managed by integrations service:
1. Runtime setting (DB-backed when `DATABASE_URL` is available; memory fallback otherwise).
2. Environment variable fallback.
3. Hardcoded default value.

This model is used by:
- LDAP runtime config
- AI provider runtime config
- Backup profiles and active profile
- Backup retention values

---

## 3. Secret Handling Model

Secrets saved via runtime settings are encrypted at rest.

- Encryption mechanism: Fernet
- Key derivation: SHA-256 digest -> URL-safe base64 key material
- Secret source priority:
  1. `INTEGRATIONS_ENCRYPTION_KEY`
  2. fallback to `JWT_SECRET` (dev/local convenience)

Stored secret values use prefix format:
- `enc:v1:<token>`

If DB is unavailable but configured, settings service may fallback to in-memory storage for availability in local/dev scenarios.

---

## 4. Domain Configuration Matrix

## Auth and Session

Environment keys:
- `JWT_SECRET`
- `AUTH_ACCESS_TOKEN_TTL_MINUTES`
- `AUTH_ACCESS_COOKIE_NAME`
- `AUTH_ACCESS_COOKIE_SAMESITE`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- `JWT_REFRESH_TOKEN_EXPIRE_MINUTES`

Behavior:
- Signed token validation with backend-side verification.
- Cookie and bearer auth modes.

## CSRF

Environment keys:
- `AUTH_CSRF_PROTECTION_ENABLED`
- `AUTH_CSRF_COOKIE_NAME`
- `AUTH_CSRF_COOKIE_SAMESITE`

Behavior:
- Enabled by default for cookie-authenticated mutation requests.
- Double-submit token pattern.

## RBAC

Environment keys:
- `RBAC_ALLOW_DEV_FALLBACK`
- `AUTH_DEV_DEMO_COMPATIBILITY`

Behavior:
- DB-backed RBAC by default.
- Dev fallback is explicitly gated and disabled by default.

## LDAP / AD

Environment baseline keys:
- `AUTH_LDAP_ENABLED`
- `LDAP_SERVER_URI`
- `LDAP_BIND_DN`
- `LDAP_BIND_PASSWORD`
- `LDAP_BASE_DN`
- `LDAP_USER_FILTER`
- `LDAP_DISPLAY_NAME_ATTRIBUTE`
- `LDAP_LOGIN_ATTRIBUTE`
- `LDAP_GROUP_ATTRIBUTE`
- `LDAP_GROUP_ROLE_MAP_JSON`
- `LDAP_DEFAULT_ROLE`
- `LDAP_TIMEOUT_SECONDS`

Runtime setting keys (admin-managed):
- `ldap.enabled`
- `ldap.server_uri`
- `ldap.bind_dn`
- `ldap.bind_password` (secret)
- `ldap.base_dn`
- `ldap.user_filter`
- `ldap.display_name_attribute`
- `ldap.login_attribute`
- `ldap.group_attribute`
- `ldap.group_role_map_json`
- `ldap.default_role`
- `ldap.timeout_seconds`

## AI Providers

Environment baseline keys:
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `ANTHROPIC_API_KEY`
- `AI_CUSTOM_PROVIDER_URL`
- `AI_CUSTOM_PROVIDER_API_KEY`
- `AI_PROVIDER_TIMEOUT_SECONDS`

Runtime setting keys (admin-managed):
- `ai.openai.api_key` (secret)
- `ai.openai.validation_url`
- `ai.gemini.api_key` (secret)
- `ai.gemini.validation_url`
- `ai.anthropic.api_key` (secret)
- `ai.anthropic.validation_url`
- `ai.custom.api_key` (secret)
- `ai.custom.validation_url`

## i18n

Environment/runtime dependency:
- Uses `DATABASE_URL` for persistence mode.

Behavior:
- System languages `kk`, `ru`, `en` are seeded and protected.
- Additional languages can be registered in admin.
- Supported UI baseline is `kk/ru/en`.

## Backup

Environment baseline keys:
- `BACKUP_ALLOWED_ROOTS`
- `BACKUP_DEFAULT_PROFILE`
- `BACKUP_PROFILES_JSON`
- `BACKUP_RETENTION_DAYS`
- `BACKUP_RETENTION_MIN_FILES`

Runtime setting keys (admin-managed):
- `backup.active_profile`
- `backup.profiles_json`
- `backup.retention_days`
- `backup.retention_min_files`

Behavior:
- Active profile must exist in profile list.
- Profile paths must be absolute and inside allowlisted roots.

## Feature Flags

Current model:
- Admin API exists (`/api/admin/feature-flags`)
- Storage is scaffold/in-memory (not persistent across restarts)

---

## 5. Operational Notes

- Source of truth for operational runtime values is backend resolution logic, not only `.env`.
- In local non-docker test contexts, `DATABASE_URL` may point to unreachable hostnames (for example `db`); settings service includes guarded fallback behavior for availability.
- Production should set a dedicated `INTEGRATIONS_ENCRYPTION_KEY` and avoid secret fallback to `JWT_SECRET`.
