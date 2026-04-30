"""XVI4 — Executive Brain KPI Dashboard tests.

Pattern: direct state seeding (no process_signal to keep tests fast).
"""
from __future__ import annotations

from app.modules.auth.token_service import create_access_token
from app.modules.brain_core.service import brain_core_service
from app.modules.brain_core.reporting.kpi_dashboard import BrainKPIDashboard
from tests.conftest import client


def _headers() -> dict[str, str]:
    token = create_access_token(
        user_id="owner@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["admin.dashboard.read", "admin.dashboard.write"],
    )
    return {"Authorization": f"Bearer {token}"}


def _reset() -> None:
    brain_core_service.__init__()


# ---------------------------------------------------------------------------
# Unit tests — BrainKPIDashboard.generate()
# ---------------------------------------------------------------------------

def test_dashboard_empty_tenant() -> None:
    """Dashboard for a tenant with no data returns zero-value KPIs."""
    dashboard = BrainKPIDashboard()
    result = dashboard.generate(tenant_id=99, signals=[], decisions=[], outcomes=[])

    assert result["tenant_id"] == 99
    assert result["signal_volume"]["total"] == 0
    assert result["decision_quality"]["total"] == 0
    assert result["outcome_effectiveness"]["total"] == 0
    assert result["outcome_effectiveness"]["effectiveness_rate"] == 0.0
    assert result["brain_health"]["active"] is False
    assert result["brain_health"]["recommendation_trigger_eligible"] is False


def test_dashboard_signal_volume_counts() -> None:
    """Signal volume KPIs correctly count and rank event types."""
    signals = [
        {"tenant_id": 1, "event_type": "academic.attendance_risk.detected"},
        {"tenant_id": 1, "event_type": "academic.attendance_risk.detected"},
        {"tenant_id": 1, "event_type": "faculty.workload_overload.detected"},
        {"tenant_id": 2, "event_type": "academic.attendance_risk.detected"},  # different tenant, excluded
    ]
    dashboard = BrainKPIDashboard()
    result = dashboard.generate(tenant_id=1, signals=signals, decisions=[], outcomes=[])

    sv = result["signal_volume"]
    assert sv["total"] == 3
    assert sv["unique_event_types"] == 2
    assert sv["top_event_types"][0]["event_type"] == "academic.attendance_risk.detected"
    assert sv["top_event_types"][0]["count"] == 2
    assert result["brain_health"]["active"] is True


def test_dashboard_decision_quality_kpis() -> None:
    """Decision quality KPIs aggregate priority, type, and confidence correctly."""
    decisions = [
        {"tenant_id": 1, "priority": "high", "decision_type": "risk", "confidence_score": 0.9, "status": "dispatched"},
        {"tenant_id": 1, "priority": "medium", "decision_type": "preventive", "confidence_score": 0.7, "status": "completed"},
        {"tenant_id": 1, "priority": "critical", "decision_type": "risk", "confidence_score": 0.85, "status": "approval_pending"},
        {"tenant_id": 2, "priority": "high", "decision_type": "risk", "confidence_score": 0.5, "status": "dispatched"},  # excluded
    ]
    dashboard = BrainKPIDashboard()
    result = dashboard.generate(tenant_id=1, signals=[], decisions=decisions, outcomes=[])

    dq = result["decision_quality"]
    assert dq["total"] == 3
    assert dq["by_priority"]["high"] == 1
    assert dq["by_priority"]["critical"] == 1
    assert dq["by_type"]["risk"] == 2
    assert dq["by_type"]["preventive"] == 1
    assert abs(dq["avg_confidence_score"] - round((0.9 + 0.7 + 0.85) / 3, 4)) < 1e-4
    assert dq["dispatched"] == 1
    assert dq["approval_pending"] == 1
    assert dq["completed"] == 1
    # critical == 1 (< 2): trigger eligible condition not met
    assert result["brain_health"]["recommendation_trigger_eligible"] is False


def test_dashboard_outcome_effectiveness_rate() -> None:
    """Outcome effectiveness_rate = positive / total."""
    outcomes = [
        {"tenant_id": 1, "effectiveness": "positive"},
        {"tenant_id": 1, "effectiveness": "positive"},
        {"tenant_id": 1, "effectiveness": "neutral"},
        {"tenant_id": 1, "effectiveness": "negative"},
    ]
    dashboard = BrainKPIDashboard()
    result = dashboard.generate(tenant_id=1, signals=[], decisions=[], outcomes=outcomes)

    oe = result["outcome_effectiveness"]
    assert oe["total"] == 4
    assert oe["positive"] == 2
    assert oe["neutral"] == 1
    assert oe["negative"] == 1
    assert oe["effectiveness_rate"] == 0.5


def test_dashboard_service_method_and_endpoint_contract() -> None:
    """Service.get_kpi_dashboard() + GET /executive-kpi/{tenant_id} endpoint contract."""
    _reset()
    # Seed signals directly
    brain_core_service._signals = [
        {"tenant_id": 3, "event_type": "academic.attendance_risk.detected"},
        {"tenant_id": 3, "event_type": "academic.attendance_risk.detected"},
        {"tenant_id": 3, "event_type": "faculty.workload_overload.detected"},
    ]
    brain_core_service._decisions = [
        {"tenant_id": 3, "priority": "high", "decision_type": "risk", "confidence_score": 0.8, "status": "dispatched"},
    ]

    # Service method
    result = brain_core_service.get_kpi_dashboard(3)
    assert result["tenant_id"] == 3
    assert result["signal_volume"]["total"] == 3
    assert result["decision_quality"]["total"] == 1
    assert "brain_health" in result

    # HTTP endpoint
    resp = client.get("/api/admin/brain/executive-kpi/3", headers=_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert data["tenant_id"] == 3
    assert data["signal_volume"]["total"] == 3
    assert "decision_quality" in data
    assert "outcome_effectiveness" in data
    assert "brain_health" in data
