from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.reporting_runtime.runtime_compliance_service import ComplianceMonitoringRuntimeService


client = TestClient(app)
BASE = "/api/admin/reporting-brain/runtime/compliance"


def _headers(
    *,
    tenant_id: int = 1,
    permissions: list[str] | None = None,
    roles: list[str] | None = None,
) -> dict[str, str]:
    token = create_access_token(
        user_id="712",
        roles=roles or ["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=permissions if permissions is not None else ["admin.reporting_runtime.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_compliance_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


def test_compliance_runtime_requires_summary_read_permission() -> None:
    response = client.get(BASE, headers=_headers(permissions=[], roles=["student"]))
    assert response.status_code == 403


def test_compliance_runtime_rbac_roles_have_access() -> None:
    for role in ["reporting_admin", "vice_rector", "quality_manager", "auditor", "analyst", "compliance_manager"]:
        response = client.get(BASE, headers=_headers(roles=[role]))
        assert response.status_code == 200


def test_compliance_runtime_coverage_and_signal_inventory() -> None:
    response = client.get(BASE, headers=_headers())
    assert response.status_code == 200
    body = response.json()

    control_names = {item["control_name"] for item in body["reports"]}
    assert control_names == {
        "Ministry Compliance",
        "Accreditation Compliance",
        "NOBD Compliance",
        "Regulatory Compliance",
        "Ranking Compliance",
        "Internal Policy Compliance",
    }
    assert set(body["signal_inventory"]) == {
        "compliance_gap_high",
        "compliance_readiness_low",
        "compliance_risk_high",
        "control_failure_detected",
        "mandatory_submission_missing",
    }
    assert body["read_only"] is True


def test_compliance_runtime_tenant_isolation_service_level() -> None:
    service = ComplianceMonitoringRuntimeService()
    tenant3 = service.get_compliance(3).model_dump(mode="json")
    tenant10 = service.get_compliance(10).model_dump(mode="json")

    assert tenant3["tenant_id"] == 3
    assert tenant10["tenant_id"] == 10
    assert tenant3["reports"][0]["id"] != tenant10["reports"][0]["id"]


def test_compliance_runtime_visibility_surfaces() -> None:
    controls = client.get(f"{BASE}/controls", headers=_headers())
    readiness = client.get(f"{BASE}/readiness", headers=_headers())
    gaps = client.get(f"{BASE}/gaps", headers=_headers())
    risks = client.get(f"{BASE}/risks", headers=_headers())

    assert controls.status_code == 200
    assert readiness.status_code == 200
    assert gaps.status_code == 200
    assert risks.status_code == 200

    control_items = controls.json()["controls"]
    readiness_items = readiness.json()["readiness"]
    gap_items = gaps.json()["gaps"]
    risk_items = risks.json()["risks"]

    assert control_items and readiness_items and gap_items and risk_items
    assert all("control_type" in item for item in control_items)
    assert all("readiness_level" in item for item in readiness_items)
    assert all("gap_severity" in item for item in gap_items)
    assert all(item["signal_owner_module"] == "brain_core" for item in risk_items)


def test_compliance_runtime_endpoints_are_read_only() -> None:
    headers = _headers()
    for endpoint in ["", "/controls", "/readiness", "/gaps", "/risks"]:
        response = client.get(f"{BASE}{endpoint}", headers=headers)
        assert response.status_code == 200
        assert response.json()["read_only"] is True