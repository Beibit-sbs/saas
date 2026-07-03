# Модуль: Scheduling / Timetable Workflow (Расписание)

[← Каталог модулей](README.md) · [Индекс](../README.md)

Backend: `scheduling/`, `human_approved_timetable_workflow/`, `timetable_change_proposal/`, `timetable_change_simulation/`, `timetable_approval_queue/`, `timetable_recommendation_bridge/`, `timetable_change_kpi_dashboard/`, `room_booking/`, `equipment_booking/`, `workload_management/`
Frontend: `frontend/modules/scheduling/`, `academic-operations-runtime/`

## Назначение
Формирование и изменение расписания с обнаружением конфликтов, рекомендациями по аудиториям и **обязательным утверждением человеком** (human‑approved timetable workflow).

## Бизнес‑функции
Секции/расписание · обнаружение конфликтов (section/room/equipment/capacity) · рекомендации аудиторий · симуляция what‑if · очередь утверждения · KPI изменений · бронирование аудиторий/оборудования · нагрузка ППС.

## Пользователи (роли)
`academic_operations_admin`, scheduling office, утверждающий (human reviewer); `auditor`.

## Страницы / Dashboard
`/console/scheduling`, `/console/academic-operations/timetable`, `/console/my-assignments`, timetable‑change KPI dashboard.

## Backend
- **Router:** `scheduling/router.py`, `human_approved_timetable_workflow/router.py`, `timetable_change_proposal/router.py`, `timetable_approval_queue/router.py`, `timetable_change_kpi_dashboard/router.py`, `workload_management/router.py`, `room_booking/router.py`, `equipment_booking/router.py`.

## Database
`university_scheduling_section_action_logs`, `university_scheduling_section_outcomes`, `campus_rooms`, `room_bookings`, `equipment_bookings`, timetable proposal/simulation/approval таблицы.

## API
`/api/admin/scheduling`, `/api/admin/human-approved-timetable-workflow`, `/api/admin/timetable-change-proposal`, `/api/admin/timetable-approval-queue`, `/api/admin/timetable-change-kpi-dashboard`, `/api/admin/room-booking`, `/api/admin/equipment-booking`, `/api/admin/workload-management`.

## Связанные модули
`academic_operations`, `enrollments`, `campus_facilities` (rooms), `digital_twin` (capacity), `brain_core`.

## Workflow
Human‑approved изменение расписания ([../08_WORKFLOWS.md](../08_WORKFLOWS.md) §9.4): proposal → simulation → recommendation bridge → approval queue → human decision → ручное применение. Состояния DRAFT→PENDING_HUMAN_REVIEW→HUMAN_APPROVED/REJECTED/CANCELLED.

## Brain / AI
Сигналы `scheduling.section.conflict_detected`, `scheduling.room_allocation.*`, `enrollment.capacity_risk.detected`, `scheduling.timetable_{proposal,simulation,approval}.*`; решения `section_conflict`, `room_allocation_recommendation`, `enrollment_capacity_risk`. **Запрещены** AUTO_APPLY/AUTO_OPTIMIZE (human gating).

## Проблемы / Рекомендации
- Множество timetable‑модулей (proposal/simulation/approval/bridge/kpi). **Рекомендация:** описать единый FSM, консолидировать под один пакет workflow.
