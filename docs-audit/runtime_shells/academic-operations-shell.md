# Runtime Shell: Academic Operations

[← Каталог Runtime Shells](README.md)

## Назначение
Операционный дашборд учебного процесса: curriculum, scheduling, enrollment‑метрики, календарь, safety‑gates.

## Страницы
`/console/academic-operations/runtime-shell` (+ ~19 под‑страниц: academic-registry, curriculum, gradebook, internships, retakes, teaching-load, timetable, cohorts, assessment, attendance, signals, dashboard, matrix).

## Backend
`academic_operations_runtime/runtime_shell_router.py` (Prefix `/api/v1/academic-operations`, `GET /runtime-shell`, permission `academic_operations.summary.read`) + 9 под‑роутеров (registry, assessment, attendance, curriculum, internship, timetable, teaching_load, dashboard, signals).

## Frontend
`frontend/modules/academic-operations-runtime/` — `AcademicOperationsRuntimeShellPage` (`pages.tsx`), `api.ts` (`ACADEMIC_OPERATIONS_RUNTIME_API_BASE`).

## Permissions
`academic_operations.summary.read` (+ `academic_groups.*`, `cohorts.*`). Роли: `academic_operations_admin`, registrar, `auditor`.

## Связанные Brain Modules
[Academic Operations Brain](../brains/academic-operations.md), [Brain Core](../brains/brain-core.md). Human‑approved timetable workflow.
