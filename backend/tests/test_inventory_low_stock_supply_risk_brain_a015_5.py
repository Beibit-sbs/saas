"""A-015.5 — Inventory Low Stock / Supply Risk Brain.

Targeted test suite covering:
- Brain Core signal routing for inventory_low_stock
- Deterministic supply risk classification (4 risk levels)
- Fail-closed behavior (tenant_id, item_id required)
- Recommended actions output
- Missing optional context (vendor/budget) does not crash
- Tenant isolation
- A-015.1–A-015.4 regression
"""
from __future__ import annotations

import pytest

from app.modules.brain_core.inventory_low_stock_brain import (
    compute_inventory_supply_risk,
    classify_supply_risk,
    build_shortage_amount,
)
from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier
from app.modules.brain_core.reasoning.rules_engine import RulesEngine
from app.modules.brain_core.registry import SignalRegistry, DecisionRegistry


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _stock_signal(
    event_type: str = "inventory.low_stock.detected",
    tenant_id: int = 88001,
    current_quantity: float | None = 3.0,
    reorder_threshold: float | None = 10.0,
    risk_level: str | None = None,
    item_id: str = "ITEM-001",
) -> dict:
    payload: dict = {"item_id": item_id, "current_quantity": current_quantity}
    if reorder_threshold is not None:
        payload["reorder_threshold"] = reorder_threshold
    if risk_level:
        payload["risk_level"] = risk_level
    return {
        "event_type": event_type,
        "tenant_id": tenant_id,
        "source_entity_type": "inventory_item",
        "source_entity_id": item_id,
        "payload": payload,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 1. Signal registry: inventory_low_stock signals are registered
# ──────────────────────────────────────────────────────────────────────────────

def test_inventory_low_stock_detected_registered():
    assert SignalRegistry.is_supported("inventory.low_stock.detected")


def test_inventory_reorder_needed_registered():
    assert SignalRegistry.is_supported("inventory.reorder_needed")


def test_supply_risk_detected_registered():
    assert SignalRegistry.is_supported("supply.risk.detected")


def test_procurement_inventory_gap_detected_registered():
    assert SignalRegistry.is_supported("procurement.inventory_gap.detected")


def test_inventory_low_stock_signals_map_to_correct_scenario():
    for evt in (
        "inventory.low_stock.detected",
        "inventory.reorder_needed",
        "supply.risk.detected",
        "procurement.inventory_gap.detected",
    ):
        entry = SignalRegistry.signals[evt]
        assert entry["scenario"] == "inventory_low_stock", f"Wrong scenario for {evt}"
        assert entry["signal_class"] == "supply_risk", f"Wrong signal_class for {evt}"


def test_inventory_low_stock_decision_registered():
    assert "inventory_low_stock" in DecisionRegistry.decisions


def test_inventory_low_stock_decision_type_is_supply_risk():
    decision = DecisionRegistry.decisions["inventory_low_stock"]
    assert decision["decision_type"] == "supply_risk"


# ──────────────────────────────────────────────────────────────────────────────
# 2. Risk classifier: 4 paths for inventory low stock events
# ──────────────────────────────────────────────────────────────────────────────

def test_classifier_zero_stock_produces_critical():
    clf = RiskClassifier()
    signal = _stock_signal(current_quantity=0)
    result = clf.classify(signal, {})
    assert result["reasoning_path"] == "inventory_low_stock_critical"
    assert result["severity"] == "critical"


def test_classifier_negative_stock_produces_critical():
    clf = RiskClassifier()
    signal = _stock_signal(current_quantity=-5)
    result = clf.classify(signal, {})
    assert result["reasoning_path"] == "inventory_low_stock_critical"


def test_classifier_below_half_threshold_produces_high():
    clf = RiskClassifier()
    # 3 < 10 * 0.5 = 5 → high
    signal = _stock_signal(current_quantity=3.0, reorder_threshold=10.0)
    result = clf.classify(signal, {})
    assert result["reasoning_path"] == "inventory_low_stock_high"
    assert result["severity"] == "high"


def test_classifier_below_threshold_produces_medium():
    clf = RiskClassifier()
    # 6 < 10 but >= 5 → medium
    signal = _stock_signal(current_quantity=6.0, reorder_threshold=10.0)
    result = clf.classify(signal, {})
    assert result["reasoning_path"] == "inventory_low_stock_medium"
    assert result["severity"] == "medium"


def test_classifier_at_or_above_threshold_produces_low():
    clf = RiskClassifier()
    signal = _stock_signal(current_quantity=12.0, reorder_threshold=10.0)
    result = clf.classify(signal, {})
    assert result["reasoning_path"] == "inventory_low_stock_low"
    assert result["severity"] == "low"


def test_classifier_explicit_critical_risk_level_in_payload():
    clf = RiskClassifier()
    # Even if quantity is fine, explicit critical should override
    signal = _stock_signal(current_quantity=50.0, reorder_threshold=10.0, risk_level="critical")
    result = clf.classify(signal, {})
    assert result["reasoning_path"] == "inventory_low_stock_critical"


def test_classifier_all_four_event_types_produce_supply_risk():
    clf = RiskClassifier()
    for evt in (
        "inventory.low_stock.detected",
        "inventory.reorder_needed",
        "supply.risk.detected",
        "procurement.inventory_gap.detected",
    ):
        signal = _stock_signal(event_type=evt, current_quantity=3.0, reorder_threshold=10.0)
        result = clf.classify(signal, {})
        assert result["situation_type"] == "supply_risk", f"Wrong situation_type for {evt}"


# ──────────────────────────────────────────────────────────────────────────────
# 3. Rules engine: correct decision_type and priority
# ──────────────────────────────────────────────────────────────────────────────

def test_rules_engine_critical_stock():
    re = RulesEngine()
    result = re.evaluate({"reasoning_path": "inventory_low_stock_critical"}, {})
    assert result["decision_type"] == "supply_risk"
    assert result["priority"] == "critical"
    assert "create_procurement_request" in result["recommended_actions"]
    assert "vendor_followup" in result["recommended_actions"]
    assert "budget_review" in result["recommended_actions"]


def test_rules_engine_high_stock():
    re = RulesEngine()
    result = re.evaluate({"reasoning_path": "inventory_low_stock_high"}, {})
    assert result["decision_type"] == "supply_risk"
    assert result["priority"] == "high"
    assert "create_procurement_request" in result["recommended_actions"]


def test_rules_engine_medium_stock():
    re = RulesEngine()
    result = re.evaluate({"reasoning_path": "inventory_low_stock_medium"}, {})
    assert result["priority"] == "medium"
    assert "reorder_review" in result["recommended_actions"]


def test_rules_engine_low_stock_no_actions():
    re = RulesEngine()
    result = re.evaluate({"reasoning_path": "inventory_low_stock_low"}, {})
    assert result["priority"] == "low"
    assert result["recommended_actions"] == []


# ──────────────────────────────────────────────────────────────────────────────
# 4. compute_inventory_supply_risk — output shape contract
# ──────────────────────────────────────────────────────────────────────────────

def test_supply_risk_output_has_required_fields():
    result = compute_inventory_supply_risk(
        tenant_id=88001,
        item_id="ITEM-001",
        current_quantity=3.0,
        reorder_threshold=10.0,
    )
    assert result["tenant_id"] == 88001
    assert result["decision_type"] == "supply_risk"
    assert result["scenario"] == "inventory_low_stock"
    assert result["risk_level"] in ("low", "medium", "high", "critical")
    assert result["item_id"] == "ITEM-001"
    assert "current_quantity" in result
    assert "reorder_threshold" in result
    assert "shortage_amount" in result
    assert "recommended_actions" in result
    assert "evidence" in result
    assert "explanation" in result
    assert "correlation_id" in result


def test_shortage_amount_is_computed():
    result = compute_inventory_supply_risk(
        tenant_id=88001, item_id="ITEM-001", current_quantity=3.0, reorder_threshold=10.0
    )
    assert result["shortage_amount"] == pytest.approx(7.0)


def test_zero_stock_produces_critical():
    result = compute_inventory_supply_risk(
        tenant_id=88001, item_id="ITEM-001", current_quantity=0, reorder_threshold=10.0
    )
    assert result["risk_level"] == "critical"


def test_below_half_threshold_produces_high():
    result = compute_inventory_supply_risk(
        tenant_id=88001, item_id="ITEM-001", current_quantity=4.0, reorder_threshold=10.0
    )
    assert result["risk_level"] == "high"


def test_below_threshold_produces_medium():
    result = compute_inventory_supply_risk(
        tenant_id=88001, item_id="ITEM-001", current_quantity=7.0, reorder_threshold=10.0
    )
    assert result["risk_level"] == "medium"


def test_at_threshold_produces_low():
    result = compute_inventory_supply_risk(
        tenant_id=88001, item_id="ITEM-001", current_quantity=10.0, reorder_threshold=10.0
    )
    assert result["risk_level"] == "low"


def test_above_threshold_produces_low():
    result = compute_inventory_supply_risk(
        tenant_id=88001, item_id="ITEM-001", current_quantity=25.0, reorder_threshold=10.0
    )
    assert result["risk_level"] == "low"
    assert result["shortage_amount"] == 0.0


# ──────────────────────────────────────────────────────────────────────────────
# 5. Missing optional data — appears in evidence, not crash
# ──────────────────────────────────────────────────────────────────────────────

def test_missing_vendor_does_not_crash():
    result = compute_inventory_supply_risk(
        tenant_id=88001, item_id="ITEM-001", current_quantity=3.0, reorder_threshold=10.0,
        vendor_id=None,
    )
    assert result["risk_level"] in ("low", "medium", "high", "critical")
    evidence_str = " ".join(result["evidence"])
    assert "vendor_id" in evidence_str


def test_missing_budget_does_not_crash():
    result = compute_inventory_supply_risk(
        tenant_id=88001, item_id="ITEM-001", current_quantity=3.0, reorder_threshold=10.0,
        budget_id=None,
    )
    assert result["risk_level"] in ("low", "medium", "high", "critical")


def test_missing_quantity_produces_medium_risk():
    result = compute_inventory_supply_risk(
        tenant_id=88001, item_id="ITEM-001",
        current_quantity=None, reorder_threshold=None,
    )
    assert result["risk_level"] == "medium"
    evidence_str = " ".join(result["evidence"])
    assert "current_quantity" in evidence_str


def test_missing_threshold_produces_medium_risk():
    result = compute_inventory_supply_risk(
        tenant_id=88001, item_id="ITEM-001", current_quantity=5.0, reorder_threshold=None
    )
    assert result["risk_level"] == "medium"


def test_all_optional_missing_does_not_crash():
    result = compute_inventory_supply_risk(
        tenant_id=88001,
        item_id="ITEM-999",
        current_quantity=None,
        reorder_threshold=None,
        vendor_id=None,
        budget_id=None,
        department=None,
        location=None,
    )
    assert result["decision_type"] == "supply_risk"


# ──────────────────────────────────────────────────────────────────────────────
# 6. Fail-closed: invalid inputs raise
# ──────────────────────────────────────────────────────────────────────────────

def test_missing_tenant_id_raises():
    with pytest.raises((ValueError, Exception)):
        compute_inventory_supply_risk(tenant_id=0, item_id="ITEM-001")


def test_negative_tenant_id_raises():
    with pytest.raises((ValueError, Exception)):
        compute_inventory_supply_risk(tenant_id=-1, item_id="ITEM-001")


def test_missing_item_id_raises():
    with pytest.raises((ValueError, Exception)):
        compute_inventory_supply_risk(tenant_id=88001, item_id=None)


def test_empty_item_id_raises():
    with pytest.raises((ValueError, Exception)):
        compute_inventory_supply_risk(tenant_id=88001, item_id="")


# ──────────────────────────────────────────────────────────────────────────────
# 7. Recommended actions structure
# ──────────────────────────────────────────────────────────────────────────────

def test_critical_stock_has_procurement_request_action():
    result = compute_inventory_supply_risk(
        tenant_id=88001, item_id="ITEM-001", current_quantity=0, reorder_threshold=10.0
    )
    types = [a["type"] for a in result["recommended_actions"]]
    assert "create_procurement_request" in types


def test_actions_have_required_fields():
    result = compute_inventory_supply_risk(
        tenant_id=88001, item_id="ITEM-001", current_quantity=2.0, reorder_threshold=10.0
    )
    for action in result["recommended_actions"]:
        assert "type" in action
        assert "severity" in action
        assert "reason" in action
        assert "source" in action
        assert action["severity"] in ("low", "medium", "high", "critical")


def test_vendor_followup_action_requires_vendor_id():
    # With vendor_id → vendor_followup should be present for critical/high
    result_with_vendor = compute_inventory_supply_risk(
        tenant_id=88001, item_id="ITEM-001", current_quantity=0, reorder_threshold=10.0,
        vendor_id="VENDOR-A",
    )
    types_with = [a["type"] for a in result_with_vendor["recommended_actions"]]
    assert "vendor_followup" in types_with

    # Without vendor_id → no vendor_followup
    result_no_vendor = compute_inventory_supply_risk(
        tenant_id=88001, item_id="ITEM-001", current_quantity=0, reorder_threshold=10.0,
        vendor_id=None,
    )
    types_no = [a["type"] for a in result_no_vendor["recommended_actions"]]
    assert "vendor_followup" not in types_no


def test_budget_review_action_requires_budget_id_and_non_low():
    result = compute_inventory_supply_risk(
        tenant_id=88001, item_id="ITEM-001", current_quantity=0, reorder_threshold=10.0,
        budget_id="BUDGET-01",
    )
    types = [a["type"] for a in result["recommended_actions"]]
    assert "budget_review" in types


def test_low_risk_has_no_actions():
    result = compute_inventory_supply_risk(
        tenant_id=88001, item_id="ITEM-001", current_quantity=50.0, reorder_threshold=10.0
    )
    assert result["recommended_actions"] == []


# ──────────────────────────────────────────────────────────────────────────────
# 8. Evidence and explanation
# ──────────────────────────────────────────────────────────────────────────────

def test_explanation_contains_risk_level_and_item_id():
    result = compute_inventory_supply_risk(
        tenant_id=88001, item_id="ITEM-007", current_quantity=2.0, reorder_threshold=10.0
    )
    assert "risk_level=" in result["explanation"]
    assert "item_id=ITEM-007" in result["explanation"]


def test_evidence_contains_quantity_and_threshold():
    result = compute_inventory_supply_risk(
        tenant_id=88001, item_id="ITEM-001", current_quantity=4.0, reorder_threshold=10.0
    )
    evidence_str = " ".join(result["evidence"])
    assert "current_quantity=4" in evidence_str
    assert "reorder_threshold=10" in evidence_str


def test_custom_correlation_id_is_preserved():
    cid = "supply-corr-xyz-789"
    result = compute_inventory_supply_risk(
        tenant_id=88001, item_id="ITEM-001", correlation_id=cid
    )
    assert result["correlation_id"] == cid


def test_auto_correlation_id_generated():
    result = compute_inventory_supply_risk(tenant_id=88001, item_id="ITEM-001")
    assert result["correlation_id"]
    assert len(result["correlation_id"]) >= 8


# ──────────────────────────────────────────────────────────────────────────────
# 9. Tenant isolation
# ──────────────────────────────────────────────────────────────────────────────

def test_results_are_tenant_scoped():
    r1 = compute_inventory_supply_risk(
        tenant_id=81001, item_id="ITEM-A", current_quantity=0, reorder_threshold=10.0
    )
    r2 = compute_inventory_supply_risk(
        tenant_id=82002, item_id="ITEM-B", current_quantity=50.0, reorder_threshold=10.0
    )
    assert r1["tenant_id"] == 81001
    assert r2["tenant_id"] == 82002
    assert r1["risk_level"] == "critical"
    assert r2["risk_level"] == "low"


def test_tenant_id_in_result_matches_input():
    for tid in (10001, 20002, 30003):
        result = compute_inventory_supply_risk(tenant_id=tid, item_id="ITEM-001")
        assert result["tenant_id"] == tid


# ──────────────────────────────────────────────────────────────────────────────
# 10. BrainCoreService integration
# ──────────────────────────────────────────────────────────────────────────────

def test_brain_service_compute_supply_risk_returns_decision():
    from app.modules.brain_core.service import BrainCoreService
    svc = BrainCoreService()
    result = svc.compute_inventory_supply_risk(
        88001, item_id="ITEM-001", current_quantity=3.0, reorder_threshold=10.0
    )
    assert result["decision_type"] == "supply_risk"
    assert result["tenant_id"] == 88001


def test_brain_service_supply_risk_records_decision():
    from app.modules.brain_core.service import BrainCoreService
    svc = BrainCoreService()
    svc.compute_inventory_supply_risk(
        88001, item_id="ITEM-001", current_quantity=0, reorder_threshold=10.0
    )
    decisions = svc.list_decisions(88001)
    assert any(d.get("decision_type") == "supply_risk" for d in decisions)


def test_brain_service_supply_risk_fails_closed_no_tenant():
    from app.modules.brain_core.service import BrainCoreService
    svc = BrainCoreService()
    with pytest.raises((ValueError, Exception)):
        svc.compute_inventory_supply_risk(0, item_id="ITEM-001")


def test_brain_service_supply_risk_fails_closed_no_item_id():
    from app.modules.brain_core.service import BrainCoreService
    svc = BrainCoreService()
    with pytest.raises((ValueError, Exception)):
        svc.compute_inventory_supply_risk(88001, item_id=None)


# ──────────────────────────────────────────────────────────────────────────────
# 11. classify_supply_risk unit tests
# ──────────────────────────────────────────────────────────────────────────────

def test_classify_none_quantity_returns_medium():
    assert classify_supply_risk(None, 10) == "medium"


def test_classify_none_threshold_returns_medium():
    assert classify_supply_risk(5, None) == "medium"


def test_classify_both_none_returns_medium():
    assert classify_supply_risk(None, None) == "medium"


def test_classify_zero_quantity_returns_critical():
    assert classify_supply_risk(0, 10) == "critical"


def test_classify_negative_quantity_returns_critical():
    assert classify_supply_risk(-3, 10) == "critical"


def test_classify_below_half_threshold_returns_high():
    assert classify_supply_risk(4, 10) == "high"


def test_classify_at_half_threshold_edge():
    # qty == threshold*0.5 → NOT less than, so medium
    assert classify_supply_risk(5, 10) == "medium"


def test_classify_below_threshold_returns_medium():
    assert classify_supply_risk(7, 10) == "medium"


def test_classify_at_threshold_returns_low():
    assert classify_supply_risk(10, 10) == "low"


def test_classify_above_threshold_returns_low():
    assert classify_supply_risk(15, 10) == "low"


def test_build_shortage_amount_below_threshold():
    assert build_shortage_amount(3, 10) == pytest.approx(7.0)


def test_build_shortage_amount_at_threshold():
    assert build_shortage_amount(10, 10) == pytest.approx(0.0)


def test_build_shortage_amount_above_threshold():
    assert build_shortage_amount(15, 10) == pytest.approx(0.0)


def test_build_shortage_amount_none_inputs():
    assert build_shortage_amount(None, 10) == 0.0
    assert build_shortage_amount(3, None) == 0.0


# ──────────────────────────────────────────────────────────────────────────────
# 12. Regression: A-015.1 budget overrun classifier intact
# ──────────────────────────────────────────────────────────────────────────────

def test_a015_1_regression_budget_overrun_still_works():
    clf = RiskClassifier()
    signal = {
        "event_type": "finance.expense.budget_exceeded",
        "tenant_id": 1,
        "payload": {"risk_level": "high", "overrun_amount": 50000},
    }
    result = clf.classify(signal, {})
    assert result["reasoning_path"] == "budget_overrun_high"


# ──────────────────────────────────────────────────────────────────────────────
# 13. Regression: A-015.2 procurement approval intact
# ──────────────────────────────────────────────────────────────────────────────

def test_a015_2_regression_procurement_approval_intact():
    clf = RiskClassifier()
    signal = {
        "event_type": "procurement.request_submitted",
        "tenant_id": 1,
        "payload": {"estimated_total": 60000, "priority": "high"},
    }
    result = clf.classify(signal, {})
    assert result["reasoning_path"] == "procurement_approval_high"


# ──────────────────────────────────────────────────────────────────────────────
# 14. Regression: A-015.3 PO delivery scenario still registered
# ──────────────────────────────────────────────────────────────────────────────

def test_a015_3_regression_procurement_signals_still_registered():
    assert SignalRegistry.is_supported("procurement.request_submitted")
    assert SignalRegistry.is_supported("procurement.approval_required")


# ──────────────────────────────────────────────────────────────────────────────
# 15. Regression: A-015.4 finance ops health still works
# ──────────────────────────────────────────────────────────────────────────────

def test_a015_4_regression_finance_ops_health_still_registered():
    assert SignalRegistry.is_supported("finance.operations.health_check")
    assert SignalRegistry.is_supported("finance.operations.risk_detected")
    assert "finance_operations_health" in DecisionRegistry.decisions


def test_a015_4_regression_finance_ops_health_classifier_intact():
    clf = RiskClassifier()
    signal = {
        "event_type": "finance.operations.health_check",
        "tenant_id": 1,
        "payload": {"risk_level": "critical", "overall_score": 20},
    }
    result = clf.classify(signal, {})
    assert result["reasoning_path"] == "finance_operations_health_critical"
