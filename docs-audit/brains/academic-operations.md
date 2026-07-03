# Brain: Academic Operations

[← Каталог Brain](README.md) · Модуль: [../modules/academic-operations.md](../modules/academic-operations.md)

Модуль: `backend/app/modules/academic_operations_runtime/` · Prefix `/api/v1/academic-operations`

## Назначение
Brain‑вертикаль операционного управления учебным процессом (расписание, нагрузка, курсы, посещаемость, стажировки).

## Функции
Академ‑реестр · assessment/learning outcomes · attendance · curriculum · internship · timetable/room allocation · teaching load · дашборд · сигналы.

## Под‑роутеры (9)
`academic_registry`, `assessment`, `attendance`, `curriculum`, `internship`, `timetable`, `teaching_load`, `dashboard`, `signals` + `runtime_shell_router`.

## Входные данные
Сигналы `faculty.workload_overload.detected`, `scheduling.section.conflict_detected`, `scheduling.room_allocation.*`, `enrollment.capacity_risk.detected`, `courses.status.risk_detected`, `thesis.*`; данные courses/programs/enrollments/attendance.

## Выходные данные
Решения `faculty_overload`, `section_conflict`, `enrollment_capacity_risk`, `room_allocation_recommendation`, `thesis_delay`, `thesis_governance`; задачи scheduling/enrollment office; дашборд.

## Связанный Runtime Shell
`AcademicOperationsRuntimeShellPage` (`/console/academic-operations/runtime-shell`): curriculum, scheduling, enrollment‑метрики, календарь, safety‑gates (metadata‑only).

## Human gating
Изменения расписания — через human‑approved timetable workflow (запрещены AUTO_APPLY/AUTO_OPTIMIZE). См. [../08_WORKFLOWS.md](../08_WORKFLOWS.md) §9.4.
