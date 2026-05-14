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

NEW_ROUTE_CONFIGS = [
    {
        "uce_id": "UCE-013",
        "candidate": "incoming_outgoing_correspondence",
        "module_path": "app.modules.incoming_outgoing_correspondence.service",
        "l4_func": "get_incoming_outgoing_correspondence_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/incoming-outgoing-correspondence/summary",
        "forbidden": ["AUTO_SEND_OFFICIAL_RESPONSE", "AUTO_CLOSE_WITHOUT_REVIEW", "AUTO_DELETE_CORRESPONDENCE"],
    },
    {
        "uce_id": "UCE-089",
        "candidate": "document_template_library",
        "module_path": "app.modules.document_template_library.service",
        "l4_func": "get_document_template_library_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/document-template-library/summary",
        "forbidden": ["AUTO_PUBLISH_TEMPLATE", "AUTO_DELETE_TEMPLATE", "AUTO_APPROVE_TEMPLATE"],
    },
    {
        "uce_id": "UCE-032",
        "candidate": "ministry_reporting_dashboard",
        "module_path": "app.modules.ministry_reporting_dashboard.service",
        "l4_func": "get_ministry_reporting_dashboard_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/ministry-reporting-dashboard/summary",
        "forbidden": [
            "AUTO_SUBMIT_REPORT",
            "AUTO_RENDER_DASHBOARD",
            "AUTO_COMPUTE_KPI",
        ],
    },
    {
        "uce_id": "UCE-031",
        "candidate": "rector_strategy_dashboard",
        "module_path": "app.modules.rector_strategy_dashboard.service",
        "l4_func": "get_rector_strategy_dashboard_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/rector-strategy-dashboard/summary",
        "forbidden": [
            "AUTO_COMPUTE_KPI",
            "AUTO_RENDER_DASHBOARD",
            "AUTO_PUBLISH_EXECUTIVE_VIEW",
        ],
    },
    {
        "uce_id": "UCE-012",
        "candidate": "archive_retention_management",
        "module_path": "app.modules.archive_retention_management.service",
        "l4_func": "get_archive_retention_management_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/archive-retention-management/summary",
        "forbidden": ["AUTO_DELETE_ARCHIVE", "AUTO_EXECUTE_DISPOSAL", "AUTO_PURGE_RECORDS"],
    },
    {
        "uce_id": "UCE-019",
        "candidate": "international_office",
        "module_path": "app.modules.international_office.service",
        "l4_func": "get_international_office_l4_visibility_summary",
        "route": "/api/admin/expansion/l4/international-office/summary",
        "forbidden": [
            "AUTO_ISSUE_VISA_DECISION",
            "AUTO_APPROVE_MOBILITY",
            "AUTO_CONFIRM_PARTNERSHIP",
            "AUTO_GRANT_VISA",
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
        user_id=f"a0283-admin-tenant-{tenant_id}@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=[permission],
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


def _headers_without_permission(tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id=f"a0283-student-tenant-{tenant_id}@example.com",
        roles=["student"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=[],
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)


def test_a0283_router_import_validation() -> None:
    module = importlib.import_module("app.modules.expansion_visibility.router")
    assert hasattr(module, "router")


def test_a0283_route_exposure_and_no_duplicate_registration() -> None:
    paths = [path for path in app.openapi()["paths"] if path.startswith("/api/admin/expansion/l4/")]
    assert len(paths) == 12
    assert len(paths) == len(set(paths))


def test_a0283_a0282_route_count_preserved_at_6() -> None:
    paths = set(app.openapi()["paths"])
    assert len(A0282_EXISTING_PATHS) == 6
    for path in A0282_EXISTING_PATHS:
        assert path in paths


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0283_all_new_paths_exist(cfg: dict[str, object]) -> None:
    assert str(cfg["route"]) in app.openapi()["paths"]


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0283_get_only_path_contract(cfg: dict[str, object]) -> None:
    path_item = app.openapi()["paths"][str(cfg["route"])]
    assert set(path_item) == {"get"}


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0283_selected_l4_service_summaries_still_exist(cfg: dict[str, object]) -> None:
    module = _load_module(cfg)
    assert hasattr(module, str(cfg["l4_func"]))


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0283_admin_headers_return_success(cfg: dict[str, object]) -> None:
    response = client.get(str(cfg["route"]), headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0283_explicit_permission_headers_return_success(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0283_missing_auth_rejected(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]))
    assert response.status_code == 401


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0283_missing_permission_rejected(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_without_permission())
    assert response.status_code == 403


@pytest.mark.parametrize("bad_header", ["0", "-1", "not-an-int"])
@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0283_invalid_tenant_rejected(test_client: TestClient, cfg: dict[str, object], bad_header: str) -> None:
    headers = _headers_with_permission()
    headers["X-Tenant-ID"] = bad_header
    response = test_client.get(str(cfg["route"]), headers=headers)
    assert response.status_code in {400, 403}


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0283_cross_tenant_override_rejected(test_client: TestClient, cfg: dict[str, object]) -> None:
    headers = _headers_with_permission(tenant_id=1)
    headers["X-Tenant-ID"] = "2"
    response = test_client.get(str(cfg["route"]), headers=headers)
    assert response.status_code == 403


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0283_response_contains_common_l4_fields(test_client: TestClient, cfg: dict[str, object]) -> None:
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


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0283_forbidden_actions_are_preserved(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    payload = response.json()
    forbidden_actions = set(payload["forbidden_actions"])

    for action in cfg["forbidden"]:
        assert action in forbidden_actions


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0283_route_output_matches_service_summary(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json() == _call_service_summary(cfg, tenant_id=1)


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
def test_a0283_route_is_deterministic_and_read_only(test_client: TestClient, cfg: dict[str, object]) -> None:
    first = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    second = test_client.get(str(cfg["route"]), headers=_headers_with_permission())

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json() == second.json()
    assert first.json()["read_only"] is True
    assert first.json()["no_mutation"] is True


@pytest.mark.parametrize("cfg", NEW_ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in NEW_ROUTE_CONFIGS])
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_a0283_non_get_methods_not_allowed(test_client: TestClient, cfg: dict[str, object], method: str) -> None:
    response = getattr(test_client, method)(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 405


def test_a0283_metric_formula_contract_for_batch2() -> None:
    a0282_count = len(A0282_EXISTING_PATHS)
    a0283_count = len(NEW_ROUTE_CONFIGS)
    total_exposed = len([path for path in app.openapi()["paths"] if path.startswith("/api/admin/expansion/l4/")])

    assert a0282_count == 6
    assert a0283_count == 6
    assert total_exposed == 12
    assert a0282_count + a0283_count == total_exposed
