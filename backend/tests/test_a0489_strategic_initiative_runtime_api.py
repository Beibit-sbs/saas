from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token


client = TestClient(app)
BASE = "/api/admin/executive-governance/runtime"


def _admin_headers() -> dict[str, str]:
    token = create_access_token(
        user_id="709",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["admin.executive_control_tower.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_strategic_initiatives_requires_auth() -> None:
    assert client.get(f"{BASE}/strategic-initiatives").status_code in (401, 403)


def test_strategic_initiatives_aggregation_surface() -> None:
    response = client.get(f"{BASE}/strategic-initiatives", headers=_admin_headers())
    assert response.status_code == 200
    body = response.json()

    assert isinstance(body, list)
    assert len(body) >= 1
    first = body[0]
    assert first["initiative_id"]
    assert first["initiative_title"]
    assert first["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def test_strategic_summary_alignment_and_roadmap_visibility() -> None:
    response = client.get(f"{BASE}/strategic-initiatives/summary", headers=_admin_headers())
    assert response.status_code == 200
    body = response.json()

    assert body["read_only"] is True
    assert body["aggregator_only"] is True
    assert body["total_initiatives"] >= body["completed_initiatives"]
    assert "kpi_deviation_visibility" in body
    assert "kpi_ownership_visibility" in body
    assert "roadmap_visibility" in body


def test_strategic_risks_and_development_program_surface() -> None:
    risks = client.get(f"{BASE}/strategic-initiatives/risks", headers=_admin_headers())
    program = client.get(f"{BASE}/development-program", headers=_admin_headers())
    program_summary = client.get(f"{BASE}/development-program/summary", headers=_admin_headers())

    assert risks.status_code == 200
    assert program.status_code == 200
    assert program_summary.status_code == 200

    risks_body = risks.json()
    program_body = program.json()
    program_summary_body = program_summary.json()

    assert risks_body["read_only"] is True
    assert risks_body["aggregator_only"] is True
    assert isinstance(risks_body["kpi_deviation_hotspots"], dict)
    assert isinstance(risks_body["strategic_bottlenecks"], dict)

    assert program_body["read_only"] is True
    assert program_body["aggregator_only"] is True
    assert program_body["initiative_count"] >= program_body["completed_initiatives"]

    assert program_summary_body["read_only"] is True
    assert program_summary_body["aggregator_only"] is True
    assert program_summary_body["program_name"] == program_body["program_name"]


def test_strategic_runtime_tenant_isolation() -> None:
    app.dependency_overrides[get_current_tenant] = lambda: {"id": 8, "name": "Tenant-8"}
    tenant8 = client.get(f"{BASE}/strategic-initiatives/summary", headers=_admin_headers())

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 16, "name": "Tenant-16"}
    tenant16 = client.get(f"{BASE}/strategic-initiatives/summary", headers=_admin_headers())

    app.dependency_overrides.pop(get_current_tenant, None)

    assert tenant8.status_code == 200
    assert tenant16.status_code == 200
    body8 = tenant8.json()
    body16 = tenant16.json()

    assert body8["tenant_id"] == 8
    assert body16["tenant_id"] == 16
    assert body8["read_only"] is True
    assert body16["read_only"] is True
