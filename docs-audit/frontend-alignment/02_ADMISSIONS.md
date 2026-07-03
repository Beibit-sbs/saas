# 02 — Admissions

## Описание модуля
Admissions CRM module (`/console/admissions-crm/*`). Frontend module `modules/admissions-crm`. Backend `admissions_crm/router.py` under `/api/admin/admissions-crm/*`. Reference docs: `docs-audit/modules/admissions.md`.

## Что найдено
- **No frontend defects.** Frontend already correctly aligned:
  - Calls `/api/admin/admissions-crm/*` (leads, qualify, convert-to-applicant, applicants, applications, submit) — paths match backend router exactly.
  - `requiredPermissions=["admin.admissions_crm.read"]` + `ADMISSIONS_CRM_RUNTIME_PERMISSIONS` match backend `admissions_crm/permissions.py` exactly.
  - Page intentionally **fail-closed** on `admin.admissions_crm.read` (message: "fail-closed until the required permission is granted") — correct secure-by-default behaviour.
- **Backend/ops gap (out of scope):** backend `rbac/service.py` grants roles `admissions.read`, **not** `admin.admissions_crm.read` (the CRM permission is ungranted to all roles, including superadmin baseline). This is a backend RBAC configuration gap; frontend correctly mirrors the backend permission.

## Что исправлено
Nothing — frontend required no changes. The fail-closed behaviour is by design and correct.

## Какие файлы изменены
None.

## Какие страницы проверены
14 routes → `AdmissionsCrmPage`. Sidebar entries in `NAVIGATION` + `TENANT_ADMIN_NAVIGATION` (both `PERMISSIONS.ADMISSIONS_READ`). Legacy `platform/admissions` module (`/api/admin/admissions`) also BFF-proxied.

## Какие API используются
`/api/admin/admissions-crm/*` via BFF → backend. Paths verified against `admissions_crm/router.py`.

## Какие Permissions используются
`admin.admissions_crm.read/write/qualify/convert/submit/audit.read` (match backend). Sidebar discoverability uses legacy `admissions.read`.

## Какие Runtime Shell используются
Admissions CRM runtime page (fail-closed gate).

## Какие Workflow проверены
Lead → qualify → convert-to-applicant → application → submit (API path mapping verified).

## Результаты Build / TypeScript / ESLint
- TypeScript: **0 errors**
- ESLint: **clean**
- Build: no changes required.

## Результаты Functional QA
Frontend matches backend; page reachable, fail-closed message informative. No mocks/hardcoded data.

## Список скриншотов
(Pre-pipeline module.)

## Оставшиеся проблемы
Backend RBAC grant for `admin.admissions_crm.read` is an ops/backend step (out of frontend scope) — tracked in `FRONTEND_REMAINING.md`.

## Итоговая готовность
**100%** (frontend) — matches backend + docs; runtime accessibility pending a backend RBAC grant (ops).
