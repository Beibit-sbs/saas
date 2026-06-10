from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.reporting_runtime.runtime_regulatory_service import RegulatoryReportingRuntimeService


client = TestClient(app)
BASE = "/api/admin/reporting-brain/runtime/regulatory"


def _headers(
    *,
    tenant_id: int = 1,
    permissions: list[str] | None = None,
    roles: list[str] | None = None,
) -> dict[str, str]:
    token = create_access_token(
        user_id="709",
        roles=roles or ["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=permissions if permissions is not None else ["admin.reporting_runtime.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_regulatory_reporting_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


def test_regulatory_reporting_requires_summary_read_permission() -> None:
    response = client.get(BASE, headers=_headers(permissions=[], roles=["student"]))
    assert response.status_code == 403


def test_regulatory_reporting_rbac_roles_have_access() -> None:
    for role in ["reporting_admin", "vice_rector", "quality_manager", "auditor", "analyst", "compliance_manager"]:
        response = client.get(BASE, headers=_headers(roles=[role]))
        assert response.status_code == 200


def test_regulatory_reporting_coverage_and_signal_inventory() -> None:
    response = client.get(BASE, headers=_headers())
    assert response.status_code == 200
    body = response.json()

    requirement_names = {item["requirement_name"] for item in body["reports"]}
    assert requirement_names == {
        "Licensing Requirements",
        "Educational Activity Requirements",
        "Scientific Activity Requirements",
        "Information Security Requirements",
        "Personal Data Requirements",
        "Labor Requirements",
        "Financial Requirements",
        "Internal Regulatory Requirements",
    }
    assert set(body["signal_inventory"]) == {
        "regulatory_deadline_risk",
        "compliance_violation_risk",
        "missing_required_document",
        "licensing_gap",
        "regulatory_readiness_low",
    }
    assert body["read_only"] is True


def test_regulatory_reporting_tenant_isolation_service_level() -> None:
    service = RegulatoryReportingRuntimeService()
    tenant2 = service.get_regulatory(2).model_dump(mode="json")
    tenant9 = service.get_regulatory(9).model_dump(mode="json")

    assert tenant2["tenant_id"] == 2
    assert tenant9["tenant_id"] == 9
    assert tenant2["reports"][0]["id"] != tenant9["reports"][0]["id"]


def test_regulatory_reporting_visibility_surfaces() -> None:
    requirements = client.get(f"{BASE}/requirements", headers=_headers())
    compliance = client.get(f"{BASE}/compliance", headers=_headers())
    deadlines = client.get(f"{BASE}/deadlines", headers=_headers())
    documents = client.get(f"{BASE}/documents", headers=_headers())
    risks = client.get(f"{BASE}/risks", headers=_headers())

    assert requirements.status_code == 200
    assert compliance.status_code == 200
    assert deadlines.status_code == 200
    assert documents.status_code == 200
    assert risks.status_code == 200

    requirement_items = requirements.json()["requirements"]
    compliance_items = compliance.json()["compliance"]
    deadline_items = deadlines.json()["deadlines"]
    document_items = documents.json()["documents"]
    risk_items = risks.json()["risks"]

    assert requirement_items and compliance_items and deadline_items and document_items and risk_items
    assert all("requirement_status" in item for item in requirement_items)
    assert all("compliance_score" in item for item in compliance_items)
    assert all("deadline_status" in item for item in deadline_items)
    assert all("document_name" in item for item in document_items)
    assert all(item["signal_owner_module"] == "brain_core" for item in risk_items)


def test_regulatory_reporting_related_endpoints_are_read_only() -> None:
    headers = _headers()
    for endpoint in ["", "/requirements", "/compliance", "/deadlines", "/documents", "/risks"]:
        response = client.get(f"{BASE}{endpoint}", headers=headers)
        assert response.status_code == 200
        assert response.json()["read_only"] is True
