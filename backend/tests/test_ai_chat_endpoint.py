from tests.conftest import ADMIN_HEADERS, _auth_headers, client

from app.modules.ai_gateway import service as ai_service


def _ensure_openai_model_enabled() -> None:
    response = client.put(
        "/api/admin/ai/models/openai.default.chat",
        headers=ADMIN_HEADERS,
        json={
            "provider": "openai",
            "provider_model_id": "gpt-4o-mini",
            "display_name": "OpenAI Default Chat",
            "enabled": True,
            "priority": 100,
        },
    )
    assert response.status_code == 200


def test_ai_chat_routes_to_provider_adapter(monkeypatch) -> None:
    _ensure_openai_model_enabled()
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    def fake_request_json(method: str, url: str, *, headers, params=None, payload=None):
        assert method == "POST"
        assert "chat/completions" in url
        assert headers["Authorization"] == "Bearer test-openai-key"
        assert payload["model"] == "gpt-4o-mini"
        return {
            "id": "chatcmpl-1",
            "choices": [{"finish_reason": "stop", "message": {"content": "Hello from model"}}],
            "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
        }

    monkeypatch.setattr(ai_service, "_request_json", fake_request_json)

    response = client.post(
        "/api/ai/chat",
        headers=ADMIN_HEADERS,
        json={
            "model": "openai.default.chat",
            "messages": [{"role": "user", "content": "hello"}],
            "temperature": 0.2,
            "max_tokens": 64,
        },
    )
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["model"] == "openai.default.chat"
    assert result["provider"] == "openai"
    assert result["provider_model_id"] == "gpt-4o-mini"
    assert result["output_text"] == "Hello from model"
    assert result["usage"]["total_tokens"] == 18


def test_ai_chat_requires_permission() -> None:
    low_priv_headers = _auth_headers("student.333", ["student"])
    response = client.post(
        "/api/ai/chat",
        headers=low_priv_headers,
        json={
            "model": "openai.default.chat",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )
    assert response.status_code == 403


def test_ai_chat_rejects_disabled_model() -> None:
    disable_response = client.patch(
        "/api/admin/ai/models/openai.default.chat/enabled",
        headers=ADMIN_HEADERS,
        json={"enabled": False},
    )
    assert disable_response.status_code == 200

    response = client.post(
        "/api/ai/chat",
        headers=ADMIN_HEADERS,
        json={
            "model": "openai.default.chat",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )
    assert response.status_code == 400
    assert "disabled" in response.json()["detail"]


def test_ai_chat_normalizes_timeout_error(monkeypatch) -> None:
    _ensure_openai_model_enabled()
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    def fake_timeout(*args, **kwargs):
        raise ai_service.AIProviderTimeoutError("timeout")

    monkeypatch.setattr(ai_service._ADAPTERS["openai"], "execute_chat", fake_timeout)

    response = client.post(
        "/api/ai/chat",
        headers=ADMIN_HEADERS,
        json={
            "model": "openai.default.chat",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )
    assert response.status_code == 504
    assert "timeout" in response.json()["detail"]


def test_ai_chat_normalizes_upstream_error(monkeypatch) -> None:
    _ensure_openai_model_enabled()
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    def fake_error(*args, **kwargs):
        raise ai_service.AIProviderExecutionError("upstream broke", status_code=500)

    monkeypatch.setattr(ai_service._ADAPTERS["openai"], "execute_chat", fake_error)

    response = client.post(
        "/api/ai/chat",
        headers=ADMIN_HEADERS,
        json={
            "model": "openai.default.chat",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )
    assert response.status_code == 502
    assert "upstream AI provider error" in response.json()["detail"]
