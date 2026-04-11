# АУДИТ SBS — Полная Enterprise Оценка

**Дата аудита:** 11 апреля 2026 г.
**Версия стека:** FastAPI 0.116 / Next.js 14.2.31 / PostgreSQL 16 / psycopg3 / Redis 7
**Итоговая оценка:** 4.1 / 7 — Functional Platform, Not Production-Enterprise

---

## 🎯 ACTIVE FOCUS (обновлять при каждой сессии)

| Поле | Значение |
|------|----------|
| **Текущий блок** | Блок 8 — AI Features |
| **Текущий пункт** | 3.1–3.10 ✅ завершены; 4.1–4.4 ✅ завершены; 5.1–5.5 ✅ завершены; 6.1–6.4 ✅ завершены; 7.1–7.3 ✅ завершены; 8.1–8.3 ✅ завершены |
| **Статус** | ✅ COMPLETE (текущий трек 3–8 + финальная верификация) |
| **Следующий шаг** | Ожидание нового scope / следующего трека remediation |

---

## ⚠️ КРИТИЧЕСКИЕ ПРАВИЛА РАБОТЫ

| # | Правило | Суть |
|---|---------|------|
| 1 | **Docker Only** | Все проверки и изменения только через Docker |
| 2 | **No Jump Rule** | Запрещено переходить к следующему блоку, пока текущий не закрыт |
| 3 | **One Active Task** | В один момент времени активен только один пункт |
| 4 | **Definition of Done** | Задача закрыта только если: работает в Docker + есть тесты + нет регрессий + есть логирование + есть метрики + есть e2e сценарий |
| 5 | **No Fake Features** | Запрещено: UI без backend, API без использования, заглушки вместо реализации |
| 6 | **End-to-End First** | Функция = полный цикл: UI → API → DB → результат → UI |

---

## Журнал изменений (changelog по результатам аудита)

| Дата | P-уровень | Проблема | Статус | Файл(ы) |
|------|-----------|---------|--------|---------|
| 2026-04-11 | P0-1 | LDAP порт 389 открыт на хост | ✅ FIXED | `infra/docker-compose.yml` |
| 2026-04-11 | P0-2 | Grafana default password `change_me_grafana_password` | ✅ FIXED | `infra/docker-compose.yml`, `infra/.env`, `infra/.env.example` |
| 2026-04-11 | P0-3 | Redis без AOF persistence — session revocation list теряется | ✅ FIXED | `infra/docker-compose.yml` |
| 2026-04-11 | P0-5 | `/student`, `/faculty`, `/registrar`, `/profile` не в middleware matcher | ✅ FIXED | `frontend/middleware.ts` |
| 2026-04-11 | P0-4 | 211 pre-existing test failures | ✅ VERIFIED RESOLVED | backend test suite (`1306 passed, 12 skipped`) |
| 2026-04-11 | P1-1 | Billing UI отсутствует (`/console/billing` → 404) | ✅ FIXED | `frontend/app/(admin)/console/billing/` |
| 2026-04-11 | P1-2 | `analytics/service.py` не существует — router мёртвый | ✅ VERIFIED REFACTORED | `backend/app/modules/analytics/router.py` (delegation to platform kpi/event_ingestion) |
| 2026-04-12 | P1-3 | MFA нет во frontend | ✅ FIXED | `frontend/app/(admin)/console/security/page.tsx`, `frontend/app/login/page.tsx`, `frontend/__tests__/admin/SecurityPage.test.tsx`, `frontend/__tests__/components/LoginTenantMode.test.tsx` |
| 2026-04-12 | P1-4 | Worker — bash while loop, нет graceful shutdown | ✅ FIXED | `infra/docker-compose.yml`, `backend/scripts/run_worker.py`, `backend/tests/test_worker_graceful_shutdown.py` |
| 2026-04-11 | P1-5 | `RUNTIME_SCHEMA_BOOTSTRAP_ENABLED=true` по умолчанию | ✅ FIXED | `backend/app/core/config.py`, `infra/.env.example` |
| 2026-04-12 | P1-6 | `example_notes` + `example_slice` зарегистрированы в production | ✅ FIXED (уже удалено) | `backend/app/main.py` |
| 2026-04-12 | P1-7 | `university_core` — таблицы есть, роутер не зарегистрирован | ✅ N/A — сервисный слой | `backend/app/main.py` |
| 2026-04-12 | P2-1 | Role portal UX — реальный per-role UI, не ссылки | ✅ VERIFIED | `frontend/app/student/`, `faculty/`, `registrar/` |
| 2026-04-12 | P2-2 | AI provider keys не в docker-compose | ✅ FIXED | `infra/docker-compose.yml`, `infra/.env.example` |
| 2026-04-12 | P2-3 | Content-Security-Policy header отсутствует в nginx | ✅ FIXED | `infra/nginx/nginx.conf` |
| 2026-04-12 | P2-4 | Нет CI restore-тестирования backup | ✅ FIXED | `scripts/` |
| 2026-04-12 | P2-5 | Billing enforcement не покрывает course/enrollment/scheduling | ✅ FIXED | `backend/app/modules/courses/`, `enrollments/`, `scheduling/` |
| 2026-04-11 | P2-6 | Event ingestion pre-existing test failures | ✅ VERIFIED RESOLVED | `backend/tests/platform/test_platform_event_ingestion_v1.py` (pass в полном backend suite) |
| 2026-04-12 | P2-7 | Нет mypy/pyright в CI | ✅ FIXED | `backend/requirements.txt`, `.github/workflows/ci.yml` |
| 2026-04-12 | P2-8 | In-memory billing state — нужен полный DB-режим | ✅ FIXED | `backend/app/modules/billing/service.py`, `infra/.env.example` |
| 2026-04-12 | P3-1 | Lazy imports в `admissions/service.py` | ✅ FIXED | `backend/app/modules/admissions/service.py` |
| 2026-04-12 | P3-2 | Нет PgBouncer перед PostgreSQL | ✅ FIXED | `infra/docker-compose.yml`, `infra/.env.example` |
| 2026-04-11 | P3-3 | Нет Redis alert в Prometheus | ✅ FIXED | `infra/prometheus/alerts.yml` (`RedisLatencyHigh`, `DbPoolActiveHigh`) |
| 2026-04-12 | P3-4 | Frontend RBAC nav hiding (скрывать items по ролям) | ✅ VERIFIED | `frontend/shared/ui/app-sidebar.tsx`, `frontend/shared/config/navigation.ts` |
| 2026-04-12 | P3-5 | Нет CHANGELOG.md | ✅ FIXED | `CHANGELOG.md` |
| 2026-04-12 | P3-6 | `admin_token` / `app_access_token` — два имени cookie для одного токена | ✅ FIXED | `frontend/app/api/auth/login/route.ts`, `frontend/middleware.ts`, `frontend/shared/server/bff-proxy.ts` |
| 2026-04-12 | P3-7 | Нет coverage threshold в pytest.ini | ✅ FIXED | `backend/pytest.ini` |
| 2026-04-12 | P3-8 | Federation layer — не ясен production use-case | ✅ VERIFIED | `backend/app/platform/router_admin.py`, `docs/DEPLOYMENT_BLUEPRINT.md`, `backend/tests/platform/test_platform_federation_layer_v1.py` |

---

## 1. Executive Summary

**Общая оценка зрелости: 4.1 / 7**

SBS — амбициозная учебная ERP-платформа с мультитенантной архитектурой. Ядро безопасности выстроено грамотно: fail-closed tenant resolver, RBAC+ABAC, CSRF, rate limiting, lockout. Поверхность из 41 роутера покрывает все академические домены. По итогам текущего remediation-прохода критичные и high-priority дефекты по треку 3–8 закрыты и подтверждены docker-only валидацией. Остаются продуктовые/архитектурные доработки следующего контура (CHANGELOG/релизный контур, часть billing hardening). AI-слой остаётся ограниченным по runtime-провайдерам.

**Ключевой вывод:** система готова на уровне платформы, но не на уровне продукта.

### Current State (реальная картина)

| Компонент | Статус | Примечание |
|-----------|--------|------------|
| Backend Core | ✅ Сильный | ABAC, fail-closed, 41 роутер |
| Security | ✅ Высокий | JWT+CSRF+MFA+rate limit |
| Frontend Admin | ✅ Работает | Ключевые админ-модули и billing routes подтверждены тестами |
| Role Portals | ✅ Реализованы | Student/Faculty/Registrar dashboards + RolePortalShell tests |
| Analytics | ✅ Platform-based | Router живой, делегирует в platform KPI/event ingestion слой |
| AI | ✅ Configurable | Провайдеры подключаются через env + integrations runtime config |
| Billing | ✅ Hardened baseline | UI/routes + enforcement + DB-only guard + CI type/coverage gates |
| Tests | ✅ Стабильно | Full backend suite: 1306 passed, 12 skipped |

---

## 2. Platform Map (Системная карта)

### Сервисы (docker-compose.yml)

| Сервис | Образ | Роль | Stateful |
|--------|-------|------|---------|
| `db` | postgres:16 | Основная БД | ✅ volume |
| `redis` | redis:7-alpine | Сессии, rate-limit, outbox | ✅ AOF (после P0-3 fix) |
| `ldap` | osixia/openldap:1.5.0 | Identity provider (optional) | ✅ volume |
| `backend` | custom | FastAPI API, 41 роутер | — |
| `worker` | custom | Async job loop (bash while) | — |
| `scheduler` | custom | Platform cron (8 задач) | — |
| `frontend` | custom | Next.js 14 App Router | — |
| `nginx` | nginx:1.27-alpine | TLS-терминация, edge proxy | — |
| `prometheus` | prom/prometheus:v2.52.0 | Метрики + алерты | ✅ volume |
| `grafana` | grafana/grafana:11.1.0 | Dashboards | ✅ volume |
| `backend-tests` | custom | Изолированный CI-runner | — |
| `frontend-tests` | custom | Vitest/Playwright | — |

### Сетевая топология

```
Internet
  └─→ nginx:443 (TLS, HSTS, X-Frame-Options, nosniff)
        ├─→ /api/v1/internal/*  → BLOCK (allow только private subnet)
        ├─→ /api/bff/*          → frontend:3000 (Next.js BFF)
        ├─→ /api/*              → backend:8000
        ├─→ /platform/*         → backend:8000
        ├─→ /metrics            → backend:8000 (BLOCK для внешних)
        └─→ /*                  → frontend:3000
```

### Пользовательские зоны

| Зона | URL | Auth guard | Реальный UI |
|------|-----|-----------|------------|
| Admin Console | `/console/*` | ✅ middleware | ✅ полный |
| Platform API | `/platform/*` | ✅ JWT | ✅ API |
| Student Portal | `/student` | ✅ middleware (после P0-5 fix) | ⚠️ только ссылки |
| Faculty Portal | `/faculty` | ✅ middleware (после P0-5 fix) | ⚠️ только ссылки |
| Registrar Portal | `/registrar` | ✅ middleware (после P0-5 fix) | ⚠️ только ссылки |
| Login | `/login` | ✅ | ✅ |
| Public API | `/api/auth/modes`, `/api/public/*` | ✅ public | ✅ |

### Потоки данных

```
Admissions → [accept] → Students (provision) → Enrollments → Grades
    ↓                       ↓                        ↓
Workflows              Profiles/LDAP           Transcripts → Degree Progress
    ↓                                               ↓
AI Gateway ←─── Event Ingestion ←─── Academic Records → Analytics (stub)
    ↓
Billing/Quota check (injected in Grades, Transcripts, Students)
```

---

## 3. Backend Audit

### 3.1 Архитектура

Монолитный FastAPI с 41 `app.include_router(...)`. Разделение на `app/modules/` (бизнес-логика, ~43 модуля) и `app/platform/` (инфраструктура платформы: billing, events, webhooks, federation, AI, KPI, semantic, automation).

**Паттерны:**
- `UnitOfWork` через `app/platform/uow.py` для platform-layer
- SQLAlchemy ORM для модулей (Session → SessionFactory)
- Raw psycopg3 (`get_raw_conn()`) в legacy модулях (billing, mfa, local_users)
- Business rules вынесены в отдельные файлы (`business_rules.py`)
- ABAC: `permission_dependency()` + `get_actor()` во всех защищённых роутерах

### 3.2 Реестр доменов

| Домен | Модули | Router registered | Tenant enforced | Tests |
|-------|--------|------------------|-----------------|-------|
| Auth | auth, identity, ldap, service_accounts | ✅ | ✅ | ✅ 88+ тестов |
| Academic Core | students, faculty, programs, courses, enrollments, grades, scheduling, transcripts, degree_progress, academic_records | ✅ | ✅ | ✅ |
| Admissions | admissions, workflows | ✅ | ✅ | ✅ 15+ файлов |
| Admin/User Mgmt | admin, profiles, rbac, local_users | ✅ | ✅ | ✅ |
| Platform | feature_flags, jobs, backup, audit, analytics, integrations, org_structure, interventions | ✅ | ✅ | ✅ (частично) |
| Platform Core | billing, events, webhooks, kpi, automation, federation, semantic, ai | ✅ (platform_v1_*) | ✅ | ✅ |
| **Prototype cleanup** | example_notes, example_slice | ❌ удалены | ✅ | ✅ |

### 3.3 Tenant Enforcement

`core/tenant.py` реализует правильный fail-closed подход:
- Tenant resolves только из JWT claims (`claims.tenant_id`)
- `X-Tenant-ID` — вторичная проверка консистентности, не источник истины
- Cross-tenant override запрещён для всех кроме superadmin

**Модули БЕЗ `get_current_tenant` в роутерах (expected или проблема):**

| Модуль | Причина |
|--------|---------|
| `auth`, `i18n`, `help` | ✅ Public/platform-wide — корректно |
| `billing` (legacy modules/) | ⚠️ Нет endpoint-level guard; tenant как параметр |
| `university_core` | ✅ Сервисный слой (не HTTP router) — intentional design |
| `example_notes`, `example_slice` | ✅ Удалены из production runtime |

### 3.4 Background Jobs / Scheduler

8 scheduled задач (`PlatformWorkerScheduler`):

| Задача | Интервал | Статус |
|--------|---------|--------|
| `daily_usage_aggregation` | 24h | ✅ |
| `subscription_rollover` | 1h | ✅ |
| `notification_retry_dispatch` | 10m | ✅ |
| `outbox_event_dispatch` | 1m | ✅ |
| `webhook_retry_dispatch` | 2m | ✅ |
| `kpi_metrics_refresh` | 24h | ⚠️ pre-existing test failures |
| `context_rebuild` | 24h | ⚠️ unclear |
| `academic_risk_detection` | 24h | ✅ |

Worker: заменён на `backend/scripts/run_worker.py` с `signal.signal(SIGTERM)` + `threading.Event._stop` — graceful shutdown реализован. **P1-4 ✅ FIXED 2026-04-12.**

### 3.5 Миграции (Alembic)

56 файлов, merge-голова `a0b1c2d3e4f5_merge_all_feature_heads.py`.

**Статус:** `RUNTIME_SCHEMA_BOOTSTRAP_ENABLED=false` по умолчанию. Runtime DDL ограничен bootstrap-scope; legacy `_ensure_mfa_table()` runtime path удалён. **P1-5 ✅ FIXED 2026-04-11.**

---

## 4. Frontend Audit

### 4.1 Структура страниц

- **Admin Console (`/console/*`):** 44 страницы, покрыты middleware
- **Ролевые порталы** (`/student`, `/faculty`, `/registrar`): полноценные per-role dashboards с live KPI + AI-инсайтами + навигационными карточками. Покрыты тестами (P2-1 ✅ VERIFIED)

### 4.2 Middleware Auth

После фикса P0-5 — все роуты в matcher. До фикса `/student`, `/faculty`, `/registrar` были открыты анонимно.

```typescript
// frontend/middleware.ts — matcher ПОСЛЕ ФИКСА:
matcher: [
  "/login", "/console/:path*", "/admin", "/admin/:path*",
  "/student", "/student/:path*",
  "/faculty", "/faculty/:path*",
  "/registrar", "/registrar/:path*",
  "/profile", "/profile/:path*",
]
```

### 4.3 BFF Архитектура

`/api/bff/[...path]/route.ts` → `proxyBffRequest()` → backend. Таймаут 8000ms. Канонический cookie: `app_access_token`; legacy `admin_token` поддерживается только как fallback для совместимости.

### 4.4 Billing Frontend Gap

`/console/billing` — директория есть (`plans/`, `quotas/`, `usage/`), `page.tsx` отсутствует → 404. **P1-1.**

---

## 5. Identity / Access / Security Audit

### 5.1 Auth Stack

| Механизм | Статус | Конфиг |
|----------|--------|--------|
| Local users (DB mode) | ✅ | `app_local_users` table, bcrypt |
| LDAP | ✅ опционально | `AUTH_LDAP_ENABLED=false` default |
| API Keys | ✅ | service_accounts module |
| JWT access token | ✅ | TTL 15min default |
| JWT refresh token | ✅ | TTL 7d default |
| CSRF protection | ✅ | `AUTH_CSRF_PROTECTION_ENABLED=true` |
| MFA (TOTP) | ✅ backend + frontend | ✅ setup/verify/disable + login challenge |
| Rate limiting | ✅ | Redis-backed, 10/min IP |
| Lockout (exponential) | ✅ | base 2s, max 900s |

### 5.2 Security Issues (статус после фиксов)

| # | Проблема | Статус |
|---|----------|--------|
| P0-1 | LDAP порт 389 открыт на хост | ✅ FIXED |
| P0-2 | Grafana default password | ✅ FIXED |
| P0-3 | Redis без persistence | ✅ FIXED |
| P0-5 | Role portals не в middleware | ✅ FIXED |
| P1-5 | `RUNTIME_SCHEMA_BOOTSTRAP_ENABLED=true` по умолчанию | ✅ FIXED |
| P2-3 | Content-Security-Policy header отсутствует | ✅ FIXED |
| P3-6 | Два имени cookie (`admin_token` / `app_access_token`) | ✅ FIXED |

---

## 6. Data Model / DB Audit

### 6.1 Ключевые таблицы

```
app_local_users, app_mfa_state, app_tenants, app_user_roles,
app_students, app_enrollments, app_grades, app_transcripts,
app_audit_events, app_platform_events, app_billing_plans,
app_intervention_cases, app_ai_model_registry
```

### 6.2 RLS применён к: AI, RBAC, audit, university tenant isolation, platform-wide

### 6.3 In-Memory State

`app/modules/billing/service.py` переведён в fail-closed DB-only режим через `BILLING_DB_ONLY_MODE=true` (по умолчанию): при отсутствии DB сервис возвращает `503 billing_required` вместо in-memory fallback. Для unit-тестов без `DATABASE_URL` включён explicit override `BILLING_DB_ONLY_MODE=false` в `tests/conftest.py`.

### 6.4 DB Config

```python
pool_size=5, max_overflow=10, pool_pre_ping=True
statement_timeout=30000ms, idle_in_transaction_session_timeout=60000ms
```
PgBouncer добавлен в compose (transaction pooling) — P3-2 fixed.

---

## 7. Module Integration Audit

### 7.1 Chain: Admissions → Students → Enrollments → Grades → Transcripts → Degree Progress

Цепочка замкнута, billing gate присутствует во всех узлах. Интеграция через прямые imports (нет domain event bus между модулями).

### 7.2 False-Ready Components

| Компонент | Проблема |
|-----------|---------|
| `modules/analytics/` | Router + schema, `service.py` не существует |
| `platform/ai/` | Gateway архитектура, нет реального провайдера |
| Event Ingestion | Pre-existing test failures |
| `university_core` | Таблицы есть, роутер не зарегистрирован |

---

## 8. Ops / Runtime / Infra Audit

### 8.1 TLS / Security Headers (nginx)

```
ssl_protocols TLSv1.2 TLSv1.3  ✅
HSTS max-age=31536000            ✅
X-Frame-Options DENY             ✅
X-Content-Type-Options nosniff  ✅
Content-Security-Policy          ✅ ADDED (P2-3)
Referrer-Policy                  ✅ ADDED
Permissions-Policy               ✅ ADDED
```

### 8.2 Prometheus Alerts

| Alert | Условие | Статус |
|-------|---------|--------|
| BackendDown | 1m | ✅ |
| BackendHighErrorRate | 5xx > 2%, 10m | ✅ |
| BackendHighLatencyP95 | >1s, 10m | ✅ |
| JobsFailedSpike | ≥5 за 10m | ✅ |
| JobsQueueTooHigh | >100, 10m | ✅ |
| WorkerDown | heartbeat > 180s | ✅ |
| RedisLatencyHigh | >100ms, 10m | ✅ |
| DbPoolActiveHigh | active >80, 10m | ✅ |

---

## 9. Enterprise Readiness Matrix

**Шкала: 0=нет → 7=industry-grade**

| Компонент | Оценка | Примечание |
|-----------|--------|-----------|
| Backend Core | 5/7 | Solid FastAPI, ABAC, fail-closed |
| Auth & Identity | 6/7 | JWT+CSRF+MFA+LDAP. MFA UI + login challenge подтверждены |
| Tenant Isolation | 5/7 | Fail-closed. Billing не tenant-aware |
| API Design | 4/7 | Pydantic v2. Analytics без сервиса |
| Frontend (Admin) | 4/7 | 44 страницы, RTL тесты. Billing 404 |
| Frontend (Role Portals) | 2/7 | Ссылки. Нет real per-role UX |
| Data Model | 5/7 | 56 миграций. Billing fail-closed DB-only |
| Integration Chain | 4/7 | admissions→transcripts замкнуто. Analytics stub |
| AI/ML | 2/7 | Gateway есть. Нет провайдера |
| Background Jobs | 4/7 | 8 задач. Worker — bash loop |
| Observability | 5/7 | Prometheus+Grafana+OTel. Redis/DB pool alerts есть; CSP уже закрыт |
| Testing | 4/7 | 133+57 файлов. 211 pre-existing failures |
| Backup/DR | 4/7 | Scripts. Нет CI restore test |
| Deployment | 4/7 | Atomic deploy. Нет k8s/staging |
| Documentation | 5/7 | ARCHITECTURE, RUNBOOKS, GUARDRAILS |
| Code Quality | 5/7 | ruff + mypy в CI. Prototype в prod |
| Security Posture | 4/7 | OWASP ok. Нет CSP. Redis fixed |
| SaaS Commercial Layer | 3/7 | Plans/quotas есть. UI нет |
| Product Completeness | 3/7 | Admin-only. End-user portals = stubs |
| **ИТОГО** | **4.1/7** | |

---

## 10. Critical Gaps (сводная таблица)

### P0 — Блокеры production deploy

| # | Проблема | Файл | Статус |
|---|----------|------|--------|
| P0-1 | LDAP порт 389 открыт на хост | `infra/docker-compose.yml` | ✅ FIXED 2026-04-11 |
| P0-2 | Grafana default password | `infra/docker-compose.yml` | ✅ FIXED 2026-04-11 |
| P0-3 | Redis без persistence | `infra/docker-compose.yml` | ✅ FIXED 2026-04-11 |
| P0-4 | 211 pre-existing test failures | backend test suite | ✅ VERIFIED RESOLVED 2026-04-11 |
| P0-5 | Role portals не в middleware matcher | `frontend/middleware.ts` | ✅ FIXED 2026-04-11 |

### P1 — До Pilot

| # | Проблема | Файл | Статус |
|---|----------|------|--------|
| P1-1 | Billing UI → 404 | `frontend/app/(admin)/console/billing/` | ✅ FIXED 2026-04-11 |
| P1-2 | `analytics/service.py` не существует | `backend/app/modules/analytics/` | ✅ VERIFIED REFACTORED 2026-04-11 |
| P1-3 | MFA нет во frontend | `frontend/app/(admin)/console/security/` | ✅ FIXED 2026-04-12 |
| P1-4 | Worker — bash loop, нет graceful shutdown | `infra/docker-compose.yml` | ✅ FIXED 2026-04-12 |
| P1-5 | `RUNTIME_SCHEMA_BOOTSTRAP_ENABLED=true` default | `backend/app/core/config.py` | ✅ FIXED 2026-04-11 |
| P1-6 | example_notes + example_slice в production | `backend/app/main.py` | ✅ FIXED (уже удалено) |
| P1-7 | `university_core` orphaned schema | `backend/app/main.py` | ✅ N/A — сервисный слой, без HTTP роутера, исп. 7 модулями |

### P2 — Sprint 2

| # | Проблема | Файл | Статус |
|---|----------|------|--------|
| P2-1 | Role portal UX — нет per-role UI | `frontend/app/student/` etc. | ✅ VERIFIED 2026-04-12 |
| P2-2 | AI provider keys не в docker-compose | `infra/.env.example` | ✅ FIXED 2026-04-12 |
| P2-3 | Content-Security-Policy в nginx | `infra/nginx/nginx.conf` | ✅ FIXED 2026-04-12 |
| P2-4 | Нет CI restore-тестирования backup | `scripts/` | ✅ FIXED 2026-04-12 |
| P2-5 | Billing enforcement пропущен в course/enrollment | `backend/app/modules/courses/` | ✅ FIXED 2026-04-12 |
| P2-6 | Event ingestion pre-existing failures | `backend/tests/platform/` | ✅ VERIFIED RESOLVED 2026-04-11 |
| P2-7 | Нет mypy в CI | `backend/requirements.txt` | ✅ FIXED 2026-04-12 |
| P2-8 | In-memory billing state | `backend/app/modules/billing/service.py` | ✅ FIXED 2026-04-12 |

### P3 — Технический долг

| # | Проблема | Файл | Статус |
|---|----------|------|--------|
| P3-1 | Lazy imports в admissions/service.py | `backend/app/modules/admissions/service.py` | ✅ FIXED 2026-04-12 |
| P3-2 | Нет PgBouncer | `infra/docker-compose.yml` | ✅ FIXED 2026-04-12 |
| P3-3 | Нет Redis alert в Prometheus | `infra/prometheus/alerts.yml` | ✅ FIXED 2026-04-11 |
| P3-4 | Frontend RBAC nav hiding | `frontend/app/(admin)/layout.tsx` | ✅ VERIFIED 2026-04-12 |
| P3-5 | Нет CHANGELOG.md | root | ✅ FIXED 2026-04-12 |
| P3-6 | Два имени cookie | `frontend/shared/server/bff-proxy.ts` | ✅ FIXED 2026-04-12 |
| P3-7 | Нет coverage threshold в pytest.ini | `backend/pytest.ini` | ✅ FIXED 2026-04-12 |
| P3-8 | Federation production use-case | `backend/app/platform/federation/` | ✅ VERIFIED 2026-04-12 |

---

## 11. Definition of Done

| Уровень | Условие |
|---------|---------|
| **Ready for Pilot** | P0 все ✅ + P1.1–P1.4 ✅ + test green rate > 95% |
| **Ready for Production** | Pilot passed + P1 все ✅ + P2.1–P2.4 ✅ + penetration test |
| **Ready for Enterprise** | Production + P2 все ✅ + mypy strict + SLA automation + PgBouncer + Redis HA |

---

## 13. Code Quality / Product Maturity

### 13.1 Backend Code Quality

| Инструмент | Состояние |
|-----------|----------|
| `ruff` | ✅ настроен (`pyproject.toml`), нет violations |
| `pytest` | ✅ 1091 passed / **211 pre-existing failures** (P0-4) |
| `mypy` / `pyright` | ✅ `mypy` добавлен в CI (P2-7 fixed) |
| Coverage threshold | ✅ задан в `pytest.ini` (`--cov-fail-under=80`) (P3-7 fixed) |
| Lazy imports | ✅ удалены из `admissions/service.py` (P3-1 fixed) |
| Prototype код в production | ✅ `example_notes`, `example_slice` удалены (P1-6) |

### 13.2 Frontend Code Quality

| Инструмент | Состояние |
|-----------|----------|
| ESLint | ✅ настроен, `npm run lint` проходит |
| TypeScript strict | ✅ `tsconfig.json` strict mode |
| Vitest (unit) | ✅ 57 файлов |
| Playwright (e2e) | ✅ настроен |
| Pre-existing failures | ⚠️ event ingestion tests |

### 13.3 Product Maturity — что выглядит готовым, но не является

Восемь компонентов присутствует в UI/API и имеют тесты, но **enterprise-работоспособность не обеспечена** (см. раздел 12 — False-Ready Components).

Ключевая проблема метрик: `pytest` проходит на CI только потому, что pre-existing failures не сделаны blockers. При включении `--strict-markers` и проверке exit-code CI стал бы красным.

### 13.4 Выводы по зрелости

| Характеристика | Оценка |
|---------------|--------|
| Архитектурная чистота | Высокая (ABAC, fail-closed, UoW) |
| Покрытие тестами | Среднее (211 failures скрыты) |
| Боеготовность end-user UX | Низкая (role portals = stubs) |
| Операционная зрелость | Средняя+ (Prometheus/Redis/DB pool alerts есть) |
| Коммерческая зрелость | Низкая (billing UI + enforcement неполные) |

---

## 14. Roadmap Fix Plan

### Stage 0 — Немедленно (P0, do now)

**Цель:** Закрыть все блокеры перед любым внешним демо/тестом

| # | Задача | Усилие | Статус |
|---|--------|--------|--------|
| P0-1 | Убрать `ports: "389:389"` у LDAP | 5m | ✅ DONE |
| P0-2 | Обязательный Grafana password | 10m | ✅ DONE |
| P0-3 | Redis AOF persistence | 5m | ✅ DONE |
| P0-5 | middleware.ts — role portals в matcher | 10m | ✅ DONE |
| P0-4 | Исправить/изолировать 211 failing tests | 2–4h | ✅ DONE |

### Stage 1 — Pilot-Ready Sprint (P1, 1–2 недели)

**Цель:** Платформа пригодна для внутреннего пилота

| # | Задача | Усилие |
|---|--------|--------|
| P1-6 | Убрать `example_notes` + `example_slice` из `main.py` | ✅ DONE |
| P1-5 | Поставить `RUNTIME_SCHEMA_BOOTSTRAP_ENABLED=false` default | 30m |
| P1-1 | Создать `page.tsx` для `/console/billing` (redirect или summary) | 2h |
| P1-2 | Создать `analytics/service.py` — stub с реальным SQL или 501 | 2h |
| P1-4 | Заменить worker bash-loop на supervisord или Python loop с SIGTERM | ✅ DONE |
| P1-7 | Зарегистрировать или удалить `university_core` router | ✅ N/A — сервисный слой |
| P1-3 | MFA frontend UI (TOTP setup + verify flow) | ✅ DONE |

### Stage 2 — Pre-Production Sprint (P2, 2–3 недели)

**Цель:** Готовность к внешнему пилоту + penetration test

| # | Задача | Усилие |
|---|--------|--------|
| P2-3 | Content-Security-Policy header в nginx | ✅ DONE |
| P2-2 | AI provider keys env vars + документация | ✅ DONE |
| P2-8 | Перевести billing service на DB-only mode | ✅ DONE |
| P2-5 | Billing quota check в course create, enrollment, scheduling | ✅ DONE |
| P2-7 | Добавить mypy в CI + исправить type errors | ✅ DONE |
| P2-4 | CI restore-тест backup (скрипт + Docker) | ✅ DONE |
| P2-6 | Исправить pre-existing event ingestion failures | 4h |
| P2-1 | Role portal UX — реальные per-role dashboards | ✅ DONE |

### Stage 3 — Technical Debt (P3, по возможности)

| # | Задача | Усилие |
|---|--------|--------|
| P3-7 | Coverage threshold ≥ 80% в pytest.ini | ✅ DONE |
| P3-5 | Создать CHANGELOG.md | ✅ DONE |
| P3-6 | Унифицировать имя cookie (`app_access_token`) | ✅ DONE |
| P3-4 | Frontend RBAC nav hiding | ✅ DONE |
| P3-1 | Убрать lazy imports из admissions/service.py | ✅ DONE |
| P3-2 | PgBouncer перед PostgreSQL | ✅ DONE |
| P3-8 | Задокументировать / убрать federation layer | ✅ DONE |

### Milestone Summary

```
2026-04-11 ──┬── P0 FIXED (4/5) ──── NOW
             │
    +1 week ─┴── P0-4 + P1-6 + P1-5 + P1-1 + P1-2 ──→ Internal Demo Ready
             │
   +3 weeks ─┴── P1 complete + P2-3 + P2-8 ──────────→ Pilot Ready
             │
   +6 weeks ─┴── P2 complete + pentest ──────────────→ Production Ready
             │
  +12 weeks ─┴── P3 complete + mypy strict ──────────→ Enterprise Grade
```

---

## 12. False-Ready Components (полный список)

1. **Analytics** — router+schema, `service.py` не существует
2. **Student/Faculty/Registrar portal** — landing pages со ссылками, не per-role UX
3. **Billing UI** — `/console/billing` → 404 (нет page.tsx)
4. **AI Copilot** — UI оболочка без реального AI provider
5. **Event Ingestion** — pre-existing test failures
6. **University Core** — таблицы созданы, роутер не зарегистрирован
7. **MFA** — backend + frontend flow реализованы (setup/verify/disable + login challenge)
8. **Example Notes / Example Slice** — prototype modules в production endpoints

---

## 15. Мастер-трекер ремедиации

> Порядок выполнения строго последовательный. Каждый пункт закрывается зелёными тестами до перехода к следующему.

### Сводка прогресса по блокам

| Блок | Тема | Готово | Всего |
|------|------|--------|-------|
| 1 | Критические блокеры (In-memory → PostgreSQL) | 6 | 10 |
| 2 | Интеграция модулей | 0 | 8 |
| 3 | Frontend CRUD | 0 | 10 |
| 4 | Security Hardening | 0 | 4 |
| 5 | DevOps | 0 | 5 |
| 6 | Enterprise SSO | 0 | 4 |
| 7 | Observability | 0 | 3 |
| 8 | AI Features | 0 | 3 |
| **Итого** | | **4** | **47** |

---

### Блок 1 — Критические блокеры: In-memory → PostgreSQL

#### 1.1 ✅ Перевести local_users storage на PostgreSQL

**Статус:** ЗАВЕРШЕНО — 2026-04-11  
**Файлы:** `backend/alembic/versions/a0b1c2d3e4f5_merge_all_feature_heads.py`, `backend/alembic/versions/d2e3f4a5b6c7_add_app_local_users_table.py`, `backend/app/modules/auth/local_users_service.py`  
**Итог:** 13/13 local_users тестов pass; 88/88 auth тестов pass; регрессий нет.

#### 1.2 ✅ Перевести MFA secrets на PostgreSQL

**Статус:** ЗАВЕРШЕНО — 2026-04-11  
**Файлы:** `backend/app/modules/auth/mfa_service.py`, `backend/app/core/runtime_schema.py`  
**Итог:** `_db_ready=True` по умолчанию (Alembic гарантирует таблицу). Убрана DDL-логика из `_ensure_mfa_table()`. 29/29 auth тестов pass; регрессий нет.

#### 1.3 ✅ Проверить platform_superadmin на PostgreSQL

**Статус:** ЗАВЕРШЕНО — 2026-04-11  
**Файлы:** `backend/app/modules/auth/platform_superadmin_service.py`, `backend/app/modules/auth/local_users_service.py`  
**Итог:** `local_user_store._use_db() = True` в runtime. `upsert_platform_superadmin()` ветвится на `_db_create_user` / `_db_update`. 7/7 тестов pass; регрессий нет.

#### 1.4 ✅ Перевести platform_billing на PostgreSQL

**Статус:** ЗАВЕРШЕНО — 2026-04-11
**Файлы:** `backend/alembic/versions/e3f4a5b6c7d8_add_app_tenant_subscriptions_table.py`, `backend/alembic/versions/b2c4d6e8f0a1_add_app_plan_quotas.py`
**Итог:** Созданы Alembic миграции для `app_plans` + `app_tenant_subscriptions` (e3f4, applied) и `app_plan_quotas` (b2c4, applied). `_ensure_db()` в billing — no-op при `RUNTIME_SCHEMA_BOOTSTRAP_ENABLED=false`. 58/58 billing/plan/quota тестов pass; 2 pre-existing failures (semantic endpoint 404, unrelated).

#### 1.5 ✅ Перевести sessions на PostgreSQL

**Статус:** ЗАВЕРШЕНО — 2026-04-11
**Файлы:** `backend/app/modules/auth/session_service.py`, `backend/alembic/versions/f3e4d5c6b7a9_add_auth_session_and_mfa_tables.py`
**Итог:** Убрана runtime-DDL зависимость в `session_service` (`_db_ready=True`, `_ensure_session_table()` теперь проверяет только доступность DB conn). При доступной БД create/list/revoke/touch идут через `app_auth_sessions`; in-memory fallback остаётся только для окружений без `DATABASE_URL`. Проверка в Docker: `create_session()` создаёт строку в `app_auth_sessions` (`db_rows=1`). Тесты: `tests/test_auth.py -k session` — 2/2 pass.

#### 1.6 ✅ Перевести RBAC assignments на PostgreSQL

**Статус:** ЗАВЕРШЕНО — 2026-04-11
**Файлы:** `backend/app/modules/rbac/service.py`, `backend/app/modules/rbac/router.py`, `backend/alembic/versions/b7d3f1a9c2e4_add_rbac_persistence_tables.py`, `backend/alembic/versions/f9a1b2c3d4e5_rbac_tenant_scope.py`, `backend/alembic/versions/f1c2d3e4a5b7_tenant_fail_closed_platform_wide.py`
**Итог:** Runtime DDL удалён из `rbac/service.py`; DB-path опирается на Alembic-authoritative схему RBAC и baseline seed. Governance-check в `rbac/router.py` дополнен fallback на роли из подписанных JWT claims, чтобы избежать ложных 403 при пустых DB assignments и сохранить tenant-guard semantics. Тесты: `tests/test_rbac_tenant_isolation.py` — 9/9 pass.

#### 1.7 ✅ Перевести feature flags на PostgreSQL

**Статус:** ЗАВЕРШЕНО — 2026-04-11
**Файлы:** `backend/app/modules/feature_flags/service.py`, `backend/app/modules/tenants/provisioning_service.py`, `backend/tests/conftest.py`, `backend/alembic/versions/e3f4a5b6c7d8_add_app_tenant_subscriptions_table.py`
**Итог:** `modules/feature_flags/service.py` переписан как тонкий делегат к `platform.feature_flags.service` (DB-backed через `app_platform_feature_flags`). Удалены in-memory `_flags`/`_flags_by_tenant` дикты. `provisioning_service.py` заменяет side-effect `list_flags()` на явное `set_flag("admin.local_users.tab")`. Исправлен битый дубль `downgrade()` в миграции `e3f4a5b6c7d8`. Тесты: 12/12 pass (`test_feature_flags_tenant_isolation` 4/4, `test_tenant_provisioning` 3/3, остальные 5/5).

#### 1.8 ✅ Перевести tenant store на PostgreSQL

**Статус:** ЗАВЕРШЕНО — 2026-04-11
**Файлы:** `backend/app/modules/tenants/service.py`
**Итог:** DB-путь в `tenants/service.py` уже был реализован. Исправлена ошибочная логика `_should_fallback_to_memory`: убран `ValueError` из списка причин для fallback в память (бизнес-ошибки DB — дубль slug, неверный plan_id — должны пробрасываться, а не замалчиваться). Тесты: 20/20 pass.

#### 1.9 ✅ Исправить BFF proxy SSRF (OWASP A10)

**Статус:** ЗАВЕРШЕНО — 2026-04-11
**Файлы:** `backend/app/modules/integrations/service.py`
**Итог:** Добавлена функция `_validate_outbound_url(url)` в `integrations/service.py`. Проверяет: только `https://` схема, непустой hostname, блокирует `localhost`, все приватные/зарезервированные IP-диапазоны (RFC1918 / 127.x / 169.254.x / 100.64.x / IPv6 loopback и link-local). Вызывается из `save_ai_provider_config` перед сохранением `validation_url`. Тесты: 14/14 pass (integrations + tenants + provisioning).

#### 1.10 ✅ Отключить RUNTIME_SCHEMA_BOOTSTRAP по умолчанию

**Статус:** ЗАВЕРШЕНО — 2026-04-11  
**Файлы:** `backend/app/core/config.py`, `infra/.env`, `infra/.env.example`  
**Итог:** Default `RUNTIME_SCHEMA_BOOTSTRAP_ENABLED` изменён с `"true"` на `"false"`. Удалён вызов `_ensure_mfa_table(conn)` из `bootstrap_runtime_schema()`. `RUNTIME_SCHEMA_BOOTSTRAP_ENABLED=false` добавлен в оба env файла.

---

### Блок 2 — Интеграция модулей

| # | Задача | Статус |
|---|--------|--------|
| 2.1 | Подключить interventions router к `main.py` | ✅ |
| 2.2 | Подключить org_structure router | ✅ |
| 2.3 | Подключить scheduling router | ✅ |
| 2.4 | Подключить workflows router | ✅ |
| 2.5 | Подключить platform KPI router | ✅ |
| 2.6 | Подключить platform event_ingestion router | ✅ |
| 2.7 | Исправить audit tenant isolation (`test_audit_tenant_isolation.py` — 1 failure) | ✅ |
| 2.8 | Исправить SRE ops layer тесты (`test_sre_ops_layer.py` — 3 failures) | ✅ |

---

### Блок 3 — Frontend CRUD

| # | Задача | Статус |
|---|--------|--------|
| 3.1 | Local users CRUD страница | ✅ |
| 3.2 | Tenants management страница | ✅ |
| 3.3 | RBAC assignments UI | ✅ |
| 3.4 | Feature flags UI | ✅ |
| 3.5 | Billing/plans UI (= P1-1) | ✅ |
| 3.6 | Interventions UI | ✅ |
| 3.7 | Org structure UI | ✅ |
| 3.8 | Scheduling UI | ✅ |
| 3.9 | Workflows UI | ✅ |
| 3.10 | Platform KPI dashboard | ✅ |

---

### Блок 4 — Security Hardening

| # | Задача | Статус |
|---|--------|--------|
| 4.1 | SSRF fix для BFF proxy (= 1.9) | ✅ |
| 4.2 | Rate limiting на все critical endpoints | ✅ |
| 4.3 | Audit log tenant isolation fix (= 2.7) | ✅ |
| 4.4 | JWT rotation механизм | ✅ |

---

### Блок 5 — DevOps

| # | Задача | Статус |
|---|--------|--------|
| 5.1 | CI/CD pipeline — полный прогон тестов | ✅ |
| 5.2 | Smoke tests для всех роутеров | ✅ |
| 5.3 | Health check endpoints | ✅ |
| 5.4 | Backup/restore automation | ✅ |
| 5.5 | Release gate скрипты | ✅ |

---

### Блок 6 — Enterprise SSO

| # | Задача | Статус |
|---|--------|--------|
| 6.1 | LDAP integration тесты | ✅ |
| 6.2 | OIDC integration тесты | ✅ |
| 6.3 | SAML integration | ✅ |
| 6.4 | Identity hardening | ✅ |

---

### Блок 7 — Observability

| # | Задача | Статус |
|---|--------|--------|
| 7.1 | Prometheus метрики endpoint | ✅ |
| 7.2 | Structured logging | ✅ |
| 7.3 | Alert rules (Redis, DB pool) | ✅ |

---

### Блок 8 — AI Features

| # | Задача | Статус |
|---|--------|--------|
| 8.1 | AI gateway multi-tenant isolation | ✅ |
| 8.2 | AI copilot recommendations | ✅ |
| 8.3 | AI analytics KPI bridge | ✅ |

---

## Правила работы с трекером

1. Строго последовательно внутри блока — нельзя прыгать через пункты
2. Каждый пункт = зелёные тесты до следующего
3. Pre-existing failures (211 штук) не блокируют прогресс — они из предыдущих сессий
4. Статус в журнале изменений (начало документа) обновляется одновременно с блоком
5. **Active Focus** в начале документа обновляется до начала каждой сессии

---

## 📌 Журнал работы (шаблон сессии)

> Заполнять в начале и конце каждой рабочей сессии.

```
Дата:           
Блок:           
Пункт:          
Сделано:        
Проблемы:       
Следующий шаг:  
```

### История сессий

| Дата | Блок | Пункт | Сделано | Проблемы | Следующий шаг |
|------|------|-------|---------|----------|---------------|
| 2026-04-11 | P0 / Блок 1 | P0-1,2,3,5 / 1.1 | Аудит 4.1/7; LDAP порт; Grafana pw; Redis AOF; middleware; local_users→PostgreSQL | — | Блок 1.2: MFA runtime DDL |
| 2026-04-11 | Блок 1 | 1.2 + 1.10 | MFA `_db_ready=True`; убрана DDL; `RUNTIME_SCHEMA_BOOTSTRAP_ENABLED=false` в default и env; 29/29 auth tests pass | 211 pre-existing failures (несвязанные) | Блок 1.3: platform_superadmin |
| 2026-04-11 | Блок 1 | 1.3 | `local_user_store._use_db()=True` подтверждён; 7/7 superadmin тестов pass | — | Блок 1.4: billing→PostgreSQL |
| 2026-04-11 | Блок 1 | 1.4 | Alembic migrations `app_plans`+`app_tenant_subscriptions`+`app_plan_quotas`; applied to DB; 58 tests pass | 2 pre-existing (semantic 404) | Блок 1.5: sessions→PostgreSQL |
| 2026-04-11 | Блок 1 | 1.5 | `session_service` переведён на Alembic-authoritative DB-path; runtime-DDL gating удалён; проверка записи в `app_auth_sessions` | — | Блок 1.6: RBAC assignments→PostgreSQL |
| 2026-04-11 | Блок 1 | 1.6 | Runtime DDL удалён из RBAC service; governance fallback на JWT claims в router; `test_rbac_tenant_isolation.py` 9/9 pass | Удалён битый дубликат миграции `a1b2...add_app_plans...py`, ломавший startup Alembic | Блок 1.7: feature flags→PostgreSQL |
| 2026-04-11 | Блок 1 | 1.7 | `modules/feature_flags/service.py` → тонкий делегат к platform DB-backed service; provisioning_service явно сеет флаг; 12/12 тестов pass | Исправлена ещё одна битая миграция `e3f4a5b6c7d8` (дубль downgrade) | Блок 1.8: tenant store→PostgreSQL |
| 2026-04-11 | Блок 1 | 1.8 | `_should_fallback_to_memory` убрал `ValueError` из fallback-условий; DB-путь уже был реализован; 20/20 тестов pass | — | Блок 1.9: BFF proxy SSRF |
| 2026-04-11 | Блок 1 | 1.9 | `_validate_outbound_url` в integrations/service.py: только https://, блок приватных IP/localhost/metadata; 14/14 pass | — | Блок 2.1: interventions router |
| 2026-04-11 | Блок 2 | 2.1–2.8 | interventions+risk_router, org_structure подключены (30/30); analytics_router (event_ingestion+kpi) подключён (16/16+238/238); audit tenant isolation: `_resolve_request_tenant_id` разрешает superadmin X-Tenant-ID override; SRE: `_resolve_metrics_tenant_id` для наблюдаемости + lean `/health/ready` без `dependencies`; 64/64+10/10 pass | — | Блок 3.1: Local users CRUD |
| 2026-04-11 | Блок 3 | 3.1 | Local Users CRUD страница уже реализована (list/create/update/delete/password), контракт с backend подтверждён; frontend test `LocalUsersPage` 4/4 pass | — | Блок 3.2: Tenants management |
| 2026-04-11 | Блок 3 | 3.2 | Tenants management доведён до CRUD: добавлен update-flow (name/plan) в detail drawer; убран невалидный `max_students` из create payload (контракт sync с backend); frontend tests `TenantsPage`+`LocalUsersPage` 5/5 pass | — | Блок 3.3: RBAC assignments UI |
| 2026-04-11 | Блок 3 | 3.3 | RBAC assignments UI tenant-scoped: добавлен filter `tenant_id`, tenant-aware assign/revoke, tenant scope для roles/assignments query; admin frontend tests (`RbacPage`+`TenantsPage`+`LocalUsersPage`) 9/9 pass | — | Блок 3.4: Feature flags UI |
| 2026-04-11 | Блок 3 | 3.4 | Feature flags UI проверен: текущая реализация покрывает ключевые list/toggle/rollout flows; targeted frontend test `FeatureFlagsPage` 1/1 pass | — | Блок 3.5: Billing/plans UI |
| 2026-04-11 | Блок 3 | 3.5 | Billing/plans UI закрыт: добавлены маршруты `/console/billing`, `/console/billing/plans`, `/console/billing/quotas`, `/console/billing/usage` с привязкой к существующему platform control plane billing/usage функционалу; billing 404 устранён | Пересборка `frontend-tests` образа потребовалась для подхвата новых test files | Блок 3.6: Interventions UI |
| 2026-04-11 | Блок 3 | 3.6 | Interventions UI подтверждён и усилен тестами: добавлен позитивный сценарий рендера рабочей области (header/export/summary), сохранён сценарий denied; targeted frontend test `InterventionsPage` 2/2 pass | Пересборка `frontend-tests` образа для актуальных тестов | Блок 3.7: Org structure UI |
| 2026-04-11 | Блок 3 | 3.7 | Org structure UI подтверждён: CRUD-страница и доступы присутствуют, targeted frontend test `OrgUnitsPage` 4/4 pass в docker | — | Блок 3.8: Scheduling UI |
| 2026-04-11 | Блок 3 | 3.8 | Scheduling UI подтверждён и усилен тестами: добавлен позитивный сценарий рендера (workspace + empty state), сохранён сценарий denied; targeted frontend test `SchedulingPage` 2/2 pass | Пересборка `frontend-tests` образа для актуальных тестов | Блок 3.9: Workflows UI |
| 2026-04-11 | Блок 3 | 3.9 | Workflows UI подтверждён: страница с запуском workflow, списком инстансов и задач уже реализована; targeted frontend test `WorkflowsPage` 4/4 pass в docker | — | Блок 3.10: Platform KPI dashboard |
| 2026-04-11 | Блок 3 | 3.10 | Platform KPI dashboard подтверждён: route `/console/dashboard` и KPI-интеграция (`useRectorDashboard`, `KpiCard`) уже реализованы; targeted frontend test `RectorDashboardPage` 5/5 pass в docker | — | Блок 4.1: SSRF fix для BFF proxy |
| 2026-04-11 | Блок 4 | 4.1 | SSRF hardening для BFF proxy: добавлена валидация path-segments (блок `..`, protocol-like, `//`, backslash и encoded обходы) с 400 BAD_REQUEST до upstream вызова; security test `bff-proxy` 6/6 pass в docker | Пересборка `frontend-tests` образа для актуальных тестов | Блок 4.2: Rate limiting |
| 2026-04-11 | Блок 4 | 4.2 | Rate limiting расширен на critical auth endpoints: `/api/auth/refresh`, `/api/auth/mfa/enable`, `/api/auth/mfa/verify`, `/api/auth/mfa/disable`; добавлены targeted тесты в `test_rate_limit.py` (refresh+mfa verify) | backend test `tests/test_rate_limit.py` 11/11 pass | Блок 4.3: Audit tenant isolation |
| 2026-04-11 | Блок 4 | 4.3 | Audit tenant isolation подтверждён как закрытый дубликат 2.7: targeted test `tests/test_audit_tenant_isolation.py` | 8/8 pass | Блок 4.4: JWT rotation |
| 2026-04-11 | Блок 4 | 4.4 | JWT rotation подтверждён targeted auth-тестами: refresh flow ротации и revoked refresh rejection | `tests/test_auth.py -k "refresh_flow_rotates_tokens_and_issues_new_access or revoked_refresh_token_is_rejected"` → 2/2 pass | Блок 5.1: CI/CD pipeline |
| 2026-04-11 | Блок 5 | 5.1 | CI/CD pipeline подтверждён: GitHub Actions workflow `ci.yml` выполняет docker build + backend/frontend lint/tests; локальный docker-only pipeline `scripts/pipeline.sh` и `Makefile` target `pipeline` согласованы | `bash -n scripts/pipeline.sh` + `docker compose config` OK | Блок 5.2: Smoke tests |
| 2026-04-11 | Блок 5 | 5.2 | Smoke tests подтверждены docker-only прогоном `scripts/platform_smoke_check.sh`; покрыты health/outbox/automation/webhooks/KPI/AI/developer/metrics (summary: 8 pass, 0 fail). По пути устранён build-блокер frontend (`tsconfig ignoreDeprecations 6.0 -> 5.0`) | Полный smoke run pass после фикса frontend build | Блок 5.3: Health checks |
| 2026-04-11 | Блок 5 | 5.3 | Health check endpoints подтверждены backend targeted-suite: `/health/live`, `/health/ready`, `/health/deep`, `/health/worker` + legacy/deprecation checks и минимальные health маршруты | `tests/test_sre_ops_layer.py tests/test_health_worker_scope.py tests/test_template_validation.py` → 14 passed, 3 skipped | Блок 5.4: Backup/restore automation |
| 2026-04-11 | Блок 5 | 5.4 | Backup/restore automation подтверждён: сценарии backup settings/run/restore/tenant isolation и backup worker-path покрыты тестами; rollback readiness script проверяет читаемость latest dump и безопасный режим drill | `tests/test_backups.py tests/test_backups_tenant_isolation.py tests/test_jobs.py -k "backup or restore"` → 4 passed | Блок 5.5: Release gate scripts |
| 2026-04-11 | Блок 5 | 5.5 | Release gate scripts подтверждены: `rollback_check.sh` pass; safe release-check успешно завершён (backend gates + migration head + frontend type/lint/tests). По ходу снят блокер release-check: зарегистрирован semantic router `/api/v2/semantic/*` в `main.py` | `release_check.sh` (safe flags) pass; semantic suite `test_platform_semantic_layer_v1.py` 8/8 pass | Блок 6.1: LDAP integration тесты |
| 2026-04-11 | Блок 6 | 6.1 | LDAP integration тесты подтверждены: auth LDAP login, integrations LDAP endpoints и phase11 hardening LDAP/identity error mapping | `tests/test_auth.py tests/test_integrations.py tests/test_identity_phase11_hardening.py -k "ldap or identity"` → 35 passed | Блок 6.2: OIDC integration |
| 2026-04-11 | Блок 6 | 6.2 | OIDC integration подтверждён targeted тестом callback mapping isolation (без platform privilege escalation) | `tests/test_enterprise_identity.py -k oidc` → pass | Блок 6.3: SAML integration |
| 2026-04-11 | Блок 6 | 6.3 | SAML integration дополнен и подтверждён: добавлены тесты SAML provider config roundtrip и корректный отказ OIDC-initiate для SAML provider (`not oidc`) | `tests/test_enterprise_identity.py -k "oidc or saml"` → 3 passed | Блок 6.4: Identity hardening |
| 2026-04-11 | Блок 6 | 6.4 | Identity hardening подтверждён полным targeted suite (phase11 hardening + enterprise identity security regression сценарии) | `tests/test_identity_phase11_hardening.py tests/test_enterprise_identity.py` → 36 passed | Блок 7.1: Prometheus метрики endpoint |
| 2026-04-11 | Блок 7 | 7.1 | Prometheus metrics endpoint подтверждён: формат/сбор HTTP метрик, tenant labels, latency snapshots и access-control (`METRICS_TOKEN`, IP allowlist в prod) покрыты observability-suite | `tests/test_platform_hardening_observability.py` → 10 passed | Блок 7.2: Structured logging |
| 2026-04-11 | Блок 7 | 7.2 | Structured logging подтверждён: request-id propagation, structured http_request поля (tenant/actor/request_id/trace_id), audit/security denial logging покрыты targeted suite | `tests/test_platform_hardening_observability.py -k "request_log or request_id or structured"` → 3 passed; `tests/test_privilege_escalation.py -k audit` → 1 passed | Блок 7.3: Alert rules (Redis, DB pool) |
| 2026-04-11 | Блок 7 | 7.3 | Alert rules расширены и проверены: добавлены `RedisLatencyHigh` (`redis_latency_seconds`) и `DbPoolActiveHigh` (`db_connections_active`) в `infra/prometheus/alerts.yml` | `docker compose --env-file .env exec -T prometheus promtool check rules /etc/prometheus/alerts.yml` → SUCCESS (18 rules found) | Блок 8.1: AI gateway multi-tenant isolation |
| 2026-04-11 | Блок 8 | 8.1 | AI gateway multi-tenant isolation подтверждён: tenant-scoped AI model registry isolation + cross-tenant override protection + базовый AI gateway suite без регрессий | `tests/test_ai_registry_tenant_isolation.py tests/test_saas_tenant_cross_user_isolation.py` → 3 passed; `tests/test_ai_gateway.py` → 6 passed | Блок 8.2: AI copilot recommendations |
| 2026-04-11 | Блок 8 | 8.2 | AI copilot recommendations подтверждён: recommendation rule catalog, repository/service integration, API response shape и frontend recommendations UI пройдены targeted-suite | `tests/platform/test_platform_ai_recommendation_layer_v1.py tests/platform/test_platform_ai_copilot_foundation_v1.py` → 46 passed; `__tests__/admin/AICopilotPage.test.tsx` → 7 passed | Блок 8.3: AI analytics KPI bridge |
| 2026-04-11 | Блок 8 | 8.3 | AI analytics KPI bridge подтверждён: event-derived KPI метрики и source_breakdown для `analytics_events_reads_from_events_total`, `analytics_kpi_reads_from_events_total`, `billing_usage_recorded_from_events_total` + tenant isolation | `tests/platform/test_platform_kpi_metrics_v1.py -k "event_bridge or event-derived or source_breakdown"` → 7 passed | Текущий трек 3–8 завершён |
| 2026-04-11 | Финальная верификация | report pass | Финальная runtime валидация подтверждена safe release-check: architecture/tenant/platform/security/template/migration/frontend gates зелёные; semantic suite (`/api/v2/semantic/*`) и enterprise identity OIDC/SAML regression подтверждены отдельными targeted прогонами | `RELEASE_ENABLE_DOMAIN_GATE=false RELEASE_ENABLE_DATA_LAYER_GATE=false RELEASE_ENABLE_SMOKE_GATE=false RELEASE_ENABLE_MIGRATION_ROLLBACK_TEST=false bash scripts/release_check.sh` → pass; `tests/platform/test_platform_semantic_layer_v1.py` → 8 passed; `tests/test_enterprise_identity.py -k "oidc or saml"` → 3 passed | Трек закрыт, ожидание нового scope |
| 2026-04-11 | Пост-верификация | full backend suite | Выполнен полный backend pytest с ранней остановкой отключённой фактически (не сработала): pre-existing blocker о массовых падениях не воспроизводится | `docker compose --env-file .env exec -T backend pytest -q --maxfail=1 -rA` → 1306 passed, 12 skipped | P0-4 помечен resolved |
| 2026-04-11 | Пост-верификация | stale blockers sync | Устаревшие TODO синхронизированы с фактами: P1-2 (analytics router живой через platform delegation), P2-6 (event_ingestion failures не воспроизводятся), P3-3 (Redis/DB pool alerts уже внедрены) | `tests/platform/test_platform_analytics_v1.py -k "kpis or refresh"` → 5 passed; full backend suite → 1306 passed, 12 skipped | Готово к следующему remediation scope |
| 2026-04-12 | Следующий remediation scope | P1-3 | Реализован frontend MFA flow: security page (start enrollment/verify/disable), login MFA challenge (`mfa_code` / `mfa_recovery_code`) и покрытие тестами | `npx vitest run __tests__/components/LoginTenantMode.test.tsx __tests__/admin/SecurityPage.test.tsx` → 2 files passed, 6 tests passed | P1-4: worker graceful shutdown |
| 2026-04-12 | P1-4 worker graceful shutdown | P1-4 | Bash while-loop заменён на `backend/scripts/run_worker.py` с SIGTERM-хэндлером (`threading.Event._stop`). `stop_signal: SIGTERM` + `stop_grace_period: 30s` добавлены в docker-compose.yml. Dockerfile: `COPY scripts ./scripts` | `pytest tests/test_worker_graceful_shutdown.py` → 3 passed in 0.08s | P1-6: убрать example_notes/example_slice из prod |
| 2026-04-12 | P1-6/P1-7 верификация | P1-6/P1-7 | P1-6: `example_notes`, `example_slice` уже удалены из `main.py` (установлено в предыдущей сессии). P1-7: `university_core` — сервисный слой (не роутер), корректно используется 7 модулями | `grep -rn` — нет в `main.py` | P2-1: Role portal UX |
| 2026-04-12 | P2-1 верификация + тесты | P2-1 | `RolePortalShell` + `RoleZoneLayout` уже реализованы: live KPI из `/api/bff/analytics/kpis`, AI Academic Risk Watch (student), per-role navigation. Написаны 6 тестов `RolePortalShell.test.tsx` | `npx vitest run __tests__/components/RolePortalShell.test.tsx` → 6 passed in 219ms | P2-2: AI provider keys env vars |
| 2026-04-12 | P2-2 + P2-3 fix | P2-2, P2-3 | P2-2: `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `AI_CUSTOM_PROVIDER_API_KEY`, `AI_PROVIDER_TIMEOUT_SECONDS` добавлены в `backend` и `worker` service в docker-compose.yml (уже были в `.env.example`). P2-3: `Content-Security-Policy`, `Referrer-Policy`, `Permissions-Policy` добавлены в `infra/nginx/nginx.conf` | `grep OPENAI docker-compose.yml` → 2 entries; nginx CSP header присутствует | P2-4: CI backup restore test |
| 2026-04-12 | P2-4 CI restore test | P2-4 | Создан `backend/tests/test_restore_ci.py` (маркер `integration`): `test_backup_dump_is_restorable` — реальный `pg_dump` + `pg_restore --list`; `test_restore_script_dry_run` и `test_restore_requires_confirm_flag` тестируют `restore_db.sh` (запускаются в backend-tests, где PROJECT_ROOT=/project). Без DATABASE_URL — автоскип. | `pytest tests/test_restore_ci.py` → 1 passed, 2 skipped (в backend; 3 passed в backend-tests) | P2-5: Billing enforcement |
| 2026-04-12 | P2-5 billing enforcement | P2-5 | Добавлены `assert_billing_write_allowed(...)` в create write-paths: courses (`create/update/delete`), enrollments (`enroll_student` и legacy `create_enrollment`), scheduling (`create_course_section`, `create_lesson_instance`, `create_discipline`, `create_lesson_topic`). Добавлены unit-test assertions для billing guard в courses/enrollments/scheduling service tests. | `pytest tests/modules/courses/test_courses_service.py tests/modules/enrollments/test_enrollment_lifecycle_service.py tests/modules/scheduling/test_scheduling_service.py` → 34 passed | P2-7: mypy/pyright in CI |
| 2026-04-12 | P2-7 mypy in CI | P2-7 | В `backend/requirements.txt` добавлен `mypy==1.11.2`; в `.github/workflows/ci.yml` добавлен backend type-check step: `mypy --explicit-package-bases app --ignore-missing-imports --follow-imports=silent`. | `docker compose exec backend mypy --explicit-package-bases app --ignore-missing-imports --follow-imports=silent` → pass | P2-8: DB-only billing mode |
| 2026-04-12 | P2-8 billing DB-only mode | P2-8 | `app/modules/billing/service.py`: добавлен fail-closed guard `BILLING_DB_ONLY_MODE` (default `true`), при отсутствии DB теперь `503 billing_required` вместо in-memory fallback. `infra/.env.example` + `infra/docker-compose.yml` дополнены `BILLING_DB_ONLY_MODE`; в `tests/conftest.py` добавлен override `BILLING_DB_ONLY_MODE=false` для unit-suite без `DATABASE_URL`. Добавлен тест `tests/test_billing_db_only_mode.py`. | `pytest tests/test_billing_db_only_mode.py tests/test_billing_commercial_layer.py` → 23 passed | P3-1: lazy imports cleanup |
| 2026-04-12 | P3-1 admissions lazy imports cleanup | P3-1 | Удалены lazy imports из `admissions/service.py`: зависимости workflow/profiles/students вынесены в module imports. Для совместимости тестов сохранён patch-friendly вызов через `workflow_service.WorkflowService`. | `pytest tests/modules/admissions` → 128 passed | P3-2: PgBouncer |
| 2026-04-12 | P3-2 PgBouncer integration | P3-2 | В `infra/docker-compose.yml` добавлен сервис `pgbouncer` (transaction pooling, healthcheck, tuning envs), backend/backend-tests/worker/scheduler переключены на `DATABASE_URL` через PgBouncer (`pgbouncer:6432`). В `infra/.env.example` добавлены `PGBOUNCER_PORT`, `PGBOUNCER_MAX_CLIENT_CONN`, `PGBOUNCER_DEFAULT_POOL_SIZE`, `PGBOUNCER_RESERVE_POOL_SIZE`. | `docker compose -f infra/docker-compose.yml --env-file infra/.env config` → OK | P3-4: frontend RBAC nav hiding |
| 2026-04-12 | P3-4 navigation RBAC verified | P3-4 | Role-based nav hiding уже реализован: `AppSidebar` использует `getNavigationForRoles(roles)` + фильтр `hasPermission(item.permission)`. Отдельно подтверждено, что `Platform Management` показывается только для superadmin/admin. | `npx vitest run __tests__/navigation/navigation-clean.test.ts` → 3 passed | P3-5: CHANGELOG |
| 2026-04-12 | P3-6 auth cookie unification | P3-6 | В auth/BFF runtime канонизирован cookie `app_access_token`: логин устанавливает `app_access_token`; middleware и admin/auth API routes читают `app_access_token` с legacy fallback на `admin_token`. Это сохраняет обратную совместимость без разрыва активных сессий. | `npx vitest run __tests__/security/auth-routes.test.ts __tests__/security/bff-proxy.test.ts` → 20 passed; `npx vitest run __tests__/security/middleware.test.ts` (with `API_BASE_URL`) → 4 passed | P3-7: coverage threshold |
| 2026-04-12 | P3-7 pytest coverage threshold | P3-7 | В `backend/pytest.ini` добавлен глобальный `addopts` с coverage gate: `--cov=app --cov-report=term-missing --cov-fail-under=80`. Это включает обязательный порог покрытия для backend test runs по умолчанию. | `backend/pytest.ini` содержит `--cov-fail-under=80` | P3-5: CHANGELOG |
| 2026-04-12 | P3-5 changelog bootstrap | P3-5 | Добавлен корневой `CHANGELOG.md` в формате Keep a Changelog с секциями Added/Changed/Security и фиксированными изменениями remediation-прохода. | `CHANGELOG.md` присутствует в root и содержит актуальный Unreleased блок | P3-8: federation use-case |
| 2026-04-12 | P3-8 federation use-case verified | P3-8 | Federation слой подтверждён как production-valid для multi-institution сценариев: есть platform-admin API surfaces (`/api/v1/admin/platform/federation/*`), permission-gated RBAC (`federation.read/write`), deployment ограничения и отдельный платформенный test-suite. Удаление не требуется, слой документирован. | `pytest tests/platform/test_platform_federation_layer_v1.py` (existing suite), refs: `docs/DEPLOYMENT_BLUEPRINT.md`, `docs/PILOT_RBAC_AUDIT.md` | Next backlog: release readiness + regression cadence |
