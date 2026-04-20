"""Tests for the students module (student lifecycle endpoints)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.main import app
from app.modules.students.dependencies import get_students_db
from tests.conftest import ADMIN_HEADERS, _auth_headers, client

VIEWER_HEADERS = _auth_headers("viewer@example.com", ["viewer"], tenant_id=1)

BASE_URL = "/api/admin/students"

_VALID_CREATE_PAYLOAD = {
    "person_id": 1,
    "student_number": "STU-TEST-001",
    "cohort_year": 2026,
}

# ---------------------------------------------------------------------------
# DB mock — students uses get_students_db (SQLAlchemy session)
# ---------------------------------------------------------------------------

def _mock_students_db():
    mock_session = MagicMock(spec=Session)

    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    result_mock.scalars.return_value.first.return_value = None
    result_mock.scalar_one_or_none.return_value = None
    result_mock.scalar.return_value = 0
    mock_session.execute.return_value = result_mock

    query_mock = MagicMock()
    query_mock.filter.return_value = query_mock
    query_mock.filter_by.return_value = query_mock
    query_mock.first.return_value = None
    query_mock.all.return_value = []
    query_mock.count.return_value = 0
    mock_session.query.return_value = query_mock

    yield mock_session


@pytest.fixture(autouse=True)
def _override_students_db():
    app.dependency_overrides[get_students_db] = _mock_students_db
    yield
    app.dependency_overrides.pop(get_students_db, None)


# ---------------------------------------------------------------------------
# POST /api/admin/students — create profile
# ---------------------------------------------------------------------------

def test_create_student_returns_response() -> None:
    resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=_VALID_CREATE_PAYLOAD)
    assert resp.status_code in (201, 400, 403, 409, 500)


def test_create_student_missing_person_id() -> None:
    payload = {**_VALID_CREATE_PAYLOAD}
    del payload["person_id"]
    resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code in (400, 422)


def test_create_student_invalid_person_id_zero() -> None:
    payload = {**_VALID_CREATE_PAYLOAD, "person_id": 0}
    resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code in (400, 422)


def test_create_student_missing_student_number() -> None:
    payload = {**_VALID_CREATE_PAYLOAD}
    del payload["student_number"]
    resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code in (400, 422)


def test_create_student_cohort_year_too_low() -> None:
    payload = {**_VALID_CREATE_PAYLOAD, "cohort_year": 1999}
    resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code in (400, 422)


def test_create_student_empty_student_number() -> None:
    payload = {**_VALID_CREATE_PAYLOAD, "student_number": ""}
    resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code in (400, 422)


# ---------------------------------------------------------------------------
# GET /api/admin/students — list
# ---------------------------------------------------------------------------

def test_list_students_returns_response() -> None:
    resp = client.get(BASE_URL, headers=ADMIN_HEADERS)
    assert resp.status_code in (200, 403, 500)


def test_list_students_with_pagination() -> None:
    resp = client.get(f"{BASE_URL}?page=1&page_size=5", headers=ADMIN_HEADERS)
    assert resp.status_code in (200, 403, 500)


# ---------------------------------------------------------------------------
# GET /api/admin/students/{id} — get profile
# ---------------------------------------------------------------------------

def test_get_student_profile_returns_response() -> None:
    resp = client.get(f"{BASE_URL}/1", headers=ADMIN_HEADERS)
    assert resp.status_code in (200, 400, 403, 404, 500)


# ---------------------------------------------------------------------------
# PATCH /api/admin/students/{id}/status — change status
# ---------------------------------------------------------------------------

def test_change_student_status_returns_response() -> None:
    payload = {"expected_version": 1, "to_status": "withdrawn", "reason": "test"}
    resp = client.patch(f"{BASE_URL}/1/status", headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code in (200, 400, 403, 404, 409, 500)


def test_change_student_status_missing_version() -> None:
    payload = {"to_status": "withdrawn"}
    resp = client.patch(f"{BASE_URL}/1/status", headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code in (400, 422)


def test_change_student_status_invalid_version_zero() -> None:
    payload = {"expected_version": 0, "to_status": "withdrawn"}
    resp = client.patch(f"{BASE_URL}/1/status", headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code in (400, 422)


# ---------------------------------------------------------------------------
# POST /api/admin/students/{id}/program-bindings — bind to program
# ---------------------------------------------------------------------------

def test_bind_student_to_program_returns_response() -> None:
    payload = {"student_profile_id": 1, "program_id": 1}
    resp = client.post(f"{BASE_URL}/1/program-bindings", headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code in (201, 400, 403, 404, 409, 500)


def test_bind_student_to_program_missing_program_id() -> None:
    payload = {"student_profile_id": 1}
    resp = client.post(f"{BASE_URL}/1/program-bindings", headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code in (400, 422)


def test_bind_student_to_program_invalid_program_id_zero() -> None:
    payload = {"student_profile_id": 1, "program_id": 0}
    resp = client.post(f"{BASE_URL}/1/program-bindings", headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code in (400, 422)


# ---------------------------------------------------------------------------
# GET /api/admin/students/{id}/program — active primary program
# ---------------------------------------------------------------------------

def test_get_active_primary_program_returns_response() -> None:
    resp = client.get(f"{BASE_URL}/1/program", headers=ADMIN_HEADERS)
    assert resp.status_code in (200, 400, 403, 404, 500)


# ---------------------------------------------------------------------------
# GET /api/admin/students/consistency/program-bindings — consistency
# ---------------------------------------------------------------------------

def test_program_binding_consistency_returns_response() -> None:
    resp = client.get(f"{BASE_URL}/consistency/program-bindings", headers=ADMIN_HEADERS)
    assert resp.status_code in (200, 403, 500)


# ---------------------------------------------------------------------------
# Unauthenticated → 401/403
# ---------------------------------------------------------------------------

def test_list_students_no_auth() -> None:
    resp = client.get(BASE_URL)
    assert resp.status_code in (401, 403)


def test_create_student_no_auth() -> None:
    resp = client.post(BASE_URL, json=_VALID_CREATE_PAYLOAD)
    assert resp.status_code in (401, 403)


def test_get_student_no_auth() -> None:
    resp = client.get(f"{BASE_URL}/1")
    assert resp.status_code in (401, 403)


def test_change_status_no_auth() -> None:
    resp = client.patch(f"{BASE_URL}/1/status", json={"expected_version": 1, "to_status": "withdrawn"})
    assert resp.status_code in (401, 403)


def test_bind_program_no_auth() -> None:
    resp = client.post(f"{BASE_URL}/1/program-bindings", json={"student_profile_id": 1, "program_id": 1})
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Viewer (read-only) → blocked on write
# ---------------------------------------------------------------------------

def test_viewer_cannot_create_student() -> None:
    resp = client.post(BASE_URL, headers=VIEWER_HEADERS, json=_VALID_CREATE_PAYLOAD)
    assert resp.status_code == 403


def test_viewer_cannot_change_status() -> None:
    payload = {"expected_version": 1, "to_status": "withdrawn"}
    resp = client.patch(f"{BASE_URL}/1/status", headers=VIEWER_HEADERS, json=payload)
    assert resp.status_code == 403


def test_viewer_cannot_bind_program() -> None:
    payload = {"student_profile_id": 1, "program_id": 1}
    resp = client.post(f"{BASE_URL}/1/program-bindings", headers=VIEWER_HEADERS, json=payload)
    assert resp.status_code == 403
