from __future__ import annotations

from app.modules.brain_core.signal_listener import SignalListener
from app.modules.platform_shared.events import DomainEvent, InProcessEventBus


def test_signal_listener_normalizes_and_forwards_tenant_event() -> None:
    bus = InProcessEventBus()
    received: list[dict] = []
    listener = SignalListener(bus, on_signal=received.append)
    listener.subscribe(["academic.attendance_risk.detected"])

    event = DomainEvent(
        event_id="evt-1",
        event_type="academic.attendance_risk.detected",
        occurred_at="2026-04-22T00:00:00Z",
        tenant_id=101,
        actor="scheduler",
        correlation_id="corr-1",
        payload={
            "student_id": "STU-1",
            "course_id": "COURSE-1",
            "section_id": "SEC-1",
            "source_entity_type": "section_attendance",
            "source_entity_id": "SEC-1",
        },
    )

    bus.publish(event)

    assert len(received) == 1
    normalized = received[0]
    assert normalized["tenant_id"] == 101
    assert normalized["event_type"] == "academic.attendance_risk.detected"
    assert normalized["correlation_id"] == "corr-1"
    assert normalized["source_entity_type"] == "section_attendance"
    assert normalized["payload"]["student_id"] == "STU-1"


def test_signal_listener_rejects_event_without_tenant() -> None:
    bus = InProcessEventBus()
    received: list[dict] = []
    listener = SignalListener(bus, on_signal=received.append)
    listener.subscribe(["academic.attendance_risk.detected"])

    event = DomainEvent(
        event_id="evt-2",
        event_type="academic.attendance_risk.detected",
        occurred_at="2026-04-22T00:00:00Z",
        tenant_id=None,
        actor="scheduler",
        correlation_id="corr-2",
        payload={"student_id": "STU-2"},
    )

    bus.publish(event)

    assert received == []
