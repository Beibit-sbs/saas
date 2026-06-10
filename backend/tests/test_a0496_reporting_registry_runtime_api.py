from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.reporting_runtime.runtime_registry_service import ReportingRegistryRuntimeService


client = TestClient(app)
BASE = "/api/admin/reporting-brain/runtime"


def _headers(
    *,
    tenant_id: int = 1,
    permissions: list[str] | None = None,
    roles: list[str] | None = None,
) -> dict[str, str]:
    token = create_access_token(
        user_id="706",
        roles=roles or ["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=permissions if permissions is not None else ["admin.reporting_runtime.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_reporting_registry_requires_auth() -> None:
    assert client.get(f"{BASE}/registry").status_code in (401, 403)


def test_reporting_registry_requires_summary_read_permission() -> None:
    response = client.get(f"{BASE}/registry", headers=_headers(permissions=[], roles=["student"]))
    assert response.status_code == 403


def test_reporting_registry_visibility_and_report_type_coverage() -> None:
    response = client.get(f"{BASE}/registry", headers=_headers())
    assert response.status_code == 200
    body = response.json()

    report_types = {entry["report_type"] for entry in body["entries"]}
    assert report_types == {
        "MINISTRY",
        "ACCREDITATION",
        "REGULATORY",
        "QS",
        "THE",
        "NOBD",
        "RECTOR",
        "STATISTICAL",
    }
    assert body["read_only"] is True


def test_reporting_registry_tenant_isolation_service_level() -> None:
    service = ReportingRegistryRuntimeService()
    tenant2 = service.get_registry(2).model_dump(mode="json")
    tenant9 = service.get_registry(9).model_dump(mode="json")

    assert tenant2["tenant_id"] == 2
    assert tenant9["tenant_id"] == 9
    assert tenant2["entries"][0]["id"] != tenant9["entries"][0]["id"]


def test_reporting_registry_provider_boundaries_are_non_live() -> None:
    response = client.get(f"{BASE}/providers", headers=_headers())
    assert response.status_code == 200
    providers = response.json()["providers"]

    assert providers
    assert all(item["live_integrations_enabled"] is False for item in providers)
    assert all(item["submission_execution_enabled"] is False for item in providers)


def test_reporting_registry_related_endpoints_are_read_only() -> None:
    headers = _headers()
    for endpoint in [
        "registry",
        "templates",
        "cycles",
        "submissions",
        "evidence",
        "providers",
    ]:
        response = client.get(f"{BASE}/{endpoint}", headers=headers)
        assert response.status_code == 200
        assert response.json()["read_only"] is True
