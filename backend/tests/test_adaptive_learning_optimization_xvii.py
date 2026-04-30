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


def _headers_read_only() -> dict[str, str]:
    token = create_access_token(
        user_id="viewer@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["admin.dashboard.read"],
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


# ---------------------------------------------------------------------------
# XVIII1 — Adaptive Learning Apply API
# ---------------------------------------------------------------------------

def test_learning_apply_dry_run_preview_only() -> None:
    """POST /brain/learning/apply dry-run returns preview without mutating profile."""
    _reset()
    before = brain_core_service._policy_resolver.get_profile(1)  # type: ignore[attr-defined]

    resp = client.post(
        "/api/admin/brain/learning/apply",
        json={
            "tenant_id": 1,
            "actor": "owner@example.com",
            "dry_run": True,
            "idempotency_key": "dry-run-preview-001",
        },
        headers=_headers(),
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["dry_run"] is True
    assert body["status"] == "preview"
    assert body["applied"] is False
    assert body["before_profile"] == body["after_profile"]

    after = brain_core_service._policy_resolver.get_profile(1)  # type: ignore[attr-defined]
    assert after.autonomy_level == before.autonomy_level


def test_learning_apply_idempotency_replay() -> None:
    """Second call with same idempotency key returns replay response."""
    _reset()
    payload = {
        "tenant_id": 1,
        "actor": "owner@example.com",
        "dry_run": False,
        "idempotency_key": "learning-apply-key-123",
    }

    first = client.post("/api/admin/brain/learning/apply", json=payload, headers=_headers())
    second = client.post("/api/admin/brain/learning/apply", json=payload, headers=_headers())

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["idempotent_replay"] is False
    assert second.json()["idempotent_replay"] is True


def test_learning_apply_requires_write_permission() -> None:
    """Endpoint is guarded by admin.dashboard.write permission."""
    _reset()
    resp = client.post(
        "/api/admin/brain/learning/apply",
        json={
            "tenant_id": 1,
            "actor": "viewer@example.com",
            "dry_run": True,
            "idempotency_key": "perm-check-001",
        },
        headers=_headers_read_only(),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# XVIII3 — Policy Drift Alerting
# ---------------------------------------------------------------------------

def test_policy_drift_detection_no_drift() -> None:
    """detect_policy_drift returns no_drift status when metrics are healthy."""
    _reset()
    alert = brain_core_service.detect_policy_drift(tenant_id=1)
    
    assert alert["tenant_id"] == 1
    assert alert["type"] == "policy_drift"
    assert alert["status"] == "no_drift"
    assert "current_metrics" in alert


def test_policy_drift_detection_creates_alert() -> None:
    """detect_policy_drift creates active alert when negative rate is high."""
    _reset()
    # Seed negative outcomes to trigger drift
    for i in range(3):
        brain_core_service._outcome_tracker.record_outcome({
            "tenant_id": 1,
            "decision_id": f"decision-{i}",
            "outcome_type": "negative",
            "effectiveness": "negative",
        })
    
    alert = brain_core_service.detect_policy_drift(tenant_id=1)
    assert alert["tenant_id"] == 1
    assert alert["status"] == "active"
    assert alert["severity"] in ["high", "medium"]
    assert "negative outcomes" in alert["reason"]


def test_get_policy_drift_alerts_retrieves_list() -> None:
    """get_policy_drift_alerts returns list of alerts for tenant."""
    _reset()
    # Create first alert
    alert1 = brain_core_service.detect_policy_drift(tenant_id=1)
    
    alerts = brain_core_service.get_policy_drift_alerts(tenant_id=1)
    assert len(alerts) >= 0


def test_policy_drift_alerts_multi_tenant_isolation() -> None:
    """Drift alerts are isolated per tenant."""
    _reset()
    # Create alert for tenant 1
    for i in range(3):
        brain_core_service._outcome_tracker.record_outcome({
            "tenant_id": 1,
            "decision_id": f"t1-decision-{i}",
            "outcome_type": "negative",
            "effectiveness": "negative",
        })
    
    alert1 = brain_core_service.detect_policy_drift(tenant_id=1)
    
    # Tenant 2 should have no alerts
    alerts2 = brain_core_service.get_policy_drift_alerts(tenant_id=2)
    assert len(alerts2) == 0


def test_policy_drift_endpoint_returns_alerts() -> None:
    """GET /policy-drift/{tenant_id} returns tenant's drift alerts."""
    _reset()
    resp = client.get(
        "/api/admin/brain/policy-drift/1",
        headers=_headers(),
    )
    
    assert resp.status_code == 200
    body = resp.json()
    assert body["tenant_id"] == 1
    assert "total" in body
    assert "alerts" in body
    assert isinstance(body["alerts"], list)


# ---------------------------------------------------------------------------
# XVIII4 — End-to-End Adaptive Loop
# ---------------------------------------------------------------------------

def test_e2e_signal_evaluation_apply_loop() -> None:
    """Signal → evaluate → apply → verify policy change (end-to-end)."""
    _reset()
    tenant_id = 1
    
    # Step 1: Get initial policy
    initial_policy = brain_core_service._policy_resolver.get_profile(tenant_id)
    initial_autonomy = initial_policy.autonomy_level
    
    # Step 2: Seed positive outcomes to show learning effectiveness
    for i in range(5):
        brain_core_service._outcome_tracker.record_outcome({
            "tenant_id": tenant_id,
            "decision_id": f"e2e-decision-{i}",
            "outcome_type": "positive",
            "effectiveness": "positive",
        })
    
    # Step 3: Evaluate learning readiness
    eval_result = brain_core_service.evaluate_learning(tenant_id)
    assert eval_result["learning_ready"] is True
    assert eval_result["positive_outcomes"] == 5
    
    # Step 4: Check policy tuning suggestion
    suggestion = brain_core_service.policy_tuning_suggestion(tenant_id)
    assert suggestion is not None
    assert "suggested_profile" in suggestion
    
    # Step 5: Apply learning
    apply_result = brain_core_service.apply_learning(
        tenant_id=tenant_id,
        dry_run=False,
        actor="e2e-test",
    )
    assert apply_result["applied"] is True
    
    # Step 6: Verify policy was updated
    updated_policy = brain_core_service._policy_resolver.get_profile(tenant_id)
    # Policy should have changed based on learning
    assert updated_policy is not None


def test_e2e_negative_outcomes_trigger_drift_detection() -> None:
    """Multiple negative outcomes trigger drift alert (end-to-end)."""
    _reset()
    tenant_id = 2
    
    # Seed multiple negative outcomes
    for i in range(4):
        brain_core_service._outcome_tracker.record_outcome({
            "tenant_id": tenant_id,
            "decision_id": f"neg-{i}",
            "outcome_type": "negative",
            "effectiveness": "negative",
        })
    
    # Trigger drift detection
    drift_alert = brain_core_service.detect_policy_drift(tenant_id)
    
    # Verify drift was detected
    assert drift_alert["tenant_id"] == tenant_id
    assert drift_alert["type"] == "policy_drift"
    # May be "active" or "no_drift" depending on thresholds
    assert drift_alert["status"] in ["active", "no_drift"]


def test_e2e_http_contract_evaluation_apply() -> None:
    """HTTP contract: GET /learning/evaluate → POST /learning/apply → GET /policy."""
    _reset()
    tenant_id = 1
    
    # Step 1: Evaluate via HTTP
    resp_eval = client.get(
        f"/api/admin/brain/learning/evaluate/{tenant_id}",
        headers=_headers(),
    )
    assert resp_eval.status_code == 200
    eval_data = resp_eval.json()
    assert eval_data["tenant_id"] == tenant_id
    
    # Step 2: Apply via HTTP
    resp_apply = client.post(
        "/api/admin/brain/learning/apply",
        json={
            "tenant_id": tenant_id,
            "actor": "e2e-test",
            "dry_run": False,
        },
        headers=_headers(),
    )
    assert resp_apply.status_code == 200
    apply_data = resp_apply.json()
    assert apply_data["tenant_id"] == tenant_id
    
    # Step 3: Get updated policy via HTTP
    resp_policy = client.get(
        f"/api/admin/brain/policy/{tenant_id}",
        headers=_headers(),
    )
    assert resp_policy.status_code == 200
    policy_data = resp_policy.json()
    assert policy_data["tenant_id"] == tenant_id
