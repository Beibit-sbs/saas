from __future__ import annotations

import pytest

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.digital_twin import permissions
from tests.conftest import client


BASE = "/api/admin/digital-twin"


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
    assert len(routes) == 2


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
