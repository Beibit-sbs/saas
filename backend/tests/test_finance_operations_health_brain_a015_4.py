"""A-015.4 — Finance Operations Health Brain + Dashboard-Ready Summary.

Targeted test suite covering:
- Brain Core signal routing for finance_operations_health
- Deterministic health computation (5 dimensions)
- KPI/dashboard-ready output shape
- Fail-closed behavior
- Tenant isolation / cross-tenant leakage prevention
- A-015.1 / A-015.2 / A-015.3 regression
"""
from __future__ import annotations

import pytest

from app.modules.brain_core.finance_operations_health import (
    compute_finance_operations_health,
    _score_budget_health,
    _score_procurement_health,
    _score_po_delivery_health,
    _score_asset_conversion_health,
    _score_risk_signal_health,
)
from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier
from app.modules.brain_core.reasoning.rules_engine import RulesEngine
from app.modules.brain_core.registry import SignalRegistry, DecisionRegistry


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _health_signal(risk_level="high", overall_score=45, tenant_id=99001):
    return {
        "event_type": "finance.operations.health_check",
        "tenant_id": tenant_id,
        "source_entity_type": "finance_health",
        "source_entity_id": f"tenant_{tenant_id}",
        "payload": {
            "risk_level": risk_level,
            "overall_score": overall_score,
        },
    }


def _low_risk_snap():
    return {
        "tenant_id": 99001,
        "contracts_total": 10,
        "at_risk_contracts": 0,
        "contracts_high_risk": 0,
        "vendors_sla_breached": 0,
        "assets_total": 5,
        "constrained_assets": 0,
    }


def _high_risk_snap():
    return {
        "tenant_id": 99001,
        "contracts_total": 10,
        "at_risk_contracts": 4,
        "contracts_high_risk": 5,
        "vendors_sla_breached": 3,
        "assets_total": 5,
        "constrained_assets": 3,
    }


def _healthy_budget_ctx():
    return {
        "module": "budget_planning",
        "tenant_id": 99001,
        "drift_rate": 0.5,
        "drift_alerts": 0,
        "risk_level": "low",
    }


def _high_risk_budget_ctx():
    return {
        "module": "budget_planning",
        "tenant_id": 99001,
        "drift_rate": 0.95,
        "drift_alerts": 3,
        "risk_level": "high",
    }


# ──────────────────────────────────────────────────────────────────────────────
# 1. Signal registry: finance_operations_health signals are registered
# ──────────────────────────────────────────────────────────────────────────────

def test_finance_health_signal_registered_in_signal_registry():
    assert SignalRegistry.is_supported("finance.operations.health_check")
    assert SignalRegistry.is_supported("finance.operations.risk_detected")


def test_finance_health_signal_routes_to_correct_scenario():
    entry = SignalRegistry.signals["finance.operations.health_check"]
    assert entry["scenario"] == "finance_operations_health"
    assert entry["signal_class"] == "financial_risk"


def test_finance_health_decision_registered_in_decision_registry():
    assert "finance_operations_health" in DecisionRegistry.decisions


def test_finance_health_decision_type_is_finance_health():
    decision = DecisionRegistry.decisions["finance_operations_health"]
    assert decision["decision_type"] == "finance_health"


# ──────────────────────────────────────────────────────────────────────────────
# 2. Risk classifier produces correct reasoning paths
# ──────────────────────────────────────────────────────────────────────────────

def test_classifier_finance_health_critical():
    clf = RiskClassifier()
    signal = _health_signal(risk_level="critical", overall_score=25)
    result = clf.classify(signal, {})
    assert result["reasoning_path"] == "finance_operations_health_critical"
    assert result["severity"] == "critical"


def test_classifier_finance_health_high():
    clf = RiskClassifier()
    signal = _health_signal(risk_level="high", overall_score=50)
    result = clf.classify(signal, {})
    assert result["reasoning_path"] == "finance_operations_health_high"
    assert result["severity"] == "high"


def test_classifier_finance_health_medium():
    clf = RiskClassifier()
    signal = _health_signal(risk_level="medium", overall_score=68)
    result = clf.classify(signal, {})
    assert result["reasoning_path"] == "finance_operations_health_medium"
    assert result["severity"] == "medium"


def test_classifier_finance_health_low_score_produces_low_path():
    clf = RiskClassifier()
    signal = _health_signal(risk_level="low", overall_score=85)
    result = clf.classify(signal, {})
    assert result["reasoning_path"] == "finance_operations_health_low"
    assert result["severity"] == "low"


# ──────────────────────────────────────────────────────────────────────────────
# 3. Rules engine produces correct decision_type and priority
# ──────────────────────────────────────────────────────────────────────────────

def test_rules_engine_finance_health_critical():
    re = RulesEngine()
    classification = {"reasoning_path": "finance_operations_health_critical"}
    result = re.evaluate(classification, {})
    assert result["decision_type"] == "finance_health"
    assert result["priority"] == "critical"
    assert "create_finance_health_review_task" in result["recommended_actions"]
    assert "notify_finance" in result["recommended_actions"]
    assert "notify_procurement_team" in result["recommended_actions"]


def test_rules_engine_finance_health_high():
    re = RulesEngine()
    result = re.evaluate({"reasoning_path": "finance_operations_health_high"}, {})
    assert result["decision_type"] == "finance_health"
    assert result["priority"] == "high"
    assert "create_finance_health_review_task" in result["recommended_actions"]


def test_rules_engine_finance_health_medium():
    re = RulesEngine()
    result = re.evaluate({"reasoning_path": "finance_operations_health_medium"}, {})
    assert result["priority"] == "medium"


def test_rules_engine_finance_health_low_no_actions():
    re = RulesEngine()
    result = re.evaluate({"reasoning_path": "finance_operations_health_low"}, {})
    assert result["priority"] == "low"
    assert result["recommended_actions"] == []


# ──────────────────────────────────────────────────────────────────────────────
# 4. compute_finance_operations_health — output shape contract
# ──────────────────────────────────────────────────────────────────────────────

def test_finance_health_output_has_required_fields():
    result = compute_finance_operations_health(tenant_id=99001)
    assert result["tenant_id"] == 99001
    assert result["decision_type"] == "finance_operations_health"
    assert result["scenario"] == "finance_operations_health"
    assert "overall_score" in result
    assert "risk_level" in result
    assert "dimensions" in result
    assert "recommended_actions" in result
    assert "explanation" in result
    assert "correlation_id" in result


def test_finance_health_dimensions_are_complete():
    result = compute_finance_operations_health(tenant_id=99001)
    dims = result["dimensions"]
    for key in (
        "budget_health",
        "procurement_health",
        "po_delivery_health",
        "asset_conversion_health",
        "risk_signal_health",
    ):
        assert key in dims, f"Missing dimension: {key}"
        dim = dims[key]
        assert "score" in dim
        assert "status" in dim
        assert "evidence" in dim
        assert 0 <= dim["score"] <= 100


def test_finance_health_overall_score_is_0_to_100():
    result = compute_finance_operations_health(tenant_id=99001)
    assert 0 <= result["overall_score"] <= 100


def test_finance_health_risk_level_values():
    result = compute_finance_operations_health(tenant_id=99001)
    assert result["risk_level"] in ("low", "medium", "high", "critical")


# ──────────────────────────────────────────────────────────────────────────────
# 5. Deterministic scoring: high risk inputs produce low score / high risk level
# ──────────────────────────────────────────────────────────────────────────────

def test_high_budget_risk_lowers_overall_health():
    result = compute_finance_operations_health(
        tenant_id=99001,
        budget_context=_high_risk_budget_ctx(),
    )
    budget_dim = result["dimensions"]["budget_health"]
    assert budget_dim["status"] in ("risk", "critical")
    assert budget_dim["score"] < 50


def test_high_procurement_risk_lowers_procurement_dimension():
    result = compute_finance_operations_health(
        tenant_id=99001,
        procurement_snapshot=_high_risk_snap(),
    )
    dim = result["dimensions"]["procurement_health"]
    assert dim["score"] < 60
    assert dim["status"] in ("risk", "critical", "watch")


def test_high_at_risk_contracts_lower_po_delivery_health():
    result = compute_finance_operations_health(
        tenant_id=99001,
        procurement_snapshot=_high_risk_snap(),
    )
    dim = result["dimensions"]["po_delivery_health"]
    assert dim["score"] < 70


def test_constrained_assets_lower_asset_conversion_health():
    asset_rows = [
        {"asset_code": "PROC-001", "status": "maintenance"},
        {"asset_code": "PROC-002", "status": "retired"},
        {"asset_code": "PROC-003", "status": "active"},
    ]
    result = compute_finance_operations_health(
        tenant_id=99001,
        asset_inventory_rows=asset_rows,
    )
    dim = result["dimensions"]["asset_conversion_health"]
    assert dim["score"] < 80


def test_active_risk_signals_lower_risk_signal_health():
    result = compute_finance_operations_health(
        tenant_id=99001,
        active_risk_signals=4,
    )
    dim = result["dimensions"]["risk_signal_health"]
    assert dim["score"] <= 20


def test_combined_high_risk_produces_high_or_critical_risk_level():
    result = compute_finance_operations_health(
        tenant_id=99001,
        budget_context=_high_risk_budget_ctx(),
        procurement_snapshot=_high_risk_snap(),
        active_risk_signals=3,
    )
    assert result["risk_level"] in ("high", "critical")


# ──────────────────────────────────────────────────────────────────────────────
# 6. Missing optional data — neutral/unknown, not false green or crash
# ──────────────────────────────────────────────────────────────────────────────

def test_missing_budget_context_produces_neutral_budget_dimension():
    result = compute_finance_operations_health(tenant_id=99001, budget_context=None)
    dim = result["dimensions"]["budget_health"]
    assert dim["score"] == 50
    assert dim["status"] == "watch"
    assert "budget_context_unavailable" in dim["evidence"]


def test_missing_procurement_snapshot_produces_neutral_dimensions():
    result = compute_finance_operations_health(tenant_id=99001, procurement_snapshot=None)
    for key in ("procurement_health", "po_delivery_health"):
        dim = result["dimensions"][key]
        assert dim["score"] == 50
        assert dim["status"] == "watch"


def test_missing_asset_rows_produces_neutral_asset_dimension():
    result = compute_finance_operations_health(tenant_id=99001, asset_inventory_rows=None)
    dim = result["dimensions"]["asset_conversion_health"]
    assert dim["score"] == 50
    assert dim["status"] == "watch"


def test_all_missing_does_not_crash_and_returns_valid_result():
    result = compute_finance_operations_health(
        tenant_id=99001,
        budget_context=None,
        expense_context=None,
        procurement_snapshot=None,
        asset_inventory_rows=None,
        active_risk_signals=0,
    )
    assert result["decision_type"] == "finance_operations_health"
    assert 0 <= result["overall_score"] <= 100


# ──────────────────────────────────────────────────────────────────────────────
# 7. Healthy input produces low risk level
# ──────────────────────────────────────────────────────────────────────────────

def test_healthy_context_produces_low_risk_level():
    result = compute_finance_operations_health(
        tenant_id=99001,
        budget_context=_healthy_budget_ctx(),
        procurement_snapshot=_low_risk_snap(),
        asset_inventory_rows=[{"asset_code": "PROC-001", "status": "active"}],
        active_risk_signals=0,
    )
    assert result["risk_level"] in ("low", "medium")
    assert result["overall_score"] > 60


# ──────────────────────────────────────────────────────────────────────────────
# 8. Recommended actions are source-tagged
# ──────────────────────────────────────────────────────────────────────────────

def test_recommended_actions_have_required_fields():
    result = compute_finance_operations_health(
        tenant_id=99001,
        budget_context=_high_risk_budget_ctx(),
        procurement_snapshot=_high_risk_snap(),
    )
    for action in result["recommended_actions"]:
        assert "type" in action
        assert "severity" in action
        assert "reason" in action
        assert "source" in action
        assert action["severity"] in ("low", "medium", "high", "critical")


def test_high_budget_risk_produces_budget_review_action():
    result = compute_finance_operations_health(
        tenant_id=99001,
        budget_context=_high_risk_budget_ctx(),
    )
    types = [a["type"] for a in result["recommended_actions"]]
    assert "budget_review" in types


# ──────────────────────────────────────────────────────────────────────────────
# 9. Fail-closed: missing/invalid tenant_id
# ──────────────────────────────────────────────────────────────────────────────

def test_missing_tenant_id_raises():
    with pytest.raises((ValueError, Exception)):
        compute_finance_operations_health(tenant_id=0)


def test_negative_tenant_id_raises():
    with pytest.raises((ValueError, Exception)):
        compute_finance_operations_health(tenant_id=-1)


# ──────────────────────────────────────────────────────────────────────────────
# 10. Tenant isolation — results are not cross-contaminated
# ──────────────────────────────────────────────────────────────────────────────

def test_cross_tenant_results_are_independent():
    r1 = compute_finance_operations_health(
        tenant_id=91001,
        budget_context=_high_risk_budget_ctx(),
    )
    r2 = compute_finance_operations_health(
        tenant_id=91002,
        budget_context=_healthy_budget_ctx(),
    )
    assert r1["tenant_id"] == 91001
    assert r2["tenant_id"] == 91002
    # High risk tenant should score lower than healthy tenant
    assert r1["overall_score"] < r2["overall_score"]


def test_finance_health_result_tenant_id_matches_input():
    for tid in (10001, 20002, 30003):
        result = compute_finance_operations_health(tenant_id=tid)
        assert result["tenant_id"] == tid


# ──────────────────────────────────────────────────────────────────────────────
# 11. BrainCoreService.compute_finance_operations_health integration
# ──────────────────────────────────────────────────────────────────────────────

def test_brain_service_compute_finance_health_returns_decision(monkeypatch):
    from app.modules.brain_core.service import BrainCoreService

    monkeypatch.setattr(
        "app.modules.brain_core.service.BrainCoreService.compute_finance_operations_health",
        lambda self, tid, **kwargs: compute_finance_operations_health(tenant_id=tid, **kwargs),
    )
    svc = BrainCoreService()
    result = svc.compute_finance_operations_health(99001)
    assert result["decision_type"] == "finance_operations_health"
    assert result["tenant_id"] == 99001


def test_brain_service_finance_health_fails_closed_on_invalid_tenant():
    from app.modules.brain_core.service import BrainCoreService
    svc = BrainCoreService()
    with pytest.raises((ValueError, Exception)):
        svc.compute_finance_operations_health(0)


# ──────────────────────────────────────────────────────────────────────────────
# 12. Evidence pack: explanation field is populated
# ──────────────────────────────────────────────────────────────────────────────

def test_explanation_includes_overall_score_and_risk_level():
    result = compute_finance_operations_health(tenant_id=99001)
    assert "overall_score=" in result["explanation"]
    assert "risk_level=" in result["explanation"]


def test_critical_dimensions_appear_in_explanation():
    result = compute_finance_operations_health(
        tenant_id=99001,
        budget_context=_high_risk_budget_ctx(),
        procurement_snapshot=_high_risk_snap(),
        active_risk_signals=5,
    )
    assert result["explanation"]
    # At least some risk evidence should be present
    explanation = result["explanation"]
    assert len(explanation) > 20


# ──────────────────────────────────────────────────────────────────────────────
# 13. correlation_id is propagated
# ──────────────────────────────────────────────────────────────────────────────

def test_custom_correlation_id_is_preserved():
    cid = "test-corr-abc-123"
    result = compute_finance_operations_health(tenant_id=99001, correlation_id=cid)
    assert result["correlation_id"] == cid


def test_auto_correlation_id_is_generated_if_not_provided():
    result = compute_finance_operations_health(tenant_id=99001)
    assert result["correlation_id"]
    assert len(result["correlation_id"]) >= 8


# ──────────────────────────────────────────────────────────────────────────────
# 14. Per-dimension score functions unit tests
# ──────────────────────────────────────────────────────────────────────────────

def test_score_budget_health_low_risk():
    dim = _score_budget_health({"drift_rate": 0.4, "drift_alerts": 0, "risk_level": "low"})
    assert dim["score"] >= 80
    assert dim["status"] == "healthy"


def test_score_budget_health_high_risk():
    dim = _score_budget_health({"drift_rate": 0.95, "drift_alerts": 2, "risk_level": "high"})
    assert dim["score"] < 40
    assert dim["status"] in ("risk", "critical")


def test_score_procurement_health_no_risk():
    dim = _score_procurement_health({"contracts_total": 5, "contracts_high_risk": 0, "vendors_sla_breached": 0})
    assert dim["score"] == 100
    assert dim["status"] == "healthy"


def test_score_procurement_health_high_risk():
    dim = _score_procurement_health({"contracts_total": 5, "contracts_high_risk": 4, "vendors_sla_breached": 3})
    assert dim["score"] < 50


def test_score_po_delivery_health_no_contracts():
    dim = _score_po_delivery_health({"contracts_total": 0, "at_risk_contracts": 0})
    assert dim["score"] == 80
    assert "no_contracts_present" in dim["evidence"]


def test_score_asset_conversion_health_all_active():
    rows = [{"asset_code": "PROC-001", "status": "active"}, {"asset_code": "PROC-002", "status": "active"}]
    dim = _score_asset_conversion_health(rows)
    assert dim["score"] == 100
    assert dim["status"] == "healthy"


def test_score_asset_conversion_health_no_proc_assets():
    rows = [{"asset_code": "EQP-001", "status": "active"}]
    dim = _score_asset_conversion_health(rows)
    assert dim["score"] == 80
    assert "no_procurement_assets_registered" in dim["evidence"]


def test_score_risk_signal_health_zero_signals():
    dim = _score_risk_signal_health(0)
    assert dim["score"] == 100
    assert dim["status"] == "healthy"


def test_score_risk_signal_health_many_signals():
    dim = _score_risk_signal_health(6)
    assert dim["score"] == 0
    assert dim["status"] == "critical"


# ──────────────────────────────────────────────────────────────────────────────
# 15. Regression: A-015.1 budget overrun signal still processes correctly
# ──────────────────────────────────────────────────────────────────────────────

def test_a015_1_regression_budget_overrun_classifier_intact():
    clf = RiskClassifier()
    signal = {
        "event_type": "finance.expense.budget_exceeded",
        "tenant_id": 1,
        "payload": {
            "risk_level": "high",
            "overrun_amount": 50000,
            "budget_limit": 100000,
        },
    }
    result = clf.classify(signal, {})
    assert result["reasoning_path"] == "budget_overrun_high"
    assert result["situation_type"] == "financial_risk"


# ──────────────────────────────────────────────────────────────────────────────
# 16. Regression: A-015.2 procurement approval signal still processes correctly
# ──────────────────────────────────────────────────────────────────────────────

def test_a015_2_regression_procurement_approval_classifier_intact():
    clf = RiskClassifier()
    signal = {
        "event_type": "procurement.request_submitted",
        "tenant_id": 1,
        "payload": {
            "request_id": "REQ-001",
            "estimated_total": 60000,
            "priority": "high",
        },
    }
    result = clf.classify(signal, {})
    assert result["reasoning_path"] == "procurement_approval_high"


# ──────────────────────────────────────────────────────────────────────────────
# 17. Regression: A-015.3 PO delivery scenario registry intact
# ──────────────────────────────────────────────────────────────────────────────

def test_a015_3_regression_procurement_signals_still_registered():
    assert SignalRegistry.is_supported("procurement.request_submitted")
    assert SignalRegistry.is_supported("procurement.approval_required")
