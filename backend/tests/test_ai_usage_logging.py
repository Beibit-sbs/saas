from tests.conftest import ADMIN_HEADERS, client

from app.modules.ai_gateway import service as ai_service


def test_ai_usage_log_records_success(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    upsert_response = client.put(
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
    assert upsert_response.status_code == 200

    def fake_request_json(method: str, url: str, *, headers, params=None, payload=None):
        return {
            "id": "chatcmpl-1",
            "choices": [{"finish_reason": "stop", "message": {"content": "ok"}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
        }

    monkeypatch.setattr(ai_service, "_request_json", fake_request_json)

    response = client.post(
        "/api/ai/chat",
        headers=ADMIN_HEADERS,
        json={
            "model": "openai.default.chat",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )
    assert response.status_code == 200

    logs = ai_service.list_usage_logs(limit=10, tenant_id=1)
    assert logs
    assert logs[0]["outcome"] == "success"
    assert logs[0]["actor"] == "owner@example.com"
    assert logs[0]["provider"] == "openai"
    assert logs[0]["model_key"] == "openai.default.chat"
    assert logs[0]["total_tokens"] == 5


def test_ai_usage_log_records_failure(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    upsert_response = client.put(
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
    assert upsert_response.status_code == 200

    def fake_error(*args, **kwargs):
        raise ai_service.AIProviderExecutionError("provider failed")

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

    logs = ai_service.list_usage_logs(limit=10, tenant_id=1)
    assert logs
    assert logs[0]["outcome"] == "failed"
    assert logs[0]["failure_reason"]
