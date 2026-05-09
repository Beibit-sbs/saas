"""A-024.6 targeted tests for SaaS readiness consolidation contract."""

from __future__ import annotations

import importlib

import pytest

from app.modules.platform import saas_readiness
from tests.conftest import ADMIN_HEADERS, client


@pytest.mark.parametrize("module_name", ["app.modules.platform.saas_readiness"])
def test_a0246_module_imports_successfully(module_name: str) -> None:
    importlib.import_module(module_name)


@pytest.mark.parametrize("tenant_id", [0, -1])
def test_a0246_tenant_id_required_and_positive(tenant_id: int) -> None:
    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        saas_readiness.build_a024_operational_backbone_summary(tenant_id=tenant_id)


def test_a0246_all_8_modules_present_in_summary() -> None:
    summary = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    modules = {item["module"] for item in summary["module_summaries"]}
    assert modules == set(saas_readiness.A024_OPERATIONAL_BACKBONE_MODULES)
    assert summary["total_modules_reviewed"] == 8


def test_a0246_visible_surface_inventory_contains_expected_l4_modules() -> None:
    summary = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    surfaces = {item["module"]: item["visible_surface"] for item in summary["visible_surface_inventory"]}
    assert surfaces["observability"] == "/api/admin/observability/summary"
    assert surfaces["attendance"] == "/api/admin/attendance/summary"
    assert surfaces["student_portal"] == "/api/admin/student-portal/summary"
    assert surfaces["university_core"] == "/api/admin/university-core/readiness"


def test_a0246_l3_modules_not_falsely_marked_l4() -> None:
    summary = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    by_module = {item["module"]: item for item in summary["module_summaries"]}
    assert by_module["ai_routing_control"]["current_level"] == 3
    assert by_module["platform_health"]["current_level"] == 3
    assert by_module["ai_copilot_ops"]["current_level"] == 3
    assert by_module["procurement_approval_workflow"]["current_level"] == 3


def test_a0246_no_fake_claim_flags_present() -> None:
    summary = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    assert summary["no_fake_saas_claim"] is True
    assert summary["no_full_production_claim"] is True
    assert summary["no_fake_brain_claim"] is True


def test_a0246_feature_flag_and_billing_statuses_are_honest_mapping_not_enforcement() -> None:
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


def test_a0246_event_kpi_brain_mapping_and_deferred_work_are_explicit() -> None:
    summary = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    mapping = summary["event_kpi_brain_mapping"]
    assert len(mapping) == 8
    assert summary["deferred_work"]


def test_a0246_operational_backbone_status_is_deterministic() -> None:
    one = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    two = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    assert one == two


def test_a0246_no_module_count_expansion() -> None:
    summary = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    assert summary["module_count_expansion"] == 0
    assert summary["baseline_total_target_modules"] == 150


def test_a0246_no_level5_or_level6_claim() -> None:
    summary = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    assert summary["no_level5_or_level6_claim"] is True


def test_a0246_no_fake_kpi_values_or_automatic_action_or_db_mutation_claims() -> None:
    summary = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    assert summary["no_fake_kpi_values"] is True
    assert summary["no_automatic_action"] is True
    assert summary["no_db_mutation"] is True


def test_a0246_known_conditions_representation_exists() -> None:
    summary = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    assert isinstance(summary["known_conditions"], list)
    assert any("known_condition" in item for item in summary["known_conditions"])


def test_a0246_summary_evidence_lineage_is_deterministic() -> None:
    summary = saas_readiness.build_a024_operational_backbone_summary(tenant_id=1)
    assert summary["evidence_items"] == sorted(summary["evidence_items"])


def test_a0246_api_route_returns_deterministic_tenant_safe_payload() -> None:
    response = client.get("/api/admin/saas-readiness/summary", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["tenant_id"] == 1
    assert payload["total_modules_reviewed"] == 8
    assert payload["visible_surface"] == "/api/admin/saas-readiness/summary"


def test_a0246_missing_tenant_context_fails_closed_pattern() -> None:
    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        saas_readiness.validate_saas_readiness_tenant(0)


def test_a0246_api_payload_contains_all_8_modules_and_flags() -> None:
    response = client.get("/api/admin/saas-readiness/summary", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload["module_summaries"]) == 8
    assert payload["no_fake_saas_claim"] is True
    assert payload["no_full_production_claim"] is True
    assert payload["no_fake_brain_claim"] is True
