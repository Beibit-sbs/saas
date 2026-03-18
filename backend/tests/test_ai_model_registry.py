from tests.conftest import ADMIN_HEADERS, _auth_headers, client


def test_model_registry_list_and_upsert_and_soft_disable() -> None:
    list_response = client.get("/api/admin/ai/models", headers=ADMIN_HEADERS)
    assert list_response.status_code == 200
    assert "models" in list_response.json()

    upsert_response = client.put(
        "/api/admin/ai/models/template.chat.openai",
        headers=ADMIN_HEADERS,
        json={
            "provider": "openai",
            "provider_model_id": "gpt-4o-mini",
            "display_name": "Template OpenAI Chat",
            "enabled": True,
            "priority": 10,
            "metadata": {"tier": "default"},
        },
    )
    assert upsert_response.status_code == 200
    assert upsert_response.json()["model"]["model_key"] == "template.chat.openai"
    assert upsert_response.json()["model"]["enabled"] is True

    disable_response = client.patch(
        "/api/admin/ai/models/template.chat.openai/enabled",
        headers=ADMIN_HEADERS,
        json={"enabled": False},
    )
    assert disable_response.status_code == 200
    assert disable_response.json()["model"]["enabled"] is False


def test_model_registry_management_requires_permission() -> None:
    low_priv_headers = _auth_headers("student.009", ["student"])

    response = client.get("/api/admin/ai/models", headers=low_priv_headers)
    assert response.status_code == 403

    upsert_response = client.put(
        "/api/admin/ai/models/blocked.model",
        headers=low_priv_headers,
        json={
            "provider": "openai",
            "provider_model_id": "gpt-4o-mini",
            "display_name": "Blocked",
            "enabled": True,
            "priority": 20,
        },
    )
    assert upsert_response.status_code == 403


def test_model_registry_changes_are_audited() -> None:
    response = client.put(
        "/api/admin/ai/models/template.chat.audit",
        headers=ADMIN_HEADERS,
        json={
            "provider": "gemini",
            "provider_model_id": "gemini-1.5-flash",
            "display_name": "Template Gemini Chat",
            "enabled": True,
            "priority": 30,
        },
    )
    assert response.status_code == 200

    events_response = client.get(
        "/api/admin/audit/events?action=ai.models.upsert",
        headers=ADMIN_HEADERS,
    )
    assert events_response.status_code == 200
    events = events_response.json()["events"]
    assert events
    assert events[0]["action"] == "ai.models.upsert"
    assert events[0]["entity"] == "ai_gateway"
