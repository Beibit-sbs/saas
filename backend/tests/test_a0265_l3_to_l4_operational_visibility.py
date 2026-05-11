from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.modules.auth.token_service import create_access_token

ROUTES: list[tuple[str, str, str]] = [
    (
        "human_approved_timetable_workflow",
        "/api/admin/human-approved-timetable-workflow/summary",
        "timetable.workflow.read",
    ),
    (
        "timetable_change_proposal",
        "/api/admin/timetable-change-proposal/summary",
        "timetable.change_proposal.read",
    ),
    (
        "timetable_approval_queue",
        "/api/admin/timetable-approval-queue/summary",
        "timetable.approval_queue.read",
    ),
    (
        "timetable_change_kpi_dashboard",
        "/api/admin/timetable-change-kpi-dashboard/summary",
        "timetable.change_kpi.read",
    ),
    (
        "workload_management",
        "/api/admin/workload-management/summary",
        "workload.read",
    ),
    (
        "notification_center",
        "/api/admin/notification-center/summary",
        "notifications.read",
    ),
]


def _headers_for_permission(permission: str, tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id=f"a0265-admin-tenant-{tenant_id}@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=[permission],
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id),
    }


def _headers_without_permission(tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id=f"a0265-user-tenant-{tenant_id}@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=[],
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id),
    }


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.mark.parametrize("module_name,path,permission", ROUTES)
def test_route_registration_and_success(client: TestClient, module_name: str, path: str, permission: str) -> None:
    response = client.get(path, headers=_headers_for_permission(permission, tenant_id=1))
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["module"] == module_name


@pytest.mark.parametrize("_module_name,path,permission", ROUTES)
def test_response_schema_common_fields(client: TestClient, _module_name: str, path: str, permission: str) -> None:
    response = client.get(path, headers=_headers_for_permission(permission, tenant_id=1))
    assert response.status_code == 200, response.text
    payload = response.json()

    required = {
        "tenant_id",
        "module",
        "visibility_level",
        "operational_status",
        "classification",
        "allowed_actions",
        "forbidden_actions",
        "safety_flags",
        "evidence_notes",
        "no_autonomous_execution",
        "readonly",
        "tenant_scoped",
    }
    assert required.issubset(payload.keys())
    assert payload["visibility_level"] == "L4"
    assert payload["readonly"] is True
    assert payload["tenant_scoped"] is True
    assert payload["no_autonomous_execution"] is True


@pytest.mark.parametrize("_module_name,path,_permission", ROUTES)
def test_permission_denied_without_scope(client: TestClient, _module_name: str, path: str, _permission: str) -> None:
    response = client.get(path, headers=_headers_without_permission(tenant_id=1))
    assert response.status_code == 403


@pytest.mark.parametrize("_module_name,path,permission", ROUTES)
def test_missing_auth_fails_closed(client: TestClient, _module_name: str, path: str, permission: str) -> None:
    response = client.get(path)
    assert response.status_code == 401


@pytest.mark.parametrize("_module_name,path,permission", ROUTES)
def test_invalid_tenant_header_fails_closed(client: TestClient, _module_name: str, path: str, permission: str) -> None:
    headers = _headers_for_permission(permission, tenant_id=1)
    headers["X-Tenant-ID"] = "0"
    response = client.get(path, headers=headers)
    assert response.status_code in {400, 403}


@pytest.mark.parametrize("_module_name,path,permission", ROUTES)
def test_cross_tenant_override_denied(client: TestClient, _module_name: str, path: str, permission: str) -> None:
    headers = _headers_for_permission(permission, tenant_id=1)
    headers["X-Tenant-ID"] = "2"
    response = client.get(path, headers=headers)
    assert response.status_code == 403


@pytest.mark.parametrize("_module_name,path,permission", ROUTES)
def test_tenant_isolation_and_scope(client: TestClient, _module_name: str, path: str, permission: str) -> None:
    tenant_a = client.get(path, headers=_headers_for_permission(permission, tenant_id=1))
    assert tenant_a.status_code == 200, tenant_a.text
    payload_a = tenant_a.json()
    assert payload_a["tenant_id"] == 1

    # Cross-tenant access must fail closed; no fallback to default tenant is allowed.
    cross_tenant_headers = _headers_for_permission(permission, tenant_id=1)
    cross_tenant_headers["X-Tenant-ID"] = "2"
    denied = client.get(path, headers=cross_tenant_headers)
    assert denied.status_code == 403
    denied_payload = denied.json()
    assert "tenant_id" not in denied_payload


@pytest.mark.parametrize("_module_name,path,permission", ROUTES)
def test_operational_visibility_output_is_deterministic(
    client: TestClient,
    _module_name: str,
    path: str,
    permission: str,
) -> None:
    headers = _headers_for_permission(permission, tenant_id=1)
    first = client.get(path, headers=headers)
    second = client.get(path, headers=headers)

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json() == second.json()


@pytest.mark.parametrize("_module_name,path,permission", ROUTES)
def test_anti_inflation_flags_present(client: TestClient, _module_name: str, path: str, permission: str) -> None:
    response = client.get(path, headers=_headers_for_permission(permission, tenant_id=1))
    assert response.status_code == 200, response.text
    payload = response.json()
    flags = payload["safety_flags"]

    assert payload["visibility_level"] == "L4"
    assert flags.get("no_brain_claim") is True
    assert flags.get("no_kpi_lineage_claim") is True
    assert payload["readonly"] is True
    assert payload["no_autonomous_execution"] is True
    assert payload["visibility_level"] not in {"L5", "L6"}


@pytest.mark.parametrize("_module_name,path,_permission", ROUTES)
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_read_only_methods_only(client: TestClient, _module_name: str, path: str, _permission: str, method: str) -> None:
    response = getattr(client, method)(path)
    assert response.status_code == 405
