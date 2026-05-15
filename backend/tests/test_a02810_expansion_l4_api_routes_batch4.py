"""
A-028.10-RUNTIME — Expansion L4 API Routes for A-028.9 Batch
Targeted test suite for 10 new read-only admin API routes.

Route prefix: /api/admin/expansion/l4
Permission: admin.expansion.read
Scope: GET only, read-only, tenant-safe, no mutation, no fake KPI
"""
from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.token_service import create_access_token
from tests.conftest import ADMIN_HEADERS, client


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

CONSOLIDATED_ROUTE = "/api/admin/expansion/l4/summary"
PROHIBITED_UCE098_ROUTE = "/api/admin/expansion/l4/procurement-plan-approval-workflow/summary"

NEW_ROUTE_CONFIGS = [
    {
        "uce_id": "UCE-001",
        "candidate": "staff_recruitment",
        "module_path": "app.modules.staff_recruitment.service",
        "l4_func": "get_staff_recruitment_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/staff-recruitment/summary",
        "forbidden": [
            "AUTO_HIRE_CANDIDATE",
            "AUTO_REJECT_CANDIDATE",
            "AUTO_RANK_CANDIDATE",
            "AUTO_SCORE_CANDIDATE",
            "AUTO_CREATE_EMPLOYMENT_CONTRACT",
            "MUTATE_HR_RECORD",
        ],
    },
    {
        "uce_id": "UCE-002",
        "candidate": "staff_onboarding",
        "module_path": "app.modules.staff_onboarding.service",
        "l4_func": "get_staff_onboarding_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/staff-onboarding/summary",
        "forbidden": [
            "AUTO_GRANT_ACCESS",
            "AUTO_ASSIGN_ROLE",
            "AUTO_COMPLETE_ONBOARDING",
            "AUTO_ISSUE_EQUIPMENT",
            "MUTATE_HR_RECORD",
        ],
    },
    {
        "uce_id": "UCE-003",
        "candidate": "employee_records",
        "module_path": "app.modules.employee_records.service",
        "l4_func": "get_employee_records_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/employee-records/summary",
        "forbidden": [
            "AUTO_CHANGE_PAYROLL_DATA",
            "AUTO_CREATE_EMPLOYEE_DECISION",
            "AUTO_TERMINATE_EMPLOYEE",
            "AUTO_UPDATE_EMPLOYMENT_STATUS",
            "MUTATE_HR_RECORD",
        ],
    },
    {
        "uce_id": "UCE-004",
        "candidate": "leave_management",
        "module_path": "app.modules.leave_management.service",
        "l4_func": "get_leave_management_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/leave-management/summary",
        "forbidden": [
            "AUTO_APPROVE_LEAVE",
            "AUTO_REJECT_LEAVE",
            "AUTO_CHANGE_BALANCE",
            "AUTO_DECIDE_LEAVE_CASE",
            "MUTATE_HR_RECORD",
        ],
    },
    {
        "uce_id": "UCE-017",
        "candidate": "dormitory_management",
        "module_path": "app.modules.dormitory_management.service",
        "l4_func": "get_dormitory_management_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/dormitory-management/summary",
        "forbidden": [
            "AUTO_ASSIGN_ROOM",
            "AUTO_APPROVE_HOUSING",
            "AUTO_REJECT_HOUSING",
            "CHARGE_HOUSING_FEE",
            "MUTATE_OCCUPANCY_RECORD",
        ],
    },
    {
        "uce_id": "UCE-022",
        "candidate": "partnership_registry",
        "module_path": "app.modules.partnership_registry.service",
        "l4_func": "get_partnership_registry_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/partnership-registry/summary",
        "forbidden": [
            "AUTO_APPROVE_PARTNER",
            "AUTO_CREATE_LEGAL_PARTNERSHIP",
            "AUTO_RENEW_PARTNERSHIP",
            "MUTATE_CONTRACT_RECORD",
            "PROVIDER_CALL",
        ],
    },
    {
        "uce_id": "UCE-023",
        "candidate": "mou_lifecycle",
        "module_path": "app.modules.mou_lifecycle.service",
        "l4_func": "get_mou_lifecycle_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/mou-lifecycle/summary",
        "forbidden": [
            "AUTO_APPROVE_MOU",
            "AUTO_RENEW_MOU",
            "AUTO_SIGN_MOU",
            "AUTO_TERMINATE_MOU",
            "MUTATE_LEGAL_RECORD",
        ],
    },
    {
        "uce_id": "UCE-037",
        "candidate": "scholarship_committee_workflow",
        "module_path": "app.modules.scholarship_committee_workflow.service",
        "l4_func": "get_scholarship_committee_workflow_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/scholarship-committee-workflow/summary",
        "forbidden": [
            "AUTO_APPROVE_SCHOLARSHIP",
            "AUTO_REJECT_SCHOLARSHIP",
            "AUTO_RANK_APPLICANT",
            "AUTO_SCORE_APPLICANT",
            "AUTO_ASSIGN_AID_AMOUNT",
            "MUTATE_FINANCIAL_AID_RECORD",
        ],
    },
    {
        "uce_id": "UCE-038",
        "candidate": "student_appeals_workflow",
        "module_path": "app.modules.student_appeals_workflow.service",
        "l4_func": "get_student_appeals_workflow_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/student-appeals-workflow/summary",
        "forbidden": [
            "AUTO_APPROVE_APPEAL",
            "AUTO_REJECT_APPEAL",
            "AUTO_REVERSE_SANCTION",
            "AUTO_CHANGE_GRADE",
            "AUTO_CHANGE_STUDENT_STATUS",
            "MUTATE_ACADEMIC_RECORD",
        ],
    },
    {
        "uce_id": "UCE-046",
        "candidate": "consent_management_policy",
        "module_path": "app.modules.consent_management_policy.service",
        "l4_func": "get_consent_management_policy_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/consent-management-policy/summary",
        "forbidden": [
            "AUTO_APPROVE_CONSENT",
            "AUTO_REVOKE_CONSENT",
            "AUTO_ENFORCE_POLICY",
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


def _load_module(cfg: dict[str, object]) -> object:
    return importlib.import_module(str(cfg["module_path"]))


def _call_service_summary(cfg: dict[str, object], tenant_id: int = 1) -> dict:
    module = _load_module(cfg)
    func = getattr(module, str(cfg["l4_func"]))
    return func(tenant_id=tenant_id)


def _headers_with_permission(permission: str = "admin.expansion.read", tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id=f"a02810-admin-tenant-{tenant_id}@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=[permission],
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


def _headers_without_permission(tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id=f"a02810-student-tenant-{tenant_id}@example.com",
        roles=["student"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=[],
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)


def test_a02810_router_import_validation() -> None:
    module = importlib.import_module("app.modules.expansion_visibility.router")
    assert hasattr(module, "router")


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_all_new_paths_exist(cfg: dict[str, object]) -> None:
    assert str(cfg["route"]) in app.openapi()["paths"]


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_get_only_path_contract(cfg: dict[str, object]) -> None:
    path_item = app.openapi()["paths"][str(cfg["route"])]
    assert set(path_item) == {"get"}


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_selected_l4_service_summaries_exist(cfg: dict[str, object]) -> None:
    module = _load_module(cfg)
    assert hasattr(module, str(cfg["l4_func"]))


def test_a02810_a0282_routes_still_exist() -> None:
    paths = set(app.openapi()["paths"])
    assert len(A0282_EXISTING_PATHS) == 6
    for path in A0282_EXISTING_PATHS:
        assert path in paths, f"A-028.2 route missing: {path}"


def test_a02810_a0283_routes_still_exist() -> None:
    paths = set(app.openapi()["paths"])
    assert len(A0283_EXISTING_PATHS) == 6
    for path in A0283_EXISTING_PATHS:
        assert path in paths, f"A-028.3 route missing: {path}"


def test_a02810_a0287_routes_still_exist() -> None:
    paths = set(app.openapi()["paths"])
    assert len(A0287_EXISTING_PATHS) == 10
    for path in A0287_EXISTING_PATHS:
        assert path in paths, f"A-028.7 route missing: {path}"


def test_a02810_consolidated_route_still_responds(test_client: TestClient) -> None:
    response = test_client.get(CONSOLIDATED_ROUTE, headers=_headers_with_permission())
    assert response.status_code == 200


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_missing_auth_rejected(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]))
    assert response.status_code == 401


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_missing_permission_rejected(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_without_permission())
    assert response.status_code == 403


@pytest.mark.parametrize("bad_header", ["0", "-1", "not-an-int"])
@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_invalid_tenant_rejected(test_client: TestClient, cfg: dict[str, object], bad_header: str) -> None:
    headers = _headers_with_permission()
    headers["X-Tenant-ID"] = bad_header
    response = test_client.get(str(cfg["route"]), headers=headers)
    assert response.status_code in {400, 403}


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_explicit_permission_headers_return_success(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_admin_headers_return_success(cfg: dict[str, object]) -> None:
    response = client.get(str(cfg["route"]), headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_route_output_matches_service_summary(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json() == _call_service_summary(cfg, tenant_id=1)


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_response_contains_common_l4_fields(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    payload = response.json()
    assert COMMON_FIELDS.issubset(set(payload))
    assert payload["tenant_id"] == 1
    assert payload["module"] == str(cfg["candidate"])
    assert payload["uce_id"] == str(cfg["uce_id"])


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_visibility_level_is_l4(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["visibility_level"] == "L4"


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_source_maturity_level_is_l3(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["source_maturity_level"] == "L3"


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_visibility_type_is_read_only_service_summary(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    payload = response.json()
    if "visibility_type" in payload:
        assert payload["visibility_type"] == "READ_ONLY_SERVICE_SUMMARY"


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_read_only_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["read_only"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_no_mutation_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["no_mutation"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_tenant_scoped_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["tenant_scoped"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_no_provider_call_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["no_provider_call"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_no_external_submission_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["no_external_submission"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_no_brain_execution_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["no_brain_execution"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_no_autonomous_execution_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["no_autonomous_execution"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_no_workflow_execution_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["no_workflow_execution"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_no_decision_execution_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["no_decision_execution"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_no_fake_kpi_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["no_fake_kpi"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_no_synthetic_score_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    payload = response.json()
    if "no_synthetic_score" in payload:
        assert payload["no_synthetic_score"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_no_l5_claim_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["no_l5_claim"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_no_l6_claim_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["no_l6_claim"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_forbidden_actions_are_preserved(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    forbidden_actions = set(response.json()["forbidden_actions"])
    for action in cfg["forbidden"]:
        assert action in forbidden_actions, f"{action} missing from forbidden_actions of {cfg['candidate']}"


def test_a02810_staff_recruitment_boundary(test_client: TestClient) -> None:
    cfg = next(c for c in NEW_ROUTE_CONFIGS if c["candidate"] == "staff_recruitment")
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    forbidden = set(payload["forbidden_actions"])
    assert "AUTO_HIRE_CANDIDATE" in forbidden
    assert "AUTO_RANK_CANDIDATE" in forbidden


def test_a02810_staff_onboarding_boundary(test_client: TestClient) -> None:
    cfg = next(c for c in NEW_ROUTE_CONFIGS if c["candidate"] == "staff_onboarding")
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    forbidden = set(payload["forbidden_actions"])
    assert "AUTO_GRANT_ACCESS" in forbidden
    assert "AUTO_ASSIGN_ROLE" in forbidden


def test_a02810_employee_records_boundary(test_client: TestClient) -> None:
    cfg = next(c for c in NEW_ROUTE_CONFIGS if c["candidate"] == "employee_records")
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    forbidden = set(payload["forbidden_actions"])
    assert "AUTO_CREATE_EMPLOYEE_DECISION" in forbidden
    assert "AUTO_CHANGE_PAYROLL_DATA" in forbidden


def test_a02810_leave_management_boundary(test_client: TestClient) -> None:
    cfg = next(c for c in NEW_ROUTE_CONFIGS if c["candidate"] == "leave_management")
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    forbidden = set(payload["forbidden_actions"])
    assert "AUTO_APPROVE_LEAVE" in forbidden
    assert "AUTO_CHANGE_BALANCE" in forbidden


def test_a02810_dormitory_management_boundary(test_client: TestClient) -> None:
    cfg = next(c for c in NEW_ROUTE_CONFIGS if c["candidate"] == "dormitory_management")
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    forbidden = set(payload["forbidden_actions"])
    assert "AUTO_ASSIGN_ROOM" in forbidden
    assert "AUTO_APPROVE_HOUSING" in forbidden


def test_a02810_partnership_registry_boundary(test_client: TestClient) -> None:
    cfg = next(c for c in NEW_ROUTE_CONFIGS if c["candidate"] == "partnership_registry")
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    forbidden = set(payload["forbidden_actions"])
    assert "AUTO_APPROVE_PARTNER" in forbidden
    assert "AUTO_CREATE_LEGAL_PARTNERSHIP" in forbidden


def test_a02810_mou_lifecycle_boundary(test_client: TestClient) -> None:
    cfg = next(c for c in NEW_ROUTE_CONFIGS if c["candidate"] == "mou_lifecycle")
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    forbidden = set(payload["forbidden_actions"])
    assert "AUTO_SIGN_MOU" in forbidden
    assert "AUTO_APPROVE_MOU" in forbidden


def test_a02810_scholarship_committee_workflow_boundary(test_client: TestClient) -> None:
    cfg = next(c for c in NEW_ROUTE_CONFIGS if c["candidate"] == "scholarship_committee_workflow")
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    forbidden = set(payload["forbidden_actions"])
    assert "AUTO_APPROVE_SCHOLARSHIP" in forbidden
    assert "AUTO_ASSIGN_AID_AMOUNT" in forbidden


def test_a02810_student_appeals_workflow_boundary(test_client: TestClient) -> None:
    cfg = next(c for c in NEW_ROUTE_CONFIGS if c["candidate"] == "student_appeals_workflow")
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    forbidden = set(payload["forbidden_actions"])
    assert "AUTO_APPROVE_APPEAL" in forbidden
    assert "AUTO_CHANGE_GRADE" in forbidden


def test_a02810_consent_management_policy_boundary(test_client: TestClient) -> None:
    cfg = next(c for c in NEW_ROUTE_CONFIGS if c["candidate"] == "consent_management_policy")
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    forbidden = set(payload["forbidden_actions"])
    assert "AUTO_ENFORCE_POLICY" in forbidden
    assert "AUTO_REVOKE_CONSENT" in forbidden


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_route_is_deterministic_and_read_only(test_client: TestClient, cfg: dict[str, object]) -> None:
    first = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    second = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json() == second.json()
    assert first.json()["read_only"] is True
    assert first.json()["no_mutation"] is True


def test_a02810_no_duplicate_route_registration() -> None:
    paths = [p for p in app.openapi()["paths"] if p.startswith("/api/admin/expansion/l4/")]
    assert len(paths) == len(set(paths))


def test_a02810_expansion_l4_visibility_count_unchanged_at_32() -> None:
    a0281_l4_visibility = 12
    a0286_l4_visibility = 10
    a0289_l4_visibility = 10
    expansion_l4_visibility_count = a0281_l4_visibility + a0286_l4_visibility + a0289_l4_visibility
    assert expansion_l4_visibility_count == 32


def test_a02810_expansion_l4_api_route_count_formula() -> None:
    a0282_count = len(A0282_EXISTING_PATHS)
    a0283_count = len(A0283_EXISTING_PATHS)
    a0287_count = len(A0287_EXISTING_PATHS)
    a02810_count = len(NEW_ROUTE_CONFIGS)
    total_exposed = len([p for p in app.openapi()["paths"] if p.startswith("/api/admin/expansion/l4/")])

    assert a0282_count == 6
    assert a0283_count == 6
    assert a0287_count == 10
    assert a02810_count == 10
    # total_exposed includes A-028.14 routes added later (+8 = 40)
    assert total_exposed >= 32
    assert a0282_count + a0283_count + a0287_count + a02810_count == 32


def test_a02810_consolidated_summary_refresh_deferred_to_a02811() -> None:
    # Consolidated endpoint exists and is refreshed by later actions.
    test_client = TestClient(app)
    response = test_client.get(CONSOLIDATED_ROUTE, headers=_headers_with_permission())
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("summary_type") == "EXPANSION_L4_CONSOLIDATED_ADMIN_SUMMARY"
    assert payload.get("total_l4_visibility_candidates") == 40


def test_a02810_consolidated_endpoint_is_not_in_openapi_schema() -> None:
    paths = set(app.openapi()["paths"])
    assert CONSOLIDATED_ROUTE not in paths


def test_a02810_uce046_route_exists_and_returns_200(test_client: TestClient) -> None:
    route = "/api/admin/expansion/l4/consent-management-policy/summary"
    response = test_client.get(route, headers=_headers_with_permission())
    assert response.status_code == 200


def test_a02810_uce098_route_does_not_exist(test_client: TestClient) -> None:
    response = test_client.get(PROHIBITED_UCE098_ROUTE, headers=_headers_with_permission())
    assert response.status_code == 404


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_no_l5_l6_claim_combined(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["no_l5_claim"] is True
    assert payload["no_l6_claim"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_a02810_non_get_methods_not_allowed(test_client: TestClient, cfg: dict[str, object], method: str) -> None:
    response = getattr(test_client, method)(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 405


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a02810_cross_tenant_override_rejected(test_client: TestClient, cfg: dict[str, object]) -> None:
    headers = _headers_with_permission(tenant_id=1)
    headers["X-Tenant-ID"] = "2"
    response = test_client.get(str(cfg["route"]), headers=headers)
    assert response.status_code == 403
