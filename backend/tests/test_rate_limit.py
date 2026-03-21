from tests.conftest import ADMIN_HEADERS, client
from app.modules.audit import service as audit_service
from app.modules.security import rate_limit as rate_limit_service
from starlette.requests import Request


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


def test_extract_client_ip_prefers_x_real_ip() -> None:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/meta",
            "headers": [
                (b"x-real-ip", b"10.10.10.10"),
                (b"x-forwarded-for", b"1.1.1.1, 2.2.2.2"),
            ],
            "client": ("127.0.0.1", 12345),
        }
    )

    assert rate_limit_service._extract_client_ip(request) == "10.10.10.10"


def test_extract_client_ip_uses_rightmost_x_forwarded_for() -> None:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/meta",
            "headers": [(b"x-forwarded-for", b"1.1.1.1, 2.2.2.2, 3.3.3.3")],
            "client": ("127.0.0.1", 12345),
        }
    )

    assert rate_limit_service._extract_client_ip(request) == "3.3.3.3"


class _FakeRedis:
    def __init__(self) -> None:
        self._store: dict[str, list[float]] = {}

    def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        rows = self._store.get(key, [])
        kept = [score for score in rows if not (float(min_score) <= score <= float(max_score))]
        removed = len(rows) - len(kept)
        self._store[key] = kept
        return removed

    def zcard(self, key: str) -> int:
        return len(self._store.get(key, []))

    def zrange(self, key: str, start: int, stop: int, withscores: bool = False):
        rows = sorted(self._store.get(key, []))
        if not rows:
            return []
        sliced = rows[start : stop + 1 if stop >= 0 else None]
        if withscores:
            return [("member", value) for value in sliced]
        return ["member" for _ in sliced]

    def zadd(self, key: str, mapping: dict[str, float]) -> int:
        rows = self._store.setdefault(key, [])
        rows.extend(float(value) for value in mapping.values())
        return 1

    def expire(self, key: str, seconds: int) -> bool:
        return True

    def scan_iter(self, pattern: str):
        for key in list(self._store.keys()):
            yield key

    def delete(self, key: str) -> int:
        self._store.pop(key, None)
        return 1


def test_rate_limit_uses_redis_store_when_available(monkeypatch) -> None:
    rate_limit_service.clear_rate_limit_state()
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_GENERAL_WINDOW_SECONDS", "60")
    monkeypatch.setenv("RATE_LIMIT_GENERAL_LIMIT", "2")
    fake_redis = _FakeRedis()
    monkeypatch.setattr(rate_limit_service, "_get_rate_limit_redis_client", lambda: fake_redis)

    first = client.get("/api/meta")
    second = client.get("/api/meta")
    third = client.get("/api/meta")

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429


def test_rate_limit_falls_back_to_memory_when_redis_unavailable(monkeypatch) -> None:
    rate_limit_service.clear_rate_limit_state()
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_GENERAL_WINDOW_SECONDS", "60")
    monkeypatch.setenv("RATE_LIMIT_GENERAL_LIMIT", "2")

    class _BrokenRedis:
        def zremrangebyscore(self, *args, **kwargs):
            raise RuntimeError("redis unavailable")

    monkeypatch.setattr(rate_limit_service, "_get_rate_limit_redis_client", lambda: _BrokenRedis())

    first = client.get("/api/meta")
    second = client.get("/api/meta")
    third = client.get("/api/meta")

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
