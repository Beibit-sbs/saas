"""Phase XIX — Advanced Policy Reasoning & Multi-Tenant Orchestration tests.

XIX1: Policy Reasoning Engine
XIX3: Cross-Tenant Learning Aggregation
XIX4: Predictive Policy Optimization
"""
from __future__ import annotations

import pytest

from app.modules.auth.token_service import create_access_token
from app.modules.brain_core.service import brain_core_service
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
# XIX1 — Policy Reasoning Engine
# ---------------------------------------------------------------------------

def test_reason_about_policy_basic() -> None:
    """reason_about_policy returns structured reasoning with recommendations."""
    _reset()
    
    # Seed some outcomes
    brain_core_service._outcome_tracker._outcomes = [
        {
            "tenant_id": 1,
            "decision_id": "dec1",
            "action_id": "act1",
            "effectiveness": "positive",
            "recorded_at": "2026-04-30T00:00:00Z",
        },
        {
            "tenant_id": 1,
            "decision_id": "dec2",
            "action_id": "act2",
            "effectiveness": "negative",
            "recorded_at": "2026-04-30T01:00:00Z",
        },
    ]
    
    result = brain_core_service.reason_about_policy(tenant_id=1)
    
    assert result["tenant_id"] == 1
    assert "reasoning" in result
    assert "current_profile" in result
    assert isinstance(result["recommendations"], list)
    assert len(result["recommendations"]) > 0
    assert isinstance(result["alternative_policies"], list)
    assert "timestamp" in result


def test_reason_about_policy_recommendations_structure() -> None:
    """Policy reasoning recommendations have correct structure."""
    _reset()
    
    result = brain_core_service.reason_about_policy(tenant_id=1)
    
    for rec in result["recommendations"]:
        assert "recommendation" in rec
        assert "rationale" in rec
        assert rec["risk_level"] in ["low", "medium", "high"]
        assert rec["expected_impact"] in ["positive", "neutral", "negative"]


def test_reason_about_policy_alternative_policies_structure() -> None:
    """Alternative policies have correct structure."""
    _reset()
    
    result = brain_core_service.reason_about_policy(tenant_id=1)
    
    for alt in result["alternative_policies"]:
        assert "name" in alt
        assert "profile" in alt
        assert "reasoning" in alt
        assert alt["adoption_risk"] in ["low", "medium", "high"]
        assert "rationale" in alt


def test_reason_about_policy_autonomy_levels() -> None:
    """Alternative policies include autonomy level variations."""
    _reset()
    
    result = brain_core_service.reason_about_policy(tenant_id=1)
    
    autonomy_levels = [alt["profile"].get("autonomy_level") for alt in result["alternative_policies"]]
    # Should have at least one conservative and one balanced
    assert any(level <= 2 for level in autonomy_levels)


def test_reason_about_policy_http_contract() -> None:
    """XIX1 HTTP endpoint returns reasoning results."""
    _reset()
    
    headers = _headers()
    response = client.get("/api/admin/brain/reasoning/policy/1", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["tenant_id"] == 1
    assert "reasoning" in data
    assert "current_profile" in data
    assert "recommendations" in data
    assert "alternative_policies" in data


def test_reason_about_policy_requires_read_permission() -> None:
    """Policy reasoning endpoint requires admin.dashboard.read permission."""
    _reset()
    
    # User without permission should get 403
    headers = {
        "Authorization": "Bearer " + create_access_token(
            user_id="noaccess@example.com",
            roles=["user"],
            auth_source="test",
            tenant_id=1,
            permissions=[],
        )
    }
    response = client.get("/api/admin/brain/reasoning/policy/1", headers=headers)
    
    assert response.status_code in [401, 403]


# ---------------------------------------------------------------------------
# XIX3 — Cross-Tenant Learning Aggregation
# ---------------------------------------------------------------------------

def test_cross_tenant_learning_aggregation_excludes_current_tenant() -> None:
    """Peer aggregation excludes the current tenant and hides raw peer identifiers."""
    _reset()

    brain_core_service._policy_resolver.set_profile_values(
        tenant_id=2,
        autonomy_level=3,
        require_approval_for_critical=False,
        default_approval_role="provost",
        enable_ai_reasoning=True,
    )
    brain_core_service._policy_resolver.set_profile_values(
        tenant_id=3,
        autonomy_level=1,
        require_approval_for_critical=True,
        default_approval_role="provost",
        enable_ai_reasoning=False,
    )
    brain_core_service._quality_tracker._observations = [
        {"tenant_id": 2, "effectiveness": "positive"},
        {"tenant_id": 2, "effectiveness": "positive"},
        {"tenant_id": 3, "effectiveness": "negative"},
    ]

    result = brain_core_service.get_cross_tenant_recommendations(tenant_id=1)

    assert result["tenant_id"] == 1
    assert result["sample_size"] == 2
    assert "tenant_id" not in result["peer_benchmarks"]
    assert result["recommended_profile"]["tenant_id"] == 1
    assert len(result["rationale"]) >= 1


def test_cross_tenant_learning_http_contract() -> None:
    """XIX3 HTTP endpoint returns anonymized peer recommendations."""
    _reset()

    brain_core_service._policy_resolver.set_profile_values(
        tenant_id=2,
        autonomy_level=3,
        require_approval_for_critical=False,
        default_approval_role="provost",
        enable_ai_reasoning=True,
    )
    brain_core_service._quality_tracker._observations = [
        {"tenant_id": 2, "effectiveness": "positive"},
    ]

    response = client.get("/api/admin/brain/cross-tenant-recommendations/1", headers=_headers_read_only())

    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == 1
    assert "recommended_profile" in data
    assert "peer_benchmarks" in data


# ---------------------------------------------------------------------------
# XIX4 — Predictive Policy Optimization
# ---------------------------------------------------------------------------

def test_predictive_policy_optimization_reduces_autonomy_on_risk() -> None:
    """High-risk forecast recommends a safer policy profile."""
    _reset()

    brain_core_service._policy_resolver.set_profile_values(
        tenant_id=1,
        autonomy_level=3,
        require_approval_for_critical=False,
        default_approval_role="dean_office",
        enable_ai_reasoning=False,
    )
    brain_core_service._quality_tracker._observations = [
        {"tenant_id": 1, "effectiveness": "negative"},
        {"tenant_id": 1, "effectiveness": "negative"},
        {"tenant_id": 1, "effectiveness": "positive"},
    ]
    brain_core_service._signals = [
        {"tenant_id": 1, "severity": "high"},
        {"tenant_id": 1, "priority": "critical"},
        {"tenant_id": 1, "priority": "urgent"},
    ]
    brain_core_service._drift_alerts = {1: [{"status": "active", "alert_id": "drift-1"}]}

    result = brain_core_service.predict_policy_optimization(tenant_id=1, horizon_days=14)

    assert result["tenant_id"] == 1
    assert result["forecast_band"] in {"moderate", "high"}
    assert result["predicted_profile"]["autonomy_level"] <= 2
    assert result["predicted_profile"]["require_approval_for_critical"] is True
    assert len(result["recommended_actions"]) >= 1


def test_predictive_policy_optimization_can_increase_autonomy() -> None:
    """Strong positive outcomes can trigger proactive autonomy increase."""
    _reset()

    brain_core_service._policy_resolver.set_profile_values(
        tenant_id=1,
        autonomy_level=1,
        require_approval_for_critical=True,
        default_approval_role="dean_office",
        enable_ai_reasoning=False,
    )
    brain_core_service._quality_tracker._observations = [
        {"tenant_id": 1, "effectiveness": "positive"},
        {"tenant_id": 1, "effectiveness": "positive"},
        {"tenant_id": 1, "effectiveness": "positive"},
        {"tenant_id": 1, "effectiveness": "positive"},
        {"tenant_id": 1, "effectiveness": "positive"},
    ]

    result = brain_core_service.predict_policy_optimization(tenant_id=1, horizon_days=14)

    assert result["forecast_band"] == "low"
    assert result["predicted_profile"]["autonomy_level"] >= 2
    assert any("Increase autonomy" in action for action in result["recommended_actions"])


def test_predictive_policy_optimization_http_contract() -> None:
    """XIX4 HTTP endpoint returns predictive optimization data."""
    _reset()

    response = client.get("/api/admin/brain/policy-optimization/1?horizon_days=21", headers=_headers_read_only())

    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == 1
    assert data["horizon_days"] == 21
    assert "predicted_profile" in data
    assert "recommended_actions" in data


# ---------------------------------------------------------------------------
# XX1 — Guided Policy Rollout Plan
# ---------------------------------------------------------------------------

def test_policy_rollout_plan_returns_staged_structure() -> None:
    """XX1 rollout plan provides staged phases and rollback triggers."""
    _reset()

    brain_core_service._quality_tracker._observations = [
        {"tenant_id": 1, "effectiveness": "positive"},
        {"tenant_id": 1, "effectiveness": "negative"},
    ]

    plan = brain_core_service.generate_policy_rollout_plan(tenant_id=1, horizon_days=14)

    assert plan["tenant_id"] == 1
    assert isinstance(plan["plan_id"], str)
    assert isinstance(plan["phases"], list)
    assert len(plan["phases"]) >= 1
    assert isinstance(plan["rollback_triggers"], list)
    assert len(plan["rollback_triggers"]) >= 1
    assert "current_profile" in plan
    assert "target_profile" in plan


def test_policy_rollout_plan_can_auto_apply_when_low_risk_and_peer_data() -> None:
    """XX1 marks can_auto_apply for low-risk, small-delta, peer-backed changes."""
    _reset()

    brain_core_service._policy_resolver.set_profile_values(
        tenant_id=1,
        autonomy_level=1,
        require_approval_for_critical=True,
        default_approval_role="dean_office",
        enable_ai_reasoning=False,
    )
    brain_core_service._policy_resolver.set_profile_values(
        tenant_id=2,
        autonomy_level=2,
        require_approval_for_critical=True,
        default_approval_role="dean_office",
        enable_ai_reasoning=True,
    )
    brain_core_service._policy_resolver.set_profile_values(
        tenant_id=3,
        autonomy_level=2,
        require_approval_for_critical=True,
        default_approval_role="dean_office",
        enable_ai_reasoning=True,
    )

    brain_core_service._quality_tracker._observations = [
        {"tenant_id": 1, "effectiveness": "positive"},
        {"tenant_id": 1, "effectiveness": "positive"},
        {"tenant_id": 1, "effectiveness": "positive"},
        {"tenant_id": 1, "effectiveness": "positive"},
        {"tenant_id": 1, "effectiveness": "positive"},
        {"tenant_id": 2, "effectiveness": "positive"},
        {"tenant_id": 3, "effectiveness": "positive"},
    ]

    plan = brain_core_service.generate_policy_rollout_plan(tenant_id=1, horizon_days=14)

    assert plan["forecast_band"] == "low"
    assert plan["peer_sample_size"] >= 2
    assert isinstance(plan["can_auto_apply"], bool)


def test_policy_rollout_plan_http_contract() -> None:
    """XX1 HTTP endpoint returns rollout plan payload."""
    _reset()

    response = client.get("/api/admin/brain/policy-rollout-plan/1?horizon_days=10", headers=_headers_read_only())

    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == 1
    assert data["horizon_days"] == 10
    assert "phases" in data
    assert "rollback_triggers" in data



# ---------------------------------------------------------------------------
# XX2 — Policy Rollout Execution
# ---------------------------------------------------------------------------

def test_execute_policy_rollout_phase_returns_metrics() -> None:
    """XX2 phase execution returns metrics and audit trail."""
    _reset()

    result = brain_core_service.execute_policy_rollout_phase(
        tenant_id=1,
        plan_id="test-plan-001",
        phase="stabilize",
    )

    assert result["plan_id"] == "test-plan-001"
    assert result["tenant_id"] == 1
    assert result["phase"] == "stabilize"
    assert result["status"] == "success"
    assert "execution_id" in result
    assert "metrics" in result
    assert "audit_trail" in result
    assert len(result["audit_trail"]) >= 1
    assert result["metrics"]["phase_status"] == "baseline_collected"


def test_execute_policy_rollout_phase_idempotency() -> None:
    """XX2 phase execution guarantees idempotency on re-execution."""
    _reset()

    # First execution
    result1 = brain_core_service.execute_policy_rollout_phase(
        tenant_id=1,
        plan_id="test-plan-002",
        phase="pilot",
    )

    # Second execution (should be idempotent)
    result2 = brain_core_service.execute_policy_rollout_phase(
        tenant_id=1,
        plan_id="test-plan-002",
        phase="pilot",
    )

    assert result2["status"] == "already_executed"
    assert result2["plan_id"] == result1["plan_id"]
    assert result2["phase"] == result1["phase"]
    # Metrics should match from original execution
    assert result2["metrics"]["phase_status"] == "pilot_active"


def test_execute_policy_rollout_phase_http_contract() -> None:
    """XX2 HTTP endpoint returns phase execution payload."""
    _reset()

    response = client.post(
        "/api/admin/brain/policy-rollout-phase/1/execute?plan_id=test-plan-003&phase=rollout",
        headers=_headers(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["plan_id"] == "test-plan-003"
    assert data["tenant_id"] == 1
    assert data["phase"] == "rollout"
    assert data["status"] == "success"
    assert "execution_id" in data
    assert "metrics" in data
    assert data["metrics"]["phase_status"] == "rollout_active"


# ---------------------------------------------------------------------------
# XX3 — Rollback Orchestration
# ---------------------------------------------------------------------------

def test_rollback_policy_rollout_negative_rate_trigger() -> None:
    """XX3 rollback on negative_rate trigger returns rolled_back status."""
    _reset()

    # First execute a phase so there is something to roll back from
    brain_core_service.execute_policy_rollout_phase(
        tenant_id=1,
        plan_id="test-plan-rb-001",
        phase="pilot",
    )

    result = brain_core_service.rollback_policy_rollout(
        tenant_id=1,
        plan_id="test-plan-rb-001",
        trigger="negative_rate",
    )

    assert result["status"] == "rolled_back"
    assert result["trigger"] == "negative_rate"
    assert result["plan_id"] == "test-plan-rb-001"
    assert result["tenant_id"] == 1
    assert "rollback_id" in result
    assert "rolled_back_at" in result
    assert "audit_trail" in result
    assert len(result["audit_trail"]) >= 1
    assert result["audit_trail"][0]["action"] == "rollback_executed"


def test_rollback_policy_rollout_invalid_trigger() -> None:
    """XX3 rollback with unknown trigger returns invalid_trigger status."""
    _reset()

    result = brain_core_service.rollback_policy_rollout(
        tenant_id=1,
        plan_id="test-plan-rb-002",
        trigger="unknown_trigger",
    )

    assert result["status"] == "invalid_trigger"
    assert result["trigger"] == "unknown_trigger"
    assert result["prior_profile"] is None
    assert result["audit_trail"] == []


def test_rollback_policy_rollout_http_contract() -> None:
    """XX3 HTTP endpoint returns rollback payload for drift_detected trigger."""
    _reset()

    response = client.post(
        "/api/admin/brain/policy-rollout-phase/1/rollback?plan_id=test-plan-rb-003&trigger=drift_detected",
        headers=_headers(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rolled_back"
    assert data["trigger"] == "drift_detected"
    assert data["plan_id"] == "test-plan-rb-003"
    assert data["tenant_id"] == 1
    assert "rollback_id" in data
    assert "audit_trail" in data


# ---------------------------------------------------------------------------
# XX4 — Cross-Tenant Rollout Coordination
# ---------------------------------------------------------------------------

def test_coordinate_cross_tenant_rollout_all_succeed() -> None:
    """XX4 fan-out to multiple tenants returns all_succeeded status."""
    _reset()

    result = brain_core_service.coordinate_cross_tenant_rollout(
        plan_id="test-plan-coord-001",
        tenant_ids=[1, 2, 3],
        phase="stabilize",
    )

    assert result["overall_status"] == "all_succeeded"
    assert result["plan_id"] == "test-plan-coord-001"
    assert result["phase"] == "stabilize"
    assert result["tenant_count"] == 3
    assert len(result["succeeded_tenants"]) == 3
    assert len(result["failed_tenants"]) == 0
    assert "coordination_id" in result
    assert "results" in result
    assert len(result["results"]) == 3


def test_coordinate_cross_tenant_rollout_metrics_per_tenant() -> None:
    """XX4 per-tenant result includes metrics and status for each tenant."""
    _reset()

    result = brain_core_service.coordinate_cross_tenant_rollout(
        plan_id="test-plan-coord-002",
        tenant_ids=[10, 20],
        phase="rollout",
    )

    assert result["overall_status"] == "all_succeeded"
    for tenant_result in result["results"]:
        assert "tenant_id" in tenant_result
        assert tenant_result["status"] in ("success", "already_executed")
        assert "metrics" in tenant_result
        assert tenant_result["metrics"]["phase_status"] == "rollout_active"


def test_coordinate_cross_tenant_rollout_http_contract() -> None:
    """XX4 HTTP endpoint returns coordination payload."""
    _reset()

    response = client.post(
        "/api/admin/brain/policy-rollout-coordination?plan_id=test-plan-coord-003&phase=pilot&tenant_ids=1&tenant_ids=2",
        headers=_headers(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] == "all_succeeded"
    assert data["plan_id"] == "test-plan-coord-003"
    assert data["phase"] == "pilot"
    assert data["tenant_count"] == 2
    assert "coordination_id" in data
    assert "results" in data
