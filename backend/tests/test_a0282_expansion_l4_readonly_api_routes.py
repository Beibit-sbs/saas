from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.token_service import create_access_token
from tests.conftest import ADMIN_HEADERS, client


ROUTE_CONFIGS = [
    {
        "uce_id": "UCE-009",
        "candidate": "document_workflow",
        "module_path": "app.modules.document_workflow.service",
        "l4_func": "get_document_workflow_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/document-workflow/summary",
        "forbidden": ["AUTO_ROUTE_DOCUMENT", "AUTO_APPROVE_DOCUMENT", "AUTO_SIGN_DOCUMENT", "AUTO_DELETE_DOCUMENT"],
    },
    {
        "uce_id": "UCE-011",
        "candidate": "order_decree_registry",
        "module_path": "app.modules.order_decree_registry.service",
        "l4_func": "get_order_decree_registry_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/order-decree-registry/summary",
        "forbidden": ["AUTO_ISSUE_DECREE", "AUTO_REGISTER_ORDER", "AUTO_SIGN_ORDER", "AUTO_ARCHIVE_WITHOUT_REVIEW"],
    },
    {
        "uce_id": "UCE-090",
        "candidate": "committee_decision_registry",
        "module_path": "app.modules.committee_decision_registry.service",
        "l4_func": "get_committee_decision_registry_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/committee-decision-registry/summary",
        "forbidden": ["AUTO_RECORD_DECISION", "AUTO_APPROVE_MINUTES", "AUTO_SIGN_PROTOCOL", "AUTO_PUBLISH_DECISION"],
    },
    {
        "uce_id": "UCE-099",
        "candidate": "rector_resolution_tracking_workflow",
        "module_path": "app.modules.rector_resolution_tracking_workflow.service",
        "l4_func": "get_rector_resolution_tracking_workflow_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/rector-resolution-tracking-workflow/summary",
        "forbidden": ["AUTO_EXECUTE_WORKFLOW", "AUTO_ROUTE_RESOLUTION", "AUTO_APPROVE_RESOLUTION"],
    },
    {
        "uce_id": "UCE-122",
        "candidate": "compliance_calendar_dashboard",
        "module_path": "app.modules.compliance_calendar_dashboard.service",
        "l4_func": "get_compliance_calendar_dashboard_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/compliance-calendar-dashboard/summary",
        "forbidden": ["AUTO_RENDER_DASHBOARD", "AUTO_COMPUTE_KPI", "AUTO_PUBLISH_METRIC"],
    },
    {
        "uce_id": "UCE-114",
        "candidate": "accreditation_dashboard",
        "module_path": "app.modules.accreditation_dashboard.service",
        "l4_func": "get_accreditation_dashboard_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/accreditation-dashboard/summary",
        "forbidden": ["AUTO_RENDER_DASHBOARD", "AUTO_COMPUTE_KPI", "AUTO_CERTIFY_ACCREDITATION"],
    },
]

NON_SELECTED_PATHS = [
    "/api/admin/expansion/l4/incoming-outgoing-correspondence/summary",
    "/api/admin/expansion/l4/document-template-library/summary",
    "/api/admin/expansion/l4/ministry-reporting-dashboard/summary",
    "/api/admin/expansion/l4/rector-strategy-dashboard/summary",
    "/api/admin/expansion/l4/archive-retention-management/summary",
    "/api/admin/expansion/l4/international-office/summary",
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
    "no_synthetic_dashboard",
    "forbidden_actions",
    "safety_flags",
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
        user_id=f"a0282-admin-tenant-{tenant_id}@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=[permission],
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


def _headers_without_permission(tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id=f"a0282-student-tenant-{tenant_id}@example.com",
        roles=["student"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=[],
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)


def test_a0282_router_import_validation() -> None:
    module = importlib.import_module("app.modules.expansion_visibility.router")
    assert hasattr(module, "router")


def test_a0282_route_count_equals_selected_batch() -> None:
    paths = [path for path in app.openapi()["paths"] if path.startswith("/api/admin/expansion/l4/")]
    assert len(paths) == 6


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0282_all_expected_paths_exist(cfg: dict[str, object]) -> None:
    assert str(cfg["route"]) in app.openapi()["paths"]


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0282_get_only_path_contract(cfg: dict[str, object]) -> None:
    path_item = app.openapi()["paths"][str(cfg["route"])]
    assert set(path_item) == {"get"}


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0282_selected_l4_service_summaries_still_exist(cfg: dict[str, object]) -> None:
    module = _load_module(cfg)
    assert hasattr(module, str(cfg["l4_func"]))


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0282_admin_headers_return_success(cfg: dict[str, object]) -> None:
    response = client.get(str(cfg["route"]), headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0282_explicit_permission_headers_return_success(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0282_missing_auth_rejected(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]))
    assert response.status_code == 401


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0282_missing_permission_rejected(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_without_permission())
    assert response.status_code == 403


@pytest.mark.parametrize("bad_header", ["0", "-1", "not-an-int"])
@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0282_invalid_tenant_rejected(test_client: TestClient, cfg: dict[str, object], bad_header: str) -> None:
    headers = _headers_with_permission()
    headers["X-Tenant-ID"] = bad_header
    response = test_client.get(str(cfg["route"]), headers=headers)
    assert response.status_code in {400, 403}


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0282_cross_tenant_override_rejected(test_client: TestClient, cfg: dict[str, object]) -> None:
    headers = _headers_with_permission(tenant_id=1)
    headers["X-Tenant-ID"] = "2"
    response = test_client.get(str(cfg["route"]), headers=headers)
    assert response.status_code == 403


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0282_response_contains_common_l4_fields(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    payload = response.json()

    assert COMMON_FIELDS.issubset(set(payload))
    assert payload["tenant_id"] == 1
    assert payload["module"] == str(cfg["candidate"])
    assert payload["uce_id"] == str(cfg["uce_id"])
    assert payload["visibility_level"] == "L4"
    assert payload["source_maturity_level"] == "L3"
    assert payload["read_only"] is True
    assert payload["no_mutation"] is True
    assert payload["tenant_scoped"] is True
    assert payload["no_provider_call"] is True
    assert payload["no_brain_execution"] is True
    assert payload["no_autonomous_execution"] is True
    assert payload["no_decision_execution"] is True
    assert payload["no_fake_kpi"] is True
    assert payload["no_synthetic_dashboard"] is True
    assert payload["no_l5_claim"] is True
    assert payload["no_l6_claim"] is True


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0282_forbidden_actions_are_preserved(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    payload = response.json()
    forbidden_actions = set(payload["forbidden_actions"])

    for action in cfg["forbidden"]:
        assert action in forbidden_actions


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0282_route_output_matches_service_summary(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json() == _call_service_summary(cfg, tenant_id=1)


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0282_route_is_deterministic_and_read_only(test_client: TestClient, cfg: dict[str, object]) -> None:
    first = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    second = test_client.get(str(cfg["route"]), headers=_headers_with_permission())

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json() == second.json()
    assert first.json()["read_only"] is True
    assert first.json()["no_mutation"] is True


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_a0282_non_get_methods_not_allowed(test_client: TestClient, cfg: dict[str, object], method: str) -> None:
    response = getattr(test_client, method)(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 405


@pytest.mark.parametrize("path", NON_SELECTED_PATHS)
def test_a0282_non_selected_candidates_not_exposed(test_client: TestClient, path: str) -> None:
    assert path not in app.openapi()["paths"]
    response = test_client.get(path, headers=_headers_with_permission())
    assert response.status_code == 404