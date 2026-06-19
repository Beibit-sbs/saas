from __future__ import annotations

from app.modules.audit import service as audit_service
from app.modules.auth.local_users_service import local_user_store
from app.modules.auth.platform_superadmin_service import ensure_platform_superadmin
from app.modules.auth.token_service import verify_access_token
from app.modules.rbac.service import BASELINE_ROLE_PERMISSIONS, add_or_update_role_for_tenant
from tests.conftest import ADMIN_HEADERS, client


def test_platform_superadmin_login_via_standard_endpoint() -> None:
    client.cookies.clear()
    ensure_platform_superadmin(
        login="platform.owner",
        password="PlatformOwnerPass123!",
        email="owner@platform.local",
    )

    response = client.post(
        "/api/auth/login",
        json={"login": "platform.owner", "password": "PlatformOwnerPass123!"},
        headers={"X-Tenant-ID": "1"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["auth_source"] == "local"
    assert "superadmin" in body["roles"]

    claims = verify_access_token(body["access_token"])
    assert claims.tenant_id == 1
    assert "superadmin" in claims.roles
    assert "tenants.write" in claims.permissions

    raw_user = local_user_store.find_user_by_login("platform.owner")
    assert raw_user is not None
    assert raw_user.get("account_scope") == "platform"
    assert bool(raw_user.get("is_platform_user", False)) is True


def test_platform_superadmin_wrong_password_fails() -> None:
    client.cookies.clear()
    ensure_platform_superadmin(
        login="platform.failcase",
        password="PlatformOwnerPass123!",
    )

    response = client.post(
        "/api/auth/login",
        json={"login": "platform.failcase", "password": "wrong-password"},
        headers={"X-Tenant-ID": "1"},
    )

    assert response.status_code in {401, 503}


def test_tenant_admin_is_not_promoted_to_platform_superadmin() -> None:
    client.cookies.clear()
    create_tenant = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": "tenant-isolation-sa", "name": "Tenant Isolation", "status": "active"},
    )
    assert create_tenant.status_code == 200, create_tenant.text
    tenant_id = int(create_tenant.json()["tenant"]["id"])

    add_or_update_role_for_tenant(tenant_id, "admin", list(BASELINE_ROLE_PERMISSIONS["admin"]))
    local_user_store.create_user(
        login="tenant.admin",
        password="TenantAdminPass123!",
        display_name="Tenant Admin",
        roles=["admin"],
        default_language="ru",
        tenant_id=tenant_id,
    )

    response = client.post(
        "/api/auth/login",
        json={"login": "tenant.admin", "password": "TenantAdminPass123!"},
        headers={"X-Tenant-ID": str(tenant_id)},
    )
    assert response.status_code == 200, response.text
    claims = verify_access_token(response.json()["access_token"])
    assert claims.tenant_id == tenant_id
    assert "admin" in claims.roles
    assert "superadmin" not in claims.roles


def test_platform_superadmin_creation_is_idempotent_and_audited() -> None:
    client.cookies.clear()
    first = ensure_platform_superadmin(
        login="platform.audit",
        password="PlatformOwnerPass123!",
        email="audit@platform.local",
    )
    second = ensure_platform_superadmin(
        login="platform.audit",
        password="PlatformOwnerPass123!",
        email="audit@platform.local",
    )

    assert first["operation"] == "created"
    assert second["operation"] in {"noop", "updated"}

    events = audit_service.list_admin_actions(
        action="platform.superadmin.ensure",
        tenant_id=1,
        limit=20,
    )
    assert events
    assert any(
        str(event.get("metadata", {}).get("login", "")) == "platform.audit"
        for event in events
    )


def test_no_implicit_platform_superadmin_autocreation_on_login() -> None:
    client.cookies.clear()
    assert local_user_store.find_user_by_login("not.provisioned") is None

    response = client.post(
        "/api/auth/login",
        json={"login": "not.provisioned", "password": "SomePassword123!"},
        headers={"X-Tenant-ID": "1"},
    )

    assert response.status_code in {401, 503}
    assert local_user_store.find_user_by_login("not.provisioned") is None


def test_platform_superadmin_header_mismatch_allows_controlled_read_override() -> None:
    client.cookies.clear()
    ensure_platform_superadmin(
        login="platform.header.guard",
        password="PlatformOwnerPass123!",
    )

    tenant_create = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": "platform-header-tenant-b", "name": "Platform Header Tenant B", "status": "active"},
    )
    assert tenant_create.status_code == 200, tenant_create.text
    tenant_b_id = int(tenant_create.json()["tenant"]["id"])

    login = client.post(
        "/api/auth/login",
        json={"login": "platform.header.guard", "password": "PlatformOwnerPass123!"},
        headers={"X-Tenant-ID": "1"},
    )
    assert login.status_code == 200, login.text

    allowed = client.get(
        "/api/admin/dashboard",
        headers={"X-Tenant-ID": str(tenant_b_id)},
    )
    assert allowed.status_code == 200, allowed.text


def test_protected_endpoint_requires_token() -> None:
    client.cookies.clear()
    response = client.get("/api/admin/dashboard")
    assert response.status_code == 401
