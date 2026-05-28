from __future__ import annotations

import pytest

from app.modules.campus_facilities_housing_transport import models, permissions, service


def test_all_operational_claim_flags_are_false() -> None:
    assert models.LIVE_IOT_ENABLED is False
    assert models.LIVE_GPS_TRACKING_ENABLED is False
    assert models.BUILDING_AUTOMATION_ENABLED is False
    assert models.ACCESS_CONTROL_ENFORCEMENT_ENABLED is False
    assert models.SAFETY_CERTIFICATION_CLAIMED is False
    assert models.MAINTENANCE_COMPLETION_GUARANTEED is False
    assert models.AUTOMATIC_HOUSING_DECISION_ENABLED is False
    assert models.AUTOMATIC_EVICTION_ENABLED is False
    assert models.AUTOMATIC_STUDENT_STAFF_SANCTION_ENABLED is False
    assert models.AUTONOMOUS_DISPATCH_ENABLED is False
    assert models.EXTERNAL_PROVIDER_SYNC_ENABLED is False
    assert models.PRODUCTION_FACILITIES_CLAIMED is False
    assert models.SALES_READY_CLAIMED is False
    assert models.GCC_READY_CLAIMED is False
    assert models.L5_L6_CLAIMED is False
    assert models.HUMAN_REVIEW_REQUIRED is True


def test_safety_flag_payload_is_fail_closed() -> None:
    payload = service._safety()
    assert payload["live_iot_enabled"] is False
    assert payload["live_gps_tracking_enabled"] is False
    assert payload["building_automation_enabled"] is False
    assert payload["automatic_housing_decision_enabled"] is False
    assert payload["automatic_eviction_enabled"] is False
    assert payload["autonomous_dispatch_enabled"] is False
    assert payload["human_review_required"] is True
    assert payload["incomplete_data"] is True


def test_metadata_contract_exposes_no_live_control_claims() -> None:
    contract = service.get_metadata_contract("db", 42)
    assert contract.runtime_mode == models.RUNTIME_MODE
    assert contract.permission_namespace == models.PERMISSION_NAMESPACE
    assert "router.py" in contract.module_files
    assert "service.py" in contract.module_files


def test_health_response_limits_claim_scope() -> None:
    response = service.get_health("db", 42)
    joined = " ".join(response.limitations)
    assert "metadata readiness" in joined.lower()
    assert "operational campus state" in joined.lower()


def test_safety_boundary_records_encode_non_operational_scope() -> None:
    response = service.get_safety_boundaries("db", 42)
    boundary_text = " ".join(record.metadata["boundary"] for record in response.records)
    assert "No live IoT" in boundary_text
    assert "No automatic housing allocation" in boundary_text
    assert "transport dispatch" in boundary_text


@pytest.mark.parametrize(
    "forbidden_fragment",
    [
        "execute",
        "approve_live",
        "evict",
        "dispatch_live",
        "telemetry_stream",
        "gps_live",
        "iot_control",
        "lockdown",
        "autonomous",
        "external_submission",
    ],
)
def test_permission_inventory_avoids_forbidden_operational_fragments(forbidden_fragment: str) -> None:
    inventory = "\n".join(sorted(permissions.ALL_PERMISSIONS))
    assert forbidden_fragment not in inventory


@pytest.mark.parametrize(
    "forbidden_fragment",
    [
        "telemetry",
        "gps",
        "automation_events",
        "auto_assign",
        "auto_evict",
        "dispatch_execution",
        "lockdown",
        "official_certification",
        "production_sync",
        "live_provider",
    ],
)
def test_table_inventory_avoids_forbidden_operational_fragments(forbidden_fragment: str) -> None:
    inventory = "\n".join(models.TABLE_NAMES)
    assert forbidden_fragment not in inventory
