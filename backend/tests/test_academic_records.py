"""Tests for the academic_records module (university records endpoints)."""

from __future__ import annotations

from tests.conftest import ADMIN_HEADERS, _auth_headers, client

VIEWER_HEADERS = _auth_headers("viewer@example.com", ["viewer"], tenant_id=1)
BASE_URL = "/api/admin/university/records"

_VALID_PAYLOAD = {
    "student_id": 1,
    "course_id": 1,
    "grade": "A",
    "semester": "Fall 2025",
    "status": "published",
}


def _seed_student_and_course() -> None:
    """Create prerequisite entities in the in-memory store so FK validation passes."""
    # Program (needed for course FK)
    client.post(
        "/api/admin/org/programs",
        headers=ADMIN_HEADERS,
        json={
            "program_code": "PRG-REC-SEED",
            "title": "Seed Program",
            "degree_type": "bachelor",
            "faculty": "Test",
            "status": "active",
        },
    )
    # Course (needs program_id)
    client.post(
        "/api/admin/org/courses",
        headers=ADMIN_HEADERS,
        json={
            "course_code": "CRS-REC-001",
            "title": "Seed Course",
            "credits": 3,
            "program_id": 1,
            "status": "active",
        },
    )
    # Student — seed directly in shared state (students API is DB-backed)
    from app.modules.university_core.shared import _state, _state_lock

    with _state_lock:
        _state.counters["students"] += 1
        sid = _state.counters["students"]
        _state.data["students"][sid] = {
            "id": sid,
            "student_number": "STU-REC-001",
            "tenant_id": "1",
        }
        # Enrollment — required by _check_enrollment_exists_for_academic_record guard
        _state.counters.setdefault("enrollments", 0)
        _state.data.setdefault("enrollments", {})
        _state.counters["enrollments"] += 1
        eid = _state.counters["enrollments"]
        _state.data["enrollments"][eid] = {
            "id": eid,
            "student_id": 1,
            "course_id": 1,
            "semester": "Fall 2025",
            "status": "active",
            "tenant_id": "1",
        }


# ---------------------------------------------------------------------------
# GET /api/admin/university/records — list
# ---------------------------------------------------------------------------

def test_list_records_returns_200() -> None:
    resp = client.get(BASE_URL, headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "records" in body
    assert isinstance(body["records"], list)


def test_list_records_initially_empty() -> None:
    resp = client.get(BASE_URL, headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()["records"]) == 0


# ---------------------------------------------------------------------------
# POST /api/admin/university/records — create
# ---------------------------------------------------------------------------

def test_create_record_returns_200() -> None:
    _seed_student_and_course()
    resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=_VALID_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert body["record"]["student_id"] == 1
    assert body["record"]["grade"] == "A"


def test_create_record_appears_in_list() -> None:
    _seed_student_and_course()
    client.post(BASE_URL, headers=ADMIN_HEADERS, json=_VALID_PAYLOAD)
    resp = client.get(BASE_URL, headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()["records"]) >= 1


def test_create_record_missing_student_id() -> None:
    payload = {k: v for k, v in _VALID_PAYLOAD.items() if k != "student_id"}
    resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code == 422


def test_create_record_zero_student_id() -> None:
    payload = {**_VALID_PAYLOAD, "student_id": 0}
    resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code == 422


def test_create_record_negative_course_id() -> None:
    payload = {**_VALID_PAYLOAD, "course_id": -1}
    resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code == 422


def test_create_record_empty_grade() -> None:
    payload = {**_VALID_PAYLOAD, "grade": ""}
    resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code == 422


def test_create_record_empty_semester() -> None:
    payload = {**_VALID_PAYLOAD, "semester": ""}
    resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code == 422


def test_create_record_empty_status() -> None:
    payload = {**_VALID_PAYLOAD, "status": ""}
    resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PUT /api/admin/university/records/{id} — update
# ---------------------------------------------------------------------------

def test_update_record_returns_200() -> None:
    _seed_student_and_course()
    create_payload = {**_VALID_PAYLOAD, "status": "draft"}
    create_resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=create_payload)
    rec_id = create_resp.json()["record"]["id"]
    updated = {**create_payload, "grade": "B+"}
    resp = client.put(f"{BASE_URL}/{rec_id}", headers=ADMIN_HEADERS, json=updated)
    assert resp.status_code == 200
    assert resp.json()["record"]["grade"] == "B+"


def test_update_record_not_found() -> None:
    _seed_student_and_course()
    resp = client.put(f"{BASE_URL}/999999", headers=ADMIN_HEADERS, json=_VALID_PAYLOAD)
    assert resp.status_code in (400, 404)


# ---------------------------------------------------------------------------
# DELETE /api/admin/university/records/{id} — delete
# ---------------------------------------------------------------------------

def test_delete_record_returns_200() -> None:
    _seed_student_and_course()
    create_resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=_VALID_PAYLOAD)
    rec_id = create_resp.json()["record"]["id"]
    resp = client.delete(f"{BASE_URL}/{rec_id}", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True


def test_delete_record_not_found() -> None:
    resp = client.delete(f"{BASE_URL}/999999", headers=ADMIN_HEADERS)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/admin/university/records/consistency
# ---------------------------------------------------------------------------

def test_records_consistency_returns_200() -> None:
    resp = client.get(f"{BASE_URL}/consistency", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "record_count" in body
    assert "issue_count" in body
    assert "issues" in body


# ---------------------------------------------------------------------------
# Auth guards — unauthenticated
# ---------------------------------------------------------------------------

def test_list_records_unauthenticated() -> None:
    resp = client.get(BASE_URL)
    assert resp.status_code in (401, 403)


def test_create_record_unauthenticated() -> None:
    resp = client.post(BASE_URL, json=_VALID_PAYLOAD)
    assert resp.status_code in (401, 403)


def test_update_record_unauthenticated() -> None:
    resp = client.put(f"{BASE_URL}/1", json=_VALID_PAYLOAD)
    assert resp.status_code in (401, 403)


def test_delete_record_unauthenticated() -> None:
    resp = client.delete(f"{BASE_URL}/1")
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Auth guards — viewer role (no write)
# ---------------------------------------------------------------------------

def test_create_record_viewer_blocked() -> None:
    resp = client.post(BASE_URL, headers=VIEWER_HEADERS, json=_VALID_PAYLOAD)
    assert resp.status_code == 403


def test_update_record_viewer_blocked() -> None:
    resp = client.put(f"{BASE_URL}/1", headers=VIEWER_HEADERS, json=_VALID_PAYLOAD)
    assert resp.status_code == 403


def test_delete_record_viewer_blocked() -> None:
    resp = client.delete(f"{BASE_URL}/1", headers=VIEWER_HEADERS)
    assert resp.status_code == 403
