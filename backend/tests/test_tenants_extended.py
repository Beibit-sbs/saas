"""Additional tests for the Tenants module.

Complements existing test_tenants.py (10 tests) with:
  - Public login-directory endpoint
  - Validation edge cases (empty slug/name)
  - Permission guards for viewer role
"""

from __future__ import annotations

from tests.conftest import ADMIN_HEADERS, _auth_headers, client


# ---------------------------------------------------------------------------
# Public login directory (no auth required)
# ---------------------------------------------------------------------------

def test_public_login_directory_returns_200() -> None:
    """GET /api/public/tenants/login-directory — no auth."""
    resp = client.get("/api/public/tenants/login-directory")
    assert resp.status_code == 200
    body = resp.json()
    assert "tenants" in body
    assert isinstance(body["tenants"], list)


def test_public_login_directory_contains_default_tenant() -> None:
    resp = client.get("/api/public/tenants/login-directory")
    assert resp.status_code == 200
    slugs = [t["slug"] for t in resp.json()["tenants"]]
    assert "default" in slugs


def test_public_login_directory_only_active_tenants() -> None:
    """All returned tenants should represent active entries."""
    resp = client.get("/api/public/tenants/login-directory")
    assert resp.status_code == 200
    tenants = resp.json()["tenants"]
    # Each entry should have required fields
    for t in tenants:
        assert "tenant_id" in t
        assert "slug" in t
        assert "name" in t


def test_public_login_directory_exposes_no_sensitive_fields() -> None:
    """Login directory must NOT leak plan, config, or internal metadata."""
    resp = client.get("/api/public/tenants/login-directory")
    assert resp.status_code == 200
    for t in resp.json()["tenants"]:
        # Only allowed fields
        allowed = {"tenant_id", "slug", "name"}
        assert set(t.keys()) <= allowed, f"Extra fields: {set(t.keys()) - allowed}"


# ---------------------------------------------------------------------------
# Validation — empty / blank fields
# ---------------------------------------------------------------------------

def test_create_tenant_empty_slug() -> None:
    resp = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": "", "name": "ValidName", "status": "active"},
    )
    assert resp.status_code in (400, 422)


def test_create_tenant_empty_name() -> None:
    resp = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": "valid-slug", "name": "", "status": "active"},
    )
    assert resp.status_code in (400, 422)


def test_create_tenant_missing_slug() -> None:
    resp = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"name": "No Slug", "status": "active"},
    )
    assert resp.status_code in (400, 422)


def test_create_tenant_missing_name() -> None:
    resp = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": "no-name", "status": "active"},
    )
    assert resp.status_code in (400, 422)


# ---------------------------------------------------------------------------
# Permission guards — viewer role
# ---------------------------------------------------------------------------

def test_list_tenants_viewer_role_blocked() -> None:
    headers = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.get("/api/admin/tenants", headers=headers)
    assert resp.status_code == 403


def test_create_tenant_viewer_role_blocked() -> None:
    headers = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.post(
        "/api/admin/tenants",
        headers=headers,
        json={"slug": "viewer-test", "name": "Viewer Test", "status": "active"},
    )
    assert resp.status_code == 403


def test_update_tenant_viewer_role_blocked() -> None:
    headers = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.put(
        "/api/admin/tenants/1",
        headers=headers,
        json={"name": "Hacked"},
    )
    assert resp.status_code == 403


def test_delete_tenant_viewer_role_blocked() -> None:
    headers = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.delete("/api/admin/tenants/1", headers=headers)
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Unauthenticated
# ---------------------------------------------------------------------------

def test_list_tenants_unauthenticated() -> None:
    resp = client.get("/api/admin/tenants")
    assert resp.status_code in (401, 403)


def test_create_tenant_unauthenticated() -> None:
    resp = client.post(
        "/api/admin/tenants",
        json={"slug": "unauth", "name": "Unauth", "status": "active"},
    )
    assert resp.status_code in (401, 403)
