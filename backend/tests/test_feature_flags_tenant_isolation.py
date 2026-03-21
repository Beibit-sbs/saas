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

    denied_update = client.post(
        "/api/admin/feature-flags",
        headers=_tenant_headers(tenant_b_id),
        json={
            "key": "admin.local_users.tab",
            "enabled": False,
            "description": "Tenant B override",
            "scope": "tenant",
        },
    )
    assert denied_update.status_code == 403, denied_update.text
    assert "cross-tenant override forbidden" in str(denied_update.json().get("detail", ""))

    platform_headers = _auth_headers("platform.root@example.com", ["superadmin"])
    monkeypatch.setattr("app.modules.rbac.security.is_platform_admin", lambda actor: actor == "platform.root@example.com")

    update_response = client.post(
        "/api/admin/feature-flags",
        headers={**platform_headers, "X-Tenant-ID": str(tenant_b_id)},
        json={
            "key": "admin.local_users.tab",
            "enabled": False,
            "description": "Tenant B override",
            "scope": "tenant",
        },
    )
    assert update_response.status_code == 200, update_response.text

    tenant_a_list = client.get("/api/admin/feature-flags", headers=ADMIN_HEADERS)
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
        json={
            "key": "admin.local_users.tab",
            "enabled": False,
            "description": "Audit check",
            "scope": "tenant",
        },
    )
    assert response.status_code == 200, response.text

    events_response = client.get("/api/admin/audit/events", headers=ADMIN_HEADERS)
    assert events_response.status_code == 200, events_response.text
    actions = [item.get("action") for item in events_response.json().get("events", [])]
    assert "feature_flags.upsert" in actions