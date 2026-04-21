from __future__ import annotations

from tests.conftest import ADMIN_HEADERS, client

BASE = "/api/v1/admin/notifications"


def _dispatch_payload(target: str, event: str) -> dict:
    return {
        "tenant_id": 1,
        "channel": "in_app",
        "target": target,
        "subject": "Platform Event",
        "payload": {"event": event, "title": "Platform Event", "message": "Notification body"},
    }


def test_notifications_list_contract() -> None:
    dispatch = client.post(BASE, headers=ADMIN_HEADERS, json=_dispatch_payload("tenant:1", "notif.list.contract"))
    assert dispatch.status_code == 201, dispatch.text

    response = client.get(BASE, headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    body = response.json()

    assert {"total", "page", "page_size", "items"}.issubset(body.keys())
    assert isinstance(body["items"], list)
    assert body["page"] == 1



def test_mark_single_notification_read() -> None:
    dispatch = client.post(BASE, headers=ADMIN_HEADERS, json=_dispatch_payload("tenant:1", "notif.mark.read"))
    assert dispatch.status_code == 201, dispatch.text
    notification_id = int(dispatch.json()["id"])

    mark = client.post(f"{BASE}/{notification_id}/read", headers=ADMIN_HEADERS)
    assert mark.status_code == 200, mark.text
    marked = mark.json()
    assert marked["id"] == str(notification_id)
    assert marked["read"] is True



def test_mark_all_notifications_read() -> None:
    first = client.post(BASE, headers=ADMIN_HEADERS, json=_dispatch_payload("tenant:1", "notif.markall.1"))
    second = client.post(BASE, headers=ADMIN_HEADERS, json=_dispatch_payload("tenant:1", "notif.markall.2"))
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text

    mark_all = client.post(f"{BASE}/mark-all-read", headers=ADMIN_HEADERS)
    assert mark_all.status_code == 200, mark_all.text
    body = mark_all.json()
    assert "updated" in body
    assert isinstance(body["updated"], int)

    unread = client.get(BASE, headers=ADMIN_HEADERS, params={"read": "false"})
    assert unread.status_code == 200, unread.text
    unread_items = unread.json()["items"]
    assert all(item["read"] is False for item in unread_items)
