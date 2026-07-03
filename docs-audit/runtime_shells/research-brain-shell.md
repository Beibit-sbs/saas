# Runtime Shell: Research Brain

[← Каталог Runtime Shells](README.md)

## Назначение
Дашборд исследований: портфель, реестр исследователей, наукометрия, research risk.

## Страницы
`/console/research-brain`, `/console/research-science/*` (~7).

## Backend
`research_science/runtime_shell_router.py` + `router.py` (Prefix `/api/admin/research-science`).

## Frontend
`frontend/modules/research-brain/` — `ResearchBrainRuntimeShellPage`, `ResearchBrainResearchersPage`, `ResearchBrainScientometricsPage`, `ResearchBrainRiskPage`, `ResearchBrainDashboardPage` (`page.tsx`), `api.ts`.

## Permissions
`research_science.*` (`projects.*`, `publications.*`, `ethics.*`, `grants.*`, `supervision.*`). Роли: `research_science_admin`, `auditor`.

## Связанные Brain Modules
[Research Science Brain](../brains/research-science.md), [Brain Core](../brains/brain-core.md).
