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
            "slug": "tenant-b-ai-registry",
            "name": "Tenant B AI Registry",
            "status": "active",
        },
    )
    assert response.status_code == 200, response.text
    return int(response.json()["tenant"]["id"])


def test_tenant_b_cannot_see_tenant_a_custom_ai_model() -> None:
    tenant_b_id = _create_tenant_b()

    upsert_a = client.put(
        "/api/admin/ai/models/tenant.a.only.model",
        headers=ADMIN_HEADERS,
        json={
            "provider": "openai",
            "provider_model_id": "gpt-4o-mini",
            "display_name": "Tenant A Only Model",
            "enabled": True,
            "priority": 33,
            "metadata": {"scope": "tenant-a"},
        },
    )
    assert upsert_a.status_code == 200, upsert_a.text

    list_a = client.get("/api/admin/ai/models", headers=ADMIN_HEADERS)
    assert list_a.status_code == 200, list_a.text
    models_a = list_a.json()["models"]
    assert any(item["model_key"] == "tenant.a.only.model" for item in models_a)

    list_b = client.get("/api/admin/ai/models", headers=_tenant_headers(tenant_b_id))
    assert list_b.status_code == 403, list_b.text


def test_tenant_b_cannot_mutate_tenant_a_custom_ai_model() -> None:
    tenant_b_id = _create_tenant_b()

    upsert_a = client.put(
        "/api/admin/ai/models/tenant.a.locked.model",
        headers=ADMIN_HEADERS,
        json={
            "provider": "gemini",
            "provider_model_id": "gemini-1.5-flash",
            "display_name": "Tenant A Locked Model",
            "enabled": True,
            "priority": 44,
        },
    )
    assert upsert_a.status_code == 200, upsert_a.text

    patch_cross = client.patch(
        "/api/admin/ai/models/tenant.a.locked.model/enabled",
        headers=_tenant_headers(tenant_b_id),
        json={"enabled": False},
    )
    assert patch_cross.status_code == 403, patch_cross.text

    list_a_after = client.get("/api/admin/ai/models", headers=ADMIN_HEADERS)
    assert list_a_after.status_code == 200, list_a_after.text
    model_a = next(item for item in list_a_after.json()["models"] if item["model_key"] == "tenant.a.locked.model")
    assert model_a["enabled"] is True
