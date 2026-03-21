from tests.conftest import ADMIN_HEADERS, client
from app.modules.audit import service as audit_service
from app.modules.security import rate_limit as rate_limit_service


def test_mock_login_rate_limit_returns_429_and_audits(monkeypatch) -> None:
    client.cookies.clear()
    audit_service.clear_audit_events()
    rate_limit_service.clear_rate_limit_state()
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_GENERAL_LIMIT", "0")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_WINDOW_SECONDS", "60")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_IP_LIMIT", "2")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_IDENTIFIER_LIMIT", "2")

    first = client.post("/api/auth/mock-login", json={"login": "admin", "password": "wrong"})
    second = client.post("/api/auth/mock-login", json={"login": "admin", "password": "wrong"})
    third = client.post("/api/auth/mock-login", json={"login": "admin", "password": "wrong"})

    assert first.status_code == 401
    assert second.status_code == 401
    assert third.status_code == 429
    assert int(third.headers["Retry-After"]) >= 59
    assert "rate limit exceeded" in third.json()["detail"]

    events_response = client.get("/api/admin/audit/events", headers=ADMIN_HEADERS)
    assert events_response.status_code == 200
    abuse_events = [item for item in events_response.json()["events"] if item["action"] == "rate_limit_exceeded"]
    assert abuse_events
    assert abuse_events[0]["actor"] == "anonymous"
    assert abuse_events[0]["entity"] == "security_abuse"
    assert abuse_events[0]["result"] == "blocked"
    assert abuse_events[0]["metadata"]["path"] == "/api/auth/mock-login"
    assert "password" not in abuse_events[0]["metadata"]


def test_sensitive_admin_rate_limit_returns_429_and_audits(monkeypatch) -> None:
    audit_service.clear_audit_events()
    rate_limit_service.clear_rate_limit_state()
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_GENERAL_LIMIT", "0")
    monkeypatch.setenv("RATE_LIMIT_SENSITIVE_ADMIN_WINDOW_SECONDS", "60")
    monkeypatch.setenv("RATE_LIMIT_SENSITIVE_ADMIN_LIMIT", "1")
    monkeypatch.setattr(
        "app.modules.ldap.router.test_ldap_connection",
        lambda username, password, tenant_id=None: {"status": "ok", "bind": bool(username)},
    )

    first = client.post("/api/admin/ldap/test-connection", headers=ADMIN_HEADERS, json={"username": "user", "password": "secret"})
    second = client.post("/api/admin/ldap/test-connection", headers=ADMIN_HEADERS, json={"username": "user", "password": "secret"})

    assert first.status_code == 200
    assert second.status_code == 429
    assert int(second.headers["Retry-After"]) >= 59

    events_response = client.get("/api/admin/audit/events", headers=ADMIN_HEADERS)
    assert events_response.status_code == 200
    abuse_events = [item for item in events_response.json()["events"] if item["action"] == "rate_limit_exceeded"]
    assert abuse_events
    assert abuse_events[0]["actor"] == "owner@example.com"
    assert abuse_events[0]["metadata"]["path"] == "/api/admin/ldap/test-connection"
    assert abuse_events[0]["metadata"]["scope"] == "sensitive_admin"


def test_general_api_rate_limit_returns_429(monkeypatch) -> None:
    rate_limit_service.clear_rate_limit_state()
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_IP_LIMIT", "0")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_IDENTIFIER_LIMIT", "0")
    monkeypatch.setenv("RATE_LIMIT_SENSITIVE_ADMIN_LIMIT", "0")
    monkeypatch.setenv("RATE_LIMIT_GENERAL_WINDOW_SECONDS", "60")
    monkeypatch.setenv("RATE_LIMIT_GENERAL_LIMIT", "2")

    first = client.get("/api/meta")
    second = client.get("/api/meta")
    third = client.get("/api/meta")

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert int(third.headers["Retry-After"]) >= 59


def test_general_api_limit_exempts_health(monkeypatch) -> None:
    rate_limit_service.clear_rate_limit_state()
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_GENERAL_WINDOW_SECONDS", "60")
    monkeypatch.setenv("RATE_LIMIT_GENERAL_LIMIT", "1")

    first = client.get("/api/health")
    second = client.get("/api/health")
    third = client.get("/api/health")

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 200
