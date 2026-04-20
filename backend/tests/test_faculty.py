"""Tests for the faculty module (org-faculty endpoints)."""

from __future__ import annotations

import pytest

from tests.conftest import ADMIN_HEADERS, _auth_headers, client

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VIEWER_HEADERS = _auth_headers("viewer@example.com", ["viewer"], tenant_id=1)
BASE_URL = "/api/admin/org/faculty"

_VALID_PAYLOAD = {
    "faculty_id": "FAC-001",
    "first_name": "John",
    "last_name": "Doe",
    "department": "Computer Science",
    "email": "john.doe@university.edu",
    "status": "active",
}


# ---------------------------------------------------------------------------
# GET /api/admin/org/faculty — list
# ---------------------------------------------------------------------------

def test_list_faculty_returns_200() -> None:
    resp = client.get(BASE_URL, headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "faculty" in body
    assert isinstance(body["faculty"], list)


def test_list_faculty_initially_empty() -> None:
    resp = client.get(BASE_URL, headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()["faculty"]) == 0


# ---------------------------------------------------------------------------
# POST /api/admin/org/faculty — create
# ---------------------------------------------------------------------------

def test_create_faculty_returns_200() -> None:
    resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=_VALID_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert body["faculty"]["faculty_id"] == "FAC-001"
    assert body["faculty"]["email"] == "john.doe@university.edu"


def test_create_faculty_appears_in_list() -> None:
    client.post(BASE_URL, headers=ADMIN_HEADERS, json=_VALID_PAYLOAD)
    resp = client.get(BASE_URL, headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()["faculty"]) >= 1


def test_create_faculty_missing_faculty_id() -> None:
    payload = {**_VALID_PAYLOAD}
    del payload["faculty_id"]
    resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code == 422


def test_create_faculty_empty_first_name() -> None:
    payload = {**_VALID_PAYLOAD, "first_name": ""}
    resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code == 422


def test_create_faculty_empty_email() -> None:
    payload = {**_VALID_PAYLOAD, "email": ""}
    resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code == 422


def test_create_faculty_empty_department() -> None:
    payload = {**_VALID_PAYLOAD, "department": ""}
    resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PUT /api/admin/org/faculty/{id} — update
# ---------------------------------------------------------------------------

def test_update_faculty_returns_200() -> None:
    create_resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=_VALID_PAYLOAD)
    fac_id = create_resp.json()["faculty"]["id"]
    update_payload = {**_VALID_PAYLOAD, "department": "Mathematics"}
    resp = client.put(f"{BASE_URL}/{fac_id}", headers=ADMIN_HEADERS, json=update_payload)
    assert resp.status_code == 200
    assert resp.json()["faculty"]["department"] == "Mathematics"


def test_update_faculty_not_found() -> None:
    resp = client.put(f"{BASE_URL}/999999", headers=ADMIN_HEADERS, json=_VALID_PAYLOAD)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/admin/org/faculty/{id} — delete
# ---------------------------------------------------------------------------

def test_delete_faculty_returns_200() -> None:
    create_resp = client.post(BASE_URL, headers=ADMIN_HEADERS, json=_VALID_PAYLOAD)
    fac_id = create_resp.json()["faculty"]["id"]
    resp = client.delete(f"{BASE_URL}/{fac_id}", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True


def test_delete_faculty_not_found() -> None:
    resp = client.delete(f"{BASE_URL}/999999", headers=ADMIN_HEADERS)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/admin/org/faculty/consistency
# ---------------------------------------------------------------------------

def test_faculty_consistency_returns_200() -> None:
    resp = client.get(f"{BASE_URL}/consistency", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "faculty_count" in body
    assert "issue_count" in body
    assert "issues" in body


# ---------------------------------------------------------------------------
# Auth guards — unauthenticated
# ---------------------------------------------------------------------------

def test_list_faculty_unauthenticated() -> None:
    resp = client.get(BASE_URL)
    assert resp.status_code in (401, 403)


def test_create_faculty_unauthenticated() -> None:
    resp = client.post(BASE_URL, json=_VALID_PAYLOAD)
    assert resp.status_code in (401, 403)


def test_update_faculty_unauthenticated() -> None:
    resp = client.put(f"{BASE_URL}/1", json=_VALID_PAYLOAD)
    assert resp.status_code in (401, 403)


def test_delete_faculty_unauthenticated() -> None:
    resp = client.delete(f"{BASE_URL}/1")
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Auth guards — viewer role (no write permission)
# ---------------------------------------------------------------------------

def test_create_faculty_viewer_blocked() -> None:
    resp = client.post(BASE_URL, headers=VIEWER_HEADERS, json=_VALID_PAYLOAD)
    assert resp.status_code == 403


def test_update_faculty_viewer_blocked() -> None:
    resp = client.put(f"{BASE_URL}/1", headers=VIEWER_HEADERS, json=_VALID_PAYLOAD)
    assert resp.status_code == 403


def test_delete_faculty_viewer_blocked() -> None:
    resp = client.delete(f"{BASE_URL}/1", headers=VIEWER_HEADERS)
    assert resp.status_code == 403
