# 04 — Полный аудит базы данных

[← 03 Роли и RBAC](03_ROLES_AND_RBAC.md) · [Индекс](README.md) · Далее: [05 API →](05_API.md)

Источники: `app/modules/university_core/shared.py`, `app/modules/*/models.py`, `backend/alembic/versions/`, `app/core/db.py`, `app/core/runtime_schema.py`, `app/core/tenant.py`. Каталог таблиц по доменам: [database/README.md](database/README.md).

---

## 5.1 Стратегия схемы (двойная)

1. **Alembic** (`backend/alembic/versions/`, ~**96** миграций) — версионируемая эволюция.
2. **Runtime‑schema bootstrap** (`app/core/runtime_schema.py`) — при старте создаёт fallback‑таблицы из реестра (`CREATE TABLE IF NOT EXISTS`), если миграция не применена. Вызывает `ensure_*` функции модулей (platform_core, session, preferences, audit, integrations, usage, i18n, ai_gateway, billing, plans, quotas, jobs, rbac).

---

## 5.2 Центральный реестр сущностей — `EntityConfig`

Файл: `app/modules/university_core/shared.py`.

```python
@dataclass(frozen=True)
class EntityConfig:
    table: str                    # имя таблицы в PostgreSQL
    fields: tuple[str, ...]       # все колонки
    required: tuple[str, ...]     # NOT NULL (подмножество fields)
    fk_fields: tuple[str, ...] = ()  # внешние ключи
```

- **Всего: 211** объявлений `EntityConfig` в `ENTITY_CONFIGS: dict[str, EntityConfig]`.
- Каждая сущность tenant‑scoped (`tenant_id` в `fields`).
- Отделён от ORM: используется для валидации и fallback‑создания таблиц.
- Вспомогательные структуры: `REQUIRED_DB_TABLES` (обязательные в проде), `ALLOWED_FALLBACK_TABLES` (= все минус required), `TEST_ONLY_DB_TABLES` = {`admissions_scorings`, `scan_requests`, `tutor_sessions`}.

---

## 5.3 Домены сущностей (сводно)

Полный поимённый список — [database/README.md](database/README.md). Основные группы:

| Домен | Примеры таблиц |
|-------|----------------|
| University Core | `university_students`, `university_faculty`, `university_faculty_contracts`, `university_programs`, `university_courses` |
| Academic Lifecycle | `university_enrollments`, `university_academic_records`, `university_advising_sessions` |
| Student Services | `university_student_service_tickets`, `university_career_*`, `university_financial_aid_*`, `university_housing_requests` |
| Alumni | `university_alumni_records`, `university_alumni_engagement_events` |
| Research / IP | `university_research_grants`, `university_research_publications`, `university_research_labs`, `ip_assets`, `patents` |
| Faculty / HR | `university_faculty_performance_kpis`, `university_hr_employees`, `university_hr_payroll_cycles`, `university_personnel_orders`, `hr_contracts` |
| Finance / Collections | `university_delinquency_records`, `finance_expense_*` |
| Facilities / Ops / Procurement | `university_facilities_work_orders`, `university_asset_inventory_items`, `university_operations_*`, `university_procurement_*` |
| Student Life / Counseling / Disciplinary | `university_student_life_*`, `counseling_cases`, `crisis_reports` |
| Library | `library_items`, `library_loans`, `library_reservations`, `library_fines`, `library_overdue_records` |
| Attendance / LMS | `attendance_records`, `attendance_sessions`, `lms_courses`, `lms_lessons`, `lms_grades` |
| Online Payments | `payment_orders`, `payment_transactions`, `payment_refunds`, `payment_failure_alerts` |
| Campus (events/rooms/visitor/parking) | `campus_events`, `campus_rooms`, `room_bookings`, `visit_requests`, `access_cards`, `parking_permits` |
| Publications / Conferences | `publications`, `citations`, `conferences`, `conference_papers` |
| AI / Tutoring | `tutor_sessions`, `scan_requests`, `model_eval_runs`, `prompt_templates` |
| Security / Incidents | `security_incidents`, `security_visitors` |
| Transport / Dining | `transport_routes`, `dining_menus`, `dining_orders` |
| Accreditation / Thesis / Exams / Syllabi | `accreditation_records`, `thesis_records`, `exams`, `syllabi`, `syllabus_approval_workflows` |
| Auth / Security | `twofa_enrollments`, `saml_identity_providers`, `saml_sessions` |
| Brain Core | `brain_core_signal_definitions`, `brain_core_signals`, decisions/explanations (см. [brains/](brains/)) |

Заметная особенность: обилие **alert/risk‑таблиц** (`*_alerts`, `*_risk_alerts`) — материализация раннего предупреждения (~40 таблиц).

---

## 5.4 ORM‑слой (SQLAlchemy)

36 модулей содержат `models.py`. Примеры:

| Модуль | Таблицы |
|--------|---------|
| `workflows` | `app_workflow_definitions`, `*_versions`, `*_triggers`, `*_steps`, `*_assignees`, `*_execution_histories` |
| `billing` | `app_billing_plans`, `app_billing_tenant_subscriptions`, `app_billing_usage_counters`, `app_billing_invoices` |
| `admissions` | `ApplicantModel`, `ApplicationModel`, `ApplicationDocumentModel`, `ApplicationStageHistoryModel`, `ApplicationDecisionModel` |
| `enrollments` | `app_enrollments_terms` (+ enum `EnrollmentStatus`, `EnrollmentType`) |
| `transcripts` | `app_transcripts`, `app_transcript_items` |
| `audit` | `app_audit_events` |
| `tenants` | `app_tenants` |
| `brain_core` | `brain_core_signal_definitions`, `brain_core_signals`, … |
| `courses` | `university_courses`, `university_course_prerequisites` |

Конвенции: `BigInteger` id/tenant_id; `JSONB` метаданные; `DateTime(timezone=True)`; FK с каскадами; `UniqueConstraint`/`CheckConstraint`.

---

## 5.5 Enum и справочники (найденные)

| Enum | Значения |
|------|----------|
| `EnrollmentStatus` | PENDING, ENROLLED, WAITLIST, DROPPED, COMPLETED, WITHDRAWN, SUSPENDED |
| `EnrollmentType` | REGULAR, AUDIT, RETAKE, TRANSFER_CREDIT |
| `WorkflowDefinitionStatus` | DRAFT, ACTIVE, ARCHIVED |
| `WorkflowDefinitionVersionStatus` | DRAFT, ACTIVE, RETIRED |
| `WorkflowTriggerMode` | MANUAL, EVENT, API |
| `WorkflowStepType` | START, TASK, APPROVAL, END, GATEWAY |
| `WorkflowAssigneeType` | USER, ROLE, GROUP, SERVICE_ACCOUNT |
| `BillingSubscriptionStatus` | TRIAL, ACTIVE, SUSPENDED, CANCELLED |
| Обобщённый `status` | active, inactive, archived, draft, completed (в 180+ сущностях, часто CHECK‑constraint) |
| Alert‑статусы | pending, acknowledged, resolved, critical |
| Уровни риска | low, medium, high, critical |

> Полный перечень enum не исчерпан — часть встроена в `models.py` конкретных модулей.

---

## 5.6 Мультитенантность на уровне БД

- Колонка `tenant_id` (BigInteger FK → `app_tenants.id`, часто `ON DELETE CASCADE`) в ~95% таблиц.
- Композитные unique‑констрейнты включают `tenant_id` (изоляция).
- Частично PostgreSQL **RLS** (напр., миграция `enable_rls_for_ai_gateway_tenant_tables`).
- Резолвинг тенанта — fail‑closed из токена (`app/core/tenant.py`).
- Таблица настроек тенанта: `app_platform_tenant_settings` (JSONB `settings/quotas/limits`, `status`).

---

## 5.7 Конфигурация подключения

`app/core/db.py`: engine с пулом `pool_size=5`, `max_overflow=10`, `pool_pre_ping=True`, `pool_timeout=30`, драйвер `postgresql+psycopg`, `prepare_threshold=None` (совместимость с PgBouncer). Raw‑доступ через `get_raw_conn()` (rollback перед возвратом в пул).

---

## 5.8 Миграции (Alembic) — обзор цепочки

~96 файлов. Фазы (по префиксам/темам):
- **Foundation:** initial_schema, students phase1, workflow engine phase1.
- **Platform core / multi‑tenancy:** platform_core tables, tenant isolation, fail‑closed platform‑wide.
- **Домены:** enrollments (phase2/3), grades, transcripts+degree_progress, faculty contracts, profiles/departments/org_units.
- **Специализированные:** scheduling, admissions, document_workflow_os.
- **Advanced:** interventions (cases, risk, effectiveness), platform KPI engine, brain_core (+ extended, signal dedup).
- **AI/Flags/RBAC:** ai_gateway v1, feature flags rollout %, rbac persistence + tenant scope, audit tenant scope.
- **Billing/Plans/Quotas/Jobs**, **Auth/Identity** (sessions, MFA, SAML, idempotency).
- **University extensions:** accreditation+thesis, syllabus+exam governance, quality_accreditation.
- **Batch entity additions (A‑серия):** `add_university_core_tables` (~100+ таблиц), alert‑таблицы, критический backfill.
- **Недавние модули:** research_science, academic_operations, admissions_crm, student_services_support, campus_facilities_housing_transport, security_access_compliance, integration_provider_readiness, rector_assignment, student_lifecycle.
- **Политики хранения:** audit retention (7 лет).

---

## 5.9 Проблемы БД (аудит)

- **EntityConfig vs ORM рассинхрон:** часть сущностей реестра не имеет ORM‑модели (fallback‑only).
- **Двойной путь схемы** (Alembic + runtime bootstrap) может давать минимальные схемы, если миграция не применена.
- **RLS частичный** — полный RLS‑аудит не проводился; большинство изоляций — на уровне приложения.
- **Дубликаты таблиц** между семействами модулей (см. [02_MODULE_DEPENDENCY_MAP.md](02_MODULE_DEPENDENCY_MAP.md) §3.6).
- Точные определения колонок edge‑case таблиц не верифицированы в этом read‑only аудите.
