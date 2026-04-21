from __future__ import annotations

import pytest

from app.core import config


def test_is_enabled_truthy_and_falsy() -> None:
    assert config.is_enabled("true") is True
    assert config.is_enabled("1") is True
    assert config.is_enabled("on") is True
    assert config.is_enabled("false") is False
    assert config.is_enabled(None) is False


def test_auth_modes_and_ai_provider_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_LDAP_ENABLED", "true")
    assert config.get_auth_modes() == {"local": True, "ldap": True, "api_keys": True}

    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "y")
    monkeypatch.setenv("AI_CUSTOM_PROVIDER_URL", "https://provider.local")
    assert config.get_ai_provider_status() == {
        "openai": True,
        "gemini": False,
        "anthropic": True,
        "custom": True,
    }


def test_runtime_schema_bootstrap_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RUNTIME_SCHEMA_BOOTSTRAP_ENABLED", "true")
    assert config.is_runtime_schema_bootstrap_enabled() is False
    with config.runtime_schema_bootstrap_scope():
        assert config.is_runtime_schema_bootstrap_enabled() is True
    assert config.is_runtime_schema_bootstrap_enabled() is False


def test_db_timeout_options_bounds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_STATEMENT_TIMEOUT_MS", "5")
    monkeypatch.setenv("DB_IDLE_IN_TRANSACTION_SESSION_TIMEOUT_MS", "9999999")
    assert config.get_db_statement_timeout_ms() == 1000
    assert config.get_db_idle_in_transaction_session_timeout_ms() == 600000
    options = config.get_db_connect_options()
    assert "statement_timeout=1000" in options
    assert "idle_in_transaction_session_timeout=600000" in options


def test_auth_ttl_bounds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_ACCESS_TOKEN_TTL_MINUTES", "abc")
    assert config.get_auth_access_token_ttl_minutes() == 15
    monkeypatch.setenv("AUTH_ACCESS_TOKEN_TTL_MINUTES", "1")
    assert config.get_auth_access_token_ttl_minutes() == 5
    monkeypatch.setenv("AUTH_ACCESS_TOKEN_TTL_MINUTES", str(999999))
    assert config.get_auth_access_token_ttl_minutes() == 24 * 60

    monkeypatch.setenv("AUTH_REFRESH_TOKEN_TTL_MINUTES", "abc")
    assert config.get_auth_refresh_token_ttl_minutes() == 7 * 24 * 60
    monkeypatch.setenv("AUTH_REFRESH_TOKEN_TTL_MINUTES", "1")
    assert config.get_auth_refresh_token_ttl_minutes() == 30
    monkeypatch.setenv("AUTH_REFRESH_TOKEN_TTL_MINUTES", str(999999))
    assert config.get_auth_refresh_token_ttl_minutes() == 30 * 24 * 60


def test_cookie_samesite_fallbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_ACCESS_COOKIE_SAMESITE", "invalid")
    assert config.get_auth_cookie_same_site() == "lax"
    monkeypatch.setenv("AUTH_ACCESS_COOKIE_SAMESITE", "none")
    assert config.get_auth_cookie_same_site() == "none"

    monkeypatch.setenv("AUTH_CSRF_COOKIE_SAMESITE", "invalid")
    assert config.get_auth_csrf_cookie_same_site() == "none"


def test_cookie_names_and_auth_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_ACCESS_COOKIE_NAME", "")
    monkeypatch.setenv("AUTH_REFRESH_COOKIE_NAME", "")
    monkeypatch.setenv("AUTH_CSRF_COOKIE_NAME", "")
    assert config.get_auth_cookie_name() == "app_access_token"
    assert config.get_auth_refresh_cookie_name() == "app_refresh_token"
    assert config.get_auth_csrf_cookie_name() == "app_csrf_token"

    monkeypatch.setenv("AUTH_CSRF_PROTECTION_ENABLED", "false")
    assert config.is_csrf_protection_enabled() is False
    monkeypatch.setenv("AUTH_ALLOW_LEGACY_HEADERS", "true")
    assert config.allow_legacy_header_auth() is True


def test_allow_rbac_dev_fallback_production_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RBAC_ALLOW_DEV_FALLBACK", "true")
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(RuntimeError):
        config.allow_rbac_dev_fallback()


def test_redis_url_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/0")
    monkeypatch.delenv("AUTH_REVOCATION_REDIS_URL", raising=False)
    monkeypatch.delenv("RATE_LIMIT_REDIS_URL", raising=False)
    assert config.get_auth_revocation_redis_url() == "redis://redis:6379/0"
    assert config.get_rate_limit_redis_url() == "redis://redis:6379/0"

    monkeypatch.setenv("AUTH_REVOCATION_REDIS_URL", "redis://redis:6379/2")
    monkeypatch.setenv("RATE_LIMIT_REDIS_URL", "redis://redis:6379/3")
    assert config.get_auth_revocation_redis_url() == "redis://redis:6379/2"
    assert config.get_rate_limit_redis_url() == "redis://redis:6379/3"


def test_internal_api_token_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INTERNAL_API_TOKEN", "abc")
    monkeypatch.delenv("PLATFORM_INTERNAL_TOKEN", raising=False)
    assert config.get_internal_api_token() == "abc"

    monkeypatch.setenv("INTERNAL_API_TOKEN", "abc")
    monkeypatch.setenv("PLATFORM_INTERNAL_TOKEN", "abc")
    assert config.get_internal_api_token() == "abc"


def test_internal_api_token_mismatch_and_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INTERNAL_API_TOKEN", "abc")
    monkeypatch.setenv("PLATFORM_INTERNAL_TOKEN", "xyz")
    with pytest.raises(RuntimeError):
        config.get_internal_api_token()

    monkeypatch.delenv("INTERNAL_API_TOKEN", raising=False)
    monkeypatch.delenv("PLATFORM_INTERNAL_TOKEN", raising=False)
    with pytest.raises(RuntimeError):
        config.get_internal_api_token()


def test_internal_api_allowed_scopes_guards(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("INTERNAL_API_ALLOWED_SCOPES", raising=False)
    with pytest.raises(RuntimeError):
        config.get_internal_api_allowed_scopes()

    monkeypatch.setenv("INTERNAL_API_ALLOWED_SCOPES", "*")
    with pytest.raises(RuntimeError):
        config.get_internal_api_allowed_scopes()

    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("INTERNAL_API_ALLOWED_SCOPES", "jobs.run,analytics.kpis.refresh")
    assert config.get_internal_api_allowed_scopes() == {"jobs.run", "analytics.kpis.refresh"}


def test_internal_api_allowed_scopes_nonprod_defaults_and_wildcard(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("INTERNAL_API_ALLOWED_SCOPES", raising=False)
    scopes = config.get_internal_api_allowed_scopes()
    assert "worker.run_once" in scopes

    monkeypatch.setenv("INTERNAL_API_ALLOWED_SCOPES", "*")
    assert config.get_internal_api_allowed_scopes() == {"*"}


def test_trusted_hosts_wildcard_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("TRUSTED_HOSTS", "*,backend")
    with pytest.raises(RuntimeError):
        config.get_trusted_hosts()


def test_rate_limit_class_defaults_and_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RATE_LIMIT_AUTH_WINDOW_SECONDS", raising=False)
    assert config.get_rate_limit_class_window_seconds("auth") == 60
    monkeypatch.setenv("RATE_LIMIT_AUTH_WINDOW_SECONDS", "120")
    assert config.get_rate_limit_class_window_seconds("auth") == 120

    monkeypatch.setenv("RATE_LIMIT_ENDPOINT_OVERRIDES_JSON", "not-json")
    assert config.get_rate_limit_endpoint_overrides() == []

    monkeypatch.setenv(
        "RATE_LIMIT_ENDPOINT_OVERRIDES_JSON",
        '[{"path_pattern":"/api/v1/admin/jobs","class":"jobs","method":"post","limit":50}]',
    )
    entries = config.get_rate_limit_endpoint_overrides()
    assert len(entries) == 1
    assert entries[0]["class"] == "jobs"
    assert entries[0]["method"] == "POST"


def test_rate_limit_class_helpers_and_numeric_getters(monkeypatch: pytest.MonkeyPatch) -> None:
    assert config._rate_limit_class_window_env_name("read") == "RATE_LIMIT_READ_WINDOW_SECONDS"
    assert config._rate_limit_class_limit_env_name("write") == "RATE_LIMIT_WRITE_LIMIT"
    assert config._rate_limit_class_burst_limit_env_name("jobs") == "RATE_LIMIT_JOBS_BURST_LIMIT"
    assert config._rate_limit_class_burst_window_env_name("auth") == "RATE_LIMIT_AUTH_BURST_WINDOW_SECONDS"

    assert config._rate_limit_class_defaults("read") == (60, 12000, 5, 2500)
    assert config._rate_limit_class_defaults("write") == (60, 8000, 5, 1800)
    assert config._rate_limit_class_defaults("jobs") == (60, 4000, 5, 1200)
    assert config._rate_limit_class_defaults("auth") == (60, 300, 10, 120)
    assert config._rate_limit_class_defaults("internal") == (60, 30000, 5, 5000)

    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    assert config.is_rate_limit_enabled() is False
    monkeypatch.setenv("RATE_LIMIT_SERVICE_BYPASS", "true")
    assert config.is_rate_limit_service_bypass_enabled() is True

    monkeypatch.setenv("RATE_LIMIT_LOGIN_WINDOW_SECONDS", "0")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_IP_LIMIT", "-1")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_IDENTIFIER_LIMIT", "500000")
    assert config.get_rate_limit_login_window_seconds() == 1
    assert config.get_rate_limit_login_ip_limit() == 0
    assert config.get_rate_limit_login_identifier_limit() == 10000

    monkeypatch.setenv("AUTH_LOGIN_LOCKOUT_THRESHOLD", "0")
    monkeypatch.setenv("AUTH_LOGIN_LOCKOUT_BASE_SECONDS", "0")
    monkeypatch.setenv("AUTH_LOGIN_LOCKOUT_MAX_SECONDS", "999999")
    monkeypatch.setenv("AUTH_LOGIN_LOCKOUT_RESET_WINDOW_SECONDS", "999999")
    assert config.get_auth_lockout_threshold() == 1
    assert config.get_auth_lockout_base_seconds() == 1
    assert config.get_auth_lockout_max_seconds() == 86400
    assert config.get_auth_lockout_reset_window_seconds() == 86400

    monkeypatch.setenv("RATE_LIMIT_SENSITIVE_ADMIN_WINDOW_SECONDS", "0")
    monkeypatch.setenv("RATE_LIMIT_SENSITIVE_ADMIN_LIMIT", "-1")
    monkeypatch.setenv("RATE_LIMIT_GENERAL_WINDOW_SECONDS", "99999")
    monkeypatch.setenv("RATE_LIMIT_GENERAL_LIMIT", "-1")
    assert config.get_rate_limit_sensitive_admin_window_seconds() == 1
    assert config.get_rate_limit_sensitive_admin_limit() == 0
    assert config.get_rate_limit_general_window_seconds() == 3600
    assert config.get_rate_limit_general_limit() == 0

    monkeypatch.setenv("ACADEMIC_RISK_GRADE_THRESHOLD", "0")
    monkeypatch.setenv("ACADEMIC_SEVERE_RISK_GRADE_THRESHOLD", "999")
    assert config.get_academic_risk_grade_threshold() == 1
    assert config.get_academic_severe_risk_grade_threshold() == 100


def test_metrics_and_ops_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("METRICS_ALLOWED_IPS", "10.0.0.1, 10.0.0.2")
    assert config.get_metrics_allowed_ips() == {"10.0.0.1", "10.0.0.2"}

    monkeypatch.setenv("METRICS_TOKEN", "token")
    assert config.get_metrics_token() == "token"
    monkeypatch.setenv("METRICS_TOKEN", "")
    assert config.get_metrics_token() is None

    monkeypatch.setenv("APP_ENV", "production")
    assert config.is_production_mode() is True
    monkeypatch.delenv("PLATFORM_SELF_SERVICE_ENABLED", raising=False)
    assert config.is_platform_self_service_enabled() is False
    monkeypatch.setenv("PLATFORM_SELF_SERVICE_ENABLED", "true")
    assert config.is_platform_self_service_enabled() is True

    monkeypatch.setenv("OPS_ALERT_COOLDOWN_SECONDS", "10")
    monkeypatch.setenv("OPS_LOGIN_FAILURE_SPIKE_THRESHOLD", "0")
    monkeypatch.setenv("OPS_JOBS_FAILURE_SPIKE_THRESHOLD", "999999")
    monkeypatch.setenv("OPS_LATENCY_P95_THRESHOLD_MS", "10")
    monkeypatch.setenv("OPS_LATENCY_P99_THRESHOLD_MS", "999999")
    monkeypatch.setenv("OPS_WORKER_STALE_SECONDS", "1")
    monkeypatch.setenv("OPS_SCHEDULER_STALE_SECONDS", "999999")
    monkeypatch.setenv("OPS_PROBE_TIMEOUT_SECONDS", "999")

    assert config.get_ops_alert_cooldown_seconds() == 30
    assert config.get_ops_login_failure_spike_threshold() == 1
    assert config.get_ops_jobs_failure_spike_threshold() == 10000
    assert config.get_ops_latency_p95_threshold_ms() == 50
    assert config.get_ops_latency_p99_threshold_ms() == 120000
    assert config.get_ops_worker_stale_seconds() == 10
    assert config.get_ops_scheduler_stale_seconds() == 7200
    assert config.get_ops_probe_timeout_seconds() == 15


def test_billing_module_router_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("BILLING_MODULE_ROUTER_ENABLED", raising=False)
    assert config.is_billing_module_router_enabled() is True

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("BILLING_MODULE_ROUTER_ENABLED", raising=False)
    assert config.is_billing_module_router_enabled() is False

    monkeypatch.setenv("BILLING_MODULE_ROUTER_ENABLED", "true")
    assert config.is_billing_module_router_enabled() is True


def test_worker_health_default_by_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("OPS_REQUIRE_WORKER_HEALTH", raising=False)
    assert config.is_worker_health_required() is True

    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("OPS_REQUIRE_WORKER_HEALTH", raising=False)
    assert config.is_worker_health_required() is False


def test_runtime_config_and_low_level_validators(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db:5432/app")
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/0")
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    monkeypatch.setenv("INTERNAL_API_TOKEN", "abc")
    monkeypatch.setenv("INTEGRATIONS_ENCRYPTION_KEY", "k" * 32)
    cfg = config.get_required_runtime_config()
    assert cfg["DATABASE_URL"].startswith("postgresql://")

    assert config._is_https_url("https://example.com") is True
    assert config._is_https_url("http://example.com") is False
    assert config._is_postgres_dsn("postgresql://x") is True
    assert config._is_postgres_dsn("postgresql+psycopg://x") is True
    assert config._is_postgres_dsn("sqlite:///x") is False
    assert config._is_redis_dsn("redis://x") is True
    assert config._is_redis_dsn("rediss://x") is True
    assert config._is_redis_dsn("amqp://x") is False
    assert config._contains_forbidden_runtime_host("postgresql://localhost:5432/app") is True
    assert config._contains_forbidden_runtime_host("postgresql://db:5432/app") is False
    assert config._is_placeholder_secret("change_me") is True
    assert config._is_placeholder_secret("real_secret") is False


def test_validate_required_environment_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db:5432/app")
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/0")
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    monkeypatch.setenv("INTERNAL_API_TOKEN", "secure_internal_token")
    monkeypatch.setenv("INTEGRATIONS_ENCRYPTION_KEY", "k" * 32)
    config.validate_required_environment()


def test_validate_required_environment_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/0")
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    monkeypatch.setenv("INTERNAL_API_TOKEN", "secure_internal_token")
    monkeypatch.setenv("INTEGRATIONS_ENCRYPTION_KEY", "k" * 32)
    with pytest.raises(RuntimeError):
        config.validate_required_environment()

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db:5432/app")
    monkeypatch.setenv("JWT_SECRET", "short")
    with pytest.raises(RuntimeError):
        config.validate_required_environment()

    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///tmp.db")
    with pytest.raises(RuntimeError):
        config.validate_required_environment()

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/app")
    with pytest.raises(RuntimeError):
        config.validate_required_environment()

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db:5432/app")
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    with pytest.raises(RuntimeError):
        config.validate_required_environment()

    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/0")
    monkeypatch.setenv("INTERNAL_API_TOKEN", "change_me")
    with pytest.raises(RuntimeError):
        config.validate_required_environment()

    monkeypatch.setenv("INTERNAL_API_TOKEN", "secure_internal_token")
    monkeypatch.setenv("INTEGRATIONS_ENCRYPTION_KEY", "short")
    with pytest.raises(RuntimeError):
        config.validate_required_environment()
