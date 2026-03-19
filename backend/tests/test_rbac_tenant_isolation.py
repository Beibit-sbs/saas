from tests.conftest import ADMIN_HEADERS, _auth_headers, client


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
    assert list_b.status_code == 200
    assert "tenant_a_only" not in list_b.json()["roles"]


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
    assert assign_attempt.status_code == 400
    assert "unknown role" in str(assign_attempt.json().get("detail", ""))


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

    create_role_b = client.post(
        "/api/admin/rbac/roles",
        headers=_tenant_headers(tenant_b_id),
        json={"name": "tenant_b_role", "permissions": ["admin.dashboard.read"]},
    )
    assert create_role_b.status_code == 200, create_role_b.text

    assign_cross = client.post(
        "/api/admin/rbac/assign",
        headers=_tenant_headers(tenant_b_id),
        json={"user_id": user_id, "role": "tenant_b_role"},
    )
    assert assign_cross.status_code == 403


def test_platform_admin_can_access_roles_of_any_tenant() -> None:
    tenant_b_id = _create_tenant_b()
    platform_headers = _auth_headers("platform.root@example.com", ["superadmin"])

    create_role_b = client.post(
        "/api/admin/rbac/roles",
        headers=_tenant_headers(tenant_b_id),
        json={"name": "tenant_b_visible", "permissions": ["admin.dashboard.read"]},
    )
    assert create_role_b.status_code == 200, create_role_b.text

    # Platform admin targets tenant B explicitly via filter.
    list_b = client.get(
        f"/api/admin/rbac/roles?tenant_id={tenant_b_id}",
        headers=platform_headers,
    )
    assert list_b.status_code == 200, list_b.text
    assert "tenant_b_visible" in list_b.json()["roles"]
