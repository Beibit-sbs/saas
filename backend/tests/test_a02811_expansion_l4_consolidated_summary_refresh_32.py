"""
A-028.11-RUNTIME — Expansion L4 Consolidated Summary Refresh to 32 Candidates
Targeted regression suite for the consolidated admin summary endpoint.

Strategy: REFRESH_EXISTING_ENDPOINT_ONLY
Endpoint:  GET /api/admin/expansion/l4/summary
Permission: admin.expansion.read
Candidates (current runtime): 40 (wave 1×12 + wave 2×10 + wave 3×10 + wave 4×8)
UCE-046 consent_management_policy: INCLUDED
UCE-098 procurement_plan_approval_workflow: EXCLUDED

Safety boundary:
- No new endpoint created
- No mutation / no provider call / no Brain / no autonomy
- Read-only, tenant-safe, RBAC-gated, aggregation-only
"""
from __future__ import annotations

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.token_service import create_access_token
from tests.conftest import ADMIN_HEADERS

CONSOLIDATED_ROUTE = "/api/admin/expansion/l4/summary"
PROHIBITED_UCE098_ROUTE = "/api/admin/expansion/l4/procurement-plan-approval-workflow/summary"

# All candidates organised by wave (currently 40 after A-028.15 refresh)
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

ALL_CANDIDATES = FIRST_WAVE_CANDIDATES + SECOND_WAVE_CANDIDATES + THIRD_WAVE_CANDIDATES + FOURTH_WAVE_CANDIDATES

ALL_MODULE_NAMES = {module for _, module in ALL_CANDIDATES}
ALL_UCE_IDS = {uce_id for uce_id, _ in ALL_CANDIDATES}

EXPECTED_SOURCE_ACTIONS = {
    "A-028.1", "A-028.2", "A-028.3",
    "A-028.6", "A-028.7", "A-028.8",
    "A-028.9", "A-028.10", "A-028.11",
    "A-028.13", "A-028.14", "A-028.15",
}

# Individual route paths from all prior batches
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


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)


def _headers_with_permission(permission: str = "admin.expansion.read", tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id=f"a02811-admin-tenant-{tenant_id}@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=[permission],
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


def _headers_without_permission(tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id=f"a02811-user-tenant-{tenant_id}@example.com",
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


# ── Group 1: Route Registration ────────────────────────────────────────────────

def test_a02811_consolidated_route_exists() -> None:
    """GET /api/admin/expansion/l4/summary still registered after refresh."""
    assert CONSOLIDATED_ROUTE in _registered_l4_routes()


def test_a02811_consolidated_route_is_get_only() -> None:
    """Consolidated summary must not register mutating HTTP methods."""
    route = _registered_l4_routes()[CONSOLIDATED_ROUTE]
    assert route.methods == {"GET"}


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_a02811_non_get_methods_rejected(test_client: TestClient, method: str) -> None:
    response = getattr(test_client, method)(CONSOLIDATED_ROUTE, headers=_headers_with_permission())
    assert response.status_code == 405


# ── Group 2: Authentication ────────────────────────────────────────────────────

def test_a02811_auth_required_unauthenticated(test_client: TestClient) -> None:
    """Unauthenticated request must be rejected."""
    response = test_client.get(CONSOLIDATED_ROUTE)
    assert response.status_code == 401


# ── Group 3: Permission ────────────────────────────────────────────────────────

def test_a02811_admin_expansion_read_required(test_client: TestClient) -> None:
    """Missing admin.expansion.read permission must be rejected with 403."""
    response = test_client.get(CONSOLIDATED_ROUTE, headers=_headers_without_permission())
    assert response.status_code == 403


def test_a02811_wrong_permission_rejected(test_client: TestClient) -> None:
    response = test_client.get(CONSOLIDATED_ROUTE, headers=_headers_with_permission("some.other.permission"))
    assert response.status_code == 403


# ── Group 4: Tenant Fail-Closed ────────────────────────────────────────────────

@pytest.mark.parametrize("bad_header", ["0", "-1", "not-an-int", ""])
def test_a02811_invalid_tenant_fail_closed(test_client: TestClient, bad_header: str) -> None:
    headers = _headers_with_permission()
    headers["X-Tenant-ID"] = bad_header
    response = test_client.get(CONSOLIDATED_ROUTE, headers=headers)
    assert response.status_code in {400, 403}


def test_a02811_cross_tenant_override_fail_closed(test_client: TestClient) -> None:
    headers = _headers_with_permission(tenant_id=1)
    headers["X-Tenant-ID"] = "2"
    response = test_client.get(CONSOLIDATED_ROUTE, headers=headers)
    assert response.status_code == 403


# ── Group 5: Happy Path ────────────────────────────────────────────────────────

def test_a02811_valid_tenant_returns_200(test_client: TestClient) -> None:
    response = test_client.get(CONSOLIDATED_ROUTE, headers=_headers_with_permission())
    assert response.status_code == 200, response.text


# ── Group 6: Response Schema ───────────────────────────────────────────────────

def test_a02811_visibility_level_is_l4(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert payload.get("visibility_level") == "L4"


def test_a02811_summary_type_correct(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert payload.get("summary_type") == "EXPANSION_L4_CONSOLIDATED_ADMIN_SUMMARY"


def test_a02811_coverage_version_is_a02815(test_client: TestClient) -> None:
    """coverage_version field must be present and set to A-028.15."""
    payload = _payload(test_client)
    cv = payload.get("coverage_version") or payload.get("summary_version")
    assert cv == "A-028.15", f"Expected coverage_version='A-028.15', got {cv!r}"


def test_a02811_tenant_id_present(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert isinstance(payload.get("tenant_id"), int)
    assert payload["tenant_id"] == 1


# ── Group 7: Source Actions ────────────────────────────────────────────────────

def test_a02811_source_actions_include_all_required_batches(test_client: TestClient) -> None:
    payload = _payload(test_client)
    source_actions = set(payload.get("source_actions", []))
    assert EXPECTED_SOURCE_ACTIONS.issubset(source_actions), (
        f"Missing source actions. Expected all of {EXPECTED_SOURCE_ACTIONS}, got {source_actions}"
    )


def test_a02811_source_actions_includes_a0289(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert "A-028.9" in payload.get("source_actions", [])


def test_a02811_source_actions_includes_a02810(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert "A-028.10" in payload.get("source_actions", [])


def test_a02811_source_actions_includes_a02811(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert "A-028.11" in payload.get("source_actions", [])


def test_a02811_source_actions_includes_a02813(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert "A-028.13" in payload.get("source_actions", [])


def test_a02811_source_actions_includes_a02814(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert "A-028.14" in payload.get("source_actions", [])


def test_a02811_source_actions_includes_a02815(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert "A-028.15" in payload.get("source_actions", [])


# ── Group 8: Candidate Counts ──────────────────────────────────────────────────

def test_a02811_total_l4_visibility_candidates_equals_40(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert payload.get("total_l4_visibility_candidates") == 40, (
        f"Expected 40, got {payload.get('total_l4_visibility_candidates')}"
    )


def test_a02811_total_api_routed_candidates_equals_40(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert payload.get("total_api_routed_candidates") == 40, (
        f"Expected 40, got {payload.get('total_api_routed_candidates')}"
    )


def test_a02811_total_consolidated_candidates_equals_40(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert payload.get("total_consolidated_candidates") == 40, (
        f"Expected 40, got {payload.get('total_consolidated_candidates')}"
    )


def test_a02811_modules_length_equals_40(test_client: TestClient) -> None:
    payload = _payload(test_client)
    modules = payload.get("modules", [])
    assert len(modules) == 40, f"Expected 40 modules, got {len(modules)}"


# ── Group 9: Wave Inclusion ────────────────────────────────────────────────────

@pytest.mark.parametrize("uce_id,module", FIRST_WAVE_CANDIDATES)
def test_a02811_first_wave_candidate_included(test_client: TestClient, uce_id: str, module: str) -> None:
    payload = _payload(test_client)
    module_ids = {m["module"] for m in payload["modules"]}
    assert module in module_ids, f"Wave-1 candidate {uce_id}/{module} not found in modules"


@pytest.mark.parametrize("uce_id,module", SECOND_WAVE_CANDIDATES)
def test_a02811_second_wave_candidate_included(test_client: TestClient, uce_id: str, module: str) -> None:
    payload = _payload(test_client)
    module_ids = {m["module"] for m in payload["modules"]}
    assert module in module_ids, f"Wave-2 candidate {uce_id}/{module} not found in modules"


@pytest.mark.parametrize("uce_id,module", THIRD_WAVE_CANDIDATES)
def test_a02811_third_wave_candidate_included(test_client: TestClient, uce_id: str, module: str) -> None:
    payload = _payload(test_client)
    module_ids = {m["module"] for m in payload["modules"]}
    assert module in module_ids, f"Wave-3 candidate {uce_id}/{module} not found in modules"


@pytest.mark.parametrize("uce_id,module", FOURTH_WAVE_CANDIDATES)
def test_a02811_fourth_wave_candidate_included(test_client: TestClient, uce_id: str, module: str) -> None:
    payload = _payload(test_client)
    module_ids = {m["module"] for m in payload["modules"]}
    assert module in module_ids, f"Wave-4 candidate {uce_id}/{module} not found in modules"


# ── Group 10: UCE Boundary ─────────────────────────────────────────────────────

def test_a02811_uce046_consent_management_policy_included(test_client: TestClient) -> None:
    payload = _payload(test_client)
    module_ids = {m["module"] for m in payload["modules"]}
    uce_ids = {m.get("uce_id") for m in payload["modules"]}
    assert "consent_management_policy" in module_ids, "UCE-046 consent_management_policy must be included"
    assert "UCE-046" in uce_ids, "UCE-046 uce_id must appear in modules list"


def test_a02811_uce098_procurement_not_in_modules(test_client: TestClient) -> None:
    payload = _payload(test_client)
    module_ids = {m["module"] for m in payload["modules"]}
    uce_ids = {m.get("uce_id") for m in payload["modules"]}
    assert "procurement_plan_approval_workflow" not in module_ids, "UCE-098 must be excluded"
    assert "UCE-098" not in uce_ids, "UCE-098 uce_id must not appear in modules list"


def test_a02811_uce098_individual_route_absent() -> None:
    """No individual route for UCE-098 procurement-plan-approval-workflow."""
    routes = _registered_l4_routes()
    assert PROHIBITED_UCE098_ROUTE not in routes, f"UCE-098 route must not exist: {PROHIBITED_UCE098_ROUTE}"


def test_a02811_total_candidates_is_not_33(test_client: TestClient) -> None:
    """Confirms UCE-098 is excluded — total is 40, not 33."""
    payload = _payload(test_client)
    modules = payload.get("modules", [])
    assert len(modules) == 40, "UCE-098 exclusion violation: len(modules) must be 40, not 33"


# ── Group 11: Modules Set ──────────────────────────────────────────────────────

def test_a02811_all_module_names_present(test_client: TestClient) -> None:
    payload = _payload(test_client)
    module_ids = {m["module"] for m in payload["modules"]}
    assert module_ids == ALL_MODULE_NAMES, (
        f"Module name mismatch. Missing: {ALL_MODULE_NAMES - module_ids}. "
        f"Unexpected: {module_ids - ALL_MODULE_NAMES}"
    )


def test_a02811_all_uce_ids_present(test_client: TestClient) -> None:
    payload = _payload(test_client)
    uce_ids = {m.get("uce_id") for m in payload["modules"]}
    assert ALL_UCE_IDS.issubset(uce_ids), (
        f"Missing UCE IDs: {ALL_UCE_IDS - uce_ids}"
    )


# ── Group 12: Aggregation ─────────────────────────────────────────────────────

def test_a02811_modules_by_domain_covers_all_40(test_client: TestClient) -> None:
    payload = _payload(test_client)
    by_domain = payload.get("modules_by_domain", {})
    assert isinstance(by_domain, dict)
    all_domain_candidates = [m for candidates in by_domain.values() for m in candidates]
    assert len(all_domain_candidates) == 40, (
        f"modules_by_domain should aggregate 40 candidates, got {len(all_domain_candidates)}"
    )


def test_a02811_readiness_status_counts_sums_to_40(test_client: TestClient) -> None:
    payload = _payload(test_client)
    counts = payload.get("readiness_status_counts", {})
    assert isinstance(counts, dict)
    total = sum(counts.values())
    assert total == 40, f"readiness_status_counts total must be 40, got {total}"


def test_a02811_risk_band_counts_sums_to_40(test_client: TestClient) -> None:
    payload = _payload(test_client)
    counts = payload.get("risk_band_counts", {})
    assert isinstance(counts, dict)
    total = sum(counts.values())
    assert total == 40, f"risk_band_counts total must be 40, got {total}"


def test_a02811_missing_evidence_rollup_present(test_client: TestClient) -> None:
    payload = _payload(test_client)
    rollup = payload.get("missing_evidence_rollup", {})
    assert isinstance(rollup, dict)
    assert "total_missing_entries" in rollup
    assert "unique_missing_evidence_items" in rollup
    assert "unique_missing_evidence_count" in rollup


def test_a02811_human_review_queue_rollup_present_no_task_creation(test_client: TestClient) -> None:
    payload = _payload(test_client)
    rollup = payload.get("human_review_queue_rollup", {})
    assert isinstance(rollup, dict)
    assert "candidate_count" in rollup
    assert "ready_for_human_review_count" in rollup
    # No autonomous task creation semantics
    assert "auto_create" not in rollup
    assert "dispatch_task" not in rollup


def test_a02811_forbidden_actions_rollup_present_and_nonempty(test_client: TestClient) -> None:
    payload = _payload(test_client)
    rollup = payload.get("forbidden_actions_rollup", [])
    assert isinstance(rollup, list)
    assert len(rollup) > 0, "forbidden_actions_rollup must not be empty — boundaries from all 40 modules"
    assert all(isinstance(item, str) and item for item in rollup)


# ── Group 13: Safety Flags ─────────────────────────────────────────────────────

def test_a02811_read_only_true(test_client: TestClient) -> None:
    assert _payload(test_client)["read_only"] is True


def test_a02811_no_mutation_true(test_client: TestClient) -> None:
    assert _payload(test_client)["no_mutation"] is True


def test_a02811_no_fake_kpi_true(test_client: TestClient) -> None:
    assert _payload(test_client)["no_fake_kpi"] is True


def test_a02811_no_synthetic_dashboard_true(test_client: TestClient) -> None:
    assert _payload(test_client)["no_synthetic_dashboard"] is True


def test_a02811_no_synthetic_score_true(test_client: TestClient) -> None:
    assert _payload(test_client)["no_synthetic_score"] is True


def test_a02811_no_ranking_true(test_client: TestClient) -> None:
    assert _payload(test_client)["no_ranking"] is True


def test_a02811_no_provider_call_true(test_client: TestClient) -> None:
    assert _payload(test_client)["no_provider_call"] is True


def test_a02811_no_external_submission_true(test_client: TestClient) -> None:
    assert _payload(test_client)["no_external_submission"] is True


def test_a02811_no_brain_execution_true(test_client: TestClient) -> None:
    assert _payload(test_client)["no_brain_execution"] is True


def test_a02811_no_autonomous_execution_true(test_client: TestClient) -> None:
    assert _payload(test_client)["no_autonomous_execution"] is True


def test_a02811_no_workflow_execution_true(test_client: TestClient) -> None:
    assert _payload(test_client)["no_workflow_execution"] is True


def test_a02811_no_decision_execution_true(test_client: TestClient) -> None:
    assert _payload(test_client)["no_decision_execution"] is True


def test_a02811_no_l5_claim_true(test_client: TestClient) -> None:
    assert _payload(test_client)["no_l5_claim"] is True


def test_a02811_no_l6_claim_true(test_client: TestClient) -> None:
    assert _payload(test_client)["no_l6_claim"] is True


def test_a02811_safety_flags_dict_all_true(test_client: TestClient) -> None:
    flags = _payload(test_client).get("safety_flags", {})
    required_flags = [
        "read_only", "no_db_mutation", "no_provider_call", "no_external_submission",
        "no_brain_execution", "no_autonomous_execution", "no_workflow_execution",
        "no_decision_execution", "no_fake_kpi", "no_synthetic_dashboard",
        "no_synthetic_score", "no_ranking", "tenant_safe_visibility",
        "no_l5_claim", "no_l6_claim",
    ]
    for flag in required_flags:
        assert flags.get(flag) is True, f"safety_flags.{flag} must be True"


# ── Group 14: Prohibited Fields ────────────────────────────────────────────────

def test_a02811_no_overall_score_field(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert "overall_score" not in payload
    assert "overall_health_score" not in payload


def test_a02811_no_kpi_value_field(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert "kpi_value" not in payload
    assert "kpi_values" not in payload


def test_a02811_no_ranking_field(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert "ranking" not in payload
    assert "module_ranking" not in payload


def test_a02811_no_recommendation_execution_field(test_client: TestClient) -> None:
    payload = _payload(test_client)
    assert "recommendation_execution" not in payload


# ── Group 15: Continuity — Prior Routes Still Exist ───────────────────────────

@pytest.mark.parametrize("route", A0282_ROUTES)
def test_a02811_a0282_individual_routes_still_exist(route: str) -> None:
    assert route in _registered_l4_routes(), f"A-028.2 route {route} must still exist"


@pytest.mark.parametrize("route", A0283_ROUTES)
def test_a02811_a0283_individual_routes_still_exist(route: str) -> None:
    assert route in _registered_l4_routes(), f"A-028.3 route {route} must still exist"


@pytest.mark.parametrize("route", A0287_ROUTES)
def test_a02811_a0287_individual_routes_still_exist(route: str) -> None:
    assert route in _registered_l4_routes(), f"A-028.7 route {route} must still exist"


@pytest.mark.parametrize("route", A02810_ROUTES)
def test_a02811_a02810_individual_routes_still_exist(route: str) -> None:
    assert route in _registered_l4_routes(), f"A-028.10 route {route} must still exist"


# ── Group 16: Idempotency ──────────────────────────────────────────────────────

def test_a02811_consolidated_endpoint_idempotent(test_client: TestClient) -> None:
    """Two consecutive GET requests must return identical counts."""
    r1 = test_client.get(CONSOLIDATED_ROUTE, headers=_headers_with_permission())
    r2 = test_client.get(CONSOLIDATED_ROUTE, headers=_headers_with_permission())
    assert r1.status_code == 200
    assert r2.status_code == 200
    p1 = r1.json()
    p2 = r2.json()
    assert p1.get("total_l4_visibility_candidates") == p2.get("total_l4_visibility_candidates")
    assert p1.get("total_consolidated_candidates") == p2.get("total_consolidated_candidates")
    assert len(p1.get("modules", [])) == len(p2.get("modules", []))


# ── Group 17: No Duplicate Routes ─────────────────────────────────────────────

def test_a02811_no_duplicate_l4_route_registration() -> None:
    """All /api/admin/expansion/l4/* paths must be unique."""
    paths = [route.path for route in app.routes
             if isinstance(route, APIRoute) and route.path.startswith("/api/admin/expansion/l4/")]
    assert len(paths) == len(set(paths)), "Duplicate route registration detected"


# ── Group 18: Metric Documentation Assertions ─────────────────────────────────

def test_a02811_expansion_l4_consolidated_summary_count_remains_1() -> None:
    """
    Expansion metric: expansion_L4_consolidated_summary_count must remain 1.
    This is a refresh of the existing endpoint, not a new endpoint.
    A second consolidated endpoint must not be registered.
    """
    consolidated_routes = [
        route.path for route in app.routes
        if isinstance(route, APIRoute) and route.path == "/api/admin/expansion/l4/summary"
    ]
    assert len(consolidated_routes) == 1, (
        "expansion_L4_consolidated_summary_count must stay 1 — "
        f"found {len(consolidated_routes)} consolidated routes"
    )


def test_a02811_consolidated_candidate_count_equals_32(test_client: TestClient) -> None:
    """Documents refreshed consolidated candidate count now equals 40 after A-028.15."""
    payload = _payload(test_client)
    total = payload.get("total_consolidated_candidates") or payload.get("total_l4_visibility_candidates")
    assert total == 40, (
        f"expansion_L4_consolidated_candidate_count must be 40, got {total}"
    )


def test_a02811_procurement_plan_approval_not_in_modules(test_client: TestClient) -> None:
    """Explicit UCE-098 exclusion assertion for metric accuracy."""
    payload = _payload(test_client)
    module_ids = {m["module"] for m in payload["modules"]}
    assert "procurement_plan_approval_workflow" not in module_ids


# ── Group 19: Per-Module Quality Checks ───────────────────────────────────────

@pytest.mark.parametrize("uce_id,module", ALL_CANDIDATES)
def test_a02811_per_module_visibility_level_l4(test_client: TestClient, uce_id: str, module: str) -> None:
    payload = _payload(test_client)
    for m in payload["modules"]:
        if m.get("module") == module:
            assert m.get("visibility_level") == "L4", (
                f"{uce_id}/{module}: visibility_level must be L4, got {m.get('visibility_level')!r}"
            )
            return
    pytest.fail(f"{uce_id}/{module} not found in modules list")


@pytest.mark.parametrize("uce_id,module", ALL_CANDIDATES)
def test_a02811_per_module_read_only_true(test_client: TestClient, uce_id: str, module: str) -> None:
    payload = _payload(test_client)
    for m in payload["modules"]:
        if m.get("module") == module:
            assert m.get("read_only") is True, f"{uce_id}/{module}: read_only must be True"
            return
    pytest.fail(f"{uce_id}/{module} not found in modules list")


@pytest.mark.parametrize("uce_id,module", ALL_CANDIDATES)
def test_a02811_per_module_no_mutation_true(test_client: TestClient, uce_id: str, module: str) -> None:
    payload = _payload(test_client)
    for m in payload["modules"]:
        if m.get("module") == module:
            assert m.get("no_mutation") is True, f"{uce_id}/{module}: no_mutation must be True"
            return
    pytest.fail(f"{uce_id}/{module} not found in modules list")
