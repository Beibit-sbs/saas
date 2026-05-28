from __future__ import annotations

import pytest

from app.modules.campus_facilities_housing_transport import permissions


EXPECTED_PERMISSIONS = {
    "campus_facilities.overview.read",
    "campus_facilities.dashboard.read",
    "campus_facilities.campus.read",
    "campus_facilities.facilities.read",
    "campus_facilities.buildings.read",
    "campus_facilities.floors.read",
    "campus_facilities.rooms.read",
    "campus_facilities.room_types.read",
    "campus_facilities.availability.read",
    "campus_facilities.occupancy.read",
    "campus_facilities.dormitories.read",
    "campus_facilities.housing_units.read",
    "campus_facilities.housing_requests.read",
    "campus_facilities.maintenance.read",
    "campus_facilities.service_requests.read",
    "campus_facilities.work_orders.read",
    "campus_facilities.transport_routes.read",
    "campus_facilities.transport_vehicles.read",
    "campus_facilities.transport_schedules.read",
    "campus_facilities.responsible_units.read",
    "campus_facilities.safety_readiness.read",
    "campus_facilities.access_visitor_bridge.read",
    "campus_facilities.student_services_bridge.read",
    "campus_facilities.finance_asset_bridge.read",
    "campus_facilities.hr_staff_bridge.read",
    "campus_facilities.audit_evidence.read",
    "campus_facilities.limitations.read",
    "campus_facilities.metadata_contract.read",
    "campus_facilities.facilities.metadata",
    "campus_facilities.buildings.metadata",
    "campus_facilities.rooms.metadata",
    "campus_facilities.availability.metadata",
    "campus_facilities.occupancy.metadata",
    "campus_facilities.dormitories.metadata",
    "campus_facilities.housing_requests.metadata",
    "campus_facilities.maintenance.metadata",
    "campus_facilities.service_requests.metadata",
    "campus_facilities.work_orders.metadata",
    "campus_facilities.transport.metadata",
    "campus_facilities.responsible_units.metadata",
    "campus_facilities.safety_readiness.evidence",
    "campus_facilities.access_visitor_bridge.metadata",
    "campus_facilities.student_services_bridge.metadata",
    "campus_facilities.finance_asset_bridge.metadata",
    "campus_facilities.hr_staff_bridge.metadata",
    "campus_facilities.limitations.metadata",
}


def test_permission_count_exact_46() -> None:
    assert len(permissions.ALL_PERMISSIONS) == 46
    assert permissions.CAMPUS_FACILITIES_PERMISSION_COUNT == 46
    assert permissions.EXPECTED_PERMISSION_COUNT == 46


def test_permission_inventory_exact_match() -> None:
    assert set(permissions.ALL_PERMISSIONS) == EXPECTED_PERMISSIONS
    assert set(permissions.CAMPUS_FACILITIES_PERMISSIONS) == EXPECTED_PERMISSIONS


@pytest.mark.parametrize("permission", sorted(EXPECTED_PERMISSIONS))
def test_each_expected_permission_present(permission: str) -> None:
    assert permission in permissions.ALL_PERMISSIONS


def test_permission_namespace_shape_is_consistent() -> None:
    assert all(permission.startswith("campus_facilities.") for permission in permissions.ALL_PERMISSIONS)
    assert sum(permission.endswith(".read") for permission in permissions.ALL_PERMISSIONS) == 28
    assert sum(permission.endswith(".metadata") for permission in permissions.ALL_PERMISSIONS) == 17
    assert sum(permission.endswith(".evidence") for permission in permissions.ALL_PERMISSIONS) == 1


@pytest.mark.parametrize(
    "forbidden_fragment",
    [
        "execute",
        "approve",
        "evict",
        "dispatch",
        "assign_live",
        "gps_track",
        "iot_control",
        "block_access",
        "sanction",
        "delete",
    ],
)
def test_forbidden_operational_permission_fragments_absent(forbidden_fragment: str) -> None:
    inventory = "\n".join(sorted(permissions.ALL_PERMISSIONS))
    assert forbidden_fragment not in inventory
