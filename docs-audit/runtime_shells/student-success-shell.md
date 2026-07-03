# Runtime Shell: Student Success

[← Каталог Runtime Shells](README.md)

## Назначение
Операционный дашборд успеха студента: агрегирует overview, интервенции, сигналы, retention‑риски, статус качества данных.

## Страницы
`/console/student-success`, `/console/student-success/runtime-shell` (+ attendance-risk, academic-risk, advisors, student-registry, student-retention, signals, dashboard, cohorts, interventions).

## Backend
`student_success_runtime/runtime_shell_router.py` (Prefix `/api/v1/student-success`, `GET /runtime-shell`, permission `student_success.summary.read`) + 8 под‑роутеров.

## Frontend
`frontend/modules/student-success/` — `StudentSuccessRuntimeShellPage` (`pages.tsx`), `api.ts` → `/api/v1/student-success/runtime-shell`. Секции: `student_success_overview`, `interventions`, `signals`, `retention_risks`, `safety`.

## Permissions
`student_success.summary.read` (+ доменные `interventions.*`). Роли: advisor, faculty, `student_lifecycle_admin`, `auditor`.

## Связанные Brain Modules
[Student Success Brain](../brains/student-success.md), [Brain Core](../brains/brain-core.md); сигнальный реестр `student_risk_signal_registry` (UCE‑049).
