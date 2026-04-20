from app.modules.billing.router import router


def test_billing_router_scaffold_routes_present() -> None:
    paths = {route.path for route in router.routes}

    assert "/api/admin/billing/plans" in paths
    assert "/api/admin/billing/tenants/{tenant_id}/state" in paths
    assert "/api/admin/billing/tenants/{tenant_id}/subscription" in paths
    assert "/api/admin/billing/tenants/{tenant_id}/subscription/transition" in paths
    assert "/api/admin/billing/tenants/{tenant_id}/subscription/plan-change" in paths
    assert "/api/admin/billing/tenants/{tenant_id}/usage" in paths
    assert "/api/admin/billing/tenants/{tenant_id}/usage/{metric}" in paths
