# Brain: Research Science

[← Каталог Brain](README.md) · Модуль: [../modules/research-science.md](../modules/research-science.md)

Модуль: `backend/app/modules/research_science/` · A‑047

## Назначение
Brain‑вертикаль исследований: портфель, риски грантов/публикаций, наукометрия, этика.

## Функции
Реестр исследователей · наукометрия (scientometrics) · research risk · дашборд · runtime shell.

## Входные данные
Сигналы `research.grant_deadline.approaching`, `research.publication_stagnant`, `research.grant_pipeline.at_risk`, `research.lab_utilization.low`, `research_ethics.*`; данные грантов/публикаций/лабораторий.

## Выходные данные
Решения `research_innovation`, `research_ethics_compliance`; research remediation workflow; уведомления research office.

## Связанный Runtime Shell
`ResearchBrainRuntimeShellPage` (`/console/research-brain`): портфель, исследователи, наукометрия, research risk, дашборд.

## Runtime‑реализации (A‑047)
research_brain runtime shell, researcher_registry, scientometrics, research_risk, research_dashboard.

## Проблемы
Семейство research (`research`, `research_projects`, `research_science`) — пересечение; `innovation_commercialization` не закоммичен (P1). См. `A-047.2` (реконсиляция).
