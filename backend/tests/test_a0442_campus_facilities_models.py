from __future__ import annotations

from pathlib import Path

from app.modules.campus_facilities_housing_transport import models


BACKEND_DIR = Path(__file__).resolve().parents[1]
MIGRATION_FILE = BACKEND_DIR / "alembic" / "versions" / "cfht0442rt01_a0442_campus_facilities_housing_transport_tables.py"

EXPECTED_TABLES = {
    "cfht_campus_profiles",
    "cfht_facility_registry_records",
    "cfht_building_records",
    "cfht_floor_records",
    "cfht_room_records",
    "cfht_room_type_records",
    "cfht_room_availability_snapshots",
    "cfht_occupancy_visibility_records",
    "cfht_dormitory_records",
    "cfht_housing_unit_records",
    "cfht_housing_request_metadata",
    "cfht_maintenance_request_records",
    "cfht_service_request_records",
    "cfht_work_order_metadata",
    "cfht_transport_route_records",
    "cfht_transport_vehicle_metadata",
    "cfht_transport_schedule_metadata",
    "cfht_facility_responsible_unit_records",
    "cfht_campus_safety_readiness_records",
    "cfht_access_visitor_bridge_records",
    "cfht_student_services_bridge_records",
    "cfht_finance_asset_bridge_records",
    "cfht_hr_staff_assignment_bridge_records",
    "cfht_rectorate_dashboard_snapshots",
    "cfht_audit_evidence_records",
    "cfht_limitations",
}


def test_import_and_constants_sanity() -> None:
    assert models.MODULE_NAME == "campus_facilities_housing_transport"
    assert models.API_PREFIX == "/api/admin/campus-facilities"
    assert models.DB_PREFIX == "cfht_"
    assert models.PERMISSION_NAMESPACE == "campus_facilities.*"
    assert models.RUNTIME_MODE == "METADATA_READINESS_EVIDENCE_CONTROL_VISIBILITY_HUMAN_REVIEW_ONLY"
    assert models.EXPECTED_TABLE_COUNT == 26
    assert models.EXPECTED_PERMISSION_COUNT == 46
    assert models.EXPECTED_ROUTE_COUNT == 52


def test_metadata_contains_expected_26_tables() -> None:
    cfht_tables = {name for name in models.Base.metadata.tables if name.startswith("cfht_")}
    assert cfht_tables == EXPECTED_TABLES
    assert set(models.TABLE_NAMES) == EXPECTED_TABLES
    assert len(models.TABLE_NAMES) == 26


def test_model_family_map_matches_table_inventory() -> None:
    assert len(models.MODEL_BY_FAMILY) == 26
    assert set(models.MODEL_BY_FAMILY) == {
        "campus",
        "facilities",
        "buildings",
        "floors",
        "rooms",
        "room_types",
        "availability",
        "occupancy",
        "dormitories",
        "housing_units",
        "housing_requests",
        "maintenance",
        "service_requests",
        "work_orders",
        "transport_routes",
        "transport_vehicles",
        "transport_schedules",
        "responsible_units",
        "safety_readiness",
        "access_visitor_bridge",
        "student_services_bridge",
        "finance_asset_bridge",
        "hr_staff_bridge",
        "dashboard",
        "audit_evidence",
        "limitations",
    }


def test_migration_file_exists_and_has_revision_chain() -> None:
    text = MIGRATION_FILE.read_text()
    assert 'revision = "cfht0442rt01"' in text
    assert 'down_revision = "sac0432rt01"' in text


def test_migration_create_and_drop_counts_match_26() -> None:
    text = MIGRATION_FILE.read_text()
    assert text.count('op.create_table("cfht_') == 26
    assert text.count('op.drop_table("cfht_') == 26


def test_all_expected_tables_appear_in_migration_text() -> None:
    text = MIGRATION_FILE.read_text()
    for table_name in EXPECTED_TABLES:
        assert table_name in text


def test_no_forbidden_operational_table_names_present() -> None:
    table_text = "\n".join(sorted(EXPECTED_TABLES))
    for forbidden in [
        "iot_telemetry",
        "gps_stream",
        "building_automation_events",
        "autonomous_dispatch",
        "eviction_execution",
        "sanction_engine",
        "payment_execution",
        "provider_sync",
        "realtime_sensor",
        "official_certification",
    ]:
        assert forbidden not in table_text
