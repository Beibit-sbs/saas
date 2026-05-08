"""A-018.6: Visitor Management + Security Operations readiness closure tests.

Tests that visitor_management and security_operations reach Level 4 maturity:
  - Visitor lifecycle FSM (REQUESTED → APPROVED/REJECTED → CHECKED_IN → CHECKED_OUT/CANCELLED/EXPIRED)
  - Security incident lifecycle events land in KPI event stream
  - KPI metrics computed: visitor_requests_pending_count, visitors_checked_in_count,
    visitor_unauthorized_attempts_count, security_incidents_open_count, security_incidents_escalated_count
  - Brain constants registered
  - Analytics-sink source tag applied to new metrics
"""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.modules.tenants import service as module_tenant_service
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork
import app.modules.visitor_management.service as visitor_svc
from app.modules.brain_core.constants import (
    VISITOR_MANAGEMENT_EVENT_TYPES,
    SECURITY_OPERATIONS_EVENT_TYPES,
)
from app.modules.brain_core.registry import DecisionRegistry, SignalRegistry
from app.platform.event_ingestion.types import VALID_EVENT_TYPES


# ─── helpers ──────────────────────────────────────────────────────────────────


def _create_tenant(prefix: str) -> int:
    slug = f"{prefix}-{uuid4().hex[:8]}"
    tenant = module_tenant_service.create_tenant({"slug": slug, "name": f"{prefix} Tenant"})
    return int(tenant["id"])


def _emit(*, tenant_id: int, event_type: str, count: int, base_id: int = 0) -> None:
    for i in range(count):
        event_ingestion_service.record_event(
            tenant_id=tenant_id,
            event_type=event_type,
            payload={"id": base_id + i, "source": "test-a0186"},
        )


# ─── Task 3: Visitor lifecycle FSM tests ──────────────────────────────────────


def test_visitor_fsm_register_creates_requested_visit(reset_shared_state) -> None:
    tenant_id = _create_tenant("vm-register")
    result = visitor_svc.register_visitor(
        tenant_id,
        name="Alice Smith",
        host_id="host-001",
        visit_date="2026-01-15",
    )
    assert result["status"] == "REQUESTED"
    assert "visit_id" in result


def test_visitor_fsm_approve_transitions_to_approved(reset_shared_state) -> None:
    tenant_id = _create_tenant("vm-approve")
    reg = visitor_svc.register_visitor(
        tenant_id, name="Bob Jones", host_id="host-002", visit_date="2026-01-16"
    )
    result = visitor_svc.approve_visit(tenant_id, visit_id=reg["visit_id"])
    assert result["status"] == "APPROVED"


def test_visitor_fsm_reject_transitions_to_rejected(reset_shared_state) -> None:
    tenant_id = _create_tenant("vm-reject")
    reg = visitor_svc.register_visitor(
        tenant_id, name="Carol White", host_id="host-003", visit_date="2026-01-17"
    )
    result = visitor_svc.reject_visit(tenant_id, visit_id=reg["visit_id"], reason="background check failed")
    assert result["status"] == "REJECTED"


def test_visitor_fsm_cancel_transitions_to_cancelled(reset_shared_state) -> None:
    tenant_id = _create_tenant("vm-cancel")
    reg = visitor_svc.register_visitor(
        tenant_id, name="Dave Black", host_id="host-004", visit_date="2026-01-18"
    )
    result = visitor_svc.cancel_visit(tenant_id, visit_id=reg["visit_id"])
    assert result["status"] == "CANCELLED"


def test_visitor_fsm_check_in_check_out_full_lifecycle(reset_shared_state) -> None:
    tenant_id = _create_tenant("vm-full-lifecycle")
    reg = visitor_svc.register_visitor(
        tenant_id, name="Eve Green", host_id="host-005", visit_date="2026-01-19"
    )
    visitor_svc.approve_visit(tenant_id, visit_id=reg["visit_id"])
    ci = visitor_svc.check_in_visitor(tenant_id, visit_id=reg["visit_id"], badge_number="BADGE-101")
    assert ci["status"] == "CHECKED_IN"
    co = visitor_svc.check_out_visitor(tenant_id, visit_id=reg["visit_id"])
    assert co["status"] == "CHECKED_OUT"


def test_visitor_fsm_invalid_transition_raises(reset_shared_state) -> None:
    tenant_id = _create_tenant("vm-invalid-transition")
    reg = visitor_svc.register_visitor(
        tenant_id, name="Frank Red", host_id="host-006", visit_date="2026-01-20"
    )
    # Cannot check_in from REQUESTED (must be APPROVED first)
    with pytest.raises(ValueError, match="Cannot transition"):
        visitor_svc.check_in_visitor(tenant_id, visit_id=reg["visit_id"], badge_number="BADGE-102")


def test_visitor_fsm_terminal_state_blocks_expire(reset_shared_state) -> None:
    tenant_id = _create_tenant("vm-terminal")
    reg = visitor_svc.register_visitor(
        tenant_id, name="Grace Blue", host_id="host-007", visit_date="2026-01-21"
    )
    visitor_svc.approve_visit(tenant_id, visit_id=reg["visit_id"])
    visitor_svc.check_in_visitor(tenant_id, visit_id=reg["visit_id"], badge_number="BADGE-103")
    visitor_svc.check_out_visitor(tenant_id, visit_id=reg["visit_id"])
    with pytest.raises(ValueError, match="terminal state"):
        visitor_svc.expire_visit(tenant_id, visit_id=reg["visit_id"])


# ─── Task 5: Event alignment tests ────────────────────────────────────────────


def test_visitor_lifecycle_events_in_valid_event_types() -> None:
    required = {
        "visitor.registered",
        "visitor.approved",
        "visitor.rejected",
        "visitor.checked_in",
        "visitor.checked_out",
        "visitor.expired",
        "visitor.cancelled",
        "visitor.unauthorized_attempt",
    }
    missing = required - VALID_EVENT_TYPES
    assert not missing, f"Missing visitor events in VALID_EVENT_TYPES: {missing}"


def test_security_incident_lifecycle_events_in_valid_event_types() -> None:
    required = {
        "security.incident.opened",
        "security.incident.acknowledged",
        "security.incident.escalated",
        "security.incident.resolved",
        "security.incident.dismissed",
    }
    missing = required - VALID_EVENT_TYPES
    assert not missing, f"Missing security incident events in VALID_EVENT_TYPES: {missing}"


# ─── Task 7: Brain readiness tests ────────────────────────────────────────────


def test_visitor_management_event_types_constant_defined() -> None:
    assert len(VISITOR_MANAGEMENT_EVENT_TYPES) >= 7
    assert "visitor.registered" in VISITOR_MANAGEMENT_EVENT_TYPES
    assert "visitor.unauthorized_attempt" in VISITOR_MANAGEMENT_EVENT_TYPES


def test_security_operations_event_types_constant_defined() -> None:
    assert len(SECURITY_OPERATIONS_EVENT_TYPES) >= 4
    assert "security.incident.opened" in SECURITY_OPERATIONS_EVENT_TYPES
    assert "security.incident.escalated" in SECURITY_OPERATIONS_EVENT_TYPES


def test_brain_signal_registry_has_visitor_signals() -> None:
    signals = SignalRegistry.signals
    assert "visitor.registered" in signals
    assert "visitor.unauthorized_attempt" in signals
    assert signals["visitor.unauthorized_attempt"]["signal_class"] == "security_threat"


def test_brain_signal_registry_has_security_incident_signals() -> None:
    signals = SignalRegistry.signals
    assert "security.incident.opened" in signals
    assert "security.incident.escalated" in signals
    assert signals["security.incident.escalated"]["signal_class"] == "security_threat"


def test_brain_decision_registry_has_visitor_management_brain() -> None:
    decisions = DecisionRegistry.decisions
    assert "visitor_management_ops" in decisions
    assert decisions["visitor_management_ops"]["decision_type"] == "visitor_risk"


def test_brain_decision_registry_has_security_operations_brain() -> None:
    decisions = DecisionRegistry.decisions
    assert "security_operations_ops" in decisions
    assert decisions["security_operations_ops"]["decision_type"] == "security_incident_risk"


# ─── Task 6: KPI compatibility tests ──────────────────────────────────────────


def test_visitor_management_kpi_metrics_derived_from_events(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-visitor-mgmt")

    _emit(tenant_id=tenant_id, event_type="visitor.registered", count=5, base_id=50_000)
    _emit(tenant_id=tenant_id, event_type="visitor.checked_in", count=3, base_id=51_000)
    _emit(tenant_id=tenant_id, event_type="visitor.unauthorized_attempt", count=2, base_id=52_000)

    with UnitOfWork() as uow:
        rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    values = {str(item["metric_key"]): int(item["metric_value"]) for item in rows}

    assert values["visitor_requests_pending_count"] == 5
    assert values["visitors_checked_in_count"] == 3
    assert values["visitor_unauthorized_attempts_count"] == 2


def test_security_operations_kpi_metrics_derived_from_events(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-security-ops")

    _emit(tenant_id=tenant_id, event_type="security.incident.opened", count=4, base_id=53_000)
    _emit(tenant_id=tenant_id, event_type="security.incident.escalated", count=1, base_id=54_000)

    with UnitOfWork() as uow:
        rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    values = {str(item["metric_key"]): int(item["metric_value"]) for item in rows}

    assert values["security_incidents_open_count"] == 4
    assert values["security_incidents_escalated_count"] == 1


def test_visitor_security_kpis_are_marked_as_analytics_sink(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-visitor-sec-meta")

    _emit(tenant_id=tenant_id, event_type="visitor.registered", count=1, base_id=55_000)
    _emit(tenant_id=tenant_id, event_type="security.incident.opened", count=1, base_id=56_000)

    with UnitOfWork() as uow:
        rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    metadata_by_key = {str(item["metric_key"]): dict(item.get("metadata_json") or {}) for item in rows}

    assert metadata_by_key["visitor_requests_pending_count"]["source"] == "analytics_sink_v1"
    assert metadata_by_key["security_incidents_open_count"]["source"] == "analytics_sink_v1"


def test_visitor_security_kpis_tenant_isolated(reset_shared_state) -> None:
    tenant_a = _create_tenant("kpi-vis-isolated-a")
    tenant_b = _create_tenant("kpi-vis-isolated-b")

    _emit(tenant_id=tenant_a, event_type="visitor.registered", count=7, base_id=60_000)
    _emit(tenant_id=tenant_b, event_type="visitor.registered", count=2, base_id=61_000)
    _emit(tenant_id=tenant_a, event_type="security.incident.opened", count=3, base_id=62_000)

    with UnitOfWork() as uow:
        rows_a = kpi_service.refresh_tenant_metrics(tenant_id=tenant_a, uow=uow)
    with UnitOfWork() as uow:
        rows_b = kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow)

    vals_a = {str(r["metric_key"]): int(r["metric_value"]) for r in rows_a}
    vals_b = {str(r["metric_key"]): int(r["metric_value"]) for r in rows_b}

    assert vals_a["visitor_requests_pending_count"] == 7
    assert vals_b["visitor_requests_pending_count"] == 2
    assert vals_a["security_incidents_open_count"] == 3
    assert vals_b["security_incidents_open_count"] == 0


def test_visitor_register_emits_event_to_ingestion_layer(reset_shared_state) -> None:
    """register_visitor() must land visitor.registered in the event_ingestion layer."""
    tenant_id = _create_tenant("vm-event-emit")
    visitor_svc.register_visitor(
        tenant_id, name="Hana Kato", host_id="host-010", visit_date="2026-02-01"
    )
    summary = event_ingestion_service.summary_for_tenant(tenant_id)
    assert summary.get("visitor.registered", 0) >= 1
