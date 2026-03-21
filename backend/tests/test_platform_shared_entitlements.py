from app.modules.platform_shared.entitlements import is_module_enabled, resolve_tenant_entitlements
from tests.conftest import ADMIN_HEADERS, client


def test_entitlement_snapshot_resolves_plan_quota_flags() -> None:
    create_response = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": "tenant-entitlement", "name": "Tenant Entitlement", "status": "active"},
    )
    assert create_response.status_code == 200, create_response.text
    tenant_id = int(create_response.json()["tenant"]["id"])

    snapshot = resolve_tenant_entitlements(tenant_id)
    assert snapshot.tenant_id == tenant_id
    assert snapshot.plan_code in {"free", "pro", "enterprise"}
    assert "users" in snapshot.quota_limits
    assert isinstance(snapshot.runtime_feature_flags, dict)


def test_module_enablement_reads_from_snapshot() -> None:
    create_response = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": "tenant-module-enable", "name": "Tenant Module Enable", "status": "active"},
    )
    assert create_response.status_code == 200, create_response.text
    tenant_id = int(create_response.json()["tenant"]["id"])

    snapshot = resolve_tenant_entitlements(tenant_id)
    assert is_module_enabled(snapshot, "identity") is True
    assert is_module_enabled(snapshot, "unknown.module") is False
