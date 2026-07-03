# API‑группа: Platform (`/api/v1/*`, `/api/dev`, `/api/v2/semantic`)

[← Каталог API](README.md) · Модуль: [../modules/platform-core.md](../modules/platform-core.md)

8 платформенных роутеров (`app/platform/router_*.py`).

## Роутеры

| Роутер | Префикс | Назначение | Auth |
|--------|---------|-----------|------|
| `router_admin` | `/api/v1/admin` | Тенанты, флаги, KPI, jobs, webhooks, analytics | JWT + RBAC |
| `router_public` | `/api/v1/public` | Зарезервировано (пусто) | — |
| `router_internal` | `/api/v1/internal` | Workers, jobs, events, webhooks, rehydration | Bearer scopes |
| `router_mcp` | `/api/v1/internal/mcp` | Интроспекция БД для AI‑copilot (redaction PII) | Bearer |
| `router_ops` | `/api/v1/platform/ops` (+ BFF `/api/bff/v1/platform/ops`) | Ops (health, backlog, latency, backup) | JWT + Ops |
| `router_developer_api` | `/api/dev` | Партнёрские интеграции (analytics, KPI, students/grades) | X‑App‑Key/Secret |
| `router_semantic` | `/api/v2/semantic` | Семантический слой (entities, metrics, dimensions, queries) | JWT + Semantic |

## Admin router — примеры endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| POST/GET | `/api/v1/admin/tenants` (+`/{id}`) | Создать/получить/список тенантов |
| PATCH | `/api/v1/admin/tenants/{id}/settings` | Настройки тенанта |
| POST | `/api/v1/admin/tenants/{id}/suspend|quotas|limits` | Suspend/квоты/лимиты |
| POST/GET/DELETE | `/api/v1/admin/feature-flags` (+`/{tenant}`) | Управление флагами |
| GET | `/api/v1/admin/kpi/dashboard/{tenant_id}` | Rector‑дашборд |
| GET | `/api/v1/admin/kpi/drill-down` | KPI drill‑down |
| POST | `/api/v1/admin/jobs/{job_id}/run|retry` | Триггер/ретрай задачи |
| POST/GET | `/api/v1/admin/notifications` | Диспетч/список уведомлений |
| POST | `/api/v1/admin/webhooks/subscriptions` | Подписка webhook |

## Permissions
`platform.admin.read/write`, `ops.read/write`, `jobs.read/write`, `analytics.data.read/write`, `health.read`, `metrics.read`. Роли: `superadmin`, `platform_admin`, `auditor` (read).
