from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token


client = TestClient(app)
BASE = "/api/admin/executive-governance/runtime"


def _admin_headers() -> dict[str, str]:
    token = create_access_token(
        user_id="703",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["admin.executive_control_tower.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_meeting_runtime_requires_auth() -> None:
    assert client.get(f"{BASE}/meetings").status_code in (401, 403)


def test_meeting_aggregation_surface() -> None:
    response = client.get(f"{BASE}/meetings", headers=_admin_headers())
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) >= 1
    first = entries[0]
    assert "meeting_id" in first
    assert "meeting_status" in first
    assert "protocol_count" in first
    assert "decision_count" in first


def test_protocol_aggregation_surface() -> None:
    response = client.get(f"{BASE}/protocols", headers=_admin_headers())
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) >= 1
    first = entries[0]
    assert "protocol_id" in first
    assert "protocol_status" in first
    assert "assignment_count" in first
    assert "execution_progress" in first


def test_protocol_execution_linkage() -> None:
    response = client.get(f"{BASE}/protocols/execution", headers=_admin_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["read_only"] is True
    assert set(body["linkage_inventory"].keys()) == {
        "meeting_registry",
        "protocol_registry",
        "decision_registry",
        "rector_assignment_workflow",
    }
    assert body["signal_families"] == [
        "protocol_non_execution",
        "execution_delay",
        "overdue_assignment",
        "escalation_risk",
        "decision_stagnation",
    ]


def test_meeting_protocol_tenant_isolation() -> None:
    app.dependency_overrides[get_current_tenant] = lambda: {"id": 4, "name": "Tenant-4"}
    tenant4 = client.get(f"{BASE}/protocols/summary", headers=_admin_headers())

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 12, "name": "Tenant-12"}
    tenant12 = client.get(f"{BASE}/protocols/summary", headers=_admin_headers())

    app.dependency_overrides.pop(get_current_tenant, None)

    assert tenant4.status_code == 200
    assert tenant12.status_code == 200
    body4 = tenant4.json()
    body12 = tenant12.json()
    assert body4["tenant_id"] == 4
    assert body12["tenant_id"] == 12
    assert body4["entries"][0]["protocol_id"] != body12["entries"][0]["protocol_id"]
