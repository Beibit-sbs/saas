from __future__ import annotations

from unittest.mock import MagicMock

from tests.conftest import ADMIN_HEADERS, client

BASE = "/api/admin/financial-aid"

_AID_PAYLOAD = {
    "student_id": 310,
    "aid_type": "scholarship",
    "amount": 2500,
    "currency": "USD",
    "term": "2026-FALL",
    "reviewer_id": "AID-1",
    "notes": "Merit-based",
}


def test_list_financial_aid_records_returns_200() -> None:
    resp = client.get(BASE, headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert isinstance(resp.json().get("items"), list)


def test_create_financial_aid_record_returns_200() -> None:
    resp = client.post(BASE, headers=ADMIN_HEADERS, json=_AID_PAYLOAD)
    assert resp.status_code == 200, resp.text
    body = resp.json()["item"]
    assert body["student_id"] == 310
    assert body["status"] == "pending"


def test_update_financial_aid_status_flow() -> None:
    create_resp = client.post(BASE, headers=ADMIN_HEADERS, json=_AID_PAYLOAD)
    assert create_resp.status_code == 200, create_resp.text
    record_id = create_resp.json()["item"]["id"]

    update_resp = client.patch(
        f"{BASE}/{record_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "approved", "notes": "Approved by committee"},
    )
    assert update_resp.status_code == 200, update_resp.text
    assert update_resp.json()["item"]["status"] == "approved"


def test_update_financial_aid_status_not_found() -> None:
    resp = client.patch(f"{BASE}/999999/status", headers=ADMIN_HEADERS, json={"status": "rejected"})
    assert resp.status_code == 404


def test_update_financial_aid_status_rejected_emits_bridge_signal(monkeypatch) -> None:
    publisher_instance = MagicMock(name="event_publisher")
    publisher_factory = MagicMock(return_value=publisher_instance)
    monkeypatch.setattr("app.platform.events.publisher.EventPublisher", publisher_factory)

    create_resp = client.post(BASE, headers=ADMIN_HEADERS, json=_AID_PAYLOAD)
    assert create_resp.status_code == 200, create_resp.text
    record_id = create_resp.json()["item"]["id"]

    update_resp = client.patch(
        f"{BASE}/{record_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "rejected", "notes": "Rejected after review"},
    )
    assert update_resp.status_code == 200, update_resp.text

    publisher_instance.publish_event.assert_called_once()
    call_kwargs = publisher_instance.publish_event.call_args.kwargs
    assert call_kwargs["event_type"] == "financial_aid.warning.detected"
    assert call_kwargs["aggregate_type"] == "financial_aid_record"
    assert call_kwargs["aggregate_id"] == record_id
    assert call_kwargs["payload_json"]["to_status"] == "rejected"


def test_update_financial_aid_status_approved_does_not_emit_bridge_signal(monkeypatch) -> None:
    publisher_instance = MagicMock(name="event_publisher")
    publisher_factory = MagicMock(return_value=publisher_instance)
    monkeypatch.setattr("app.platform.events.publisher.EventPublisher", publisher_factory)

    create_resp = client.post(BASE, headers=ADMIN_HEADERS, json=_AID_PAYLOAD)
    assert create_resp.status_code == 200, create_resp.text
    record_id = create_resp.json()["item"]["id"]

    update_resp = client.patch(
        f"{BASE}/{record_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "approved", "notes": "Approved by committee"},
    )
    assert update_resp.status_code == 200, update_resp.text

    publisher_instance.publish_event.assert_not_called()
