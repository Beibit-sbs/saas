from app.modules.platform_shared.events import InProcessEventBus, create_domain_event


def test_tenant_aware_event_requires_tenant_id() -> None:
    try:
        create_domain_event(event_type="student.created", payload={"student_id": 1})
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "tenant-aware event requires tenant_id" in str(exc)


def test_in_process_event_bus_dispatches_event() -> None:
    bus = InProcessEventBus()
    received: list[str] = []

    def _handler(event) -> None:
        received.append(event.event_type)

    bus.subscribe("ai.chat.executed", _handler)
    event = create_domain_event(
        event_type="ai.chat.executed",
        tenant_id=1,
        actor="owner@example.com",
        correlation_id="req-1",
        payload={"model": "gpt-4o-mini"},
    )
    bus.publish(event)

    assert received == ["ai.chat.executed"]
