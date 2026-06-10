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
        user_id="902",
        roles=[role],
        auth_source="test",
        tenant_id=1,
        permissions=["admin.executive_control_tower.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_executive_risk_runtime_requires_auth() -> None:
    assert client.get(f"{BASE}/risks").status_code in (401, 403)


def test_executive_risk_runtime_rbac_visibility_is_read_only() -> None:
    for role in ALLOWED_ROLES:
        headers = _headers_for_role(role)
        risks = client.get(f"{BASE}/risks", headers=headers)
        summary = client.get(f"{BASE}/risks/summary", headers=headers)
        heatmap = client.get(f"{BASE}/risks/heatmap", headers=headers)
        escalations = client.get(f"{BASE}/risks/escalations", headers=headers)
        score = client.get(f"{BASE}/risks/score", headers=headers)

        assert risks.status_code == 200
        assert summary.status_code == 200
        assert heatmap.status_code == 200
        assert escalations.status_code == 200
        assert score.status_code == 200


def test_executive_risk_aggregation_score_heatmap_and_escalations() -> None:
    headers = _headers_for_role("administrator")

    risks = client.get(f"{BASE}/risks", headers=headers)
    summary = client.get(f"{BASE}/risks/summary", headers=headers)
    heatmap = client.get(f"{BASE}/risks/heatmap", headers=headers)
    escalations = client.get(f"{BASE}/risks/escalations", headers=headers)
    score = client.get(f"{BASE}/risks/score", headers=headers)

    assert risks.status_code == 200
    assert summary.status_code == 200
    assert heatmap.status_code == 200
    assert escalations.status_code == 200
    assert score.status_code == 200

    risks_body = risks.json()
    summary_body = summary.json()
    heatmap_body = heatmap.json()
    escalations_body = escalations.json()
    score_body = score.json()

    assert isinstance(risks_body, list)
    assert len(risks_body) >= 1
    assert risks_body[0]["risk_id"]
    assert risks_body[0]["risk_source"]

    assert summary_body["read_only"] is True
    assert summary_body["aggregator_only"] is True
    assert summary_body["total_risks"] == len(risks_body)
    assert isinstance(summary_body["risk_distribution"], dict)
    assert isinstance(summary_body["risk_category_breakdown"], dict)
    assert isinstance(summary_body["risk_ownership_visibility"], dict)
    assert isinstance(summary_body["risk_trend_analysis"], dict)
    assert isinstance(summary_body["risk_hotspots"], dict)

    assert heatmap_body["read_only"] is True
    assert heatmap_body["aggregator_only"] is True
    assert isinstance(heatmap_body["heatmap"], dict)
    assert "75-100" in heatmap_body["heatmap"]

    assert escalations_body["read_only"] is True
    assert escalations_body["aggregator_only"] is True
    assert isinstance(escalations_body["high_risk_items"], list)
    assert isinstance(escalations_body["critical_risks"], list)
    assert isinstance(escalations_body["escalating_risks"], list)
    assert isinstance(escalations_body["overdue_risks"], list)
    assert "kpi_drift" in escalations_body["signal_families"]
    assert "accreditation_risk" in escalations_body["signal_families"]

    assert score_body["read_only"] is True
    assert score_body["aggregator_only"] is True
    assert score_body["executive_risk_score"] == summary_body["executive_risk_score"]
    assert score_body["high_risk_items"] == len(escalations_body["high_risk_items"])


def test_executive_risk_runtime_tenant_isolation() -> None:
    headers = _headers_for_role("administrator")

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 7, "name": "Tenant-7"}
    tenant7 = client.get(f"{BASE}/risks/summary", headers=headers)

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 11, "name": "Tenant-11"}
    tenant11 = client.get(f"{BASE}/risks/summary", headers=headers)

    app.dependency_overrides.pop(get_current_tenant, None)

    assert tenant7.status_code == 200
    assert tenant11.status_code == 200

    body7 = tenant7.json()
    body11 = tenant11.json()

    assert body7["tenant_id"] == 7
    assert body11["tenant_id"] == 11
    assert body7["entries"][0]["risk_id"] != body11["entries"][0]["risk_id"]
    assert body7["read_only"] is True
    assert body11["read_only"] is True
