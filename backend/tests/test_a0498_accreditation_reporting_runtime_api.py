from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.reporting_runtime.runtime_accreditation_service import AccreditationReportingRuntimeService


client = TestClient(app)
BASE = "/api/admin/reporting-brain/runtime/accreditation"


def _headers(
    *,
    tenant_id: int = 1,
    permissions: list[str] | None = None,
    roles: list[str] | None = None,
) -> dict[str, str]:
    token = create_access_token(
        user_id="708",
        roles=roles or ["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=permissions if permissions is not None else ["admin.reporting_runtime.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_accreditation_reporting_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


def test_accreditation_reporting_requires_summary_read_permission() -> None:
    response = client.get(BASE, headers=_headers(permissions=[], roles=["student"]))
    assert response.status_code == 403


def test_accreditation_reporting_rbac_roles_have_access() -> None:
    for role in ["reporting_admin", "quality_manager", "accreditation_manager", "vice_rector", "auditor", "analyst"]:
        response = client.get(BASE, headers=_headers(roles=[role]))
        assert response.status_code == 200


def test_accreditation_reporting_coverage_and_signal_inventory() -> None:
    response = client.get(BASE, headers=_headers())
    assert response.status_code == 200
    body = response.json()

    accreditation_names = {item["accreditation_name"] for item in body["reports"]}
    assert accreditation_names == {
        "Institutional Accreditation",
        "Specialized Accreditation",
        "Program Accreditation",
        "International Accreditation",
        "Internal Quality Reviews",
        "Accreditation Evidence Packages",
    }
    assert set(body["signal_inventory"]) == {
        "accreditation_deadline_risk",
        "accreditation_gap",
        "missing_evidence",
        "accreditation_compliance_risk",
        "accreditation_readiness_low",
    }
    assert body["read_only"] is True


def test_accreditation_reporting_tenant_isolation_service_level() -> None:
    service = AccreditationReportingRuntimeService()
    tenant2 = service.get_accreditation(2).model_dump(mode="json")
    tenant9 = service.get_accreditation(9).model_dump(mode="json")

    assert tenant2["tenant_id"] == 2
    assert tenant9["tenant_id"] == 9
    assert tenant2["reports"][0]["id"] != tenant9["reports"][0]["id"]


def test_accreditation_reporting_visibility_surfaces() -> None:
    readiness = client.get(f"{BASE}/readiness", headers=_headers())
    compliance = client.get(f"{BASE}/compliance", headers=_headers())
    deadlines = client.get(f"{BASE}/deadlines", headers=_headers())
    risks = client.get(f"{BASE}/risks", headers=_headers())

    assert readiness.status_code == 200
    assert compliance.status_code == 200
    assert deadlines.status_code == 200
    assert risks.status_code == 200

    readiness_items = readiness.json()["readiness"]
    compliance_items = compliance.json()["compliance"]
    deadline_items = deadlines.json()["deadlines"]
    risk_items = risks.json()["risks"]

    assert readiness_items and compliance_items and deadline_items and risk_items
    assert all("readiness_score" in item for item in readiness_items)
    assert all("compliance_score" in item for item in compliance_items)
    assert all("deadline_status" in item for item in deadline_items)
    assert all(item["signal_owner_module"] == "brain_core" for item in risk_items)


def test_accreditation_reporting_related_endpoints_are_read_only() -> None:
    headers = _headers()
    for endpoint in [
        "",
        "/cycles",
        "/readiness",
        "/compliance",
        "/deadlines",
        "/risks",
    ]:
        response = client.get(f"{BASE}{endpoint}", headers=headers)
        assert response.status_code == 200
        assert response.json()["read_only"] is True
