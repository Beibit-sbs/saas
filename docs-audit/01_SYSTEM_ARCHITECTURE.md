# 01 — Архитектура системы (System Architecture)

[← 00 Обзор](00_PROJECT_OVERVIEW.md) · [Индекс](README.md) · Далее: [02 Карта зависимостей →](02_MODULE_DEPENDENCY_MAP.md)

---

## 2.1 Технологический стек

| Слой | Технологии |
|------|-----------|
| **Backend** | FastAPI, Python 3.12, SQLAlchemy 2 (DeclarativeBase), Alembic, psycopg v3, Pydantic |
| **Frontend** | Next.js 14.2.35 (App Router), React 18.3.1, TypeScript 5.9, TanStack React Query 5, React Hook Form + Zod, Tailwind CSS 3.4, Radix UI, lucide‑react |
| **База данных** | PostgreSQL (JSONB, частично RLS), tenant‑scoped таблицы |
| **Кэш/состояние** | Redis (revocation токенов, кэш), in‑memory fallback |
| **Инфраструктура** | Docker Compose, Nginx (edge), pgAdmin (dev profile) |
| **Тестирование** | pytest (backend), Vitest + Testing Library (frontend unit), Playwright (e2e) |
| **Аутентификация** | JWT (HttpOnly cookie) + CSRF, LDAP/AD, OIDC, SAML, 2FA (TOTP) |

---

## 2.2 Высокоуровневая архитектура (слои)

```text
        ┌─────────────────────────────────────────────┐
        │  Frontend (Next.js App Router)               │
        │  /console (admin), /student /faculty         │
        │  /registrar /profile /login                  │
        └───────────────┬─────────────────────────────┘
                        │ HTTPS (JWT cookie + CSRF)
                        ▼
        ┌─────────────────────────────────────────────┐
        │  Nginx edge  →  FastAPI (app/main.py)        │
        │  151 роутер, middleware (tenant, audit, rate │
        │  limit, observability, brain activity signal)│
        └───────────────┬─────────────────────────────┘
                        ▼
   ┌──────────────┬───────────────┬────────────────────┐
   │ Domain       │ Platform      │ Brain Core          │
   │ Modules      │ (events, jobs,│ (decision engine)   │
   │ (~241)       │ kpi, tenant,  │                     │
   │              │ billing, uow) │                     │
   └──────┬───────┴──────┬────────┴─────────┬───────────┘
          │              │                  │
          ▼              ▼                  ▼
   Domain CRUD    Outbox events        Signals/Decisions
   (EntityConfig  → Webhooks/          → Actions (workflow/
    + ORM)         Notifications        notification/job)
          │              │                  │
          └──────────────┴──────────────────┘
                        ▼
              PostgreSQL (tenant‑scoped)
```

Концептуальный поток (из `SBS_UB_BRAIN_CORE_ARCHITECTURE.md`):
`Domain Modules → Events/Signals → Brain Core → Decisions → Workflow/Automation/Notifications/Jobs → Execution → Outcome → Learning/Policy Refinement`.

Полная карта модулей — [02_MODULE_DEPENDENCY_MAP.md](02_MODULE_DEPENDENCY_MAP.md).

---

## 2.3 Frontend‑архитектура

- **Next.js App Router** (`frontend/app/`). ~**380** файлов `page.tsx`.
- **Route‑группы:** `(admin)` (консоль, ~370 страниц под `/console/*`), `(auth)` (только layout), плюс ролевые зоны `/student`, `/faculty`, `/registrar`, `/profile`, `/login`, корень `/`.
- **middleware.ts** — аутентификация и маршрутизация: проверка истечения JWT (`exp`), чтение cookie `app_access_token`/`admin_token`, редирект `/admin → /console/platform`, редирект авторизованного `/login → /console`, gate на `/console|/student|/faculty|/registrar|/profile`, иначе `→ /login?next=…`.
- **Модульная структура** (`frontend/modules/*`, ~81 модуль): типичный модуль = `api.ts` (клиент + типы), `pages.tsx`/`page.tsx`, `components/`, `hooks.ts`, `types.ts`, `constants.ts`, иногда `guards.ts`, `boundaryLabels.ts`.
- **Shared UI** (`frontend/shared/ui/`, ~30 компонентов): `app-sidebar`, `app-topbar`, `page-header`, `data-table`, `filter-bar`, `metric-card`, `permission-gate`, `require-admin-role`, `toast`/`toaster`, диалоги и т.д. Дизайн‑система на Radix UI + Tailwind + CVA.
- **Состояние сервера:** React Query (кэш/синхронизация). **Формы:** React Hook Form + Zod. **i18n:** реестр языков (`kk`, `ru`, `en` — защищённые системные).
- **Runtime Shells** (7–8 фронтовых): специализированные операционные дашборды, тянут данные `getRuntimeShell()` (см. [06_RUNTIME_SHELLS.md](06_RUNTIME_SHELLS.md)).

Детали: [pages/README.md](pages/README.md).

---

## 2.4 Backend‑архитектура

- **Точка входа:** `backend/app/main.py` — регистрирует **151 роутер** (143 модульных + 8 платформенных), настраивает middleware, lifespan (OTel, валидация окружения, runtime‑schema bootstrap).
- **Модульный монолит:** каждый модуль (`backend/app/modules/<name>/`) по канону содержит:
  `router.py` (API), `service.py` (бизнес‑логика), `schemas.py` (Pydantic DTO), `models.py` (SQLAlchemy ORM), `repository.py` (DAL), `business_rules.py`, `dependencies.py`, `permissions.py`.
  Фактическое покрытие: `service.py` ~225, `schemas.py` ~91, `router.py` 151, `models.py` 36, `permissions.py` 19, `repository.py` 14 (большинство сервисов обращаются к БД напрямую через raw‑conn/UoW, а не через отдельный repository).
- **Ядро (`app/core/`):** `config.py`, `db.py` (engine, пул 5+10, `pool_pre_ping`, psycopg), `tenant.py` (fail‑closed резолвинг тенанта), `runtime_schema.py` (bootstrap таблиц), `errors.py`, `module_helpers/`.
- **Платформенный слой (`app/platform/`):** events, jobs, kpi, tenant, billing, notifications, webhooks, idempotency, uow, feature_flags, federation, semantic, developer, automation, context, event_ingestion, а также платформенные роутеры `router_admin/public/internal/mcp/ops/developer_api/semantic`.
- **Brain Core (`app/modules/brain_core/`):** движок решений (см. [07_BRAIN_MODULES.md](07_BRAIN_MODULES.md)).

Детали API: [05_API.md](05_API.md).

---

## 2.5 Архитектура базы данных

Гибридная стратегия создания схемы:

1. **Alembic** (`backend/alembic/versions/`, ~**96** миграций) — версионируемая эволюция схемы.
2. **Runtime‑schema bootstrap** (`app/core/runtime_schema.py`) — создание fallback‑таблиц из реестра при старте, если миграция ещё не применена (`CREATE TABLE IF NOT EXISTS`).

- **Центральный реестр сущностей:** `app/modules/university_core/shared.py` — **211** объявлений `EntityConfig` (dataclass: `table`, `fields`, `required`, `fk_fields`). Отделён от ORM: используется для валидации и fallback‑создания таблиц.
- **ORM‑слой:** 36 модулей с `models.py` (SQLAlchemy). `BigInteger` для `id`/`tenant_id`, `JSONB` для метаданных, `DateTime(timezone=True)`, FK с каскадами, `UniqueConstraint`/`CheckConstraint`.
- **Всего таблиц:** ~250+ (211 EntityConfig + ORM‑специфичные платформенные/audit/jobs/billing и т.д.).
- `TEST_ONLY_DB_TABLES` = {`admissions_scorings`, `scan_requests`, `tutor_sessions`} — только для тестов.

Полный аудит БД: [04_DATABASE.md](04_DATABASE.md), каталог таблиц: [database/README.md](database/README.md).

---

## 2.6 Event‑архитектура

- **Реестр событий:** `app/platform/events/registry.py` — гибрид: `EXACT_EVENT_REGISTRY` (**232** точных типа) + `PREFIX_EVENT_REGISTRY` (префиксные матчеры, напр. `automation.*`, `campus.*`). Валидация payload (Pydantic), обязательный `tenant_id > 0`.
- **Publishing (Outbox pattern):** `OutboxEventModel` + `EventPublisher` → запись в `outbox` через `UnitOfWork`. Поля: `event_type`, `aggregate_type/id`, `payload_json`, `status` (pending/processing/delivered/failed), `retry_count`, `correlation_id`, `causation_id`.
- **Consumption:** `app/platform/events/worker.py` (`outbox_worker.run_once`) → `WebhookDispatcher` (платформенные + developer‑app подписки, retry) и `app/platform/event_ingestion/` (аналитика, fire‑and‑forget).
- **Brain‑интеграция:** middleware в `main.py` эмитит `platform.module.activity.logged` в Brain Core на admin‑запросах; `brain_core/signal_listener.py` подписан на доменные события.

Детали: [09_INTEGRATIONS.md](09_INTEGRATIONS.md), [11_BACKGROUND_JOBS.md](11_BACKGROUND_JOBS.md).

---

## 2.7 Integration‑архитектура

- **10 интеграционных модулей** по паттерну «country‑adapter» (KZ live, планы SA/AE/QA/OM/BH/KW), все на уровне **L2 contract‑ready** (флаги `no_provider_call`, `no_credential_use`, `no_live_integration_claim`): finance_erp, hr_payroll, payment_gateway, sso_saml, identity_provider, LMS, SIS, government_services, regulatory_reporting, notification_gateway.
- **Gateway‑модули:** email_gateway_integration, mobile_push_gateway, notification_center, integrations (управление провайдерами).
- **Developer API / Webhooks:** `router_developer_api` (`/api/dev`, ключи `X‑App‑Key/Secret`), подписки на события через webhooks.
- **MCP:** `router_mcp` (`/api/v1/internal/mcp`) — интроспекция БД для AI‑copilot (redaction PII).

Полный список: [09_INTEGRATIONS.md](09_INTEGRATIONS.md).

---

## 2.8 Tenant‑архитектура (мультитенантность)

- **Строгий fail‑closed:** тенант резолвится **только** из claim‑ов аутентифицированного токена (`app/core/tenant.py`). Заголовок `X‑Tenant‑ID` — вторичная сверка; cross‑tenant override — только для `superadmin`.
- **Коды:** 401 (нет/невалидна аутентификация), 403 (невалидный tenant в токене / запрещён cross‑tenant), 404 (тенант не найден), 400 (невалидный `X‑Tenant‑ID`).
- **Изоляция на уровне БД:** колонка `tenant_id` (BigInteger FK → `app_tenants.id`, часто `ON DELETE CASCADE`), композитные unique‑констрейнты, частично PostgreSQL RLS (напр. AI Gateway).
- **Платформенный тенант:** `tenant_id = 1` (платформенные операции).
- **Настройки тенанта:** `app_platform_tenant_settings` (JSONB `settings/quotas/limits`, `status`). Контекст тенанта кэшируется и ежедневно перестраивается (`context_rebuild` job).

---

## 2.9 Platform‑архитектура

- **Unit of Work** (`app/platform/uow.py`): контекст‑менеджер транзакции + ~21 репозиторий (tenant, billing, usage, invoice, job, notification, idempotency, analytics, ai_copilot, automation, developer, education_graph, federation, kpi, outbox_event, platform_event, webhook, context …). Fallback на in‑memory при недоступности БД.
- **Idempotency** (`app/platform/idempotency/`): ключ + операция + SHA‑256 хэш запроса → защита от повторов.
- **KPI** (`app/platform/kpi/`): реестр 150+ метрик, `TenantMetricSnapshotModel`/`TenantDashboardSnapshotModel`, lineage событие→метрика (`EVENT_DERIVED_METRIC_LINEAGE`), ежедневный `refresh_all_tenants`.
- **Jobs** (`app/platform/jobs/scheduler.py`): кастомный `PlatformWorkerScheduler` (не Celery/не APScheduler), 9 периодических задач.
- **Billing/Plans/Quotas/Subscriptions/Usage**, **Feature Flags** (DB‑backed + кэш, детерминированный rollout по SHA‑256).

---

## 2.10 Безопасность

- **AuthN:** JWT в HttpOnly‑cookie + CSRF‑cookie для cookie‑мутаций; методы: local (PBKDF2‑SHA256, 200K итераций), LDAP/AD, OIDC, SAML 2.0, 2FA (TOTP). Сессии в PostgreSQL, revocation в Redis (+ memory fallback).
- **AuthZ:** **RBAC** (permissions вида `module.resource.action`) + **ABAC** (tenant, ownership, department, sensitivity). Обе проверки требуются для чувствительных ресурсов.
- **Tenant‑изоляция:** fail‑closed (см. 2.8).
- **Rate limiting:** `app/modules/security/rate_limit.py` (IP + actor, backoff, аудит).
- **Аудит:** `app/modules/audit/` — `app_audit_events`, политика хранения (до 7 лет), экспорт JSON/CSV, correlation_id.
- **Observability:** JSON‑логирование, OpenTelemetry, метрики, perf‑profiling, health‑эндпоинты (live/ready/deep/comprehensive).
- **Демо‑доступ:** `/api/auth/demo-users`, `/api/auth/demo-login` — только для шаблона/демо, требуют отключения перед продакшеном (`README.md`).

Полный аудит RBAC/ABAC: [03_ROLES_AND_RBAC.md](03_ROLES_AND_RBAC.md).

---

## 2.11 Dependency graph (сводно)

```text
Page (frontend/app/**/page.tsx)
  → frontend/modules/<m>/api.ts (fetch)
    → FastAPI router (/api/...)  [permission_dependency]
      → service.py (бизнес-логика, business_rules.py)
        → repository / UoW / raw psycopg
          → PostgreSQL (tenant-scoped table; EntityConfig/ORM)
      → publish_event (Outbox)  → Brain Core signal_listener
                                   → context → classify → reason
                                   → policy guard (human approval)
                                   → action (workflow/notification/job)
                                   → outcome → learning
      → KPI metric refresh (event → metric lineage)
Runtime Shell page → getRuntimeShell() → runtime_shell_router → aggregated read
```

Детальная карта: [02_MODULE_DEPENDENCY_MAP.md](02_MODULE_DEPENDENCY_MAP.md).
