from app.modules.auth.token_service import create_access_token
from app.modules.plans.service import get_plan_by_code
from app.modules.quotas.service import check_quota, resolve_tenant_quotas
from app.modules.tenants.service import create_tenant

from conftest import client


def _platform_headers() -> dict[str, str]:
    token = create_access_token(user_id="platform.owner@example.com", roles=["superadmin"], auth_source="test", tenant_id=1)
    return {"Authorization": f"Bearer {token}"}


def test_tenant_receives_plan_quotas() -> None:
    free_plan = get_plan_by_code("free")
    assert free_plan is not None

    response = client.put(
        f"/platform/quotas/{free_plan['id']}",
        headers=_platform_headers(),
        json={"quotas": {"users": 2, "jobs_per_day": 3}},
    )
    assert response.status_code == 200

    tenant = create_tenant(
        {
            "slug": "quota-tenant",
            "name": "Quota Tenant",
            "status": "active",
            "plan_id": int(free_plan["id"]),
        }
    )

    tenant_quotas = resolve_tenant_quotas(int(tenant["id"]))
    assert tenant_quotas["users"] == 2
    assert tenant_quotas["jobs_per_day"] == 3

    check = check_quota(int(tenant["id"]), "users")
    assert check["limit_value"] == 2
    assert check["within_limit"] is True
