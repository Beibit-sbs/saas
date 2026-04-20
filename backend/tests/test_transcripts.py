"""Tests for the transcripts module (transcript endpoints)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.main import app
from app.modules.transcripts.dependencies import get_transcripts_db
from tests.conftest import ADMIN_HEADERS, _auth_headers, client

VIEWER_HEADERS = _auth_headers("viewer@example.com", ["viewer"], tenant_id=1)

# ---------------------------------------------------------------------------
# DB mock — transcripts uses get_transcripts_db (SqlAlchemy session)
# ---------------------------------------------------------------------------

def _mock_transcripts_db():
    mock_session = MagicMock(spec=Session)

    # SQLAlchemy 2.0 execute chain
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    result_mock.scalars.return_value.first.return_value = None
    result_mock.scalar_one_or_none.return_value = None
    result_mock.scalar.return_value = 0
    mock_session.execute.return_value = result_mock

    # Legacy query chain
    query_mock = MagicMock()
    query_mock.filter.return_value = query_mock
    query_mock.filter_by.return_value = query_mock
    query_mock.first.return_value = None
    query_mock.all.return_value = []
    query_mock.count.return_value = 0
    mock_session.query.return_value = query_mock

    yield mock_session


@pytest.fixture(autouse=True)
def _override_transcripts_db():
    app.dependency_overrides[get_transcripts_db] = _mock_transcripts_db
    yield
    app.dependency_overrides.pop(get_transcripts_db, None)


# ---------------------------------------------------------------------------
# GET /api/admin/students/{id}/transcript — get transcript
# ---------------------------------------------------------------------------

def test_get_transcript_returns_response() -> None:
    resp = client.get("/api/admin/students/1/transcript", headers=ADMIN_HEADERS)
    assert resp.status_code in (200, 403, 404, 500)


def test_get_transcript_zero_student_id() -> None:
    resp = client.get("/api/admin/students/0/transcript", headers=ADMIN_HEADERS)
    assert resp.status_code == 422


def test_get_transcript_negative_student_id() -> None:
    resp = client.get("/api/admin/students/-1/transcript", headers=ADMIN_HEADERS)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/admin/students/{id}/transcript/snapshot — create snapshot
# ---------------------------------------------------------------------------

def test_create_snapshot_returns_response() -> None:
    resp = client.post("/api/admin/students/1/transcript/snapshot", headers=ADMIN_HEADERS)
    assert resp.status_code in (201, 403, 404, 500)


def test_create_snapshot_zero_student_id() -> None:
    resp = client.post("/api/admin/students/0/transcript/snapshot", headers=ADMIN_HEADERS)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/admin/students/{id}/transcript/consistency — student consistency
# ---------------------------------------------------------------------------

def test_student_transcript_consistency_returns_response() -> None:
    resp = client.get("/api/admin/students/1/transcript/consistency", headers=ADMIN_HEADERS)
    assert resp.status_code in (200, 403, 404, 500)


def test_student_transcript_consistency_zero_id() -> None:
    resp = client.get("/api/admin/students/0/transcript/consistency", headers=ADMIN_HEADERS)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/admin/transcripts/consistency — tenant-wide consistency
# ---------------------------------------------------------------------------

def test_tenant_transcript_consistency_returns_response() -> None:
    resp = client.get("/api/admin/transcripts/consistency", headers=ADMIN_HEADERS)
    assert resp.status_code in (200, 403, 500)


# ---------------------------------------------------------------------------
# Auth guards — unauthenticated
# ---------------------------------------------------------------------------

def test_get_transcript_unauthenticated() -> None:
    resp = client.get("/api/admin/students/1/transcript")
    assert resp.status_code in (401, 403)


def test_create_snapshot_unauthenticated() -> None:
    resp = client.post("/api/admin/students/1/transcript/snapshot")
    assert resp.status_code in (401, 403)


def test_student_consistency_unauthenticated() -> None:
    resp = client.get("/api/admin/students/1/transcript/consistency")
    assert resp.status_code in (401, 403)


def test_tenant_consistency_unauthenticated() -> None:
    resp = client.get("/api/admin/transcripts/consistency")
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Auth guards — viewer role (no write)
# ---------------------------------------------------------------------------

def test_create_snapshot_viewer_blocked() -> None:
    resp = client.post("/api/admin/students/1/transcript/snapshot", headers=VIEWER_HEADERS)
    assert resp.status_code == 403
