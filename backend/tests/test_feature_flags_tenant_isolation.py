from tests.conftest import ADMIN_HEADERS, _auth_headers, client


def _tenant_headers(tenant_id: int) -> dict[str, str]:
    headers = dict(ADMIN_HEADERS)
    headers["X-Tenant-ID"] = str(tenant_id)
    return headers


def _create_tenant_b() -> int:
    response = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": "tenant-b-feature-flags", "name": "Tenant B Feature Flags", "status": "active"},
    )
    assert response.status_code == 200, response.text
    return int(response.json()["tenant"]["id"])


def test_feature_flags_are_isolated_per_tenant(monkeypatch) -> None:
    tenant_b_id = _create_tenant_b()
    platform_headers = _auth_headers("platform.root@example.com", ["superadmin"])
    monkeypatch.setattr("app.modules.rbac.security.is_platform_admin", lambda actor: actor == "platform.root@example.com")

    # Create flag for tenant A (platform tenant 1) via superadmin
    set_a_response = client.post(
        "/api/admin/feature-flags",
        headers=platform_headers,
        json={"key": "admin.local_users.tab", "enabled": True, "scope": "tenant"},
    )
    assert set_a_response.status_code == 200, set_a_response.text

    # A non-superadmin user cannot write flags for a different tenant (cross-tenant protection in get_current_tenant)
    denied_update = client.post(
        "/api/admin/feature-flags",
        headers=_tenant_headers(tenant_b_id),
        json={"key": "admin.local_users.tab", "enabled": False, "scope": "tenant"},
    )
    assert denied_update.status_code == 403, denied_update.text
    assert "cross-tenant override forbidden" in str(denied_update.json().get("detail", ""))

    # Superadmin can set flag for tenant B
    update_response = client.post(
        "/api/admin/feature-flags",
        headers={**platform_headers, "X-Tenant-ID": str(tenant_b_id)},
        json={"key": "admin.local_users.tab", "enabled": False, "scope": "tenant"},
    )
    assert update_response.status_code == 200, update_response.text

    tenant_a_list = client.get("/api/admin/feature-flags", headers=platform_headers)
    tenant_b_list = client.get(
        "/api/admin/feature-flags",
        headers={**platform_headers, "X-Tenant-ID": str(tenant_b_id)},
    )
    assert tenant_a_list.status_code == 200, tenant_a_list.text
    assert tenant_b_list.status_code == 200, tenant_b_list.text

    tenant_a_flag = next(item for item in tenant_a_list.json()["flags"] if item["key"] == "admin.local_users.tab")
    tenant_b_flag = next(item for item in tenant_b_list.json()["flags"] if item["key"] == "admin.local_users.tab")

    assert tenant_a_flag["enabled"] is True
    assert tenant_b_flag["enabled"] is False
    assert tenant_b_flag["scope"] == "tenant"


def test_feature_flag_mutation_is_audited() -> None:
    response = client.post(
        "/api/admin/feature-flags",
        headers=ADMIN_HEADERS,
        json={"key": "admin.local_users.tab", "enabled": False, "scope": "tenant"},
    )
    assert response.status_code == 200, response.text

    events_response = client.get("/api/admin/audit/events", headers=ADMIN_HEADERS)
    assert events_response.status_code == 200, events_response.text
    actions = [item.get("action") for item in events_response.json().get("events", [])]
    assert "feature_flags.upsert" in actions


def test_feature_flag_rollout_percentage() -> None:
    """Platform feature flag supports rollout_percentage (stored and returned)."""
    platform_headers = _auth_headers("pf.rollout@example.com", ["superadmin"])

    set_resp = client.post(
        "/api/admin/feature-flags",
        headers=platform_headers,
        json={"key": "beta.new_dashboard", "enabled": True, "scope": "tenant"},
    )
    assert set_resp.status_code == 200, set_resp.text
    data = set_resp.json()["flag"]
    assert data["key"] == "beta.new_dashboard"
    assert data["enabled"] is True
    assert "rollout_percentage" in data


def test_platform_feature_flags_list_and_set_via_admin_api() -> None:
    """GET/PUT /api/v1/admin/features endpoints work end-to-end (in-memory store)."""
    platform_headers = _auth_headers("pf.admin@example.com", ["superadmin"])

    # PUT platform-level flag
    put_resp = client.put(
        "/api/v1/admin/features/analytics/beta_charts",
        headers=platform_headers,
        json={"enabled": True, "rollout_percentage": 50},
    )
    assert put_resp.status_code == 200, put_resp.text
    put_data = put_resp.json()
    assert put_data["module"] == "analytics"
    assert put_data["key"] == "beta_charts"
    assert put_data["enabled"] is True
    assert put_data["rollout_percentage"] == 50

    # GET platform features list
    list_resp = client.get("/api/v1/admin/features", headers=platform_headers)
    assert list_resp.status_code == 200, list_resp.text
    flags = list_resp.json()
    assert isinstance(flags, list)
    found = next((f for f in flags if f["module"] == "analytics" and f["key"] == "beta_charts"), None)
    assert found is not None
    assert found["rollout_percentage"] == 50