from app.modules.auth.token_service import create_access_token
from tests.conftest import ADMIN_HEADERS, client


def _tenant_admin_headers(tenant_id: int) -> dict[str, str]:
    token = create_access_token(
        user_id="tenant.admin@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
    )
    return {"Authorization": f"Bearer {token}"}


def test_list_tenants_default_tenant_exists() -> None:
    """Default tenant (id=1) is always present after state reset."""
    response = client.get("/api/admin/tenants", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    tenants = response.json()["tenants"]
    assert len(tenants) >= 1
    default = next((t for t in tenants if t["slug"] == "default"), None)
    assert default is not None
    assert default["id"] == 1
    assert default["name"] == "Default Organization"
    assert default["status"] == "active"


def test_create_tenant() -> None:
    payload = {"slug": "acme-corp", "name": "Acme Corporation", "status": "active"}
    response = client.post("/api/admin/tenants", headers=ADMIN_HEADERS, json=payload)
    assert response.status_code == 200
    tenant = response.json()["tenant"]
    assert tenant["slug"] == "acme-corp"
    assert tenant["name"] == "Acme Corporation"
    assert tenant["status"] == "active"
    assert tenant["id"] > 0


def test_create_tenant_duplicate_slug_rejected() -> None:
    payload = {"slug": "shared-slug", "name": "First", "status": "active"}
    r1 = client.post("/api/admin/tenants", headers=ADMIN_HEADERS, json=payload)
    assert r1.status_code == 200

    r2 = client.post("/api/admin/tenants", headers=ADMIN_HEADERS, json=payload)
    assert r2.status_code == 400
    assert "already exists" in r2.json()["detail"]


def test_update_tenant() -> None:
    # Create a tenant to update
    create = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": "update-me", "name": "Before Update", "status": "active"},
    )
    assert create.status_code == 200
    tenant_id = create.json()["tenant"]["id"]

    update = client.put(
        f"/api/admin/tenants/{tenant_id}",
        headers=ADMIN_HEADERS,
        json={"name": "After Update"},
    )
    assert update.status_code == 200
    updated = update.json()["tenant"]
    assert updated["name"] == "After Update"
    assert updated["slug"] == "update-me"  # slug unchanged
    assert updated["status"] == "active"  # status unchanged


def test_update_tenant_not_found() -> None:
    response = client.put(
        "/api/admin/tenants/99999",
        headers=ADMIN_HEADERS,
        json={"name": "Ghost"},
    )
    assert response.status_code == 404


def test_delete_tenant_soft_deactivates() -> None:
    create = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": "deactivate-me", "name": "To Deactivate", "status": "active"},
    )
    assert create.status_code == 200
    tenant_id = create.json()["tenant"]["id"]

    delete = client.delete(f"/api/admin/tenants/{tenant_id}", headers=ADMIN_HEADERS)
    assert delete.status_code == 200
    result = delete.json()
    assert result["deleted"] is True
    assert result["tenant"]["status"] == "inactive"

    # Tenant still appears in list with inactive status
    list_response = client.get("/api/admin/tenants", headers=ADMIN_HEADERS)
    tenants = list_response.json()["tenants"]
    found = next((t for t in tenants if t["id"] == tenant_id), None)
    assert found is not None
    assert found["status"] == "inactive"


def test_delete_tenant_not_found() -> None:
    response = client.delete("/api/admin/tenants/99999", headers=ADMIN_HEADERS)
    assert response.status_code == 404


def test_inactive_tenant_excluded_from_active_count() -> None:
    """After deleting a tenant, active count decreases but tenant is not removed."""
    create = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": "temp-org", "name": "Temp Org", "status": "active"},
    )
    tenant_id = create.json()["tenant"]["id"]

    before = client.get("/api/admin/tenants", headers=ADMIN_HEADERS).json()["tenants"]
    active_before = sum(1 for t in before if t["status"] == "active")

    client.delete(f"/api/admin/tenants/{tenant_id}", headers=ADMIN_HEADERS)

    after = client.get("/api/admin/tenants", headers=ADMIN_HEADERS).json()["tenants"]
    active_after = sum(1 for t in after if t["status"] == "active")

    assert active_after == active_before - 1
    assert len(after) == len(before)  # row count unchanged (soft delete)


def test_default_tenant_always_present_after_reset() -> None:
    """Simulates state reset between tests — default tenant is re-seeded."""
    # The autouse fixture resets state before each test.
    # Just call list again to verify default exists (same as first test).
    response = client.get("/api/admin/tenants", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    slugs = [t["slug"] for t in response.json()["tenants"]]
    assert "default" in slugs


def test_non_platform_tenant_admin_cannot_mutate_tenants() -> None:
    create_tenant_b = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": "tenant-b-control", "name": "Tenant B Control", "status": "active"},
    )
    assert create_tenant_b.status_code == 200, create_tenant_b.text
    tenant_b_id = int(create_tenant_b.json()["tenant"]["id"])

    headers = _tenant_admin_headers(tenant_b_id)
    denied_create = client.post(
        "/api/admin/tenants",
        headers=headers,
        json={"slug": "forbidden-tenant", "name": "Forbidden Tenant", "status": "active"},
    )
    assert denied_create.status_code == 403, denied_create.text
    assert "platform tenant context required" in str(denied_create.json().get("detail", ""))
