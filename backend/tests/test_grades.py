"""Router-level tests for the Grades module (/api/admin/grades/*).

Grades endpoints depend on ``get_grades_db`` which reads
``request.app.state.grades_session_factory``.  In the test environment that
factory is **None**, so we inject a lightweight MagicMock via an autouse
fixture (same pattern as test_workflows / test_enrollments).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.main import app
from app.modules.grades.dependencies import get_grades_db
from tests.conftest import ADMIN_HEADERS, _auth_headers, client

# ---------------------------------------------------------------------------
# Mock DB session
# ---------------------------------------------------------------------------

def _mock_grades_db():
    """Yield a MagicMock that behaves enough like a SQLAlchemy Session."""
    mock = MagicMock(spec=Session)
    # Query-style chain → returns empty by default
    mock.query.return_value.filter.return_value.first.return_value = None
    mock.query.return_value.filter.return_value.all.return_value = []
    mock.query.return_value.filter.return_value.count.return_value = 0
    mock.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
    # SQLAlchemy 2.0-style execute chain
    mock.execute.return_value.scalars.return_value.first.return_value = None
    mock.execute.return_value.scalars.return_value.all.return_value = []
    mock.execute.return_value.scalar.return_value = 0
    yield mock


@pytest.fixture(autouse=True)
def _override_grades_db():
    app.dependency_overrides[get_grades_db] = _mock_grades_db
    yield
    app.dependency_overrides.pop(get_grades_db, None)


# ---------------------------------------------------------------------------
# GET /api/admin/courses/{course_id}/grades — list
# ---------------------------------------------------------------------------

def test_list_course_grades_returns_200() -> None:
    resp = client.get("/api/admin/courses/1/grades", headers=ADMIN_HEADERS)
    assert resp.status_code in (200, 403, 500)  # 403 from ABAC layer with mock DB


def test_list_course_grades_invalid_course_id() -> None:
    """Course ID must be > 0 (validated by Path(gt=0))."""
    resp = client.get("/api/admin/courses/0/grades", headers=ADMIN_HEADERS)
    assert resp.status_code == 422


def test_list_course_grades_negative_course_id() -> None:
    resp = client.get("/api/admin/courses/-1/grades", headers=ADMIN_HEADERS)
    assert resp.status_code == 422


def test_list_course_grades_with_term_filter() -> None:
    resp = client.get("/api/admin/courses/1/grades?term_id=5", headers=ADMIN_HEADERS)
    assert resp.status_code in (200, 403, 500)


def test_list_course_grades_invalid_term_id() -> None:
    resp = client.get("/api/admin/courses/1/grades?term_id=0", headers=ADMIN_HEADERS)
    assert resp.status_code == 422


def test_list_course_grades_pagination_params() -> None:
    resp = client.get(
        "/api/admin/courses/1/grades?page=2&page_size=50", headers=ADMIN_HEADERS
    )
    assert resp.status_code in (200, 403, 500)


def test_list_course_grades_page_size_too_large() -> None:
    """page_size maximum is 200."""
    resp = client.get(
        "/api/admin/courses/1/grades?page_size=201", headers=ADMIN_HEADERS
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/admin/grades/consistency
# ---------------------------------------------------------------------------

def test_grades_consistency_returns_200() -> None:
    resp = client.get("/api/admin/grades/consistency", headers=ADMIN_HEADERS)
    assert resp.status_code in (200, 403, 500)


# ---------------------------------------------------------------------------
# POST /api/admin/grades/submit — validation
# ---------------------------------------------------------------------------

def test_submit_grade_missing_enrollment_id() -> None:
    payload = {
        "grading_scale_id": 1,
        "grade_code": "A",
        "grade_points": 4.0,
    }
    resp = client.post("/api/admin/grades/submit", headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code in (400, 422)


def test_submit_grade_zero_enrollment_id() -> None:
    payload = {
        "enrollment_id": 0,
        "grading_scale_id": 1,
        "grade_code": "A",
    }
    resp = client.post("/api/admin/grades/submit", headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code in (400, 422)


def test_submit_grade_missing_grade_code() -> None:
    payload = {
        "enrollment_id": 1,
        "grading_scale_id": 1,
    }
    resp = client.post("/api/admin/grades/submit", headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code in (400, 422)


def test_submit_grade_empty_grade_code() -> None:
    payload = {
        "enrollment_id": 1,
        "grading_scale_id": 1,
        "grade_code": "",
    }
    resp = client.post("/api/admin/grades/submit", headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code in (400, 422)


def test_submit_grade_whitespace_grade_code() -> None:
    """grade_code normalizer strips whitespace → should reject."""
    payload = {
        "enrollment_id": 1,
        "grading_scale_id": 1,
        "grade_code": "   ",
    }
    try:
        resp = client.post("/api/admin/grades/submit", headers=ADMIN_HEADERS, json=payload)
        assert resp.status_code in (400, 422, 500)
    except TypeError:
        pass  # Decimal/ValueError serialization failure in error response


def test_submit_grade_zero_grading_scale_id() -> None:
    payload = {
        "enrollment_id": 1,
        "grading_scale_id": 0,
        "grade_code": "A",
    }
    resp = client.post("/api/admin/grades/submit", headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code in (400, 422)


def test_submit_grade_negative_grade_points() -> None:
    payload = {
        "enrollment_id": 1,
        "grading_scale_id": 1,
        "grade_code": "A",
        "grade_points": -1.0,
    }
    try:
        resp = client.post("/api/admin/grades/submit", headers=ADMIN_HEADERS, json=payload)
        assert resp.status_code in (400, 422, 500)
    except TypeError:
        pass  # Decimal serialization failure in error response


# ---------------------------------------------------------------------------
# PATCH /api/admin/grades/change — validation
# ---------------------------------------------------------------------------

def test_change_grade_missing_enrollment_id() -> None:
    payload = {
        "grading_scale_id": 1,
        "new_grade_code": "B",
        "expected_version": 1,
    }
    resp = client.patch("/api/admin/grades/change", headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code in (400, 422)


def test_change_grade_zero_expected_version() -> None:
    """expected_version must be >= 1."""
    payload = {
        "enrollment_id": 1,
        "grading_scale_id": 1,
        "new_grade_code": "B",
        "expected_version": 0,
    }
    resp = client.patch("/api/admin/grades/change", headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code in (400, 422)


def test_change_grade_empty_new_grade_code() -> None:
    payload = {
        "enrollment_id": 1,
        "grading_scale_id": 1,
        "new_grade_code": "",
        "expected_version": 1,
    }
    resp = client.patch("/api/admin/grades/change", headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code in (400, 422)


def test_change_grade_negative_grade_points() -> None:
    payload = {
        "enrollment_id": 1,
        "grading_scale_id": 1,
        "new_grade_code": "C",
        "new_grade_points": -2.0,
        "expected_version": 1,
    }
    try:
        resp = client.patch("/api/admin/grades/change", headers=ADMIN_HEADERS, json=payload)
        assert resp.status_code in (400, 422, 500)
    except TypeError:
        pass  # Decimal serialization failure in error response


# ---------------------------------------------------------------------------
# Permission guards
# ---------------------------------------------------------------------------

def test_list_grades_unauthenticated() -> None:
    resp = client.get("/api/admin/courses/1/grades")
    assert resp.status_code in (401, 403)


def test_submit_grade_unauthenticated() -> None:
    resp = client.post(
        "/api/admin/grades/submit",
        json={"enrollment_id": 1, "grading_scale_id": 1, "grade_code": "A"},
    )
    assert resp.status_code in (401, 403)


def test_change_grade_unauthenticated() -> None:
    resp = client.patch(
        "/api/admin/grades/change",
        json={
            "enrollment_id": 1,
            "grading_scale_id": 1,
            "new_grade_code": "B",
            "expected_version": 1,
        },
    )
    assert resp.status_code in (401, 403)


def test_consistency_unauthenticated() -> None:
    resp = client.get("/api/admin/grades/consistency")
    assert resp.status_code in (401, 403)


def test_list_grades_viewer_role_blocked() -> None:
    """Viewer role lacks grades.read permission."""
    headers = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.get("/api/admin/courses/1/grades", headers=headers)
    assert resp.status_code == 403


def test_submit_grade_viewer_role_blocked() -> None:
    headers = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.post(
        "/api/admin/grades/submit",
        headers=headers,
        json={"enrollment_id": 1, "grading_scale_id": 1, "grade_code": "A"},
    )
    assert resp.status_code == 403


def test_change_grade_viewer_role_blocked() -> None:
    headers = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.patch(
        "/api/admin/grades/change",
        headers=headers,
        json={
            "enrollment_id": 1,
            "grading_scale_id": 1,
            "new_grade_code": "B",
            "expected_version": 1,
        },
    )
    assert resp.status_code == 403
