# AUDIT_SBS — Мастер-трекер ремедиации платформы

> Порядок выполнения строго последовательный. Без пропусков.
> Каждый пункт закрывается зелёной проверкой тестов **до** перехода к следующему.

---

## Сводка прогресса

| Блок | Тема | Готово | Всего |
|------|------|--------|-------|
| 1 | Критические блокеры (In-memory → PostgreSQL) | 1 | 10 |
| 2 | Интеграция модулей | 0 | 8 |
| 3 | Frontend CRUD | 0 | 10 |
| 4 | Security Hardening | 0 | 4 |
| 5 | DevOps | 0 | 5 |
| 6 | Enterprise SSO | 0 | 4 |
| 7 | Observability | 0 | 3 |
| 8 | AI Features | 0 | 3 |
| **Итого** | | **1** | **47** |

---

## Блок 0 — Базовое состояние системы

- Бэкенд: FastAPI, 35+ роутеров, PostgreSQL (SQLAlchemy + psycopg), Redis
- Фронтенд: Next.js 14, TypeScript
- БД: PostgreSQL 16 (контейнер ai-db-1)
- Docker: ai-db-1, ai-redis-1, ai-backend-1, ai-scheduler-1
- Тесты (последнее состояние): 88 auth/local_users → все passes; полный сюит 1091 passed / 211 pre-existing failures

---

## Блок 1 — Критические блокеры: In-memory → PostgreSQL

### 1.1 ✅ Перевести local_users storage на PostgreSQL

**Статус:** ЗАВЕРШЕНО  
**Дата:** 2026-04-11  
**Файлы:**
- `backend/alembic/versions/a0b1c2d3e4f5_merge_all_feature_heads.py` — merge 8 branch heads
- `backend/alembic/versions/d2e3f4a5b6c7_add_app_local_users_table.py` — таблица `app_local_users` + data migration из JSON blob
- `backend/app/modules/auth/local_users_service.py` — переписан (604 строки): DB-mode через `get_raw_conn()`, in-memory fallback для тестов через проверку `os.environ.get("DATABASE_URL")`

**Итог:** 13/13 local_users тестов pass; 88/88 auth тестов pass; регрессий нет.

---

### 1.2 🔲 Перевести MFA secrets на PostgreSQL

MFA уже использует `app_mfa_state` таблицу (миграция `f3e4d5c6b7a9`). Нужно убрать `_ensure_mfa_table()` runtime DDL (связано с 1.10).

---

### 1.3 🔲 Перевести platform_superadmin на PostgreSQL

`upsert_platform_superadmin()` уже работает через новый DB-mode `local_users_service`. Проверить и отметить.

---

### 1.4 🔲 Перевести platform_billing на PostgreSQL

Проверить `billing/service.py` на in-memory stores. Найти `billing_repository.py`.

---

### 1.5 🔲 Перевести sessions на PostgreSQL

`session_service.py` — проверить есть ли in-memory dict, добавить DB-backend аналогично mfa_service.

---

### 1.6 🔲 Перевести RBAC assignments на PostgreSQL

`rbac/service.py` — проверить `_user_roles` структуру.

---

### 1.7 🔲 Перевести feature flags на PostgreSQL

`feature_flags/service.py` — проверить in-memory `_flags`.

---

### 1.8 🔲 Перевести tenant store на PostgreSQL

`tenants/service.py` — проверить in-memory.

---

### 1.9 🔲 Исправить BFF proxy SSRF (OWASP A10)

Проверить proxy endpoint на SSRF. Валидация URL против allowlist.

---

### 1.10 🔲 Отключить RUNTIME_SCHEMA_BOOTSTRAP по умолчанию

Убрать `_ensure_mfa_table()` из `mfa_service.py`. Установить дефолт `RUNTIME_SCHEMA_BOOTSTRAP=false`.

---

## Блок 2 — Интеграция модулей

### 2.1 🔲 Подключить interventions router к main.py

404 на `/api/interventions/*` — роутер не подключён или путь неверный.

### 2.2 🔲 Подключить org_structure router

404 на `/api/org-structure/*`.

### 2.3 🔲 Подключить scheduling router

Проверить endpoint availability.

### 2.4 🔲 Подключить workflows router

### 2.5 🔲 Подключить platform KPI router

404 на `/api/platform/kpi/*`.

### 2.6 🔲 Подключить platform event_ingestion router

### 2.7 🔲 Исправить audit tenant isolation

`test_audit_tenant_isolation.py` — 1 test failure.

### 2.8 🔲 Исправить SRE ops layer тесты

`test_sre_ops_layer.py` — 3 test failures (health_ready, metrics).

---

## Блок 3 — Frontend CRUD

### 3.1 🔲 Local users CRUD страница
### 3.2 🔲 Tenants management страница
### 3.3 🔲 RBAC assignments UI
### 3.4 🔲 Feature flags UI
### 3.5 🔲 Billing/plans UI
### 3.6 🔲 Interventions UI
### 3.7 🔲 Org structure UI
### 3.8 🔲 Scheduling UI
### 3.9 🔲 Workflows UI
### 3.10 🔲 Platform KPI dashboard

---

## Блок 4 — Security Hardening

### 4.1 🔲 SSRF fix для BFF proxy
### 4.2 🔲 Rate limiting на все critical endpoints
### 4.3 🔲 Audit log tenant isolation fix
### 4.4 🔲 JWT rotation механизм

---

## Блок 5 — DevOps

### 5.1 🔲 CI/CD pipeline — полный прогон тестов
### 5.2 🔲 Smoke tests для всех роутеров
### 5.3 🔲 Health check endpoints
### 5.4 🔲 Backup/restore automation
### 5.5 🔲 Release gate скрипты

---

## Блок 6 — Enterprise SSO

### 6.1 🔲 LDAP integration тесты
### 6.2 🔲 OIDC integration тесты
### 6.3 🔲 SAML integration
### 6.4 🔲 Identity phase11 hardening

---

## Блок 7 — Observability

### 7.1 🔲 Prometheus метрики endpoint
### 7.2 🔲 Structured logging
### 7.3 🔲 Alert rules

---

## Блок 8 — AI Features

### 8.1 🔲 AI gateway multi-tenant isolation
### 8.2 🔲 AI copilot recommendations
### 8.3 🔲 AI analytics KPI bridge

---

## Журнал сессий

| Дата | Сессия | Выполнено |
|------|--------|-----------|
| 2026-04-11 | Сессия 1 | Создан AUDIT_SBS.md; переписан local_users_service на PostgreSQL; миграции a0b1c2d3e4f5 + d2e3f4a5b6c7; 88 auth тестов pass |

---

## Правила

1. Строго последовательно — нельзя прыгать через пункты
2. Каждый пункт = зелёные тесты до следующего
3. Новые файлы сразу фиксировать в git (или хотя бы в Docker образе)
4. Pre-existing failures (211 штук) не блокируют прогресс — они из предыдущих сессий
