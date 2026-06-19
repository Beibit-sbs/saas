from __future__ import annotations

from unittest.mock import patch

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
    assert len(routes) == 5


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


@patch("app.modules.digital_twin.service._live_enrollment_count", return_value=2000)
def test_capacity_simulation_uses_live_enrollments_when_requested(mock_count) -> None:
    resp = client.post(
        f"{BASE}/simulate/capacity",
        headers=ADMIN_HEADERS,
        json={"current_students": 10, "intake_growth_percent": 20, "use_live_sources": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    # live count (2000) overrides the caller value (10): projected = 2000 * 1.2
    assert body["projected_students"] == 2400
    assert body["live_sources_used"] == ["enrollments"]
    students = next(e for e in body["evidence"] if e["field"] == "current_students")
    assert students["mode"] == "live"
    assert students["value"] == 2000


@patch("app.modules.digital_twin.service._live_enrollment_count", return_value=None)
def test_capacity_simulation_falls_back_when_live_read_fails(mock_count) -> None:
    resp = client.post(
        f"{BASE}/simulate/capacity",
        headers=ADMIN_HEADERS,
        json={"current_students": 800, "intake_growth_percent": 0, "use_live_sources": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    # honest fallback to caller-provided; no fabrication
    assert body["projected_students"] == 800
    assert body["live_sources_used"] == []
    students = next(e for e in body["evidence"] if e["field"] == "current_students")
    assert students["mode"] == "caller_provided"


def test_early_warning_requires_auth_and_denies_viewer() -> None:
    assert client.post(f"{BASE}/early-warning/capacity", json={"current_students": 1, "intake_growth_percent": 0}).status_code in (401, 403)
    resp = client.post(
        f"{BASE}/early-warning/capacity",
        headers=VIEWER_HEADERS,
        json={"current_students": 1000, "intake_growth_percent": 20},
    )
    assert resp.status_code == 403


def test_early_warning_flags_capacity_risk_with_human_action() -> None:
    resp = client.post(
        f"{BASE}/early-warning/capacity",
        headers=ADMIN_HEADERS,
        json={
            "current_students": 1000,
            "intake_growth_percent": 20,
            "classroom_capacity": 600,
            "dormitory_capacity": 300,
            "housing_demand_ratio": 0.5,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    signals = {w["signal"]: w for w in body["warnings"]}
    # classroom util 1200/600 = 2.0 -> high; dormitory 600/300 = 2.0 -> high
    assert signals["classroom_capacity_risk"]["severity"] == "high"
    assert signals["classroom_capacity_risk"]["recommended_human_action"] == "escalate_to_scheduling_and_facilities"
    assert signals["dormitory_capacity_risk"]["recommended_human_action"] == "escalate_to_housing_office"
    # human-gated, no autonomy
    assert all(w["requires_human_approval"] is True for w in body["warnings"])
    assert all(w["no_autonomous_action"] is True for w in body["warnings"])
    # honest: signal registries declared as candidate sources, not fabricated counts
    assert "student_risk_signal_registry" in body["candidate_signal_sources"]
    assert body["human_review_required"] is True
    assert body["projection"]["safety_flags"]["fake_metrics"] is False


def test_early_warning_silent_when_within_capacity() -> None:
    resp = client.post(
        f"{BASE}/early-warning/capacity",
        headers=ADMIN_HEADERS,
        json={"current_students": 1000, "intake_growth_percent": 0, "classroom_capacity": 2000},
    )
    assert resp.status_code == 200
    body = resp.json()
    # util 1000/2000 = 0.5 -> no warning
    assert all(w["signal"] != "classroom_capacity_risk" for w in body["warnings"])


def test_capacity_scenarios_requires_auth_and_denies_viewer() -> None:
    assert client.post(f"{BASE}/scenarios/capacity", json={"current_students": 1}).status_code in (401, 403)
    resp = client.post(f"{BASE}/scenarios/capacity", headers=VIEWER_HEADERS, json={"current_students": 1000})
    assert resp.status_code == 403


def test_capacity_scenarios_named_registry_for_executive_review() -> None:
    resp = client.post(
        f"{BASE}/scenarios/capacity",
        headers=ADMIN_HEADERS,
        json={"current_students": 1000, "classroom_capacity": 1000},
    )
    assert resp.status_code == 200
    body = resp.json()
    scenarios = {s["name"]: s for s in body["scenarios"]}
    # default named scenarios: baseline, +10, +20, +30
    assert set(scenarios) == {"baseline", "intake_plus_10pct", "intake_plus_20pct", "intake_plus_30pct"}
    # deterministic projections per scenario
    assert scenarios["baseline"]["projection"]["projected_students"] == 1000
    assert scenarios["intake_plus_30pct"]["projection"]["projected_students"] == 1300
    # +30% util 1.3 -> a high classroom warning surfaces in that scenario
    plus30_signals = {w["signal"]: w for w in scenarios["intake_plus_30pct"]["warnings"]}
    assert plus30_signals["classroom_capacity_risk"]["severity"] == "high"
    # baseline util 1.0 -> no classroom warning (strict >)
    assert all(w["signal"] != "classroom_capacity_risk" for w in scenarios["baseline"]["warnings"])
    assert body["human_review_required"] is True
