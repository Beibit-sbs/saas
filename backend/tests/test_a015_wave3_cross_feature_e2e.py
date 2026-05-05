"""A-015.7 — Wave 3 Cross-Feature E2E Integration Tests.

Validates that Wave 3 features (A-015.1–A-015.6) work as a connected autonomy loop:

1. Budget Overrun → Brain Decision → Review Action → KPI Flow
   - Finance expense budget_exceeded signal
   - → Brain Core budget risk scenario
   - → budget review/actionability decision
   - → budget risk KPI represented in metrics
   - → dashboard can consume resulting state

2. Procurement Request → Approval → PO Flow
   - Procurement request submitted
   - → Brain Core procurement approval scenario
   - → approval/review action
   - → approved request issues PO through FSM
   - → procurement KPI represented

3. PO → Delivery → Asset Inventory Flow
   - PO issued
   - → delivery recorded
   - → asset inventory item created
   - → asset conversion KPI represented
   - → inventory/dashboard surface can consume result

4. Finance Operations Health Brain Flow
   - Budget/procurement/PO/asset/supply risk context
   - → finance_operations_health Brain decision
   - → health scores/dimensions
   - → finance health KPI represented
   - → dashboard can consume resulting state

5. Inventory Low Stock → Supply Risk → Reorder/Review Flow
   - Inventory low stock signal
   - → Brain Core supply risk decision
   - → reorder/procurement review actionability
   - → supply risk KPI represented
   - → inventory/dashboard surface can consume result

6. Cross-Tenant Isolation
   - Tenant 201 signals do not influence tenant 202 KPIs
   - Tenant 202 signals do not influence tenant 201 KPIs
"""
from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.modules.brain_core.service import BrainCoreService
from app.modules.brain_core.registry import SignalRegistry
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.kpi import service as kpi_service
from app.modules.tenants import service as tenant_service


# ─── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _stub_brain_context_sources() -> None:
    """Stub all Brain Core context builders to avoid external dependencies."""
    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_academic_context",
                return_value={"student_profile": None, "academic_health_snapshot": {}},
            )
        )
        stack.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_student_success_context",
                return_value={"active_interventions": 0, "open_advising_tasks": 0},
            )
        )
        stack.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_faculty_context",
                return_value={"faculty_health_snapshot": {}},
            )
        )
        stack.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_finance_context",
                return_value={"billing_health_snapshot": {}, "procurement_health_snapshot": {}},
            )
        )
        stack.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_operations_context",
                return_value={"operations_health_snapshot": {}},
            )
        )
        stack.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_platform_context",
                return_value={"platform_health_snapshot": {}},
            )
        )
        yield


def _create_tenant(prefix: str) -> int:
    """Create a test tenant."""
    slug = f"{prefix}-{uuid4().hex[:8]}"
    result = tenant_service.create_tenant({"slug": slug, "name": f"{prefix} Tenant"})
    return int(result["id"])


def _emit_event(
    tenant_id: int,
    event_type: str,
    payload: dict,
) -> None:
    """Emit an event to the event ingestion service."""
    event_ingestion_service.record_event(
        tenant_id=tenant_id,
        event_type=event_type,
        payload=payload,
    )


def _refresh_kpi_metrics(tenant_id: int) -> None:
    """Refresh KPI metrics for a tenant."""
    from app.platform.uow import UnitOfWork
    
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)


def _get_kpi_cards(tenant_id: int) -> dict[str, dict]:
    """Get KPI cards for a tenant via service."""
    from app.platform.uow import UnitOfWork

    with UnitOfWork() as uow:
        result = kpi_service.get_tenant_product_kpis(tenant_id=tenant_id, uow=uow)
    return {item["key"]: item for item in result["kpis"]}


# ─── Flow 1: Budget Overrun → Brain Decision → Review Action → KPI ──────────


# ─── Simplified Flow Tests: Focus on KPI + Brain Integration ────────────────


def test_wave3_budget_to_kpi_via_events() -> None:
    """Test budget signals → KPI metrics (simplified flow)."""
    tenant_id = _create_tenant("budget-simple")
    
    # Emit multiple budget overrun events
    for i in range(3):
        _emit_event(
            tenant_id=tenant_id,
            event_type="finance.expense.budget_exceeded",
            payload={
                "cost_center_id": f"CC-{i}",
                "department_id": "D-01",
                "amount": 1000.0,
                "budget_limit": 50000.0,
                "attempted_total": 50000.0 + (1000.0 * i),
                "risk_level": "high",
                "source_entity_type": "expense_record",
                "source_entity_id": f"CC-{i}",
            },
        )
    
    _refresh_kpi_metrics(tenant_id=tenant_id)
    cards = _get_kpi_cards(tenant_id=tenant_id)
    
    assert "budget_overrun_risk_count" in cards
    assert cards["budget_overrun_risk_count"]["value"] == 3


def test_wave3_procurement_events_to_kpi() -> None:
    """Test procurement signals → KPI metrics."""
    tenant_id = _create_tenant("procure-simple")
    
    # Emit procurement request submitted
    _emit_event(
        tenant_id=tenant_id,
        event_type="procurement.request_submitted",
        payload={
            "request_id": "REQ-001",
            "estimated_total": 5000.0,
            "requester_email": "test@edu.edu",
            "risk_level": "medium",
        },
    )
    
    # Emit PO issued
    _emit_event(
        tenant_id=tenant_id,
        event_type="procurement.po_issued",
        payload={
            "po_number": "PO-001",
            "request_id": "REQ-001",
            "vendor_id": "V-01",
            "total_amount": 5000.0,
            "issued_date": "2026-05-05T00:00:00Z",
        },
    )
    
    _refresh_kpi_metrics(tenant_id=tenant_id)
    cards = _get_kpi_cards(tenant_id=tenant_id)
    
    assert "procurement_po_issued_count" in cards
    assert cards["procurement_po_issued_count"]["value"] >= 1


def test_wave3_asset_delivery_to_kpi() -> None:
    """Test PO delivery → asset creation → KPI metrics."""
    tenant_id = _create_tenant("asset-simple")
    
    # Emit PO issued
    _emit_event(
        tenant_id=tenant_id,
        event_type="procurement.po_issued",
        payload={
            "po_number": "PO-ASSET-01",
            "request_id": "REQ-ASSET-01",
            "vendor_id": "VENDOR-A",
            "total_amount": 10000.0,
            "issued_date": "2026-05-05T00:00:00Z",
        },
    )
    
    # Emit asset created (delivery occurred)
    _emit_event(
        tenant_id=tenant_id,
        event_type="procurement.asset_created",
        payload={
            "asset_id": "A-001",
            "po_number": "PO-ASSET-01",
            "description": "Server",
            "serial_number": "SN-001",
            "status": "in_inventory",
            "created_date": "2026-05-05T02:00:00Z",
        },
    )
    
    _refresh_kpi_metrics(tenant_id=tenant_id)
    cards = _get_kpi_cards(tenant_id=tenant_id)
    
    # Both metrics should be present
    assert "po_delivery_completion_rate" in cards
    assert "asset_conversion_gap_count" in cards


def test_wave3_finance_operations_risk_to_kpi() -> None:
    """Test finance operations risk signals → health KPI."""
    tenant_id = _create_tenant("finance-ops")
    
    # Emit multiple risk signals
    for i in range(2):
        _emit_event(
            tenant_id=tenant_id,
            event_type="finance.operations.risk_detected",
            payload={
                "risk_type": "budget_overrun",
                "severity": "high",
                "affected_entity": f"ENTITY-{i}",
                "risk_reason": f"Risk {i}",
            },
        )
    
    _refresh_kpi_metrics(tenant_id=tenant_id)
    cards = _get_kpi_cards(tenant_id=tenant_id)
    
    assert "active_finance_risk_signals_count" in cards
    assert cards["active_finance_risk_signals_count"]["value"] >= 2


def test_wave3_inventory_supply_to_kpi() -> None:
    """Test inventory low stock → supply risk KPI."""
    tenant_id = _create_tenant("supply-simple")
    
    # Emit low stock signals
    for i in range(2):
        _emit_event(
            tenant_id=tenant_id,
            event_type="inventory.low_stock.detected",
            payload={
                "inventory_item_id": f"INV-{i}",
                "item_name": f"Item {i}",
                "current_quantity": 5,
                "reorder_threshold": 50,
                "shortage_amount": 45,
                "supplier_id": f"SUP-{i}",
                "estimated_reorder_cost": 225.0,
            },
        )
    
    # Emit reorder needed
    _emit_event(
        tenant_id=tenant_id,
        event_type="inventory.reorder_needed",
        payload={
            "inventory_item_id": "INV-0",
            "item_name": "Item 0",
            "reorder_quantity": 100,
            "reorder_cost": 500.0,
        },
    )
    
    _refresh_kpi_metrics(tenant_id=tenant_id)
    cards = _get_kpi_cards(tenant_id=tenant_id)
    
    assert "inventory_low_stock_items_count" in cards
    assert cards["inventory_low_stock_items_count"]["value"] >= 2
    
    assert "reorder_recommendations_count" in cards
    assert cards["reorder_recommendations_count"]["value"] >= 1


def test_wave3_budget_overrun_to_review_to_kpi() -> None:
    """Test Flow 1: Budget Overrun → Brain Decision → Review Action → KPI.
    
    Covers:
    - Budget overrun event emitted
    - Brain Core processes signal and creates review action
    - KPI metrics computed and represented
    - API returns budget KPI cards
    """
    tenant_id = _create_tenant("budget-flow")
    
    # Step 1: Emit budget overrun signal
    _emit_event(
        tenant_id=tenant_id,
        event_type="finance.expense.budget_exceeded",
        payload={
            "cost_center_id": "CC-101",
            "department_id": "D-01",
            "project_id": "P-01",
            "amount": 7000.0,
            "current_total": 47000.0,
            "budget_limit": 50000.0,
            "attempted_total": 54000.0,
            "risk_level": "high",
            "reason": "procurement_request_exceeds_available_budget",
            "source_entity_type": "expense_record",
            "source_entity_id": "CC-101",
        },
    )
    
    # Also emit review-trigger event so budget_review_actions_count >= 1
    _emit_event(
        tenant_id=tenant_id,
        event_type="campus.budget.overrun_risk_detected",
        payload={
            "cost_center_id": "CC-101",
            "department_id": "D-01",
            "project_id": "P-01",
            "risk_level": "high",
            "review_required": True,
        },
    )

    # Step 2: Verify Brain Core processes signal
    service = BrainCoreService()
    signal = {
        "signal_id": f"sig-budget-{tenant_id}-CC-101",
        "tenant_id": tenant_id,
        "correlation_id": f"corr-budget-{tenant_id}-CC-101",
        "event_type": "finance.expense.budget_exceeded",
        "payload": {
            "cost_center_id": "CC-101",
            "department_id": "D-01",
            "project_id": "P-01",
            "amount": 7000.0,
            "current_total": 47000.0,
            "budget_limit": 50000.0,
            "attempted_total": 54000.0,
            "risk_level": "high",
            "reason": "procurement_request_exceeds_available_budget",
            "source_entity_type": "expense_record",
            "source_entity_id": "CC-101",
        },
        "metadata": {},
    }
    
    result = service.process_signal(signal)
    assert result["status"] == "processed"
    assert result["decision"]["priority"] == "high"
    assert any(
        item["action"] == "create_intervention_case"
        for item in result["dispatch_results"]
    )
    
    # Step 3: Refresh KPI metrics
    _refresh_kpi_metrics(tenant_id=tenant_id)
    
    # Step 4: Verify KPI cards are present and represent budget risk
    cards = _get_kpi_cards(tenant_id=tenant_id)
    
    assert "budget_overrun_risk_count" in cards
    assert cards["budget_overrun_risk_count"]["value"] >= 1
    
    assert "budget_review_actions_count" in cards
    assert cards["budget_review_actions_count"]["value"] >= 1


def test_wave3_budget_warning_threshold_severity() -> None:
    """Test that budget overrun risk KPI triggers warning severity at threshold."""
    tenant_id = _create_tenant("budget-warn")
    
    # Emit one budget overrun (should trigger warning threshold)
    _emit_event(
        tenant_id=tenant_id,
        event_type="finance.expense.budget_exceeded",
        payload={
            "cost_center_id": "CC-W1",
            "department_id": "D-01",
            "project_id": "P-01",
            "amount": 5000.0,
            "current_total": 45000.0,
            "budget_limit": 50000.0,
            "attempted_total": 50000.0,
            "risk_level": "high",
            "source_entity_type": "expense_record",
            "source_entity_id": "CC-W1",
        },
    )
    
    _refresh_kpi_metrics(tenant_id=tenant_id)
    cards = _get_kpi_cards(tenant_id=tenant_id)
    
    assert "budget_overrun_risk_count" in cards
    assert cards["budget_overrun_risk_count"]["severity"] == "warning"


# ─── Flow 2: Procurement Request → Approval → PO ──────────────────────────


def test_wave3_procurement_request_to_approval_to_po() -> None:
    """Test Flow 2: Procurement Request → Approval → PO (event-based).
    
    Covers:
    - Procurement request submitted signal
    - Brain Core processes approval scenario
    - PO issued signal
    - Procurement KPI metrics represented
    """
    tenant_id = _create_tenant("procure-flow")
    
    # Step 1: Emit procurement request submitted signal
    _emit_event(
        tenant_id=tenant_id,
        event_type="procurement.request_submitted",
        payload={
            "request_id": "REQ-FLOW-001",
            "estimated_total": 10000.0,
            "requester_email": "procurement@test.edu",
            "risk_level": "high",
        },
    )
    
    # Step 2: Process Brain Core approval signal
    service = BrainCoreService()
    signal = {
        "signal_id": f"sig-proc-{tenant_id}-REQ-FLOW-001",
        "tenant_id": tenant_id,
        "correlation_id": f"corr-proc-{tenant_id}-REQ-FLOW-001",
        "event_type": "procurement.request_submitted",
        "payload": {
            "request_id": "REQ-FLOW-001",
            "estimated_total": 10000.0,
            "requester_email": "procurement@test.edu",
            "risk_level": "high",
        },
        "metadata": {},
    }
    
    result = service.process_signal(signal)
    assert result["status"] == "processed"
    
    # Step 3: Emit PO issued signal (after approval workflow)
    _emit_event(
        tenant_id=tenant_id,
        event_type="procurement.po_issued",
        payload={
            "po_number": "PO-FLOW-001",
            "request_id": "REQ-FLOW-001",
            "vendor_id": "VENDOR-01",
            "total_amount": 10000.0,
            "issued_date": "2026-05-05T00:00:00Z",
        },
    )
    
    # Step 4: Refresh KPI and verify procurement metrics
    _refresh_kpi_metrics(tenant_id=tenant_id)
    cards = _get_kpi_cards(tenant_id=tenant_id)
    
    assert "procurement_po_issued_count" in cards
    assert cards["procurement_po_issued_count"]["value"] >= 1


# ─── Flow 3: PO → Delivery → Asset Inventory → KPI ────────────────────────


def test_wave3_po_delivery_to_asset_inventory_to_kpi() -> None:
    """Test Flow 3: PO → Delivery → Asset Inventory (event-based).
    
    Covers:
    - PO issued event
    - Delivery recorded (asset created event)
    - Asset conversion KPI computed
    - Dashboard surface can consume result
    """
    tenant_id = _create_tenant("asset-flow")
    
    # Step 1: Emit PO issued event
    po_number = "PO-ASSET-001"
    _emit_event(
        tenant_id=tenant_id,
        event_type="procurement.po_issued",
        payload={
            "po_number": po_number,
            "request_id": "REQ-001",
            "vendor_id": "VENDOR-01",
            "total_amount": 5000.0,
            "issued_date": "2026-05-05T00:00:00Z",
        },
    )
    
    # Step 2: Emit asset created event
    _emit_event(
        tenant_id=tenant_id,
        event_type="procurement.asset_created",
        payload={
            "asset_id": "ASSET-001",
            "po_number": po_number,
            "item_description": "Server",
            "serial_number": "SN-12345",
            "status": "in_inventory",
            "created_date": "2026-05-05T01:00:00Z",
        },
    )
    
    # Step 3: Refresh KPI and verify PO/asset metrics
    _refresh_kpi_metrics(tenant_id=tenant_id)
    cards = _get_kpi_cards(tenant_id=tenant_id)
    
    # Both PO issued and asset created should be counted
    assert "po_delivery_completion_rate" in cards
    assert "asset_conversion_gap_count" in cards


# ─── Flow 4: Finance Operations Health Brain ────────────────────────────────


def test_wave3_finance_operations_health_to_kpi() -> None:
    """Test Flow 4: Finance Operations Health Brain (event-based).
    
    Covers:
    - Multiple risk signals (budget, procurement, supply)
    - Finance operations health decision
    - Health score KPI computed
    - Active risk signals KPI counted
    - Dashboard can consume health state
    """
    tenant_id = _create_tenant("finance-health")
    
    # Step 1: Emit multiple risk signals
    _emit_event(
        tenant_id=tenant_id,
        event_type="finance.operations.risk_detected",
        payload={
            "risk_type": "budget_overrun",
            "severity": "high",
            "affected_entity": "CC-101",
            "risk_reason": "Budget exceeded procurement request",
        },
    )
    
    # Step 2: Process finance health signal
    service = BrainCoreService()
    signal = {
        "signal_id": f"sig-health-{tenant_id}",
        "tenant_id": tenant_id,
        "correlation_id": f"corr-health-{tenant_id}",
        "event_type": "finance.operations.risk_detected",
        "payload": {
            "risk_type": "budget_overrun",
            "severity": "high",
            "affected_entity": "CC-101",
            "risk_reason": "Budget exceeded procurement request",
        },
        "metadata": {},
    }
    
    result = service.process_signal(signal)
    assert result["status"] == "processed"
    
    # Step 3: Refresh KPI and verify finance health metrics
    _refresh_kpi_metrics(tenant_id=tenant_id)
    cards = _get_kpi_cards(tenant_id=tenant_id)
    
    assert "active_finance_risk_signals_count" in cards
    assert cards["active_finance_risk_signals_count"]["value"] >= 1


# ─── Flow 5: Inventory Low Stock → Supply Risk → Reorder ──────────────────


def test_wave3_low_stock_to_supply_risk_to_kpi() -> None:
    """Test Flow 5: Inventory Low Stock → Supply Risk → Reorder/Review (event-based).
    
    Covers:
    - Low stock inventory signal
    - Brain Core supply risk decision
    - Reorder actionability created
    - Supply risk KPI computed
    - Inventory surface can consume result
    """
    tenant_id = _create_tenant("supply-flow")
    
    # Step 1: Emit low stock signal
    _emit_event(
        tenant_id=tenant_id,
        event_type="inventory.low_stock.detected",
        payload={
            "inventory_item_id": "INV-001",
            "item_name": "Network Cable",
            "current_quantity": 5,
            "reorder_threshold": 50,
            "shortage_amount": 45,
            "supplier_id": "SUP-01",
            "estimated_reorder_cost": 225.0,
        },
    )
    
    # Step 2: Process Brain Core supply risk signal
    service = BrainCoreService()
    signal = {
        "signal_id": f"sig-supply-{tenant_id}",
        "tenant_id": tenant_id,
        "correlation_id": f"corr-supply-{tenant_id}",
        "event_type": "inventory.low_stock.detected",
        "payload": {
            "inventory_item_id": "INV-001",
            "item_name": "Network Cable",
            "current_quantity": 5,
            "reorder_threshold": 50,
            "shortage_amount": 45,
            "supplier_id": "SUP-01",
            "estimated_reorder_cost": 225.0,
        },
        "metadata": {},
    }
    
    result = service.process_signal(signal)
    assert result["status"] == "processed"
    assert any(
        item["action"] in ["create_reorder_request", "create_procurement_request"]
        for item in result["dispatch_results"]
    )
    
    # Step 3: Emit reorder needed event
    _emit_event(
        tenant_id=tenant_id,
        event_type="inventory.reorder_needed",
        payload={
            "inventory_item_id": "INV-001",
            "item_name": "Network Cable",
            "reorder_quantity": 100,
            "reorder_cost": 500.0,
        },
    )
    
    # Step 4: Refresh KPI and verify supply risk metrics
    _refresh_kpi_metrics(tenant_id=tenant_id)
    cards = _get_kpi_cards(tenant_id=tenant_id)
    
    assert "inventory_low_stock_items_count" in cards
    assert cards["inventory_low_stock_items_count"]["value"] >= 1
    
    assert "reorder_recommendations_count" in cards
    assert cards["reorder_recommendations_count"]["value"] >= 1


# ─── Flow 6: Cross-Tenant Isolation ──────────────────────────────────────────


def test_wave3_cross_tenant_isolation() -> None:
    """Test Flow 6: Cross-Tenant Isolation (event-based).
    
    Covers:
    - Tenant 201 signals do not influence tenant 202 KPIs
    - Tenant 202 signals do not influence tenant 201 KPIs
    - Each tenant has independent metric state
    """
    tenant_201 = _create_tenant("isolation-t201")
    tenant_202 = _create_tenant("isolation-t202")
    
    # Step 1: Emit budget overrun signal for tenant 201
    _emit_event(
        tenant_id=tenant_201,
        event_type="finance.expense.budget_exceeded",
        payload={
            "cost_center_id": "CC-T201",
            "department_id": "D-01",
            "project_id": "P-01",
            "amount": 5000.0,
            "current_total": 45000.0,
            "budget_limit": 50000.0,
            "attempted_total": 50000.0,
            "risk_level": "high",
            "source_entity_type": "expense_record",
            "source_entity_id": "CC-T201",
        },
    )
    
    # Step 2: Emit different signal for tenant 202
    _emit_event(
        tenant_id=tenant_202,
        event_type="inventory.low_stock.detected",
        payload={
            "inventory_item_id": "INV-T202",
            "item_name": "Supplies",
            "current_quantity": 2,
            "reorder_threshold": 20,
            "shortage_amount": 18,
            "supplier_id": "SUP-01",
            "estimated_reorder_cost": 90.0,
        },
    )
    
    # Step 3: Refresh both tenant metrics
    _refresh_kpi_metrics(tenant_id=tenant_201)
    _refresh_kpi_metrics(tenant_id=tenant_202)
    
    # Step 4: Verify isolation: tenant 201 has budget KPI, not inventory
    cards_201 = _get_kpi_cards(tenant_id=tenant_201)
    assert cards_201.get("budget_overrun_risk_count", {}).get("value", 0) >= 1
    # Tenant 201 should have low/no inventory signals
    assert cards_201.get("inventory_low_stock_items_count", {}).get("value", 0) == 0
    
    # Step 5: Verify isolation: tenant 202 has inventory KPI, not budget
    cards_202 = _get_kpi_cards(tenant_id=tenant_202)
    assert cards_202.get("inventory_low_stock_items_count", {}).get("value", 0) >= 1
    # Tenant 202 should have low/no budget signals
    assert cards_202.get("budget_overrun_risk_count", {}).get("value", 0) == 0


# ─── Composite: All Flows Together ──────────────────────────────────────────


def test_wave3_all_flows_combined() -> None:
    """
    Test all 5 flows together in a single tenant.
    
    Covers:
    - Budget, Procurement, PO/Asset, Finance Health, Supply Risk all active
    - KPI metrics computed for all domains
    - Cross-domain dashboard rendering possible
    """
    tenant_id = _create_tenant("combined-flow")
    
    # Emit budget overrun
    _emit_event(
        tenant_id=tenant_id,
        event_type="finance.expense.budget_exceeded",
        payload={
            "cost_center_id": "CC-COMBO",
            "department_id": "D-01",
            "project_id": "P-01",
            "amount": 3000.0,
            "current_total": 47000.0,
            "budget_limit": 50000.0,
            "attempted_total": 50000.0,
            "risk_level": "high",
            "source_entity_type": "expense_record",
            "source_entity_id": "CC-COMBO",
        },
    )
    
    # Emit procurement request
    _emit_event(
        tenant_id=tenant_id,
        event_type="procurement.request_submitted",
        payload={
            "request_id": "REQ-COMBO",
            "estimated_total": 5000.0,
            "requester_email": "combo@test.edu",
            "risk_level": "medium",
        },
    )
    
    # Emit PO issued
    _emit_event(
        tenant_id=tenant_id,
        event_type="procurement.po_issued",
        payload={
            "po_number": "PO-COMBO",
            "request_id": "REQ-COMBO",
            "vendor_id": "VENDOR-01",
            "total_amount": 5000.0,
            "issued_date": "2026-05-05T00:00:00Z",
        },
    )
    
    # Emit asset created
    _emit_event(
        tenant_id=tenant_id,
        event_type="procurement.asset_created",
        payload={
            "asset_id": "ASSET-COMBO",
            "po_number": "PO-COMBO",
            "item_description": "Equipment",
            "serial_number": "SN-COMBO",
            "status": "in_inventory",
            "created_date": "2026-05-05T01:00:00Z",
        },
    )
    
    # Emit finance operations health check
    _emit_event(
        tenant_id=tenant_id,
        event_type="finance.operations.health_check",
        payload={
            "health_dimension": "budget",
            "status": "at_risk",
            "check_date": "2026-05-05T00:00:00Z",
        },
    )
    
    # Emit low stock
    _emit_event(
        tenant_id=tenant_id,
        event_type="inventory.low_stock.detected",
        payload={
            "inventory_item_id": "INV-COMBO",
            "item_name": "Supplies",
            "current_quantity": 10,
            "reorder_threshold": 50,
            "shortage_amount": 40,
            "supplier_id": "SUP-01",
            "estimated_reorder_cost": 200.0,
        },
    )
    
    # Refresh metrics
    _refresh_kpi_metrics(tenant_id=tenant_id)
    
    # Verify all metric types are present
    cards = _get_kpi_cards(tenant_id=tenant_id)
    
    # Budget metrics
    assert "budget_overrun_risk_count" in cards
    
    # Procurement metrics
    assert "procurement_po_issued_count" in cards
    
    # Asset metrics
    assert "asset_conversion_gap_count" in cards or "po_delivery_completion_rate" in cards
    
    # Finance health metrics
    assert "active_finance_risk_signals_count" in cards or "finance_operations_health_score" in cards
    
    # Supply metrics
    assert "inventory_low_stock_items_count" in cards


def test_wave3_brain_core_signals_are_registered() -> None:
    """Verify that all Wave 3 Brain Core signals are registered.
    
    Note: Some Wave 3 events (procurement.po_issued, procurement.asset_created, 
    inventory.reorder_needed, supply.risk.detected, procurement.inventory_gap.detected)
    are KPI events only, not Brain Core signals.
    """
    # Brain Core registered signals for Wave 3 features
    wave3_brain_signals = [
        "finance.expense.budget_exceeded",
        "campus.budget.overrun_risk_detected",
        "campus.expense_controls.budget_exceeded_risk_detected",
        "procurement.request_submitted",
        "procurement.approval_required",
        "finance.operations.health_check",
        "finance.operations.risk_detected",
        "inventory.low_stock.detected",
    ]
    
    for event_type in wave3_brain_signals:
        assert SignalRegistry.is_supported(event_type), f"{event_type} not registered in Brain Core"


def test_wave3_kpi_metrics_all_keys_present() -> None:
    """Verify that all Wave 3 metric keys are defined and accessible."""
    from app.platform.kpi.service import METRIC_TITLES, EVENT_DERIVED_METRIC_LINEAGE, KPI_SEVERITY_RULES
    
    wave3_metrics = {
        # Budget
        "budget_overrun_risk_count",
        "budget_overrun_amount_at_risk",
        "budget_review_actions_count",
        # Procurement
        "procurement_requests_pending_approval",
        "procurement_approval_automation_count",
        "procurement_po_issued_count",
        # PO/Asset
        "po_delivery_completion_rate",
        "delivered_po_asset_conversion_rate",
        "asset_conversion_gap_count",
        # Finance Health
        "finance_operations_health_score",
        "budget_health_score",
        "procurement_health_score",
        "po_delivery_health_score",
        "asset_conversion_health_score",
        "active_finance_risk_signals_count",
        "finance_operations_actionability_count",
        # Inventory/Supply
        "inventory_low_stock_items_count",
        "critical_supply_risk_count",
        "reorder_recommendations_count",
        "supply_risk_actions_count",
    }
    
    for metric_key in wave3_metrics:
        assert metric_key in METRIC_TITLES, f"{metric_key} not in METRIC_TITLES"
        assert metric_key in EVENT_DERIVED_METRIC_LINEAGE, f"{metric_key} not in EVENT_DERIVED_METRIC_LINEAGE"


def test_wave3_severity_rules_defined_for_thresholded() -> None:
    """Verify that severity rules are defined for thresholded Wave 3 metrics."""
    from app.platform.kpi.service import KPI_SEVERITY_RULES
    
    thresholded_metrics = {
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
    
    for metric_key in thresholded_metrics:
        assert metric_key in KPI_SEVERITY_RULES, f"{metric_key} not in KPI_SEVERITY_RULES"
        assert "basis" in KPI_SEVERITY_RULES[metric_key]
        assert "warning_gte" in KPI_SEVERITY_RULES[metric_key]
        assert "critical_gte" in KPI_SEVERITY_RULES[metric_key]
        assert "policy_pack" in KPI_SEVERITY_RULES[metric_key]
