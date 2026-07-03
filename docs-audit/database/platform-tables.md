# Кластер таблиц: Platform / Auth / Billing

[← Каталог таблиц](README.md) · Модуль: [../modules/platform-core.md](../modules/platform-core.md), [../modules/auth-identity.md](../modules/auth-identity.md)

Платформенные и инфраструктурные таблицы (не всегда tenant‑scoped — часть платформенные).

## Tenant / Platform

| Таблица | Описание | Tenant‑scoped |
|---------|----------|---------------|
| `app_tenants` | Реестр тенантов (slug, name, status, plan_id) | нет (корень) |
| `app_platform_tenant_settings` | Настройки тенанта (JSONB settings/quotas/limits, status) | PK=tenant_id |
| `app_platform_feature_flags` | Feature flags (scope/module/key/enabled/rollout%) | опционально |
| `app_platform_plans` | Тарифные планы | нет |

## Billing

| Таблица | Описание |
|---------|----------|
| `app_billing_plans` | Планы биллинга |
| `app_billing_tenant_subscriptions` | Подписки тенантов (enum BillingSubscriptionStatus) |
| `app_billing_usage_counters` | Счётчики использования |
| `app_billing_invoices` | Инвойсы |

## Auth / Security

| Таблица | Описание |
|---------|----------|
| session/MFA tables | Сессии + MFA (`f3e4d5c6b7a9`) |
| `twofa_enrollments`/`twofa_challenges` | 2FA/TOTP |
| `saml_identity_providers`/`saml_sessions`/`saml_attribute_mappings` | SAML SSO |
| `user_roles`, `role_permissions` | RBAC persistence (tenant‑scoped) |

## Workflows / Jobs / Events / Audit

| Таблица | Описание |
|---------|----------|
| `app_workflow_definitions`/`_versions`/`_triggers`/`_steps`/`_assignees`/`_execution_histories` | Движок workflow |
| `app_jobs_*` | Очередь фоновых задач |
| outbox/webhook/analytics event tables | Event bus (Outbox) + webhooks |
| kpi snapshot tables (`TenantMetricSnapshotModel`, `TenantDashboardSnapshotModel`) | KPI |
| `app_audit_events` | Аудит‑лог (retention до 7 лет) |

## Используется в
Все модули (инфраструктура). См. [../11_BACKGROUND_JOBS.md](../11_BACKGROUND_JOBS.md), [../10_FEATURE_FLAGS.md](../10_FEATURE_FLAGS.md).
