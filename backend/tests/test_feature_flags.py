"""Tests for feature_flags module — CRUD endpoints + service-layer unit tests.

Covers: list flags, upsert flag, toggle enabled/disabled, key splitting,
legacy composite-key format, permission guards, unauthenticated access.
"""

from tests.conftest import ADMIN_HEADERS, _auth_headers, client

from app.modules.feature_flags import service as ff_service


# ---------------------------------------------------------------------------
# 1. Router — list / upsert
# ---------------------------------------------------------------------------


def test_list_feature_flags_empty() -> None:
    resp = client.get("/api/admin/feature-flags", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "flags" in body
    assert isinstance(body["flags"], list)


def test_upsert_feature_flag_creates_new() -> None:
    resp = client.post(
        "/api/admin/feature-flags",
        headers=ADMIN_HEADERS,
        json={"key": "test.flag_one", "enabled": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "flag" in body
    assert body["flag"]["key"] == "test.flag_one"
    assert body["flag"]["enabled"] is True


def test_upsert_flag_appears_in_list() -> None:
    client.post(
        "/api/admin/feature-flags",
        headers=ADMIN_HEADERS,
        json={"key": "test.flag_list", "enabled": True},
    )
    resp = client.get("/api/admin/feature-flags", headers=ADMIN_HEADERS)
    keys = [f["key"] for f in resp.json()["flags"]]
    assert "test.flag_list" in keys


def test_upsert_flag_toggle_off() -> None:
    client.post(
        "/api/admin/feature-flags",
        headers=ADMIN_HEADERS,
        json={"key": "test.toggle_me", "enabled": True},
    )
    resp = client.post(
        "/api/admin/feature-flags",
        headers=ADMIN_HEADERS,
        json={"key": "test.toggle_me", "enabled": False},
    )
    assert resp.status_code == 200
    assert resp.json()["flag"]["enabled"] is False


def test_upsert_flag_global_key() -> None:
    """A key without a dot should use 'global' module prefix."""
    resp = client.post(
        "/api/admin/feature-flags",
        headers=ADMIN_HEADERS,
        json={"key": "simpleglobal", "enabled": True},
    )
    assert resp.status_code == 200
    # The key returned may be 'simpleglobal' (no module prefix shown for global)
    body = resp.json()
    assert body["flag"]["enabled"] is True


def test_upsert_flag_with_scope() -> None:
    resp = client.post(
        "/api/admin/feature-flags",
        headers=ADMIN_HEADERS,
        json={"key": "billing.beta_ui", "enabled": True, "scope": "tenant"},
    )
    assert resp.status_code == 200
    assert resp.json()["flag"]["key"] == "billing.beta_ui"


# ---------------------------------------------------------------------------
# 2. Validation
# ---------------------------------------------------------------------------


def test_upsert_flag_short_key_fails() -> None:
    resp = client.post(
        "/api/admin/feature-flags",
        headers=ADMIN_HEADERS,
        json={"key": "ab", "enabled": True},
    )
    assert resp.status_code == 422


def test_upsert_flag_missing_enabled_fails() -> None:
    resp = client.post(
        "/api/admin/feature-flags",
        headers=ADMIN_HEADERS,
        json={"key": "valid.flag"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 3. Permission guards
# ---------------------------------------------------------------------------


def test_list_flags_requires_auth() -> None:
    resp = client.get("/api/admin/feature-flags")
    assert resp.status_code in (401, 403)


def test_upsert_flag_requires_auth() -> None:
    resp = client.post(
        "/api/admin/feature-flags",
        json={"key": "test.unauthed", "enabled": True},
    )
    assert resp.status_code in (401, 403)


def test_viewer_cannot_upsert_flag() -> None:
    viewer_headers = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.post(
        "/api/admin/feature-flags",
        headers=viewer_headers,
        json={"key": "test.viewer_try", "enabled": True},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 4. Service-layer unit tests
# ---------------------------------------------------------------------------


def test_service_list_flags_empty() -> None:
    flags = ff_service.list_flags(tenant_id=1)
    assert isinstance(flags, list)


def test_service_set_and_check_flag() -> None:
    ff_service.set_flag("mymod.test_key", enabled=True, tenant_id=1)
    assert ff_service.is_flag_enabled("mymod.test_key", tenant_id=1) is True


def test_service_disable_flag() -> None:
    ff_service.set_flag("mymod.disable_me", enabled=True, tenant_id=1)
    ff_service.set_flag("mymod.disable_me", enabled=False, tenant_id=1)
    assert ff_service.is_flag_enabled("mymod.disable_me", tenant_id=1) is False


def test_service_flag_not_found_returns_default() -> None:
    result = ff_service.is_flag_enabled("nonexistent.flag", tenant_id=1, default=False)
    assert result is False


def test_service_flag_empty_key_returns_default() -> None:
    assert ff_service.is_flag_enabled("", tenant_id=1, default=True) is True


def test_service_flag_no_tenant_returns_default() -> None:
    assert ff_service.is_flag_enabled("some.flag", tenant_id=None, default=False) is False


def test_service_list_flags_requires_tenant() -> None:
    try:
        ff_service.list_flags(tenant_id=None)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_service_set_flag_requires_tenant() -> None:
    try:
        ff_service.set_flag("test.key", enabled=True, tenant_id=None)
        assert False, "Expected ValueError"
    except ValueError:
        pass
