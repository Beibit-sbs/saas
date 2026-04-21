"""ERP-QA-170 - Student Services ticketing module endpoint tests."""

from __future__ import annotations

from tests.conftest import ADMIN_HEADERS, client

BASE = "/api/admin/student-services/tickets"

_TICKET_PAYLOAD = {
    "student_id": 110,
    "category": "registrar",
    "subject": "Enrollment certificate",
    "description": "Need enrollment confirmation for embassy submission",
    "priority": "high",
    "owner_id": "STAFF-7",
    "channel": "portal",
}


def test_list_student_service_tickets_returns_200() -> None:
    resp = client.get(BASE, headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert isinstance(resp.json().get("items"), list)


def test_create_student_service_ticket_returns_200() -> None:
    resp = client.post(BASE, headers=ADMIN_HEADERS, json=_TICKET_PAYLOAD)
    assert resp.status_code == 200, resp.text
    body = resp.json()["item"]
    assert body["student_id"] == 110
    assert body["status"] == "open"


def test_update_student_service_ticket_status_full_flow() -> None:
    create_resp = client.post(BASE, headers=ADMIN_HEADERS, json=_TICKET_PAYLOAD)
    assert create_resp.status_code == 200, create_resp.text
    ticket_id = create_resp.json()["item"]["id"]

    update_resp = client.patch(
        f"{BASE}/{ticket_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "in_progress", "resolution_notes": "Assigned to registrar desk"},
    )
    assert update_resp.status_code == 200, update_resp.text
    assert update_resp.json()["item"]["status"] == "in_progress"


def test_update_student_service_ticket_status_not_found() -> None:
    resp = client.patch(f"{BASE}/999999/status", headers=ADMIN_HEADERS, json={"status": "closed"})
    assert resp.status_code == 404


def test_create_ticket_invalid_payload() -> None:
    payload = {**_TICKET_PAYLOAD, "subject": ""}
    resp = client.post(BASE, headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code == 422
