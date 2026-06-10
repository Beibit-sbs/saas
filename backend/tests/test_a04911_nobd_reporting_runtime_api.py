from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.reporting_runtime.runtime_nobd_service import NobdReportingRuntimeService


client = TestClient(app)
BASE = "/api/admin/reporting-brain/runtime/nobd"


def _headers(
    *,
    tenant_id: int = 1,
    permissions: list[str] | None = None,
    roles: list[str] | None = None,
) -> dict[str, str]:
    token = create_access_token(
        user_id="711",
        roles=roles or ["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=permissions if permissions is not None else ["admin.reporting_runtime.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_nobd_reporting_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


def test_nobd_reporting_requires_summary_read_permission() -> None:
    response = client.get(BASE, headers=_headers(permissions=[], roles=["student"]))
    assert response.status_code == 403


def test_nobd_reporting_rbac_roles_have_access() -> None:
    for role in ["reporting_admin", "vice_rector", "registrar", "analyst", "auditor", "data_manager"]:
        response = client.get(BASE, headers=_headers(roles=[role]))
        assert response.status_code == 200


def test_nobd_reporting_dataset_coverage_and_signal_inventory() -> None:
    response = client.get(BASE, headers=_headers())
    assert response.status_code == 200
    body = response.json()

    dataset_names = {item["dataset_name"] for item in body["reports"]}
    assert dataset_names == {
        "Student Data",
        "Staff Data",
        "Academic Data",
        "Educational Programs",
        "Research Data",
        "Graduate Data",
        "Infrastructure Data",
    }
    assert set(body["signal_inventory"]) == {
        "nobd_completeness_low",
        "nobd_quality_risk",
        "nobd_sync_delay",
        "missing_required_dataset",
        "nobd_readiness_low",
    }
    assert body["read_only"] is True


def test_nobd_reporting_tenant_isolation_service_level() -> None:
    service = NobdReportingRuntimeService()
    tenant2 = service.get_nobd(2).model_dump(mode="json")
    tenant9 = service.get_nobd(9).model_dump(mode="json")

    assert tenant2["tenant_id"] == 2
    assert tenant9["tenant_id"] == 9
    assert tenant2["reports"][0]["id"] != tenant9["reports"][0]["id"]


def test_nobd_reporting_visibility_surfaces() -> None:
    datasets = client.get(f"{BASE}/datasets", headers=_headers())
    completeness = client.get(f"{BASE}/completeness", headers=_headers())
    quality = client.get(f"{BASE}/quality", headers=_headers())
    sync_status = client.get(f"{BASE}/sync-status", headers=_headers())
    risks = client.get(f"{BASE}/risks", headers=_headers())

    assert datasets.status_code == 200
    assert completeness.status_code == 200
    assert quality.status_code == 200
    assert sync_status.status_code == 200
    assert risks.status_code == 200

    dataset_items = datasets.json()["datasets"]
    completeness_items = completeness.json()["completeness"]
    quality_items = quality.json()["quality"]
    sync_items = sync_status.json()["sync_status"]
    risk_items = risks.json()["risks"]

    assert dataset_items and completeness_items and quality_items and sync_items and risk_items
    assert all("dataset_priority" in item for item in dataset_items)
    assert all("completeness_gap" in item for item in completeness_items)
    assert all("quality_band" in item for item in quality_items)
    assert all("sync_lag_hours" in item for item in sync_items)
    assert all(item["signal_owner_module"] == "brain_core" for item in risk_items)


def test_nobd_reporting_related_endpoints_are_read_only() -> None:
    headers = _headers()
    for endpoint in ["", "/datasets", "/completeness", "/quality", "/sync-status", "/risks"]:
        response = client.get(f"{BASE}{endpoint}", headers=headers)
        assert response.status_code == 200
        assert response.json()["read_only"] is True