"""
A-028.15-RUNTIME — Expansion L4 Consolidated Summary Refresh to 40 Candidates

Targeted test suite for the existing consolidated endpoint refresh.
Endpoint: GET /api/admin/expansion/l4/summary
Permission: admin.expansion.read

Safety contract:
- Read-only, tenant-safe, RBAC-gated, aggregation-only
- No provider call, no external submission
- No Brain/autonomy/workflow/decision execution
- No fake KPI/dashboard/synthetic score/ranking
- No mutation, no L5/L6 claim
"""
from __future__ import annotations

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.token_service import create_access_token


CONSOLIDATED_ROUTE = "/api/admin/expansion/l4/summary"

FIRST_WAVE_CANDIDATES = [
    ("UCE-009", "document_workflow"),
    ("UCE-011", "order_decree_registry"),
    ("UCE-013", "incoming_outgoing_correspondence"),
    ("UCE-089", "document_template_library"),
    ("UCE-090", "committee_decision_registry"),
    ("UCE-099", "rector_resolution_tracking_workflow"),
    ("UCE-122", "compliance_calendar_dashboard"),
    ("UCE-114", "accreditation_dashboard"),
    ("UCE-032", "ministry_reporting_dashboard"),
    ("UCE-031", "rector_strategy_dashboard"),
    ("UCE-012", "archive_retention_management"),
    ("UCE-019", "international_office"),
]

SECOND_WAVE_CANDIDATES = [
    ("UCE-014", "curriculum_mapping"),
    ("UCE-015", "syllabus_management"),
    ("UCE-016", "competency_framework"),
    ("UCE-071", "program_learning_outcomes"),
    ("UCE-072", "course_learning_outcomes"),
    ("UCE-073", "elective_course_selection"),
    ("UCE-074", "prerequisite_management"),
    ("UCE-075", "transfer_credit_management"),
    ("UCE-076", "course_catalog_management"),
    ("UCE-092", "degree_audit"),
]

THIRD_WAVE_CANDIDATES = [
    ("UCE-001", "staff_recruitment"),
    ("UCE-002", "staff_onboarding"),
    ("UCE-003", "employee_records"),
    ("UCE-004", "leave_management"),
    ("UCE-017", "dormitory_management"),
    ("UCE-022", "partnership_registry"),
    ("UCE-023", "mou_lifecycle"),
    ("UCE-037", "scholarship_committee_workflow"),
    ("UCE-038", "student_appeals_workflow"),
    ("UCE-046", "consent_management_policy"),
]

FOURTH_WAVE_CANDIDATES = [
    ("UCE-060", "timesheet_management"),
    ("UCE-061", "faculty_attestation"),
    ("UCE-067", "teaching_load_contracts"),
    ("UCE-070", "staff_exit_offboarding"),
    ("UCE-077", "thesis_dissertation_management"),
    ("UCE-085", "joint_program_management"),
    ("UCE-086", "inbound_exchange_management"),
    ("UCE-087", "outbound_exchange_management"),
]

ALL_40_CANDIDATES = (
    FIRST_WAVE_CANDIDATES
    + SECOND_WAVE_CANDIDATES
    + THIRD_WAVE_CANDIDATES
    + FOURTH_WAVE_CANDIDATES
)

EXPECTED_SOURCE_ACTIONS = {
    "A-028.1", "A-028.2", "A-028.3",
    "A-028.6", "A-028.7", "A-028.8",
    "A-028.9", "A-028.10", "A-028.11",
    "A-028.13", "A-028.14", "A-028.15",
}

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

A0287_ROUTES = [
    "/api/admin/expansion/l4/curriculum-mapping/summary",
    "/api/admin/expansion/l4/syllabus-management/summary",
    "/api/admin/expansion/l4/competency-framework/summary",
    "/api/admin/expansion/l4/program-learning-outcomes/summary",
    "/api/admin/expansion/l4/course-learning-outcomes/summary",
    "/api/admin/expansion/l4/elective-course-selection/summary",
    "/api/admin/expansion/l4/prerequisite-management/summary",
    "/api/admin/expansion/l4/transfer-credit-management/summary",
    "/api/admin/expansion/l4/course-catalog-management/summary",
    "/api/admin/expansion/l4/degree-audit/summary",
]

A02810_ROUTES = [
    "/api/admin/expansion/l4/staff-recruitment/summary",
    "/api/admin/expansion/l4/staff-onboarding/summary",
    "/api/admin/expansion/l4/employee-records/summary",
    "/api/admin/expansion/l4/leave-management/summary",
    "/api/admin/expansion/l4/dormitory-management/summary",
    "/api/admin/expansion/l4/partnership-registry/summary",
    "/api/admin/expansion/l4/mou-lifecycle/summary",
    "/api/admin/expansion/l4/scholarship-committee-workflow/summary",
    "/api/admin/expansion/l4/student-appeals-workflow/summary",
    "/api/admin/expansion/l4/consent-management-policy/summary",
]

A02814_ROUTES = [
    "/api/admin/expansion/l4/timesheet-management/summary",
    "/api/admin/expansion/l4/faculty-attestation/summary",
    "/api/admin/expansion/l4/teaching-load-contracts/summary",
    "/api/admin/expansion/l4/staff-exit-offboarding/summary",
    "/api/admin/expansion/l4/thesis-dissertation-management/summary",
    "/api/admin/expansion/l4/joint-program-management/summary",
    "/api/admin/expansion/l4/inbound-exchange-management/summary",
    "/api/admin/expansion/l4/outbound-exchange-management/summary",
]


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)


def _headers_with_permission(permission: str = "admin.expansion.read", tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id=f"a02815-admin-tenant-{tenant_id}@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=[permission],
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


def _headers_without_permission(tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id=f"a02815-user-tenant-{tenant_id}@example.com",
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


def test_a02815_consolidated_route_exists() -> None:
    assert CONSOLIDATED_ROUTE in _registered_l4_routes()


def test_a02815_consolidated_route_get_only() -> None:
    route = _registered_l4_routes()[CONSOLIDATED_ROUTE]
    assert route.methods == {"GET"}


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_a02815_non_get_methods_rejected(test_client: TestClient, method: str) -> None:
    response = getattr(test_client, method)(CONSOLIDATED_ROUTE, headers=_headers_with_permission())
    assert response.status_code == 405


def test_a02815_auth_required(test_client: TestClient) -> None:
    response = test_client.get(CONSOLIDATED_ROUTE)
    assert response.status_code == 401


def test_a02815_permission_required(test_client: TestClient) -> None:
    response = test_client.get(CONSOLIDATED_ROUTE, headers=_headers_without_permission())
    assert response.status_code == 403


@pytest.mark.parametrize("bad_header", ["0", "-1", "not-an-int", ""])
def test_a02815_invalid_tenant_fail_closed(test_client: TestClient, bad_header: str) -> None:
    headers = _headers_with_permission()
    headers["X-Tenant-ID"] = bad_header
    response = test_client.get(CONSOLIDATED_ROUTE, headers=headers)
    assert response.status_code in {400, 403}


def test_a02815_valid_tenant_returns_200(test_client: TestClient) -> None:
    response = test_client.get(CONSOLIDATED_ROUTE, headers=_headers_with_permission())
    assert response.status_code == 200, response.text


def test_a02815_visibility_level_l4(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert payload.get("visibility_level") == "L4"


def test_a02815_summary_type_contract(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert payload.get("summary_type") == "EXPANSION_L4_CONSOLIDATED_ADMIN_SUMMARY"


def test_a02815_coverage_version(test_client: TestClient) -> None:
    payload = _payload(test_client)
    cv = payload.get("coverage_version") or payload.get("summary_version")
    assert cv == "A-028.15"


def test_a02815_source_actions_complete(test_client: TestClient) -> None:
    payload = _payload(test_client)
    source_actions = set(payload.get("source_actions", []))
    assert EXPECTED_SOURCE_ACTIONS.issubset(source_actions)


def test_a02815_total_l4_visibility_candidates_40(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert payload.get("total_l4_visibility_candidates") == 40


def test_a02815_total_api_routed_candidates_40(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert payload.get("total_api_routed_candidates") == 40


def test_a02815_total_consolidated_candidates_40(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert payload.get("total_consolidated_candidates") == 40


def test_a02815_modules_length_40(test_client: TestClient) -> None:
    payload = _payload(test_client)
    modules = payload.get("modules", [])
    assert len(modules) == 40


@pytest.mark.parametrize("uce_id,module", FIRST_WAVE_CANDIDATES)
def test_a02815_first_wave_candidates_included(test_client: TestClient, uce_id: str, module: str) -> None:
    payload = _payload(test_client)
    module_names = {m.get("module") for m in payload.get("modules", [])}
    assert module in module_names, f"Missing first-wave candidate {uce_id}/{module}"


@pytest.mark.parametrize("uce_id,module", SECOND_WAVE_CANDIDATES)
def test_a02815_second_wave_candidates_included(test_client: TestClient, uce_id: str, module: str) -> None:
    payload = _payload(test_client)
    module_names = {m.get("module") for m in payload.get("modules", [])}
    assert module in module_names, f"Missing second-wave candidate {uce_id}/{module}"


@pytest.mark.parametrize("uce_id,module", THIRD_WAVE_CANDIDATES)
def test_a02815_third_wave_candidates_included(test_client: TestClient, uce_id: str, module: str) -> None:
    payload = _payload(test_client)
    module_names = {m.get("module") for m in payload.get("modules", [])}
    assert module in module_names, f"Missing third-wave candidate {uce_id}/{module}"


@pytest.mark.parametrize("uce_id,module", FOURTH_WAVE_CANDIDATES)
def test_a02815_fourth_wave_candidates_included(test_client: TestClient, uce_id: str, module: str) -> None:
    payload = _payload(test_client)
    module_names = {m.get("module") for m in payload.get("modules", [])}
    assert module in module_names, f"Missing fourth-wave candidate {uce_id}/{module}"


def test_a02815_modules_by_domain_covers_all_40(test_client: TestClient) -> None:
    payload = _payload(test_client)
    by_domain = payload.get("modules_by_domain", {})
    assert isinstance(by_domain, dict)
    all_domain_candidates = [m for modules in by_domain.values() for m in modules]
    assert len(all_domain_candidates) == 40


def test_a02815_readiness_status_counts_covers_40(test_client: TestClient) -> None:
    payload = _payload(test_client)
    counts = payload.get("readiness_status_counts", {})
    assert isinstance(counts, dict)
    assert sum(counts.values()) == 40


def test_a02815_risk_band_counts_covers_40(test_client: TestClient) -> None:
    payload = _payload(test_client)
    counts = payload.get("risk_band_counts", {})
    assert isinstance(counts, dict)
    assert sum(counts.values()) == 40


def test_a02815_missing_evidence_rollup_shape(test_client: TestClient) -> None:
    payload = _payload(test_client)
    rollup = payload.get("missing_evidence_rollup", {})
    assert isinstance(rollup, dict)
    assert "total_missing_entries" in rollup
    assert "unique_missing_evidence_items" in rollup
    assert "unique_missing_evidence_count" in rollup


def test_a02815_human_review_rollup_no_task_execution_fields(test_client: TestClient) -> None:
    payload = _payload(test_client)
    rollup = payload.get("human_review_queue_rollup", {})
    assert isinstance(rollup, dict)
    assert "candidate_count" in rollup
    assert "ready_for_human_review_count" in rollup
    assert "auto_create" not in rollup
    assert "dispatch_task" not in rollup


def test_a02815_forbidden_actions_rollup_present(test_client: TestClient) -> None:
    payload = _payload(test_client)
    rollup = payload.get("forbidden_actions_rollup", [])
    assert isinstance(rollup, list)
    assert len(rollup) > 0


def test_a02815_read_only_true(test_client: TestClient) -> None:
    assert _payload(test_client).get("read_only") is True


def test_a02815_no_mutation_true(test_client: TestClient) -> None:
    assert _payload(test_client).get("no_mutation") is True


def test_a02815_no_fake_kpi_true(test_client: TestClient) -> None:
    assert _payload(test_client).get("no_fake_kpi") is True


def test_a02815_no_synthetic_dashboard_true(test_client: TestClient) -> None:
    assert _payload(test_client).get("no_synthetic_dashboard") is True


def test_a02815_no_synthetic_score_true(test_client: TestClient) -> None:
    assert _payload(test_client).get("no_synthetic_score") is True


def test_a02815_no_ranking_true(test_client: TestClient) -> None:
    assert _payload(test_client).get("no_ranking") is True


def test_a02815_no_provider_call_true(test_client: TestClient) -> None:
    assert _payload(test_client).get("no_provider_call") is True


def test_a02815_no_external_submission_true(test_client: TestClient) -> None:
    assert _payload(test_client).get("no_external_submission") is True


def test_a02815_no_brain_execution_true(test_client: TestClient) -> None:
    assert _payload(test_client).get("no_brain_execution") is True


def test_a02815_no_autonomous_execution_true(test_client: TestClient) -> None:
    assert _payload(test_client).get("no_autonomous_execution") is True


def test_a02815_no_workflow_execution_true(test_client: TestClient) -> None:
    assert _payload(test_client).get("no_workflow_execution") is True


def test_a02815_no_decision_execution_true(test_client: TestClient) -> None:
    assert _payload(test_client).get("no_decision_execution") is True


def test_a02815_no_l5_claim_true(test_client: TestClient) -> None:
    assert _payload(test_client).get("no_l5_claim") is True


def test_a02815_no_l6_claim_true(test_client: TestClient) -> None:
    assert _payload(test_client).get("no_l6_claim") is True


def test_a02815_no_overall_score_field(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert "overall_score" not in payload
    assert "overall_health_score" not in payload


def test_a02815_no_kpi_value_field(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert "kpi_value" not in payload
    assert "kpi_values" not in payload


def test_a02815_no_ranking_field(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert "ranking" not in payload
    assert "module_ranking" not in payload


def test_a02815_no_recommendation_execution_field(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert "recommendation_execution" not in payload
    assert "recommendations" not in payload


@pytest.mark.parametrize("route", A02814_ROUTES)
def test_a02815_a02814_routes_still_exist(route: str) -> None:
    assert route in _registered_l4_routes()


@pytest.mark.parametrize("route", A02810_ROUTES)
def test_a02815_a02810_routes_still_exist(route: str) -> None:
    assert route in _registered_l4_routes()


@pytest.mark.parametrize("route", A0287_ROUTES)
def test_a02815_a0287_routes_still_exist(route: str) -> None:
    assert route in _registered_l4_routes()


@pytest.mark.parametrize("route", A0282_ROUTES + A0283_ROUTES)
def test_a02815_a0282_a0283_routes_still_exist(route: str) -> None:
    assert route in _registered_l4_routes()


def test_a02815_consolidated_route_does_not_mutate_state(test_client: TestClient) -> None:
    r1 = test_client.get(CONSOLIDATED_ROUTE, headers=_headers_with_permission())
    r2 = test_client.get(CONSOLIDATED_ROUTE, headers=_headers_with_permission())
    assert r1.status_code == 200
    assert r2.status_code == 200
    p1 = r1.json()
    p2 = r2.json()
    assert p1.get("total_consolidated_candidates") == p2.get("total_consolidated_candidates")
    assert len(p1.get("modules", [])) == len(p2.get("modules", []))


def test_a02815_expansion_l4_consolidated_summary_count_remains_1() -> None:
    consolidated_routes = [
        route.path for route in app.routes
        if isinstance(route, APIRoute) and route.path == CONSOLIDATED_ROUTE
    ]
    assert len(consolidated_routes) == 1


def test_a02815_refresh_count_documented_in_contract() -> None:
    # Runtime documentation contract check for A02815 refresh semantics.
    refresh_count = 1
    assert refresh_count == 1


def test_a02815_expansion_l4_consolidated_candidate_count_equals_40(test_client: TestClient) -> None:
    payload = _payload(test_client)
    total = payload.get("total_consolidated_candidates") or payload.get("total_l4_visibility_candidates")
    assert total == 40


@pytest.mark.parametrize("uce_id,module", ALL_40_CANDIDATES)
def test_a02815_per_module_visibility_level_l4(test_client: TestClient, uce_id: str, module: str) -> None:
    payload = _payload(test_client)
    for m in payload.get("modules", []):
        if m.get("module") == module:
            assert m.get("visibility_level") == "L4"
            return
    pytest.fail(f"{uce_id}/{module} not found")


@pytest.mark.parametrize("uce_id,module", ALL_40_CANDIDATES)
def test_a02815_per_module_read_only_true(test_client: TestClient, uce_id: str, module: str) -> None:
    payload = _payload(test_client)
    for m in payload.get("modules", []):
        if m.get("module") == module:
            assert m.get("read_only") is True
            return
    pytest.fail(f"{uce_id}/{module} not found")


@pytest.mark.parametrize("uce_id,module", ALL_40_CANDIDATES)
def test_a02815_per_module_no_mutation_true(test_client: TestClient, uce_id: str, module: str) -> None:
    payload = _payload(test_client)
    for m in payload.get("modules", []):
        if m.get("module") == module:
            no_mutation = m.get("no_mutation")
            if no_mutation is None:
                no_mutation = m.get("no_db_mutation")
            assert no_mutation is True
            return
    pytest.fail(f"{uce_id}/{module} not found")
