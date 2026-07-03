# Модуль: Admissions (Приём) + Admissions CRM

[← Каталог модулей](README.md) · [Индекс](../README.md)

Backend: `backend/app/modules/admissions/`, `backend/app/modules/admissions_crm/`, `backend/app/modules/ai_admissions_scoring/`
Frontend: `frontend/modules/admissions-crm/`
Продуктовая вертикаль: **V12 Admissions / Recruitment / Yield**
Дизайн‑документы: `backend/modules/admissions/ADMISSIONS_MODULE_DESIGN.md`, `backend/ADMISSIONS_WORKFLOW_*.md`

---

## Назначение
Приём абитуриентов: ведение заявлений, движение по этапам приёмного workflow, приём документов, скоринг и принятие решения (accept/reject/waitlist). `admissions_crm` добавляет воронку/лиды/кампании.

## Бизнес‑функции
- Регистрация абитуриентов и заявлений (один абитуриент — одна заявка на программу в год).
- Движение заявления по этапам с неизменяемой историей (append‑only stage history).
- Прикрепление документов (безопасные ключи, не пути к файлам).
- AI‑скоринг заявлений (`ai_admissions_scoring`).
- Финальное решение с версионированием (optimistic concurrency).
- Отчёт согласованности данных приёма.
- CRM: лиды, воронка, кампании (`admissions_crm`).

## Пользователи (роли)
`student_lifecycle_admin` / admissions‑admin, `registrar`, `admin`; `auditor` (read‑only). ABAC — по тенанту.

## Основной функционал
CRUD абитуриентов/заявлений · submit · смена этапа · документы · решение · consistency‑report · CRM‑лиды.

## Страницы / Маршруты
- `/console/admissions/*` (~11: applications, applicants, leads, workflows, dashboard, audit, settings).
- `/console/admissions-crm`.
- **Dashboard:** admissions dashboard (воронка, конверсия).
- **Runtime Shell:** отдельного нет; данные приёма участвуют в student‑lifecycle дереве.

## Backend
- **Controllers (router):** `admissions/router.py` (prefix `/api/admin/admissions`, tag `admissions`); `admissions_crm/router.py` (`/api/admin/admissions-crm`).
- **Services:** `ApplicantService`, `ApplicationService`, `DecisionService`, `DocumentService`, `StageTransitionService`.
- **Repository:** доступ через `dependencies.get_admissions_db` (SQLAlchemy Session).
- **Models (ORM):** `ApplicantModel`, `ApplicationModel`, `ApplicationDocumentModel`, `ApplicationStageHistoryModel`, `ApplicationDecisionModel`; `admissions_crm/models.py` (`admissions_crm_*`).
- **DTO (schemas):** `ApplicantCreate/Read/Update/ListResponse`, `ApplicationCreate/Read/ListResponse`, `ApplicationSubmitRequest`, `StageTransitionRequest/Response`, `DocumentAttachRequest`, `DocumentRead`, `DecisionMakeRequest`, `ApplicationDecisionRead`, `AdmissionsConsistencyReport`, `ApplicationStage`.

## Database
- **Таблицы:** `ApplicantModel` (uniq: `tenant_id,email,program_id,application_year`), `ApplicationModel` (workflow state), `ApplicationDocumentModel`, `ApplicationStageHistoryModel` (append‑only), `ApplicationDecisionModel`; `admissions_scorings` (**test‑only**); `admissions_crm_*`.
- **Связи:** applicant 1:N application; application 1:N document; application 1:N stage_history; application 1:1 decision. Все FK на `app_tenants` (BigInteger, `ON DELETE CASCADE`).
- **Индексы:** `tenant_id`; композитные `(tenant_id,email)`, `(tenant_id,program_id,application_year)`.
- **Enum/справочники:** `ApplicationStage`; статусы решения (accept/reject/waitlist).
- **Аудит‑поля:** `created_at/updated_at/verified_at/decided_at`, `created_by/verified_by/decided_by_id/actor_id`, `metadata_json` (JSONB).

## API
Префикс `/api/admin/admissions`. Endpoints (методы/permissions) — см. [../05_API.md](../05_API.md) §6.3. Ключевые: POST applicants, GET applicants(+`{id}`), PUT applicant, POST applications, POST `.../submit`, POST `.../stage`, POST `.../documents`, POST `.../decision`, GET consistency‑report. Ошибки: 400/403/404/409.

## Permissions
`admissions.read`, `admissions.write`; CRM — свои permissions в `admissions_crm/permissions.py`. Проверка `permission_dependency` + `get_actor` + `get_current_tenant`.

## Связанные модули
`student_lifecycle` (переход абитуриент→студент), `programs`/`courses` (целевая программа), `enrollments` (зачисление после accept), `ai_admissions_scoring`, `brain_core` (decision `enrollment_dropout_risk`, сигналы `admissions.*`), `document_workflow` (документы), `notification_center`.

## Workflow
См. [../08_WORKFLOWS.md](../08_WORKFLOWS.md) §9.1: applicant → application → stages → documents → scoring → decision. События: `admissions.application.{submitted,stage_changed,decision_made,workflow_decision_finalized}`.

## Runtime Shell
Нет выделенного; вклад в student‑lifecycle (A‑055).

## Brain
Сигналы `admissions.{score_generated,anomaly_detected}`, `admissions.application.*`. Decision‑сценарий `enrollment_dropout_risk` (Brain Core). Human‑gated.

## AI
`ai_admissions_scoring` — скоринг заявлений (сервис‑only). Событие `admissions.score_generated`, `admissions.anomaly_detected`.

## Интеграции
Внутренние: события в Brain/KPI. Внешние: потенциально SIS (`student_information_system_integration`, L2). Уведомления через notification_center.

## Background Jobs
Прямых cron нет; участвует в `composite_early_warning_sweep` косвенно (через lifecycle). KPI‑refresh агрегирует admissions‑метрики.

## Feature Flags
Возможен флаг `early_warning_auto_intervention` (модуль admissions) — см. [../10_FEATURE_FLAGS.md](../10_FEATURE_FLAGS.md).

## Проблемы / Рекомендации
- **`admissions_crm` не закоммичен в git** (P1, риск целостности) — реконсилировать или удалить.
- `admissions_scorings` — только тестовая таблица (исключена из прод‑bootstrap).
- Возможное дублирование ответственности `admissions` vs `admissions_crm` — уточнить границы.
- **Рекомендация:** зафиксировать код в git, консолидировать CRM/скоринг, добавить E2E для полного цикла accept→enroll.
