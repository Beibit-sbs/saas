from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.reporting_runtime.runtime_ministry_service import MinistryReportingRuntimeService


client = TestClient(app)
BASE = "/api/admin/reporting-brain/runtime/ministry"


def _headers(
    *,
    tenant_id: int = 1,
    permissions: list[str] | None = None,
    roles: list[str] | None = None,
) -> dict[str, str]:
    token = create_access_token(
        user_id="707",
        roles=roles or ["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=permissions if permissions is not None else ["admin.reporting_runtime.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_ministry_reporting_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


def test_ministry_reporting_requires_summary_read_permission() -> None:
    response = client.get(BASE, headers=_headers(permissions=[], roles=["student"]))
    assert response.status_code == 403


def test_ministry_reporting_rbac_roles_have_access() -> None:
    for role in ["reporting_admin", "vice_rector", "quality_manager", "analyst", "auditor"]:
        response = client.get(BASE, headers=_headers(roles=[role]))
        assert response.status_code == 200


def test_ministry_reporting_coverage_and_signal_inventory() -> None:
    response = client.get(BASE, headers=_headers())
    assert response.status_code == 200
    body = response.json()

    report_names = {item["report_name"] for item in body["reports"]}
    assert report_names == {
        "Statistical reporting",
        "Academic reporting",
        "Scientific reporting",
        "Financial reporting",
        "Infrastructure reporting",
        "Human resource reporting",
        "Digitalization reporting",
    }
    assert set(body["signal_inventory"]) == {
        "ministry_deadline_risk",
        "report_overdue",
        "missing_required_data",
        "reporting_incomplete",
        "reporting_readiness_low",
    }
    assert body["read_only"] is True


def test_ministry_reporting_tenant_isolation_service_level() -> None:
    service = MinistryReportingRuntimeService()
    tenant2 = service.get_ministry(2).model_dump(mode="json")
    tenant9 = service.get_ministry(9).model_dump(mode="json")

    assert tenant2["tenant_id"] == 2
    assert tenant9["tenant_id"] == 9
    assert tenant2["reports"][0]["id"] != tenant9["reports"][0]["id"]


def test_ministry_reporting_deadline_readiness_and_risk_visibility() -> None:
    deadlines = client.get(f"{BASE}/deadlines", headers=_headers())
    readiness = client.get(f"{BASE}/readiness", headers=_headers())
    risks = client.get(f"{BASE}/risks", headers=_headers())

    assert deadlines.status_code == 200
    assert readiness.status_code == 200
    assert risks.status_code == 200

    deadline_items = deadlines.json()["deadlines"]
    readiness_items = readiness.json()["readiness"]
    risk_items = risks.json()["risks"]

    assert deadline_items and readiness_items and risk_items
    assert all("deadline_status" in item for item in deadline_items)
    assert all("readiness_score" in item for item in readiness_items)
    assert all(item["signal_owner_module"] == "brain_core" for item in risk_items)


def test_ministry_reporting_related_endpoints_are_read_only() -> None:
    headers = _headers()
    for endpoint in [
        "",
        "/cycles",
        "/deadlines",
        "/readiness",
        "/completeness",
        "/risks",
    ]:
        response = client.get(f"{BASE}{endpoint}", headers=headers)
        assert response.status_code == 200
        assert response.json()["read_only"] is True
