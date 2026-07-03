# Runtime Shell: Reporting Runtime (Ministry)

[← Каталог Runtime Shells](README.md)

## Назначение
Дашборд регуляторной отчётности: реестр/расписание отчётов, готовность Ministry/NOBD/ranking/regulatory, delivery‑аудит.

## Страницы
`/console/reporting-runtime` (навигация из tenant admin).

## Backend
`reporting_runtime/runtime_shell_router.py` (Prefix `/api/v1/reporting`) + 8 сервисов (accreditation, compliance, ministry, nobd, ranking, regulatory, dashboard, registry).

## Frontend
`frontend/modules/reporting-runtime/` — `ReportingRuntimeShellPage` (`page.tsx`), `api.ts` (`getRuntimeShell()`).

## Permissions
`reporting_runtime/permissions.py`. Роли: reporting‑admin, `rector`/`executive`, `auditor`.

## Связанные Brain Modules
[Reporting/Ministry Brain](../brains/reporting-ministry.md), [Quality Accreditation Brain](../brains/quality-accreditation.md). Интеграции: `regulatory_reporting_integration`, `government_services_integration` (L2).
