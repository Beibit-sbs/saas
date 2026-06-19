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
    assert len(routes) == 7


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
    assert "enrollments" in body["live_sources_used"]
    students = next(e for e in body["evidence"] if e["field"] == "current_students")
    assert students["mode"] == "live"
    assert students["value"] == 2000


@patch("app.modules.digital_twin.service._live_classroom_capacity", return_value=2000)
@patch("app.modules.digital_twin.service._live_enrollment_count", return_value=None)
def test_capacity_simulation_uses_live_classroom_capacity(mock_enr, mock_cap) -> None:
    resp = client.post(
        f"{BASE}/simulate/capacity",
        headers=ADMIN_HEADERS,
        json={"current_students": 1000, "intake_growth_percent": 0, "classroom_capacity": 5, "use_live_sources": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    # live room capacity (2000) overrides caller value (5): util = 1000/2000 = 0.5
    assert body["classroom_utilization"] == 0.5
    assert "campus_rooms" in body["live_sources_used"]
    classroom = next(e for e in body["evidence"] if e["field"] == "classroom_capacity")
    assert classroom["mode"] == "live"
    assert classroom["source_module"] == "campus_rooms"
    assert classroom["value"] == 2000


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


def test_scenario_decision_requires_auth_and_denies_viewer() -> None:
    payload = {"scenario_name": "intake_plus_30pct", "decision": "accepted", "rationale": "ok"}
    assert client.post(f"{BASE}/scenarios/decision", json=payload).status_code in (401, 403)
    assert client.post(f"{BASE}/scenarios/decision", headers=VIEWER_HEADERS, json=payload).status_code == 403


@patch("app.modules.audit.service.log_admin_action")
def test_scenario_decision_is_recorded_to_audit_without_execution(mock_audit) -> None:
    resp = client.post(
        f"{BASE}/scenarios/decision",
        headers=ADMIN_HEADERS,
        json={"scenario_name": "intake_plus_30pct", "decision": "rejected", "rationale": "capacity risk too high"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["recorded"] is True
    assert body["decision"] == "rejected"
    assert body["scenario_name"] == "intake_plus_30pct"
    assert body["no_autonomous_execution"] is True
    assert body["audit_action"] == "digital_twin.scenario_decision_recorded"
    assert body["correlation_id"]
    # the decision was written to the real audit trail (Human approves -> Audit records)
    mock_audit.assert_called_once()
    kwargs = mock_audit.call_args.kwargs
    assert kwargs["action"] == "digital_twin.scenario_decision_recorded"
    assert kwargs["metadata"]["decision"] == "rejected"
    assert kwargs["metadata"]["no_autonomous_execution"] is True
    # tenant-scoped write (isolation invariant)
    assert kwargs["tenant_id"] == 1


def test_scenario_decision_rejects_invalid_decision_value() -> None:
    resp = client.post(
        f"{BASE}/scenarios/decision",
        headers=ADMIN_HEADERS,
        json={"scenario_name": "x", "decision": "execute_now", "rationale": "nope"},
    )
    assert resp.status_code == 422


def test_scenario_decisions_log_requires_auth_and_denies_viewer() -> None:
    assert client.get(f"{BASE}/scenarios/decisions").status_code in (401, 403)
    assert client.get(f"{BASE}/scenarios/decisions", headers=VIEWER_HEADERS).status_code == 403


@patch("app.modules.audit.service.list_admin_actions")
def test_scenario_decisions_log_reads_back_from_audit(mock_list) -> None:
    mock_list.return_value = [
        {
            "correlation_id": "cid-1",
            "actor": "reviewer-7",
            "timestamp": "2026-06-19T00:00:00Z",
            "metadata": {"scenario_name": "intake_plus_20pct", "decision": "accepted", "rationale": "ok"},
        }
    ]
    resp = client.get(f"{BASE}/scenarios/decisions", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    item = body["decisions"][0]
    assert item["scenario_name"] == "intake_plus_20pct"
    assert item["decision"] == "accepted"
    assert item["reviewer"] == "reviewer-7"
    assert item["correlation_id"] == "cid-1"
    assert body["no_autonomous_execution"] is True
    # queried the audit trail filtered to the decision action AND scoped to the caller's tenant
    assert mock_list.call_args.kwargs["action"] == "digital_twin.scenario_decision_recorded"
    assert mock_list.call_args.kwargs["tenant_id"] == 1
    assert mock_list.call_args.kwargs.get("include_all_tenants") in (None, False)


# --- Hardening from the A-056 adversarial review (15 confirmed findings) ---

_JSON_HEADERS = {**ADMIN_HEADERS, "Content-Type": "application/json"}


# Raw JSON tokens that parse to non-finite floats server-side (httpx json= cannot encode inf/nan).
@pytest.mark.parametrize("token", ["1e400", "-1e400", "NaN"])
def test_non_finite_growth_fails_closed_not_500(token) -> None:
    # F1: inf/nan must fail closed with a 4xx (422), never an unhandled 500 from round(inf).
    resp = client.post(
        f"{BASE}/simulate/capacity",
        headers=_JSON_HEADERS,
        content=f'{{"current_students": 100, "intake_growth_percent": {token}}}',
    )
    assert resp.status_code == 400


def test_non_finite_scenario_value_fails_closed_not_500() -> None:
    # F2: non-finite scenario list element must fail closed (422), never a 500.
    resp = client.post(
        f"{BASE}/scenarios/capacity",
        headers=_JSON_HEADERS,
        content='{"current_students": 100, "intake_growth_scenarios": [0, 1e400]}',
    )
    assert resp.status_code == 400


_FAIL_CLOSED_ROUTES = [
    ("get", "/state", None),
    ("get", "/safety-boundaries", None),
    ("post", "/simulate/capacity", {"current_students": 1, "intake_growth_percent": 0}),
    ("post", "/early-warning/capacity", {"current_students": 1, "intake_growth_percent": 0}),
    ("post", "/scenarios/capacity", {"current_students": 1}),
    ("post", "/scenarios/decision", {"scenario_name": "x", "decision": "accepted", "rationale": "y"}),
    ("get", "/scenarios/decisions", None),
]


@pytest.mark.parametrize("method,path,body", _FAIL_CLOSED_ROUTES)
@pytest.mark.parametrize("bad_tenant", [None, 0, -1, True, 1.2, "bad"])
def test_every_route_is_tenant_fail_closed(method, path, body, bad_tenant) -> None:
    # F4: tenant fail-closed (-> 400) must hold on ALL routes, not just /state.
    app.dependency_overrides[get_current_tenant] = lambda: {"id": bad_tenant}
    try:
        if method == "get":
            resp = client.get(f"{BASE}{path}", headers=ADMIN_HEADERS)
        else:
            resp = client.post(f"{BASE}{path}", headers=ADMIN_HEADERS, json=body)
        assert resp.status_code == 400
    finally:
        app.dependency_overrides.pop(get_current_tenant, None)


@patch("app.modules.digital_twin.service._live_enrollment_count", return_value=None)
@patch("app.modules.digital_twin.service._live_classroom_capacity", return_value=None)
def test_live_classroom_fallback_keeps_caller_value(mock_cap, mock_enr) -> None:
    # F6: when the live room read fails, fall back honestly to the caller capacity.
    resp = client.post(
        f"{BASE}/simulate/capacity",
        headers=ADMIN_HEADERS,
        json={"current_students": 1000, "intake_growth_percent": 0, "classroom_capacity": 800, "use_live_sources": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["classroom_utilization"] == 1.25  # 1000/800
    assert "campus_rooms" not in body["live_sources_used"]
    classroom = next(e for e in body["evidence"] if e["field"] == "classroom_capacity")
    assert classroom["mode"] == "caller_provided"
    assert classroom["source_module"] == "scheduling"


@patch("app.modules.digital_twin.service._live_enrollment_count", return_value=None)
@patch("app.modules.digital_twin.service._live_classroom_capacity", return_value=0)
def test_live_classroom_zero_does_not_override(mock_cap, mock_enr) -> None:
    # F5: a zero live room total must not override a valid caller capacity / force incomplete.
    resp = client.post(
        f"{BASE}/simulate/capacity",
        headers=ADMIN_HEADERS,
        json={"current_students": 1000, "intake_growth_percent": 0, "classroom_capacity": 500, "use_live_sources": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["classroom_utilization"] == 2.0  # 1000/500, caller value kept
    assert body["incomplete_data"] is False


@pytest.mark.parametrize("growth,expected", [(-50.0, 500), (-100.0, 0)])
def test_negative_growth_is_deterministic(growth, expected) -> None:
    # F7: ge=-100 is allowed; verify the deterministic shrink and no fabricated risk.
    resp = client.post(
        f"{BASE}/simulate/capacity",
        headers=ADMIN_HEADERS,
        json={"current_students": 1000, "intake_growth_percent": growth, "classroom_capacity": 1000},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["projected_students"] == expected
    assert "classroom_capacity_exceeded" not in body["risks"]


def test_utilization_exactly_one_is_not_a_risk() -> None:
    # F8: strict > boundary at 1.0 -> no warning.
    resp = client.post(
        f"{BASE}/early-warning/capacity",
        headers=ADMIN_HEADERS,
        json={"current_students": 1000, "intake_growth_percent": 0, "classroom_capacity": 1000},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["projection"]["classroom_utilization"] == 1.0
    assert all(w["signal"] != "classroom_capacity_risk" for w in body["warnings"])


def test_utilization_exactly_1_2_is_medium_not_high() -> None:
    # F8: 1.2 boundary -> medium (not high, which needs strictly > 1.2).
    resp = client.post(
        f"{BASE}/early-warning/capacity",
        headers=ADMIN_HEADERS,
        json={"current_students": 1200, "intake_growth_percent": 0, "classroom_capacity": 1000},
    )
    assert resp.status_code == 200
    body = resp.json()
    warn = next(w for w in body["warnings"] if w["signal"] == "classroom_capacity_risk")
    assert warn["severity"] == "medium"


def test_dormitory_incomplete_when_capacity_unknown() -> None:
    # F9: dormitory_capacity=0 with demand>0 -> dorm_pressure None + incomplete, classroom still computed.
    resp = client.post(
        f"{BASE}/simulate/capacity",
        headers=ADMIN_HEADERS,
        json={"current_students": 1000, "intake_growth_percent": 0, "classroom_capacity": 1000, "dormitory_capacity": 0, "housing_demand_ratio": 0.3},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["dormitory_pressure"] is None
    assert body["incomplete_data"] is True
    assert body["classroom_utilization"] == 1.0


@patch("app.modules.audit.service.log_admin_action")
def test_read_only_routes_never_write_audit(mock_audit) -> None:
    # F12: simulate / early-warning / scenarios must not write to the audit trail.
    for path, body in [
        ("/simulate/capacity", {"current_students": 10, "intake_growth_percent": 0}),
        ("/early-warning/capacity", {"current_students": 10, "intake_growth_percent": 0}),
        ("/scenarios/capacity", {"current_students": 10}),
    ]:
        assert client.post(f"{BASE}{path}", headers=ADMIN_HEADERS, json=body).status_code == 200
    mock_audit.assert_not_called()


@patch("app.modules.digital_twin.service._live_classroom_capacity", return_value=900)
@patch("app.modules.digital_twin.service._live_enrollment_count", return_value=1000)
def test_both_live_sources_used_and_provider_stays_disabled(mock_enr, mock_cap) -> None:
    # F13: both live sources resolve -> both tagged live; provider_live_enabled stays false.
    resp = client.post(
        f"{BASE}/simulate/capacity",
        headers=ADMIN_HEADERS,
        json={"current_students": 1, "intake_growth_percent": 0, "classroom_capacity": 1, "use_live_sources": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert set(body["live_sources_used"]) == {"enrollments", "campus_rooms"}
    modes = {e["field"]: e["mode"] for e in body["evidence"]}
    assert modes["current_students"] == "live"
    assert modes["classroom_capacity"] == "live"
    assert body["safety_flags"]["provider_live_enabled"] is False


def test_scenarios_custom_and_negative_growth_named_deterministically() -> None:
    # F14: explicit scenarios (incl. negative) produce deterministic names/projections.
    resp = client.post(
        f"{BASE}/scenarios/capacity",
        headers=ADMIN_HEADERS,
        json={"current_students": 1000, "intake_growth_scenarios": [-50, 0, 50]},
    )
    assert resp.status_code == 200
    scenarios = {s["name"]: s for s in resp.json()["scenarios"]}
    assert scenarios["baseline"]["projection"]["projected_students"] == 1000
    assert scenarios["intake_plus_50pct"]["projection"]["projected_students"] == 1500
    assert scenarios["intake_plus_-50pct"]["projection"]["projected_students"] == 500


def test_decision_log_uses_read_permission_not_record() -> None:
    # F11: GET decisions is least-privilege — guarded by decision.read, distinct from decision.record.
    from app.modules.digital_twin import permissions as dt_perms

    assert dt_perms.DECISION_READ == "digital_twin.decision.read"
    assert dt_perms.DECISION_READ != dt_perms.DECISION_RECORD
    assert dt_perms.DECISION_READ in dt_perms.ALL_PERMISSIONS
