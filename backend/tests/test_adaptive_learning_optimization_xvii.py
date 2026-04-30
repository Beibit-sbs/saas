"""Phase XVII — Adaptive Learning & Brain Optimization tests (XVII3 + XVII4).

Pattern: direct state seeding + service calls + HTTP contract checks.
"""
from __future__ import annotations

import pytest

from app.modules.auth.token_service import create_access_token
from app.modules.brain_core.service import brain_core_service
from app.modules.brain_core.reasoning.optimizer import BrainOptimizer
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
# XVII3 — Learning Evaluation
# ---------------------------------------------------------------------------

def test_evaluate_learning_empty_tenant() -> None:
    """evaluate_learning returns structured result for a tenant with no data."""
    _reset()
    result = brain_core_service.evaluate_learning(tenant_id=77)

    assert result["tenant_id"] == 77
    assert result["total_decisions"] == 0
    assert result["total_outcomes"] == 0
    assert result["effectiveness_score"] == 0.0
    assert result["policy_drift_detected"] is False
    assert result["learning_ready"] is False
    assert "evaluated_at" in result


def test_evaluate_learning_with_outcomes() -> None:
    """evaluate_learning detects learning readiness when outcomes are present."""
    _reset()
    # Seed 4 outcomes directly into the outcome tracker
    for i in range(4):
        brain_core_service._outcome_tracker._outcomes.append({  # type: ignore[attr-defined]
            "outcome_id": f"outcome-{i}",
            "tenant_id": 5,
            "decision_id": f"decision-{i}",
            "outcome_type": "completed",
            "effectiveness": "positive",
            "outcome_payload": {},
        })

    result = brain_core_service.evaluate_learning(tenant_id=5)
    assert result["total_outcomes"] == 4
    assert result["learning_ready"] is True


def test_evaluate_learning_endpoint() -> None:
    """GET /brain/learning/evaluate/{tenant_id} returns 200 with evaluation fields."""
    _reset()
    resp = client.get("/api/admin/brain/learning/evaluate/1", headers=_headers())
    assert resp.status_code == 200
    body = resp.json()
    assert body["tenant_id"] == 1
    assert "total_decisions" in body
    assert "effectiveness_score" in body
    assert "learning_ready" in body
    assert "evaluated_at" in body


# ---------------------------------------------------------------------------
# XVII4 — Brain Optimization Engine
# ---------------------------------------------------------------------------

def test_optimizer_no_signals() -> None:
    """Optimizer returns empty recommendations and score=1.0 for no signals."""
    optimizer = BrainOptimizer()
    result = optimizer.optimize(tenant_id=1, domain_signals=[])

    assert result["tenant_id"] == 1
    assert result["recommendations"] == []
    assert result["optimization_score"] == 1.0
    assert "generated_at" in result


def test_optimizer_breached_threshold() -> None:
    """Optimizer generates recommendation when signal exceeds threshold."""
    optimizer = BrainOptimizer()
    result = optimizer.optimize(
        tenant_id=1,
        domain_signals=[
            {"domain": "academic", "metric": "dropout_risk_count", "value": 12.0, "threshold": 5.0},
        ],
    )
    assert len(result["recommendations"]) == 1
    rec = result["recommendations"][0]
    assert rec["domain"] == "academic"
    assert rec["metric"] == "dropout_risk_count"
    assert rec["priority"] in ("critical", "high", "medium")
    assert rec["expected_improvement"] > 0.0
    assert "Increase advising capacity" in rec["recommended_action"]


def test_optimizer_sorts_by_priority() -> None:
    """Optimizer sorts recommendations critical > high > medium > low."""
    optimizer = BrainOptimizer()
    result = optimizer.optimize(
        tenant_id=2,
        domain_signals=[
            {"domain": "operations", "metric": "open_work_orders", "value": 30.0, "threshold": 10.0},
            {"domain": "finance", "metric": "overdue_payments", "value": 100.0, "threshold": 20.0},
            {"domain": "research", "metric": "expired_grants", "value": 3.0, "threshold": 1.0},
        ],
    )
    priorities = [r["priority"] for r in result["recommendations"]]
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    assert all(
        order[priorities[i]] <= order[priorities[i + 1]]
        for i in range(len(priorities) - 1)
    )


def test_optimizer_service_method() -> None:
    """BrainCoreService.optimize() delegates to BrainOptimizer correctly."""
    _reset()
    result = brain_core_service.optimize(
        tenant_id=3,
        domain_signals=[
            {"domain": "faculty", "metric": "overloaded_faculty", "value": 8.0, "threshold": 3.0},
        ],
    )
    assert result["tenant_id"] == 3
    assert len(result["recommendations"]) == 1
    assert result["recommendations"][0]["domain"] == "faculty"


def test_optimizer_endpoint_contract() -> None:
    """POST /brain/optimize returns 200 with recommendations list."""
    _reset()
    payload = {
        "tenant_id": 1,
        "domain_signals": [
            {"domain": "academic", "metric": "dropout_risk_count", "value": 15.0, "threshold": 5.0},
            {"domain": "finance", "metric": "overdue_tuition", "value": 50.0, "threshold": 10.0},
        ],
    }
    resp = client.post("/api/admin/brain/optimize", json=payload, headers=_headers())
    assert resp.status_code == 200
    body = resp.json()
    assert body["tenant_id"] == 1
    assert isinstance(body["recommendations"], list)
    assert len(body["recommendations"]) == 2
    assert "optimization_score" in body
    assert "generated_at" in body
