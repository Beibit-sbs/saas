from __future__ import annotations

from tests.conftest import ADMIN_HEADERS, client

BASE = "/api/admin/alumni"

_PAYLOAD = {
    "student_id": 510,
    "graduation_year": 2024,
    "engagement_type": "event",
    "employer": "Contoso",
    "contact_email": "alumni510@example.edu",
    "notes": "Interested in mentoring",
}


def test_list_alumni_records_returns_200() -> None:
    resp = client.get(BASE, headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert isinstance(resp.json().get("items"), list)


def test_create_alumni_record_returns_200() -> None:
    resp = client.post(BASE, headers=ADMIN_HEADERS, json=_PAYLOAD)
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "active"


def test_update_alumni_status_flow() -> None:
    create_resp = client.post(BASE, headers=ADMIN_HEADERS, json=_PAYLOAD)
    assert create_resp.status_code == 200, create_resp.text
    record_id = create_resp.json()["item"]["id"]

    update_resp = client.patch(
        f"{BASE}/{record_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "engaged", "notes": "Joined alumni event"},
    )
    assert update_resp.status_code == 200, update_resp.text
    assert update_resp.json()["item"]["status"] == "engaged"


def test_update_alumni_status_not_found() -> None:
    resp = client.patch(f"{BASE}/999999/status", headers=ADMIN_HEADERS, json={"status": "inactive"})
    assert resp.status_code == 404
