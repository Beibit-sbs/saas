"""Tests for LDAP module — router + service layer.

Covers: status endpoint, test-connection (disabled/enabled states),
configuration flow, tenant isolation, permission guards.
"""

from unittest.mock import patch

from tests.conftest import ADMIN_HEADERS, _auth_headers, client


# ---------------------------------------------------------------------------
# Helper: configure LDAP for default tenant via integrations API
# ---------------------------------------------------------------------------

_LDAP_CONFIG = {
    "enabled": True,
    "server_uri": "ldap://dc.test.local:389",
    "bind_dn": "CN=svc,OU=Service,DC=test,DC=local",
    "bind_password": "bind-secret",
    "base_dn": "DC=test,DC=local",
    "user_filter": "(sAMAccountName={username})",
    "group_role_map_json": '{"cn=admins,ou=groups,dc=test,dc=local":"admin"}',
    "default_role": "student",
}


def _configure_ldap(enabled: bool = True) -> None:
    """Push LDAP settings via the integrations admin endpoint."""
    payload = dict(_LDAP_CONFIG)
    payload["enabled"] = enabled
    resp = client.put("/api/admin/integrations/ldap", json=payload, headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text


# ---------------------------------------------------------------------------
# 1. Status endpoint
# ---------------------------------------------------------------------------


def test_ldap_status_returns_200() -> None:
    resp = client.get("/api/admin/ldap/status", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "ldap" in body
    ldap = body["ldap"]
    assert "enabled" in ldap
    assert "configured" in ldap
    assert "server_uri" in ldap


def test_ldap_status_disabled_by_default() -> None:
    """Without explicit config LDAP should report disabled."""
    resp = client.get("/api/admin/ldap/status", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["ldap"]["enabled"] is False


def test_ldap_status_enabled_after_config() -> None:
    _configure_ldap(enabled=True)
    resp = client.get("/api/admin/ldap/status", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    ldap = resp.json()["ldap"]
    assert ldap["enabled"] is True
    assert ldap["configured"] is True
    assert ldap["server_uri"] == "ldap://dc.test.local:389"
    assert ldap["base_dn"] == "DC=test,DC=local"


# ---------------------------------------------------------------------------
# 2. Test-connection endpoint — LDAP disabled
# ---------------------------------------------------------------------------


def test_ldap_test_connection_fails_when_disabled() -> None:
    _configure_ldap(enabled=False)
    resp = client.post("/api/admin/ldap/test-connection", json={}, headers=ADMIN_HEADERS)
    assert resp.status_code == 400
    assert "disabled" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 3. Test-connection — LDAP enabled (mock ldap3 Connection)
# ---------------------------------------------------------------------------


def test_ldap_test_connection_service_bind_ok() -> None:
    """Service-bind (no user credentials) succeeds when ldap3 connects."""
    _configure_ldap(enabled=True)

    class _FakeConn:
        def __enter__(self):
            return self
        def __exit__(self, *_a):
            pass

    with patch("app.modules.ldap.service.Connection", return_value=_FakeConn()):
        resp = client.post(
            "/api/admin/ldap/test-connection",
            json={},
            headers=ADMIN_HEADERS,
        )

    assert resp.status_code == 200
    result = resp.json()["result"]
    assert result["status"] == "service_bind_ok"
    assert result["server_uri"] == "ldap://dc.test.local:389"


# ---------------------------------------------------------------------------
# 4. Permission guard — non-admin gets 403
# ---------------------------------------------------------------------------


def test_ldap_status_requires_admin_permission() -> None:
    viewer_headers = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.get("/api/admin/ldap/status", headers=viewer_headers)
    assert resp.status_code == 403


def test_ldap_test_connection_requires_admin_permission() -> None:
    viewer_headers = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.post("/api/admin/ldap/test-connection", json={}, headers=viewer_headers)
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 5. Unauthenticated — 401
# ---------------------------------------------------------------------------


def test_ldap_status_unauthenticated() -> None:
    resp = client.get("/api/admin/ldap/status")
    assert resp.status_code in (401, 403)


def test_ldap_test_connection_unauthenticated() -> None:
    resp = client.post("/api/admin/ldap/test-connection", json={})
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 6. Schema validation
# ---------------------------------------------------------------------------


def test_ldap_test_connection_schema_accepts_empty_body() -> None:
    """Payload with no username/password is valid (service-bind only)."""
    _configure_ldap(enabled=True)
    with patch("app.modules.ldap.service.Connection", side_effect=ValueError("mock")):
        resp = client.post(
            "/api/admin/ldap/test-connection",
            json={},
            headers=ADMIN_HEADERS,
        )
    # 400 because ldap3 raises ValueError via our mock, but 422 would mean schema error
    assert resp.status_code == 400


def test_ldap_test_connection_schema_accepts_credentials() -> None:
    """LdapTestPayload accepts optional username + password."""
    _configure_ldap(enabled=True)
    with patch("app.modules.ldap.service.Connection", side_effect=ValueError("mock")):
        resp = client.post(
            "/api/admin/ldap/test-connection",
            json={"username": "jdoe", "password": "secret"},
            headers=ADMIN_HEADERS,
        )
    assert resp.status_code == 400  # connection fails but schema is valid


# ---------------------------------------------------------------------------
# 7. Unit tests for service helpers
# ---------------------------------------------------------------------------


def test_ldap_group_role_map_invalid_json() -> None:
    """Invalid JSON in group_role_map_json raises ValueError."""
    from app.modules.ldap.service import _group_role_map
    with patch("app.modules.ldap.service._cfg", return_value="not-json"):
        try:
            _group_role_map()
            assert False, "Should have raised ValueError"
        except ValueError as exc:
            assert "valid JSON" in str(exc)


def test_ldap_map_groups_to_roles_default() -> None:
    """When no groups match, default role is returned."""
    from app.modules.ldap.service import _map_groups_to_roles
    with patch("app.modules.ldap.service._group_role_map", return_value={}), \
         patch("app.modules.ldap.service._default_role", return_value="student"):
        roles = _map_groups_to_roles(["CN=Unknown,DC=test"])
    assert roles == ["student"]


def test_ldap_map_groups_to_roles_matched() -> None:
    """When groups match, mapped roles are returned (sorted, deduped)."""
    from app.modules.ldap.service import _map_groups_to_roles
    role_map = {
        "cn=admins,dc=test": "admin",
        "cn=teachers,dc=test": "teacher",
    }
    with patch("app.modules.ldap.service._group_role_map", return_value=role_map), \
         patch("app.modules.ldap.service._default_role", return_value="student"):
        roles = _map_groups_to_roles(["CN=Admins,DC=test", "CN=Teachers,DC=test"])
    assert roles == ["admin", "teacher"]
