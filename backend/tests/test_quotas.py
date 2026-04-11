from app.modules.auth.token_service import create_access_token
from app.modules.plans.service import get_plan_by_code
from app.modules import quotas as quotas_module
from app.modules.quotas.service import (
    BASELINE_QUOTA_KEYS,
    check_quota,
    get_plan_quota_consistency_report,
    resolve_tenant_quotas,
)
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


def test_plan_quota_consistency_report_detects_missing_keys_and_orphans() -> None:
    free_plan = get_plan_by_code("free")
    assert free_plan is not None

    free_plan_id = int(free_plan["id"])
    resolve_tenant_quotas(1)

    with quotas_module.service._state_lock:
        quotas_module.service._state.rows_by_plan[free_plan_id].pop("users", None)
        quotas_module.service._state.rows_by_plan[999999] = {"users": 1}

    report = get_plan_quota_consistency_report()

    assert report.issue_count >= 2
    assert any(
        issue.issue_type == "plan_missing_quota_key"
        and issue.plan_id == free_plan_id
        and issue.quota_key == "users"
        for issue in report.issues
    )
    assert any(
        issue.issue_type == "quota_plan_missing" and issue.plan_id == 999999
        for issue in report.issues
    )
    assert set(BASELINE_QUOTA_KEYS)


def test_platform_quota_consistency_endpoint_returns_detected_issues() -> None:
    free_plan = get_plan_by_code("free")
    assert free_plan is not None

    free_plan_id = int(free_plan["id"])
    resolve_tenant_quotas(1)

    with quotas_module.service._state_lock:
        quotas_module.service._state.rows_by_plan[free_plan_id].pop("users", None)

    response = client.get("/platform/quotas/consistency", headers=_platform_headers())

    assert response.status_code == 200
    payload = response.json()
    assert payload["issue_count"] >= 1
    assert any(
        issue["issue_type"] == "plan_missing_quota_key"
        and issue["plan_id"] == free_plan_id
        and issue["quota_key"] == "users"
        for issue in payload["issues"]
    )
