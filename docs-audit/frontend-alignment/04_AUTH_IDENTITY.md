# 04 — Auth / Identity / RBAC

## Описание модуля
Аутентификация и идентичность: local/LDAP/OIDC/SAML login, сессии/токены (JWT), 2FA, RBAC/ABAC, сервисные аккаунты, локальные пользователи, профили.
Backend: `auth/`, `identity/`, `ldap/`, `rbac/`, `service_accounts/`, `admin/local_users_router.py`, `profiles/`.
Документация: `docs-audit/modules/auth-identity.md`. Страницы по спеке: `/login`, `/profile`, `/console/rbac`, `/console/identity`, `/console/ldap`, `/console/local-users`, `/console/service-accounts`.

## Что найдено
1. **КРИТИЧНО — сырые i18n‑ключи на admin‑страницах (runtime).** RBAC и все остальные admin‑страницы этого модуля выводили СЫРЫЕ ключи перевода (`rbacRolesTitle`, `rbacRoleName`, `rbacRevoke`, `identityProvider`, `serviceAccountName`, `localEditDisplayName`, `roles` …) вместо подписей. Обнаружено ТОЛЬКО в живом браузере (скриншот) — статический анализ путей/прав это не выявил.
   - **Корень:** `LanguageProvider.t()` читает лишь `commonTranslations` (`i18n/common`). Словарь `adminTranslations` (`i18n/admin/{ru,en,kk,ar}.ts`, где ЕСТЬ все admin‑ключи) был **мёртвым кодом** — нигде не импортировался/не использовался (grep: 3 само‑ссылки в `i18n/admin/index.ts`). При отсутствии ключа `t()` возвращает сам ключ.
   - Затрагивало 5 страниц: rbac, identity, ldap, local-users, service-accounts (у всех паттерн `tAny = (k)=>t(k as never)` с admin‑ключами).
2. Соответствие API/прав: **расхождений нет.** 100% фронтовых путей совпадают с backend‑маршрутами (нет риска 404); все permissions совпадают.
3. Mock/fake/hardcoded: **нет.** Все страницы используют реальный API (`apiGet/apiPost/apiPatch/apiDelete`, React Query).
4. Backend‑endpoints без UI (MFA, sessions, OIDC‑инициация, identity mapping edit/delete) — **не** перечислены как страницы в docs‑audit (см. «Оставшиеся проблемы»); вне scope.

## Что исправлено
- Подключён `adminTranslations` в `LanguageProvider`: `getRuntimeDictionary()` теперь возвращает `{...admin[locale], ...common[locale]}` (common имеет приоритет — изменение чисто аддитивное, существующие строки не меняются); fallback‑словари `ruDict/enDict` тоже берутся из `getRuntimeDictionary`. Все admin‑ключи резолвятся. Исправляет RBAC и остальные 4 страницы разом (и ретроспективно любые другие admin‑модули с admin‑ключами).

## Какие файлы изменены
- `frontend/app/components/LanguageProvider.tsx` (единственное изменение; 3 правки: импорт + `getRuntimeDictionary` merge + `ruDict/enDict`).

## Какие страницы проверены (live)
| Страница | H1 | Данные |
|----------|----|--------|
| `/login` | — | Форма логина (username/password/tenant), реальная авторизация |
| `/profile` | Профиль пользователя | Реальные данные сессии (Platform Superadmin, local.001, superadmin, язык ru) + форма выбора языка |
| `/console/rbac` | RBAC | 2 таблицы (Роли + Назначения), реальные роли/назначения, 2 drawer‑формы, CRUD |
| `/console/identity` | Идентификация и доступ | 3 таблицы (провайдеры/directory/mappings), форма mapping, кнопка Test |
| `/console/ldap` | LDAP | Реальный статус LDAP (Выключен) + форма Test connection |
| `/console/local-users` | Локальные пользователи | Реальная таблица пользователей (platform_admin, inst_admin, acad_admin, qa.*), поиск + фильтр |
| `/console/service-accounts` | Сервисные аккаунты | Таблица + кнопка «Добавить» + реальное empty‑state |

## Какие API используются (все 200)
- `GET/POST /api/admin/rbac/roles`, `POST /api/admin/rbac/assign`, `GET /api/admin/rbac/assignments`, `DELETE /api/admin/rbac/assignments/{user}/{role}`
- `GET /api/admin/identity/{providers,directory-providers,mappings}`, `POST .../directory-providers/{id}/test`, `POST .../mappings`
- `GET /api/admin/ldap/status`, `POST /api/admin/ldap/test-connection`
- `GET/POST/PATCH/DELETE /api/admin/local-users`, `POST .../{id}/password`
- `GET/POST /api/admin/service-accounts`, `POST .../{id}/token`, `POST .../{id}/revoke`
- `POST /api/auth/login`, `GET /api/auth/me`, `GET /api/auth/csrf`, `GET/PUT /api/auth/me/preferences[/language]`
All via BFF proxy (`/api/bff/...`). No 401/403/404/500 while authenticated.

## Какие Permissions используются
`admin.roles.manage` (rbac), `admin.integrations.manage` (identity/ldap/service-accounts), `admin.users.manage` (local-users), `profiles.read/write` (profiles). Все совпадают с backend. superadmin имеет все → нет отказов доступа.

## Какие Runtime Shell используются
Нет — модуль состоит из admin‑CRUD страниц (без runtime‑shell архитектуры).

## Какие Workflow проверены
Login → session (`/me`); role upsert/assign/revoke; identity provider test + mapping create; LDAP test‑connection; local user CRUD + password set; service‑account create + issue token + revoke; profile language change + persist.

## Результаты Build / TypeScript / ESLint
- **TypeScript:** PASS (`tsc --noEmit` EXIT=0; language‑server clean).
- **ESLint:** PASS (EXIT=0 на изменённом файле; `next build` lint — только 2 pre‑existing warning в courses/grades, не относятся к модулю).
- **Build:** PASS (frontend image пересобран, `✓ Compiled successfully`, static pages 383/383, контейнер `ai-frontend-1` healthy).

## Результаты Functional QA
**PASS.** Все 7 страниц открываются; 0 console errors; 0 failed network; 0 raw i18n keys (после фикса — verified `rawKeysFound: []` на всех 5 admin‑страницах); реальные данные из backend; формы/таблицы/кнопки/drawer‑диалоги на месте; RBAC/permissions корректны; sidebar‑навигация работает.

## Список скриншотов
- rbac (после фикса — «Roles and permissions», «Role name», «Save role», реальные роли)
- identity (Identity/Directory провайдеры, форма Login)
- ldap (статус Выключен, Test‑connection форма)
- local-users (реальная таблица пользователей + поиск/фильтр)
- service-accounts (таблица + Добавить + empty‑state)
- profile (реальные данные сессии + выбор языка)
- login (форма авторизации — использована при аутентификации)

## Оставшиеся проблемы
1. **Admin ru/kk словарь частично на английском** (translation‑completeness): напр. `rbacRolesTitle` в `i18n/admin/ru.ts` = «Roles and permissions». Фикс делает ключи ЧИТАЕМЫМИ (не сырыми); перевод на RU/KK — отдельная низкоприоритетная задача (нельзя «выдумывать» переводы). → FRONTEND_REMAINING.
2. **Backend endpoints без UI** (MFA enable/verify/disable, sessions list/revoke, OIDC initiate, identity mapping edit/delete) — НЕ в списке страниц docs‑audit; построение = изобретение архитектуры сверх документации. Вне scope (аналогично AI Gateway v1). → FRONTEND_REMAINING (Low).
3. **Admissions‑style:** нет (все права выданы superadmin, страницы открываются).

## Итоговая готовность
**100%** соответствия docs‑audit по страницам модуля: все 7 документированных страниц реализованы, работают на реальном API, без mock, с корректными правами и навигацией; критичный i18n‑баг исправлен и подтверждён вживую. Недокументированные backend‑возможности (MFA/sessions/OIDC UI) вне scope.

---

## Чеклист завершения модуля
| Пункт | Рабочие / Всего | Статус |
|-------|-----------------|--------|
| Pages | 7 / 7 | ✅ |
| Components (shared UI) | все | ✅ |
| Forms | 8 / 8 (rbac×2, identity×1, ldap×1, local-users×1, service-accounts×2, profile×1) | ✅ |
| Dialogs (drawers) | 4 / 4 (rbac×2, service-accounts×2) + local-users drawer | ✅ |
| Tables | 7 / 7 (rbac×2, identity×3, local-users×1, service-accounts×1) | ✅ |
| Charts | 0 / 0 (нет в модуле) | — |
| Buttons | все (save/assign/revoke/edit/test/add/issue-token/apply) | ✅ |
| Routes | 7 / 7 | ✅ |
| API 200 | все авторизованные вызовы | ✅ |
| API 401 | только до логина (ожидаемо) | ✅ |
| API 403 | 0 | ✅ |
| API 404 | 0 | ✅ |
| API 500 | 0 | ✅ |
| Runtime Shell | N/A (нет в модуле) | — |
| Navigation | Работает | ✅ |
| Sidebar | Работает | ✅ |
| Permissions | Работают | ✅ |
| RBAC | Работает | ✅ |
| Workflow | Работает | ✅ |
| Build | PASS | ✅ |
| TypeScript | PASS | ✅ |
| ESLint | PASS | ✅ |
| Playwright | PASS | ✅ |
| Functional QA | PASS | ✅ |
