from __future__ import annotations

from uuid import uuid4

from app.modules.auth.local_users_service import local_user_store
from app.modules.tenants.provisioning_service import TenantProvisioningService
from tests.conftest import client


def _login(login: str, password: str, tenant_id: int) -> str:
    client.cookies.clear()
    response = client.post(
        "/api/auth/login",
        json={"login": login, "password": password},
        headers={"X-Tenant-ID": str(tenant_id)},
    )
    assert response.status_code == 200, response.text
    token = response.json().get("access_token")
    assert isinstance(token, str) and token
    return token


def test_two_tenant_users_cannot_cross_access() -> None:
    suffix = uuid4().hex[:8]

    tenant_a = TenantProvisioningService.create_tenant_with_defaults(
        tenant_name=f"iso-a-{suffix}",
        admin_email=f"iso-a-{suffix}@example.local",
        plan_code="free",
        actor="tests",
    )["tenant"]
    tenant_b = TenantProvisioningService.create_tenant_with_defaults(
        tenant_name=f"iso-b-{suffix}",
        admin_email=f"iso-b-{suffix}@example.local",
        plan_code="free",
        actor="tests",
    )["tenant"]

    tenant_a_id = int(tenant_a["id"])
    tenant_b_id = int(tenant_b["id"])

    password = "Iso!Pass123"
    user_a = local_user_store.create_user(
        login=f"iso_user_a_{suffix}",
        password=password,
        display_name="ISO User A",
        roles=["admin"],
        default_language="ru",
        tenant_id=tenant_a_id,
    )
    user_b = local_user_store.create_user(
        login=f"iso_user_b_{suffix}",
        password=password,
        display_name="ISO User B",
        roles=["admin"],
        default_language="ru",
        tenant_id=tenant_b_id,
    )

    token_a = _login(str(user_a["login"]), password, tenant_a_id)
    token_b = _login(str(user_b["login"]), password, tenant_b_id)

    # User A cannot access tenant B scoped resources through tenant_id override.
    user_a_cross = client.get(
        f"/api/admin/jobs?tenant_id={tenant_b_id}",
        headers={
            "Authorization": f"Bearer {token_a}",
            "X-Tenant-ID": str(tenant_a_id),
        },
    )
    assert user_a_cross.status_code == 404
    assert "job not found" in str(user_a_cross.json().get("detail", "")).lower()

    # User B cannot access tenant A scoped resources through tenant_id override.
    user_b_cross = client.get(
        f"/api/admin/jobs?tenant_id={tenant_a_id}",
        headers={
            "Authorization": f"Bearer {token_b}",
            "X-Tenant-ID": str(tenant_b_id),
        },
    )
    assert user_b_cross.status_code == 404
    assert "job not found" in str(user_b_cross.json().get("detail", "")).lower()

    # Header override with token from another tenant is explicitly forbidden.
    header_mismatch = client.get(
        "/api/auth/me",
        headers={
            "Authorization": f"Bearer {token_a}",
            "X-Tenant-ID": str(tenant_b_id),
        },
    )
    assert header_mismatch.status_code == 403
    assert "cross-tenant override forbidden" in str(header_mismatch.json().get("detail", "")).lower()
