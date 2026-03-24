import pytest
from uuid import uuid4

from app.modules.auth.local_users_service import local_user_store
from app.modules.auth.token_service import create_access_token, verify_access_token
from app.modules.rbac.service import BASELINE_ROLE_PERMISSIONS, add_or_update_role_for_tenant
from tests.conftest import ADMIN_HEADERS, client


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
        "/api/auth/mock-login",
        json={"login": tenant_b_login, "password": "TenantBpass123"},
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
        "/api/auth/mock-login",
        json={"login": tenant_b_override_login, "password": "TenantBpass123"},
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