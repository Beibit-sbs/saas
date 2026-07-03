# Модуль: Platform Core (Платформенная инфраструктура)

[← Каталог модулей](README.md) · [Индекс](../README.md)

Backend: `backend/app/platform/*`, `backend/app/modules/platform/`, `platform_shared/`, `platform_health/`, `tenants/`, `billing/`, `plans/`, `subscriptions/`, `quotas/`, `usage/`, `invoices/`, `feature_flags/`, `jobs/`, `workflows/`, `federation_management/`, `observability/`, `backup/`, `audit/`

## Назначение
Мультитенантная SaaS‑подложка: тенанты, биллинг, квоты, события, jobs, KPI, уведомления, webhooks, идемпотентность, UoW, feature flags, семантический слой, developer API, MCP.

## Бизнес‑функции
Управление тенантами (settings/quotas/limits/suspend) · биллинг (планы, подписки, инвойсы, usage) · Outbox‑события и webhooks · KPI‑агрегация · фоновые задачи · уведомления · идемпотентность · федерация · developer/semantic/MCP API.

## Пользователи (роли)
`superadmin`, `platform_admin`; `auditor`; developer (партнёрский API).

## Страницы
`/console/platform/*` (control plane, tenants, billing-plans, usage-quotas, feature-flags, [section]), `/console/developer/*`, `/console/health`, `/console/ops`, `/console/billing/*`.

## Backend
- **Платформенные роутеры (8):** `router_admin` (`/api/v1/admin`), `router_public` (`/api/v1/public`), `router_internal` (`/api/v1/internal`), `router_mcp` (`/api/v1/internal/mcp`), `router_ops` (`/api/v1/platform/ops` + BFF), `router_developer_api` (`/api/dev`), `router_semantic` (`/api/v2/semantic`).
- **UoW** (`uow.py`): ~21 репозиторий (tenant, billing, usage, invoice, job, notification, idempotency, analytics, ai_copilot, automation, developer, education_graph, federation, kpi, outbox_event, platform_event, webhook, context…).

## Database
`app_tenants`, `app_platform_tenant_settings`, `app_platform_feature_flags`, `app_platform_plans`, `app_billing_*`, `app_jobs_*`, `app_workflow_*`, outbox/webhook/kpi таблицы, `app_audit_events`.

## API
См. [../05_API.md](../05_API.md) §6.2 (платформенные API).

## Связанные модули
Все доменные модули (инфраструктура). См. [../01_SYSTEM_ARCHITECTURE.md](../01_SYSTEM_ARCHITECTURE.md) §2.9.

## Background Jobs / Feature Flags / Integrations
- Jobs: 9 периодических ([../11_BACKGROUND_JOBS.md](../11_BACKGROUND_JOBS.md)).
- Flags: DB‑backed + кэш ([../10_FEATURE_FLAGS.md](../10_FEATURE_FLAGS.md)).
- Integrations/Webhooks/Developer API ([../09_INTEGRATIONS.md](../09_INTEGRATIONS.md)).

## Проблемы / Рекомендации
- `router_public` пуст (зарезервирован). Планировщик — in‑memory (нет распределённого брокера). Feature flags помечены как scaffold в историческом README. **Рекомендация:** ввести распределённую очередь для jobs, каталог флагов.
