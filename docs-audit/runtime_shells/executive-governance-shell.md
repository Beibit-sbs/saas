# Runtime Shell: Executive Governance

[← Каталог Runtime Shells](README.md)

## Назначение
Исполнительный дашборд руководства: стратегические инициативы, KPI, meeting protocols, риски, decision registry, executive assignments.

## Страницы
`/console/executive-governance` (runtime shell), `/console/executive-control-tower/*` (strategy, sla-risk, audit, metric-registry, documents, departments, assignments), `/console/my-assignments/*`.

## Backend
`executive_governance/runtime_shell_router.py` (Prefix `/api/v1/executive-governance`); `executive_control_tower/router.py`; `rector_assignment_workflow/router.py`.

## Frontend
`frontend/modules/executive-governance/` — `ExecutiveGovernanceRuntimeShellPage` (`page.tsx`), `api.ts`; `frontend/modules/executive-control-tower/`.

## Permissions
`admin.executive_control_tower.*.read`, `admin.rector_assignments.*`. Роли: `rector`, `executive_control_tower`, `auditor`.

## Связанные Brain Modules
[Executive Governance Brain](../brains/executive-governance.md), [Brain Core](../brains/brain-core.md) (`executive-kpi/{tenant}`). Питается KPI‑агрегацией всех вертикалей.
