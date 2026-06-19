from __future__ import annotations

import pytest

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.digital_twin import permissions
from tests.conftest import _auth_headers, client


BASE = "/api/admin/digital-twin"
VIEWER_HEADERS = _auth_headers("viewer-dt@example.com", ["viewer"], tenant_id=1)


def _admin_headers() -> dict[str, str]:
    token = create_access_token(
        user_id="901",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=sorted(permissions.ALL_PERMISSIONS),
    )
    return {"Authorization": f"Bearer {token}"}


ADMIN_HEADERS = _admin_headers()


def test_route_surface_count() -> None:
    routes = [r for r in app.routes if getattr(r, "path", "").startswith(BASE)]
    assert len(routes) == 3


@pytest.mark.parametrize("path", ["/state", "/safety-boundaries"])
def test_no_auth_requires_protection(path: str) -> None:
    assert client.get(f"{BASE}{path}").status_code in (401, 403)


@pytest.mark.parametrize("tenant_id", [None, 0, -1, True, 1.2, "bad"])
def test_invalid_tenant_fail_closed(tenant_id) -> None:
    app.dependency_overrides[get_current_tenant] = lambda: {"id": tenant_id}
    try:
        resp = client.get(f"{BASE}/state", headers=ADMIN_HEADERS)
        assert resp.status_code == 400
    finally:
        app.dependency_overrides.pop(get_current_tenant, None)


def test_state_contract_is_reuse_and_safe() -> None:
    resp = client.get(f"{BASE}/state", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["runtime_mode"] == "METADATA_OBSERVATION_SIMULATION_HUMAN_REVIEW_ONLY"
    # reuses existing infrastructure, does not duplicate
    assert "student_risk_signal_registry" in body["source_signal_registries"]
    assert "scheduling" in body["source_capacity_modules"]
    assert "student_population" in body["observed_dimensions"]
    # no fabricated metrics; honest incomplete data
    assert body["safety_flags"]["fake_metrics"] is False
    assert body["incomplete_data"] is True


def test_safety_boundaries_block_autonomy() -> None:
    resp = client.get(f"{BASE}/safety-boundaries", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    flags = body["safety_flags"]
    assert flags["no_autonomous_budget_commitment"] is True
    assert flags["no_autonomous_academic_decision"] is True
    assert flags["no_autonomous_disciplinary_decision"] is True
    assert flags["no_hidden_scoring"] is True
    assert flags["all_accepted_actions_audited"] is True
    assert "autonomous_budget_commitment" in body["forbidden_actions"]


def test_capacity_simulation_requires_auth() -> None:
    resp = client.post(f"{BASE}/simulate/capacity", json={"current_students": 1, "intake_growth_percent": 0})
    assert resp.status_code in (401, 403)


def test_viewer_cannot_run_capacity_simulation() -> None:
    resp = client.post(
        f"{BASE}/simulate/capacity",
        headers=VIEWER_HEADERS,
        json={"current_students": 1000, "intake_growth_percent": 20},
    )
    assert resp.status_code == 403


def test_capacity_simulation_is_deterministic_and_evidence_explained() -> None:
    resp = client.post(
        f"{BASE}/simulate/capacity",
        headers=ADMIN_HEADERS,
        json={
            "current_students": 1000,
            "intake_growth_percent": 20,
            "classroom_capacity": 900,
            "dormitory_capacity": 300,
            "housing_demand_ratio": 0.3,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    # deterministic arithmetic on real inputs (NOT fabricated)
    assert body["projected_students"] == 1200
    assert body["classroom_utilization"] == 1.3333
    assert body["dormitory_pressure"] == 1.2  # housing_need 360 / 300
    assert "classroom_capacity_exceeded" in body["risks"]
    assert "dormitory_capacity_exceeded" in body["risks"]
    assert body["incomplete_data"] is False
    assert body["human_review_required"] is True
    assert body["safety_flags"]["fake_metrics"] is False
    # evidence lineage tags each input to its source module
    sources = {e["field"]: e["source_module"] for e in body["evidence"]}
    assert sources["current_students"] == "enrollments"
    assert sources["classroom_capacity"] == "scheduling"


def test_capacity_simulation_marks_incomplete_when_capacity_unknown() -> None:
    resp = client.post(
        f"{BASE}/simulate/capacity",
        headers=ADMIN_HEADERS,
        json={"current_students": 500, "intake_growth_percent": 10},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["projected_students"] == 550
    assert body["classroom_utilization"] is None
    assert body["incomplete_data"] is True
    assert body["risks"] == []
