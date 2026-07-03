# Frontend Alignment — Remaining Issues

Tracks open discrepancies discovered during module-by-module alignment.
Backend/API changes are out of scope by directive — items requiring backend/ops changes are flagged as such.

| Модуль | Проблема | Приоритет | Статус |
|--------|----------|-----------|--------|
| Admissions | Backend RBAC grants `admissions.read` but CRM router requires `admin.admissions_crm.read` (ungranted to all roles) → CRM page fail-closed until backend grant. Backend/ops change, out of frontend scope. | Medium | Open (backend/ops) |
| AI | AI Gateway v1 admin endpoints `/api/admin/ai/{models,providers,prices,safety-policies}` have no frontend UI and are not listed as pages in `docs-audit/modules/ai.md`. Building = inventing architecture. | Low | Deferred (out of scope) |
| Auth / Identity | Admin i18n dictionaries (`i18n/admin/ru.ts`, `kk.ts`) contain English strings for some admin keys (e.g. `rbacRolesTitle`). Keys now RESOLVE (fixed), but RU/KK translation completeness is a content follow-up. | Low | Open (content) |
| Auth / Identity | Backend endpoints without UI: MFA enable/verify/disable, session list/revoke, OIDC initiate, identity mapping edit/delete. Not listed as pages in docs-audit. | Low | Deferred (out of scope) |
| Campus Facilities | `guards.ts` `CAMPUS_FACILITIES_PERMISSIONS` enumeration (length-locked at 46 by a test) still lists old transport/bridge strings; the functional gate (route definitions) is fixed, but full enum reconciliation to backend taxonomy is a follow-up. | Low | Open |
| Campus Facilities | Metadata-write (POST) parity for superadmin gated separately from VIEW; full write-parity is a follow-up. | Low | Open |

_Last updated: 2026-07-03._
