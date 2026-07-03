# Модуль: Academic Operations (Академические операции)

[← Каталог модулей](README.md) · [Индекс](../README.md)

Backend: `backend/app/modules/academic_operations/`, `backend/app/modules/academic_operations_runtime/`
Frontend: `frontend/modules/academic-operations/`, `frontend/modules/academic-operations-runtime/`
Вертикаль: **V03 Academic Operations** · Brain: [Academic Operations Brain](../brains/academic-operations.md)

## Назначение
Операционное управление учебным процессом: реестр программ/курсов, учебные группы и когорты, gradebook‑метаданные, учебный план, расписание, посещаемость, оценивание, нагрузка ППС, стажировки.

## Бизнес‑функции
Академ‑группы/когорты · gradebook · retake · timetable · attendance · assessment/learning outcomes · teaching load · internship placements · сигналы риска · дашборд.

## Пользователи (роли)
`academic_operations_admin`, `registrar`, `faculty`; `auditor` (read); `rector`/`executive` (агрегаты).

## Основной функционал
Управление реестром, когортами, расписанием и нагрузкой; агрегированный runtime‑дашборд; сигналы (`academic_operations_signals_runtime`).

## Страницы / Маршруты / Runtime Shell / Dashboard
- `/console/academic-operations/*` (~19: academic-registry, curriculum, gradebook, internships, retakes, teaching-load, timetable, cohorts, assessment, attendance, signals, dashboard, matrix).
- **Runtime Shell:** `/console/academic-operations/runtime-shell` (`AcademicOperationsRuntimeShellPage`).
- **Dashboard:** `academic_operations_dashboard_runtime`.

## Backend
- **Router:** `academic_operations/router.py` + 10 runtime‑роутеров (`academic_operations_runtime/*`): dashboard, signals, assessment, attendance, academic_registry, curriculum, internship, runtime_shell, teaching_load, timetable.
- **Services:** `academic_operations/service.py` + runtime‑сервисы.
- **Models:** `academic_operations/models.py` (`academic_operations_*`).
- **DTO:** `schemas.py`. **Permissions:** `permissions.py` (58+).

## Database
Таблицы `academic_operations_*`; читает `university_courses`, `university_programs`, `university_enrollments`, `attendance_records`, `attendance_sessions`. Enum статусов; alert‑таблицы для сигналов.

## API
Префикс `/api/admin/academic-operations` + под‑пути (`/registry`, `/curriculum`, `/timetable`, `/attendance`, `/assessment`, `/teaching-load`, `/internship`, `/signals`, `/dashboard`, `/runtime-shell`). Permission `academic_operations.summary.read` и т.д.

## Permissions
`academic_operations.*` (overview, dashboard, academic_groups.*, cohorts.*, gradebook_metadata.*), bridges (student_lifecycle, document_workflow).

## Связанные модули
`courses`, `programs`, `enrollments`, `scheduling`, `grades`, `attendance`, `interventions`, `student_success_runtime`, `brain_core`, `document_workflow_os` (bridge), `student_lifecycle` (bridge).

## Workflow
Академический жизненный цикл ([../08_WORKFLOWS.md](../08_WORKFLOWS.md) §9.2), human‑approved timetable ([../08_WORKFLOWS.md](../08_WORKFLOWS.md) §9.4).

## Brain / AI
Brain‑вертикаль Academic Operations: сигналы `faculty.workload_overload.detected`, `scheduling.section.conflict_detected`, `enrollment.capacity_risk.detected`, `courses.status.risk_detected`; решения `faculty_overload`, `section_conflict`, `enrollment_capacity_risk`, `room_allocation_recommendation`. AI — через Brain reasoning.

## Интеграции / Background Jobs / Feature Flags
Интеграции: события в Brain/KPI, потенциально LMS (L2). Jobs: `academic_risk_detection`, `composite_early_warning_sweep`. Флаги: динамические.

## Проблемы / Рекомендации
- **Дубль‑пара** `academic_operations` vs `academic_operations_runtime` (последний без `router.py` в основном пакете) — консолидировать.
- Safety‑gates runtime — metadata‑only (нет живой синхронизации). **Рекомендация:** унифицировать пакеты, довести провайдер‑синхронизацию.
