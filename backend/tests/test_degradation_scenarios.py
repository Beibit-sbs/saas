"""ERP-QA G4 — Graceful degradation scenario tests.

Verifies that the system behaves predictably when key dependencies degrade:
  1. DB unavailable → in-memory fallback where supported, error where not.
  2. Redis unavailable → rate-limiting fails-open, token revocation fails-closed.
  3. AI provider unavailable → deterministic degraded fallback response.

These tests run in the standard no-DB unit-test environment using monkeypatched
dependencies.  No external services required.
"""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth import token_service
from app.modules.security import rate_limit as rate_limit_mod

client = TestClient(app)


# ---------------------------------------------------------------------------
# Scenario 1: Redis unavailable — token revocation fails-closed
# ---------------------------------------------------------------------------


class TestRedisUnavailableTokenRevocation:
    """When Redis is configured but unreachable, token revocation must
    fail-closed: treat every token as revoked to prevent unauthorized access."""

    def test_revocation_check_returns_true_when_redis_unreachable(self, monkeypatch):
        """is_token_revoked must return True when Redis raises."""
        mock_client = MagicMock()
        mock_client.exists.side_effect = ConnectionError("redis down")

        monkeypatch.setattr(
            token_service, "_get_redis_client", lambda: mock_client
        )

        assert token_service.is_token_revoked("some-jti-value") is True

    def test_revocation_check_returns_false_when_redis_works(self, monkeypatch):
        """Baseline: when Redis is up and jti not revoked, return False."""
        mock_client = MagicMock()
        mock_client.exists.return_value = 0

        monkeypatch.setattr(
            token_service, "_get_redis_client", lambda: mock_client
        )

        assert token_service.is_token_revoked("some-jti-value") is False


# ---------------------------------------------------------------------------
# Scenario 2: Redis unavailable — rate limiting fails-open to in-memory
# ---------------------------------------------------------------------------


class TestRedisUnavailableRateLimit:
    """When Redis is unreachable, rate limiting must fall back to in-memory
    enforcement (fail-open to in-memory, not fail-open to no-limit)."""

    def test_rate_limit_falls_back_to_memory_when_redis_fails(self, monkeypatch):
        """Rate limiter should not raise when Redis is down; it should use
        the in-memory fallback path."""
        mock_client = MagicMock()
        mock_client.eval.side_effect = ConnectionError("redis down")

        # Bypass lru_cache by patching the module-level function
        monkeypatch.setattr(
            rate_limit_mod, "_get_rate_limit_redis_client", lambda: mock_client
        )

        # Should not raise — falls back to in-memory
        decision = rate_limit_mod._enforce_checks(
            scope="test-degradation",
            checks=[
                rate_limit_mod.LimitCheck(
                    bucket_key=("degradation", "test", "fallback"),
                    limit=100,
                    window_seconds=60,
                    label="test",
                ),
            ],
        )
        # With a limit of 100 and a single call, should not be throttled
        assert decision is None

    def test_rate_limit_enforces_in_memory_when_redis_fails(self, monkeypatch):
        """In-memory fallback must still enforce limits."""
        mock_client = MagicMock()
        mock_client.eval.side_effect = ConnectionError("redis down")

        monkeypatch.setattr(
            rate_limit_mod, "_get_rate_limit_redis_client", lambda: mock_client
        )

        check = rate_limit_mod.LimitCheck(
            bucket_key=("degradation", "exhaust", "inmem"),
            limit=2,
            window_seconds=60,
            label="exhaust-test",
        )

        for _ in range(2):
            rate_limit_mod._enforce_checks(scope="exhaust-test", checks=[check])

        # Third call should be throttled
        decision = rate_limit_mod._enforce_checks(
            scope="exhaust-test", checks=[check]
        )
        assert decision is not None
        assert decision.retry_after > 0


# ---------------------------------------------------------------------------
# Scenario 3: AI provider unavailable — degraded fallback
# ---------------------------------------------------------------------------


class TestAIProviderDegraded:
    """When the AI provider is unreachable or errors, the gateway must
    return a deterministic degraded fallback (HTTP 200, degraded=True)."""

    def test_degraded_fallback_result_structure(self):
        """Verify _degraded_fallback_result returns the expected shape."""
        from app.modules.ai_gateway import service as ai_svc

        result = ai_svc._degraded_fallback_result(
            model_key="test-model",
            provider="test-provider",
            provider_model_id="test-model-v1",
            latency_ms=150.0,
            degraded_reason="provider_timeout",
        )

        assert result["degraded"] is True
        assert result["degraded_reason"] == "provider_timeout"
        assert result["finish_reason"] == "degraded_fallback"
        assert "temporarily unavailable" in result["output_text"]
        assert result["model"] == "test-model"
        assert result["latency_ms"] == 150.0

    def test_execute_chat_timeout_returns_degraded(self, monkeypatch):
        """A provider timeout must yield degraded fallback, not an error."""
        from app.modules.ai_gateway import service as ai_svc

        tenant_key = "1:test-model"
        monkeypatch.setitem(
            ai_svc._model_registry,
            tenant_key,
            {
                "provider": "openai",
                "provider_model_id": "gpt-test",
                "model_key": "test-model",
                "enabled": True,
            },
        )

        # Patch the adapter to raise a timeout
        mock_adapter = MagicMock()
        mock_adapter.execute_chat.side_effect = ai_svc.AIProviderTimeoutError("timeout")
        monkeypatch.setattr(ai_svc, "_adapter_for_provider", lambda p: mock_adapter)
        monkeypatch.setattr(ai_svc, "enforce_rate_limit", lambda *a, **kw: None)

        result = ai_svc.execute_chat(
            {"model": "test-model", "messages": [{"role": "user", "content": "test"}]},
            actor="test@test.com",
            roles=["admin"],
            tenant_id=1,
        )
        assert result["degraded"] is True
        assert result["degraded_reason"] == "provider_timeout"

    def test_execute_chat_remote_error_returns_degraded(self, monkeypatch):
        """A remote provider error (with status_code) yields degraded fallback."""
        from app.modules.ai_gateway import service as ai_svc

        tenant_key = "1:test-model-err"
        monkeypatch.setitem(
            ai_svc._model_registry,
            tenant_key,
            {
                "provider": "openai",
                "provider_model_id": "gpt-test",
                "model_key": "test-model-err",
                "enabled": True,
            },
        )

        exc = ai_svc.AIProviderExecutionError("service unavailable")
        exc.status_code = 503

        mock_adapter = MagicMock()
        mock_adapter.execute_chat.side_effect = exc
        monkeypatch.setattr(ai_svc, "_adapter_for_provider", lambda p: mock_adapter)
        monkeypatch.setattr(ai_svc, "enforce_rate_limit", lambda *a, **kw: None)

        result = ai_svc.execute_chat(
            {"model": "test-model-err", "messages": [{"role": "user", "content": "test"}]},
            actor="test@test.com",
            roles=["admin"],
            tenant_id=1,
        )
        assert result["degraded"] is True
        assert result["degraded_reason"] == "provider_error"


# ---------------------------------------------------------------------------
# Scenario 4: DB unavailable — health endpoint reports not-ready
# ---------------------------------------------------------------------------


class TestDBUnavailableHealth:
    """When PostgreSQL is down, the readiness probe must report 503."""

    def test_health_live_always_ok(self):
        """/health/live must always return 200 regardless of backend state."""
        resp = client.get("/health/live")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["live"] is True

    def test_health_ready_503_when_db_unavailable(self, monkeypatch):
        """Readiness check should return 503 when DB is not reachable."""
        from app.modules.observability import health as health_mod

        def _broken_pg(app_instance):
            return health_mod._dependency_payload(
                name="postgresql",
                healthy=False,
                critical=True,
                details={"reason": "connection refused"},
            )

        monkeypatch.setattr(health_mod, "_postgres_dependency", _broken_pg)

        resp = client.get("/health/ready")
        assert resp.status_code == 503
        data = resp.json()
        assert data["ready"] is False


# ---------------------------------------------------------------------------
# Scenario 5: DB unavailable — platform services fall back to in-memory
# ---------------------------------------------------------------------------


class TestDBUnavailableFallback:
    """Platform services with in-memory fallback must continue operating
    when db_available() returns False."""

    def test_platform_repository_db_available_returns_false_without_url(self, monkeypatch):
        """db_available() must return False when DATABASE_URL is absent."""
        from app.platform.repository import db as platform_db

        monkeypatch.setattr(platform_db, "db_url", lambda: "")

        assert platform_db.db_available() is False

    def test_tenant_service_fallback_predicate_catches_db_errors(self):
        """The _should_fallback_to_memory helper must catch DB-class errors."""
        from app.modules.tenants import service as tenant_svc

        if hasattr(tenant_svc, "_should_fallback_to_memory"):
            # OperationalError, ConnectionError, TimeoutError, OSError
            assert tenant_svc._should_fallback_to_memory(ConnectionError("db down")) is True
            assert tenant_svc._should_fallback_to_memory(TimeoutError("db timeout")) is True
            assert tenant_svc._should_fallback_to_memory(OSError("network error")) is True
            # ValueError is NOT a DB error — should not fallback
            assert tenant_svc._should_fallback_to_memory(ValueError("bad input")) is False
