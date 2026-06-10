from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token


client = TestClient(app)
BASE = "/api/admin/executive-governance/runtime/control-tower"


def _admin_headers() -> dict[str, str]:
    token = create_access_token(
        user_id="705",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["admin.executive_control_tower.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_control_tower_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


def test_control_tower_aggregation_surface() -> None:
    response = client.get(BASE, headers=_admin_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["read_only"] is True
    assert body["aggregator_only"] is True
    assert body["total_decisions"] >= 1
    assert body["total_protocols"] >= 1
    assert body["total_assignments"] >= body["completed_assignments"]
    assert body["active_assignments"] + body["completed_assignments"] == body["total_assignments"]


def test_control_tower_kpi_and_risk_aggregation() -> None:
    kpis = client.get(f"{BASE}/kpis", headers=_admin_headers())
    risks = client.get(f"{BASE}/risks", headers=_admin_headers())
    escalations = client.get(f"{BASE}/escalations", headers=_admin_headers())

    assert kpis.status_code == 200
    assert risks.status_code == 200
    assert escalations.status_code == 200

    kpis_body = kpis.json()
    risks_body = risks.json()
    escalations_body = escalations.json()

    assert set(kpis_body["kpi_distribution"].keys()) == {"green", "amber", "red"}
    assert "kpi_drift" in kpis_body["signal_families"]
    assert risks_body["risk_score"] >= 0
    assert "executive_workload" in risks_body["signal_families"]
    assert "workload_distribution" in escalations_body
    assert "unit_performance" in escalations_body


def test_control_tower_summary_surface() -> None:
    response = client.get(f"{BASE}/summary", headers=_admin_headers())
    assert response.status_code == 200
    body = response.json()

    assert body["read_only"] is True
    assert body["aggregator_only"] is True
    assert set(body.keys()) >= {
        "rector_overview",
        "university_execution_status",
        "strategic_initiatives",
        "executive_risks",
        "kpi_performance",
        "escalation_summary",
    }


def test_control_tower_tenant_isolation() -> None:
    app.dependency_overrides[get_current_tenant] = lambda: {"id": 6, "name": "Tenant-6"}
    tenant6 = client.get(BASE, headers=_admin_headers())

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 14, "name": "Tenant-14"}
    tenant14 = client.get(BASE, headers=_admin_headers())

    app.dependency_overrides.pop(get_current_tenant, None)

    assert tenant6.status_code == 200
    assert tenant14.status_code == 200
    body6 = tenant6.json()
    body14 = tenant14.json()
    assert body6["tenant_id"] == 6
    assert body14["tenant_id"] == 14
    assert body6["read_only"] is True
    assert body14["read_only"] is True
