from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token


client = TestClient(app)
BASE = "/api/admin/executive-governance/runtime"


def _admin_headers() -> dict[str, str]:
    token = create_access_token(
        user_id="701",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["admin.executive_control_tower.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_runtime_requires_auth() -> None:
    assert client.get(f"{BASE}/overview").status_code in (401, 403)


def test_runtime_overview_surface_contract() -> None:
    response = client.get(f"{BASE}/overview", headers=_admin_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["owner_module"] == "executive_control_tower"
    assert body["read_only_runtime"] is True
    assert body["provider_integrations_enabled"] is False
    assert body["external_calls_enabled"] is False
    assert body["executive_assignments"] >= 1
    assert body["executive_decisions"] >= 1
    assert body["executive_protocols"] >= 1
    assert body["executive_meetings"] >= 1
    assert body["overdue_items"] >= 1
    assert body["escalated_items"] >= 1
    assert body["strategic_items"] >= 1
    assert body["executive_signals"] == 10


def test_runtime_summary_preserves_tenant_isolation() -> None:
    app.dependency_overrides[get_current_tenant] = lambda: {"id": 2, "name": "Tenant-2"}
    tenant2 = client.get(f"{BASE}/summary", headers=_admin_headers())

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 10, "name": "Tenant-10"}
    tenant10 = client.get(f"{BASE}/summary", headers=_admin_headers())

    app.dependency_overrides.pop(get_current_tenant, None)

    assert tenant2.status_code == 200
    assert tenant10.status_code == 200
    body2 = tenant2.json()
    body10 = tenant10.json()
    assert body2["tenant_id"] == 2
    assert body10["tenant_id"] == 10
    assert body2["executive_assignments"] != body10["executive_assignments"]


def test_runtime_signal_surface_inventory() -> None:
    response = client.get(f"{BASE}/signals", headers=_admin_headers())
    assert response.status_code == 200
    body = response.json()
    families = [item["signal_family"] for item in body]
    assert families == [
        "overdue_assignment",
        "execution_delay",
        "resolution_risk",
        "kpi_drift",
        "escalation_risk",
        "strategic_goal_slippage",
        "executive_workload",
        "ministry_deadline_risk",
        "protocol_non_execution",
        "decision_stagnation",
    ]
    assert all(item["owner_module"] == "brain_core" for item in body)
    assert all(item["read_only"] is True for item in body)


def test_runtime_dashboard_rbac_surface() -> None:
    response = client.get(f"{BASE}/dashboard", headers=_admin_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["dashboard_owner_module"] == "executive_control_tower"
    assert body["dashboard_view"] == "executive_control_tower"
    assert body["read_only"] is True
    assert body["auditability_preserved"] is True
    assert body["rbac_roles"] == [
        "rector",
        "vice_rector",
        "chief_of_staff",
        "executive_manager",
        "auditor",
        "administrator",
    ]
