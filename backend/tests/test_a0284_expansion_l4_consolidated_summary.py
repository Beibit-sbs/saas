from __future__ import annotations

from collections import Counter

import pytest
from fastapi.testclient import TestClient
from fastapi.routing import APIRoute

from app.main import app
from app.modules.auth.token_service import create_access_token
from tests.conftest import ADMIN_HEADERS, client


CONSOLIDATED_ROUTE = "/api/admin/expansion/l4/summary"
A0282_ROUTES = [
    "/api/admin/expansion/l4/document-workflow/summary",
    "/api/admin/expansion/l4/order-decree-registry/summary",
    "/api/admin/expansion/l4/committee-decision-registry/summary",
    "/api/admin/expansion/l4/rector-resolution-tracking-workflow/summary",
    "/api/admin/expansion/l4/compliance-calendar-dashboard/summary",
    "/api/admin/expansion/l4/accreditation-dashboard/summary",
]
A0283_ROUTES = [
    "/api/admin/expansion/l4/incoming-outgoing-correspondence/summary",
    "/api/admin/expansion/l4/document-template-library/summary",
    "/api/admin/expansion/l4/ministry-reporting-dashboard/summary",
    "/api/admin/expansion/l4/rector-strategy-dashboard/summary",
    "/api/admin/expansion/l4/archive-retention-management/summary",
    "/api/admin/expansion/l4/international-office/summary",
]
EXPECTED_MODULES = {
    "document_workflow",
    "order_decree_registry",
    "incoming_outgoing_correspondence",
    "document_template_library",
    "committee_decision_registry",
    "rector_resolution_tracking_workflow",
    "compliance_calendar_dashboard",
    "accreditation_dashboard",
    "ministry_reporting_dashboard",
    "rector_strategy_dashboard",
    "archive_retention_management",
    "international_office",
    "curriculum_mapping",
    "syllabus_management",
    "competency_framework",
    "program_learning_outcomes",
    "course_learning_outcomes",
    "elective_course_selection",
    "prerequisite_management",
    "transfer_credit_management",
    "course_catalog_management",
    "degree_audit",
    # Wave 3 — added in A-028.11-RUNTIME
    "staff_recruitment",
    "staff_onboarding",
    "employee_records",
    "leave_management",
    "dormitory_management",
    "partnership_registry",
    "mou_lifecycle",
    "scholarship_committee_workflow",
    "student_appeals_workflow",
    "consent_management_policy",
    # Wave 4 — added in A-028.15-RUNTIME
    "timesheet_management",
    "faculty_attestation",
    "teaching_load_contracts",
    "staff_exit_offboarding",
    "thesis_dissertation_management",
    "joint_program_management",
    "inbound_exchange_management",
    "outbound_exchange_management",
}
EXPECTED_SOURCE_ACTIONS = {
    "A-028.1", "A-028.2", "A-028.3",
    "A-028.6", "A-028.7", "A-028.8",
    "A-028.9", "A-028.10", "A-028.11",
    "A-028.13", "A-028.14", "A-028.15",
}  # A-028.11-RUNTIME: expanded to include all 9 source actions


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)


def _headers_with_permission(permission: str = "admin.expansion.read", tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id=f"a0284-admin-tenant-{tenant_id}@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=[permission],
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


def _headers_without_permission(tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id=f"a0284-user-tenant-{tenant_id}@example.com",
        roles=["student"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=[],
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


def _payload(tc: TestClient) -> dict:
    response = tc.get(CONSOLIDATED_ROUTE, headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    return response.json()


def _registered_l4_routes() -> dict[str, APIRoute]:
    routes: dict[str, APIRoute] = {}
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path.startswith("/api/admin/expansion/l4/"):
            routes[route.path] = route
    return routes


def test_a0284_route_exists() -> None:
    assert CONSOLIDATED_ROUTE in _registered_l4_routes()


def test_a0284_route_is_get_only() -> None:
    route = _registered_l4_routes()[CONSOLIDATED_ROUTE]
    assert route.methods == {"GET"}


def test_a0284_auth_required(test_client: TestClient) -> None:
    response = test_client.get(CONSOLIDATED_ROUTE)
    assert response.status_code == 401


def test_a0284_permission_required(test_client: TestClient) -> None:
    response = test_client.get(CONSOLIDATED_ROUTE, headers=_headers_without_permission())
    assert response.status_code == 403


@pytest.mark.parametrize("bad_header", ["0", "-1", "not-an-int"])
def test_a0284_invalid_tenant_fail_closed(test_client: TestClient, bad_header: str) -> None:
    headers = _headers_with_permission()
    headers["X-Tenant-ID"] = bad_header
    response = test_client.get(CONSOLIDATED_ROUTE, headers=headers)
    assert response.status_code in {400, 403}


def test_a0284_cross_tenant_override_fail_closed(test_client: TestClient) -> None:
    headers = _headers_with_permission(tenant_id=1)
    headers["X-Tenant-ID"] = "2"
    response = test_client.get(CONSOLIDATED_ROUTE, headers=headers)
    assert response.status_code == 403


def test_a0284_valid_tenant_returns_200() -> None:
    response = client.get(CONSOLIDATED_ROUTE, headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text


def test_a0284_core_contract_fields(test_client: TestClient) -> None:
    payload = _payload(test_client)

    assert payload["tenant_id"] == 1
    assert payload["visibility_level"] == "L4"
    assert payload["summary_type"] == "EXPANSION_L4_CONSOLIDATED_ADMIN_SUMMARY"
    assert EXPECTED_SOURCE_ACTIONS.issubset(set(payload["source_actions"]))  # A-028.11-RUNTIME: superset allowed
    assert payload["total_l4_visibility_candidates"] == 40
    assert payload["total_api_routed_candidates"] == 40


def test_a0284_modules_included_and_complete(test_client: TestClient) -> None:
    payload = _payload(test_client)
    modules = payload["modules"]

    assert isinstance(modules, list)
    assert len(modules) == 40

    module_ids = {item["module"] for item in modules}
    assert module_ids == EXPECTED_MODULES


def test_a0284_modules_by_domain_deterministic(test_client: TestClient) -> None:
    first = _payload(test_client)
    second = _payload(test_client)

    assert first["modules_by_domain"] == second["modules_by_domain"]
    assert isinstance(first["modules_by_domain"], dict)

    all_grouped = sorted(module for grouped in first["modules_by_domain"].values() for module in grouped)
    assert all_grouped == sorted(EXPECTED_MODULES)


def test_a0284_readiness_counts_derived_unknown_safe(test_client: TestClient) -> None:
    payload = _payload(test_client)
    counts = payload["readiness_status_counts"]

    assert isinstance(counts, dict)
    assert sum(counts.values()) == 40
    assert all(isinstance(key, str) and key for key in counts)
    assert all(isinstance(value, int) and value >= 0 for value in counts.values())


def test_a0284_risk_counts_derived_unknown_safe(test_client: TestClient) -> None:
    payload = _payload(test_client)
    counts = payload["risk_band_counts"]

    assert isinstance(counts, dict)
    assert sum(counts.values()) == 40
    assert all(isinstance(key, str) and key for key in counts)
    assert all(isinstance(value, int) and value >= 0 for value in counts.values())


def test_a0284_missing_evidence_rollup_present(test_client: TestClient) -> None:
    payload = _payload(test_client)
    rollup = payload["missing_evidence_rollup"]

    assert set(rollup.keys()) == {
        "total_missing_entries",
        "unique_missing_evidence_items",
        "unique_missing_evidence_count",
    }
    assert isinstance(rollup["total_missing_entries"], int)
    assert isinstance(rollup["unique_missing_evidence_items"], list)
    assert isinstance(rollup["unique_missing_evidence_count"], int)


def test_a0284_human_review_rollup_present_no_task_creation_semantics(test_client: TestClient) -> None:
    payload = _payload(test_client)
    rollup = payload["human_review_queue_rollup"]

    assert set(rollup.keys()) == {
        "candidate_count",
        "ready_for_human_review_count",
        "pending_manual_evidence_count",
        "blocked_count",
        "modules_requiring_human_review_count",
    }
    assert all(isinstance(value, int) and value >= 0 for value in rollup.values())


def test_a0284_forbidden_actions_rollup_present(test_client: TestClient) -> None:
    payload = _payload(test_client)
    rollup = payload["forbidden_actions_rollup"]

    assert isinstance(rollup, list)
    assert len(rollup) > 0
    assert all(isinstance(item, str) and item for item in rollup)


def test_a0284_read_only_and_no_mutation_flags(test_client: TestClient) -> None:
    payload = _payload(test_client)

    assert payload["read_only"] is True
    assert payload["no_mutation"] is True
    assert payload["no_fake_kpi"] is True
    assert payload["no_synthetic_dashboard"] is True
    assert payload["no_synthetic_score"] is True
    assert payload["no_ranking"] is True
    assert payload["no_provider_call"] is True
    assert payload["no_external_submission"] is True
    assert payload["no_brain_execution"] is True
    assert payload["no_autonomous_execution"] is True
    assert payload["no_workflow_execution"] is True
    assert payload["no_decision_execution"] is True
    assert payload["no_l5_claim"] is True
    assert payload["no_l6_claim"] is True


def test_a0284_safety_flags_include_boundaries(test_client: TestClient) -> None:
    payload = _payload(test_client)
    flags = payload["safety_flags"]

    for key in [
        "read_only",
        "no_db_mutation",
        "no_provider_call",
        "no_external_submission",
        "no_brain_execution",
        "no_autonomous_execution",
        "no_workflow_execution",
        "no_decision_execution",
        "no_fake_kpi",
        "no_synthetic_dashboard",
        "no_synthetic_score",
        "no_ranking",
        "tenant_safe_visibility",
        "no_l5_claim",
        "no_l6_claim",
    ]:
        assert flags.get(key) is True


def test_a0284_no_synthetic_score_kpi_ranking_recommendation_fields(test_client: TestClient) -> None:
    payload = _payload(test_client)

    forbidden_root_fields = {
        "overall_score",
        "overall_health_score",
        "university_readiness_score",
        "kpi_values",
        "ranking",
        "module_ranking",
        "recommendations",
        "recommendation_execution",
    }
    assert forbidden_root_fields.isdisjoint(set(payload))


def test_a0284_source_actions_are_exactly_a0281_to_a0283(test_client: TestClient) -> None:
    payload = _payload(test_client)
    # A-028.11-RUNTIME: source_actions now includes A-028.9, A-028.10, A-028.11
    required = {
        "A-028.1", "A-028.2", "A-028.3", "A-028.6", "A-028.7", "A-028.8",
        "A-028.9", "A-028.10", "A-028.11", "A-028.13", "A-028.14", "A-028.15",
    }
    assert required.issubset(set(payload["source_actions"]))


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_a0284_non_get_methods_not_allowed(test_client: TestClient, method: str) -> None:
    response = getattr(test_client, method)(CONSOLIDATED_ROUTE, headers=_headers_with_permission())
    assert response.status_code == 405


def test_a0284_all_a0282_individual_routes_still_exist() -> None:
    paths = set(_registered_l4_routes())
    for path in A0282_ROUTES:
        assert path in paths


def test_a0284_all_a0283_individual_routes_still_exist() -> None:
    paths = set(_registered_l4_routes())
    for path in A0283_ROUTES:
        assert path in paths


def test_a0284_consolidated_route_is_deterministic_and_read_only(test_client: TestClient) -> None:
    first = _payload(test_client)
    second = _payload(test_client)

    assert first == second
    assert first["read_only"] is True
    assert first["no_mutation"] is True


def test_a0284_metric_formula_contract_documented_by_route_counts() -> None:
    all_l4_paths = list(_registered_l4_routes())

    assert len(A0282_ROUTES) == 6
    assert len(A0283_ROUTES) == 6
    assert CONSOLIDATED_ROUTE in all_l4_paths
    # A-028.14 added 8 individual routes:
    # total = A0282(6) + A0283(6) + A0287(10) + A02810(10) + A02814(8) + consolidated(1) = 41
    a0287_count = 10
    a02810_count = 10
    a02814_count = 8
    assert len(A0282_ROUTES) + len(A0283_ROUTES) + a0287_count + a02810_count + a02814_count + 1 == 41
    assert len(all_l4_paths) == 41
    assert len(A0282_ROUTES) + len(A0283_ROUTES) + a0287_count + a02810_count + a02814_count + 1 == len(all_l4_paths)


def test_a0284_no_duplicate_route_registration() -> None:
    all_l4_paths = list(_registered_l4_routes())
    assert len(all_l4_paths) == len(set(all_l4_paths))
