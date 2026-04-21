from __future__ import annotations

from tests.conftest import ADMIN_HEADERS, client

BASE = "/api/admin/housing"

_REQUEST_PAYLOAD = {
    "student_id": 410,
    "request_type": "assignment",
    "dormitory": "North Hall",
    "room_preference": "double",
    "manager_id": "HSG-1",
    "notes": "Needs quiet floor",
}


def test_list_housing_requests_returns_200() -> None:
    resp = client.get(BASE, headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert isinstance(resp.json().get("items"), list)


def test_create_housing_request_returns_200() -> None:
    resp = client.post(BASE, headers=ADMIN_HEADERS, json=_REQUEST_PAYLOAD)
    assert resp.status_code == 200, resp.text
    body = resp.json()["item"]
    assert body["student_id"] == 410
    assert body["status"] == "submitted"


def test_update_housing_request_status_flow() -> None:
    create_resp = client.post(BASE, headers=ADMIN_HEADERS, json=_REQUEST_PAYLOAD)
    assert create_resp.status_code == 200, create_resp.text
    request_id = create_resp.json()["item"]["id"]

    update_resp = client.patch(
        f"{BASE}/{request_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "in_review", "notes": "Document package complete"},
    )
    assert update_resp.status_code == 200, update_resp.text
    assert update_resp.json()["item"]["status"] == "in_review"


def test_update_housing_request_status_not_found() -> None:
    resp = client.patch(f"{BASE}/999999/status", headers=ADMIN_HEADERS, json={"status": "approved"})
    assert resp.status_code == 404
