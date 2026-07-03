# 02 — Полная карта системы и карта зависимостей (Module Dependency Map)

[← 01 Архитектура](01_SYSTEM_ARCHITECTURE.md) · [Индекс](README.md) · Далее: [03 Роли и RBAC →](03_ROLES_AND_RBAC.md)

---

## 3.1 Центральные (ядровые) модули

Эти модули — «хабы», от которых зависит большинство остальных:

| Модуль | Роль в системе | От него зависят |
|--------|----------------|-----------------|
| **`university_core`** | Центральный реестр сущностей (`EntityConfig`, 211 сущностей), tenant‑entity API, readiness‑summary | Практически все доменные модули (данные хранятся по этому реестру) |
| **`rbac`** | RBAC + ABAC, `permission_dependency`, `get_actor`, резолвинг прав по тенанту | Все роутеры (каждый endpoint защищён permission) |
| **`tenants` / `core/tenant`** | Мультитенантность, `get_current_tenant`, fail‑closed | Все доменные модули |
| **`brain_core`** | Движок решений; принимает сигналы всех доменов | Все модули, публикующие события/сигналы |
| **`platform/*`** | Events, jobs, kpi, uow, notifications, webhooks, billing, feature_flags | Все модули (инфраструктура) |
| **`auth` / `identity` / `ldap` / `sso_saml`** | Аутентификация, токены, сессии | Все защищённые запросы |
| **`audit`** | Централизованный аудит‑лог | Все мутации |
| **`observability`** | Логи, метрики, health, трейсинг | Все запросы (middleware) |

---

## 3.2 Группировка модулей по продуктовым вертикалям

Система организована в ~20–25 продуктовых вертикалей (V01–V25 по `SBS_UB_AUTHORITATIVE_SYSTEM_EVIDENCE_INVENTORY.md`). Многие backend‑модули «сворачиваются» в вертикаль.

| Вертикаль | Ключевые backend‑модули | Статус (по инвентарю) |
|-----------|-------------------------|-----------------------|
| V01 Executive Governance | `executive_governance`, `executive_control_tower` | CLOSED_WITH_EVIDENCE |
| V02 Student Lifecycle | `student_lifecycle`, `students` | CLOSED_WITH_EVIDENCE |
| V03 Academic Operations | `academic_operations` (+ `academic_operations_runtime`) | CLOSED (есть dup‑пара) |
| V04 Research / Science | `research_science` (+ `research`, `research_projects`, `research_ethics`, `research_grants`) | CLOSED |
| V05 Quality / Accreditation | `quality_accreditation` (+ `accreditation`×3) | CLOSED (dup‑семейство) |
| V06 HR / Staff Governance | `hr_staff_governance` (+ `hr_payroll`×2) | CLOSED (dup‑семейство) |
| V07 Finance / Procurement / Asset | `finance_procurement_asset` | RUNTIME_VERIFIED |
| V08 Document / Decree / Correspondence | `document_decree_correspondence`, `document_workflow_os` | CLOSED |
| V09 Student Services / Welfare | `student_services_support` (+ `student_services`) | RUNTIME_VERIFIED |
| V10 Security / Access / Compliance | `security_access_compliance` | CLOSED |
| V11 Campus / Facilities / Housing / Transport | `campus_facilities_housing_transport` | CLOSED |
| V12 Admissions / Recruitment / Yield | `admissions_crm` (+ `admissions`) | **BLOCKED_CODE** (не закоммичен) |
| V13 Integration / Provider Readiness | `integration_provider_readiness`, `provider_readiness` | PARTIAL_RUNTIME |
| V14 Library / Archive / Knowledge | `library`, `library_circulation`, `knowledge_retrieval` | PARTIAL_RUNTIME |
| V15 Communications / Notification / Community | `communications`, `notification_center`, `mobile_push_gateway` | ACTIVE_RUNTIME |
| V16 Data Platform / Analytics / KPI | `analytics`, `reporting_runtime` | PARTIAL_RUNTIME |
| V17 AI Brain Core | `brain_core` | RUNTIME_VERIFIED (наибольшее покрытие тестами) |
| V18 Infrastructure / Ops / SRE | `observability`, `platform_health`, `backup` | PARTIAL_RUNTIME |
| V19–V25 | `alumni`, `lms_*`, `exam_*`, `contracts_legal_*`, `ministry_*`, medical, integrity | SPEC_COMPLETE / PARTIAL |
| (ext) Innovation / Commercialization | `innovation_commercialization` | **DEPRECATED/UNTRACKED** (не закоммичен) |

Полный каталог всех модулей: [modules/README.md](modules/README.md).

---

## 3.3 Данные, передаваемые между модулями

- **Через события (Outbox → Brain/Webhooks/KPI):** доменные модули публикуют события (`student.created`, `finance.payment_overdue.detected`, `procurement.approval_required`, …). Полезная нагрузка = tenant‑scoped JSON с `aggregate_type/id`, `correlation_id`.
- **Через Brain Core (сигналы → решения):** нормализованные сигналы преобразуются в решения; действия возвращаются доменам как workflow‑задачи/уведомления/jobs.
- **Через EntityConfig‑реестр:** общие сущности (студенты, факультет, программы, курсы) читаются несколькими модулями по единому реестру `university_core`.
- **Через KPI‑lineage:** события питают метрики (`EVENT_DERIVED_METRIC_LINEAGE`), которые агрегируются в дашборды (Rector/Executive).
- **Через «мосты» (bridges):** явные пермишены‑мосты между вертикалями (напр. `campus_facilities.*_bridge`, `finance_asset_bridge`, `hr_staff_bridge`, `student_lifecycle`↔`document_workflow`).

---

## 3.4 Центральные vs зависимые (граф связей, сводно)

```text
                         ┌───────────────┐
                         │ university_core│  (реестр сущностей)
                         └───────┬───────┘
        ┌───────────────┬────────┼────────┬────────────────┐
        ▼               ▼        ▼        ▼                ▼
   Academic Ops    Student    Finance   Campus          Research
   (courses,       Lifecycle  Proc.     Facilities      Science
    scheduling,    / Success  Asset     Housing Transp.
    grades…)          │         │         │                │
        └──────┬──────┴────┬────┴────┬────┴────────┬───────┘
               ▼           ▼         ▼             ▼
            events  ───────────────────────────────►  Brain Core
               │                                         │
               ▼                                         ▼
             KPI  ◄──────────── outcome/learning ─── Decisions → Actions
               │                                         │
               ▼                                         ▼
        Executive Governance / Rector Dashboards    Workflows / Notifications / Jobs
               │
               ▼
        Ministry / Regulatory Reporting (reporting_runtime)
```

---

## 3.5 Полная цепочка зависимости (как требует ТЗ, раздел 12)

```text
Модуль
  ↓
API (router.py, /api/...)               [permission_dependency: RBAC+ABAC]
  ↓
Service (service.py, business_rules.py)
  ↓
Repository / UoW / raw psycopg
  ↓
Database (PostgreSQL, tenant-scoped; EntityConfig + ORM)
  ↓
Runtime Shell (агрегирующий read-эндпоинт → фронтовый shell)
  ↓
Brain (signal → decision → action, human-gated)
  ↓
Integration (outbox → webhooks / внешние адаптеры / очереди уведомлений)
```

Эта цепочка воспроизводится для каждого модуля; конкретика — в файлах [modules/](modules/).

---

## 3.6 Известные структурные проблемы карты (из инвентаря)

- **Дубликаты/семейства модулей:** `academic_operations` vs `academic_operations_runtime`; `quality_accreditation` vs `accreditation`×3; `hr_staff_governance` vs `hr_payroll`×2; `student_services_support` vs `student_services`; семейство research (`research`, `research_projects`, `research_science`). Требуют консолидации.
- **Незакоммиченный код:** `admissions_crm` (V12) и `innovation_commercialization` — на диске, но не в git → риск целостности (P1 по инвентарю).
- **Разрыв покрытия тестами:** Communications (V15) — 0 выделенных тестов на момент инвентаря.
