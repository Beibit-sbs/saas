# API‑группа: Auth (`/api/auth`)

[← Каталог API](README.md) · Модуль: [../modules/auth-identity.md](../modules/auth-identity.md)

Роутер: `auth/router.py` · Часть путей публична (login), остальные — аутентифицированы.

## Endpoints (сводно)

| Метод | Путь | Описание | Permissions |
|-------|------|----------|-------------|
| POST | `/api/auth/login` | Вход local (username/password → JWT cookie) | public |
| POST | `/api/auth/login/ldap` | Вход через LDAP/AD | public |
| POST | `/api/auth/logout` | Выход (revoke сессии + jti) | auth |
| POST | `/api/auth/refresh` | Обновление access‑токена | refresh cookie |
| GET | `/api/auth/demo-users` | Демо‑пользователи (**только шаблон/демо**) | public (отключить в проде) |
| POST | `/api/auth/demo-login` | Демо‑вход (**только шаблон/демо**) | public (отключить в проде) |
| POST | `/api/auth/mfa/enroll` | Инициировать 2FA (TOTP) | auth |
| POST | `/api/auth/mfa/verify` | Проверить код 2FA | auth |
| POST | `/api/auth/mfa/disable` | Отключить 2FA | auth |

## Request/Response
Login → `{access_token в cookie, csrf, user claims}`. Токен‑claims: `user_id, roles, permissions, auth_source, tenant_id, jti, token_type, session_id, platform_global, issued_at, expires_at`.

## Безопасность
PBKDF2‑SHA256 (200K); HttpOnly cookie + CSRF; revocation в Redis; rate limiting (`security/rate_limit.py`); SAML/OIDC — через `sso_saml`/`identity`.

## Проблемы
Демо‑пути обязательны к отключению перед продакшеном (README).
