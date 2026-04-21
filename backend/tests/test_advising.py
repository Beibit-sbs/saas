"""ERP-QA-168 – Advising & Mentoring module endpoint tests.

Covers 3 endpoints under /api/admin/advising:
  GET    /              (advising.read)
  POST   /              (advising.write)
  PATCH  /{id}/status   (advising.write)
"""

from __future__ import annotations

import pytest

from tests.conftest import ADMIN_HEADERS, _auth_headers, client

BASE = "/api/admin/advising"

VIEWER_HEADERS = _auth_headers("viewer@example.com", ["viewer"], tenant_id=1)

_SESSION_PAYLOAD = {
    "student_id": 101,
    "advisor_id": "FAC-101",
    "session_type": "academic",
    "scheduled_at": "2026-05-01T10:00",
    "notes": "Discuss progress",
}


# ---------------------------------------------------------------------------
# GET /api/admin/advising
# ---------------------------------------------------------------------------

def test_list_advising_sessions_returns_200() -> None:
    resp = client.get(BASE, headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert isinstance(body["items"], list)


def test_list_advising_sessions_requires_auth() -> None:
    resp = client.get(BASE)
    assert resp.status_code in (401, 403)


def test_list_advising_sessions_with_status_filter() -> None:
    resp = client.get(f"{BASE}?status=scheduled", headers=ADMIN_HEADERS)
    assert resp.status_code == 200


def test_list_advising_sessions_invalid_status_passthrough() -> None:
    # query param is string; backend filters gracefully
    resp = client.get(f"{BASE}?status=invalid_status", headers=ADMIN_HEADERS)
    assert resp.status_code in (200, 422)


# ---------------------------------------------------------------------------
# POST /api/admin/advising
# ---------------------------------------------------------------------------

def test_create_advising_session_returns_200() -> None:
    resp = client.post(BASE, headers=ADMIN_HEADERS, json=_SESSION_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert body["item"]["student_id"] == 101
    assert body["item"]["advisor_id"] == "FAC-101"
    assert body["item"]["status"] == "scheduled"


def test_create_advising_session_missing_advisor_id() -> None:
    payload = {**_SESSION_PAYLOAD, "advisor_id": ""}
    resp = client.post(BASE, headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code == 422


def test_create_advising_session_invalid_student_id() -> None:
    payload = {**_SESSION_PAYLOAD, "student_id": 0}
    resp = client.post(BASE, headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code == 422


def test_create_advising_session_requires_auth() -> None:
    resp = client.post(BASE, json=_SESSION_PAYLOAD)
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# PATCH /api/admin/advising/{id}/status
# ---------------------------------------------------------------------------

def test_update_session_status_not_found() -> None:
    resp = client.patch(
        f"{BASE}/99999/status",
        headers=ADMIN_HEADERS,
        json={"status": "completed"},
    )
    assert resp.status_code == 404


def test_update_session_status_invalid_status() -> None:
    resp = client.patch(
        f"{BASE}/1/status",
        headers=ADMIN_HEADERS,
        json={"status": "invalid_status"},
    )
    assert resp.status_code == 422


def test_update_session_status_full_flow() -> None:
    # Create a session, then complete it
    create_resp = client.post(BASE, headers=ADMIN_HEADERS, json=_SESSION_PAYLOAD)
    assert create_resp.status_code == 200
    session_id = create_resp.json()["item"]["id"]

    update_resp = client.patch(
        f"{BASE}/{session_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "completed", "outcome": "Student cleared for next semester"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["item"]["status"] == "completed"
    assert update_resp.json()["item"]["outcome"] == "Student cleared for next semester"


def test_update_session_status_requires_auth() -> None:
    resp = client.patch(f"{BASE}/1/status", json={"status": "completed"})
    assert resp.status_code in (401, 403)
