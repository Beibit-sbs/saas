from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token


client = TestClient(app)
BASE = "/api/admin/executive-governance/runtime"


ALLOWED_ROLES = [
    "rector",
    "vice_rector",
    "chief_of_staff",
    "executive_manager",
    "strategic_office",
    "auditor",
    "administrator",
]


def _headers_for_role(role: str) -> dict[str, str]:
    token = create_access_token(
        user_id="901",
        roles=[role],
        auth_source="test",
        tenant_id=1,
        permissions=["admin.executive_control_tower.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_kpi_runtime_requires_auth() -> None:
    assert client.get(f"{BASE}/kpis").status_code in (401, 403)


def test_kpi_runtime_rbac_visibility_is_read_only() -> None:
    for role in ALLOWED_ROLES:
        response = client.get(f"{BASE}/kpis", headers=_headers_for_role(role))
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert len(body) >= 1
        assert "kpi_id" in body[0]


def test_kpi_aggregation_performance_and_risks_surface() -> None:
    headers = _headers_for_role("administrator")
    kpis = client.get(f"{BASE}/kpis", headers=headers)
    summary = client.get(f"{BASE}/kpis/summary", headers=headers)
    performance = client.get(f"{BASE}/kpis/performance", headers=headers)
    risks = client.get(f"{BASE}/kpis/risks", headers=headers)
    trends = client.get(f"{BASE}/kpis/trends", headers=headers)

    assert kpis.status_code == 200
    assert summary.status_code == 200
    assert performance.status_code == 200
    assert risks.status_code == 200
    assert trends.status_code == 200

    kpis_body = kpis.json()
    summary_body = summary.json()
    performance_body = performance.json()
    risks_body = risks.json()
    trends_body = trends.json()

    assert len(kpis_body) == summary_body["total_kpis"]
    assert summary_body["read_only"] is True
    assert summary_body["aggregator_only"] is True
    assert summary_body["completion_rate"] >= 0
    assert summary_body["achievement_rate"] >= 0
    assert summary_body["deviation_rate"] >= 0
    assert summary_body["risk_rate"] >= 0

    assert performance_body["read_only"] is True
    assert performance_body["aggregator_only"] is True
    assert performance_body["kpi_completion_rate"] == summary_body["completion_rate"]
    assert performance_body["kpi_risk_rate"] == summary_body["risk_rate"]
    assert isinstance(performance_body["unit_kpi_performance"], dict)
    assert isinstance(performance_body["strategic_kpi_alignment"], dict)

    assert risks_body["read_only"] is True
    assert risks_body["aggregator_only"] is True
    assert isinstance(risks_body["high_risk_kpis"], list)
    assert isinstance(risks_body["missed_kpis"], list)
    assert isinstance(risks_body["kpi_deviation_hotspots"], dict)

    assert trends_body["read_only"] is True
    assert trends_body["aggregator_only"] is True
    assert isinstance(trends_body["performance_scores"], list)
    assert "kpi_drift" in trends_body["signal_families"]


def test_kpi_runtime_tenant_isolation() -> None:
    headers = _headers_for_role("administrator")

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 7, "name": "Tenant-7"}
    tenant7 = client.get(f"{BASE}/kpis/summary", headers=headers)

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 11, "name": "Tenant-11"}
    tenant11 = client.get(f"{BASE}/kpis/summary", headers=headers)

    app.dependency_overrides.pop(get_current_tenant, None)

    assert tenant7.status_code == 200
    assert tenant11.status_code == 200

    body7 = tenant7.json()
    body11 = tenant11.json()

    assert body7["tenant_id"] == 7
    assert body11["tenant_id"] == 11
    assert body7["entries"][0]["kpi_id"] != body11["entries"][0]["kpi_id"]
    assert body7["read_only"] is True
    assert body11["read_only"] is True
