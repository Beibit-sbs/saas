"""
Wave1 #47 – Event Bus hardening: production contract tests.
Wires real platform_shared.events implementations (no skeleton stubs).
Covers: TENANT_AWARE_EVENT_TYPES validation, create_domain_event contract,
        InProcessEventBus dispatch, unregistered-type safety, DuplicateHandler isolation.
"""
from __future__ import annotations

import pytest

from app.modules.platform_shared.events import (
    TENANT_AWARE_EVENT_TYPES,
    DomainEvent,
    InProcessEventBus,
    create_domain_event,
)


# ---------------------------------------------------------------------------
# create_domain_event contract
# ---------------------------------------------------------------------------


def test_create_domain_event_rejects_empty_event_type() -> None:
    with pytest.raises(ValueError, match="event_type is required"):
        create_domain_event(event_type="", tenant_id=1)


def test_create_domain_event_requires_tenant_for_tenant_aware_types() -> None:
    """Any type in TENANT_AWARE_EVENT_TYPES must carry a positive tenant_id."""
    sample_type = next(iter(TENANT_AWARE_EVENT_TYPES))
    with pytest.raises(ValueError, match="tenant-aware event requires tenant_id"):
        create_domain_event(event_type=sample_type, tenant_id=None)


def test_create_domain_event_rejects_non_positive_tenant_id() -> None:
    with pytest.raises(ValueError, match="tenant_id must be positive"):
        create_domain_event(event_type="grade.submitted", tenant_id=0)


def test_create_domain_event_returns_valid_domain_event() -> None:
    event = create_domain_event(
        event_type="grade.submitted",
        tenant_id=7,
        actor="teacher@uni.edu",
        correlation_id="corr-001",
        payload={"grade_id": "g-1", "value": 4.0},
    )
    assert isinstance(event, DomainEvent)
    assert event.event_type == "grade.submitted"
    assert event.tenant_id == 7
    assert event.actor == "teacher@uni.edu"
    assert event.correlation_id == "corr-001"
    assert event.payload == {"grade_id": "g-1", "value": 4.0}
    # event_id is a non-empty UUID string
    assert len(event.event_id) > 0
    # occurred_at is non-empty ISO string
    assert "T" in event.occurred_at


def test_create_domain_event_normalises_event_type_to_lowercase() -> None:
    event = create_domain_event(event_type="Grade.Submitted", tenant_id=1)
    assert event.event_type == "grade.submitted"


# ---------------------------------------------------------------------------
# InProcessEventBus dispatch
# ---------------------------------------------------------------------------


def test_event_bus_dispatches_to_subscribed_handler() -> None:
    bus = InProcessEventBus()
    received: list[DomainEvent] = []
    bus.subscribe("grade.submitted", received.append)

    event = create_domain_event(event_type="grade.submitted", tenant_id=3)
    bus.publish(event)

    assert len(received) == 1
    assert received[0].event_id == event.event_id


def test_event_bus_does_not_dispatch_to_wrong_type_handler() -> None:
    bus = InProcessEventBus()
    received: list[DomainEvent] = []
    bus.subscribe("tenant.created", received.append)

    event = create_domain_event(event_type="grade.submitted", tenant_id=3)
    bus.publish(event)

    assert len(received) == 0


def test_event_bus_dispatches_to_multiple_handlers() -> None:
    bus = InProcessEventBus()
    sink_a: list[DomainEvent] = []
    sink_b: list[DomainEvent] = []
    bus.subscribe("grade.submitted", sink_a.append)
    bus.subscribe("grade.submitted", sink_b.append)

    event = create_domain_event(event_type="grade.submitted", tenant_id=5)
    bus.publish(event)

    assert len(sink_a) == 1
    assert len(sink_b) == 1


def test_event_bus_subscribe_rejects_empty_event_type() -> None:
    bus = InProcessEventBus()
    with pytest.raises(ValueError, match="event_type is required"):
        bus.subscribe("", lambda e: None)


def test_event_bus_publishes_to_no_handlers_without_error() -> None:
    """Publishing an event with no subscribers must not raise."""
    bus = InProcessEventBus()
    event = create_domain_event(event_type="grade.submitted", tenant_id=2)
    bus.publish(event)  # should not raise


# ---------------------------------------------------------------------------
# TENANT_AWARE_EVENT_TYPES registry coverage
# ---------------------------------------------------------------------------


def test_known_producer_types_are_in_tenant_aware_registry() -> None:
    """Types actively published in production code must be in the registry."""
    produced_in_code = {"tenant.created", "student.created"}
    missing = produced_in_code - TENANT_AWARE_EVENT_TYPES
    assert not missing, f"Produced types missing from registry: {missing}"
