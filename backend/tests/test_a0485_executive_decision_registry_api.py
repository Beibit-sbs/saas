from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token


client = TestClient(app)
BASE = "/api/admin/executive-governance/runtime"


def _admin_headers() -> dict[str, str]:
    token = create_access_token(
        user_id="702",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["admin.executive_control_tower.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_decision_registry_requires_auth() -> None:
    assert client.get(f"{BASE}/decisions").status_code in (401, 403)


def test_decision_registry_aggregation_and_source_attribution() -> None:
    response = client.get(f"{BASE}/decisions", headers=_admin_headers())
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 7
    sources = {entry["decision_source"] for entry in entries}
    assert sources == {"committee_decision_registry", "order_decree_registry"}
    assert all("decision_id" in entry for entry in entries)


def test_decision_summary_execution_linkage_statuses() -> None:
    response = client.get(f"{BASE}/decisions/summary", headers=_admin_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["aggregator_only"] is True
    assert body["read_only"] is True
    statuses = body["execution_status_counts"]
    assert set(statuses.keys()) == {
        "NOT_STARTED",
        "IN_PROGRESS",
        "AT_RISK",
        "ESCALATED",
        "OVERDUE",
        "COMPLETED",
        "CLOSED",
    }
    assert body["decision_sources"]["committee_decision_registry"] >= 1
    assert body["decision_sources"]["order_decree_registry"] >= 1


def test_decision_execution_summary_signal_surface() -> None:
    response = client.get(f"{BASE}/decisions/execution", headers=_admin_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["signal_families"] == [
        "decision_stagnation",
        "overdue_assignment",
        "execution_delay",
        "escalation_risk",
        "protocol_non_execution",
    ]
    assert body["overdue_items"] >= 1
    assert body["escalated_items"] >= 1


def test_decision_registry_tenant_isolation() -> None:
    app.dependency_overrides[get_current_tenant] = lambda: {"id": 3, "name": "Tenant-3"}
    tenant3 = client.get(f"{BASE}/decisions/summary", headers=_admin_headers())

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 11, "name": "Tenant-11"}
    tenant11 = client.get(f"{BASE}/decisions/summary", headers=_admin_headers())

    app.dependency_overrides.pop(get_current_tenant, None)

    assert tenant3.status_code == 200
    assert tenant11.status_code == 200
    body3 = tenant3.json()
    body11 = tenant11.json()
    assert body3["tenant_id"] == 3
    assert body11["tenant_id"] == 11
    assert body3["entries"][0]["decision_id"] != body11["entries"][0]["decision_id"]
