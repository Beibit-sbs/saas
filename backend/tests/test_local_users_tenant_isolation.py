import pytest

from tests.conftest import ADMIN_HEADERS, client


pytestmark = pytest.mark.security_regression


def _tenant_headers(tenant_id: int, base_headers: dict[str, str] | None = None) -> dict[str, str]:
    headers = dict(base_headers or ADMIN_HEADERS)
    headers["X-Tenant-ID"] = str(tenant_id)
    return headers


def _create_tenant_b() -> int:
    response = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={
            "slug": "tenant-b-local-users",
            "name": "Tenant B Local Users",
            "status": "active",
        },
    )
    assert response.status_code == 200, response.text
    return int(response.json()["tenant"]["id"])


def test_tenant_b_cannot_see_tenant_a_local_user() -> None:
    tenant_b_id = _create_tenant_b()

    create_a = client.post(
        "/api/admin/local-users",
        headers=ADMIN_HEADERS,
        json={
            "login": "tenant.a.local.user",
            "password": "tenantA12345",
            "display_name": "Tenant A Local User",
            "roles": ["student"],
            "default_language": "ru",
        },
    )
    assert create_a.status_code == 200, create_a.text
    user_a = create_a.json()["user"]

    list_a = client.get("/api/admin/local-users", headers=ADMIN_HEADERS)
    assert list_a.status_code == 200, list_a.text
    assert any(item["user_id"] == user_a["user_id"] for item in list_a.json()["users"])

    list_b = client.get("/api/admin/local-users", headers=_tenant_headers(tenant_b_id))
    assert list_b.status_code == 403, list_b.text


def test_tenant_b_cannot_mutate_tenant_a_local_user() -> None:
    tenant_b_id = _create_tenant_b()

    create_a = client.post(
        "/api/admin/local-users",
        headers=ADMIN_HEADERS,
        json={
            "login": "tenant.a.local.mutate",
            "password": "tenantA54321",
            "display_name": "Tenant A Mutable User",
            "roles": ["student"],
            "default_language": "ru",
        },
    )
    assert create_a.status_code == 200, create_a.text
    user_id = str(create_a.json()["user"]["user_id"])

    update_cross = client.patch(
        f"/api/admin/local-users/{user_id}",
        headers=_tenant_headers(tenant_b_id),
        json={"display_name": "Hacked Name"},
    )
    assert update_cross.status_code == 403, update_cross.text

    password_cross = client.post(
        f"/api/admin/local-users/{user_id}/password",
        headers=_tenant_headers(tenant_b_id),
        json={"password": "crossTenant999"},
    )
    assert password_cross.status_code == 403, password_cross.text

    delete_cross = client.delete(
        f"/api/admin/local-users/{user_id}",
        headers=_tenant_headers(tenant_b_id),
    )
    assert delete_cross.status_code == 403, delete_cross.text

    list_a_after = client.get("/api/admin/local-users", headers=ADMIN_HEADERS)
    assert list_a_after.status_code == 200, list_a_after.text
    user_after = next(item for item in list_a_after.json()["users"] if item["user_id"] == user_id)
    assert user_after["display_name"] == "Tenant A Mutable User"
