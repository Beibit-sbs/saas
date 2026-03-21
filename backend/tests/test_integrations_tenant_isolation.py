from tests.conftest import ADMIN_HEADERS, client


def _tenant_headers(tenant_id: int) -> dict[str, str]:
    headers = dict(ADMIN_HEADERS)
    headers["X-Tenant-ID"] = str(tenant_id)
    return headers


def _create_tenant_b() -> int:
    response = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": "tenant-b-integrations", "name": "Tenant B Integrations", "status": "active"},
    )
    assert response.status_code == 200, response.text
    return int(response.json()["tenant"]["id"])


def test_integrations_settings_are_isolated_per_tenant() -> None:
    tenant_b_id = _create_tenant_b()

    response = client.put(
        "/api/admin/integrations/ldap",
        headers=_tenant_headers(tenant_b_id),
        json={"enabled": True, "server_uri": "ldap://tenant-b.example.local:389"},
    )
    assert response.status_code == 200, response.text

    response = client.put(
        "/api/admin/integrations/ai/openai",
        headers=_tenant_headers(tenant_b_id),
        json={"api_key": "tenant-b-openai-key", "validation_url": "https://tenant-b.example.local/models"},
    )
    assert response.status_code == 200, response.text

    tenant_a_settings = client.get("/api/admin/integrations/settings", headers=ADMIN_HEADERS)
    assert tenant_a_settings.status_code == 200, tenant_a_settings.text
    assert tenant_a_settings.json()["ldap"]["server_uri"] != "ldap://tenant-b.example.local:389"

    tenant_b_settings = client.get("/api/admin/integrations/settings", headers=_tenant_headers(tenant_b_id))
    assert tenant_b_settings.status_code == 200, tenant_b_settings.text
    assert tenant_b_settings.json()["ldap"]["server_uri"] == "ldap://tenant-b.example.local:389"

    tenant_a_openai = next(
        item
        for item in tenant_a_settings.json()["ai_providers"]
        if item["provider"] == "openai"
    )
    tenant_b_openai = next(
        item
        for item in tenant_b_settings.json()["ai_providers"]
        if item["provider"] == "openai"
    )
    assert tenant_a_openai["has_api_key"] is False
    assert tenant_b_openai["has_api_key"] is True