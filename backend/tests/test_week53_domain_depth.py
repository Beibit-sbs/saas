"""Week 53: student_services domain depth — queue cap + unresolved risk alerts."""

import pytest
from unittest.mock import MagicMock

from app.modules.student_services import service
from app.modules.student_services.schemas import StudentServiceTicketCreateSchema


@pytest.mark.asyncio
async def test_ticket_queue_cap_dict_structure():
    """Test that _TICKET_QUEUE_MAX_ACTIVE has the expected structure."""
    assert isinstance(service._TICKET_QUEUE_MAX_ACTIVE, dict)
    assert "urgent" in service._TICKET_QUEUE_MAX_ACTIVE
    assert "high" in service._TICKET_QUEUE_MAX_ACTIVE
    assert "medium" in service._TICKET_QUEUE_MAX_ACTIVE
    assert "low" in service._TICKET_QUEUE_MAX_ACTIVE

    for priority, cap in service._TICKET_QUEUE_MAX_ACTIVE.items():
        assert isinstance(priority, str)
        assert isinstance(cap, int)
        assert cap > 0


@pytest.mark.asyncio
async def test_unresolved_ticket_statuses_and_risk_statuses():
    """Test that status constants are properly defined."""
    assert isinstance(service._UNRESOLVED_TICKET_STATUSES, frozenset)
    assert isinstance(service._UNRESOLVED_RISK_STATUSES, frozenset)
    assert "open" in service._UNRESOLVED_TICKET_STATUSES
    assert "in_progress" in service._UNRESOLVED_TICKET_STATUSES
    assert "open" in service._UNRESOLVED_RISK_STATUSES
    assert "in_progress" in service._UNRESOLVED_RISK_STATUSES


@pytest.mark.asyncio
async def test_create_ticket_raises_when_queue_cap_reached(monkeypatch):
    """Test that creating a ticket raises ValueError when queue cap is reached."""
    tenant_id = 1
    request = StudentServiceTicketCreateSchema(
        student_id=100,
        category="technical",
        subject="Test issue",
        description="Test description",
        priority="urgent",
    )
    actor = "test_user"
    monkeypatch.setattr(service, "_check_student_is_enrolled_for_service_ticket", lambda *a, **kw: None)

    # Mock list_entities_for_tenant to return enough tickets to hit the cap
    # urgent cap is 20, so we return 20 existing tickets
    existing_tickets = [
        {
            "id": i,
            "priority": "urgent",
            "status": "open",
            "student_id": 100 + i,
            "category": "technical",
        }
        for i in range(1, 21)  # 20 tickets
    ]

    monkeypatch.setattr(
        "app.modules.student_services.service.list_entities_for_tenant",
        lambda entity_name, tid: existing_tickets if entity_name == "student_service_tickets" else [],
    )

    with pytest.raises(ValueError) as exc_info:
        service.create_student_service_ticket(tenant_id, request, actor)
    assert "ticket queue cap reached" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ensure_unresolved_alert_record_is_idempotent(monkeypatch):
    """Test that _ensure_unresolved_alert_record is idempotent via integration_source deduplication."""
    tenant_id = 1
    ticket_id = 42
    ticket_data = {
        "id": ticket_id,
        "student_id": 100,
        "priority": "high",
        "category": "technical",
        "status": "open",
    }

    # Mock publish_event to track if it's called (it should be called once)
    publish_event_mock = MagicMock()
    monkeypatch.setattr(
        "app.platform.events.publisher.EventPublisher.publish_event",
        publish_event_mock,
    )

    # On first call, return no existing alerts
    create_count = [0]
    def mock_list_entities(entity_name, tid):
        if entity_name == "student_service_unresolved_alerts":
            return []
        return []

    def mock_create_entity(*args, **kwargs):
        create_count[0] += 1
        return {"id": 1}

    monkeypatch.setattr(
        "app.modules.student_services.service.list_entities_for_tenant",
        mock_list_entities,
    )
    monkeypatch.setattr(
        "app.modules.student_services.service.create_entity_for_tenant",
        mock_create_entity,
    )

    # First call should create alert and publish event
    service._ensure_unresolved_alert_record(tenant_id, ticket_id, ticket_data)
    assert create_count[0] == 1
    assert publish_event_mock.call_count == 1

    # Second call should find existing alert and skip creation
    def mock_list_entities_with_existing(entity_name, tid):
        if entity_name == "student_service_unresolved_alerts":
            return [
                {
                    "id": 1,
                    "integration_source": "student_service_unresolved_queue",
                    "source_entity_id": str(ticket_id),
                }
            ]
        return []

    monkeypatch.setattr(
        "app.modules.student_services.service.list_entities_for_tenant",
        mock_list_entities_with_existing,
    )

    # Second call should skip creation and event publishing
    service._ensure_unresolved_alert_record(tenant_id, ticket_id, ticket_data)
    assert create_count[0] == 1  # No additional creation
    assert publish_event_mock.call_count == 1  # No additional event
