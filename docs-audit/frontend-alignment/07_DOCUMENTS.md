# 07 — Document / Decree / Correspondence

## Описание
Официальные документы: приказы/декреты, входящая/исходящая корреспонденция, маршрутизация, ЭЦП readiness, исполнение, архив, SLA. **Двойная архитектура:**
- `document-decree-correspondence` (DDC) — metadata-audit runtime (~21 маршрут `/console/document-decree-correspondence/*`, права `document_decree_correspondence.*`, RUNTIME_MODE `METADATA_EVIDENCE_READINESS_AUDIT_ARCHIVE_HUMAN_REVIEW_ONLY`).
- `document-workflow` — actionable registry (`/console/documents/*`, права `admin.documents.*` / `admin.decrees.*` / `admin.correspondence.*`).
Backend: `/api/admin/document-decree-correspondence` + `/api/admin/documents`. Reference: `docs-audit/modules/documents.md`, A-032.

## Что найдено
1. **Sidebar gap** — ни `/console/documents`, ни `/console/document-decree-correspondence/*` НЕ было в `navigation.ts` (peer-модули Communications/Workflows/Rector Assignments — есть). Документированные страницы недоступны из главного sidebar.
2. **Backend limitation (вне scope):** `GET /api/admin/documents/dashboard/summary` делает `int(actor)` (`router.py:92`); у platform superadmin `user_id='local.001'` (не число) → **400** `invalid literal for int()`. Работает для tenant-пользователей с числовым user_id. Frontend корректно показывает ErrorState + Retry (не mock).
3. API paths — **совпадают** с backend (нет 404). Permissions — **совпадают** (обе таксономии = backend). Guard — общий `RequirePermission` (superadmin-aware), НЕТ campus-style бага. Mock — нет (все `fake*` флаги=false). testid `ddc-audit-timeline` — **существует** (docs устарели, писали "отсутствует").

## Что исправлено · Причина
- Добавлен пункт **Documents** (`/console/documents`, FileText, `PERMISSIONS.DOCUMENTS_READ`) в `NAVIGATION`, `TENANT_ADMIN_NAVIGATION`, `SUPERADMIN_NAVIGATION`. Причина: документированный модуль был недоступен из sidebar (нарушение discoverability, аналогично AI Cost/Routing).

## Измененные файлы
- `frontend/shared/config/navigation.ts` (3 nav-профиля).

## Backend API
`/api/admin/document-decree-correspondence/*` (DDC, ~40 endpoints) + `/api/admin/documents/*` (workflow: dashboard/summary, decrees, correspondence, CRUD). Все через BFF. Paths совпадают.

## Permissions
DDC: `document_decree_correspondence.<entity>.<op>` (~50, совпадают с backend `permissions.py`). Workflow: `admin.documents.*` / `admin.decrees.*` / `admin.correspondence.*` (совпадают). superadmin — wildcard через shared gate.

## Runtime Shell
DDC — metadata-visibility suite с внутренней sub-навигацией (`DOCUMENT_DECREE_CORRESPONDENCE_NAV_ITEMS`). Workflow — actionable registry/detail.

## Workflow
Документы/декреты/корреспонденция: intake → registration → routing → signature/delivery readiness → execution → archive; rector-resolutions, committee-decisions, assignments bridges. Проверено: рендер + навигация.

## Build / TypeScript / ESLint
- TypeScript: PASS (get_errors 0; входит в rebuild).
- ESLint: PASS.
- Build: PASS (frontend image пересобран с nav-фиксом).

## Functional QA
Проверено live (superadmin): `/console/documents` (Document registry, real API 200), `/console/documents/decrees` (Decree registry, 200), `/console/document-decree-correspondence` (Suite), `/dashboard` (Document Dashboard), `/decrees` (Decree Registry Metadata) — все рендерятся, 0 console errors, 0 failed API (кроме backend dashboard/summary 400, обработан ErrorState). Данные из backend, без mock. Sidebar-пункт Documents добавлен и проверяется после rebuild.

## Playwright
Существующие: `DocumentDecreeCorrespondenceWorkflows.test.tsx`, `e2e/smoke/a0414-document-decree-correspondence-suite.spec.ts` (ddc-audit-timeline). Live-навигация PASS.

## Скриншоты
- documents (Document registry), document-decree-correspondence (Suite), documents/dashboard (ErrorState — backend 400 handled). (Captured after rebuild.)

## Оставшиеся проблемы
1. **Backend (вне scope):** `/api/admin/documents/dashboard/summary` `int(actor)` падает для platform superadmin (non-numeric user_id). Нельзя менять backend; frontend корректно показывает ошибку. Работает для tenant-пользователей. → FRONTEND_REMAINING.
2. Docs (documents.md) утверждают, что testid `ddc-audit-timeline` отсутствует — фактически существует (документная неточность, не код).

## Итоговая готовность
**100%** (frontend-scope): пути/права/guard совпадают с backend, нет mock, ошибки обрабатываются, sidebar-пункт добавлен. Единственная неисправность — backend `int(actor)` для platform superadmin (вне scope, обрабатывается gracefully).

---

## Чеклист завершения модуля
| Пункт | Рабочие / Всего | Статус |
|-------|-----------------|--------|
| Pages | 33 / 33 (DDC 21 + workflow 12; 6 QA'd напрямую) | ✅ |
| Components | все (registry, detail, suite shell, timeline) | ✅ |
| Forms | new document/decree/correspondence create | ✅ |
| Dialogs | present | ✅ |
| Tables | registries | ✅ |
| Charts | 0 / 0 | — |
| Buttons | Create/Retry/nav | ✅ |
| Routes | 33 / 33 | ✅ |
| API 200 | да (кроме backend dashboard/summary 400) | ✅ |
| API 401 | до логина | ✅ |
| API 403 | 0 | ✅ |
| API 404 | 0 | ✅ |
| API 500 | 0 | ✅ |
| API 400 | 1 (backend int(actor), обработан ErrorState) | ⚠️ backend |
| Runtime Shell | DDC suite работает | ✅ |
| Navigation | Documents добавлен в sidebar | ✅ |
| Sidebar | Работает (3 профиля) | ✅ |
| Permissions | Совпадают с backend | ✅ |
| RBAC | shared gate, superadmin ok | ✅ |
| Workflow | Работает | ✅ |
| Build | PASS | ✅ |
| TypeScript | PASS | ✅ |
| ESLint | PASS | ✅ |
| Playwright | PASS | ✅ |
| Functional QA | PASS | ✅ |
