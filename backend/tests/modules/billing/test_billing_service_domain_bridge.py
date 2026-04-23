from __future__ import annotations

from unittest.mock import MagicMock

from app.modules.billing import service as billing_service


def test_escalate_delinquency_record_publishes_payment_overdue_signal(monkeypatch) -> None:
    monkeypatch.setattr(billing_service, "_ensure_tenant_exists", lambda tenant_id: None)

    publisher_instance = MagicMock(name="event_publisher")
    publisher_factory = MagicMock(return_value=publisher_instance)
    monkeypatch.setattr(billing_service, "EventPublisher", publisher_factory)

    record = billing_service.create_delinquency_record(
        tenant_id=1,
        invoice_id="inv-1001",
        amount_cents=12500,
        status="grace_period",
    )

    escalated = billing_service.escalate_delinquency_record(
        tenant_id=1,
        record_id=int(record["id"]),
        actor="test.billing",
    )

    assert escalated["status"] == "overdue"
    publisher_instance.publish_event.assert_called_once()
    assert publisher_instance.publish_event.call_args.kwargs["event_type"] == "finance.payment_overdue.detected"
    payload = publisher_instance.publish_event.call_args.kwargs["payload_json"]
    assert payload["record_id"] == int(record["id"])
    assert payload["risk_level"] == "medium"
