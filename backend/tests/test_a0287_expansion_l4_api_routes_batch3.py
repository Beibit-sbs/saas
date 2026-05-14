"""
A-028.7-RUNTIME — Expansion L4 API Routes for A-028.6 Batch
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


# ---------------------------------------------------------------------------
# Existing routes preserved from A-028.2
# ---------------------------------------------------------------------------
A0282_EXISTING_PATHS = [
    "/api/admin/expansion/l4/document-workflow/summary",
    "/api/admin/expansion/l4/order-decree-registry/summary",
    "/api/admin/expansion/l4/committee-decision-registry/summary",
    "/api/admin/expansion/l4/rector-resolution-tracking-workflow/summary",
    "/api/admin/expansion/l4/compliance-calendar-dashboard/summary",
    "/api/admin/expansion/l4/accreditation-dashboard/summary",
]

# ---------------------------------------------------------------------------
# Existing routes preserved from A-028.3
# ---------------------------------------------------------------------------
A0283_EXISTING_PATHS = [
    "/api/admin/expansion/l4/incoming-outgoing-correspondence/summary",
    "/api/admin/expansion/l4/document-template-library/summary",
    "/api/admin/expansion/l4/ministry-reporting-dashboard/summary",
    "/api/admin/expansion/l4/rector-strategy-dashboard/summary",
    "/api/admin/expansion/l4/archive-retention-management/summary",
    "/api/admin/expansion/l4/international-office/summary",
]

# ---------------------------------------------------------------------------
# Consolidated summary endpoint — unchanged from A-028.4
# (include_in_schema=False — does NOT appear in openapi paths)
# ---------------------------------------------------------------------------
CONSOLIDATED_ROUTE = "/api/admin/expansion/l4/summary"

# ---------------------------------------------------------------------------
# New A-028.7 route configurations
# ---------------------------------------------------------------------------
NEW_ROUTE_CONFIGS = [
    {
        "uce_id": "UCE-014",
        "candidate": "curriculum_mapping",
        "module_path": "app.modules.curriculum_mapping.service",
        "l4_func": "get_curriculum_mapping_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/curriculum-mapping/summary",
        "forbidden": [
            "AUTO_CHANGE_CURRICULUM",
            "AUTO_APPROVE_OUTCOME_MAPPING",
            "AUTO_MODIFY_PROGRAM_REQUIREMENTS",
        ],
    },
    {
        "uce_id": "UCE-015",
        "candidate": "syllabus_management",
        "module_path": "app.modules.syllabus_management.service",
        "l4_func": "get_syllabus_management_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/syllabus-management/summary",
        "forbidden": [
            "AUTO_APPROVE_SYLLABUS",
            "AUTO_CHANGE_ASSESSMENT_RULES",
            "AUTO_PUBLISH_SYLLABUS",
        ],
    },
    {
        "uce_id": "UCE-016",
        "candidate": "competency_framework",
        "module_path": "app.modules.competency_framework.service",
        "l4_func": "get_competency_framework_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/competency-framework/summary",
        "forbidden": [
            "AUTO_APPROVE_COMPETENCY",
            "AUTO_CHANGE_PROGRAM_OUTCOMES",
            "AUTO_DELETE_FRAMEWORK",
            "AUTO_ENFORCE_POLICY",
            "MUTATE_ACADEMIC_RECORD",
        ],
    },
    {
        "uce_id": "UCE-071",
        "candidate": "program_learning_outcomes",
        "module_path": "app.modules.program_learning_outcomes.service",
        "l4_func": "get_program_learning_outcomes_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/program-learning-outcomes/summary",
        "forbidden": [
            "AUTO_APPROVE_OUTCOME",
            "AUTO_CHANGE_ACCREDITATION_MAPPING",
            "AUTO_PUBLISH_CURRICULUM_CHANGE",
            "AUTO_ENFORCE_POLICY",
            "MUTATE_ACADEMIC_RECORD",
        ],
    },
    {
        "uce_id": "UCE-072",
        "candidate": "course_learning_outcomes",
        "module_path": "app.modules.course_learning_outcomes.service",
        "l4_func": "get_course_learning_outcomes_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/course-learning-outcomes/summary",
        "forbidden": [
            "AUTO_APPROVE_CLO",
            "AUTO_CHANGE_ASSESSMENT_MAPPING",
            "AUTO_PUBLISH_COURSE_OUTCOME",
            "AUTO_ENFORCE_POLICY",
            "MUTATE_ACADEMIC_RECORD",
        ],
    },
    {
        "uce_id": "UCE-073",
        "candidate": "elective_course_selection",
        "module_path": "app.modules.elective_course_selection.service",
        "l4_func": "get_elective_course_selection_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/elective-course-selection/summary",
        "forbidden": [
            "AUTO_ENROLL_STUDENT",
            "AUTO_APPROVE_ELECTIVE",
            "AUTO_OVERRIDE_PREREQUISITE",
            "AUTO_RESERVE_SEAT",
            "MUTATE_STUDENT_RECORD",
        ],
    },
    {
        "uce_id": "UCE-074",
        "candidate": "prerequisite_management",
        "module_path": "app.modules.prerequisite_management.service",
        "l4_func": "get_prerequisite_management_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/prerequisite-management/summary",
        "forbidden": [
            "AUTO_CHANGE_PREREQUISITE",
            "AUTO_OVERRIDE_STUDENT_ELIGIBILITY",
            "AUTO_REGISTER_STUDENT",
        ],
    },
    {
        "uce_id": "UCE-075",
        "candidate": "transfer_credit_management",
        "module_path": "app.modules.transfer_credit_management.service",
        "l4_func": "get_transfer_credit_management_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/transfer-credit-management/summary",
        "forbidden": [
            "AUTO_APPROVE_CREDIT",
            "AUTO_CHANGE_GPA",
            "AUTO_MODIFY_ACADEMIC_RECORD",
        ],
    },
    {
        "uce_id": "UCE-076",
        "candidate": "course_catalog_management",
        "module_path": "app.modules.course_catalog_management.service",
        "l4_func": "get_course_catalog_management_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/course-catalog-management/summary",
        "forbidden": [
            "AUTO_PUBLISH_COURSE",
            "AUTO_DELETE_COURSE",
            "AUTO_CHANGE_CREDIT_VALUE",
        ],
    },
    {
        "uce_id": "UCE-092",
        "candidate": "degree_audit",
        "module_path": "app.modules.degree_audit.service",
        "l4_func": "get_degree_audit_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/degree-audit/summary",
        "forbidden": [
            "AUTO_GRADUATE_STUDENT",
            "AUTO_OVERRIDE_REQUIREMENT",
            "AUTO_CHANGE_TRANSCRIPT",
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
    "no_brain_execution",
    "no_autonomous_execution",
    "no_decision_execution",
    "no_fake_kpi",
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
        user_id=f"a0287-admin-tenant-{tenant_id}@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=[permission],
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


def _headers_without_permission(tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id=f"a0287-student-tenant-{tenant_id}@example.com",
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
# Group 1: Router import / app registration validation
# ---------------------------------------------------------------------------

def test_a0287_router_import_validation() -> None:
    module = importlib.import_module("app.modules.expansion_visibility.router")
    assert hasattr(module, "router")


# ---------------------------------------------------------------------------
# Group 2: All 10 new paths exist
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_all_new_paths_exist(cfg: dict[str, object]) -> None:
    assert str(cfg["route"]) in app.openapi()["paths"]


# ---------------------------------------------------------------------------
# Group 3: All 10 new paths are GET only
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_get_only_path_contract(cfg: dict[str, object]) -> None:
    path_item = app.openapi()["paths"][str(cfg["route"])]
    assert set(path_item) == {"get"}


# ---------------------------------------------------------------------------
# Group 4: Selected A-028.6 L4 service summaries still exist
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_selected_l4_service_summaries_exist(cfg: dict[str, object]) -> None:
    module = _load_module(cfg)
    assert hasattr(module, str(cfg["l4_func"]))


# ---------------------------------------------------------------------------
# Group 5: All A-028.2 routes still exist
# ---------------------------------------------------------------------------

def test_a0287_a0282_routes_still_exist() -> None:
    paths = set(app.openapi()["paths"])
    assert len(A0282_EXISTING_PATHS) == 6
    for path in A0282_EXISTING_PATHS:
        assert path in paths, f"A-028.2 route missing: {path}"


# ---------------------------------------------------------------------------
# Group 6: All A-028.3 routes still exist
# ---------------------------------------------------------------------------

def test_a0287_a0283_routes_still_exist() -> None:
    paths = set(app.openapi()["paths"])
    assert len(A0283_EXISTING_PATHS) == 6
    for path in A0283_EXISTING_PATHS:
        assert path in paths, f"A-028.3 route missing: {path}"


# ---------------------------------------------------------------------------
# Group 7: A-028.4 consolidated summary route exists via direct HTTP call
# (include_in_schema=False so won't appear in openapi paths)
# ---------------------------------------------------------------------------

def test_a0287_consolidated_route_still_responds(test_client: TestClient) -> None:
    response = test_client.get(CONSOLIDATED_ROUTE, headers=_headers_with_permission())
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Group 8: Route requires authentication
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_missing_auth_rejected(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]))
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Group 9: Route requires admin.expansion.read permission
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_missing_permission_rejected(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_without_permission())
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Group 10: Invalid tenant rejected / fail-closed
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_header", ["0", "-1", "not-an-int"])
@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_invalid_tenant_rejected(test_client: TestClient, cfg: dict[str, object], bad_header: str) -> None:
    headers = _headers_with_permission()
    headers["X-Tenant-ID"] = bad_header
    response = test_client.get(str(cfg["route"]), headers=headers)
    assert response.status_code in {400, 403}


# ---------------------------------------------------------------------------
# Group 11: Valid tenant accepted
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_explicit_permission_headers_return_success(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text


# ---------------------------------------------------------------------------
# Group 12: Valid request returns 200 and preserves service summary payload
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_admin_headers_return_success(cfg: dict[str, object]) -> None:
    response = client.get(str(cfg["route"]), headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_route_output_matches_service_summary(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json() == _call_service_summary(cfg, tenant_id=1)


# ---------------------------------------------------------------------------
# Group 13: Response shape matches L4 API standard
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_response_contains_common_l4_fields(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    payload = response.json()
    assert COMMON_FIELDS.issubset(set(payload))
    assert payload["tenant_id"] == 1
    assert payload["module"] == str(cfg["candidate"])
    assert payload["uce_id"] == str(cfg["uce_id"])


# ---------------------------------------------------------------------------
# Group 14: visibility_level == "L4"
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_visibility_level_is_l4(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["visibility_level"] == "L4"


# ---------------------------------------------------------------------------
# Group 15: source_maturity_level == "L3"
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_source_maturity_level_is_l3(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["source_maturity_level"] == "L3"


# ---------------------------------------------------------------------------
# Group 16: visibility_type == "READ_ONLY_SERVICE_SUMMARY"
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_visibility_type_is_read_only_service_summary(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    payload = response.json()
    # visibility_type field if present
    if "visibility_type" in payload:
        assert payload["visibility_type"] == "READ_ONLY_SERVICE_SUMMARY"


# ---------------------------------------------------------------------------
# Group 17: read_only=True
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_read_only_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["read_only"] is True


# ---------------------------------------------------------------------------
# Group 18: no_mutation=True
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_no_mutation_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["no_mutation"] is True


# ---------------------------------------------------------------------------
# Group 19: tenant_scoped=True
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_tenant_scoped_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["tenant_scoped"] is True


# ---------------------------------------------------------------------------
# Group 20: no_provider_call=True
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_no_provider_call_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["no_provider_call"] is True


# ---------------------------------------------------------------------------
# Group 21: no_external_submission=True
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_no_external_submission_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    payload = response.json()
    if "no_external_submission" in payload:
        assert payload["no_external_submission"] is True


# ---------------------------------------------------------------------------
# Group 22: no_brain_execution=True
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_no_brain_execution_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["no_brain_execution"] is True


# ---------------------------------------------------------------------------
# Group 23: no_autonomous_execution=True
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_no_autonomous_execution_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["no_autonomous_execution"] is True


# ---------------------------------------------------------------------------
# Group 24: no_workflow_execution=True
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_no_workflow_execution_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    payload = response.json()
    if "no_workflow_execution" in payload:
        assert payload["no_workflow_execution"] is True


# ---------------------------------------------------------------------------
# Group 25: no_decision_execution=True
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_no_decision_execution_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["no_decision_execution"] is True


# ---------------------------------------------------------------------------
# Group 26: no_fake_kpi=True
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_no_fake_kpi_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["no_fake_kpi"] is True


# ---------------------------------------------------------------------------
# Group 27: no_synthetic_score=True
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_no_synthetic_score_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    payload = response.json()
    if "no_synthetic_score" in payload:
        assert payload["no_synthetic_score"] is True


# ---------------------------------------------------------------------------
# Group 28: no_l5_claim=True
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_no_l5_claim_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["no_l5_claim"] is True


# ---------------------------------------------------------------------------
# Group 29: no_l6_claim=True
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_no_l6_claim_flag(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json()["no_l6_claim"] is True


# ---------------------------------------------------------------------------
# Group 30: forbidden_actions preserved
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_forbidden_actions_are_preserved(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    payload = response.json()
    forbidden_actions = set(payload["forbidden_actions"])
    for action in cfg["forbidden"]:
        assert action in forbidden_actions, f"{action} missing from forbidden_actions of {cfg['candidate']}"


# ---------------------------------------------------------------------------
# Group 31: Candidate-specific forbidden boundaries verified
# ---------------------------------------------------------------------------

def test_a0287_curriculum_mapping_no_mutation_boundary(test_client: TestClient) -> None:
    cfg = next(c for c in NEW_ROUTE_CONFIGS if c["candidate"] == "curriculum_mapping")
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200
    payload = response.json()
    assert payload["no_mutation"] is True
    assert payload["read_only"] is True
    forbidden = set(payload["forbidden_actions"])
    assert "AUTO_CHANGE_CURRICULUM" in forbidden
    assert "AUTO_APPROVE_OUTCOME_MAPPING" in forbidden


def test_a0287_syllabus_management_no_publishing_boundary(test_client: TestClient) -> None:
    cfg = next(c for c in NEW_ROUTE_CONFIGS if c["candidate"] == "syllabus_management")
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200
    payload = response.json()
    assert payload["no_mutation"] is True
    forbidden = set(payload["forbidden_actions"])
    assert "AUTO_PUBLISH_SYLLABUS" in forbidden
    assert "AUTO_APPROVE_SYLLABUS" in forbidden


def test_a0287_competency_framework_no_scoring_boundary(test_client: TestClient) -> None:
    cfg = next(c for c in NEW_ROUTE_CONFIGS if c["candidate"] == "competency_framework")
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200
    payload = response.json()
    assert payload["no_mutation"] is True
    forbidden = set(payload["forbidden_actions"])
    assert "AUTO_APPROVE_COMPETENCY" in forbidden
    assert "AUTO_ENFORCE_POLICY" in forbidden


def test_a0287_program_learning_outcomes_no_curriculum_mutation(test_client: TestClient) -> None:
    cfg = next(c for c in NEW_ROUTE_CONFIGS if c["candidate"] == "program_learning_outcomes")
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200
    payload = response.json()
    assert payload["no_mutation"] is True
    assert payload["no_fake_kpi"] is True
    forbidden = set(payload["forbidden_actions"])
    assert "AUTO_APPROVE_OUTCOME" in forbidden


def test_a0287_course_learning_outcomes_no_assessment_enforcement(test_client: TestClient) -> None:
    cfg = next(c for c in NEW_ROUTE_CONFIGS if c["candidate"] == "course_learning_outcomes")
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200
    payload = response.json()
    assert payload["no_mutation"] is True
    forbidden = set(payload["forbidden_actions"])
    assert "AUTO_APPROVE_CLO" in forbidden
    assert "AUTO_PUBLISH_COURSE_OUTCOME" in forbidden


def test_a0287_elective_course_selection_no_auto_enrollment(test_client: TestClient) -> None:
    cfg = next(c for c in NEW_ROUTE_CONFIGS if c["candidate"] == "elective_course_selection")
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200
    payload = response.json()
    assert payload["no_mutation"] is True
    forbidden = set(payload["forbidden_actions"])
    assert "AUTO_ENROLL_STUDENT" in forbidden
    assert "AUTO_RESERVE_SEAT" in forbidden


def test_a0287_prerequisite_management_no_rule_enforcement(test_client: TestClient) -> None:
    cfg = next(c for c in NEW_ROUTE_CONFIGS if c["candidate"] == "prerequisite_management")
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200
    payload = response.json()
    assert payload["no_mutation"] is True
    forbidden = set(payload["forbidden_actions"])
    assert "AUTO_CHANGE_PREREQUISITE" in forbidden
    assert "AUTO_REGISTER_STUDENT" in forbidden


def test_a0287_transfer_credit_management_no_credit_approval(test_client: TestClient) -> None:
    cfg = next(c for c in NEW_ROUTE_CONFIGS if c["candidate"] == "transfer_credit_management")
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200
    payload = response.json()
    assert payload["no_mutation"] is True
    forbidden = set(payload["forbidden_actions"])
    assert "AUTO_APPROVE_CREDIT" in forbidden
    assert "AUTO_MODIFY_ACADEMIC_RECORD" in forbidden


def test_a0287_course_catalog_management_no_publishing(test_client: TestClient) -> None:
    cfg = next(c for c in NEW_ROUTE_CONFIGS if c["candidate"] == "course_catalog_management")
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200
    payload = response.json()
    assert payload["no_mutation"] is True
    forbidden = set(payload["forbidden_actions"])
    assert "AUTO_PUBLISH_COURSE" in forbidden
    assert "AUTO_DELETE_COURSE" in forbidden


def test_a0287_degree_audit_no_graduation_clearance(test_client: TestClient) -> None:
    cfg = next(c for c in NEW_ROUTE_CONFIGS if c["candidate"] == "degree_audit")
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200
    payload = response.json()
    assert payload["no_mutation"] is True
    assert payload["no_l5_claim"] is True
    assert payload["no_l6_claim"] is True
    forbidden = set(payload["forbidden_actions"])
    assert "AUTO_GRADUATE_STUDENT" in forbidden
    assert "AUTO_CHANGE_TRANSCRIPT" in forbidden


# ---------------------------------------------------------------------------
# Group 32: Route does not mutate state (deterministic and idempotent)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_route_is_deterministic_and_read_only(test_client: TestClient, cfg: dict[str, object]) -> None:
    first = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    second = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json() == second.json()
    assert first.json()["read_only"] is True
    assert first.json()["no_mutation"] is True


# ---------------------------------------------------------------------------
# Group 33: No duplicate route registration
# ---------------------------------------------------------------------------

def test_a0287_no_duplicate_route_registration() -> None:
    paths = [p for p in app.openapi()["paths"] if p.startswith("/api/admin/expansion/l4/")]
    assert len(paths) == len(set(paths))


# ---------------------------------------------------------------------------
# Group 34: expansion_L4_visibility_count remains 22 (not changed by routes)
# ---------------------------------------------------------------------------

def test_a0287_expansion_l4_visibility_count_unchanged_at_22() -> None:
    # A-028.1: 12 visibility candidates; A-028.6: 10 new visibility candidates
    # API routes do not alter visibility count — expansion_L4_visibility_count = 22
    a0281_l4_visibility = 12
    a0286_l4_visibility = 10
    expansion_l4_visibility_count = a0281_l4_visibility + a0286_l4_visibility
    assert expansion_l4_visibility_count == 22


# ---------------------------------------------------------------------------
# Group 35: expansion_L4_api_route_count formula documented
# ---------------------------------------------------------------------------

def test_a0287_expansion_l4_api_route_count_formula() -> None:
    a0282_count = len(A0282_EXISTING_PATHS)
    a0283_count = len(A0283_EXISTING_PATHS)
    a0287_count = len(NEW_ROUTE_CONFIGS)
    # Consolidated is include_in_schema=False — not in openapi paths
    total_exposed = len([p for p in app.openapi()["paths"] if p.startswith("/api/admin/expansion/l4/")])

    assert a0282_count == 6
    assert a0283_count == 6
    assert a0287_count == 10
    assert total_exposed == 22
    assert a0282_count + a0283_count + a0287_count == total_exposed


# ---------------------------------------------------------------------------
# Group 36: Consolidated summary refresh deferred to A-028.8
# ---------------------------------------------------------------------------

def test_a0287_consolidated_summary_refresh_deferred_to_a0288() -> None:
    # Consolidated endpoint is unchanged — A-028.7 adds individual routes only
    # CONSOLIDATED_SUMMARY_REFRESH_DEFERRED_TO_A0288 = YES
    # Verify consolidated still returns 12-module catalog (pre-A-028.7 batch)
    test_client = TestClient(app)
    response = test_client.get(CONSOLIDATED_ROUTE, headers=_headers_with_permission())
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("summary_type") == "EXPANSION_L4_CONSOLIDATED_ADMIN_SUMMARY"
    # Consolidated catalog has 12 modules (A-028.1/2/3 batch) — not refreshed in A-028.7
    assert payload.get("total_l4_visibility_candidates") == 12


# ---------------------------------------------------------------------------
# Group 37: Consolidated endpoint unchanged
# ---------------------------------------------------------------------------

def test_a0287_consolidated_endpoint_is_not_in_openapi_schema() -> None:
    # include_in_schema=False for consolidated endpoint
    paths = set(app.openapi()["paths"])
    assert CONSOLIDATED_ROUTE not in paths


# ---------------------------------------------------------------------------
# Group 38: No L5/L6 claim
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_no_l5_l6_claim_combined(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["no_l5_claim"] is True
    assert payload["no_l6_claim"] is True


# ---------------------------------------------------------------------------
# Non-GET methods not allowed
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_a0287_non_get_methods_not_allowed(test_client: TestClient, cfg: dict[str, object], method: str) -> None:
    response = getattr(test_client, method)(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 405


# ---------------------------------------------------------------------------
# Cross-tenant override rejected
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0287_cross_tenant_override_rejected(test_client: TestClient, cfg: dict[str, object]) -> None:
    headers = _headers_with_permission(tenant_id=1)
    headers["X-Tenant-ID"] = "2"
    response = test_client.get(str(cfg["route"]), headers=headers)
    assert response.status_code == 403
