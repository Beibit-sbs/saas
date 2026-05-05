"""A-015.2 — Procurement Request → Approval → PO Automation: targeted tests.

Tests cover:
1. procurement.request_submitted is supported in Brain Core and mapped to procurement_approval_automation
2. High-value submitted request routes to approval action (create_procurement_approval_case)
3. Duplicate approval signal is deduplicated
4. Procurement risk origin and evidence are propagated to action payload
5. Missing tenant_id fails closed (missing_tenant_context)
6. Missing request_id and estimated_total fails closed (missing_procurement_request_context)
7. Cross-tenant isolation: signals for different tenants produce independent decisions
8. Low-risk procurement request does not create an approval case
9. submit_procurement_request emits procurement.request_submitted event
10. ensure_procurement_approval_action is idempotent (call twice → one approval step, one transition)
11. ensure_po_on_approved_request creates PO for approved request idempotently
12. Rejected request does not create a PO
"""
from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import pytest

from app.modules.brain_core.registry import SignalRegistry
from app.modules.brain_core.service import BrainCoreService
from app.modules.procurement.service import (
    create_procurement_request,
    submit_procurement_request,
    update_procurement_status,
    get_approval_steps,
    get_request_order,
    ensure_procurement_approval_action,
    ensure_po_on_approved_request,
    _requests_store,
    _orders_store,
    _approvals_store,
    _audit_store,
)
from app.modules.procurement.schemas import (
    ProcurementRequestCreateSchema,
    RequestItemCreateSchema,
    ProcurementStatusUpdateSchema,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _stub_context_sources():
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
        yield


@pytest.fixture(autouse=True)
def _clear_procurement_stores():
    """Isolate each test from cross-test state pollution in in-memory stores."""
    _requests_store.clear()
    _orders_store.clear()
    _approvals_store.clear()
    _audit_store.clear()
    yield
    _requests_store.clear()
    _orders_store.clear()
    _approvals_store.clear()
    _audit_store.clear()


def _proc_signal(
    *,
    tenant_id: int,
    request_id: str = "req-001",
    estimated_total: float = 75000.0,
    priority: str = "high",
    department_id: str = "DEPT-IT",
) -> dict:
    return {
        "signal_id": f"sig-proc-{tenant_id}-{request_id}",
        "tenant_id": tenant_id,
        "correlation_id": f"corr-proc-{tenant_id}-{request_id}",
        "event_type": "procurement.request_submitted",
        "payload": {
            "request_id": request_id,
            "department_id": department_id,
            "title": "Software licenses procurement",
            "estimated_total": estimated_total,
            "priority": priority,
            "status": "submitted",
            "source_entity_type": "procurement_request",
            "source_entity_id": request_id,
        },
        "metadata": {},
    }


# ---------------------------------------------------------------------------
# Test 1 — Signal registry coverage
# ---------------------------------------------------------------------------


def test_procurement_request_submitted_supported_and_mapped() -> None:
    assert SignalRegistry.is_supported("procurement.request_submitted"), (
        "procurement.request_submitted must be in SignalRegistry"
    )
    info = SignalRegistry.signals["procurement.request_submitted"]
    assert info["scenario"] == "procurement_approval_automation"
    assert info["signal_class"] == "procurement_risk"


# ---------------------------------------------------------------------------
# Test 2 — High-value request routes to approval action
# ---------------------------------------------------------------------------


def test_high_value_procurement_request_creates_approval_action() -> None:
    svc = BrainCoreService()
    result = svc.process_signal(_proc_signal(tenant_id=10, estimated_total=80000.0, priority="high"))

    assert result["status"] == "processed", result
    action_names = [a["name"] for a in result.get("action_plan", [])]
    assert "create_procurement_approval_case" in action_names, (
        f"Expected create_procurement_approval_case in action_plan, got: {action_names}"
    )


# ---------------------------------------------------------------------------
# Test 3 — Duplicate signal is deduplicated
# ---------------------------------------------------------------------------


def test_duplicate_procurement_approval_signal_is_deduplicated() -> None:
    svc = BrainCoreService()
    sig = _proc_signal(tenant_id=11, request_id="req-dedup-001")
    first = svc.process_signal(sig)
    second = svc.process_signal(sig)

    assert first["status"] == "processed", first
    assert second["status"] == "deduplicated", second


# ---------------------------------------------------------------------------
# Test 4 — Risk origin and evidence propagated to action payload
# ---------------------------------------------------------------------------


def test_procurement_risk_origin_and_evidence_in_action_payload() -> None:
    svc = BrainCoreService()
    result = svc.process_signal(
        _proc_signal(
            tenant_id=12,
            request_id="req-evidence-001",
            estimated_total=120000.0,
            priority="critical",
            department_id="DEPT-FINANCE",
        )
    )

    assert result["status"] == "processed", result
    approval_actions = [a for a in result.get("action_plan", []) if a["name"] == "create_procurement_approval_case"]
    assert approval_actions, "create_procurement_approval_case action must be present"
    action = approval_actions[0]
    p = action.get("payload", {})
    assert p.get("procurement_risk_origin") == "procurement.request_submitted"
    assert p.get("department_id") == "DEPT-FINANCE"
    assert float(p.get("estimated_total") or 0) == pytest.approx(120000.0)


# ---------------------------------------------------------------------------
# Test 5 — Missing tenant_id fails closed
# ---------------------------------------------------------------------------


def test_missing_tenant_fails_closed() -> None:
    svc = BrainCoreService()
    sig = _proc_signal(tenant_id=0, request_id="req-notenant")
    result = svc.process_signal(sig)
    assert result["status"] == "rejected"
    assert result["reason"] == "missing_tenant_context"


# ---------------------------------------------------------------------------
# Test 6 — Missing request_id and estimated_total fails closed
# ---------------------------------------------------------------------------


def test_missing_request_id_and_total_fails_closed() -> None:
    svc = BrainCoreService()
    sig = {
        "signal_id": "sig-missing-context",
        "tenant_id": 13,
        "event_type": "procurement.request_submitted",
        "payload": {
            # No request_id, no estimated_total
            "department_id": "DEPT-X",
            "status": "submitted",
        },
        "metadata": {},
    }
    result = svc.process_signal(sig)
    assert result["status"] == "rejected"
    assert result["reason"] == "missing_procurement_request_context"


# ---------------------------------------------------------------------------
# Test 7 — Cross-tenant isolation
# ---------------------------------------------------------------------------


def test_cross_tenant_isolation_for_procurement_approval() -> None:
    svc = BrainCoreService()
    r1 = svc.process_signal(_proc_signal(tenant_id=20, request_id="req-t20-001", estimated_total=90000.0))
    r2 = svc.process_signal(_proc_signal(tenant_id=21, request_id="req-t21-001", estimated_total=90000.0))

    assert r1["status"] == "processed", r1
    assert r2["status"] == "processed", r2
    # Each decision must carry independent tenant context
    assert r1["context"]["tenant_id"] != r2["context"]["tenant_id"], (
        "Cross-tenant signals must produce distinct context (tenant isolation)"
    )


# ---------------------------------------------------------------------------
# Test 8 — Low-risk request does not create approval case
# ---------------------------------------------------------------------------


def test_low_risk_procurement_request_does_not_create_approval_case() -> None:
    svc = BrainCoreService()
    result = svc.process_signal(
        _proc_signal(tenant_id=14, request_id="req-low-001", estimated_total=500.0, priority="low")
    )
    assert result["status"] == "processed", result
    action_names = [a["name"] for a in result.get("action_plan", [])]
    assert "create_procurement_approval_case" not in action_names, (
        f"Low-risk request should not create approval case, got: {action_names}"
    )


# ---------------------------------------------------------------------------
# Test 9 — submit_procurement_request emits procurement.request_submitted
# ---------------------------------------------------------------------------


def test_submit_procurement_request_emits_event() -> None:
    tenant_id = 30
    req = create_procurement_request(
        tenant_id,
        ProcurementRequestCreateSchema(
            department_id="DEPT-A",
            title="Test procurement",
            priority="medium",
            items=[RequestItemCreateSchema(description="Laptop", quantity=5, unit_price=1200.0)],
        ),
        actor="requester@test.com",
    )

    with patch("app.modules.procurement.service.EventPublisher") as mock_cls:
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub
        submit_procurement_request(tenant_id, req.request_id, "requester@test.com")

    event_types = [c.kwargs["event_type"] for c in mock_pub.publish_event.call_args_list]
    assert "procurement.request_submitted" in event_types, (
        f"Expected procurement.request_submitted to be emitted, got: {event_types}"
    )


# ---------------------------------------------------------------------------
# Test 10 — ensure_procurement_approval_action is idempotent
# ---------------------------------------------------------------------------


def test_ensure_procurement_approval_action_is_idempotent() -> None:
    tenant_id = 31
    req = create_procurement_request(
        tenant_id,
        ProcurementRequestCreateSchema(
            department_id="DEPT-B",
            title="Idempotency test",
            priority="high",
            items=[RequestItemCreateSchema(description="Server", quantity=2, unit_price=5000.0)],
        ),
        actor="mgr@test.com",
    )
    submit_procurement_request(tenant_id, req.request_id, "mgr@test.com")

    # Call twice
    r1 = ensure_procurement_approval_action(tenant_id, req.request_id, "mgr@test.com")
    r2 = ensure_procurement_approval_action(tenant_id, req.request_id, "mgr@test.com")

    assert r1["idempotent"] is False  # first call: actually performed
    assert r2["idempotent"] is True   # second call: already under_review

    # Status must be under_review
    from app.modules.procurement.service import get_procurement_request
    updated = get_procurement_request(tenant_id, req.request_id)
    assert updated is not None
    assert updated.status == "under_review"


# ---------------------------------------------------------------------------
# Test 11 — ensure_po_on_approved_request is idempotent
# ---------------------------------------------------------------------------


def test_ensure_po_on_approved_request_is_idempotent() -> None:
    tenant_id = 32
    req = create_procurement_request(
        tenant_id,
        ProcurementRequestCreateSchema(
            department_id="DEPT-C",
            title="PO idempotency test",
            priority="high",
            items=[RequestItemCreateSchema(description="Tablet", quantity=10, unit_price=800.0)],
        ),
        actor="buyer@test.com",
    )
    submit_procurement_request(tenant_id, req.request_id, "buyer@test.com")
    update_procurement_status(tenant_id, req.request_id, ProcurementStatusUpdateSchema(status="under_review"), "buyer@test.com")
    update_procurement_status(tenant_id, req.request_id, ProcurementStatusUpdateSchema(status="approved"), "approver@test.com")

    # Call twice
    po1 = ensure_po_on_approved_request(tenant_id, req.request_id, "buyer@test.com")
    po2 = ensure_po_on_approved_request(tenant_id, req.request_id, "buyer@test.com")

    assert po1 is not None, "First call should create PO"
    assert po2 is not None, "Second call should return existing PO"
    assert po1["order_id"] == po2["order_id"], "Both calls must return the same order_id (idempotent)"


# ---------------------------------------------------------------------------
# Test 12 — Rejected request does not create PO
# ---------------------------------------------------------------------------


def test_rejected_request_does_not_create_po() -> None:
    tenant_id = 33
    req = create_procurement_request(
        tenant_id,
        ProcurementRequestCreateSchema(
            department_id="DEPT-D",
            title="Rejected request",
            priority="medium",
            items=[RequestItemCreateSchema(description="Chair", quantity=50, unit_price=200.0)],
        ),
        actor="staff@test.com",
    )
    submit_procurement_request(tenant_id, req.request_id, "staff@test.com")
    update_procurement_status(tenant_id, req.request_id, ProcurementStatusUpdateSchema(status="under_review"), "staff@test.com")
    update_procurement_status(tenant_id, req.request_id, ProcurementStatusUpdateSchema(status="rejected"), "approver@test.com")

    # ensure_po_on_approved_request on a rejected request must return None / not create PO
    po = ensure_po_on_approved_request(tenant_id, req.request_id, "staff@test.com")
    assert po is None, "Rejected request must not create a PO"

    # No order should exist
    existing_order = get_request_order(tenant_id, req.request_id)
    assert existing_order is None, "No PO order should exist for a rejected request"
