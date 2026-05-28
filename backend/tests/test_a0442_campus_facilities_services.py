from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.modules.campus_facilities_housing_transport import models, permissions, service


SAMPLE_RECORD = {
    "id": 1,
    "tenant_id": 77,
    "status": "draft",
    "reference_key": "sample",
    "title": "Sample",
    "source_module": "tests",
    "source_entity_id": "1",
    "metadata": {"x": 1},
    "limitations": ["human review"],
    "incomplete_data": True,
}


@pytest.mark.parametrize(
    ("method_name", "family"),
    [
        ("get_campus", "campus"),
        ("get_facilities", "facilities"),
        ("get_buildings", "buildings"),
        ("get_floors", "floors"),
        ("get_rooms", "rooms"),
        ("get_room_types", "room_types"),
        ("get_availability", "availability"),
        ("get_occupancy", "occupancy"),
        ("get_dormitories", "dormitories"),
        ("get_housing_units", "housing_units"),
        ("get_housing_requests", "housing_requests"),
        ("get_maintenance", "maintenance"),
        ("get_service_requests", "service_requests"),
        ("get_work_orders", "work_orders"),
        ("get_transport_routes", "transport_routes"),
        ("get_transport_vehicles", "transport_vehicles"),
        ("get_transport_schedules", "transport_schedules"),
        ("get_responsible_units", "responsible_units"),
        ("get_safety_readiness", "safety_readiness"),
        ("get_access_visitor_bridge", "access_visitor_bridge"),
        ("get_student_services_bridge", "student_services_bridge"),
        ("get_finance_asset_bridge", "finance_asset_bridge"),
        ("get_hr_staff_bridge", "hr_staff_bridge"),
        ("get_audit_evidence", "audit_evidence"),
        ("get_limitations", "limitations"),
    ],
)
def test_collection_getters_return_metadata_only_payload(monkeypatch: pytest.MonkeyPatch, method_name: str, family: str) -> None:
    def fake_list_family_records(db, tenant_id, target_family):
        assert db == "db"
        assert tenant_id == 77
        assert target_family == family
        return [SAMPLE_RECORD]

    monkeypatch.setattr(service.repository, "list_family_records", fake_list_family_records)
    response = getattr(service, method_name)("db", 77)
    assert response.tenant_id == 77
    assert response.module == models.MODULE_NAME
    assert response.human_review_required is True
    assert response.records[0].reference_key == "sample"


def test_get_overview_reports_contract_counts() -> None:
    response = service.get_overview("db", 55)
    assert response.tenant_id == 55
    assert response.table_count == 26
    assert response.route_count == 52
    assert response.permission_count == 46
    assert len(response.families) == 25


def test_get_dashboard_uses_repository_inputs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(service.repository, "get_dashboard_inputs", lambda db, tenant_id: {"rooms": 3, "transport_routes": 2})
    response = service.get_dashboard("db", 91)
    assert response.tenant_id == 91
    assert response.summary["rooms"] == 3
    assert response.summary["transport_routes"] == 2
    assert response.summary["tracked_families"] == 2


def test_get_metadata_contract_matches_runtime_contract() -> None:
    response = service.get_metadata_contract("db", 99)
    assert response.api_prefix == models.API_PREFIX
    assert response.db_prefix == models.DB_PREFIX
    assert response.table_count == 26
    assert response.route_count == 52
    assert response.permission_count == 46
    assert response.permission_namespace == models.PERMISSION_NAMESPACE
    assert len(response.module_files) == 8


def test_get_health_is_metadata_only() -> None:
    response = service.get_health("db", 88)
    assert response.status == "healthy_metadata_only"
    assert response.expected_table_count == 26
    assert response.expected_permission_count == 46
    assert response.expected_route_count == 52
    assert response.production_facilities_claimed is False


def test_get_safety_boundaries_blocks_live_operations() -> None:
    response = service.get_safety_boundaries("db", 77)
    assert response.tenant_id == 77
    assert len(response.records) == 2
    boundaries = " ".join(record.metadata["boundary"] for record in response.records)
    assert "No live IoT" in boundaries
    assert "No automatic housing allocation" in boundaries


@pytest.mark.parametrize(
    ("method_name", "family"),
    [
        ("create_campus_metadata", "campus"),
        ("create_facility_metadata", "facilities"),
        ("create_building_metadata", "buildings"),
        ("create_floor_metadata", "floors"),
        ("create_room_metadata", "rooms"),
        ("create_room_type_metadata", "room_types"),
        ("create_availability_metadata", "availability"),
        ("create_occupancy_metadata", "occupancy"),
        ("create_dormitory_metadata", "dormitories"),
        ("create_housing_unit_metadata", "housing_units"),
        ("create_housing_request_metadata", "housing_requests"),
        ("create_maintenance_metadata", "maintenance"),
        ("create_service_request_metadata", "service_requests"),
        ("create_work_order_metadata", "work_orders"),
        ("create_transport_metadata", "transport_vehicles"),
        ("create_responsible_unit_metadata", "responsible_units"),
        ("create_safety_readiness_evidence", "safety_readiness"),
        ("create_access_visitor_bridge_metadata", "access_visitor_bridge"),
        ("create_student_services_bridge_metadata", "student_services_bridge"),
        ("create_finance_asset_bridge_metadata", "finance_asset_bridge"),
        ("create_hr_staff_bridge_metadata", "hr_staff_bridge"),
        ("create_limitations_metadata", "limitations"),
    ],
)
def test_create_methods_delegate_to_repository(monkeypatch: pytest.MonkeyPatch, method_name: str, family: str) -> None:
    captured = {}

    def fake_create_family_record(db, tenant_id, target_family, actor, payload):
        captured.update({"db": db, "tenant_id": tenant_id, "family": target_family, "actor": actor, "payload": payload})
        return SAMPLE_RECORD

    monkeypatch.setattr(service.repository, "create_family_record", fake_create_family_record)
    payload = SimpleNamespace(status="draft", reference_key="sample", title="Sample", source_module="tests", source_entity_id="1", metadata={}, limitations=[], incomplete_data=True)
    response = getattr(service, method_name)("db", 77, "actor-1", payload)
    assert captured == {"db": "db", "tenant_id": 77, "family": family, "actor": "actor-1", "payload": payload}
    assert response.record.reference_key == "sample"
    assert response.tenant_id == 77


def test_permission_inventory_matches_service_contract() -> None:
    contract = service.get_metadata_contract("db", 1)
    assert contract.permission_count == len(permissions.ALL_PERMISSIONS)
