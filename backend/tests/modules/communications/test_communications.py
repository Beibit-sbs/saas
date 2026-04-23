"""Phase VIII-1: Communications module tests."""
from __future__ import annotations

import pytest

from app.modules.communications import service as comm_service
from tests.conftest import ADMIN_HEADERS, client as test_client


def test_list_messages_empty(monkeypatch) -> None:
    monkeypatch.setattr(comm_service, "list_entities_for_tenant", lambda name, tid: [])
    assert comm_service.list_messages(tenant_id=1) == []


def test_list_messages_filter_by_type(monkeypatch) -> None:
    rows = [
        {"id": 1, "message_code": "MSG-001", "title": "Welcome", "message_type": "announcement", "target_audience": "all", "status": "sent", "recipients_count": 100, "delivered_count": 95, "opened_count": 60, "tenant_id": 1},
        {"id": 2, "message_code": "MSG-002", "title": "Reminder", "message_type": "reminder", "target_audience": "students", "status": "sent", "recipients_count": 50, "delivered_count": 48, "opened_count": 30, "tenant_id": 1},
    ]
    monkeypatch.setattr(comm_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = comm_service.list_messages(tenant_id=1, message_type="announcement")
    assert len(result) == 1
    assert result[0]["message_code"] == "MSG-001"


def test_list_messages_filter_by_status(monkeypatch) -> None:
    rows = [
        {"id": 1, "message_code": "MSG-001", "title": "Draft Msg", "message_type": "newsletter", "target_audience": "all", "status": "draft", "recipients_count": 0, "delivered_count": 0, "opened_count": 0, "tenant_id": 1},
        {"id": 2, "message_code": "MSG-002", "title": "Sent Msg", "message_type": "newsletter", "target_audience": "all", "status": "sent", "recipients_count": 200, "delivered_count": 180, "opened_count": 100, "tenant_id": 1},
    ]
    monkeypatch.setattr(comm_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = comm_service.list_messages(tenant_id=1, status="sent")
    assert len(result) == 1
    assert result[0]["message_code"] == "MSG-002"


def test_get_communications_brain_context_good(monkeypatch) -> None:
    messages = [
        {"id": 1, "status": "sent", "recipients_count": 100, "delivered_count": 90, "opened_count": 60},
        {"id": 2, "status": "delivered", "recipients_count": 100, "delivered_count": 95, "opened_count": 70},
    ]
    monkeypatch.setattr(comm_service, "list_entities_for_tenant", lambda name, tid: messages)
    ctx = comm_service.get_communications_brain_context(tenant_id=1)
    assert ctx["delivery_health"] == "good"
    assert ctx["total_messages"] == 2
    assert ctx["sent_messages"] == 2


def test_get_communications_brain_context_poor(monkeypatch) -> None:
    messages = [
        {"id": 1, "status": "sent", "recipients_count": 100, "delivered_count": 30, "opened_count": 5},
    ]
    monkeypatch.setattr(comm_service, "list_entities_for_tenant", lambda name, tid: messages)
    ctx = comm_service.get_communications_brain_context(tenant_id=1)
    assert ctx["delivery_health"] == "poor"
    assert ctx["delivery_rate"] == 0.3


def test_get_communications_brain_context_fair(monkeypatch) -> None:
    messages = [
        {"id": 1, "status": "sent", "recipients_count": 100, "delivered_count": 70, "opened_count": 40},
    ]
    monkeypatch.setattr(comm_service, "list_entities_for_tenant", lambda name, tid: messages)
    ctx = comm_service.get_communications_brain_context(tenant_id=1)
    assert ctx["delivery_health"] == "fair"


def test_get_communications_brain_context_empty(monkeypatch) -> None:
    monkeypatch.setattr(comm_service, "list_entities_for_tenant", lambda name, tid: [])
    ctx = comm_service.get_communications_brain_context(tenant_id=1)
    assert ctx["delivery_rate"] == 0.0
    assert ctx["open_rate"] == 0.0
    assert ctx["delivery_health"] == "poor"


def test_create_message(monkeypatch) -> None:
    created = {"id": 5, "message_code": "MSG-005", "title": "Test", "message_type": "announcement", "target_audience": "all", "status": "draft", "recipients_count": 0, "delivered_count": 0, "opened_count": 0, "tenant_id": 1}
    monkeypatch.setattr(comm_service, "create_entity_for_tenant", lambda name, p, tid: created)
    result = comm_service.create_message({"message_code": "MSG-005", "title": "Test", "message_type": "announcement", "target_audience": "all", "status": "draft", "recipients_count": 0}, tenant_id=1)
    assert result["id"] == 5
    assert result["message_code"] == "MSG-005"
