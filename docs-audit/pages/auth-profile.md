# Страница‑зона: Auth / Профиль / Корень

[← Каталог страниц](README.md)

## Страницы

| URL | Файл | Назначение |
|-----|------|-----------|
| `/` | `frontend/app/page.tsx` | Landing/диспетчер: редирект на login или console по auth‑состоянию |
| `/login` | `frontend/app/login/page.tsx` (+ `tenant-directory.ts`) | Вход; валидация токена, редирект авторизованного на `/console` |
| `/profile` | `frontend/app/profile/page.tsx` | Профиль/настройки пользователя (все аутентифицированные) |
| `(auth)` | `frontend/app/(auth)/` | Только layout, без страниц |
| `/api` | `frontend/app/api/` | Next.js route handlers (в т.ч. auth‑прокси) |

## Доступ / Permissions
`/login` и `/api/auth/login` — доступны неаутентифицированным. `/profile` — любой аутентифицированный. Логика — `middleware.ts` (проверка `exp`, cookie `app_access_token`/`admin_token`).

## Backend API
`/api/auth/*` (login, login/ldap, mfa/*, logout, demo-users, demo-login, refresh). См. [../modules/auth-identity.md](../modules/auth-identity.md).

## Методы аутентификации
local (PBKDF2), LDAP/AD, OIDC, SAML, 2FA/TOTP.

## Проблемы
Демо‑пути (`demo-users`, `demo-login`) — отключить перед продом.
