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


def _seed_graduated_student(student_id: int = 510, tenant_id: int = 1) -> None:
    """Seed a graduated student record required by _check_student_has_graduated_for_alumni_record."""
    from app.modules.university_core.shared import _state, _state_lock

    with _state_lock:
        _state.data.setdefault("students", {})
        _state.data["students"][student_id] = {
            "id": student_id,
            "student_id": f"STU-{student_id}",
            "status": "graduated",
            "tenant_id": str(tenant_id),
        }


def test_list_alumni_records_returns_200() -> None:
    resp = client.get(BASE, headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert isinstance(resp.json().get("items"), list)


def test_create_alumni_record_returns_200() -> None:
    _seed_graduated_student()
    resp = client.post(BASE, headers=ADMIN_HEADERS, json=_PAYLOAD)
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "active"


def test_update_alumni_status_flow() -> None:
    _seed_graduated_student()
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
