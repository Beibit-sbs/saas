# 05 — Полный аудит API

[← 04 База данных](04_DATABASE.md) · [Индекс](README.md) · Далее: [06 Runtime Shells →](06_RUNTIME_SHELLS.md)

Источник: `backend/app/main.py` (регистрация роутеров), `app/modules/*/router.py`, `app/platform/router_*.py`. Каталог по логическим группам: [api/README.md](api/README.md).

---

## 6.1 Обзор поверхности API

- **Всего роутеров: 151** (143 модульных + 8 платформенных).
- **Permission‑guarded endpoints: 685+** (по `SBS_UB_PROJECT_CONTEXT_2026.md`); каждый защищён `permission_dependency(...)`.
- **Стиль:** REST, JSON. Префиксы: `/api/admin/...` (админ‑консоль), `/api/...` (публичные/доменные), `/api/v1/...` и `/api/v2/...` (платформа), `/api/dev` (developer), `/api/bff/...` (BFF ops).
- **Аутентификация:** JWT cookie/Bearer; developer API — `X‑App‑Key`/`X‑App‑Secret`; internal/mcp — Bearer со scopes.
- **Обработка ошибок:** унифицирована (`app/core/module_helpers/router_errors.py`): 400 (валидация), 401, 403 (permission/tenant), 404, 409 (конфликт/версия), 429 (rate limit).

---

## 6.2 Группы API (сводная таблица)

### Платформа и админ (11)
`admin` `/api/admin` · `rbac` `/api/admin/rbac` · `audit` `/api/admin/audit` · `tenants` `/api/admin/tenants` (+ public `/api/tenants`) · `feature_flags` `/api/admin/feature-flags` · `service_accounts` `/api/admin/service-accounts` · `backup` `/api/admin/backups` · `jobs` `/api/admin/jobs` · `operations` `/api/admin/operations` · `local_users`.

### Аутентификация и идентичность (5)
`auth` `/api/auth` · `identity` `/api/admin/identity` (+ phase1) · `ldap` `/api/admin/ldap` · `i18n` `/api/i18n` + `/api/admin/i18n`.

### Академическое ядро (20)
`admissions` `/api/admin/admissions` · `admissions_crm` `/api/admin/admissions-crm` · `students` `/api/admin/students` · `faculty` `/api/admin/org/faculty` · `programs` `/api/admin/org/programs` · `courses` `/api/admin/org/courses` · `enrollments` `/api/admin/enrollments` · `academic_records` `/api/admin/university/records` · `grades` `/api/admin/grades` · `transcripts` `/api/admin/transcripts` · `degree_progress` `/api/admin/degree-progress` · `thesis` `/api/admin/thesis` · `academic_integrity` `/api/admin/academic-integrity` · `teaching_quality` `/api/admin/teaching-quality` · `advising` `/api/admin/advising` · `scheduling` `/api/admin/scheduling` · `exam_governance` `/api/admin/exam-governance` · `org_structure` `/api/admin/org-units` · `profiles` `/api/admin/profiles` · `workflows` `/api/admin/workflows`.

### Успех студента и интервенции (11)
`student_lifecycle` `/api/admin/student-lifecycle` · `interventions` (cases/playbooks/risk/effectiveness) `/api/admin/interventions/*` · `student_services` `/api/admin/student-services/tickets` · `student_services_support` `/api/admin/student-services` · `student_life` `/api/admin/student-life` · `career_services` `/api/admin/career-services` · `financial_aid` `/api/admin/financial-aid` · `scholarship` `/api/admin/scholarship`.

### Финансы и операции (12)
`budget_planning` · `expense_controls` · `delinquency_collections` · `hr_payroll` · `hr_staff_governance` · `finance_procurement_asset` · `procurement` · `billing` (опционально) · `asset_inventory` · `facilities_work_orders` · `operations` · `currency_localization` (префиксы `/api/admin/<kebab>`).

### Кампус и инфраструктура (10)
`campus_facilities_housing_transport` · `campus_sla` · `housing` · `dining` · `transport` · `room_booking` · `equipment_booking` · `visitor_management` · `access_control` · `security_operations`.

### Исследования и качество (10)
`research` · `research_ethics` · `research_science` · `quality_accreditation` · `accreditation` (`/api/admin/accreditation-compliance`) · `innovation_commercialization` · `syllabus_governance` · `pdpl` · `analytics` `/api/analytics` · `expansion_visibility` `/api/admin/expansion/l4`.

### Brain и AI (8)
`brain_core` `/api/admin/brain` · `ai_gateway` `/api/admin/ai` (+ public) · `faculty_copilot` · `knowledge_retrieval` · `prompt_management` · `model_evaluation` · `digital_twin` `/api/admin/digital-twin` · `security_access_compliance`.

### Runtime Shells (13)
`academic_operations` (shell) + под‑runtime (registry, curriculum, timetable, attendance, assessment, teaching-load, internship, signals, dashboard) `/api/admin/academic-operations/*`; `student_success_runtime` `/api/admin/student-success` (или `/api/v1/student-success`); `research_science` (shell); `quality_accreditation` (shell). См. [06_RUNTIME_SHELLS.md](06_RUNTIME_SHELLS.md).

### Governance и контроль (6)
`executive_control_tower` · `executive_governance` (runtime) · `rector_assignment_workflow` `/api/admin/rector-assignments` · `communications` · `notification_center` · `events_management`.

### Интеграции и внешние (11)
`integrations` · `provider_readiness` `/api/admin/provider-readiness/l4` · `integration_provider_readiness` · `document_workflow_os` `/api/admin/documents` · `document_decree_correspondence` · `alumni` · `human_approved_timetable_workflow` · `timetable_change_proposal` · `timetable_approval_queue` · `timetable_change_kpi_dashboard` · `workload_management`.

### Платформенные API (8, `app/platform/`)
| Роутер | Префикс | Назначение | Auth |
|--------|---------|-----------|------|
| `router_admin` | `/api/v1/admin` | Платформенные админ‑операции (tenants, flags, kpi, jobs, webhooks, analytics) | JWT + RBAC |
| `router_public` | `/api/v1/public` | Зарезервировано (нет endpoint'ов) | — |
| `router_internal` | `/api/v1/internal` | Внутренние (workers, jobs, events, webhooks, rehydration) | Bearer scopes |
| `router_mcp` | `/api/v1/internal/mcp` | Интроспекция БД для AI copilot (redaction PII) | Bearer |
| `router_ops` | `/api/v1/platform/ops` (+ BFF `/api/bff/...`) | Ops‑дашборд (health, backlog, latency, backup) | JWT + Ops |
| `router_developer_api` | `/api/dev` | Партнёрские интеграции (analytics, kpi, students/grades) | X‑App‑Key/Secret |
| `router_semantic` | `/api/v2/semantic` | Семантический слой (entities, metrics, dimensions, queries) | JWT + Semantic |

### Прочие (5)
`reporting_runtime` (через admin) · `help` `/api/help` · `platform` `/platform` + self‑service · `analytics`.

---

## 6.3 Пример полного контракта endpoint (Admissions)

Модуль `admissions`, роутер `prefix="/api/admin/admissions"`, tag `admissions`:

| Метод | Путь | Назначение | Permission (типовой) |
|-------|------|-----------|----------------------|
| POST | `/api/admin/admissions/applicants` | Создать абитуриента | `admissions.write` |
| GET | `/api/admin/admissions/applicants` | Список абитуриентов | `admissions.read` |
| GET | `/api/admin/admissions/applicants/{id}` | Карточка абитуриента | `admissions.read` |
| PUT | `/api/admin/admissions/applicants/{id}` | Обновить (optimistic version) | `admissions.write` |
| POST | `/api/admin/admissions/applications` | Создать заявление | `admissions.write` |
| POST | `/api/admin/admissions/applications/{id}/submit` | Подать (→ событие `admissions.application.submitted`) | `admissions.write` |
| POST | `/api/admin/admissions/applications/{id}/stage` | Смена этапа (append‑only history) | `admissions.write` |
| POST | `/api/admin/admissions/applications/{id}/documents` | Прикрепить документ (safe key) | `admissions.write` |
| POST | `/api/admin/admissions/applications/{id}/decision` | Решение accept/reject/waitlist | `admissions.write` |
| GET | `/api/admin/admissions/consistency-report` | Отчёт согласованности | `admissions.read` |

Request/Response — Pydantic‑схемы (`ApplicantCreateSchema`, `ApplicationReadSchema`, `DecisionMakeRequestSchema`, …). Ошибки: 400/403/404/409 через `_map_service_error`.

> Полные контракты по каждому модулю не воспроизведены поштучно (685+ endpoint'ов). Для конкретного модуля endpoint'ы перечислены в его файле [modules/](modules/) и в [api/README.md](api/README.md). Живой контракт доступен через OpenAPI (`/docs`, `/openapi.json`) запущенного backend.

---

## 6.4 Brain API (пример системного роутера)

`brain_core/router.py`, prefix `/api/admin/brain`, guard `admin.dashboard.read`:
`GET /health`, `/tenants/{id}/signals`, `/tenants/{id}/decisions`, `/decisions/{id}`, `/explanations/{id}`, `/dispatch/snapshot`, `/policy/{tenant}` (GET/PUT), `/recommendations/{tenant}`, `/executive-kpi/{tenant}`; симуляции `POST /simulate/*`, `/predict`, `/anomalies`. Детали — [brains/brain-core.md](brains/brain-core.md).

---

## 6.5 Проблемы API (аудит)

- **Несогласованность префиксов:** часть путей с историческими алиасами (`/api/admin/org/faculty`, `/api/admin/university/records`, `research-grants→research`, `accreditation-compliance→accreditation`) — мэппинг в `_extract_admin_module_from_path`.
- **Дублирующиеся поверхности** для семейств‑дубликатов модулей (academic_operations vs runtime и т.п.).
- `router_public` (`/api/v1/public`) — зарезервирован, пуст.
- Полный список 685+ endpoint'ов в статике не перечислялся поштучно — источник истины — OpenAPI работающего сервиса.
