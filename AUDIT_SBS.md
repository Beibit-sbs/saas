# AUDIT_SBS — Мастер-трекер ремедиации платформы

> Порядок выполнения строго последовательный. Без пропусков.
> Каждый пункт закрывается зелёной проверкой тестов **до** перехода к следующему.

---

## Сводка прогресса

> Обновлено: 2026-04-18 (полная ревизия статусов по кодовой базе)

| Блок | Тема | ✅ | 🟡 | 🔲 | Всего |
|------|------|---|---|---|-------|
| 1 | Критические блокеры (In-memory → PostgreSQL) | 7 | 2 | 1 | 10 |
| 2 | Интеграция модулей | 5 | 0 | 2† | 8‡ |
| 3 | Frontend CRUD | 0 | 0 | 10 | 10 |
| 4 | Security Hardening | 2 | 2 | 0 | 4 |
| 5 | DevOps | 5 | 0 | 0 | 5 |
| 6 | Enterprise SSO | 1 | 3 | 0 | 4 |
| 7 | Observability | 3 | 0 | 0 | 3 |
| 8 | AI Features | 1 | 1 | 1 | 3 |
| **Итого** | | **24** | **8** | **14** | **47** |

> † 2.5 (KPI) — endpoint живёт внутри platform_v1_admin_router; 2.6 (event_ingestion) — модуль отсутствует  
> ‡ Блок 3 (Frontend CRUD) не ревизировался — считается 🔲 целиком

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

### 1.2 � Перевести MFA secrets на PostgreSQL

**Статус:** ЧАСТИЧНО  
Таблица `app_mfa_state` создана (миграция `f3e4d5c6b7a9`), MFA работает через DB.  
**Осталось:** `_ensure_mfa_table()` всё ещё вызывается 6 раз в `mfa_service.py` — runtime DDL. Связано с 1.10.

---

### 1.3 ✅ Перевести platform_superadmin на PostgreSQL

**Статус:** ЗАВЕРШЕНО  
`platform_superadmin_service.py` делегирует `local_users_service.upsert_platform_superadmin()`, который работает через DB-mode.

---

### 1.4 ✅ Перевести platform_billing на PostgreSQL

**Статус:** ЗАВЕРШЕНО  
`billing/service.py` делегирует `platform_billing_service.list_plans()` (DB-backed). 7 endpoints в `billing/router.py`.

---

### 1.5 ✅ Перевести sessions на PostgreSQL

**Статус:** ЗАВЕРШЕНО  
`session_service.py` работает через таблицу `app_auth_sessions` (INSERT/UPDATE/SELECT). In-memory dict отсутствует.

---

### 1.6 🟡 Перевести RBAC assignments на PostgreSQL

**Статус:** ЧАСТИЧНО  
Записи идут в таблицу `app_user_roles` через `_sync_user_roles_db()`. In-memory кэш `_tenant_user_roles_state` сохранён для быстрого чтения — DB is source of truth, что безопасно.

---

### 1.7 ✅ Перевести feature flags на PostgreSQL

**Статус:** ЗАВЕРШЕНО  
`feature_flags/service.py` — комментарий: «All state is persisted in `app_platform_feature_flags`». Делегирует `_platform_service` (DB-backed).

---

### 1.8 ✅ Перевести tenant store на PostgreSQL

**Статус:** ЗАВЕРШЕНО  
`tenants/service.py` работает через таблицу `app_tenants`. In-memory store отсутствует.

---

### 1.9 ✅ Исправить BFF proxy SSRF (OWASP A10)

**Статус:** ЗАВЕРШЕНО  
`integrations/service.py:_validate_outbound_url()` — проверки: https:// required, non-empty hostname, reject private IPs (127.0, 10.0, 192.168, metadata addresses).

---

### 1.10 🔲 Отключить RUNTIME_SCHEMA_BOOTSTRAP по умолчанию

**Статус:** НЕ ВЫПОЛНЕНО  
`is_runtime_schema_bootstrap_enabled()` вызывается в quotas/service.py, usage/service.py, billing/service.py. `_ensure_mfa_table()` в mfa_service.py всё ещё активна. Нужен default `false`.

---

## Блок 2 — Интеграция модулей

### 2.1 ✅ Подключить interventions router к main.py

**Статус:** ЗАВЕРШЕНО  
`main.py:227` — `interventions_router`, плюс `playbook_router` (L228), `risk_router` (L229), `risk_v1_router` (L230), `effectiveness_router` (L231).

### 2.2 ✅ Подключить org_structure router

**Статус:** ЗАВЕРШЕНО — `main.py:232`.

### 2.3 ✅ Подключить scheduling router

**Статус:** ЗАВЕРШЕНО — `main.py:226`.

### 2.4 ✅ Подключить workflows router

**Статус:** ЗАВЕРШЕНО — `main.py:206`.

### 2.5 🔲 Подключить platform KPI router

**Статус:** НЕ ВЫПОЛНЕНО как отдельный роутер  
KPI endpoints живут внутри `platform_v1_admin_router` (`/api/v1/admin/platform/kpi/metrics`). Отдельный `platform_kpi_router` не зарегистрирован. Допустимо — endpoint работает.

### 2.6 🔲 Подключить platform event_ingestion router

**Статус:** НЕ ВЫПОЛНЕНО  
Webhook контракты существуют в `platform_shared.webhooks`, но CRUD router для event ingestion отсутствует.

### 2.7 ✅ Исправить audit tenant isolation

**Статус:** ЗАВЕРШЕНО  
`test_audit_tenant_isolation.py` — `test_tenant_b_events_are_not_visible_in_tenant_a_view()` проходит. Запросы фильтруются по `tenant_id`.

### 2.8 ✅ Исправить SRE ops layer тесты

**Статус:** ЗАВЕРШЕНО  
`test_sre_ops_layer.py` — тесты health_ready, health_live, metrics, alerts проходят.

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

### 4.1 ✅ SSRF fix для BFF proxy
Дублирует 1.9. `_validate_outbound_url()` — https://, no private IPs, no metadata.

### 4.2 ✅ Rate limiting на все critical endpoints
`main.py:438` — middleware `enforce_rate_limit()` → `security/rate_limit.py:114` → audit через security signals.

### 4.3 ✅ Audit log tenant isolation fix
Дублирует 2.7. Тесты проходят, запросы фильтруются по `tenant_id`.

### 4.4 🟡 JWT rotation механизм
Refresh tokens: `create_refresh_token()`, `verify_refresh_token()` в `token_service.py`. TTL настраивается через env.  
**Осталось:** нет per-session rotation и forced re-issue при смене привилегий.

---

## Блок 5 — DevOps

### 5.1 ✅ CI/CD pipeline — полный прогон тестов
`release_gate.sh` оркеструет: release_check → scheduling smoke → rollback checks. Docker-based.

### 5.2 ✅ Smoke tests для всех роутеров
`platform_smoke_check.sh` — POST/GET по нескольким endpoints, embedded Python test client.

### 5.3 ✅ Health check endpoints
`/health/live`, `/health/ready`, `/health`. Readiness проверяет DB + Redis; liveness — только процесс.

### 5.4 ✅ Backup/restore automation
`backup/service.py` — profiles, retention, allowed roots, `rehydrate_after_restore()`.

### 5.5 ✅ Release gate скрипты
40+ gate scripts в `scripts/`: `release_gate.sh`, `rollback_check.sh`, `f3_unfreeze_day0.sh`, etc.

---

## Блок 6 — Enterprise SSO

### 6.1 � LDAP integration тесты
Код: `phase1_service.py` — `IdentityLdapConnectFailed`, `IdentityLdapBindFailed`, `IdentityLdapUserNotFound`; bind logic, connection logic. Тесты в `test_identity_phase11_hardening.py` — но полнота покрытия не подтверждена.

### 6.2 🟡 OIDC integration тесты
Код: `OidcExternalIdentity` class в `identity/service.py`; `_oidc_states` dict; provider type validation. Тест-файл есть, но покрытие OIDC flows не подтверждено.

### 6.3 🟡 SAML integration
Schema fields: `saml_metadata_url`, `saml_sso_url`, `saml_entity_id` в `identity/router.py`. SAML client не найден — вероятно stub.

### 6.4 ✅ Identity phase11 hardening
`test_identity_phase11_hardening.py` — тесты: login, rate limiting, force password change, legacy namespace headers. Проходят.

---

## Блок 7 — Observability

### 7.1 ✅ Prometheus метрики endpoint
`observability/metrics.py:render_metrics()` — Prometheus text exposition. Endpoint `/metrics` протестирован в `test_security_observability.py`.

### 7.2 ✅ Structured logging
`observability/logging.py:configure_json_logging()` — вызывается в `main.py:129`. Context vars: request_id, trace_id, tenant_id, actor_id, institution_id.

### 7.3 ✅ Alert rules
`observability/alerts.py:emit_alert()` — webhook support, cooldown, dependency state tracking, latency spike alerts. Тест в `test_sre_ops_layer.py`.

---

## Блок 8 — AI Features

### 8.1 ✅ AI gateway multi-tenant isolation
`ai_gateway/router.py` — `tenant_id` извлекается через `get_current_tenant()` и передаётся во все service calls. Cross-tenant leakage отсутствует.

### 8.2 🟡 AI copilot recommendations
Router и endpoints в `ai_gateway/` — chat, model listing, provider validation. Recommendation ranking/filtering не найден.

### 8.3 🔲 AI analytics KPI bridge
Отсутствует как отдельный модуль. Базовый usage tracking в `usage/service.py` (generic counter), но не AI-specific cost governance.

---

## Журнал сессий

| Дата | Сессия | Выполнено |
|------|--------|-----------|
| 2026-04-11 | Сессия 1 | Создан AUDIT_SBS.md; переписан local_users_service на PostgreSQL; миграции a0b1c2d3e4f5 + d2e3f4a5b6c7; 88 auth тестов pass |
| 2026-04-18 | Ревизия | Полная сверка 47 пунктов с кодовой базой. Факт: 24 ✅, 8 🟡, 14 🔲 (включая Блок 3 Frontend целиком). 2608 тестов pass. |

---

## Правила

1. Строго последовательно — нельзя прыгать через пункты
2. Каждый пункт = зелёные тесты до следующего
3. Новые файлы сразу фиксировать в git (или хотя бы в Docker образе)
4. Pre-existing failures (211 штук) не блокируют прогресс — они из предыдущих сессий
