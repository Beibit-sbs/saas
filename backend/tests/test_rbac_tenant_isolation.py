from tests.conftest import ADMIN_HEADERS, _auth_headers, client
from app.modules.auth.token_service import create_access_token
from app.modules.rbac import service as rbac_service


def _tenant_headers(tenant_id: int, base_headers: dict[str, str] | None = None) -> dict[str, str]:
    headers = dict(base_headers or ADMIN_HEADERS)
    headers["X-Tenant-ID"] = str(tenant_id)
    return headers


def _create_tenant_b() -> int:
    response = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={
            "slug": "tenant-b-rbac",
            "name": "Tenant B RBAC",
            "status": "active",
        },
    )
    assert response.status_code == 200, response.text
    return int(response.json()["tenant"]["id"])


def test_tenant_a_role_is_not_visible_for_tenant_b() -> None:
    tenant_b_id = _create_tenant_b()

    create_role = client.post(
        "/api/admin/rbac/roles",
        headers=ADMIN_HEADERS,
        json={"name": "tenant_a_only", "permissions": ["admin.dashboard.read"]},
    )
    assert create_role.status_code == 200, create_role.text

    list_a = client.get("/api/admin/rbac/roles", headers=ADMIN_HEADERS)
    assert list_a.status_code == 200
    assert "tenant_a_only" in list_a.json()["roles"]

    list_b = client.get("/api/admin/rbac/roles", headers=_tenant_headers(tenant_b_id))
    assert list_b.status_code == 403
    assert "cross-tenant override forbidden" in str(list_b.json().get("detail", ""))


def test_tenant_b_cannot_assign_tenant_a_role() -> None:
    tenant_b_id = _create_tenant_b()

    create_role = client.post(
        "/api/admin/rbac/roles",
        headers=ADMIN_HEADERS,
        json={"name": "tenant_a_assign_only", "permissions": ["admin.dashboard.read"]},
    )
    assert create_role.status_code == 200

    assign_attempt = client.post(
        "/api/admin/rbac/assign",
        headers=_tenant_headers(tenant_b_id),
        json={"user_id": "local.001", "role": "tenant_a_assign_only"},
    )
    assert assign_attempt.status_code == 403
    assert "cross-tenant override forbidden" in str(assign_attempt.json().get("detail", ""))


def test_cross_tenant_assignment_returns_403() -> None:
    tenant_b_id = _create_tenant_b()

    create_user_a = client.post(
        "/api/admin/local-users",
        headers=ADMIN_HEADERS,
        json={
            "login": "tenant-a-user",
            "password": "tenantApass123",
            "display_name": "Tenant A User",
            "roles": ["student"],
            "default_language": "ru",
        },
    )
    assert create_user_a.status_code == 200, create_user_a.text
    user_id = create_user_a.json()["user"]["user_id"]

    assign_cross = client.post(
        "/api/admin/rbac/assign",
        headers=_tenant_headers(tenant_b_id),
        json={"user_id": user_id, "role": "admin"},
    )
    assert assign_cross.status_code == 403


def test_platform_admin_can_access_roles_of_any_tenant(monkeypatch) -> None:
    tenant_b_id = _create_tenant_b()
    platform_headers = _auth_headers("platform.root@example.com", ["superadmin"])
    monkeypatch.setattr("app.modules.rbac.security.is_platform_admin", lambda actor: actor == "platform.root@example.com")
    monkeypatch.setattr("app.modules.rbac.router.is_platform_admin", lambda actor: actor == "platform.root@example.com")

    create_role_b = client.post(
        "/api/admin/rbac/roles",
        headers=_tenant_headers(tenant_b_id, platform_headers),
        json={"name": "tenant_b_visible", "permissions": ["admin.dashboard.read"]},
    )
    assert create_role_b.status_code == 200, create_role_b.text

    list_b = client.get("/api/admin/rbac/roles", headers=_tenant_headers(tenant_b_id, platform_headers))
    assert list_b.status_code == 200, list_b.text
    assert "tenant_b_visible" in list_b.json()["roles"]


def test_tenant_admin_cannot_create_platform_role_superadmin() -> None:
    tenant_b_id = _create_tenant_b()
    create_role = client.post(
        "/api/admin/rbac/roles",
        headers=_tenant_headers(tenant_b_id),
        json={"name": "superadmin", "permissions": ["admin.dashboard.read"]},
    )
    assert create_role.status_code == 403, create_role.text
    assert "cross-tenant override forbidden" in str(create_role.json().get("detail", ""))


def test_tenant_admin_cannot_escalate_to_platform_admin_via_superadmin_role() -> None:
    tenant_b_id = _create_tenant_b()

    create_role_b = client.post(
        "/api/admin/rbac/roles",
        headers=_tenant_headers(tenant_b_id),
        json={"name": "tenant_b_admin", "permissions": ["admin.roles.manage"]},
    )
    assert create_role_b.status_code == 403, create_role_b.text
    assert "cross-tenant override forbidden" in str(create_role_b.json().get("detail", ""))

    tenant_b_admin_token = create_access_token(
        user_id="tenant-b-admin",
        roles=["superadmin"],
        auth_source="test",
        tenant_id=tenant_b_id,
    )
    tenant_b_admin_headers = {"Authorization": f"Bearer {tenant_b_admin_token}"}
    denied = client.get("/platform/plans", headers=tenant_b_admin_headers)
    assert denied.status_code == 403


def test_platform_admin_role_is_only_honored_in_platform_tenant() -> None:
    tenant_b_id = _create_tenant_b()
    non_platform_headers = _auth_headers("owner@example.com", ["admin"])

    create_role = client.post(
        "/api/admin/rbac/roles",
        headers=non_platform_headers,
        json={
            "tenant_id": tenant_b_id,
            "name": "superadmin",
            "permissions": ["admin.dashboard.read", "admin.tenants.read"],
        },
    )
    assert create_role.status_code == 403, create_role.text


def test_platform_admin_detection_only_uses_platform_tenant(monkeypatch) -> None:
    monkeypatch.setattr(rbac_service, "_use_database", lambda: False)
    monkeypatch.setattr(
        rbac_service,
        "_tenant_user_roles_state",
        {
            1: {"platform.user": {"superadmin"}},
            2: {"tenant.user": {"superadmin"}},
        },
    )

    assert rbac_service.is_platform_admin("platform.user") is True
    assert rbac_service.is_platform_admin("tenant.user") is False


def test_rbac_mutations_are_audited() -> None:
    create_role = client.post(
        "/api/admin/rbac/roles",
        headers=ADMIN_HEADERS,
        json={"name": "audited_role", "permissions": ["admin.dashboard.read"]},
    )
    assert create_role.status_code == 200, create_role.text

    assign_role = client.post(
        "/api/admin/rbac/assign",
        headers=ADMIN_HEADERS,
        json={"user_id": "local.001", "role": "audited_role"},
    )
    assert assign_role.status_code == 200, assign_role.text

    revoke_role = client.delete(
        "/api/admin/rbac/assignments/local.001/audited_role",
        headers=ADMIN_HEADERS,
    )
    assert revoke_role.status_code == 200, revoke_role.text

    events_response = client.get("/api/admin/audit/events", headers=ADMIN_HEADERS)
    assert events_response.status_code == 200, events_response.text
    actions = [item.get("action") for item in events_response.json().get("events", [])]
    assert "rbac.role.upsert" in actions
    assert "rbac.assignment.create" in actions
    assert "rbac.assignment.delete" in actions
