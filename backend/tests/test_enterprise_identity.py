import base64
import hmac
import hashlib
import struct
import time

import pytest

from app.modules.auth.token_service import create_access_token
from app.modules.auth.local_users_service import local_user_store
from tests.conftest import ADMIN_HEADERS, _auth_headers, client


pytestmark = pytest.mark.security_regression


def _totp(secret: str, for_time: int | None = None, step_seconds: int = 30, digits: int = 6) -> str:
    normalized = secret.strip().upper().replace(" ", "")
    padding = "=" * ((8 - len(normalized) % 8) % 8)
    key = base64.b32decode(normalized + padding, casefold=True)
    ts = int(time.time()) if for_time is None else int(for_time)
    counter = ts // step_seconds
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code_int = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(code_int % (10 ** digits)).zfill(digits)


def _create_tenant_b() -> int:
    response = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": "tenant-b-identity", "name": "Tenant B Identity", "status": "active"},
    )
    assert response.status_code == 200, response.text
    return int(response.json()["tenant"]["id"])


def _csrf_headers() -> dict[str, str]:
    csrf = client.get("/api/auth/csrf")
    assert csrf.status_code == 200, csrf.text
    return {"X-CSRF-Token": str(csrf.json()["csrf_token"])}


def _ensure_local_user(login: str, password: str, roles: list[str], display_name: str) -> None:
    if local_user_store.find_user_by_login(login) is not None:
        return
    local_user_store.create_user(
        login=login,
        password=password,
        display_name=display_name,
        roles=roles,
        default_language="ru",
        tenant_id=1,
    )


def test_mfa_enable_and_login_enforcement() -> None:
    create_local = client.post(
        "/api/admin/local-users",
        headers=ADMIN_HEADERS,
        json={
            "login": "mfa.local.user",
            "password": "mfa12345",
            "display_name": "MFA Local User",
            "roles": ["auditor"],
            "default_language": "en",
        },
    )
    assert create_local.status_code == 200, create_local.text

    client.cookies.clear()
    _ensure_local_user("mfa.local.user", "mfa12345", ["auditor"], "MFA Local User")
    login = client.post(
        "/api/auth/login",
        json={"login": "mfa.local.user", "password": "mfa12345"},
        headers={"X-Tenant-ID": "1"},
    )
    assert login.status_code == 200, login.text

    enable = client.post("/api/auth/mfa/enable", headers=_csrf_headers())
    assert enable.status_code == 200, enable.text
    secret = str(enable.json()["secret"])

    verify = client.post(
        "/api/auth/mfa/verify",
        headers=_csrf_headers(),
        json={"code": _totp(secret)},
    )
    assert verify.status_code == 200, verify.text
    assert verify.json()["status"] == "enabled"

    client.post("/api/auth/logout", headers=_csrf_headers())

    denied_login = client.post(
        "/api/auth/login",
        json={"login": "mfa.local.user", "password": "mfa12345"},
        headers={"X-Tenant-ID": "1"},
    )
    assert denied_login.status_code == 401, denied_login.text

    allowed_login = client.post(
        "/api/auth/login",
        json={"login": "mfa.local.user", "password": "mfa12345", "mfa_code": _totp(secret)},
        headers={"X-Tenant-ID": "1"},
    )
    assert allowed_login.status_code == 200, allowed_login.text


def test_revoke_current_session_invalidates_access_token() -> None:
    client.cookies.clear()
    _ensure_local_user("admin", "admin123", ["admin"], "Admin Local")
    login = client.post(
        "/api/auth/login",
        json={"login": "admin", "password": "admin123"},
        headers={"X-Tenant-ID": "1"},
    )
    assert login.status_code == 200, login.text
    access_token = str(login.json()["access_token"])

    revoke = client.post(
        "/api/auth/sessions/revoke-current",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert revoke.status_code == 200, revoke.text

    denied = client.get(
        "/api/auth/me/profile",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert denied.status_code == 401, denied.text
    assert str(denied.json().get("detail", "")) in {"token revoked", "session revoked"}


def test_revoke_all_sessions_invalidates_other_sessions() -> None:
    client.cookies.clear()
    _ensure_local_user("admin", "admin123", ["admin"], "Admin Local")
    login_1 = client.post("/api/auth/login", json={"login": "admin", "password": "admin123"}, headers={"X-Tenant-ID": "1"})
    assert login_1.status_code == 200, login_1.text
    token_1 = str(login_1.json()["access_token"])

    client.cookies.clear()
    login_2 = client.post("/api/auth/login", json={"login": "admin", "password": "admin123"}, headers={"X-Tenant-ID": "1"})
    assert login_2.status_code == 200, login_2.text
    token_2 = str(login_2.json()["access_token"])

    revoke_all = client.post(
        "/api/auth/sessions/revoke-all",
        headers={"Authorization": f"Bearer {token_2}"},
    )
    assert revoke_all.status_code == 200, revoke_all.text
    assert int(revoke_all.json().get("revoked_count", 0)) >= 1

    denied = client.get(
        "/api/auth/me/profile",
        headers={"Authorization": f"Bearer {token_1}"},
    )
    assert denied.status_code == 401, denied.text


def test_service_token_cannot_access_browser_profile() -> None:
    create_account = client.post(
        "/api/admin/service-accounts",
        headers=ADMIN_HEADERS,
        json={
            "name": "reporting-agent",
            "permissions": ["admin.integrations.manage"],
            "platform_global": False,
        },
    )
    assert create_account.status_code == 200, create_account.text
    account = create_account.json()["account"]

    issue_token = client.post(
        f"/api/admin/service-accounts/{account['account_id']}/token",
        headers=ADMIN_HEADERS,
        json={"secret": account["secret"]},
    )
    assert issue_token.status_code == 200, issue_token.text
    service_token = str(issue_token.json()["token"])

    denied = client.get(
        "/api/auth/me/profile",
        headers={"Authorization": f"Bearer {service_token}"},
    )
    assert denied.status_code == 403, denied.text


def test_revoked_service_account_token_is_rejected() -> None:
    create_account = client.post(
        "/api/admin/service-accounts",
        headers=ADMIN_HEADERS,
        json={
            "name": "revoked-agent",
            "permissions": ["admin.integrations.manage"],
            "platform_global": False,
        },
    )
    assert create_account.status_code == 200, create_account.text
    account = create_account.json()["account"]

    issue_token = client.post(
        f"/api/admin/service-accounts/{account['account_id']}/token",
        headers=ADMIN_HEADERS,
        json={"secret": account["secret"]},
    )
    assert issue_token.status_code == 200, issue_token.text
    service_token = str(issue_token.json()["token"])

    allowed = client.get(
        "/api/admin/service-accounts",
        headers={"Authorization": f"Bearer {service_token}"},
    )
    assert allowed.status_code == 200, allowed.text

    revoke_account = client.post(
        f"/api/admin/service-accounts/{account['account_id']}/revoke",
        headers=ADMIN_HEADERS,
    )
    assert revoke_account.status_code == 200, revoke_account.text

    denied = client.get(
        "/api/admin/service-accounts",
        headers={"Authorization": f"Bearer {service_token}"},
    )
    assert denied.status_code == 401, denied.text
    assert "service account revoked" in str(denied.json().get("detail", ""))


def test_platform_global_service_account_requires_platform_admin() -> None:
    denied_create = client.post(
        "/api/admin/service-accounts",
        headers=ADMIN_HEADERS,
        json={
            "name": "platform-agent-denied",
            "permissions": ["admin.integrations.manage"],
            "platform_global": True,
        },
    )
    assert denied_create.status_code == 403, denied_create.text
    assert "platform-global service account requires platform admin" in str(denied_create.json().get("detail", ""))

    platform_headers = _auth_headers("platform.root@example.com", ["superadmin"], tenant_id=1)
    create_account = client.post(
        "/api/admin/service-accounts",
        headers=platform_headers,
        json={
            "name": "platform-agent-allowed",
            "permissions": ["admin.integrations.manage"],
            "platform_global": True,
        },
    )
    assert create_account.status_code == 200, create_account.text
    account = create_account.json()["account"]
    assert account["platform_global"] is True

    non_platform_list = client.get(
        "/api/admin/service-accounts",
        headers=ADMIN_HEADERS,
    )
    assert non_platform_list.status_code == 200, non_platform_list.text
    visible_ids = {item["account_id"] for item in non_platform_list.json().get("accounts", [])}
    assert account["account_id"] not in visible_ids

    denied_issue = client.post(
        f"/api/admin/service-accounts/{account['account_id']}/token",
        headers=ADMIN_HEADERS,
        json={"secret": account["secret"]},
    )
    assert denied_issue.status_code == 403, denied_issue.text
    assert "platform-global service account requires platform admin" in str(denied_issue.json().get("detail", ""))

    denied_revoke = client.post(
        f"/api/admin/service-accounts/{account['account_id']}/revoke",
        headers=ADMIN_HEADERS,
    )
    assert denied_revoke.status_code == 403, denied_revoke.text
    assert "platform-global service account requires platform admin" in str(denied_revoke.json().get("detail", ""))


def test_oidc_callback_mapping_does_not_grant_platform_authority(monkeypatch) -> None:
    tenant_b_id = _create_tenant_b()
    tenant_b_admin_headers = {
        "Authorization": f"Bearer {create_access_token('tenant-b-admin@example.com', ['admin'], 'test', tenant_id=tenant_b_id)}"
    }

    upsert_provider = client.put(
        "/api/admin/identity/providers/entra",
        headers=tenant_b_admin_headers,
        json={
            "provider": "entra",
            "type": "oidc",
            "enabled": True,
            "issuer": "https://idp.example.com",
            "client_id": "client-123",
            "client_secret": "secret-123",
            "redirect_uri": "https://app.example.com/api/auth/oidc/entra/callback",
            "scopes": ["openid", "profile", "email"],
            "tenant_scope": "tenant",
            "saml_metadata_url": "",
            "saml_sso_url": "",
            "saml_entity_id": "",
        },
    )
    assert upsert_provider.status_code == 200, upsert_provider.text

    initiate = client.post(
        "/api/auth/oidc/entra/initiate",
        headers={**tenant_b_admin_headers, "X-Tenant-ID": str(tenant_b_id)},
    )
    assert initiate.status_code == 200, initiate.text
    state = str(initiate.json()["state"])

    class _External:
        subject = "sub-001"
        email = "owner@example.com"
        display_name = "Owner"

    monkeypatch.setattr("app.modules.auth.router.exchange_oidc_code_for_identity", lambda provider_config, code: _External())

    callback = client.get(
        "/api/auth/oidc/entra/callback",
        params={"state": state, "code": "dummy-code"},
    )
    assert callback.status_code == 200, callback.text
    oidc_token = str(callback.json()["access_token"])

    denied = client.get(
        "/platform/plans",
        headers={"Authorization": f"Bearer {oidc_token}"},
    )
    assert denied.status_code == 403, denied.text


def test_saml_provider_configuration_roundtrip() -> None:
    tenant_b_id = _create_tenant_b()
    tenant_b_admin_headers = {
        "Authorization": f"Bearer {create_access_token('tenant-b-admin@example.com', ['admin'], 'test', tenant_id=tenant_b_id)}"
    }

    upsert_provider = client.put(
        "/api/admin/identity/providers/okta-saml",
        headers=tenant_b_admin_headers,
        json={
            "provider": "okta-saml",
            "type": "saml",
            "enabled": True,
            "issuer": "",
            "client_id": "",
            "client_secret": "",
            "redirect_uri": "",
            "scopes": [],
            "tenant_scope": "tenant",
            "saml_metadata_url": "https://idp.example.com/metadata.xml",
            "saml_sso_url": "https://idp.example.com/sso",
            "saml_entity_id": "urn:example:tenant-b:saml",
        },
    )
    assert upsert_provider.status_code == 200, upsert_provider.text

    providers = client.get(
        "/api/admin/identity/providers",
        headers=tenant_b_admin_headers,
    )
    assert providers.status_code == 200, providers.text
    rows = providers.json().get("providers", [])
    row = next(item for item in rows if item["provider"] == "okta-saml")
    assert row["type"] == "saml"
    assert row["saml_metadata_url"] == "https://idp.example.com/metadata.xml"


def test_oidc_initiate_rejects_saml_provider() -> None:
    tenant_b_id = _create_tenant_b()
    tenant_b_admin_headers = {
        "Authorization": f"Bearer {create_access_token('tenant-b-admin@example.com', ['admin'], 'test', tenant_id=tenant_b_id)}"
    }

    upsert_provider = client.put(
        "/api/admin/identity/providers/saml-only",
        headers=tenant_b_admin_headers,
        json={
            "provider": "saml-only",
            "type": "saml",
            "enabled": True,
            "issuer": "",
            "client_id": "",
            "client_secret": "",
            "redirect_uri": "",
            "scopes": [],
            "tenant_scope": "tenant",
            "saml_metadata_url": "https://idp.example.com/saml-only/metadata.xml",
            "saml_sso_url": "https://idp.example.com/saml-only/sso",
            "saml_entity_id": "urn:example:saml-only",
        },
    )
    assert upsert_provider.status_code == 200, upsert_provider.text

    initiate = client.post(
        "/api/auth/oidc/saml-only/initiate",
        headers={**tenant_b_admin_headers, "X-Tenant-ID": str(tenant_b_id)},
    )
    assert initiate.status_code == 400, initiate.text
    assert "not oidc" in str(initiate.json().get("detail", "")).lower()


def test_auth_lifecycle_and_service_account_events_are_audited() -> None:
    client.cookies.clear()
    _ensure_local_user("admin", "admin123", ["admin"], "Admin Local")
    login = client.post("/api/auth/login", json={"login": "admin", "password": "admin123"}, headers={"X-Tenant-ID": "1"})
    assert login.status_code == 200, login.text

    csrf = client.get("/api/auth/csrf")
    assert csrf.status_code == 200, csrf.text
    csrf_token = str(csrf.json()["csrf_token"])

    refresh = client.post("/api/auth/refresh", headers={"X-CSRF-Token": csrf_token})
    assert refresh.status_code == 200, refresh.text

    logout = client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf_token})
    assert logout.status_code == 200, logout.text

    create_account = client.post(
        "/api/admin/service-accounts",
        headers=ADMIN_HEADERS,
        json={"name": "audit-agent", "permissions": ["admin.integrations.manage"], "platform_global": False},
    )
    assert create_account.status_code == 200, create_account.text
    account = create_account.json()["account"]

    revoke_account = client.post(
        f"/api/admin/service-accounts/{account['account_id']}/revoke",
        headers=ADMIN_HEADERS,
    )
    assert revoke_account.status_code == 200, revoke_account.text

    events = client.get("/api/admin/audit/events", headers=ADMIN_HEADERS)
    assert events.status_code == 200, events.text
    actions = [item.get("action") for item in events.json().get("events", [])]
    assert "auth.login.success" in actions
    assert "auth.refresh.success" in actions
    assert "auth.logout" in actions
    assert "service_accounts.create" in actions
    assert "service_accounts.revoke" in actions
