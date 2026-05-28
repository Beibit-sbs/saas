"""Campus / Facilities / Housing / Transport permission constants."""

from __future__ import annotations

OVERVIEW_READ = "campus_facilities.overview.read"
DASHBOARD_READ = "campus_facilities.dashboard.read"
CAMPUS_READ = "campus_facilities.campus.read"
FACILITIES_READ = "campus_facilities.facilities.read"
BUILDINGS_READ = "campus_facilities.buildings.read"
FLOORS_READ = "campus_facilities.floors.read"
ROOMS_READ = "campus_facilities.rooms.read"
ROOM_TYPES_READ = "campus_facilities.room_types.read"
AVAILABILITY_READ = "campus_facilities.availability.read"
OCCUPANCY_READ = "campus_facilities.occupancy.read"
DORMITORIES_READ = "campus_facilities.dormitories.read"
HOUSING_UNITS_READ = "campus_facilities.housing_units.read"
HOUSING_REQUESTS_READ = "campus_facilities.housing_requests.read"
MAINTENANCE_READ = "campus_facilities.maintenance.read"
SERVICE_REQUESTS_READ = "campus_facilities.service_requests.read"
WORK_ORDERS_READ = "campus_facilities.work_orders.read"
TRANSPORT_ROUTES_READ = "campus_facilities.transport_routes.read"
TRANSPORT_VEHICLES_READ = "campus_facilities.transport_vehicles.read"
TRANSPORT_SCHEDULES_READ = "campus_facilities.transport_schedules.read"
RESPONSIBLE_UNITS_READ = "campus_facilities.responsible_units.read"
SAFETY_READINESS_READ = "campus_facilities.safety_readiness.read"
ACCESS_VISITOR_BRIDGE_READ = "campus_facilities.access_visitor_bridge.read"
STUDENT_SERVICES_BRIDGE_READ = "campus_facilities.student_services_bridge.read"
FINANCE_ASSET_BRIDGE_READ = "campus_facilities.finance_asset_bridge.read"
HR_STAFF_BRIDGE_READ = "campus_facilities.hr_staff_bridge.read"
AUDIT_EVIDENCE_READ = "campus_facilities.audit_evidence.read"
LIMITATIONS_READ = "campus_facilities.limitations.read"
METADATA_CONTRACT_READ = "campus_facilities.metadata_contract.read"

FACILITIES_METADATA = "campus_facilities.facilities.metadata"
BUILDINGS_METADATA = "campus_facilities.buildings.metadata"
ROOMS_METADATA = "campus_facilities.rooms.metadata"
AVAILABILITY_METADATA = "campus_facilities.availability.metadata"
OCCUPANCY_METADATA = "campus_facilities.occupancy.metadata"
DORMITORIES_METADATA = "campus_facilities.dormitories.metadata"
HOUSING_REQUESTS_METADATA = "campus_facilities.housing_requests.metadata"
MAINTENANCE_METADATA = "campus_facilities.maintenance.metadata"
SERVICE_REQUESTS_METADATA = "campus_facilities.service_requests.metadata"
WORK_ORDERS_METADATA = "campus_facilities.work_orders.metadata"
TRANSPORT_METADATA = "campus_facilities.transport.metadata"
RESPONSIBLE_UNITS_METADATA = "campus_facilities.responsible_units.metadata"
SAFETY_READINESS_EVIDENCE = "campus_facilities.safety_readiness.evidence"
ACCESS_VISITOR_BRIDGE_METADATA = "campus_facilities.access_visitor_bridge.metadata"
STUDENT_SERVICES_BRIDGE_METADATA = "campus_facilities.student_services_bridge.metadata"
FINANCE_ASSET_BRIDGE_METADATA = "campus_facilities.finance_asset_bridge.metadata"
HR_STAFF_BRIDGE_METADATA = "campus_facilities.hr_staff_bridge.metadata"
LIMITATIONS_METADATA = "campus_facilities.limitations.metadata"

ALL_PERMISSIONS: frozenset[str] = frozenset(
    {
        OVERVIEW_READ,
        DASHBOARD_READ,
        CAMPUS_READ,
        FACILITIES_READ,
        BUILDINGS_READ,
        FLOORS_READ,
        ROOMS_READ,
        ROOM_TYPES_READ,
        AVAILABILITY_READ,
        OCCUPANCY_READ,
        DORMITORIES_READ,
        HOUSING_UNITS_READ,
        HOUSING_REQUESTS_READ,
        MAINTENANCE_READ,
        SERVICE_REQUESTS_READ,
        WORK_ORDERS_READ,
        TRANSPORT_ROUTES_READ,
        TRANSPORT_VEHICLES_READ,
        TRANSPORT_SCHEDULES_READ,
        RESPONSIBLE_UNITS_READ,
        SAFETY_READINESS_READ,
        ACCESS_VISITOR_BRIDGE_READ,
        STUDENT_SERVICES_BRIDGE_READ,
        FINANCE_ASSET_BRIDGE_READ,
        HR_STAFF_BRIDGE_READ,
        AUDIT_EVIDENCE_READ,
        LIMITATIONS_READ,
        METADATA_CONTRACT_READ,
        FACILITIES_METADATA,
        BUILDINGS_METADATA,
        ROOMS_METADATA,
        AVAILABILITY_METADATA,
        OCCUPANCY_METADATA,
        DORMITORIES_METADATA,
        HOUSING_REQUESTS_METADATA,
        MAINTENANCE_METADATA,
        SERVICE_REQUESTS_METADATA,
        WORK_ORDERS_METADATA,
        TRANSPORT_METADATA,
        RESPONSIBLE_UNITS_METADATA,
        SAFETY_READINESS_EVIDENCE,
        ACCESS_VISITOR_BRIDGE_METADATA,
        STUDENT_SERVICES_BRIDGE_METADATA,
        FINANCE_ASSET_BRIDGE_METADATA,
        HR_STAFF_BRIDGE_METADATA,
        LIMITATIONS_METADATA,
    }
)

CAMPUS_FACILITIES_PERMISSIONS = sorted(ALL_PERMISSIONS)
CAMPUS_FACILITIES_PERMISSION_COUNT = 46
EXPECTED_PERMISSION_COUNT = 46
