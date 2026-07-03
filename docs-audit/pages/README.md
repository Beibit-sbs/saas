# Каталог страниц (Pages Catalog)

[← Индекс аудита](../README.md)

Frontend — Next.js App Router (`frontend/app/`), **~380** файлов `page.tsx`. Ролевые зоны и маршрутизация — `frontend/middleware.ts`.

## Ролевые зоны (файлы)

| Зона | Файл | URL |
|------|------|-----|
| Админ‑консоль | [admin-console.md](admin-console.md) | `/console/*` (~370 страниц) |
| Портал студента | [student-portal.md](student-portal.md) | `/student` |
| Портал преподавателя | [faculty-portal.md](faculty-portal.md) | `/faculty` |
| Портал регистратора | [registrar-portal.md](registrar-portal.md) | `/registrar` |
| Auth / профиль | [auth-profile.md](auth-profile.md) | `/login`, `/profile`, `/`, `(auth)` |

## Формат (для каждой страницы)
URL · Название · Назначение · Модуль · Runtime Shell · Backend API · Permissions · Компоненты · Сервисы · Таблицы.

> Из‑за объёма (~380 страниц) поштучные файлы на каждую страницу не создавались; страницы каталогизированы по зонам и группам доменов (ниже). Детализация конкретной страницы выводима из соответствующего файла [../modules/](../modules/) (там указаны маршруты, API, permissions, таблицы).

## Группы страниц админ‑консоли (по доменам)

| Группа | Маршруты (примеры) | Модуль |
|--------|--------------------|--------|
| Academic & Enrollment | `/console/academic-operations/*` (19), `/console/enrollments`, `/console/grades`, `/console/transcripts`, `/console/degree-progress`, `/console/scheduling`, `/console/courses`, `/console/exam-governance`, `/console/thesis`, `/console/teaching-quality` | [academic-operations](../modules/academic-operations.md), [scheduling](../modules/scheduling-timetable.md) |
| Admissions | `/console/admissions/*` (11), `/console/admissions-crm` | [admissions](../modules/admissions.md) |
| Student Support & Advising | `/console/student-success/*` (11), `/console/advising`, `/console/student-services`, `/console/student-services-welfare-support`, `/console/career-services`, `/console/financial-aid`, `/console/housing` | [student-success](../modules/student-success.md), [student-lifecycle](../modules/student-lifecycle.md) |
| Research & Innovation | `/console/research-brain`, `/console/research-science/*` (7), `/console/innovation-commercialization`, `/console/digital-twin` | [research-science](../modules/research-science.md) |
| People & HR | `/console/hr-staff-governance/*` (15), `/console/hr-payroll`, `/console/faculty`, `/console/faculty-performance-kpis`, `/console/faculty-copilot` | [hr-staff-governance](../modules/hr-staff-governance.md) |
| Finance & Procurement | `/console/billing/*` (7), `/console/finance-procurement-asset/*` (21), `/console/budget-planning`, `/console/delinquency-collections`, `/console/expense-controls`, `/console/contracts-legal-repository` | [finance-procurement-asset](../modules/finance-procurement-asset.md) |
| Campus & Facilities | `/console/campus-facilities/*` (23) | [campus-facilities](../modules/campus-facilities.md) |
| Operations & Governance | `/console/executive-control-tower/*` (8), `/console/executive-governance`, `/console/communications/*` (9), `/console/document-decree-correspondence/*` (20), `/console/workflows`, `/console/interventions/*` (6), `/console/jobs`, `/console/automation/*` (4), `/console/audit`, `/console/notifications` | [executive-governance](../modules/executive-governance.md), [documents](../modules/documents.md), [communications](../modules/communications.md) |
| Records & Administration | `/console/records`, `/console/documents/*` (7), `/console/org-units`, `/console/local-users`, `/console/identity`, `/console/ldap`, `/console/access-control`, `/console/rbac`, `/console/security-access-compliance`, `/console/visitor-management` | [auth-identity](../modules/auth-identity.md), [security-access-compliance](../modules/security-access-compliance.md) |
| Platform & Developer | `/console/platform/*` (5+), `/console/developer/*` (2), `/console/ai/*` (5), `/console/integrations/*` (2), `/console/health`, `/console/ops`, `/console/model-evaluation`, `/console/knowledge-retrieval`, `/console/prompt-management` | [platform-core](../modules/platform-core.md), [ai](../modules/ai.md) |
| Quality & Compliance | `/console/quality-accreditation/*`, `/console/accreditation-compliance`, `/console/academic-integrity`, `/console/reporting-runtime` | [quality-accreditation](../modules/quality-accreditation.md) |
| Misc | `/console/alumni`, `/console/syllabus-governance`, `/console/currency-localization`, `/console/languages`, `/console/event-management`, `/console/my-assignments/*` (3), `/console/preferences`, `/console/workload` | [../modules/README.md](../modules/README.md) |

## Общие компоненты страниц
Shared UI: `app-sidebar`, `app-topbar`, `page-header`, `data-table`, `filter-bar`, `metric-card`, `permission-gate`, `require-admin-role`, диалоги, toast. Данные — React Query; формы — RHF+Zod.
