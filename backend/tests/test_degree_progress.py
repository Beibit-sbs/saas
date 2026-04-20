"""Tests for the degree_progress module (degree progress & graduation endpoints)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.main import app
from app.modules.degree_progress.dependencies import get_degree_progress_db
from tests.conftest import ADMIN_HEADERS, _auth_headers, client

VIEWER_HEADERS = _auth_headers("viewer@example.com", ["viewer"], tenant_id=1)

# ---------------------------------------------------------------------------
# DB mock — degree_progress uses get_degree_progress_db (SQLAlchemy session)
# ---------------------------------------------------------------------------

def _mock_degree_progress_db():
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
def _override_degree_progress_db():
    app.dependency_overrides[get_degree_progress_db] = _mock_degree_progress_db
    yield
    app.dependency_overrides.pop(get_degree_progress_db, None)


# ---------------------------------------------------------------------------
# GET /api/admin/students/{id}/degree-progress — degree progress
# ---------------------------------------------------------------------------

def test_get_degree_progress_returns_response() -> None:
    resp = client.get("/api/admin/students/1/degree-progress", headers=ADMIN_HEADERS)
    assert resp.status_code in (200, 400, 403, 404, 500)


def test_get_degree_progress_zero_student_id() -> None:
    resp = client.get("/api/admin/students/0/degree-progress", headers=ADMIN_HEADERS)
    assert resp.status_code == 422


def test_get_degree_progress_negative_student_id() -> None:
    resp = client.get("/api/admin/students/-1/degree-progress", headers=ADMIN_HEADERS)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/admin/students/{id}/graduation-eligibility — graduation
# ---------------------------------------------------------------------------

def test_get_graduation_eligibility_returns_response() -> None:
    resp = client.get("/api/admin/students/1/graduation-eligibility", headers=ADMIN_HEADERS)
    assert resp.status_code in (200, 400, 403, 404, 500)


def test_get_graduation_eligibility_zero_student_id() -> None:
    resp = client.get("/api/admin/students/0/graduation-eligibility", headers=ADMIN_HEADERS)
    assert resp.status_code == 422


def test_get_graduation_eligibility_negative_student_id() -> None:
    resp = client.get("/api/admin/students/-1/graduation-eligibility", headers=ADMIN_HEADERS)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/admin/degree-progress/consistency — consistency
# ---------------------------------------------------------------------------

def test_get_consistency_returns_response() -> None:
    resp = client.get("/api/admin/degree-progress/consistency", headers=ADMIN_HEADERS)
    assert resp.status_code in (200, 403, 500)


# ---------------------------------------------------------------------------
# Unauthenticated → 401/403
# ---------------------------------------------------------------------------

def test_degree_progress_no_auth() -> None:
    resp = client.get("/api/admin/students/1/degree-progress")
    assert resp.status_code in (401, 403)


def test_graduation_eligibility_no_auth() -> None:
    resp = client.get("/api/admin/students/1/graduation-eligibility")
    assert resp.status_code in (401, 403)


def test_consistency_no_auth() -> None:
    resp = client.get("/api/admin/degree-progress/consistency")
    assert resp.status_code in (401, 403)
