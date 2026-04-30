"""Tests for programs + courses modules — router-level CRUD endpoints.

Covers: programs (GET list, GET consistency, POST create, PUT update, DELETE)
and courses (GET list, GET consistency, POST create, PUT update, DELETE).
Plus permission guards and validation checks.
"""

from tests.conftest import ADMIN_HEADERS, _auth_headers, client


# ===========================================================================
# PROGRAMS
# ===========================================================================


def test_list_programs_returns_200() -> None:
    resp = client.get("/api/admin/org/programs", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "programs" in body
    assert isinstance(body["programs"], list)


def test_programs_consistency_returns_200() -> None:
    resp = client.get("/api/admin/org/programs/consistency", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "program_count" in body
    assert "issue_count" in body


def test_create_program_and_list() -> None:
    payload = {
        "program_code": "TEST-PRG-001",
        "title": "Test Program for Hardening",
        "degree_type": "bachelor",
        "faculty": "Engineering",
        "status": "active",
    }
    resp = client.post("/api/admin/org/programs", headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert "program" in body
    program = body["program"]
    assert program["program_code"] == "TEST-PRG-001"
    program["id"]

    # Verify it appears in list
    list_resp = client.get("/api/admin/org/programs", headers=ADMIN_HEADERS)
    codes = [p["program_code"] for p in list_resp.json()["programs"]]
    assert "TEST-PRG-001" in codes


def test_update_program() -> None:
    # Create first
    create_resp = client.post(
        "/api/admin/org/programs",
        headers=ADMIN_HEADERS,
        json={
            "program_code": "TEST-UPD-001",
            "title": "Original Title",
            "degree_type": "bachelor",
            "faculty": "Engineering",
            "status": "active",
        },
    )
    assert create_resp.status_code == 200
    pid = create_resp.json()["program"]["id"]

    # Update
    update_resp = client.put(
        f"/api/admin/org/programs/{pid}",
        headers=ADMIN_HEADERS,
        json={
            "program_code": "TEST-UPD-001",
            "title": "Updated Title",
            "degree_type": "bachelor",
            "faculty": "Engineering",
            "status": "draft",
        },
    )
    assert update_resp.status_code == 200, update_resp.text
    assert update_resp.json()["program"]["title"] == "Updated Title"


def test_delete_program() -> None:
    create_resp = client.post(
        "/api/admin/org/programs",
        headers=ADMIN_HEADERS,
        json={
            "program_code": "TEST-DEL-001",
            "title": "To Delete",
            "degree_type": "bachelor",
            "faculty": "Science",
            "status": "active",
        },
    )
    assert create_resp.status_code == 200
    pid = create_resp.json()["program"]["id"]

    del_resp = client.delete(f"/api/admin/org/programs/{pid}", headers=ADMIN_HEADERS)
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True


def test_create_program_empty_code_fails() -> None:
    resp = client.post(
        "/api/admin/org/programs",
        headers=ADMIN_HEADERS,
        json={
            "program_code": "",
            "title": "X",
            "degree_type": "bachelor",
            "faculty": "Y",
            "status": "active",
        },
    )
    assert resp.status_code == 422


def test_update_nonexistent_program() -> None:
    resp = client.put(
        "/api/admin/org/programs/999999",
        headers=ADMIN_HEADERS,
        json={
            "program_code": "X",
            "title": "X",
            "degree_type": "bachelor",
            "faculty": "Y",
            "status": "active",
        },
    )
    assert resp.status_code in (404, 400)


def test_delete_nonexistent_program() -> None:
    resp = client.delete("/api/admin/org/programs/999999", headers=ADMIN_HEADERS)
    assert resp.status_code in (404, 400)


# Programs — permission guards
def test_programs_list_requires_auth() -> None:
    resp = client.get("/api/admin/org/programs")
    assert resp.status_code in (401, 403)


def test_programs_create_requires_auth() -> None:
    resp = client.post(
        "/api/admin/org/programs",
        json={"program_code": "x", "title": "x", "degree_type": "x", "faculty": "x", "status": "x"},
    )
    assert resp.status_code in (401, 403)


def test_viewer_cannot_create_program() -> None:
    viewer = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.post(
        "/api/admin/org/programs",
        headers=viewer,
        json={"program_code": "x", "title": "x", "degree_type": "x", "faculty": "x", "status": "x"},
    )
    assert resp.status_code == 403


# ===========================================================================
# COURSES
# ===========================================================================


def _create_program_for_courses() -> int:
    """Helper — create a program to reference in courses."""
    resp = client.post(
        "/api/admin/org/programs",
        headers=ADMIN_HEADERS,
        json={
            "program_code": "CRS-HOST-001",
            "title": "Host Program",
            "degree_type": "bachelor",
            "faculty": "CS",
            "status": "active",
        },
    )
    return resp.json()["program"]["id"]


def test_list_courses_returns_200() -> None:
    resp = client.get("/api/admin/org/courses", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "courses" in body
    assert isinstance(body["courses"], list)


def test_courses_consistency_returns_200() -> None:
    resp = client.get("/api/admin/org/courses/consistency", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "course_count" in body
    assert "issue_count" in body


def test_create_course_and_list() -> None:
    pid = _create_program_for_courses()
    payload = {
        "course_code": "CS-101",
        "title": "Intro to CS",
        "credits": 3,
        "program_id": pid,
        "status": "active",
    }
    resp = client.post("/api/admin/org/courses", headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert "course" in body
    assert body["course"]["course_code"] == "CS-101"

    # Verify in list
    list_resp = client.get("/api/admin/org/courses", headers=ADMIN_HEADERS)
    codes = [c["course_code"] for c in list_resp.json()["courses"]]
    assert "CS-101" in codes


def test_update_course() -> None:
    pid = _create_program_for_courses()
    create_resp = client.post(
        "/api/admin/org/courses",
        headers=ADMIN_HEADERS,
        json={
            "course_code": "UPD-101",
            "title": "Original",
            "credits": 2,
            "program_id": pid,
            "status": "active",
        },
    )
    assert create_resp.status_code == 200
    cid = create_resp.json()["course"]["id"]

    update_resp = client.put(
        f"/api/admin/org/courses/{cid}",
        headers=ADMIN_HEADERS,
        json={
            "course_code": "UPD-101",
            "title": "Updated",
            "credits": 4,
            "program_id": pid,
            "status": "active",
        },
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["course"]["title"] == "Updated"


def test_delete_course() -> None:
    pid = _create_program_for_courses()
    create_resp = client.post(
        "/api/admin/org/courses",
        headers=ADMIN_HEADERS,
        json={
            "course_code": "DEL-101",
            "title": "To Delete",
            "credits": 1,
            "program_id": pid,
            "status": "active",
        },
    )
    assert create_resp.status_code == 200
    cid = create_resp.json()["course"]["id"]

    del_resp = client.delete(f"/api/admin/org/courses/{cid}", headers=ADMIN_HEADERS)
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True


def test_create_course_empty_code_fails() -> None:
    resp = client.post(
        "/api/admin/org/courses",
        headers=ADMIN_HEADERS,
        json={
            "course_code": "",
            "title": "X",
            "credits": 1,
            "program_id": 1,
            "status": "active",
        },
    )
    assert resp.status_code == 422


def test_create_course_negative_credits_fails() -> None:
    resp = client.post(
        "/api/admin/org/courses",
        headers=ADMIN_HEADERS,
        json={
            "course_code": "NEG-101",
            "title": "Neg Credits",
            "credits": -1,
            "program_id": 1,
            "status": "active",
        },
    )
    assert resp.status_code == 422


def test_update_nonexistent_course() -> None:
    resp = client.put(
        "/api/admin/org/courses/999999",
        headers=ADMIN_HEADERS,
        json={
            "course_code": "X",
            "title": "X",
            "credits": 1,
            "program_id": 1,
            "status": "active",
        },
    )
    assert resp.status_code in (404, 400)


def test_delete_nonexistent_course() -> None:
    resp = client.delete("/api/admin/org/courses/999999", headers=ADMIN_HEADERS)
    assert resp.status_code in (404, 400)


# Courses — permission guards
def test_courses_list_requires_auth() -> None:
    resp = client.get("/api/admin/org/courses")
    assert resp.status_code in (401, 403)


def test_courses_create_requires_auth() -> None:
    resp = client.post(
        "/api/admin/org/courses",
        json={"course_code": "x", "title": "x", "credits": 1, "program_id": 1, "status": "x"},
    )
    assert resp.status_code in (401, 403)


def test_viewer_cannot_create_course() -> None:
    viewer = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.post(
        "/api/admin/org/courses",
        headers=viewer,
        json={"course_code": "x", "title": "x", "credits": 1, "program_id": 1, "status": "x"},
    )
    assert resp.status_code == 403
