from __future__ import annotations

from tests.conftest import ADMIN_HEADERS, client

BASE = "/api/admin/career-services"

_OPPORTUNITY_PAYLOAD = {
    "student_id": 210,
    "title": "Backend Intern",
    "company": "Acme Labs",
    "opportunity_type": "internship",
    "owner_id": "CAREER-1",
    "start_date": "2026-06-01",
    "notes": "Priority candidate",
}


def _seed_enrollment_for_student(student_id: int, tenant_id: int = 1) -> None:
    """Seed an active enrollment to satisfy _check_student_is_actively_enrolled_for_career_opportunity."""
    from app.modules.university_core.shared import _state, _state_lock

    with _state_lock:
        _state.data.setdefault("enrollments", {})
        _state.counters.setdefault("enrollments", 0)
        _state.counters["enrollments"] += 1
        eid = _state.counters["enrollments"]
        _state.data["enrollments"][eid] = {
            "id": eid,
            "student_id": student_id,
            "course_id": 1,
            "semester": "Fall 2025",
            "status": "active",
            "tenant_id": str(tenant_id),
        }


def test_list_career_opportunities_returns_200() -> None:
    resp = client.get(BASE, headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert isinstance(resp.json().get("items"), list)


def test_create_career_opportunity_returns_200() -> None:
    _seed_enrollment_for_student(210)
    resp = client.post(BASE, headers=ADMIN_HEADERS, json=_OPPORTUNITY_PAYLOAD)
    assert resp.status_code == 200, resp.text
    body = resp.json()["item"]
    assert body["student_id"] == 210
    assert body["status"] == "open"


def test_update_career_opportunity_status_flow() -> None:
    _seed_enrollment_for_student(210)
    create_resp = client.post(BASE, headers=ADMIN_HEADERS, json=_OPPORTUNITY_PAYLOAD)
    assert create_resp.status_code == 200, create_resp.text
    opportunity_id = create_resp.json()["item"]["id"]

    update_resp = client.patch(
        f"{BASE}/{opportunity_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "in_review", "notes": "Resume validated"},
    )
    assert update_resp.status_code == 200, update_resp.text
    assert update_resp.json()["item"]["status"] == "in_review"


def test_update_career_opportunity_status_not_found() -> None:
    resp = client.patch(f"{BASE}/999999/status", headers=ADMIN_HEADERS, json={"status": "closed"})
    assert resp.status_code == 404
