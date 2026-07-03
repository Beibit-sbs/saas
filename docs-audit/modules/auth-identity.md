# Модуль: Auth / Identity / RBAC (Аутентификация и идентичность)

[← Каталог модулей](README.md) · [Индекс](../README.md)

Backend: `auth/`, `identity/`, `identity_provider_integration/`, `ldap/`, `sso_saml/`, `two_factor_auth/`, `rbac/`, `service_accounts/`, `local_user_management/`, `profiles/`

## Назначение
Аутентификация (local/LDAP/OIDC/SAML/2FA), управление сессиями и токенами, RBAC/ABAC, сервисные аккаунты, локальные пользователи, профили.

## Бизнес‑функции
Логин/логаут · выдача/ревокация JWT · сессии · 2FA (TOTP) · LDAP/AD · OIDC · SAML SSO · управление ролями/правами · сервисные токены (M2M).

## Пользователи (роли)
Все (аутентификация); `platform_admin`/`admin` (управление ролями, IdP, LDAP).

## Страницы
`/login`, `/profile`, `/console/rbac`, `/console/identity`, `/console/ldap`, `/console/local-users`, `/console/service-accounts`.

## Backend
- **Router:** `auth/router.py` (`/api/auth`), `identity/router.py` + `phase1_router.py`, `ldap/router.py`, `rbac/router.py`, `service_accounts/router.py`.
- **Services:** `auth/token_service.py`, `local_users_service.py`, `session_service.py`, `mfa_service.py`, `platform_superadmin_service.py`; `rbac/service.py`, `security.py`, `abac.py`.

## Database
`app_tenants`, session/MFA таблицы (миграция `f3e4d5c6b7a9_add_auth_session_and_mfa_tables`), `twofa_enrollments/challenges`, `saml_identity_providers/sessions/attribute_mappings`, RBAC persistence (`user_roles`, `role_permissions`; миграции `b7d3f1a9c2e4`, `f9a1b2c3d4e5`).

## API
`/api/auth` (login, login/ldap, mfa/*, logout, demo-users, demo-login), `/api/admin/rbac`, `/api/admin/identity`, `/api/admin/ldap`. См. [../03_ROLES_AND_RBAC.md](../03_ROLES_AND_RBAC.md).

## Токен (JWT)
claims: `user_id, roles, permissions, auth_source, tenant_id, jti, token_type(user|service), session_id, platform_global, issued_at, expires_at`.

## Связанные модули
Все (защита endpoint'ов), `audit` (логи отказов), `sso_saml`, `two_factor_auth`.

## Безопасность
PBKDF2‑SHA256 (200K); cookie HttpOnly + CSRF; revocation в Redis; rate limiting (`security/rate_limit.py`).

## Проблемы / Рекомендации
- **Демо‑доступ** (`demo-users`, `demo-login`) — отключить перед продом (README).
- `identity_phase1` — legacy backward‑compat. **Рекомендация:** зафиксировать список ролей, вывести демо‑пути из прод‑сборки.
