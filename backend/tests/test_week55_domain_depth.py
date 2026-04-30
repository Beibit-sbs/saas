"""Week 55: facilities_work_orders domain depth — delay queue cap + overdue alerts."""

import pytest
from unittest.mock import MagicMock

from app.modules.facilities_work_orders import service
from app.modules.facilities_work_orders.schemas import WorkOrderCreateSchema


@pytest.mark.asyncio
async def test_work_order_delay_queue_cap_dict_structure():
    """Test that _WORK_ORDER_QUEUE_MAX_DELAYED has the expected structure."""
    assert isinstance(service._WORK_ORDER_QUEUE_MAX_DELAYED, dict)
    assert "critical" in service._WORK_ORDER_QUEUE_MAX_DELAYED
    assert "high" in service._WORK_ORDER_QUEUE_MAX_DELAYED
    assert "medium" in service._WORK_ORDER_QUEUE_MAX_DELAYED
    assert "low" in service._WORK_ORDER_QUEUE_MAX_DELAYED

    for priority, cap in service._WORK_ORDER_QUEUE_MAX_DELAYED.items():
        assert isinstance(priority, str)
        assert isinstance(cap, int)
        assert cap > 0


@pytest.mark.asyncio
async def test_delayed_work_order_statuses_and_risk_statuses():
    """Test that status constants are properly defined."""
    assert isinstance(service._DELAYED_WORK_ORDER_STATUSES, frozenset)
    assert isinstance(service._OVERDUE_RISK_STATUSES, frozenset)
    assert "on_hold" in service._DELAYED_WORK_ORDER_STATUSES
    assert "on_hold" in service._OVERDUE_RISK_STATUSES


@pytest.mark.asyncio
async def test_create_work_order_raises_when_delay_queue_cap_reached(monkeypatch):
    """Test that creating a work order raises ValueError when delay queue cap is reached."""
    tenant_id = 1
    request = WorkOrderCreateSchema(
        order_code="WO-001",
        facility_code="BLDG-A",
        title="Test repair",
        work_type="repair",
        priority="critical",
        status="open",
    )
    actor = "test_user"

    # Mock list_entities_for_tenant to return enough on_hold orders to hit the cap
    # critical delay cap is 2, so we return 2 existing on_hold orders
    existing_orders = [
        {
            "id": i,
            "priority": "critical",
            "status": "on_hold",
            "order_code": f"WO-{i:03d}",
            "facility_code": "BLDG-A",
        }
        for i in range(1, 3)  # 2 on_hold orders
    ]

    monkeypatch.setattr(
        "app.modules.facilities_work_orders.service.list_entities_for_tenant",
        lambda entity_name, tid: existing_orders if entity_name == "facilities_work_orders" else [],
    )

    with pytest.raises(ValueError) as exc_info:
        service.create_work_order(tenant_id, request, actor)
    assert "delay queue cap reached" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ensure_overdue_work_order_alert_record_is_idempotent(monkeypatch):
    """Test that _ensure_overdue_work_order_alert_record is idempotent via integration_source deduplication."""
    tenant_id = 1
    order_id = 42
    order_data = {
        "id": order_id,
        "order_code": "WO-042",
        "facility_code": "BLDG-A",
        "priority": "high",
        "status": "on_hold",
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
        if entity_name == "facilities_overdue_work_order_alerts":
            return []
        return []

    def mock_create_entity(*args, **kwargs):
        create_count[0] += 1
        return {"id": 1}

    monkeypatch.setattr(
        "app.modules.facilities_work_orders.service.list_entities_for_tenant",
        mock_list_entities,
    )
    monkeypatch.setattr(
        "app.modules.facilities_work_orders.service.create_entity_for_tenant",
        mock_create_entity,
    )

    # First call should create alert and publish event
    service._ensure_overdue_work_order_alert_record(tenant_id, order_id, order_data)
    assert create_count[0] == 1
    assert publish_event_mock.call_count == 1

    # Second call should find existing alert and skip creation
    def mock_list_entities_with_existing(entity_name, tid):
        if entity_name == "facilities_overdue_work_order_alerts":
            return [
                {
                    "id": 1,
                    "integration_source": "facilities_overdue_queue",
                    "source_entity_id": str(order_id),
                }
            ]
        return []

    monkeypatch.setattr(
        "app.modules.facilities_work_orders.service.list_entities_for_tenant",
        mock_list_entities_with_existing,
    )

    # Second call should skip creation and event publishing
    service._ensure_overdue_work_order_alert_record(tenant_id, order_id, order_data)
    assert create_count[0] == 1  # No additional creation
    assert publish_event_mock.call_count == 1  # No additional event
