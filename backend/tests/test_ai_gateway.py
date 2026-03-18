from tests.conftest import ADMIN_HEADERS, _auth_headers, client
from app.modules.ai_gateway import service as ai_service
from app.modules.rbac import service as rbac_service


def test_ai_providers_endpoint() -> None:
    response = client.get("/api/admin/ai/providers", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert "providers" in response.json()


def test_ai_provider_validation_for_unknown_provider() -> None:
    response = client.post("/api/admin/ai/providers/unknown/validate", headers=ADMIN_HEADERS)
    assert response.status_code == 400


def test_ai_provider_runtime_validation(monkeypatch) -> None:
    ai_service.clear_rate_limit_state()
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class FakeResponse:
        status_code = 200
        text = "ok"

    def fake_request(method: str, url: str, headers: dict[str, str], params: dict[str, str] | None):
        assert method == "GET"
        assert "openai" in url
        assert headers["Authorization"] == "Bearer test-key"
        return FakeResponse()

    monkeypatch.setattr(ai_service, "_request", fake_request)

    response = client.post("/api/admin/ai/providers/openai/validate", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["result"]["status"] == "validated"
    assert response.json()["result"]["rate_limit"]["user_used"] == 1


def test_ai_provider_rate_limit_per_user(monkeypatch) -> None:
    ai_service.clear_rate_limit_state()
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AI_RATE_LIMIT_USER_LIMIT", "1")
    monkeypatch.setenv("AI_RATE_LIMIT_ROLE_LIMIT", "5")
    monkeypatch.setenv("AI_RATE_LIMIT_PROVIDER_OPENAI_LIMIT", "5")

    class FakeResponse:
        status_code = 200
        text = "ok"

    monkeypatch.setattr(ai_service, "_request", lambda method, url, headers, params: FakeResponse())

    first = client.post("/api/admin/ai/providers/openai/validate", headers=ADMIN_HEADERS)
    second = client.post("/api/admin/ai/providers/openai/validate", headers=ADMIN_HEADERS)

    assert first.status_code == 200
    assert second.status_code == 429
    assert "user:owner@example.com" in second.json()["detail"]


def test_ai_provider_rate_limit_per_role(monkeypatch) -> None:
    ai_service.clear_rate_limit_state()
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AI_RATE_LIMIT_USER_LIMIT", "5")
    monkeypatch.setenv("AI_RATE_LIMIT_ROLE_LIMIT", "1")
    monkeypatch.setenv("AI_RATE_LIMIT_PROVIDER_OPENAI_LIMIT", "5")

    class FakeResponse:
        status_code = 200
        text = "ok"

    monkeypatch.setattr(ai_service, "_request", lambda method, url, headers, params: FakeResponse())
    monkeypatch.setattr(
        rbac_service,
        "_get_user_roles_db",
        lambda user_id: ["admin"] if user_id in {"owner@example.com", "reviewer@example.com"} else [],
    )

    first = client.post(
        "/api/admin/ai/providers/openai/validate",
        headers=_auth_headers("owner@example.com", ["admin"]),
    )
    second = client.post(
        "/api/admin/ai/providers/openai/validate",
        headers=_auth_headers("reviewer@example.com", ["admin"]),
    )

    assert first.status_code == 200
    assert second.status_code == 429
    assert "role:admin" in second.json()["detail"]


def test_ai_provider_rate_limit_per_provider(monkeypatch) -> None:
    ai_service.clear_rate_limit_state()
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AI_RATE_LIMIT_USER_LIMIT", "5")
    monkeypatch.setenv("AI_RATE_LIMIT_ROLE_LIMIT", "5")
    monkeypatch.setenv("AI_RATE_LIMIT_PROVIDER_OPENAI_LIMIT", "1")

    class FakeResponse:
        status_code = 200
        text = "ok"

    monkeypatch.setattr(ai_service, "_request", lambda method, url, headers, params: FakeResponse())
    monkeypatch.setattr(
        rbac_service,
        "_get_user_roles_db",
        lambda user_id: ["admin"] if user_id in {"owner@example.com", "reviewer@example.com"} else [],
    )

    first = client.post(
        "/api/admin/ai/providers/openai/validate",
        headers=_auth_headers("owner@example.com", ["admin"]),
    )
    second = client.post(
        "/api/admin/ai/providers/openai/validate",
        headers=_auth_headers("reviewer@example.com", ["admin"]),
    )

    assert first.status_code == 200
    assert second.status_code == 429
    assert "provider:openai" in second.json()["detail"]
