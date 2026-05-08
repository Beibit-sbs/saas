"""A-018.7 Campus Operations Cross-Feature E2E contracts.

Scope: validation/evidence only. No new business features, no migrations,
no optimizer, no hardware ACS integration, no destructive automation.
"""
from __future__ import annotations

from uuid import uuid4

from app.modules.access_control import service as access_control_service
from app.modules.brain_core.registry import DecisionRegistry
from app.modules.events_management import service as events_management_service
from app.modules.security_operations import service as security_operations_service
from app.modules.tenants import service as module_tenant_service
from app.modules.visitor_management import service as visitor_management_service
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.event_ingestion.types import VALID_EVENT_TYPES
from app.platform.events.registry import EXACT_EVENT_REGISTRY
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork


def _create_tenant(prefix: str) -> int:
    slug = f"{prefix}-{uuid4().hex[:8]}"
    tenant = module_tenant_service.create_tenant({"slug": slug, "name": f"{prefix} Tenant"})
    return int(tenant["id"])


def _emit_many(*, tenant_id: int, event_type: str, count: int, base_id: int) -> None:
    for index in range(count):
        event_ingestion_service.record_event(
            tenant_id=tenant_id,
            event_type=event_type,
            payload={"id": base_id + index, "source": "test-a0187"},
        )


def _refresh_values(tenant_id: int) -> dict[str, int]:
    with UnitOfWork() as uow:
        rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)
    return {str(item["metric_key"]): int(item["metric_value"]) for item in rows}


def test_scheduling_room_booking_capacity_signal_to_dashboard_contract(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0187-flow1")

    # Room-booking/scheduling signals feed campus operations KPIs.
    _emit_many(tenant_id=tenant_id, event_type="scheduling.section.conflict_detected", count=1, base_id=10_000)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.room_conflict.detected", count=2, base_id=10_100)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.room_allocation.required", count=3, base_id=10_200)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.capacity_mismatch.detected", count=1, base_id=10_300)

    values = _refresh_values(tenant_id)

    # KPI contract: scheduling_conflicts_count is derived from section conflicts only.
    assert values["scheduling_conflicts_count"] == 1
    assert values["room_conflict_count"] == 5
    assert values["capacity_risk_sections_count"] == 0

    assert "scheduling.room_conflict.detected" in EXACT_EVENT_REGISTRY
    assert "scheduling.room_allocation.required" in EXACT_EVENT_REGISTRY
    assert "scheduling.capacity_mismatch.detected" in EXACT_EVENT_REGISTRY

    # Contract: no auto room reassignment capability/event is introduced.
    assert "scheduling.room_reassigned" not in VALID_EVENT_TYPES


def test_event_room_booking_lifecycle_to_campus_kpi_contract(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0187-flow2")

    event_created = events_management_service.create_event(
        tenant_id,
        title="Campus Open Day",
        category_id="ops",
        organizer_id="org-ops-1",
        capacity=80,
        start_time="2026-05-20T10:00:00+00:00",
        end_time="2026-05-20T12:00:00+00:00",
    )
    event_id = event_created["event_id"]

    # Lifecycle/KPI contract evidence comes from canonical event stream.
    # (No new business behavior introduced in A-018.7.)
    event_ingestion_service.record_event(
        tenant_id=tenant_id,
        event_type="event.published",
        payload={"event_id": event_id, "source": "test-a0187-flow2"},
    )
    event_ingestion_service.record_event(
        tenant_id=tenant_id,
        event_type="event.started",
        payload={"event_id": event_id, "source": "test-a0187-flow2"},
    )
    event_ingestion_service.record_event(
        tenant_id=tenant_id,
        event_type="event.completed",
        payload={"event_id": event_id, "source": "test-a0187-flow2"},
    )

    created_events = events_management_service.list_events(tenant_id)
    assert any(str(item.get("id")) == str(event_id) and str(item.get("status")) == "DRAFT" for item in created_events)

    # Room reference/capacity evidence from room-booking/scheduling namespace.
    _emit_many(tenant_id=tenant_id, event_type="scheduling.room_allocation.required", count=1, base_id=11_000)

    values = _refresh_values(tenant_id)

    assert values["events_published_count"] == 1
    assert values["events_started_count"] == 1
    assert values["events_completed_count"] == 1
    assert values["room_conflict_count"] == 1

    # Contract: events flow does not imply automatic room reassignment or access-policy mutation.
    assert "scheduling.room_reassigned" not in VALID_EVENT_TYPES
    assert "access.policy.auto_changed" not in VALID_EVENT_TYPES


def test_visitor_checkin_access_control_evidence_contract(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0187-flow3")

    visit = visitor_management_service.register_visitor(
        tenant_id,
        name="Visitor A",
        host_id="host-100",
        purpose="workshop",
        visit_date="2026-05-20",
    )
    visitor_management_service.approve_visit(tenant_id, visit_id=visit["visit_id"])
    visitor_management_service.check_in_visitor(
        tenant_id,
        visit_id=visit["visit_id"],
        badge_number="BADGE-A0187",
    )

    card = access_control_service.issue_card(
        tenant_id,
        holder_id="visitor-A",
        zones=["LOBBY", "MEETING_A"],
        actor="ops.user",
    )
    access_result = access_control_service.attempt_access(
        tenant_id,
        card_id=card["card_id"],
        zone="LOBBY",
        actor="ops.user",
    )

    events = event_ingestion_service.list_events_for_tenant(tenant_id=tenant_id, limit=200)
    access_logs = access_control_service.list_access_logs(tenant_id)

    assert access_result["granted"] is True
    assert any(e.get("event_type") == "visitor.checked_in" for e in events)
    assert any(str(log.get("result")) == "GRANTED" for log in access_logs)

    # Contract: no physical/hardware action marker is emitted by this flow.
    assert "door.unlock.hardware" not in VALID_EVENT_TYPES


def test_access_denied_security_operations_incident_contract(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0187-flow4")

    card = access_control_service.issue_card(
        tenant_id,
        holder_id="student-1",
        zones=["LIBRARY"],
        actor="sec.user",
    )

    deny_1 = access_control_service.attempt_access(tenant_id, card_id=card["card_id"], zone="LAB_X", actor="sec.user")
    deny_2 = access_control_service.attempt_access(tenant_id, card_id=card["card_id"], zone="LAB_X", actor="sec.user")
    deny_3 = access_control_service.attempt_access(tenant_id, card_id=card["card_id"], zone="LAB_X", actor="sec.user")

    visitor_management_service.record_unauthorized_attempt(
        tenant_id,
        visitor_name="Unknown Person",
        zone="LAB_X",
    )

    incident = security_operations_service.create_security_incident(
        {
            "incident_code": "INC-A0187-001",
            "facility_code": "LAB_X",
            "category": "unauthorized_access",
            "severity": "critical",
            "status": "open",
            "response_team": "security_command",
            "reported_at": "2026-05-20T10:15:00+00:00",
            "description": "Repeated denied attempts",
            "integration_source": "access_control",
            "access_control_event_id": str(card["card_id"]),
        },
        tenant_id,
    )

    values = _refresh_values(tenant_id)
    cards = access_control_service.list_cards(tenant_id)

    assert deny_1["granted"] is False
    assert deny_2["granted"] is False
    assert deny_3["granted"] is False
    assert str(incident["severity"]).lower() == "critical"
    assert values["visitor_unauthorized_attempts_count"] == 1
    assert values["security_incidents_open_count"] == 1
    assert values["security_incidents_escalated_count"] == 1

    # Review/escalation only: no auto lockout/ban side effect.
    assert any(str(c.get("id")) == str(card["card_id"]) and str(c.get("status")) == "ACTIVE" for c in cards)


def test_campus_operations_kpi_aggregates_supported_event_counts(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0187-flow5")

    _emit_many(tenant_id=tenant_id, event_type="scheduling.room_conflict.detected", count=2, base_id=12_000)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.room_allocation.required", count=1, base_id=12_100)
    _emit_many(tenant_id=tenant_id, event_type="access.denied", count=3, base_id=12_200)
    _emit_many(tenant_id=tenant_id, event_type="security.anomaly", count=1, base_id=12_300)
    _emit_many(tenant_id=tenant_id, event_type="event.published", count=2, base_id=12_400)
    _emit_many(tenant_id=tenant_id, event_type="event.completed", count=1, base_id=12_500)
    _emit_many(tenant_id=tenant_id, event_type="visitor.checked_in", count=4, base_id=12_600)
    _emit_many(tenant_id=tenant_id, event_type="security.incident.opened", count=2, base_id=12_700)

    values = _refresh_values(tenant_id)

    assert values["room_conflict_count"] == 3
    assert values["access_denied_count"] == 3
    assert values["unauthorized_attempts_count"] == 4
    assert values["events_published_count"] == 2
    assert values["events_completed_count"] == 1
    assert values["visitors_checked_in_count"] == 4
    assert values["security_incidents_open_count"] == 2


def test_cross_tenant_spoof_payload_cannot_override_authoritative_tenant(reset_shared_state) -> None:
    tenant_a = _create_tenant("a0187-tenant-a")
    tenant_b = _create_tenant("a0187-tenant-b")

    event_ingestion_service.record_event(
        tenant_id=tenant_a,
        event_type="visitor.registered",
        payload={"tenant_id": tenant_b, "spoof": True},
    )

    summary_a = event_ingestion_service.summary_for_tenant(tenant_a)
    summary_b = event_ingestion_service.summary_for_tenant(tenant_b)
    values_a = _refresh_values(tenant_a)
    values_b = _refresh_values(tenant_b)

    assert int(summary_a.get("visitor.registered", 0)) == 1
    assert int(summary_b.get("visitor.registered", 0)) == 0
    assert values_a["visitor_requests_pending_count"] == 1
    assert values_b["visitor_requests_pending_count"] == 0


def test_no_destructive_automation_contract(reset_shared_state) -> None:
    banned_event_markers = {
        "scheduling.room_reassigned",
        "access.lockout.applied",
        "access.ban.applied",
        "disciplinary.action.executed",
        "door.unlock.hardware",
    }
    assert not (banned_event_markers & set(VALID_EVENT_TYPES))

    action_sources = [
        DecisionRegistry.decisions["campus_operations"]["action_map"],
        DecisionRegistry.decisions["section_conflict"]["action_map"],
        DecisionRegistry.decisions["campus_security"]["action_map"],
        DecisionRegistry.decisions["visitor_management_ops"]["action_map"],
        DecisionRegistry.decisions["security_operations_ops"]["action_map"],
    ]

    flattened_actions: list[str] = []
    for action_map in action_sources:
        for value in action_map.values():
            if isinstance(value, str):
                flattened_actions.append(value.lower())
            else:
                flattened_actions.extend(str(item).lower() for item in value)

    banned_action_tokens = ("lockout", "ban", "disciplin", "hardware", "reassign")
    assert all(token not in action for action in flattened_actions for token in banned_action_tokens)
