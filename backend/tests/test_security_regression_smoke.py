import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.token_service import create_access_token


pytestmark = pytest.mark.security_regression


def test_help_ask_requires_authentication() -> None:
    with TestClient(app) as local_client:
        local_client.cookies.clear()
        response = local_client.post(
            "/api/help/ask",
            json={
                "page": "admin",
                "question": "Как добавить роль?",
                "field": "role_name",
                "language": "ru",
            },
        )

    assert response.status_code == 401


def test_platform_path_is_covered_by_csrf_perimeter() -> None:
    token = create_access_token(
        user_id="platform.owner@example.com",
        roles=["superadmin"],
        auth_source="test",
    )

    with TestClient(app) as local_client:
        local_client.cookies.set("app_access_token", token)
        response = local_client.post(
            "/platform/plans",
            json={
                "code": "csrf-check",
                "name": "CSRF Check",
                "description": "csrf perimeter smoke",
                "active": True,
            },
        )

    assert response.status_code == 403
    assert response.json().get("detail") == "csrf token required"


def test_app_startup_fails_with_insecure_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "change_me")

    with pytest.raises(RuntimeError, match="JWT_SECRET must be configured"):
        with TestClient(app):
            pass


def test_metrics_requires_token_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("METRICS_TOKEN", "metrics-secret-token")
    with TestClient(app) as local_client:
        response = local_client.get("/metrics")

    assert response.status_code == 401


def test_metrics_rejects_invalid_token_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("METRICS_TOKEN", "metrics-secret-token")
    with TestClient(app) as local_client:
        response = local_client.get("/metrics", headers={"Authorization": "Bearer wrong-token"})

    assert response.status_code == 403


def test_metrics_accepts_valid_token_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("METRICS_TOKEN", "metrics-secret-token")
    with TestClient(app) as local_client:
        response = local_client.get("/metrics", headers={"Authorization": "Bearer metrics-secret-token"})

    assert response.status_code == 200
    assert "# HELP" in response.text


def test_metrics_ip_allowlist_blocks_non_allowed_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("METRICS_ALLOWED_IPS", "10.10.10.10")
    monkeypatch.setenv("METRICS_TOKEN", "metrics-secret-token")
    with TestClient(app) as local_client:
        response = local_client.get(
            "/metrics",
            headers={
                "Authorization": "Bearer metrics-secret-token",
                "X-Real-IP": "1.1.1.1",
            },
        )

    assert response.status_code == 403


def test_metrics_ip_allowlist_allows_configured_ip_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("METRICS_ALLOWED_IPS", "10.10.10.10")
    monkeypatch.setenv("METRICS_TOKEN", "metrics-secret-token")
    with TestClient(app) as local_client:
        response = local_client.get(
            "/metrics",
            headers={
                "Authorization": "Bearer metrics-secret-token",
                "X-Real-IP": "10.10.10.10",
            },
        )

    assert response.status_code == 200


def test_logout_invalidates_previous_access_and_refresh_tokens() -> None:
    with TestClient(app) as local_client:
        login = local_client.post(
            "/api/auth/mock-login",
            json={"login": "admin", "password": "admin123"},
        )
        assert login.status_code == 200
        old_access = login.json().get("access_token")
        old_refresh = login.json().get("refresh_token")
        assert isinstance(old_access, str)
        assert isinstance(old_refresh, str)

        csrf = local_client.get("/api/auth/csrf")
        assert csrf.status_code == 200
        csrf_token = csrf.json().get("csrf_token")
        assert isinstance(csrf_token, str)

        logout = local_client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf_token})
        assert logout.status_code == 200

        old_access_response = local_client.get(
            "/api/auth/me/profile",
            headers={"Authorization": f"Bearer {old_access}"},
        )
        assert old_access_response.status_code == 401

        old_refresh_response = local_client.post(
            "/api/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert old_refresh_response.status_code == 401