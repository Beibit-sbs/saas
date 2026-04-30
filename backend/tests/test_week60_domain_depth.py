"""Week 60 domain-depth tests: communications — message type active cap + broadcast risk alert."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Test 1: Cap dict structure
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_message_type_max_active_dict_structure():
    from app.modules.communications.service import _MESSAGE_TYPE_MAX_ACTIVE

    assert isinstance(_MESSAGE_TYPE_MAX_ACTIVE, dict)
    assert len(_MESSAGE_TYPE_MAX_ACTIVE) >= 2
    for k, v in _MESSAGE_TYPE_MAX_ACTIVE.items():
        assert isinstance(k, str) and len(k) > 0
        assert isinstance(v, int) and v > 0


# ---------------------------------------------------------------------------
# Test 2: Frozenset constants
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_active_message_statuses_and_broadcast_risk_statuses_are_frozensets():
    from app.modules.communications.service import _ACTIVE_MESSAGE_STATUSES, _BROADCAST_RISK_STATUSES

    assert isinstance(_ACTIVE_MESSAGE_STATUSES, frozenset)
    assert isinstance(_BROADCAST_RISK_STATUSES, frozenset)
    assert len(_ACTIVE_MESSAGE_STATUSES) >= 1
    assert len(_BROADCAST_RISK_STATUSES) >= 1
    assert all(isinstance(s, str) for s in _ACTIVE_MESSAGE_STATUSES)
    assert all(isinstance(s, str) for s in _BROADCAST_RISK_STATUSES)


# ---------------------------------------------------------------------------
# Test 3: create_message raises when active cap reached
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_message_raises_when_active_cap_reached(monkeypatch):
    from app.modules.communications import service

    msg_type = next(iter(service._MESSAGE_TYPE_MAX_ACTIVE))
    cap = service._MESSAGE_TYPE_MAX_ACTIVE[msg_type]
    active_status = next(iter(service._ACTIVE_MESSAGE_STATUSES))

    fake_records = [
        {"message_type": msg_type, "status": active_status, "id": i}
        for i in range(cap)
    ]

    monkeypatch.setattr(
        service, "list_entities_for_tenant",
        lambda entity, tenant_id: fake_records,
    )

    payload = {
        "message_code": "MSG-001",
        "title": "Test Message",
        "message_type": msg_type,
        "target_audience": "faculty",
        "status": active_status,
        "recipients_count": 100,
    }

    with pytest.raises(ValueError, match="Active message cap"):
        service.create_message(payload=payload, tenant_id=1)


# ---------------------------------------------------------------------------
# Test 4: _ensure_broadcast_risk_alert is idempotent
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ensure_broadcast_risk_alert_is_idempotent(monkeypatch):
    from app.modules.communications import service

    calls_to_create: list = []
    event_mock = MagicMock()

    monkeypatch.setattr(
        service, "list_entities_for_tenant",
        lambda entity, tenant_id: (
            [{"integration_source": "communications_broadcast_risk_queue", "source_entity_id": "42"}]
            if entity == "communication_broadcast_risk_alerts"
            else []
        ),
    )
    monkeypatch.setattr(
        service, "create_entity_for_tenant",
        lambda entity, data, tenant_id: calls_to_create.append((entity, data)) or data,
    )

    with patch(
        "app.platform.events.publisher.EventPublisher.publish_event",
        event_mock,
    ):
        service._ensure_broadcast_risk_alert(
            tenant_id=1,
            message_id=42,
            message_data={
                "message_code": "MSG-001",
                "message_type": "announcement",
                "recipients_count": 1000,
                "status": "sending",
            },
        )

    # Already exists → no new create, no event
    assert len(calls_to_create) == 0
    event_mock.assert_not_called()
