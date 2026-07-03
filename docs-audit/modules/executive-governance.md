# Модуль: Executive Governance / Control Tower

[← Каталог модулей](README.md) · [Индекс](../README.md)

Backend: `executive_governance/`, `executive_control_tower/`, `rector_assignment_workflow/`, `rector_resolution_tracking_workflow/`, `rector_strategy_dashboard/`, `committee_decision_registry/`
Frontend: `frontend/modules/executive-governance/`, `executive-control-tower/`, `rector-assignments/`
Вертикаль: **V01 Executive Governance** · Brain: [Executive Governance Brain](../brains/executive-governance.md)

## Назначение
Управленческий уровень вуза: исполнительные дашборды, реестр решений, cross‑domain risk heatmap, KPI, стратегические инициативы, поручения ректора с SLA.

## Бизнес‑функции
Executive Control Tower summary · decision registry · risk heatmap · KPI performance · strategic initiatives · rector assignments (поручения) · meeting protocols.

## Пользователи (роли)
`rector`, `executive_control_tower`, `admin`; `auditor` (read).

## Страницы / Runtime Shell / Dashboard
- `/console/executive-control-tower/*` (~8: strategy, sla-risk, audit, metric-registry, documents, departments, assignments).
- `/console/executive-governance` (**Runtime Shell** `ExecutiveGovernanceRuntimeShellPage`).
- `/console/rector-assignments`, `/console/my-assignments/*`.

## Backend
- **Router:** `executive_governance/runtime_shell_router.py`; `executive_control_tower/router.py`; `rector_assignment_workflow/router.py`.
- **Permissions:** `executive_control_tower/permissions.py` (`_EXECUTIVE_CONTROL_TOWER_PERMISSIONS`), `rector_assignment_workflow/permissions.py`.

## Database
Метрик‑реестр (`TenantMetricSnapshotModel`), rector‑assignment таблицы (миграции `zq35rs47tu58_a031_1`, `ar46st58uv69_a031_5`), decision registry.

## API
`/api/admin/executive-control-tower`, `/api/v1/executive-governance`, `/api/admin/rector-assignments`. Permissions `admin.executive_control_tower.*.read`, `admin.rector_assignments.*`.

## Связанные модули
Все вертикали (агрегирует KPI/риски), `reporting_runtime`, `brain_core`, `kpi` (platform), `document_decree_correspondence`.

## Workflow
Governance/поручения ([../08_WORKFLOWS.md](../08_WORKFLOWS.md) §9.11).

## Brain / AI
Brain‑вертикаль Executive Governance: высокоуровневые governance‑сигналы всех вертикалей; стратегические эскалации. `executive-kpi/{tenant}` из Brain Core.

## Background Jobs
`kpi_metrics_refresh` (24ч) питает дашборды; `context_rebuild`.

## Проблемы / Рекомендации
- Закрыто исторически (`A-034`/`A-048`), не реверифицировано в последней сессии. **Рекомендация:** реверифицировать KPI‑lineage и evidence drill‑down.
