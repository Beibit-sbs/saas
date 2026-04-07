# ПОЛНЫЙ АУДИТ СИСТЕМЫ AI University OS
**Дата**: 2026-04-06  
**Аудитор**: GitHub Copilot (Claude Sonnet 4.6)  
**Режим**: READ-ONLY, без изменений кода  
**Статус**: ЗАВЕРШЁН

---

## EXECUTIVE SUMMARY

Система **в целом работоспособна и запущена**. Все 9 Docker-контейнеров здоровы. Аутентификация, RBAC, база данных и ключевые бизнес-потоки функционируют. Однако обнаружены **3 критических проблемы** (P0) и **11 серьёзных проблем** (P1), требующих устранения до production-релиза.

**Главные риски:**
- `/docs` и `/openapi.json` публично доступны без аутентификации — полный API-контракт открыт
- Frontend `Metrics` тип (health-страница) имеет 0% совпадения с реальным backend-ответом — данные никогда не отображаются
- Тестовая директория не попадает в Docker-образ — тесты не запускаются в CI через container

---

## ФАЗА 1: ИНВЕНТАРЬ

### 1.1 Docker-контейнеры (runtime)

| Контейнер | IP | Порт | Статус |
|-----------|-----|------|--------|
| ai-backend-1 | 172.18.0.5 | 8000 | ✅ healthy |
| ai-db-1 | 172.18.0.x | 5432 | ✅ healthy |
| ai-frontend-1 | 172.18.0.8 | 3000 | ✅ healthy |
| ai-ldap-1 | 172.18.0.x | 389 | ✅ healthy |
| ai-nginx-1 | 172.18.0.11 | 443 | ✅ up |
| ai-prometheus-1 | 172.18.0.x | 9090 | ✅ up |
| ai-redis-1 | 172.18.0.x | 6379 | ✅ healthy |
| ai-scheduler-1 | 172.18.0.x | — | ✅ healthy |
| ai-worker-1 | 172.18.0.x | — | ✅ up |

### 1.2 Миграции Alembic

- Всего: **54 миграции**
- Заголовок (head): `d4c5e6f7a8b9`
- Runtime статус: `current == head` ✅ Все применены

### 1.3 Backend — зарегистрированные роутеры (main.py)

59 роутеров включено в FastAPI app. Структурно разбиты на:
- **Модульный слой** (`app/modules/`): 35 роутеров
- **Platform слой** (`app/platform/`): 9 роутеров
- **Legacy platform** (`app/modules/platform/`): 2 роутера

### 1.4 Frontend — страницы console

29 `page.tsx` файлов в `app/(admin)/console/`:
admissions, ai/copilot, automation (+ executions/new/templates), dashboard, developer/apps, enrollments, feature-flags, federation, grades, health, interventions, jobs, notifications, ops, platform/[section], preferences, profile, scheduling, security, students/[id], students/[id]/transcript, students, tenants, transcripts

Плюс параллельный legacy zone: `app/admin/` (13 компонентов, 12 hooks)

### 1.5 Тесты

| Тип | Файлов | Где |
|-----|--------|-----|
| Backend unit/integration | 114 test_*.py | `/backend/tests/` |
| Frontend unit (Jest/RTL) | 31 | `/frontend/__tests__/` |
| E2E (Playwright) | 6 spec | `/frontend/e2e/` |

---

## ФАЗА 2: FRONTEND АУДИТ (страница за страницей)

### 2.1 Таблица страниц

| Маршрут | Файл | Модуль | Permission Guard | API путь | Статус |
|---------|------|--------|-----------------|---------|--------|
| `/console` | `page.tsx` | re-export dashboard | ❌ Нет | — | ⚠️ redirect alias |
| `/console/dashboard` | `dashboard/page.tsx` | — | ⚠️ частичный (metrics only) | `/api/admin/dashboard` | ✅ |
| `/console/health` | `health/page.tsx` | platform/health | ✅ `HEALTH_READ` | `/api/health` + `/metrics` | ⚠️ Metrics schema drift |
| `/console/admissions` | `admissions/page.tsx` | platform/admissions | ❌ Нет page-level guard | `/api/admin/admissions` | ⚠️ |
| `/console/interventions` | `interventions/page.tsx` | platform/interventions | ✅ `PermissionGate` ×3 | `/api/admin/interventions/cases` | ✅ |
| `/console/students` | `students/page.tsx` | students | ✅ `hasPermission(STUDENTS_READ)` | `/api/admin/students` | ✅ |
| `/console/students/[id]` | `[id]/page.tsx` | students | (не читался) | — | ? |
| `/console/enrollments` | `enrollments/page.tsx` | enrollments | ✅ `PermissionGate` (только write) | `/api/admin/enrollments` | ⚠️ READ не защищён |
| `/console/grades` | `grades/page.tsx` | grades | ✅ `PermissionGate (GRADES_WRITE)` | `/api/admin/grades` | ✅ |
| `/console/scheduling` | `scheduling/page.tsx` | scheduling | ✅ `hasPermission(SCHEDULING_READ)` | `/api/admin/scheduling/sections` | ✅ |
| `/console/automation` | `automation/page.tsx` | platform/automation | ✅ `RequirePermission(AUTOMATION_READ)` | `/api/bff/admin/platform/automation/*` | ✅ |
| `/console/automation/new` | `new/page.tsx` | platform/automation | (не читался) | — | ? |
| `/console/automation/executions` | `executions/page.tsx` | platform/automation | ✅ `RequirePermission(AUTOMATION_READ)` | `/api/bff/admin/platform/automation/executions` | ✅ |
| `/console/automation/templates` | `templates/page.tsx` | platform/automation | (не читался) | — | ? |
| `/console/feature-flags` | `feature-flags/page.tsx` | platform/feature-flags | ✅ `hasPermission(FEATURE_FLAGS_WRITE)` | `/api/admin/feature-flags` | ✅ |
| `/console/federation` | `federation/page.tsx` | platform/federation | ✅ `RequirePermission` | `/api/bff/admin/platform/federation/*` | ✅ |
| `/console/jobs` | `jobs/page.tsx` | platform/jobs | ✅ `PermissionGate(JOBS_WRITE)` | `/api/bff/admin/jobs` | ✅ |
| `/console/notifications` | `notifications/page.tsx` | platform/notifications | ✅ `PermissionGate(NOTIFICATIONS_WRITE)` | `/api/v1/admin/notifications` | ✅ |
| `/console/ops` | `ops/page.tsx` | platform/ops | ✅ `RequirePermission(ops.read)` | `/api/v1/platform/ops/summary` | ✅ |
| `/console/platform` | `platform/page.tsx` | — | ❌ Нет guard | `PlatformSectionView` | ⚠️ |
| `/console/platform/[section]` | `[section]/page.tsx` | — | (не читался) | — | ? |
| `/console/ai/copilot` | `copilot/page.tsx` | platform/ai | ✅ `RequirePermission` | `/api/bff/admin/platform/ai/copilot/*` | ✅ |
| `/console/developer/apps` | `apps/page.tsx` | platform/developer | ✅ `RequirePermission` | `/api/bff/admin/platform/developer/apps` | ✅ |
| `/console/tenants` | `tenants/page.tsx` | platform/tenants | ✅ `PermissionGate(TENANTS_WRITE)` | `/api/admin/tenants` | ✅ |
| `/console/transcripts` | `transcripts/page.tsx` | — | ✅ `hasPermission(TRANSCRIPTS_READ)` | — | ✅ |
| `/console/security` | `security/page.tsx` | — | ❌ Нет guard | Self-service (password change) | ⚠️ Low risk |
| `/console/preferences` | `preferences/page.tsx` | — | ❌ Нет guard | User prefs only | ⚠️ Low risk |
| `/console/profile` | `profile/page.tsx` | — | ❌ Нет guard | User profile only | ⚠️ Low risk |

### 2.2 Ролевые зоны (role portals)

| Маршрут | Auth | Данные |
|---------|------|--------|
| `/student` | ✅ Middleware: full session check + role | KPI cards через `useKpiDashboard` |
| `/faculty` | ✅ Middleware: full session check + role | KPI cards |
| `/registrar` | ✅ Middleware: full session check + role | KPI cards |

Логика ROLE_ROUTE_RULES в middleware.ts работает корректно.

### 2.3 Legacy admin zone (`/admin/`)

Полноценная параллельная реализация с:
- `AdminShell` — tabbed UI с 13 вкладками
- 12 React hooks с прямыми API вызовами
- Собственный `adminTranslations` i18n
- CSS: `admin-legacy.css`

**Статус**: Живой, рабочий код. `/admin` маршрут не удалён. Полный дубликат функциональности `/console/`.

---

## ФАЗА 3: BACKEND АУДИТ (модуль за модулем)

### 3.1 Модульный слой — статус реализации

| Модуль | Router Prefix | RBAC | Статус | Примечания |
|--------|--------------|------|--------|-----------|
| auth | `/api/auth/` | Частичный | ✅ Рабочий | JWT + LDAP + local |
| admin | `/api/admin/` | ✅ | ✅ Рабочий | dashboard + system/health |
| admin/local_users | `/api/admin/local-users` | ✅ | ✅ | — |
| admissions | `/api/admin/admissions` | ✅ | ✅ | Full workflow |
| ai_gateway | `/api/admin/ai/` | ✅ | ✅ | Заглушки для anthropic/custom |
| analytics | `/api/analytics/` | ✅ | ✅ | — |
| audit | `/api/admin/audit/` | ✅ | ✅ | — |
| backup | `/api/admin/backups/` | ✅ | ✅ | — |
| **billing** | ❌ Нет роутера | N/A | ⚠️ Library only | Вызывается внутренне |
| courses | `/api/admin/university/courses` | ✅ | ⚠️ Legacy | Только legacy prefix |
| degree_progress | nested students | ✅ | ✅ | — |
| enrollments | `/api/admin/enrollments/` + legacy | ✅ | ✅ Dual path | — |
| faculty | `/api/admin/university/faculty` | ✅ | ⚠️ Legacy | Только legacy prefix |
| feature_flags | `/api/admin/feature-flags` | ✅ | ✅ | — |
| grades | `/api/admin/grades/` | ✅ | ✅ | — |
| help | `/api/help/topics` | ❌ Публичный | ✅ | Корректно |
| i18n | `/api/i18n/` + `/api/admin/i18n/` | Частичный | ✅ | — |
| identity | dual router | ✅ | ⚠️ Dual router | phase1_router — legacy |
| integrations | `/api/admin/integrations/` | ✅ | ✅ | — |
| interventions | `/api/admin/interventions/cases` | ✅ | ✅ | + risk_router |
| jobs | `/api/admin/jobs/` | ✅ | ⚠️ Stub handlers | sync/ldap.sync/ai.generate = placeholder |
| ldap | `/api/admin/ldap/status` | ✅ | ✅ | — |
| observability | health/metrics | ✅ (часть) | ✅ | — |
| org_structure | `/api/admin/org-units/` | ✅ | ✅ | — |
| **plans** | ❌ Нет роутера | N/A | ⚠️ Library only | Через `/platform/plans` |
| **quotas** | ❌ Нет роутера | N/A | ⚠️ Library only | Через `/platform/quotas` |
| profiles | `/api/admin/profiles/` | ✅ | ✅ | — |
| programs | `/api/admin/university/programs` | ✅ | ⚠️ Legacy | Только legacy prefix |
| rbac | `/api/admin/rbac/` | ✅ | ✅ | — |
| scheduling | `/api/admin/scheduling/` | ✅ | ✅ | — |
| security | Нет роутера | N/A | ✅ Library | rate_limit, url_validation |
| service_accounts | `/api/admin/service-accounts` | ✅ | ✅ | — |
| students | `/api/admin/students/` + legacy | ✅ | ✅ Dual path | — |
| tenants | `/api/admin/tenants/` + public | ✅ | ✅ | — |
| transcripts | nested students | ✅ | ✅ | — |
| **university_core** | ❌ Нет роутера | N/A | ⚠️ Dead | Нет вызовов |
| usage | Нет роутера | N/A | ✅ Library | Вызывается внутренне |
| workflows | `/api/admin/workflows/` | ✅ | ✅ | — |

### 3.2 Platform слой — статус

| Router | Prefix | Endpoints | Статус |
|--------|--------|-----------|--------|
| router_admin.py | `/api/v1/admin` | 40+ endpoints | ✅ Полный |
| router_ops.py | `/api/v1/platform/ops` | 1 (`/summary`) | ✅ Реализован |
| router_public.py | `/api/v1/public` | (context) | ✅ |
| router_internal.py | `/api/v1/internal` | webhooks/notifications | ✅ |
| router_mcp.py | `/api/v1/internal/mcp` | schema endpoints | ✅ |
| router_developer_api.py | `/api/dev` | analytics/enrollments/grades/students | ✅ |
| router_semantic.py | `/api/v2/semantic` | dimensions/entities/insights | ✅ |
| platform/router.py (legacy) | `/platform` | plans/quotas/billing | ✅ Legacy |
| platform/self_service_router.py | — | billing self-service | ✅ |

### 3.3 Job handlers (worker.py)

Реализованы:
- `backup.run` → `_execute_backup_run()` ✅
- `audit.export` → `_execute_audit_export()` ✅

**Заглушки (placeholder)**:
- `sync` → `_execute_placeholder`
- `ldap.sync` → `_execute_placeholder`
- `ai.generate` → `_execute_placeholder`
- `report.generate` → `_execute_placeholder`

---

## ФАЗА 4: CONNECTIVITY AUDIT (E2E цепочки)

### 4.1 Технический стек маршрутизации

```
Browser → nginx:443 (SSL termination)
  ├── /api/bff/* → frontend:3000 → BFF proxy → backend:8000 (с JWT)
  ├── /api/v1/internal/* → backend:8000 (allow: RFC1918 only)
  ├── /api/* → backend:8000 (прямо)
  ├── /health, /health/* → backend:8000 (прямо)
  ├── /metrics → backend:8000 (allow: RFC1918 only)
  ├── /platform, /platform/* → backend:8000 (прямо)
  └── /* → frontend:3000 (Next.js)
```

### 4.2 BFF proxy — маппинг путей

`mapToBffPath()` в `client.ts`:
- `/api/v1/admin/*` → `/api/bff/v1/admin/*` → BFF → backend `/api/v1/admin/*`
- `/api/admin/*` → `/api/bff/admin/*` → BFF → backend `/api/admin/*`
- `/platform/*` → `/api/bff/platform/*` → BFF → backend `/platform/*`
- `/health`, `/health/*` → `/api/bff/health*` → BFF → backend `/health*`
- `/metrics`, `/metrics/*` → `/api/bff/metrics*` → BFF → backend `/metrics*`

`toUpstreamPath()` в `bff-proxy.ts`:
- `admin/platform/*` → `/api/v1/admin/platform/*` (backend) ✅
- `platform/*` → `/platform/*` (backend) ✅
- `health*`, `metrics*` → `/{path}` (backend) ✅
- else → `/api/{path}` ✅

### 4.3 Runtime проверки успешности

| Endpoint | Статус | Auth | Корректность |
|---------|--------|------|-------------|
| `GET /health/live` | 200 | Нет | ✅ |
| `GET /health/ready` | 200 | Нет | ✅ |
| `GET /health` | 401 | Да | ✅ |
| `GET /health/comprehensive` | 401 | Да | ✅ |
| `GET /metrics` | 401 | Да | ✅ |
| `GET /api/health` | 200 | Нет | ✅ |
| `GET /api/meta` | 200 | Нет | ✅ |
| `GET /api/auth/csrf` | 200 | Нет | ✅ |
| `GET /api/auth/modes` | 200 | Нет | ✅ |
| `GET /api/public/tenants/login-directory` | 200 | Нет | ✅ |
| **`GET /docs`** | **200** | **Нет** | ❌ **ПРОБЛЕМА** |
| **`GET /openapi.json`** | **200** | **Нет** | ❌ **ПРОБЛЕМА** |
| **`GET /redoc`** | **200** | **Нет** | ❌ **ПРОБЛЕМА** |
| `GET /api/v1/admin/tenants/1` | 401 | Да | ✅ |
| `GET /api/v1/platform/ops/summary` | 401 | Да | ✅ |
| `GET /api/dev/students` | 401 | Да | ✅ |
| `GET /api/bff/health` | 401 | Да | ✅ |
| `GET /api/bff/metrics` | 401 | Да | ✅ |
| `GET /api/internal/ready` (frontend) | 200 | Нет | ✅ |

---

## ФАЗА 5: ДУБЛИКАТЫ / LEGACY / МЁРТВЫЙ КОД

### 5.1 Backend дубликаты

| Проблема | Где | Риск |
|---------|-----|------|
| Legacy API `/api/admin/university/students` | `legacy_students_router` | P2 — дублирует `/api/admin/students` |
| Legacy API `/api/admin/university/enrollments` | `legacy_enrollments_router` | P2 |
| Legacy API `/api/admin/university/courses` | courses module | P2 |
| Legacy API `/api/admin/university/faculty` | faculty module | P2 |
| Legacy API `/api/admin/university/programs` | programs module | P2 |
| `identity_phase1_router` vs `identity_router` | identity module | P2 — "phase1" в имени рабочего кода |
| `/platform/plans` + `/platform/quotas` (old prefix) | platform/router.py | P2 — рядом с новым `/api/v1/admin/billing/plans` |
| `billing/service.py`, `plans/service.py`, `quotas/service.py` — без роутеров | modules/ | OK — library use |
| `university_core/service.py` | modules/ | P3 — нет вызовов нигде |
| `/api/admin/system/health` vs `/api/admin/dashboard` | admin/router.py | P3 — оба делают похожее |

### 5.2 Frontend дубликаты

| Проблема | Файлы | Риск |
|---------|-------|------|
| **Legacy admin zone** `/app/admin/` | 13 компонентов, 12 hooks, `admin-legacy.css` | P1 — живая копия `/console/` |
| `app/admin/hooks/` — отдельный слой hooks с прямыми `fetch` | admin/hooks/*.ts | P1 — дублирует `modules/platform/*/hooks.ts` |
| `app/admin/types.ts` — свои типы | admin/types.ts | P2 |
| `i18n/admin.ts` — отдельный translation store | `adminTranslations` | P2 — рядом с основным i18n |

### 5.3 Неиспользуемый / заглушечный код

| Код | Статус |
|-----|--------|
| `_execute_placeholder` для `sync`, `ldap.sync`, `ai.generate`, `report.generate` | Зарегистрировано как JOB_HANDLERS, но нигде не вызывается реально |
| `app/platform/context/service.py` — "No-op rebuild placeholder" | stub |
| `enrollments/service.py::_load_course_placeholder` | stub — нет реальной валидации курса |
| `scheduling/service.py::_load_course_placeholder` | stub — аналогично |

---

## ФАЗА 6: АУДИТ БЕЗОПАСНОСТИ

### 6.1 КРИТИЧЕСКИЕ проблемы (P0)

#### P0-1: `/docs`, `/openapi.json`, `/redoc` открыты без аутентификации

**Факт**: `GET /docs → 200`, `GET /openapi.json → 200`, `GET /redoc → 200` — проверено в runtime.  
**Риск**: Полный API-контракт (все 200+ endpoints, схемы, параметры) доступен без credentials.  
**Вектор**: Внешний злоумышленник изучает API структуру, находит уязвимые эндпоинты.  
**nginx**: `/docs`, `/openapi.json`, `/redoc` не имеют явных location rules → попадают в `location /api/` или `location /` — не заблокированы.  

#### P0-2: Metrics schema drift — health-страница всегда пустая

**Факт**: `useMetrics()` → `/metrics` → BFF → backend `/metrics` → 401 без токена.  
**Но даже если бы данные пришли**: Frontend `Metrics` type (8 полей: `total_tenants, active_tenants, total_students, active_jobs, queued_jobs, failed_jobs_24h, api_requests_1h, avg_response_ms`) имеет **0 совпадений** с backend `/metrics/ops` ответом.  
**Верный эндпоинт для метрик**: `/api/v1/platform/ops/summary` — но health-страница его не использует.  
**Результат**: MetricCards на health-странице показывают `undefined`/`null` / `NaN`.

#### P0-3: Тесты не включены в Docker-образ

**Факт**: `backend/Dockerfile` копирует только `app/`, `alembic/`, `alembic.ini`. Директория `tests/` не включена.  
**Результат**: `docker compose exec backend pytest` не находит тесты. Все 114 test-файлов невозможно запустить через CI с текущим образом.  
**Риск**: Иллюзия CI/CD покрытия без реального выполнения тестов в контейнере.

### 6.2 СЕРЬЁЗНЫЕ проблемы (P1)

#### P1-1: Legacy admin UI (`/admin/`) — параллельный несинхронизированный фронт

**Факт**: `/app/admin/page.tsx` + 13 компонентов + 12 hooks — живой, рабочий код.  
**Риск**: Изменения в `/console/` не отражаются в `/admin/`. Администраторы могут использовать устаревший интерфейс. Permission guards могут отличаться.  
**API hooks**: Несинхронизированы с основными `modules/` — возможны расхождения в логике.

#### P1-2: `/console/admissions/page.tsx` — нет page-level permission guard

**Факт**: `grep -c "PermissionGate\|RequirePermission\|hasPermission" admissions/page.tsx = 0`.  
**Место**: Admissions содержит персональные данные абитуриентов, документы, решения.  
**Риск**: Любой авторизованный пользователь (с валидным токеном) видит и может менять данные.  
**Backend**: Защищён `permission_dependency("admissions.read/write")` — frontend guard отсутствует.

#### P1-3: `/console/platform/page.tsx` — нет permission guard

**Факт**: re-export `PlatformSectionView` без обёртки PermissionGate.  
**Platform**: содержит управление тенантами, billing, feature flags, automation — критичный раздел.  

#### P1-4: Dual router paths — legacy `/api/admin/university/*` активны

**Факт**: 5 пар legacy/new роутеров зарегистрированы одновременно в `main.py` (строки 234–241).  
**Риск**: Две версии API конкурируют. Изменение одного не меняет другой. Возможны расхождения в данных.

#### P1-5: `JWT_SECRET_KEY` не задан в env, но `JWT_SECRET` задан корректно

**Уточнение**: Backend читает `JWT_SECRET` (не `JWT_SECRET_KEY`) — проверено в `token_service.py`. JWT_SECRET длина 64 символа ✅. Но в `.env` отсутствует явный `JWT_SECRET_KEY` (имя env var из некоторых фреймворков) — мелкое несоответствие.

#### P1-6: `ENVIRONMENT`, `ALLOW_ORIGINS`, `AUTH_ALLOW_LEGACY_HEADERS` — не заданы в env

**Факт**: `ENVIRONMENT=UNSET`, `ALLOW_ORIGINS=UNSET` в runtime.  
**Риск**: Если backend применяет дефолты (например, `allow_origins=["*"]`), это CORS-уязвимость.  
**Нужна проверка**: Какие дефолты применяются при отсутствии этих переменных.

#### P1-7: `/api/help/topics` — публичный, возвращает реальные данные на русском

**Факт**: `GET /api/help/topics → 200` → данные на русском языке без аутентификации.  
**Оценка**: Вероятно, задизайнено так (help публичен). Но данные включают пользовательские подсказки — оцените, что именно раскрывается.

#### P1-8: `/api/auth/modes` — раскрывает конфигурацию auth без аутентификации

**Факт**: `{"modes":{"local":true,"ldap":false,"api_keys":true}}` без auth.  
**Оценка**: Незначительный инфо-leak, но помогает атакующему строить стратегию.

#### P1-9: `outbox_backlog` и `event_queue_size` — одно и то же значение

**Факт**: В `router_ops.py` (строки 56–57):
```python
outbox_backlog = _safe_metric_int(lambda: uow.outbox_event_repository.count_backlog(...))
event_queue_size = _safe_metric_int(lambda: uow.outbox_event_repository.count_backlog(...))
```
Оба значения из одного и того же метода. `event_queue_size` и `outbox_backlog` всегда идентичны.

#### P1-10: Job handlers — 4 из 6 типов задач — заглушки

**Факт**: `sync`, `ldap.sync`, `ai.generate`, `report.generate` возвращают `{"status": "accepted", "note": "handler placeholder"}`.  
**Риск**: Задачи создаются пользователями, принимаются системой, но не выполняются реально.

#### P1-11: Worker/Scheduler — нет heartbeat update в логах

**Факт**: Логи показывают только `"worker loop started"` / `"scheduler loop started"` — нет итераций.  
**Риск**: Неизвестно, обрабатывают ли воркеры задачи в runtime.

### 6.3 УМЕРЕННЫЕ проблемы (P2)

| ID | Проблема | Риск |
|----|---------|------|
| P2-1 | Legacy `/api/admin/university/*` роутеры — нет плана удаления | Maintenance |
| P2-2 | `identity_phase1_router` — "phase1" в имени активного рабочего кода | Confusion |
| P2-3 | `/console/security/page.tsx` — нет permission guard (только изменение пароля) | Low (self-service) |
| P2-4 | `/console/preferences/` и `/console/profile/` — нет guard | Low (personal only) |
| P2-5 | `enrollments/page.tsx` — READ-данные не защищены guard | Medium |
| P2-6 | `useMetrics()` hook обращается к `/metrics` через BFF → backend `/metrics` — этот endpoint требует auth, BFF добавляет JWT — технически OK, но старый путь |
| P2-7 | `admin-legacy.css` — отдельный stylesheet для deprecated zone | Tech debt |
| P2-8 | `dashboard/page.tsx` — metrics секция показывается только при `METRICS_READ`, но весь dashboard доступен без guard | Info leak |

### 6.4 Безопасность конфигурации

| Параметр | Статус | Оценка |
|---------|--------|--------|
| `JWT_SECRET` | ✅ Задан, 64 символа | Хорошо |
| `INTERNAL_API_TOKEN` | ✅ Задан, 74z3**** | Хорошо |
| `/api/v1/internal/` | ✅ RFC1918 only в nginx | Хорошо |
| `/metrics` | ✅ RFC1918 only в nginx | Хорошо |
| SSL/TLS | ✅ TLSv1.2+1.3, HSTS | Хорошо |
| X-Frame-Options | ✅ DENY | Хорошо |
| X-Content-Type-Options | ✅ nosniff | Хорошо |
| CSRF | ✅ Endpoint `/api/auth/csrf` + аномалия в backend logs | OK |
| Rate limiting | ✅ `security/rate_limit.py` — реализован | Хорошо |
| `/docs` открыт | ❌ Без auth | **P0** |
| CORS origins | ❓ `ALLOW_ORIGINS` не задан | Проверить |

---

## ФАЗА 7: АУДИТ ТЕСТОВ

### 7.1 Backend тесты

114 test-файлов локально. Покрывают:
- Auth, RBAC, ABAC, tenant isolation
- Billing, plans, quotas, usage
- AI gateway, ai model registry, ai usage logging
- Admissions, enrollments, grades, scheduling, degree_progress
- Backup, jobs, audit, workflows
- Identity, LDAP, integrations
- Platform KPI, analytics, automation, developer API, federation
- Observability, tenant metadata, webhooks

**Критично**: Тесты **не включены в Docker-образ** → невозможно запустить через `docker compose exec backend pytest` в CI.

### 7.2 Frontend unit тесты (31 файл)

Находятся в `frontend/__tests__/`. Запускаются через `npm run test:frontend` (Vitest).

### 7.3 E2E тесты Playwright (6 файлов)

| Файл | Что тестирует |
|------|--------------|
| `admin-console.spec.ts` | Admin console navigation |
| `copilot-interventions-e2e.spec.ts` | AI copilot + interventions flow |
| `i18n-runtime.spec.ts` | Internationalization |
| `interventions.spec.ts` | Interventions workflow |
| `phase8-network-forensics.spec.ts` | Network forensics |
| `role-zones.spec.ts` | Role-based access zones |

---

## ФАЗА 8: ФИНАЛЬНЫЙ ВЕРДИКТ

См. отдельный реестр финального удаления: `CLEANUP_ENDGAME_TRACKER.md`.
В этом реестре фиксируются только кандидаты на удаление после полной стабилизации.

### ИТОГОВАЯ ТАБЛИЦА ПРОБЛЕМ

| ID | Приоритет | Категория | Описание | Файл/Путь |
|----|-----------|-----------|---------|----------|
| P0-1 | **P0** | Security | `/docs`, `/openapi.json`, `/redoc` без auth | nginx.conf + FastAPI |
| P0-2 | **P0** | Data | Metrics schema drift: UI показывает null/undefined | `modules/platform/health/types.ts` + `hooks.ts` |
| P0-3 | **P0** | CI/CD | Тесты не в Docker-образе — CI нерабочий | `backend/Dockerfile` |
| P1-1 | P1 | Architecture | Legacy `/app/admin/` zone — живой дубль console | `frontend/app/admin/` |
| P1-2 | P1 | Security | `admissions/page.tsx` — нет permission guard | `app/(admin)/console/admissions/page.tsx` |
| P1-3 | P1 | Security | `platform/page.tsx` — нет permission guard | `app/(admin)/console/platform/page.tsx` |
| P1-4 | P1 | Architecture | Dual legacy/new API routers активны | `backend/app/main.py:235-241` |
| P1-5 | P1 | Config | `ENVIRONMENT`, `ALLOW_ORIGINS` не заданы — CORS риск | `.env` / config.py |
| P1-6 | P1 | Data | `outbox_backlog == event_queue_size` — одни данные | `backend/app/platform/router_ops.py:56-57` |
| P1-7 | P1 | Feature | 4 из 6 job handlers — заглушки | `backend/app/modules/jobs/worker.py:50-55` |
| P1-8 | P1 | Ops | Worker/Scheduler — нет видимых итераций в логах | worker/scheduler containers |
| P2-1 | P2 | Legacy | 5 дублей legacy `/api/admin/university/*` роутеров | backend/main.py |
| P2-2 | P2 | Legacy | `identity_phase1_router` — "phase1" в продакшн коде | identity module |
| P2-3 | P2 | UI | `enrollments/page.tsx` — READ не защищён guard | enrollments page |
| P2-4 | P2 | Info leak | `/api/auth/modes` раскрывает конфиг auth без auth | backend auth router |
| P3-1 | P3 | Dead code | `university_core/service.py` — нет роутера, нет вызовов | backend/modules/ |
| P3-2 | P3 | Dead code | Job placeholders `sync`, `ldap.sync` — зарегистрированы | worker.py |
| P3-3 | P3 | Tech debt | `admin-legacy.css` + `i18n/admin.ts` — orphan files | frontend/app/admin/ |

---

### ЧТО НЕ ТРОГАТЬ

1. **nginx BFF routing** (`location ^~ /api/bff/`) — исправлено в предыдущей сессии, работает
2. **JWT система** — `JWT_SECRET` задан корректно, HMAC-HS256 реализован правильно
3. **Alembic миграции** — все 54 применены, голова актуальна
4. **RBAC/ABAC core** (`rbac/security.py`, `rbac/abac.py`) — корректно реализован, не трогать без глубокого аудита
5. **SSL/TLS конфигурация nginx** — TLSv1.2+1.3, HSTS — корректно
6. **`/api/v1/internal/` и `/metrics` nginx ACL** — RFC1918 ограничения правильные
7. **BFF proxy** (`bff-proxy.ts`) — маппинг путей корректный
8. **Ops Summary endpoint** (`/api/v1/platform/ops/summary`) — правильно реализован и подключён в `/console/ops/`

---

### ПЛАН РЕМЕДИАЦИИ (приоритизированный)

#### P0 — Сегодня, до любого production трафика

**P0-1: Закрыть `/docs`, `/openapi.json`, `/redoc`**
```nginx
# nginx.conf — добавить ДО location /api/
location ~ ^/(docs|redoc|openapi\.json)$ {
  allow 127.0.0.1;
  allow 10.0.0.0/8;
  allow 172.16.0.0/12;
  allow 192.168.0.0/16;
  deny all;
  set $backend_upstream http://backend:8000;
  proxy_pass $backend_upstream;
  ...
}
```
или отключить FastAPI docs через `app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)` в production.

**P0-2: Исправить Metrics schema drift**
Вариант A: Заменить `useMetrics()` на `useOpsMetrics()` (уже правильно работает в `/console/ops/`).  
Вариант B: Обновить тип `Metrics` в `types.ts` под реальный `/api/v1/platform/ops/summary`.

**P0-3: Добавить тесты в Docker-образ**
```dockerfile
# backend/Dockerfile — добавить после COPY app
COPY tests ./tests
COPY pytest.ini ./pytest.ini
```

#### P1 — В течение sprint

**P1-1**: Принять решение по legacy `/app/admin/` zone — либо deprecate + redirect → `/console`, либо задокументировать как "legacy self-hosted admin".

**P1-2**: Добавить `RequirePermission` wrapper в `admissions/page.tsx`:
```tsx
// Вверху компонента:
<RequirePermission permission={PERMISSIONS.ADMISSIONS_READ}>
  {/* существующий JSX */}
</RequirePermission>
```

**P1-3**: Аналогично для `platform/page.tsx`.

**P1-5**: Задать `ENVIRONMENT=production` и `ALLOW_ORIGINS=https://your-domain.com` в `.env`.

**P1-6**: Исправить дублирование в `router_ops.py` — `event_queue_size` должен иметь своё значение или убрать один из двух полей.

**P1-7**: Реализовать или явно задокументировать plan `sync`, `ldap.sync`, `ai.generate`, `report.generate` handlers.

#### P2 — Backlog

- Создать план удаления legacy `/api/admin/university/*` роутеров
- Переименовать `identity_phase1_router` → `identity_self_service_router` или подходящее
- Добавить guard на `enrollments/page.tsx` READ view
- Оценить раскрытие `/api/help/topics` и `/api/auth/modes`

#### P3 — Tech debt backlog

- Удалить или реализовать `university_core/service.py`
- Очистить job placeholder handlers или реализовать
- Архивировать `admin-legacy.css`

---

### АРХИТЕКТУРНЫЕ НАБЛЮДЕНИЯ

1. **Два параллельных admin интерфейса** — legacy `/admin/` и новый `/console/` — требуют стратегического решения о миграции
2. **Platform layer API** (`/api/v1/admin/`) правильно спроектирован и хорошо покрыт тестами
3. **BFF proxy** — чистая архитектура, правильно добавляет JWT к upstream запросам
4. **ABAC** реализован для student/enrollment/grade/course ownership — хорошая практика
5. **Middleware** разделяет `/console/*` (token-only) и role-portals (full backend check) — разумный компромисс latency vs security, но console RBAC полиси зависит только от per-page guard
6. **Tenant isolation** — реализована через schema-per-tenant, проверена в тестах
7. **Ops monitoring** — `/console/ops/` и `/api/v1/platform/ops/summary` хорошо связаны, но `event_queue_size == outbox_backlog` — data quality issue

---

*Аудит проведён без изменений кода. Все находки основаны на чтении файлов и runtime проверках.*
