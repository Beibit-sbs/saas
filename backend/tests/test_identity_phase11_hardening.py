from __future__ import annotations

from contextlib import contextmanager
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any

import pytest

from app.core.errors import DependencyUnavailableError
from app.modules.auth.token_service import create_access_token
from app.modules.identity import phase1_service
from app.modules.identity.identity_errors import (
    IdentityGroupFetchFailed,
    IdentityInvalidCredentials,
    IdentityLdapBindFailed,
    IdentityLdapConnectFailed,
    IdentityMappingEmpty,
    IdentityProviderDisabled,
    IdentityProviderNotFound,
    IdentityProviderUnavailable,
)
from tests.conftest import ADMIN_HEADERS, client


def _tenant_admin_headers(tenant_id: int) -> dict[str, str]:
    token = create_access_token(
        user_id=f"tenant-{tenant_id}-admin@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
    )
    return {"Authorization": f"Bearer {token}"}


def _create_tenant(slug: str) -> int:
    response = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": slug, "name": slug, "status": "active"},
    )
    assert response.status_code == 200, response.text
    return int(response.json()["tenant"]["id"])


@pytest.mark.parametrize(
    ("raised", "expected_status", "expected_code"),
    [
        (IdentityInvalidCredentials(), 401, "IDENTITY_INVALID_CREDENTIALS"),
        (IdentityProviderDisabled(), 403, "IDENTITY_PROVIDER_DISABLED"),
        (IdentityProviderUnavailable(), 503, "IDENTITY_PROVIDER_UNAVAILABLE"),
        (IdentityMappingEmpty(), 403, "IDENTITY_MAPPING_EMPTY"),
    ],
)
def test_identity_login_errors_are_typed_and_stable(monkeypatch: pytest.MonkeyPatch, raised: Exception, expected_status: int, expected_code: str) -> None:
    def _raise(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise raised

    monkeypatch.setattr("app.modules.auth.router.authenticate_tenant_login", _raise)

    response = client.post(
        "/api/auth/login",
        json={"login": "identity.user", "password": "bad-password"},
    )

    assert response.status_code == expected_status, response.text
    assert response.json()["detail"]["code"] == expected_code
    assert "message" in response.json()["detail"]


def test_identity_login_dependency_unavailable_is_typed_503(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise DependencyUnavailableError("identity database unavailable")

    monkeypatch.setattr("app.modules.auth.router.authenticate_tenant_login", _raise)

    response = client.post(
        "/api/auth/login",
        json={"login": "identity.user", "password": "bad-password"},
    )

    assert response.status_code == 503, response.text
    assert response.json()["detail"]["code"] == "IDENTITY_PROVIDER_UNAVAILABLE"
    assert response.json()["detail"]["message"] == "identity database unavailable"


def test_identity_login_never_leaks_raw_internal_exception_details(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise IdentityProviderUnavailable(details="LDAPSocketOpenError connection refused 10.0.0.1")

    monkeypatch.setattr("app.modules.auth.router.authenticate_tenant_login", _raise)

    response = client.post(
        "/api/auth/login",
        json={"login": "identity.user", "password": "bad-password"},
    )

    assert response.status_code == 503, response.text
    body = response.json()["detail"]
    assert body["code"] == "IDENTITY_PROVIDER_UNAVAILABLE"
    assert body["message"] == "identity provider is unavailable"
    assert "LDAPSocketOpenError" not in str(body)


@pytest.mark.parametrize(
    ("raised", "expected_status", "expected_code"),
    [
        (IdentityProviderNotFound(), 404, "IDENTITY_PROVIDER_NOT_FOUND"),
        (IdentityProviderDisabled(), 403, "IDENTITY_PROVIDER_DISABLED"),
        (IdentityLdapConnectFailed(), 503, "IDENTITY_LDAP_CONNECT_FAILED"),
        (IdentityLdapBindFailed(), 401, "IDENTITY_LDAP_BIND_FAILED"),
        (IdentityInvalidCredentials(), 401, "IDENTITY_INVALID_CREDENTIALS"),
        (IdentityGroupFetchFailed(), 503, "IDENTITY_GROUP_FETCH_FAILED"),
        (IdentityMappingEmpty(), 403, "IDENTITY_MAPPING_EMPTY"),
        (IdentityProviderUnavailable(), 503, "IDENTITY_PROVIDER_UNAVAILABLE"),
    ],
)
def test_identity_provider_test_maps_typed_identity_errors(monkeypatch: pytest.MonkeyPatch, raised: Exception, expected_status: int, expected_code: str) -> None:
    def _raise(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise raised

    monkeypatch.setattr("app.modules.identity.phase1_router.test_directory_provider", _raise)

    response = client.post(
        "/api/identity/providers/9/test",
        json={"login": "u", "password": "p"},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == expected_status, response.text
    assert response.json()["detail"]["code"] == expected_code
    assert "message" in response.json()["detail"]


def test_identity_provider_test_maps_dependency_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise DependencyUnavailableError("identity backend unavailable")

    monkeypatch.setattr("app.modules.identity.phase1_router.test_directory_provider", _raise)

    response = client.post(
        "/api/identity/providers/9/test",
        json={"login": "u", "password": "p"},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 503, response.text
    assert response.json()["detail"] == {
        "code": "IDENTITY_PROVIDER_UNAVAILABLE",
        "message": "identity backend unavailable",
    }


def test_provider_policy_explicit_provider_selection_works(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeConn:
        def commit(self) -> None:
            return None

    @contextmanager
    def _fake_conn():
        yield _FakeConn()

    seen: dict[str, Any] = {}

    provider = phase1_service.IdentityProviderRecord(
        id=10,
        tenant_id=1,
        type="ldap",
        name="corp-main",
        is_enabled=True,
        config_json={},
        created_at="",
        updated_at="",
        mapping_count=0,
        has_bind_password=True,
        is_default=False,
        priority=100,
        allow_local_login=False,
        allow_external_login=True,
        login_hint="",
        auto_provision=True,
        require_mapping=True,
    )

    def _resolve(conn: Any, *, tenant_id: int, provider_name: str | None):
        seen["provider_name"] = provider_name
        return provider, "enc-secret"

    monkeypatch.setattr(phase1_service, "_conn", _fake_conn)
    monkeypatch.setattr(phase1_service, "_resolve_provider_for_login", _resolve)
    monkeypatch.setattr(phase1_service, "_check_rate_limit", lambda **_kwargs: None)
    monkeypatch.setattr(phase1_service, "_check_account_lock", lambda **_kwargs: None)
    monkeypatch.setattr(phase1_service, "_clear_failed_login", lambda **_kwargs: None)
    monkeypatch.setattr(phase1_service, "_record_failed_login", lambda **_kwargs: None)
    monkeypatch.setattr(
        phase1_service,
        "_authenticate_via_provider",
        lambda *_args, **_kwargs: {
            "user_id": "u1",
            "display_name": "U1",
            "roles": ["auditor"],
            "language": "ru",
            "auth_source": "ldap",
            "sync_with_ad": True,
            "provider": "corp-main",
        },
    )

    result = phase1_service.authenticate_tenant_login(
        tenant_id=1,
        login="corp.user",
        password="pass",
        provider_name="corp-main",
    )

    assert seen["provider_name"] == "corp-main"
    assert result["auth_source"] == "ldap"


def test_provider_policy_default_provider_selection_works(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeConn:
        def commit(self) -> None:
            return None

    @contextmanager
    def _fake_conn():
        yield _FakeConn()

    seen: dict[str, Any] = {}

    provider = phase1_service.IdentityProviderRecord(
        id=11,
        tenant_id=1,
        type="ldap",
        name="corp-default",
        is_enabled=True,
        config_json={},
        created_at="",
        updated_at="",
        mapping_count=0,
        has_bind_password=True,
        is_default=True,
        priority=1,
        allow_local_login=False,
        allow_external_login=True,
        login_hint="",
        auto_provision=True,
        require_mapping=True,
    )

    def _resolve(conn: Any, *, tenant_id: int, provider_name: str | None):
        seen["provider_name"] = provider_name
        return provider, "enc-secret"

    monkeypatch.setattr(phase1_service, "_conn", _fake_conn)
    monkeypatch.setattr(phase1_service, "_resolve_provider_for_login", _resolve)
    monkeypatch.setattr(phase1_service, "_check_rate_limit", lambda **_kwargs: None)
    monkeypatch.setattr(phase1_service, "_check_account_lock", lambda **_kwargs: None)
    monkeypatch.setattr(phase1_service, "_clear_failed_login", lambda **_kwargs: None)
    monkeypatch.setattr(phase1_service, "_record_failed_login", lambda **_kwargs: None)
    monkeypatch.setattr(
        phase1_service,
        "_authenticate_via_provider",
        lambda *_args, **_kwargs: {
            "user_id": "u2",
            "display_name": "U2",
            "roles": ["auditor"],
            "language": "ru",
            "auth_source": "ldap",
            "sync_with_ad": True,
            "provider": "corp-default",
        },
    )

    result = phase1_service.authenticate_tenant_login(
        tenant_id=1,
        login="corp.user",
        password="pass",
        provider_name=None,
    )

    assert seen["provider_name"] is None
    assert result["provider"] == "corp-default"


def test_authenticate_tenant_login_falls_back_to_local_when_identity_db_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        phase1_service,
        "_conn",
        lambda: (_ for _ in ()).throw(DependencyUnavailableError("identity database unavailable")),
    )
    monkeypatch.setattr(phase1_service, "_check_rate_limit", lambda **_kwargs: None)
    monkeypatch.setattr(phase1_service, "_check_account_lock", lambda **_kwargs: None)
    monkeypatch.setattr(phase1_service, "_clear_failed_login", lambda **_kwargs: None)
    monkeypatch.setattr(phase1_service, "_authenticate_local", lambda *_args, **_kwargs: {
        "user_id": "local.777",
        "display_name": "Local Pilot",
        "roles": ["teacher"],
        "language": "ru",
        "auth_source": "local",
        "sync_with_ad": False,
    })

    result = phase1_service.authenticate_tenant_login(
        tenant_id=1,
        login="pilot-local",
        password="secret",
    )

    assert result["user_id"] == "local.777"
    assert result["roles"] == ["teacher"]


def test_provider_policy_disabled_provider_blocks_login(monkeypatch: pytest.MonkeyPatch) -> None:
    @contextmanager
    def _fake_conn():
        yield object()

    disabled_provider = phase1_service.IdentityProviderRecord(
        id=12,
        tenant_id=1,
        type="ldap",
        name="corp-disabled",
        is_enabled=False,
        config_json={},
        created_at="",
        updated_at="",
        mapping_count=0,
        has_bind_password=True,
        is_default=False,
        priority=100,
        allow_local_login=False,
        allow_external_login=True,
        login_hint="",
        auto_provision=True,
        require_mapping=True,
    )

    monkeypatch.setattr(phase1_service, "_conn", _fake_conn)
    monkeypatch.setattr(
        phase1_service,
        "_resolve_provider_for_login",
        lambda *_args, **_kwargs: (disabled_provider, "enc-secret"),
    )
    monkeypatch.setattr(phase1_service, "_check_rate_limit", lambda **_kwargs: None)
    monkeypatch.setattr(phase1_service, "_check_account_lock", lambda **_kwargs: None)

    with pytest.raises(IdentityProviderDisabled):
        phase1_service.authenticate_tenant_login(
            tenant_id=1,
            login="corp.user",
            password="pass",
            provider_name="corp-disabled",
        )


def test_provider_policy_require_mapping_is_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = phase1_service.IdentityProviderRecord(
        id=13,
        tenant_id=1,
        type="ldap",
        name="corp-mapped",
        is_enabled=True,
        config_json={},
        created_at="",
        updated_at="",
        mapping_count=0,
        has_bind_password=True,
        is_default=False,
        priority=100,
        allow_local_login=False,
        allow_external_login=True,
        login_hint="",
        auto_provision=True,
        require_mapping=True,
    )

    monkeypatch.setattr(
        phase1_service,
        "_ldap_search_groups",
        lambda **_kwargs: ("corp.user", "Corp User", "ext-1", "corp@example.com", ["CN=GroupA"]),
    )
    monkeypatch.setattr(phase1_service, "_group_roles", lambda *_args, **_kwargs: [])

    with pytest.raises(IdentityMappingEmpty):
        phase1_service._authenticate_via_provider(
            conn=object(),
            tenant_id=1,
            provider=provider,
            secret_enc="plain-secret",
            login="corp.user",
            password="pass",
        )


def test_mapping_api_crud_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    state: dict[int, dict[str, Any]] = {}

    def _create(*, tenant_id: int, provider_id: int, external_group: str, platform_role: str) -> dict[str, Any]:
        mapping = {
            "id": 1,
            "tenant_id": tenant_id,
            "provider_id": provider_id,
            "external_group": external_group,
            "platform_role": platform_role,
        }
        state[1] = mapping
        return mapping

    def _list(*, tenant_id: int, provider_id: int | None = None) -> list[dict[str, Any]]:
        return [row for row in state.values() if row["tenant_id"] == tenant_id and (provider_id is None or row["provider_id"] == provider_id)]

    def _update(*, tenant_id: int, mapping_id: int, external_group: str, platform_role: str) -> dict[str, Any]:
        row = dict(state[mapping_id])
        row["tenant_id"] = tenant_id
        row["external_group"] = external_group
        row["platform_role"] = platform_role
        state[mapping_id] = row
        return row

    def _delete(*, tenant_id: int, mapping_id: int) -> bool:
        row = state.get(mapping_id)
        if row is None or row["tenant_id"] != tenant_id:
            return False
        del state[mapping_id]
        return True

    monkeypatch.setattr("app.modules.identity.phase1_router.create_identity_mapping", _create)
    monkeypatch.setattr("app.modules.identity.phase1_router.list_identity_mappings", _list)
    monkeypatch.setattr("app.modules.identity.phase1_router.update_identity_mapping", _update)
    monkeypatch.setattr("app.modules.identity.phase1_router.delete_identity_mapping", _delete)

    create_response = client.post(
        "/api/identity/mappings",
        headers=ADMIN_HEADERS,
        json={"provider_id": 7, "external_group": "CN=Finance", "platform_role": "auditor"},
    )
    assert create_response.status_code == 200, create_response.text
    assert create_response.json()["mapping"]["external_group"] == "CN=Finance"

    list_response = client.get("/api/identity/mappings?provider_id=7", headers=ADMIN_HEADERS)
    assert list_response.status_code == 200, list_response.text
    assert len(list_response.json()["mappings"]) == 1

    update_response = client.put(
        "/api/identity/mappings/1",
        headers=ADMIN_HEADERS,
        json={"external_group": "CN=Finance-Updated", "platform_role": "admin"},
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["mapping"]["platform_role"] == "admin"

    delete_response = client.delete("/api/identity/mappings/1", headers=ADMIN_HEADERS)
    assert delete_response.status_code == 200, delete_response.text
    assert delete_response.json()["deleted"] is True


def test_mapping_api_enforces_tenant_isolation(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = _create_tenant("tenant-phase11")
    seen: dict[str, int] = {}

    def _list(*, tenant_id: int, provider_id: int | None = None) -> list[dict[str, Any]]:
        seen["tenant_id"] = tenant_id
        return []

    monkeypatch.setattr("app.modules.identity.phase1_router.list_identity_mappings", _list)

    response = client.get("/api/identity/mappings", headers=_tenant_admin_headers(tenant_id))

    assert response.status_code == 200, response.text
    assert seen["tenant_id"] == tenant_id


def test_mapping_preview_shows_expected_roles(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.modules.identity.phase1_router.preview_provider_mapping",
        lambda **_kwargs: {
            "provider_id": 7,
            "username": "corp.user",
            "display_name": "Corp User",
            "external_user_id": "ext-1",
            "email": "corp@example.com",
            "groups": ["CN=Finance"],
            "mapped_roles": ["auditor"],
            "mapping_empty": False,
        },
    )

    response = client.post(
        "/api/identity/providers/7/mapping/preview",
        headers=ADMIN_HEADERS,
        json={"username": "corp.user"},
    )

    assert response.status_code == 200, response.text
    preview = response.json()["preview"]
    assert preview["mapped_roles"] == ["auditor"]
    assert preview["mapping_empty"] is False


def test_mapping_preview_provider_unavailable_returns_typed_503(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise DependencyUnavailableError("preview backend unavailable")

    monkeypatch.setattr("app.modules.identity.phase1_router.preview_provider_mapping", _raise)

    response = client.post(
        "/api/identity/providers/7/mapping/preview",
        headers=ADMIN_HEADERS,
        json={"username": "corp.user"},
    )

    assert response.status_code == 503, response.text
    assert response.json()["detail"] == {
        "code": "IDENTITY_PROVIDER_UNAVAILABLE",
        "message": "preview backend unavailable",
    }


def test_legacy_migration_contains_phase11_policy_and_secret_migration_contract() -> None:
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "e1f2a3b4c5d6_identity_phase11_hardening_policy_and_legacy_ldap_migration.py"
    )
    assert migration_path.exists()

    migration_text = migration_path.read_text(encoding="utf-8")
    for token in (
        '"is_default"',
        '"priority"',
        '"allow_local_login"',
        '"allow_external_login"',
        '"login_hint"',
        '"auto_provision"',
        '"require_mapping"',
        "app_identity_provider_secrets",
        "bind_password_enc",
        "tenant:%:ldap.%",
        "_insert_legacy_provider(conn, tenant_id=int(tenant_id), settings=settings)",
    ):
        assert token in migration_text


def test_legacy_migration_parses_tenant_scoped_legacy_keys() -> None:
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "e1f2a3b4c5d6_identity_phase11_hardening_policy_and_legacy_ldap_migration.py"
    )
    spec = spec_from_file_location("identity_phase11_migration", migration_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module._tenant_id_from_key("tenant:1:ldap.server_uri") == 1
    assert module._tenant_id_from_key("tenant:42:ldap.bind_dn") == 42
    assert module._tenant_id_from_key("tenant:0:ldap.bind_dn") is None
    assert module._tenant_id_from_key("tenant:1:oidc.client_id") is None
