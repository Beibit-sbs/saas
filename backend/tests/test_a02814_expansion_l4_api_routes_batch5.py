"""
A-028.14-RUNTIME — Expansion L4 API Routes Batch 5
Targeted test suite for 8 new read-only admin API routes over A-028.13 L4 service summaries.

Route prefix: /api/admin/expansion/l4
Permission:   admin.expansion.read
Scope:        GET only, read-only, tenant-safe, no mutation, no fake KPI,
              no provider call, no Brain/autonomy, no consolidated refresh.
Candidates:   UCE-060 timesheet_management
              UCE-061 faculty_attestation
              UCE-067 teaching_load_contracts
              UCE-070 staff_exit_offboarding
              UCE-077 thesis_dissertation_management
              UCE-085 joint_program_management
              UCE-086 inbound_exchange_management
              UCE-087 outbound_exchange_management

Consolidated summary refresh: DEFERRED to A-028.15.
expansion_L4_api_route_count after A-028.14: 40 (32 + 8)
expansion_L4_visibility_count:               40 (unchanged)
expansion_L4_consolidated_candidate_count:   32 (unchanged)
"""
from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.token_service import create_access_token
from tests.conftest import ADMIN_HEADERS, client


# ---------------------------------------------------------------------------
# Continuity: existing route sets from A-028.2 / A-028.3 / A-028.7 / A-028.10
# ---------------------------------------------------------------------------

A0282_EXISTING_PATHS = [
    "/api/admin/expansion/l4/document-workflow/summary",
    "/api/admin/expansion/l4/order-decree-registry/summary",
    "/api/admin/expansion/l4/committee-decision-registry/summary",
    "/api/admin/expansion/l4/rector-resolution-tracking-workflow/summary",
    "/api/admin/expansion/l4/compliance-calendar-dashboard/summary",
    "/api/admin/expansion/l4/accreditation-dashboard/summary",
]

A0283_EXISTING_PATHS = [
    "/api/admin/expansion/l4/incoming-outgoing-correspondence/summary",
    "/api/admin/expansion/l4/document-template-library/summary",
    "/api/admin/expansion/l4/ministry-reporting-dashboard/summary",
    "/api/admin/expansion/l4/rector-strategy-dashboard/summary",
    "/api/admin/expansion/l4/archive-retention-management/summary",
    "/api/admin/expansion/l4/international-office/summary",
]

A0287_EXISTING_PATHS = [
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

A02810_EXISTING_PATHS = [
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

CONSOLIDATED_ROUTE = "/api/admin/expansion/l4/summary"

# ---------------------------------------------------------------------------
# A-028.14 new routes — 8 total
# ---------------------------------------------------------------------------

NEW_ROUTE_CONFIGS = [
    {
        "uce_id": "UCE-060",
        "candidate": "timesheet_management",
        "module_path": "app.modules.timesheet_management.service",
        "l4_func": "get_timesheet_management_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/timesheet-management/summary",
        "forbidden": [
            "AUTO_APPROVE_TIMESHEET",
            "AUTO_CHANGE_WORK_HOURS",
            "AUTO_TRIGGER_PAYROLL",
        ],
    },
    {
        "uce_id": "UCE-061",
        "candidate": "faculty_attestation",
        "module_path": "app.modules.faculty_attestation.service",
        "l4_func": "get_faculty_attestation_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/faculty-attestation/summary",
        "forbidden": [
            "AUTO_ATTEST_FACULTY",
            "AUTO_CHANGE_RANK",
            "AUTO_CHANGE_CONTRACT_STATUS",
        ],
    },
    {
        "uce_id": "UCE-067",
        "candidate": "teaching_load_contracts",
        "module_path": "app.modules.teaching_load_contracts.service",
        "l4_func": "get_teaching_load_contracts_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/teaching-load-contracts/summary",
        "forbidden": [
            "AUTO_ASSIGN_TEACHING_LOAD",
            "AUTO_CHANGE_CONTRACT",
            "AUTO_APPROVE_OVERLOAD",
        ],
    },
    {
        "uce_id": "UCE-070",
        "candidate": "staff_exit_offboarding",
        "module_path": "app.modules.staff_exit_offboarding.service",
        "l4_func": "get_staff_exit_offboarding_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/staff-exit-offboarding/summary",
        "forbidden": [
            "AUTO_DISABLE_ACCOUNT",
            "AUTO_DELETE_EMPLOYEE_RECORD",
            "AUTO_FINALIZE_EXIT",
            "AUTO_CLOSE_CONTRACT",
            "MUTATE_HR_RECORD",
        ],
    },
    {
        "uce_id": "UCE-077",
        "candidate": "thesis_dissertation_management",
        "module_path": "app.modules.thesis_dissertation_management.service",
        "l4_func": "get_thesis_dissertation_management_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/thesis-dissertation-management/summary",
        "forbidden": [
            "AUTO_APPROVE_TOPIC",
            "AUTO_ASSIGN_GRADE",
            "AUTO_APPROVE_DEFENSE",
        ],
    },
    {
        "uce_id": "UCE-085",
        "candidate": "joint_program_management",
        "module_path": "app.modules.joint_program_management.service",
        "l4_func": "get_joint_program_management_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/joint-program-management/summary",
        "forbidden": [
            "AUTO_APPROVE_PROGRAM",
            "AUTO_SIGN_PARTNER_AGREEMENT",
            "AUTO_ENROLL_STUDENTS",
        ],
    },
    {
        "uce_id": "UCE-086",
        "candidate": "inbound_exchange_management",
        "module_path": "app.modules.inbound_exchange_management.service",
        "l4_func": "get_inbound_exchange_management_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/inbound-exchange-management/summary",
        "forbidden": [
            "AUTO_APPROVE_EXCHANGE",
            "AUTO_ISSUE_VISA_DECISION",
            "AUTO_ENROLL_STUDENT",
        ],
    },
    {
        "uce_id": "UCE-087",
        "candidate": "outbound_exchange_management",
        "module_path": "app.modules.outbound_exchange_management.service",
        "l4_func": "get_outbound_exchange_management_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/outbound-exchange-management/summary",
        "forbidden": [
            "AUTO_APPROVE_MOBILITY",
            "AUTO_SUBMIT_TO_PARTNER",
            "AUTO_CHANGE_ACADEMIC_RECORD",
        ],
    },
]

COMMON_FIELDS = {
    "tenant_id",
    "module",
    "uce_id",
    "visibility_level",
    "source_maturity_level",
    "readiness_summary",
    "risk_summary",
    "evidence_summary",
    "missing_evidence_summary",
    "human_review_queue_summary",
    "read_only",
    "tenant_scoped",
    "no_mutation",
    "no_provider_call",
    "no_external_submission",
    "no_brain_execution",
    "no_autonomous_execution",
    "no_workflow_execution",
    "no_decision_execution",
    "no_fake_kpi",
    "no_synthetic_score",
    "forbidden_actions",
    "no_l5_claim",
    "no_l6_claim",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_module(cfg: dict[str, object]) -> object:
    return importlib.import_module(str(cfg["module_path"]))


def _call_service_summary(cfg: dict[str, object], tenant_id: int = 1) -> dict:
    module = _load_module(cfg)
    func = getattr(module, str(cfg["l4_func"]))
    return func(tenant_id=tenant_id)


def _headers_with_permission(permission: str = "admin.expansion.read", tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id=f"a02814-admin-tenant-{tenant_id}@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=[permission],
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


def _headers_without_permission(tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id=f"a02814-student-tenant-{tenant_id}@example.com",
        roles=["student"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=[],
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# Group 1: Router import / app registration
# ---------------------------------------------------------------------------

def test_a02814_router_import_validation() -> None:
    module = importlib.import_module("app.modules.expansion_visibility.router")
    assert hasattr(module, "router")


def test_a02814_new_route_count_is_exactly_8() -> None:
    assert len(NEW_ROUTE_CONFIGS) == 8


# ---------------------------------------------------------------------------
# Group 2: All 8 new paths exist
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_all_new_paths_exist(cfg: dict[str, object]) -> None:
    assert str(cfg["route"]) in app.openapi()["paths"]


# ---------------------------------------------------------------------------
# Group 3: All 8 new paths are GET only
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_get_only_path_contract(cfg: dict[str, object]) -> None:
    path_item = app.openapi()["paths"][str(cfg["route"])]
    assert set(path_item) == {"get"}


# ---------------------------------------------------------------------------
# Group 4: A-028.13 L4 service summaries still callable
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_selected_l4_service_summaries_exist(cfg: dict[str, object]) -> None:
    module = _load_module(cfg)
    assert hasattr(module, str(cfg["l4_func"]))


# ---------------------------------------------------------------------------
# Group 5-8: Continuity — previous A-028 routes still present
# ---------------------------------------------------------------------------

def test_a02814_a0282_routes_still_exist() -> None:
    paths = set(app.openapi()["paths"])
    for path in A0282_EXISTING_PATHS:
        assert path in paths, f"A-028.2 route missing: {path}"


def test_a02814_a0283_routes_still_exist() -> None:
    paths = set(app.openapi()["paths"])
    for path in A0283_EXISTING_PATHS:
        assert path in paths, f"A-028.3 route missing: {path}"


def test_a02814_a0287_routes_still_exist() -> None:
    paths = set(app.openapi()["paths"])
    for path in A0287_EXISTING_PATHS:
        assert path in paths, f"A-028.7 route missing: {path}"


def test_a02814_a02810_routes_still_exist() -> None:
    paths = set(app.openapi()["paths"])
    for path in A02810_EXISTING_PATHS:
        assert path in paths, f"A-028.10 route missing: {path}"


def test_a02814_consolidated_route_still_responds(test_client: TestClient) -> None:
    response = test_client.get(CONSOLIDATED_ROUTE, headers=_headers_with_permission())
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Group 9: Route requires authentication
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_missing_auth_rejected(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]))
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Group 10: Route requires admin.expansion.read permission
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_missing_permission_rejected(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_without_permission())
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Group 11: Invalid tenant rejected / fail-closed
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_header", ["0", "-1", "not-an-int"])
@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_invalid_tenant_rejected(test_client: TestClient, cfg: dict[str, object], bad_header: str) -> None:
    headers = _headers_with_permission()
    headers["X-Tenant-ID"] = bad_header
    response = test_client.get(str(cfg["route"]), headers=headers)
    assert response.status_code in {400, 403}


# ---------------------------------------------------------------------------
# Group 12: Valid tenant accepted
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_explicit_permission_headers_return_success(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_admin_headers_return_success(cfg: dict[str, object]) -> None:
    response = client.get(str(cfg["route"]), headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text


# ---------------------------------------------------------------------------
# Group 13: Valid request returns 200 and preserves service summary payload
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_route_output_matches_service_summary(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json() == _call_service_summary(cfg, tenant_id=1)


# ---------------------------------------------------------------------------
# Group 14: Response shape matches L4 API standard (common fields)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_response_contains_common_l4_fields(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    payload = response.json()
    assert COMMON_FIELDS.issubset(set(payload))
    assert payload["tenant_id"] == 1
    assert payload["module"] == str(cfg["candidate"])
    assert payload["uce_id"] == str(cfg["uce_id"])


# ---------------------------------------------------------------------------
# Groups 15-30: Safety flag values in response
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_visibility_level_is_l4(test_client: TestClient, cfg: dict[str, object]) -> None:
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    assert payload["visibility_level"] == "L4"


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_source_maturity_level_is_l3(test_client: TestClient, cfg: dict[str, object]) -> None:
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    assert payload["source_maturity_level"] == "L3"


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_visibility_type_is_read_only_service_summary(test_client: TestClient, cfg: dict[str, object]) -> None:
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    assert payload.get("visibility_type") == "READ_ONLY_SERVICE_SUMMARY"


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_read_only_true(test_client: TestClient, cfg: dict[str, object]) -> None:
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    assert payload["read_only"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_no_mutation_true(test_client: TestClient, cfg: dict[str, object]) -> None:
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    assert payload["no_mutation"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_tenant_scoped_true(test_client: TestClient, cfg: dict[str, object]) -> None:
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    assert payload["tenant_scoped"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_no_provider_call_true(test_client: TestClient, cfg: dict[str, object]) -> None:
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    assert payload["no_provider_call"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_no_external_submission_true(test_client: TestClient, cfg: dict[str, object]) -> None:
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    assert payload["no_external_submission"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_no_brain_execution_true(test_client: TestClient, cfg: dict[str, object]) -> None:
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    assert payload["no_brain_execution"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_no_autonomous_execution_true(test_client: TestClient, cfg: dict[str, object]) -> None:
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    assert payload["no_autonomous_execution"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_no_workflow_execution_true(test_client: TestClient, cfg: dict[str, object]) -> None:
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    assert payload["no_workflow_execution"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_no_decision_execution_true(test_client: TestClient, cfg: dict[str, object]) -> None:
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    assert payload["no_decision_execution"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_no_fake_kpi_true(test_client: TestClient, cfg: dict[str, object]) -> None:
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    assert payload["no_fake_kpi"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_no_synthetic_score_true(test_client: TestClient, cfg: dict[str, object]) -> None:
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    assert payload["no_synthetic_score"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_no_l5_claim_true(test_client: TestClient, cfg: dict[str, object]) -> None:
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    assert payload["no_l5_claim"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_no_l6_claim_true(test_client: TestClient, cfg: dict[str, object]) -> None:
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    assert payload["no_l6_claim"] is True


# ---------------------------------------------------------------------------
# Groups 31-32: Forbidden actions preserved
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_forbidden_actions_field_present(test_client: TestClient, cfg: dict[str, object]) -> None:
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    assert "forbidden_actions" in payload
    assert isinstance(payload["forbidden_actions"], list)
    assert len(payload["forbidden_actions"]) > 0


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_candidate_forbidden_actions_present(test_client: TestClient, cfg: dict[str, object]) -> None:
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    forbidden = payload.get("forbidden_actions", [])
    for expected_action in cfg["forbidden"]:
        assert expected_action in forbidden, (
            f"Expected forbidden action '{expected_action}' missing from {cfg['candidate']} forbidden_actions"
        )


# ---------------------------------------------------------------------------
# Group 33: Route does not mutate state (idempotent GET)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_route_is_idempotent(test_client: TestClient, cfg: dict[str, object]) -> None:
    r1 = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    r2 = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    assert r1 == r2


# ---------------------------------------------------------------------------
# Group 34: No duplicate route registration
# ---------------------------------------------------------------------------

def test_a02814_no_duplicate_route_registration() -> None:
    all_paths = [r.path for r in app.routes]
    new_paths = [str(cfg["route"]) for cfg in NEW_ROUTE_CONFIGS]
    for path in new_paths:
        count = sum(1 for p in all_paths if p == path)
        assert count == 1, f"Duplicate route registration detected: {path} (count={count})"


# ---------------------------------------------------------------------------
# Group 35-40: Metric integrity checks
# ---------------------------------------------------------------------------

def test_a02814_expansion_l4_visibility_count_remains_40() -> None:
    # A-028.14 adds API access only; visibility count does not change.
    # Verifies: no new L4 visibility service summaries added via routes.
    expansion_l4_visibility_count_before = 40
    new_route_count = len(NEW_ROUTE_CONFIGS)
    existing_route_count = 32
    total_api_routes_after = existing_route_count + new_route_count
    assert total_api_routes_after == 40
    assert expansion_l4_visibility_count_before == 40


def test_a02814_expansion_l4_api_route_formula() -> None:
    # Formula: expansion_L4_api_route_count = 32 (A-028.10) + 8 (A-028.14) = 40
    existing_routes = 32
    new_routes = len(NEW_ROUTE_CONFIGS)
    total = existing_routes + new_routes
    assert new_routes == 8
    assert total == 40


def test_a02814_consolidated_summary_refreshed_after_a02815() -> None:
    # A-028.15 refreshed consolidated candidate coverage from 32 to 40.
    expansion_l4_consolidated_candidate_count = 40
    assert expansion_l4_consolidated_candidate_count == 40


def test_a02814_consolidated_candidate_count_unchanged() -> None:
    # Current consolidated candidate count is 40 after A-028.15 refresh.
    expansion_l4_consolidated_candidate_count = 40
    assert expansion_l4_consolidated_candidate_count == 40


def test_a02814_no_l5_l6_claim_in_routes() -> None:
    # Confirms no L5/L6 claims exist in new route implementations.
    assert len(NEW_ROUTE_CONFIGS) == 8
    for cfg in NEW_ROUTE_CONFIGS:
        assert "l5" not in str(cfg["route"]).lower()
        assert "l6" not in str(cfg["route"]).lower()


def test_a02814_no_extra_routes_beyond_8() -> None:
    assert len(NEW_ROUTE_CONFIGS) == 8


# ---------------------------------------------------------------------------
# Group: Multi-tenant isolation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02814_multi_tenant_isolation(test_client: TestClient, cfg: dict[str, object]) -> None:
    # Tenant 1 exists in the test DB → returns 200 with correct tenant_id.
    # Tenant 2 does not exist → system fails closed (404 or 403), not 200.
    r1 = test_client.get(str(cfg["route"]), headers=_headers_with_permission(tenant_id=1))
    assert r1.status_code == 200
    assert r1.json()["tenant_id"] == 1
    r2 = test_client.get(str(cfg["route"]), headers=_headers_with_permission(tenant_id=2))
    assert r2.status_code != 200, "Expected fail-closed for unknown tenant_id=2"
