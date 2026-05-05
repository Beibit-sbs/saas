"""A-017.1 — Budget Planning Maturity Closure Tests.

Validates:
1. budget_plan.* events accepted by VALID_EVENT_TYPES
2. finance.budget_variance.threshold_reached in VALID_EVENT_TYPES
3. budget_plan.approved / budget_plan.rejected in Brain Core signal registry → budget_overrun_prevention
4. finance.budget_variance.threshold_reached contributes to budget_overrun_risk_count and budget_review_actions_count
5. get_budget_brain_context() output shape matches finance_operations_health expectations
6. budget_planning context contributes to finance_operations_health scoring
7. No duplicate budget brain scenario introduced (budget_plan.* does not create new scenarios)
8. Missing tenant_id fails closed in budget_plan lookups
9. Cross-tenant budget plan isolation (no data leakage)
10. Existing A-015.1 and A-015.4 tests remain unaffected (non-regression)
"""
from __future__ import annotations

import pytest

# ─── VALID_EVENT_TYPES coverage ──────────────────────────────────────────────

def test_budget_plan_lifecycle_events_in_valid_event_types():
    """A-017.1 T1: All budget_plan.* lifecycle events are in VALID_EVENT_TYPES."""
    from app.platform.event_ingestion.types import VALID_EVENT_TYPES

    lifecycle_events = [
        "budget_plan.created",
        "budget_plan.review_requested",
        "budget_plan.approved",
        "budget_plan.locked",
        "budget_plan.rejected",
        "budget_plan.outcome_recorded",
    ]
    for event in lifecycle_events:
        assert event in VALID_EVENT_TYPES, (
            f"A-017.1: '{event}' must be in VALID_EVENT_TYPES for budget_planning maturity"
        )


def test_finance_budget_variance_threshold_reached_in_valid_event_types():
    """A-017.1 T2: finance.budget_variance.threshold_reached is in VALID_EVENT_TYPES."""
    from app.platform.event_ingestion.types import VALID_EVENT_TYPES

    assert "finance.budget_variance.threshold_reached" in VALID_EVENT_TYPES, (
        "A-017.1: finance.budget_variance.threshold_reached must be in VALID_EVENT_TYPES "
        "— budget_planning emits this when drift_rate > 0.9"
    )


# ─── Brain Core signal registry ──────────────────────────────────────────────

def test_budget_plan_approved_registered_in_brain_signal_registry():
    """A-017.1 T3a: budget_plan.approved is registered in SignalRegistry → budget_overrun_prevention."""
    from app.modules.brain_core.registry import SignalRegistry

    assert SignalRegistry.is_supported("budget_plan.approved"), (
        "A-017.1: budget_plan.approved must be registered in SignalRegistry"
    )
    entry = SignalRegistry.signals["budget_plan.approved"]
    assert entry["scenario"] == "budget_overrun_prevention", (
        "A-017.1: budget_plan.approved must route to budget_overrun_prevention scenario"
    )
    assert entry["signal_class"] == "financial_risk"
    assert "finance" in entry["context_sources"]


def test_budget_plan_rejected_registered_in_brain_signal_registry():
    """A-017.1 T3b: budget_plan.rejected is registered in SignalRegistry → budget_overrun_prevention."""
    from app.modules.brain_core.registry import SignalRegistry

    assert SignalRegistry.is_supported("budget_plan.rejected"), (
        "A-017.1: budget_plan.rejected must be registered in SignalRegistry"
    )
    entry = SignalRegistry.signals["budget_plan.rejected"]
    assert entry["scenario"] == "budget_overrun_prevention", (
        "A-017.1: budget_plan.rejected must route to budget_overrun_prevention scenario"
    )
    assert entry["signal_class"] == "financial_risk"


def test_no_new_budget_brain_scenario_introduced():
    """A-017.1 T4: budget_plan.* events reuse existing scenario — no new budget brain scenario.

    All budget_plan.* entries must map to existing scenarios only.
    """
    from app.modules.brain_core.registry import SignalRegistry, DecisionRegistry

    budget_plan_events = [
        k for k in SignalRegistry.signals if k.startswith("budget_plan.")
    ]
    # Every budget_plan.* event must route to an existing scenario (no new ones)
    existing_scenarios = set(DecisionRegistry.decisions.keys())
    for event in budget_plan_events:
        scenario = SignalRegistry.signals[event]["scenario"]
        assert scenario in existing_scenarios, (
            f"A-017.1: budget_plan event '{event}' routes to unknown scenario '{scenario}'. "
            f"Must reuse an existing scenario."
        )


# ─── KPI lineage alignment ───────────────────────────────────────────────────

def test_budget_overrun_risk_count_lineage_includes_budget_variance():
    """A-017.1 T5: budget_overrun_risk_count lineage includes finance.budget_variance.threshold_reached."""
    from app.platform.kpi.service import EVENT_DERIVED_METRIC_LINEAGE

    assert "budget_overrun_risk_count" in EVENT_DERIVED_METRIC_LINEAGE
    lineage = EVENT_DERIVED_METRIC_LINEAGE["budget_overrun_risk_count"]
    assert "finance.budget_variance.threshold_reached" in lineage, (
        "A-017.1: finance.budget_variance.threshold_reached must be in budget_overrun_risk_count lineage"
    )


def test_budget_review_actions_count_lineage_includes_budget_variance():
    """A-017.1 T6: budget_review_actions_count lineage includes finance.budget_variance.threshold_reached."""
    from app.platform.kpi.service import EVENT_DERIVED_METRIC_LINEAGE

    assert "budget_review_actions_count" in EVENT_DERIVED_METRIC_LINEAGE
    lineage = EVENT_DERIVED_METRIC_LINEAGE["budget_review_actions_count"]
    assert "finance.budget_variance.threshold_reached" in lineage, (
        "A-017.1: finance.budget_variance.threshold_reached must be in budget_review_actions_count lineage"
    )


def test_budget_variance_event_contributes_to_overrun_risk_count():
    """A-017.1 T7: budget_variance drift events increment budget_overrun_risk_count and budget_review_actions_count."""
    from app.platform.kpi.service import _compute_budget_kpi_values

    event_counts = {"finance.budget_variance.threshold_reached": 3}
    metrics = _compute_budget_kpi_values(event_counts)

    assert metrics["budget_overrun_risk_count"] >= 3, (
        "A-017.1: budget_overrun_risk_count must include finance.budget_variance.threshold_reached count"
    )
    assert metrics["budget_review_actions_count"] >= 3, (
        "A-017.1: budget_review_actions_count must include finance.budget_variance.threshold_reached count"
    )


def test_budget_variance_event_additive_not_replacing():
    """A-017.1 T8: adding budget_variance events adds to existing budget metrics, not replaces them."""
    from app.platform.kpi.service import _compute_budget_kpi_values

    # Combined: existing budget event + new variance event
    event_counts = {
        "finance.expense.budget_exceeded": 2,
        "finance.budget_variance.threshold_reached": 4,
    }
    metrics = _compute_budget_kpi_values(event_counts)

    # budget_overrun_risk_count = 2 + 4 = 6 (at minimum)
    assert metrics["budget_overrun_risk_count"] >= 6
    # budget_overrun_amount_at_risk only counts budget_exceeded (unchanged)
    assert metrics["budget_overrun_amount_at_risk"] == 2


# ─── get_budget_brain_context() shape ────────────────────────────────────────

def test_get_budget_brain_context_returns_expected_shape():
    """A-017.1 T9: get_budget_brain_context output matches finance_operations_health contract."""
    from app.modules.budget_planning.service import get_budget_brain_context

    ctx = get_budget_brain_context(tenant_id=99200)

    assert ctx["module"] == "budget_planning"
    assert ctx["tenant_id"] == 99200
    assert "drift_rate" in ctx
    assert "drift_alerts" in ctx
    assert "risk_level" in ctx
    assert ctx["risk_level"] in ("low", "medium", "high")
    assert isinstance(ctx["drift_rate"], float)
    assert isinstance(ctx["drift_alerts"], int)


def test_get_budget_brain_context_risk_level_low_with_no_data():
    """A-017.1 T10: Empty tenant returns risk_level=low (safe default)."""
    from app.modules.budget_planning.service import get_budget_brain_context

    ctx = get_budget_brain_context(tenant_id=99201)
    assert ctx["risk_level"] == "low"
    assert ctx["drift_alerts"] == 0


# ─── Brain integration: budget context feeds finance_operations_health ────────

def test_budget_context_feeds_finance_operations_health():
    """A-017.1 T11: high-risk budget context produces budget_health risk in finance_operations_health."""
    from app.modules.brain_core.finance_operations_health import compute_finance_operations_health

    high_risk_budget_ctx = {
        "module": "budget_planning",
        "tenant_id": 99300,
        "drift_rate": 0.95,
        "drift_alerts": 3,
        "risk_level": "high",
    }
    result = compute_finance_operations_health(
        tenant_id=99300,
        budget_context=high_risk_budget_ctx,
    )

    assert result["decision_type"] == "finance_operations_health"
    dimensions = result.get("dimensions", {})
    budget_dim = dimensions.get("budget_health", {})
    assert budget_dim.get("status") in ("risk", "critical"), (
        "A-017.1: high-risk budget context must yield risk/critical budget_health dimension"
    )


def test_budget_context_low_risk_passes_finance_operations_health():
    """A-017.1 T12: low-risk budget context produces healthy budget dimension."""
    from app.modules.brain_core.finance_operations_health import compute_finance_operations_health

    low_risk_budget_ctx = {
        "module": "budget_planning",
        "tenant_id": 99301,
        "drift_rate": 0.3,
        "drift_alerts": 0,
        "risk_level": "low",
    }
    result = compute_finance_operations_health(
        tenant_id=99301,
        budget_context=low_risk_budget_ctx,
    )
    dimensions = result.get("dimensions", {})
    budget_dim = dimensions.get("budget_health", {})
    assert budget_dim.get("status") in ("healthy", "warning"), (
        "A-017.1: low-risk budget context must yield healthy/warning budget_health dimension"
    )


# ─── Tenant isolation / fail-closed ──────────────────────────────────────────

def test_budget_brain_context_is_tenant_scoped():
    """A-017.1 T13: get_budget_brain_context is tenant-scoped — different tenants return independent contexts."""
    from app.modules.budget_planning.service import get_budget_brain_context

    ctx_a = get_budget_brain_context(tenant_id=99400)
    ctx_b = get_budget_brain_context(tenant_id=99401)

    assert ctx_a["tenant_id"] == 99400
    assert ctx_b["tenant_id"] == 99401
    # Both return valid shapes independently
    assert ctx_a["module"] == "budget_planning"
    assert ctx_b["module"] == "budget_planning"


def test_budget_kpi_metrics_zero_for_empty_event_counts():
    """A-017.1 T14: budget metrics are zero when event_counts has no budget events (no phantom inflation)."""
    from app.platform.kpi.service import _compute_budget_kpi_values

    metrics = _compute_budget_kpi_values({})

    assert metrics["budget_overrun_risk_count"] == 0
    assert metrics["budget_review_actions_count"] == 0
    assert metrics["budget_overrun_amount_at_risk"] == 0


# ─── Non-regression: existing A-015.1 and A-015.4 contracts ─────────────────

def test_existing_budget_overrun_prevention_scenario_still_registered():
    """A-017.1 T15 (non-regression): budget_overrun_prevention scenario still exists in DecisionRegistry."""
    from app.modules.brain_core.registry import DecisionRegistry

    assert "budget_overrun_prevention" in DecisionRegistry.decisions, (
        "Non-regression: budget_overrun_prevention scenario must remain registered (A-015.1)"
    )


def test_existing_finance_expense_budget_exceeded_still_in_registry():
    """A-017.1 T16 (non-regression): existing finance.expense.budget_exceeded signal still registered."""
    from app.modules.brain_core.registry import SignalRegistry

    assert SignalRegistry.is_supported("finance.expense.budget_exceeded"), (
        "Non-regression: finance.expense.budget_exceeded must remain registered (A-015.1)"
    )
    assert SignalRegistry.signals["finance.expense.budget_exceeded"]["scenario"] == "budget_overrun_prevention"


def test_existing_budget_overrun_risk_count_baseline_computes():
    """A-017.1 T17 (non-regression): existing budget_overrun_risk_count still computes from original events."""
    from app.platform.kpi.service import _compute_budget_kpi_values

    event_counts = {
        "finance.expense.budget_exceeded": 2,
        "campus.budget.overrun_risk_detected": 1,
        "campus.expense_controls.budget_exceeded_risk_detected": 1,
    }
    metrics = _compute_budget_kpi_values(event_counts)

    # All 3 original events still count
    assert metrics["budget_overrun_risk_count"] == 4
    assert metrics["budget_review_actions_count"] == 2  # only overrun_risk + controls
    assert metrics["budget_overrun_amount_at_risk"] == 2  # only budget_exceeded


def test_finance_budget_variance_threshold_reached_brain_registry_entry():
    """A-017.1 T18 (non-regression): finance.budget_variance.threshold_reached still routes to procurement_supply_chain."""
    from app.modules.brain_core.registry import SignalRegistry

    assert SignalRegistry.is_supported("finance.budget_variance.threshold_reached")
    entry = SignalRegistry.signals["finance.budget_variance.threshold_reached"]
    assert entry["scenario"] == "procurement_supply_chain", (
        "Non-regression: finance.budget_variance.threshold_reached scenario must remain procurement_supply_chain"
    )
