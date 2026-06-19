import pytest
from uuid import uuid4

from app.modules.auth.local_users_service import local_user_store
from app.modules.auth.token_service import create_access_token, verify_access_token
from app.modules.rbac.service import BASELINE_ROLE_PERMISSIONS, add_or_update_role_for_tenant
from tests.conftest import ADMIN_HEADERS, _auth_headers, client


pytestmark = pytest.mark.security_regression


def _create_tenant_b() -> int:
    suffix = uuid4().hex[:8]
    response = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": f"tenant-b-auth-{suffix}", "name": "Tenant B Auth", "status": "active"},
    )
    assert response.status_code == 200, response.text
    return int(response.json()["tenant"]["id"])


def test_platform_superadmin_created_tenant_admin_can_login_to_created_tenant() -> None:
    suffix = uuid4().hex[:8]
    platform_headers = _auth_headers("platform-root@example.com", ["superadmin"], tenant_id=1)
    tenant_admin_login = f"tenant-root-{suffix}"
    tenant_admin_password = "TenantRootPass123!"

    created = client.post(
        "/platform/tenants",
        headers=platform_headers,
        json={
            "tenant_name": f"Root Flow University {suffix}",
            "admin_email": f"admin-{suffix}@root-flow.edu",
            "admin_login": tenant_admin_login,
            "admin_password": tenant_admin_password,
            "admin_display_name": "Root Flow Tenant Admin",
            "plan_code": "free",
        },
    )
    assert created.status_code == 200, created.text
    created_payload = created.json()
    tenant_id = int(created_payload["tenant"]["id"])
    assert created_payload["admin_user"]["login"] == tenant_admin_login
    assert "invite_token" not in created_payload

    client.cookies.clear()
    login = client.post(
        "/api/auth/login",
        json={"login": tenant_admin_login, "password": tenant_admin_password},
        headers={"X-Tenant-ID": str(tenant_id)},
    )
    assert login.status_code == 200, login.text

    token = login.cookies.get("app_access_token")
    assert isinstance(token, str)
    claims = verify_access_token(token)
    assert claims.tenant_id == tenant_id
    assert claims.user_id == created_payload["admin_user"]["user_id"]

    me = client.get("/api/auth/me")
    assert me.status_code == 200, me.text
    assert me.json()["user"]["tenantId"] == tenant_id


def test_local_cookie_session_inherits_user_tenant_without_header() -> None:
    tenant_b_id = _create_tenant_b()
    suffix = uuid4().hex[:8]
    tenant_a_login = f"tenant-a-admin-{suffix}"
    tenant_b_login = f"tenant-b-admin-{suffix}"
    add_or_update_role_for_tenant(tenant_b_id, "admin", list(BASELINE_ROLE_PERMISSIONS["admin"]))
    local_user_store.create_user(
        login=tenant_a_login,
        password="TenantApass123",
        display_name="Tenant A Admin",
        roles=["admin"],
        default_language="ru",
        tenant_id=1,
    )
    local_user_store.create_user(
        login=tenant_b_login,
        password="TenantBpass123",
        display_name="Tenant B Admin",
        roles=["admin"],
        default_language="ru",
        tenant_id=tenant_b_id,
    )

    client.cookies.clear()
    login = client.post(
        "/api/auth/login",
        json={"login": tenant_b_login, "password": "TenantBpass123"},
        headers={"X-Tenant-ID": str(tenant_b_id)},
    )
    assert login.status_code == 200, login.text

    token = login.cookies.get("app_access_token")
    assert isinstance(token, str)
    claims = verify_access_token(token)
    assert claims.tenant_id == tenant_b_id

    dashboard = client.get("/api/admin/dashboard")
    assert dashboard.status_code == 200, dashboard.text
    assert dashboard.json()["users"]["local_users_count"] == 1


def test_local_session_cannot_override_tenant_header() -> None:
    tenant_b_id = _create_tenant_b()
    suffix = uuid4().hex[:8]
    tenant_b_override_login = f"tenant-b-override-{suffix}"
    add_or_update_role_for_tenant(tenant_b_id, "admin", list(BASELINE_ROLE_PERMISSIONS["admin"]))
    local_user_store.create_user(
        login=tenant_b_override_login,
        password="TenantBpass123",
        display_name="Tenant B Override",
        roles=["admin"],
        default_language="ru",
        tenant_id=tenant_b_id,
    )

    client.cookies.clear()
    login = client.post(
        "/api/auth/login",
        json={"login": tenant_b_override_login, "password": "TenantBpass123"},
        headers={"X-Tenant-ID": str(tenant_b_id)},
    )
    assert login.status_code == 200, login.text

    response = client.get(
        "/api/admin/dashboard",
        headers={"X-Tenant-ID": "1"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "cross-tenant override forbidden"


def test_non_local_auth_source_cannot_override_tenant_header() -> None:
    tenant_b_id = _create_tenant_b()
    token = create_access_token(
        user_id="oauth.user.001",
        roles=["admin"],
        auth_source="oauth",
        tenant_id=tenant_b_id,
    )

    response = client.get(
        "/api/admin/dashboard",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": "1",
        },
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "cross-tenant override forbidden"


def test_tenant_user_with_matching_header_is_allowed() -> None:
    tenant_b_id = _create_tenant_b()
    suffix = uuid4().hex[:8]
    tenant_b_login = f"tenant-b-match-{suffix}"
    add_or_update_role_for_tenant(tenant_b_id, "admin", list(BASELINE_ROLE_PERMISSIONS["admin"]))
    local_user_store.create_user(
        login=tenant_b_login,
        password="TenantBpass123",
        display_name="Tenant B Match",
        roles=["admin"],
        default_language="ru",
        tenant_id=tenant_b_id,
    )

    client.cookies.clear()
    login = client.post(
        "/api/auth/login",
        json={"login": tenant_b_login, "password": "TenantBpass123"},
        headers={"X-Tenant-ID": str(tenant_b_id)},
    )
    assert login.status_code == 200, login.text

    ok = client.get(
        "/api/admin/dashboard",
        headers={"X-Tenant-ID": str(tenant_b_id)},
    )
    assert ok.status_code == 200, ok.text


def test_platform_local_login_without_tenant_header_is_rejected() -> None:
    suffix = uuid4().hex[:8]
    platform_login = f"platform-default-{suffix}"
    local_user_store.create_user(
        login=platform_login,
        password="PlatformDefaultPass123",
        display_name="Platform Default",
        roles=["admin"],
        default_language="ru",
        tenant_id=1,
    )

    client.cookies.clear()
    login = client.post(
        "/api/auth/login",
        json={"login": platform_login, "password": "PlatformDefaultPass123"},
    )
    assert login.status_code == 400, login.text


def test_tenant_local_login_requires_explicit_tenant_header() -> None:
    tenant_b_id = _create_tenant_b()
    suffix = uuid4().hex[:8]
    tenant_b_login = f"tenant-b-explicit-{suffix}"
    add_or_update_role_for_tenant(tenant_b_id, "admin", list(BASELINE_ROLE_PERMISSIONS["admin"]))
    local_user_store.create_user(
        login=tenant_b_login,
        password="TenantBexplicit123",
        display_name="Tenant B Explicit",
        roles=["admin"],
        default_language="ru",
        tenant_id=tenant_b_id,
    )

    client.cookies.clear()
    without_header = client.post(
        "/api/auth/login",
        json={"login": tenant_b_login, "password": "TenantBexplicit123"},
    )
    assert without_header.status_code == 400, without_header.text

    with_wrong_header = client.post(
        "/api/auth/login",
        json={"login": tenant_b_login, "password": "TenantBexplicit123"},
        headers={"X-Tenant-ID": "1"},
    )
    assert with_wrong_header.status_code in {401, 503}, with_wrong_header.text

    with_correct_header = client.post(
        "/api/auth/login",
        json={"login": tenant_b_login, "password": "TenantBexplicit123"},
        headers={"X-Tenant-ID": str(tenant_b_id)},
    )
    assert with_correct_header.status_code == 200, with_correct_header.text
