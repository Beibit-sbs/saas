# Модуль: Campus / Facilities / Housing / Transport

[← Каталог модулей](README.md) · [Индекс](../README.md)

Backend: `campus_facilities_housing_transport/`, `campus_sla/`, `facilities_work_orders/`, `operations/`, `housing/`, `dormitory_management/`, `transport/`, `dining/`, `parking/`, `parking_enforcement/`, `parking_permit_ops/`, `room_booking/`, `equipment_booking/`, `lab_operations/`, `events_management/`
Frontend: `frontend/modules/campus-facilities/`, `scheduling/`, `events-management/`
Вертикаль: **V11 Campus / Facilities / Housing / Transport**

## Назначение
Кампусная инфраструктура: здания, аудитории, общежития, транспорт, питание, парковка, work orders, бронирование, события, SLA.

## Бизнес‑функции
Управление зданиями/этажами/аудиториями · заявки на обслуживание (work orders) · общежития (заявки, распределение) · транспорт (маршруты, брони, сбои) · питание (меню, заказы, вместимость) · парковка (пропуска, нарушения) · бронирование аудиторий/оборудования · события · SLA‑мониторинг.

## Пользователи (роли)
campus/facilities admin, коменданты, транспортная служба; `auditor`.

## Страницы / Dashboard
`/console/campus-facilities/*` (~23: buildings, campus, dormitories, floors, rooms, facilities, housing-units/requests, maintenance, occupancy, service-requests, work-orders, availability, safety-readiness, transport, bridges, dashboard, audit-evidence, responsible-units).

## Backend
- **Router:** `campus_facilities_housing_transport/router.py` + `campus_sla`, `facilities_work_orders`, `operations`, `housing`, `transport`, `dining`, `room_booking`, `equipment_booking`, `visitor_management` (в security‑вертикали).
- **Permissions:** `campus_facilities_housing_transport/permissions.py` (53; импортируется в `rbac/service.py`).

## Database
`university_facilities_work_orders`, `university_facilities_maintenance_requests`, `university_operations_*`, `campus_rooms`, `room_bookings`, `campus_events`, `event_registrations`, `equipment_items/bookings`, `transport_routes/bookings`, `dining_menus/orders`, `parking_lots/permits/sessions/violations`, `campus_sla_records`, `university_housing_requests`, `room_assignment_records`.

## API
`/api/admin/campus-facilities`, `/api/admin/campus-sla`, `/api/admin/facilities`, `/api/admin/housing`, `/api/admin/transport`, `/api/admin/dining`, `/api/admin/room-booking`, `/api/admin/equipment-booking`. Permissions `campus.read`, `buildings.read`, `maintenance.read`, `transport.read`, bridges (`finance_asset_bridge`, `hr_staff_bridge`, `student_services`, `access_visitor`).

## Связанные модули
`security_access_compliance` (access-visitor), `finance_procurement_asset` (asset bridge), `hr_staff_governance`, `scheduling`/`room_booking`, `digital_twin` (capacity), `brain_core`.

## Workflow
Work order / бронирование / события. События `event.*`, `booking.{approved,conflict_detected}`, `operations.facility_issue.reported`, `campus.transport.disruption_detected`.

## Brain / AI
Сигналы Campus Operations (19): `operations.facility_issue.reported`, `campus.*`, `resource.overload`; решения `campus_operations`, `supply_management`. Digital Twin использует capacity‑модули (rooms, dining, dormitory).

## Проблемы / Рекомендации
- FE testid `campus-facilities-permission-denied` отсутствует — P2. Много под‑модулей парковки (parking, parking_enforcement, parking_permit_ops). **Рекомендация:** консолидировать парковку, добавить testid.
