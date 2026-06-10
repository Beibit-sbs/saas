from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.reporting_runtime.runtime_dashboard_service import ReportingDashboardRuntimeService


client = TestClient(app)
BASE = "/api/admin/reporting-brain/runtime/reporting-dashboard"


def _headers(
    *,
    tenant_id: int = 1,
    permissions: list[str] | None = None,
    roles: list[str] | None = None,
) -> dict[str, str]:
    token = create_access_token(
        user_id="713",
        roles=roles or ["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=permissions if permissions is not None else ["admin.reporting_runtime.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_reporting_dashboard_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


def test_reporting_dashboard_runtime_requires_summary_read_permission() -> None:
    response = client.get(BASE, headers=_headers(permissions=[], roles=["student"]))
    assert response.status_code == 403


def test_reporting_dashboard_runtime_rbac_roles_have_access() -> None:
    for role in ["reporting_admin", "vice_rector", "auditor", "analyst", "registrar", "data_manager"]:
        response = client.get(BASE, headers=_headers(roles=[role]))
        assert response.status_code == 200


def test_reporting_dashboard_coverage_and_signal_inventory() -> None:
    response = client.get(BASE, headers=_headers())
    assert response.status_code == 200
    body = response.json()

    dashboard_names = {item["dashboard_name"] for item in body["dashboards"]}
    assert dashboard_names == {
        "Ministry Reporting",
        "Accreditation Reporting",
        "Regulatory Reporting",
        "Ranking Reporting",
        "NOBD Reporting",
        "Compliance Monitoring",
    }
    assert set(body["signal_inventory"]) == {
        "reporting_readiness_low",
        "reporting_workload_high",
        "reporting_risk_high",
        "reporting_submission_delay",
        "reporting_attention_required",
    }
    assert body["read_only"] is True


def test_reporting_dashboard_runtime_tenant_isolation_service_level() -> None:
    service = ReportingDashboardRuntimeService()
    tenant4 = service.get_dashboard(4).model_dump(mode="json")
    tenant11 = service.get_dashboard(11).model_dump(mode="json")

    assert tenant4["tenant_id"] == 4
    assert tenant11["tenant_id"] == 11
    assert tenant4["dashboards"][0]["id"] != tenant11["dashboards"][0]["id"]


def test_reporting_dashboard_runtime_visibility_surfaces() -> None:
    readiness = client.get(f"{BASE}/readiness", headers=_headers())
    workload = client.get(f"{BASE}/workload", headers=_headers())
    risks = client.get(f"{BASE}/risks", headers=_headers())
    signals = client.get(f"{BASE}/signals", headers=_headers())

    assert readiness.status_code == 200
    assert workload.status_code == 200
    assert risks.status_code == 200
    assert signals.status_code == 200

    readiness_items = readiness.json()["readiness"]
    workload_items = workload.json()["workload"]
    risk_items = risks.json()["risks"]
    signal_items = signals.json()["signals"]

    assert readiness_items and workload_items and risk_items and signal_items
    assert all(item["read_only"] is True for item in readiness_items)
    assert all(item["read_only"] is True for item in workload_items)
    assert all(item["read_only"] is True for item in risk_items)
    assert all(item["read_only"] is True for item in signal_items)


def test_reporting_dashboard_endpoints_are_read_only() -> None:
    headers = _headers()
    for endpoint in ["", "/readiness", "/workload", "/risks", "/signals"]:
        response = client.get(f"{BASE}{endpoint}", headers=headers)
        assert response.status_code == 200
        assert response.json()["read_only"] is True
