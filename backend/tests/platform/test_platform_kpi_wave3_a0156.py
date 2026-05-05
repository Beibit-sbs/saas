"""A-015.6 Wave 3 KPI backend tests.

Covers:
- All Wave 3 metric keys are present after refresh_tenant_metrics()
- Correct event-derived computation for each domain group (budget, procurement, PO/asset, finance health, inventory/supply)
- Zero-value metrics do not crash (no events = 0 values)
- Severity rules defined for all thresholded Wave 3 metric keys
- Non-thresholded Wave 3 metrics return policy_pack=null
- METRIC_TITLES defined for all Wave 3 metric keys
- EVENT_DERIVED_METRIC_LINEAGE defined for all Wave 3 metric keys
- VALID_EVENT_TYPES includes all Wave 3 event types
"""
from __future__ import annotations

from uuid import uuid4

from tests.conftest import ADMIN_HEADERS, client

from app.modules.auth.token_service import create_access_token
from app.modules.tenants import service as module_tenant_service
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.event_ingestion.types import VALID_EVENT_TYPES
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork

# ─── Wave 3 metric key sets ───────────────────────────────────────────────────

WAVE3_BUDGET_KEYS = {
    "budget_overrun_risk_count",
    "budget_overrun_amount_at_risk",
    "budget_review_actions_count",
}

WAVE3_PROCUREMENT_KEYS = {
    "procurement_requests_pending_approval",
    "procurement_approval_automation_count",
    "procurement_po_issued_count",
}

WAVE3_PO_ASSET_KEYS = {
    "po_delivery_completion_rate",
    "delivered_po_asset_conversion_rate",
    "asset_conversion_gap_count",
}

WAVE3_FINANCE_HEALTH_KEYS = {
    "finance_operations_health_score",
    "budget_health_score",
    "procurement_health_score",
    "po_delivery_health_score",
    "asset_conversion_health_score",
    "active_finance_risk_signals_count",
    "finance_operations_actionability_count",
}

WAVE3_INVENTORY_KEYS = {
    "inventory_low_stock_items_count",
    "critical_supply_risk_count",
    "reorder_recommendations_count",
    "supply_risk_actions_count",
}

WAVE3_ALL_KEYS = (
    WAVE3_BUDGET_KEYS
    | WAVE3_PROCUREMENT_KEYS
    | WAVE3_PO_ASSET_KEYS
    | WAVE3_FINANCE_HEALTH_KEYS
    | WAVE3_INVENTORY_KEYS
)

# Thresholded: have KPI_SEVERITY_RULES entries
WAVE3_THRESHOLDED_KEYS = {
    "budget_overrun_risk_count",
    "budget_review_actions_count",
    "active_finance_risk_signals_count",
    "finance_operations_actionability_count",
    "asset_conversion_gap_count",
    "inventory_low_stock_items_count",
    "critical_supply_risk_count",
    "reorder_recommendations_count",
    "supply_risk_actions_count",
}

# Non-thresholded: no severity rules, policy_pack must be null
WAVE3_NON_THRESHOLDED_KEYS = WAVE3_ALL_KEYS - WAVE3_THRESHOLDED_KEYS

WAVE3_EVENT_TYPES = {
    "finance.expense.budget_exceeded",
    "campus.budget.overrun_risk_detected",
    "campus.expense_controls.budget_exceeded_risk_detected",
    "procurement.request_submitted",
    "procurement.approval_required",
    "procurement.po_issued",
    "procurement.asset_created",
    "finance.operations.health_check",
    "finance.operations.risk_detected",
    "inventory.low_stock.detected",
    "inventory.reorder_needed",
    "supply.risk.detected",
    "procurement.inventory_gap.detected",
}

# ─── helpers ─────────────────────────────────────────────────────────────────


def _create_tenant(prefix: str) -> int:
    slug = f"{prefix}-{uuid4().hex[:8]}"
    tenant = module_tenant_service.create_tenant({"slug": slug, "name": f"{prefix} Tenant"})
    return int(tenant["id"])


def _analytics_read_headers(*, tenant_id: int) -> dict[str, str]:
    token = create_access_token(
        user_id=f"kpi.viewer.{tenant_id}@example.com",
        roles=["student"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=["analytics.data.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def _emit_event(*, tenant_id: int, event_type: str, count: int = 1) -> None:
    for idx in range(count):
        event_ingestion_service.record_event(
            tenant_id=tenant_id,
            event_type=event_type,
            payload={"seq": idx + 1, "source": "test-a0156"},
        )


def _refresh_metrics(*, tenant_id: int) -> None:
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)


def _cards_by_key(body: dict) -> dict[str, dict]:
    return {str(item["key"]): item for item in body["kpis"]}


# ─── registration tests ───────────────────────────────────────────────────────


def test_wave3_metric_titles_defined_for_all_keys() -> None:
    """All Wave 3 metric keys must have display titles in METRIC_TITLES."""
    for key in WAVE3_ALL_KEYS:
        assert key in kpi_service.METRIC_TITLES, f"METRIC_TITLES missing entry for '{key}'"
        assert kpi_service.METRIC_TITLES[key], f"METRIC_TITLES['{key}'] must be non-empty"


def test_wave3_event_lineage_defined_for_all_keys() -> None:
    """All Wave 3 metric keys must have event lineage in EVENT_DERIVED_METRIC_LINEAGE."""
    for key in WAVE3_ALL_KEYS:
        assert key in kpi_service.EVENT_DERIVED_METRIC_LINEAGE, (
            f"EVENT_DERIVED_METRIC_LINEAGE missing entry for '{key}'"
        )
        assert len(kpi_service.EVENT_DERIVED_METRIC_LINEAGE[key]) > 0, (
            f"EVENT_DERIVED_METRIC_LINEAGE['{key}'] must list at least one event type"
        )


def test_wave3_event_types_in_valid_event_types() -> None:
    """All Wave 3 event types must be present in VALID_EVENT_TYPES."""
    for evt in WAVE3_EVENT_TYPES:
        assert evt in VALID_EVENT_TYPES, f"VALID_EVENT_TYPES missing '{evt}'"


def test_wave3_thresholded_keys_have_severity_rules() -> None:
    """All thresholded Wave 3 metric keys must have KPI_SEVERITY_RULES entries with required fields."""
    for key in WAVE3_THRESHOLDED_KEYS:
        assert key in kpi_service.KPI_SEVERITY_RULES, f"KPI_SEVERITY_RULES missing entry for '{key}'"
        rule = kpi_service.KPI_SEVERITY_RULES[key]
        assert "basis" in rule, f"KPI_SEVERITY_RULES['{key}'] must have 'basis'"
        assert "policy_pack" in rule, f"KPI_SEVERITY_RULES['{key}'] must have 'policy_pack'"
        assert "warning_gte" in rule, f"KPI_SEVERITY_RULES['{key}'] must have 'warning_gte'"
        assert "critical_gte" in rule, f"KPI_SEVERITY_RULES['{key}'] must have 'critical_gte'"


def test_wave3_non_thresholded_keys_absent_from_severity_rules() -> None:
    """Non-thresholded Wave 3 metric keys must not appear in KPI_SEVERITY_RULES."""
    for key in WAVE3_NON_THRESHOLDED_KEYS:
        assert key not in kpi_service.KPI_SEVERITY_RULES, (
            f"KPI_SEVERITY_RULES should NOT have an entry for non-thresholded metric '{key}'"
        )


# ─── zero-event baseline tests ────────────────────────────────────────────────


def test_wave3_all_keys_present_after_refresh_zero_events(reset_shared_state) -> None:
    """refresh_tenant_metrics() returns all Wave 3 keys even with no relevant events."""
    tenant_id = _create_tenant("a0156-zero")
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    keys = {item["key"] for item in response.json()["kpis"]}
    for k in WAVE3_ALL_KEYS:
        assert k in keys, f"KPI key '{k}' missing from /api/analytics/kpis response"


def test_wave3_non_thresholded_keys_policy_pack_null(reset_shared_state) -> None:
    """Non-thresholded Wave 3 metrics return policy_pack=null from the API."""
    tenant_id = _create_tenant("a0156-null-pack")
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    for key in WAVE3_NON_THRESHOLDED_KEYS:
        assert cards[key]["policy_pack"] is None, f"'{key}' expected policy_pack=null"


# ─── budget metrics ───────────────────────────────────────────────────────────


def test_wave3_budget_overrun_risk_increments_on_budget_exceeded_event(reset_shared_state) -> None:
    """budget_overrun_risk_count increases when finance.expense.budget_exceeded events are ingested."""
    tenant_id = _create_tenant("a0156-budget-overrun")
    _emit_event(tenant_id=tenant_id, event_type="finance.expense.budget_exceeded", count=3)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["budget_overrun_risk_count"]["value"]) >= 3


def test_wave3_budget_review_actions_count_on_overrun_risk_events(reset_shared_state) -> None:
    """budget_review_actions_count increases when campus.budget.overrun_risk_detected events arrive."""
    tenant_id = _create_tenant("a0156-budget-review")
    _emit_event(tenant_id=tenant_id, event_type="campus.budget.overrun_risk_detected", count=2)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["budget_review_actions_count"]["value"]) >= 2


def test_wave3_budget_overrun_risk_severity_warning(reset_shared_state) -> None:
    """budget_overrun_risk_count reaches warning severity when >= 1."""
    tenant_id = _create_tenant("a0156-budget-sev")
    _emit_event(tenant_id=tenant_id, event_type="finance.expense.budget_exceeded", count=1)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    card = cards["budget_overrun_risk_count"]
    assert card["severity"] in ("warning", "critical")
    assert card["policy_pack"] == "budget_risk_wave3_v1"


# ─── procurement metrics ──────────────────────────────────────────────────────


def test_wave3_procurement_pending_approval_on_submitted_events(reset_shared_state) -> None:
    """procurement_requests_pending_approval increases when procurement.request_submitted events arrive."""
    tenant_id = _create_tenant("a0156-proc-submit")
    _emit_event(tenant_id=tenant_id, event_type="procurement.request_submitted", count=4)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["procurement_requests_pending_approval"]["value"]) >= 4


def test_wave3_procurement_po_issued_count_on_po_issued_events(reset_shared_state) -> None:
    """procurement_po_issued_count increases when procurement.po_issued events arrive."""
    tenant_id = _create_tenant("a0156-po-issued")
    _emit_event(tenant_id=tenant_id, event_type="procurement.po_issued", count=5)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["procurement_po_issued_count"]["value"]) == 5


# ─── PO / delivery / asset metrics ───────────────────────────────────────────


def test_wave3_asset_conversion_gap_nonzero_when_po_without_asset(reset_shared_state) -> None:
    """asset_conversion_gap_count > 0 when POs issued but no assets created."""
    tenant_id = _create_tenant("a0156-asset-gap")
    _emit_event(tenant_id=tenant_id, event_type="procurement.po_issued", count=3)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["asset_conversion_gap_count"]["value"]) == 3


def test_wave3_asset_conversion_gap_zero_when_all_assets_created(reset_shared_state) -> None:
    """asset_conversion_gap_count == 0 when all POs result in asset creation."""
    tenant_id = _create_tenant("a0156-asset-nogap")
    _emit_event(tenant_id=tenant_id, event_type="procurement.po_issued", count=2)
    _emit_event(tenant_id=tenant_id, event_type="procurement.asset_created", count=2)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["asset_conversion_gap_count"]["value"]) == 0


def test_wave3_asset_conversion_gap_severity_warning(reset_shared_state) -> None:
    """asset_conversion_gap_count reaches warning severity when >= 1."""
    tenant_id = _create_tenant("a0156-gap-sev")
    _emit_event(tenant_id=tenant_id, event_type="procurement.po_issued", count=2)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    card = cards["asset_conversion_gap_count"]
    assert card["severity"] in ("warning", "critical")
    assert card["policy_pack"] == "asset_chain_wave3_v1"


# ─── finance operations health metrics ───────────────────────────────────────


def test_wave3_active_finance_risk_signals_on_risk_detected_events(reset_shared_state) -> None:
    """active_finance_risk_signals_count increases when finance.operations.risk_detected events arrive."""
    tenant_id = _create_tenant("a0156-fin-risk")
    _emit_event(tenant_id=tenant_id, event_type="finance.operations.risk_detected", count=3)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["active_finance_risk_signals_count"]["value"]) == 3


def test_wave3_finance_risk_signals_severity_warning(reset_shared_state) -> None:
    """active_finance_risk_signals_count reaches warning severity when >= 1."""
    tenant_id = _create_tenant("a0156-fin-sev")
    _emit_event(tenant_id=tenant_id, event_type="finance.operations.risk_detected", count=1)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    card = cards["active_finance_risk_signals_count"]
    assert card["severity"] in ("warning", "critical")
    assert card["policy_pack"] == "finance_risk_wave3_v1"


# ─── inventory / supply metrics ───────────────────────────────────────────────


def test_wave3_inventory_low_stock_on_low_stock_events(reset_shared_state) -> None:
    """inventory_low_stock_items_count increases when inventory.low_stock.detected events arrive."""
    tenant_id = _create_tenant("a0156-inv-low")
    _emit_event(tenant_id=tenant_id, event_type="inventory.low_stock.detected", count=5)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["inventory_low_stock_items_count"]["value"]) == 5


def test_wave3_critical_supply_risk_on_supply_risk_events(reset_shared_state) -> None:
    """critical_supply_risk_count increases when supply.risk.detected events arrive."""
    tenant_id = _create_tenant("a0156-supply-risk")
    _emit_event(tenant_id=tenant_id, event_type="supply.risk.detected", count=2)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["critical_supply_risk_count"]["value"]) >= 2


def test_wave3_supply_risk_severity_critical_at_high_count(reset_shared_state) -> None:
    """critical_supply_risk_count reaches critical severity when >= 3."""
    tenant_id = _create_tenant("a0156-supply-crit")
    _emit_event(tenant_id=tenant_id, event_type="supply.risk.detected", count=3)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    card = cards["critical_supply_risk_count"]
    assert card["severity"] == "critical"
    assert card["policy_pack"] == "supply_risk_wave3_v1"


def test_wave3_reorder_recommendations_on_reorder_needed_events(reset_shared_state) -> None:
    """reorder_recommendations_count increases when inventory.reorder_needed events arrive."""
    tenant_id = _create_tenant("a0156-reorder")
    _emit_event(tenant_id=tenant_id, event_type="inventory.reorder_needed", count=4)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["reorder_recommendations_count"]["value"]) == 4


def test_wave3_supply_risk_actions_on_multiple_sources(reset_shared_state) -> None:
    """supply_risk_actions_count aggregates supply.risk.detected and procurement.inventory_gap.detected events."""
    tenant_id = _create_tenant("a0156-supply-multi")
    _emit_event(tenant_id=tenant_id, event_type="supply.risk.detected", count=2)
    _emit_event(tenant_id=tenant_id, event_type="procurement.inventory_gap.detected", count=3)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["supply_risk_actions_count"]["value"]) == 5
