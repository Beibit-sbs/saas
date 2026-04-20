"""Additional tests for the AI Gateway module — model CRUD endpoints.

The existing test_ai_gateway.py covers provider status/validation and rate
limiting.  These tests add coverage for the model registry endpoints:
  GET  /api/admin/ai/models
  PUT  /api/admin/ai/models/{key}
  PATCH /api/admin/ai/models/{key}/enabled
"""

from __future__ import annotations

from tests.conftest import ADMIN_HEADERS, _auth_headers, client
from app.modules.ai_gateway import service as ai_service


# ---------------------------------------------------------------------------
# GET /api/admin/ai/models
# ---------------------------------------------------------------------------

def test_list_models_returns_200() -> None:
    resp = client.get("/api/admin/ai/models", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "models" in body
    assert isinstance(body["models"], list)


def test_list_models_unauthenticated() -> None:
    resp = client.get("/api/admin/ai/models")
    assert resp.status_code in (401, 403)


def test_list_models_viewer_blocked() -> None:
    headers = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.get("/api/admin/ai/models", headers=headers)
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PUT /api/admin/ai/models/{model_key} — upsert
# ---------------------------------------------------------------------------

def test_upsert_model_creates_entry() -> None:
    payload = {
        "provider": "openai",
        "provider_model_id": "gpt-4o-mini-test",
        "display_name": "GPT-4o Mini Test",
        "enabled": True,
        "priority": 50,
    }
    resp = client.put("/api/admin/ai/models/test-model-1", headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code == 200
    model = resp.json()["model"]
    assert model["model_key"] == "test-model-1"
    assert model["provider"] == "openai"
    assert model["enabled"] is True
    assert model["priority"] == 50


def test_upsert_model_update_existing() -> None:
    """PUT the same key again → should update."""
    payload_v1 = {
        "provider": "openai",
        "provider_model_id": "gpt-4o",
        "display_name": "GPT-4o V1",
        "enabled": True,
        "priority": 100,
    }
    client.put("/api/admin/ai/models/update-test", headers=ADMIN_HEADERS, json=payload_v1)

    payload_v2 = {
        "provider": "openai",
        "provider_model_id": "gpt-4o",
        "display_name": "GPT-4o V2",
        "enabled": False,
        "priority": 200,
    }
    resp = client.put("/api/admin/ai/models/update-test", headers=ADMIN_HEADERS, json=payload_v2)
    assert resp.status_code == 200
    model = resp.json()["model"]
    assert model["display_name"] == "GPT-4o V2"
    assert model["enabled"] is False
    assert model["priority"] == 200


def test_upsert_model_invalid_provider() -> None:
    payload = {
        "provider": "nonexistent",
        "provider_model_id": "x",
        "display_name": "X",
    }
    resp = client.put("/api/admin/ai/models/bad-prov", headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code == 422  # Literal validation


def test_upsert_model_empty_display_name() -> None:
    payload = {
        "provider": "openai",
        "provider_model_id": "gpt-4o",
        "display_name": "",
    }
    resp = client.put("/api/admin/ai/models/bad-name", headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code == 422


def test_upsert_model_empty_provider_model_id() -> None:
    payload = {
        "provider": "openai",
        "provider_model_id": "",
        "display_name": "Valid Name",
    }
    resp = client.put("/api/admin/ai/models/bad-mid", headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code == 422


def test_upsert_model_priority_out_of_range() -> None:
    payload = {
        "provider": "openai",
        "provider_model_id": "gpt-4o",
        "display_name": "Valid",
        "priority": 99999,  # max 10000
    }
    resp = client.put("/api/admin/ai/models/bad-prio", headers=ADMIN_HEADERS, json=payload)
    assert resp.status_code == 422


def test_upsert_model_unauthenticated() -> None:
    payload = {"provider": "openai", "provider_model_id": "x", "display_name": "X"}
    resp = client.put("/api/admin/ai/models/no-auth", json=payload)
    assert resp.status_code in (401, 403)


def test_upsert_model_viewer_blocked() -> None:
    headers = _auth_headers("viewer@example.com", ["viewer"])
    payload = {"provider": "openai", "provider_model_id": "x", "display_name": "X"}
    resp = client.put("/api/admin/ai/models/viewer-m", headers=headers, json=payload)
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /api/admin/ai/models/{model_key}/enabled
# ---------------------------------------------------------------------------

def test_set_model_enabled_toggle() -> None:
    """Create a model, then disable it."""
    client.put(
        "/api/admin/ai/models/toggle-test",
        headers=ADMIN_HEADERS,
        json={
            "provider": "anthropic",
            "provider_model_id": "claude-3-sonnet",
            "display_name": "Claude 3 Sonnet",
            "enabled": True,
        },
    )
    resp = client.patch(
        "/api/admin/ai/models/toggle-test/enabled",
        headers=ADMIN_HEADERS,
        json={"enabled": False},
    )
    assert resp.status_code == 200
    assert resp.json()["model"]["enabled"] is False


def test_set_model_enabled_nonexistent() -> None:
    resp = client.patch(
        "/api/admin/ai/models/no-such-model/enabled",
        headers=ADMIN_HEADERS,
        json={"enabled": True},
    )
    assert resp.status_code == 404


def test_set_model_enabled_missing_field() -> None:
    resp = client.patch(
        "/api/admin/ai/models/toggle-test/enabled",
        headers=ADMIN_HEADERS,
        json={},
    )
    assert resp.status_code == 422


def test_set_model_enabled_unauthenticated() -> None:
    resp = client.patch(
        "/api/admin/ai/models/any/enabled",
        json={"enabled": True},
    )
    assert resp.status_code in (401, 403)


def test_set_model_enabled_viewer_blocked() -> None:
    headers = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.patch(
        "/api/admin/ai/models/any/enabled",
        headers=headers,
        json={"enabled": True},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Model appears in list after creation
# ---------------------------------------------------------------------------

def test_created_model_appears_in_list() -> None:
    key = "list-check-model"
    client.put(
        f"/api/admin/ai/models/{key}",
        headers=ADMIN_HEADERS,
        json={
            "provider": "gemini",
            "provider_model_id": "gemini-1.5-pro",
            "display_name": "Gemini 1.5 Pro",
            "enabled": True,
        },
    )
    resp = client.get("/api/admin/ai/models", headers=ADMIN_HEADERS)
    models = resp.json()["models"]
    keys = [m["model_key"] for m in models]
    assert key in keys


def test_gemini_and_custom_providers_accepted() -> None:
    """All four Literal providers should be accepted."""
    for provider, mid in [("gemini", "gemini-2.0"), ("custom", "my-custom-v1")]:
        resp = client.put(
            f"/api/admin/ai/models/prov-{provider}",
            headers=ADMIN_HEADERS,
            json={
                "provider": provider,
                "provider_model_id": mid,
                "display_name": f"Test {provider}",
            },
        )
        assert resp.status_code == 200, f"Provider {provider} failed: {resp.text}"
