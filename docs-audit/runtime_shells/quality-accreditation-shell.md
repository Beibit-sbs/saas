# Runtime Shell: Quality Accreditation

[← Каталог Runtime Shells](README.md)

## Назначение
Дашборд качества/аккредитации: baseline‑скор, комплаенс, доказательства, remediation, готовность к отчёту министерству.

## Страницы
`/console/quality-accreditation/runtime-shell` (+ self-assessment, accreditation-evidence, corrective-action, audit-findings, improvement-plan, readiness-monitoring, registry, dashboard).

## Backend
`quality_accreditation/runtime_shell_router.py` + 8 под‑роутеров (accreditation_evidence, accreditation_registry, audit_findings, corrective_action, dashboard, improvement_plan, readiness_monitoring, self_assessment).

## Frontend
`frontend/modules/quality-accreditation/` — `QualityAccreditationRuntimeShellPage` (`pages.tsx`), `api.ts` (`getQualityAccreditationRuntimeShell()`), `boundaryLabels.ts`.

## Permissions
`quality_accreditation.*` (`self_assessment.*`, `accreditation_evidence.create`, `corrective_action.*`). Роли: `quality_accreditation_admin`, `auditor`.

## Связанные Brain Modules
[Quality Accreditation Brain](../brains/quality-accreditation.md), [Reporting/Ministry Brain](../brains/reporting-ministry.md).
