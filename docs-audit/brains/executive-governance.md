# Brain: Executive Governance

[← Каталог Brain](README.md) · Модуль: [../modules/executive-governance.md](../modules/executive-governance.md)

Модуль: `backend/app/modules/executive_governance/` · Prefix `/api/v1/executive-governance` · A‑048

## Назначение
Brain‑вертикаль управленческого уровня: агрегирует KPI и риски всех вертикалей для руководства вуза.

## Функции
Executive Control Tower summary · decision registry · risk heatmap · KPI performance · strategic initiatives · rector dashboard · meeting protocols · assignment execution.

## Входные данные
Высокоуровневые governance‑сигналы всех вертикалей; KPI‑снапшоты (`TenantMetricSnapshotModel`); риски доменов.

## Выходные данные
Executive‑дашборды, decision registry, risk heatmap, стратегические эскалации, `executive-kpi/{tenant}` (из Brain Core).

## Связанный Runtime Shell
`ExecutiveGovernanceRuntimeShellPage` (`/console/executive-governance`): стратегические инициативы, KPI, meeting protocols, риски, decision registry, executive assignments.

## Runtime‑реализации (A‑048)
executive_governance runtime shell, executive_decision_registry, meeting_protocol, assignment_execution, executive_control_tower, strategic_initiative, kpi_performance, executive_risk.

## Проблемы
Историческое закрытие (`A-034`/`A-048`), не реверифицировано. Governance‑console частичный.
