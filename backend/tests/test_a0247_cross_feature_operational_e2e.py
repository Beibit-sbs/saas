"""A-024.7 cross-feature operational E2E validation for A-024 backbone surfaces."""

from __future__ import annotations

import importlib

import pytest

import app.main as main_module
from app.modules.attendance import service as attendance_service
from app.modules.observability import service as observability_service
from app.modules.platform import saas_readiness
from app.modules.student_portal import service as student_portal_service
from app.modules.university_core import service as university_core_service
from tests.conftest import ADMIN_HEADERS, client


@pytest.mark.parametrize(
    "module_name",
    [
        "app.modules.ai_routing_control.service",
        "app.modules.platform_health.service",
        "app.modules.ai_copilot_ops.service",
        "app.modules.procurement_approval_workflow.service",
        "app.modules.observability.service",
        "app.modules.attendance.service",
        "app.modules.student_portal.service",
        "app.modules.university_core.service",
        "app.modules.platform.saas_readiness",
    ],
)
def test_a0247_required_modules_import_successfully(module_name: str) -> None:
    importlib.import_module(module_name)


def test_a0247_backbone_includes_exact_8_modules() -> None:
    summary = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    assert summary["total_modules_reviewed"] == 8
    assert {item["module"] for item in summary["module_summaries"]} == set(
        saas_readiness.A024_OPERATIONAL_BACKBONE_MODULES
    )


def test_a0247_cross_feature_surface_inventory_has_expected_5_surfaces() -> None:
    summary = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    inventory = {item["module"]: item["visible_surface"] for item in summary["visible_surface_inventory"]}
    assert inventory == {
        "observability": "/api/admin/observability/summary",
        "attendance": "/api/admin/attendance/summary",
        "student_portal": "/api/admin/student-portal/summary",
        "university_core": "/api/admin/university-core/readiness",
    }


def test_a0247_l3_modules_are_not_falsely_marked_as_visible_l4() -> None:
    summary = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    by_module = {item["module"]: item for item in summary["module_summaries"]}
    assert by_module["ai_routing_control"]["current_level"] == 3
    assert by_module["ai_routing_control"]["visible_surface"] is None
    assert by_module["platform_health"]["current_level"] == 3
    assert by_module["platform_health"]["visible_surface"] is None
    assert by_module["ai_copilot_ops"]["current_level"] == 3
    assert by_module["ai_copilot_ops"]["visible_surface"] is None
    assert by_module["procurement_approval_workflow"]["current_level"] == 3
    assert by_module["procurement_approval_workflow"]["visible_surface"] is None


def test_a0247_l4_modules_are_visible() -> None:
    summary = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    by_module = {item["module"]: item for item in summary["module_summaries"]}
    assert by_module["observability"]["current_level"] == 4
    assert by_module["observability"]["visible_surface"] == "/api/admin/observability/summary"
    assert by_module["attendance"]["current_level"] == 4
    assert by_module["attendance"]["visible_surface"] == "/api/admin/attendance/summary"
    assert by_module["student_portal"]["current_level"] == 4
    assert by_module["student_portal"]["visible_surface"] == "/api/admin/student-portal/summary"
    assert by_module["university_core"]["current_level"] == 4
    assert by_module["university_core"]["visible_surface"] == "/api/admin/university-core/readiness"


def test_a0247_summary_flags_preserve_no_fake_and_no_mutation_contracts() -> None:
    summary = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    assert summary["no_fake_saas_claim"] is True
    assert summary["no_fake_brain_claim"] is True
    assert summary["no_full_production_claim"] is True
    assert summary["no_fake_kpi_values"] is True
    assert summary["no_automatic_action"] is True
    assert summary["no_db_mutation"] is True


def test_a0247_feature_flag_and_billing_are_classification_only() -> None:
    summary = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    for item in summary["module_summaries"]:
        assert item["feature_flag_status"] in {
            "supported",
            "ready_for_mapping",
            "deferred",
            "not_applicable",
            "unknown",
        }
        assert item["billing_plan_status"] in {
            "supported",
            "ready_for_mapping",
            "deferred",
            "not_applicable",
            "unknown",
        }


def test_a0247_event_kpi_brain_mapping_is_explicit_and_honest() -> None:
    summary = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    mapping = summary["event_kpi_brain_mapping"]
    assert len(mapping) == 8
    for item in mapping:
        assert item["decision"] == "readiness_mapping_only"
        assert item["event_mapping_status"] in {"ready_for_mapping", "partially_mapped", "deferred", "unknown"}
        assert item["kpi_mapping_status"] in {"ready_for_mapping", "partially_mapped", "deferred", "unknown"}
        assert item["brain_mapping_status"] in {"ready_for_mapping", "deferred", "unknown"}
        assert item["no_runtime_event_emission_added"] is True
        assert item["no_fake_kpi_values"] is True
        assert item["no_brain_autonomy_claim"] is True


def test_a0247_deterministic_backbone_summary() -> None:
    first = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    second = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    assert first == second


def test_a0247_continuity_baseline_and_levels_unchanged_from_a0246() -> None:
    summary = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    assert summary["module_count_expansion"] == 0
    assert summary["baseline_total_target_modules"] == 150
    assert summary["no_level5_or_level6_claim"] is True
    by_module = {item["module"]: item["current_level"] for item in summary["module_summaries"]}
    assert by_module["ai_routing_control"] == 3
    assert by_module["platform_health"] == 3
    assert by_module["ai_copilot_ops"] == 3
    assert by_module["procurement_approval_workflow"] == 3
    assert by_module["observability"] == 4
    assert by_module["attendance"] == 4
    assert by_module["student_portal"] == 4
    assert by_module["university_core"] == 4


@pytest.mark.parametrize(
    ("path", "expected_visible_surface"),
    [
        ("/api/admin/observability/summary", "/api/admin/observability/summary"),
        ("/api/admin/attendance/summary", "/api/admin/attendance/summary"),
        ("/api/admin/student-portal/summary", "/api/admin/student-portal/summary"),
        ("/api/admin/university-core/readiness", "/api/admin/university-core/readiness"),
        ("/api/admin/saas-readiness/summary", "/api/admin/saas-readiness/summary"),
    ],
)
def test_a0247_admin_visibility_endpoints_return_tenant_safe_payloads(
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    expected_visible_surface: str,
) -> None:
    # Freeze dynamic dependencies so endpoint contracts stay deterministic.
    monkeypatch.setattr(
        main_module,
        "deep_payload",
        lambda _app: {
            "deep": True,
            "dependencies": {
                "postgresql": {"healthy": True},
                "redis": {"healthy": True},
                "worker": {"healthy": True},
                "scheduler": {"healthy": True},
            },
        },
    )
    monkeypatch.setattr(
        main_module,
        "snapshot_latency_metrics",
        lambda: {
            "p95_latency_ms": 120.0,
            "p99_latency_ms": 300.0,
            "requests_per_minute": 20,
            "http_5xx_count": 0,
        },
    )
    monkeypatch.setattr(
        main_module,
        "validate_entity_tables_impl",
        lambda: {
            "missing": [],
            "present": ["university_students", "university_courses"],
            "missing_fallback": ["planned_table"],
            "present_fallback": ["legacy_fallback"],
        },
    )
    monkeypatch.setattr(main_module, "list_attendance_records", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(main_module, "list_student_portal_requests", lambda *_args, **_kwargs: [])

    response = client.get(path, headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["tenant_id"] == 1
    assert payload["visible_surface"] == expected_visible_surface


def test_a0247_saas_summary_contains_cross_feature_endpoint_continuity() -> None:
    summary = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    visible_surfaces = {item["visible_surface"] for item in summary["visible_surface_inventory"]}
    assert "/api/admin/observability/summary" in visible_surfaces
    assert "/api/admin/attendance/summary" in visible_surfaces
    assert "/api/admin/student-portal/summary" in visible_surfaces
    assert "/api/admin/university-core/readiness" in visible_surfaces


def test_a0247_known_conditions_and_deferred_work_are_explicit() -> None:
    summary = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    assert isinstance(summary["known_conditions"], list)
    assert isinstance(summary["deferred_work"], list)
    assert len(summary["known_conditions"]) > 0
    assert len(summary["deferred_work"]) > 0


@pytest.mark.parametrize("tenant_id", [0, -1])
def test_a0247_missing_tenant_context_fails_closed_pattern(tenant_id: int) -> None:
    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        saas_readiness.validate_saas_readiness_tenant(tenant_id)

    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        observability_service.build_observability_signal(
            tenant_id=tenant_id,
            component="api",
            status="healthy",
            source="test",
            source_entity_type="probe",
            source_entity_id="api",
        )

    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        attendance_service.build_attendance_visibility_summary(
            tenant_id=tenant_id,
            records=[],
            source_entity_type="attendance_records",
            source_entity_id="summary",
        )

    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        student_portal_service.build_student_portal_visibility_summary(
            tenant_id=tenant_id,
            access_status="active",
            has_required_profile=True,
            has_active_enrollment=True,
            has_portal_role=True,
            has_contact_channel=True,
            source_entity_type="portal_requests",
            source_entity_id="summary",
        )

    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        university_core_service.validate_university_core_tenant(tenant_id)


def test_a0247_e2e_runtime_surfaces_and_backbone_contract_align(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        main_module,
        "deep_payload",
        lambda _app: {
            "deep": True,
            "dependencies": {
                "postgresql": {"healthy": True},
                "redis": {"healthy": True},
                "worker": {"healthy": True},
                "scheduler": {"healthy": True},
            },
        },
    )
    monkeypatch.setattr(
        main_module,
        "snapshot_latency_metrics",
        lambda: {
            "p95_latency_ms": 100.0,
            "p99_latency_ms": 200.0,
            "requests_per_minute": 12,
            "http_5xx_count": 0,
        },
    )
    monkeypatch.setattr(
        main_module,
        "validate_entity_tables_impl",
        lambda: {
            "missing": [],
            "present": ["university_students"],
            "missing_fallback": [],
            "present_fallback": [],
        },
    )
    monkeypatch.setattr(main_module, "list_attendance_records", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(main_module, "list_student_portal_requests", lambda *_args, **_kwargs: [])

    obs = client.get("/api/admin/observability/summary", headers=ADMIN_HEADERS)
    att = client.get("/api/admin/attendance/summary", headers=ADMIN_HEADERS)
    portal = client.get("/api/admin/student-portal/summary", headers=ADMIN_HEADERS)
    uni = client.get("/api/admin/university-core/readiness", headers=ADMIN_HEADERS)
    saas = client.get("/api/admin/saas-readiness/summary", headers=ADMIN_HEADERS)

    assert obs.status_code == 200
    assert att.status_code == 200
    assert portal.status_code == 200
    assert uni.status_code == 200
    assert saas.status_code == 200

    saas_payload = saas.json()
    inventory = {item["module"]: item["visible_surface"] for item in saas_payload["visible_surface_inventory"]}

    assert obs.json()["visible_surface"] == inventory["observability"]
    assert att.json()["visible_surface"] == inventory["attendance"]
    assert portal.json()["visible_surface"] == inventory["student_portal"]
    assert uni.json()["visible_surface"] == inventory["university_core"]
    assert saas_payload["visible_surface"] == "/api/admin/saas-readiness/summary"


def test_a0247_consolidation_surface_is_part_of_cross_feature_contract() -> None:
    response = client.get("/api/admin/saas-readiness/summary", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    payload = response.json()
    inventory_surfaces = {item["visible_surface"] for item in payload["visible_surface_inventory"]}
    all_surfaces = set(inventory_surfaces)
    all_surfaces.add(payload["visible_surface"])
    assert all_surfaces == {
        "/api/admin/observability/summary",
        "/api/admin/attendance/summary",
        "/api/admin/student-portal/summary",
        "/api/admin/university-core/readiness",
        "/api/admin/saas-readiness/summary",
    }
