from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token


client = TestClient(app)
BASE = "/api/admin/executive-governance/runtime"


def _admin_headers() -> dict[str, str]:
    token = create_access_token(
        user_id="704",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["admin.executive_control_tower.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_assignment_runtime_requires_auth() -> None:
    assert client.get(f"{BASE}/assignments").status_code in (401, 403)


def test_assignment_registry_surface() -> None:
    response = client.get(f"{BASE}/assignments", headers=_admin_headers())
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) >= 1
    first = entries[0]
    assert "assignment_id" in first
    assert "assignment_title" in first
    assert "assignment_source" in first
    assert "assignment_type" in first
    assert "assigned_unit" in first
    assert "assigned_person" in first
    assert "completion_percent" in first
    assert "execution_status" in first
    assert "risk_level" in first
    assert "overdue_flag" in first
    assert "escalation_flag" in first


def test_assignment_summary_and_execution_surfaces() -> None:
    summary = client.get(f"{BASE}/assignments/summary", headers=_admin_headers())
    execution = client.get(f"{BASE}/assignments/execution", headers=_admin_headers())

    assert summary.status_code == 200
    assert execution.status_code == 200

    summary_body = summary.json()
    execution_body = execution.json()

    assert summary_body["read_only"] is True
    assert summary_body["aggregator_only"] is True
    assert summary_body["total_assignments"] >= summary_body["completed_assignments"]
    assert summary_body["active_assignments"] + summary_body["completed_assignments"] == summary_body["total_assignments"]

    assert execution_body["read_only"] is True
    assert execution_body["aggregator_only"] is True
    assert set(execution_body["escalation_inventory"].keys()) == {"high", "critical", "overdue"}
    assert set(execution_body["escalation_summary"].keys()) == {"total_escalations", "high_risk", "overdue"}


def test_assignment_risk_signal_inventory() -> None:
    response = client.get(f"{BASE}/assignments/risks", headers=_admin_headers())
    assert response.status_code == 200
    body = response.json()

    assert body["execution_trend"] in {"STABLE", "IMPROVING", "DECLINING"}
    assert body["escalation_trends"] == ["high_risk_watchlist_active", "escalation_rate_stable"]
    assert body["signal_families"] == [
        "overdue_assignment",
        "execution_delay",
        "escalation_risk",
        "assignment_stagnation",
        "workload_imbalance",
        "strategic_goal_slippage",
        "ministry_deadline_risk",
    ]


def test_assignment_tenant_isolation() -> None:
    app.dependency_overrides[get_current_tenant] = lambda: {"id": 5, "name": "Tenant-5"}
    tenant5 = client.get(f"{BASE}/assignments/summary", headers=_admin_headers())

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 13, "name": "Tenant-13"}
    tenant13 = client.get(f"{BASE}/assignments/summary", headers=_admin_headers())

    app.dependency_overrides.pop(get_current_tenant, None)

    assert tenant5.status_code == 200
    assert tenant13.status_code == 200
    body5 = tenant5.json()
    body13 = tenant13.json()
    assert body5["tenant_id"] == 5
    assert body13["tenant_id"] == 13
    assert body5["entries"][0]["assignment_id"] != body13["entries"][0]["assignment_id"]
