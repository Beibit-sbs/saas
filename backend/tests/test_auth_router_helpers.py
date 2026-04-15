from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

import app.modules.auth.router as auth_router


def _request(path: str = "/api/auth/me", *, headers: dict[str, str] | None = None) -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "https",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": b"",
        "headers": [
            (k.lower().encode("utf-8"), v.encode("utf-8")) for k, v in (headers or {}).items()
        ],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 443),
    }
    return Request(scope)


def test_require_tenant_id_branches() -> None:
    assert auth_router._require_tenant_id("1", operation="x") == 1
    with pytest.raises(HTTPException):
        auth_router._require_tenant_id(None, operation="x")
    with pytest.raises(HTTPException):
        auth_router._require_tenant_id("bad", operation="x")
    with pytest.raises(HTTPException):
        auth_router._require_tenant_id("0", operation="x")


def test_resolve_tenant_for_auth_entrypoint_missing_header() -> None:
    with pytest.raises(HTTPException) as exc:
        auth_router._resolve_tenant_for_auth_entrypoint(None)
    assert exc.value.status_code == 400


def test_resolve_tenant_for_auth_entrypoint_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth_router, "get_tenant", lambda tenant_id: None)
    with pytest.raises(HTTPException) as exc:
        auth_router._resolve_tenant_for_auth_entrypoint("9")
    assert exc.value.status_code == 404


def test_resolve_tenant_for_auth_entrypoint_inactive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth_router, "get_tenant", lambda tenant_id: {"id": tenant_id, "status": "suspended"})
    with pytest.raises(HTTPException) as exc:
        auth_router._resolve_tenant_for_auth_entrypoint("9")
    assert exc.value.status_code == 403


def test_resolve_tenant_for_auth_entrypoint_success(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = {"id": 2, "status": "active", "name": "Tenant"}
    monkeypatch.setattr(auth_router, "get_tenant", lambda tenant_id: expected)
    assert auth_router._resolve_tenant_for_auth_entrypoint("2") == expected


def test_validate_tenant_consistency_invalid_header() -> None:
    claims = SimpleNamespace(tenant_id=1, user_id="u1")
    with pytest.raises(HTTPException) as exc:
        auth_router._validate_tenant_consistency(claims, "bad", _request())
    assert exc.value.status_code == 400


def test_validate_tenant_consistency_mismatch_records_signal(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[dict[str, object]] = []

    def _record(**kwargs):
        seen.append(kwargs)

    monkeypatch.setattr(auth_router, "record_security_signal", _record)
    claims = SimpleNamespace(tenant_id=1, user_id="u1")
    with pytest.raises(HTTPException) as exc:
        auth_router._validate_tenant_consistency(claims, "2", _request("/api/auth/me"))
    assert exc.value.status_code == 403
    assert seen and seen[0]["signal"] == "auth.tenant_override_attempt"


def test_validate_tenant_consistency_same_tenant_no_error() -> None:
    claims = SimpleNamespace(tenant_id=7, user_id="u1")
    auth_router._validate_tenant_consistency(claims, "7", _request())


@pytest.mark.parametrize(
    ("ua", "expected"),
    [
        ("Mozilla/5.0 Windows Edg/120", "Windows (Edge)"),
        ("Mozilla/5.0 Windows Firefox", "Windows (Firefox)"),
        ("Mozilla/5.0 Windows Chrome", "Windows (Chrome)"),
        ("Mozilla/5.0 Windows", "Windows"),
        ("Mozilla/5.0 Macintosh Safari", "macOS (Safari)"),
        ("Mozilla/5.0 Macintosh Chrome Safari", "macOS"),
        ("Mozilla/5.0 Linux", "Linux"),
        ("Mozilla/5.0 iPhone", "iOS"),
        ("Mozilla/5.0 Android", "Android"),
        ("SomeAgent", "Unknown Device"),
    ],
)
def test_extract_device_name_from_ua_branches(ua: str, expected: str) -> None:
    assert auth_router._extract_device_name_from_ua(ua) == expected


def test_token_permissions_for_roles_empty_and_error(monkeypatch: pytest.MonkeyPatch) -> None:
    assert auth_router._token_permissions_for_roles(roles=[], tenant_id=1) == []

    def _boom(_roles, _tenant):
        raise RuntimeError("boom")

    monkeypatch.setattr(auth_router, "resolve_permissions_for_tenant", _boom)
    assert auth_router._token_permissions_for_roles(roles=["admin"], tenant_id=1) == []


def test_token_permissions_for_roles_sorted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth_router, "resolve_permissions_for_tenant", lambda _roles, _tenant: {"b", "a"})
    assert auth_router._token_permissions_for_roles(roles=["admin"], tenant_id=1) == ["a", "b"]


def test_resolve_authoritative_permissions_claims_precedence() -> None:
    claims = SimpleNamespace(permissions=["p2", "p1", "p1"])
    result = auth_router._resolve_authoritative_permissions(claims=claims, roles=["admin"], tenant_id=1)
    assert result == ["p1", "p2"]


def test_resolve_authoritative_permissions_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth_router, "_token_permissions_for_roles", lambda **_: ["fallback"])
    result = auth_router._resolve_authoritative_permissions(
        claims=SimpleNamespace(permissions=[]),
        roles=["admin"],
        tenant_id=1,
    )
    assert result == ["fallback"]


def test_session_payload_shape() -> None:
    payload = auth_router._session_payload(
        user_id="u1",
        display_name="User",
        roles=["admin"],
        language="ru",
        auth_source="local",
        sync_with_ad=False,
    )
    assert payload["user_id"] == "u1"
    assert payload["display_name"] == "User"
    assert payload["roles"] == ["admin"]
    assert payload["language"] == "ru"
