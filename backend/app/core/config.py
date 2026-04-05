import os
import json
from contextlib import contextmanager
from contextvars import ContextVar, Token
from urllib.parse import urlparse
import hmac


_runtime_schema_bootstrap_scope: ContextVar[bool] = ContextVar(
    "runtime_schema_bootstrap_scope",
    default=False,
)


def is_enabled(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def get_auth_modes() -> dict[str, bool]:
    return {
        "local": True,
        "ldap": is_enabled(os.getenv("AUTH_LDAP_ENABLED", "false")),
        "api_keys": True,
    }


def get_ai_provider_status() -> dict[str, bool]:
    return {
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "gemini": bool(os.getenv("GEMINI_API_KEY")),
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "custom": bool(os.getenv("AI_CUSTOM_PROVIDER_URL")),
    }


def is_runtime_schema_bootstrap_enabled() -> bool:
    # Runtime DDL is allowed only inside the explicit startup/bootstrap scope.
    # Default stays enabled for startup compatibility until all bootstrap DDL is
    # fully migrated to Alembic, but regular request paths never enter the scope.
    return is_enabled(os.getenv("RUNTIME_SCHEMA_BOOTSTRAP_ENABLED", "true")) and _runtime_schema_bootstrap_scope.get()


@contextmanager
def runtime_schema_bootstrap_scope():
    token: Token[bool] = _runtime_schema_bootstrap_scope.set(True)
    try:
        yield
    finally:
        _runtime_schema_bootstrap_scope.reset(token)


def get_db_statement_timeout_ms() -> int:
    return _int_env("DB_STATEMENT_TIMEOUT_MS", 30000, minimum=1000, maximum=300000)


def get_db_idle_in_transaction_session_timeout_ms() -> int:
    return _int_env("DB_IDLE_IN_TRANSACTION_SESSION_TIMEOUT_MS", 60000, minimum=1000, maximum=600000)


def get_db_connect_options() -> str:
    return (
        f"-c statement_timeout={get_db_statement_timeout_ms()} "
        f"-c idle_in_transaction_session_timeout={get_db_idle_in_transaction_session_timeout_ms()}"
    )


def get_auth_access_token_ttl_minutes() -> int:
    raw = os.getenv("AUTH_ACCESS_TOKEN_TTL_MINUTES", "15").strip()
    try:
        value = int(raw)
    except ValueError:
        return 15
    return max(5, min(value, 24 * 60))


def get_auth_refresh_token_ttl_minutes() -> int:
    raw = os.getenv("AUTH_REFRESH_TOKEN_TTL_MINUTES", str(7 * 24 * 60)).strip()
    try:
        value = int(raw)
    except ValueError:
        return 7 * 24 * 60
    return max(30, min(value, 30 * 24 * 60))


def get_auth_cookie_name() -> str:
    raw = os.getenv("AUTH_ACCESS_COOKIE_NAME", "app_access_token").strip()
    return raw or "app_access_token"


def get_auth_refresh_cookie_name() -> str:
    raw = os.getenv("AUTH_REFRESH_COOKIE_NAME", "app_refresh_token").strip()
    return raw or "app_refresh_token"


def get_auth_cookie_same_site() -> str:
    raw = os.getenv("AUTH_ACCESS_COOKIE_SAMESITE", "lax").strip().lower()
    if raw in {"strict", "lax", "none"}:
        return raw
    return "lax"


def is_csrf_protection_enabled() -> bool:
    # Secure by default for cookie-authenticated browser flows.
    return is_enabled(os.getenv("AUTH_CSRF_PROTECTION_ENABLED", "true"))


def get_auth_csrf_cookie_name() -> str:
    raw = os.getenv("AUTH_CSRF_COOKIE_NAME", "app_csrf_token").strip()
    return raw or "app_csrf_token"


def get_auth_csrf_cookie_same_site() -> str:
    raw = os.getenv("AUTH_CSRF_COOKIE_SAMESITE", get_auth_cookie_same_site()).strip().lower()
    if raw in {"strict", "lax", "none"}:
        return raw
    return get_auth_cookie_same_site()


def allow_legacy_header_auth() -> bool:
    # Legacy identity headers are disabled by default and require explicit opt-in.
    return is_enabled(os.getenv("AUTH_ALLOW_LEGACY_HEADERS", "false"))


def allow_rbac_dev_fallback() -> bool:
    # Security default: in operational mode authorization must not trust client roles
    # when DB-backed RBAC is unavailable.
    enabled = is_enabled(os.getenv("RBAC_ALLOW_DEV_FALLBACK", "false"))
    if enabled and is_production_mode():
        raise RuntimeError(
            "RBAC_ALLOW_DEV_FALLBACK must not be enabled in production: "
            "set RBAC_ALLOW_DEV_FALLBACK=false or remove the variable"
        )
    return enabled


def get_auth_revocation_redis_url() -> str | None:
    raw = os.getenv("AUTH_REVOCATION_REDIS_URL", os.getenv("REDIS_URL", "")).strip()
    return raw or None


def _int_env(name: str, default: int, *, minimum: int = 0, maximum: int | None = None) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        value = default
    if maximum is not None:
        value = min(value, maximum)
    return max(minimum, value)


def is_rate_limit_enabled() -> bool:
    return is_enabled(os.getenv("RATE_LIMIT_ENABLED", "true"))


def get_rate_limit_login_window_seconds() -> int:
    return _int_env("RATE_LIMIT_LOGIN_WINDOW_SECONDS", 60, minimum=1, maximum=3600)


def get_rate_limit_login_ip_limit() -> int:
    return _int_env("RATE_LIMIT_LOGIN_IP_LIMIT", 10, minimum=0, maximum=10000)


def get_rate_limit_login_identifier_limit() -> int:
    return _int_env("RATE_LIMIT_LOGIN_IDENTIFIER_LIMIT", 5, minimum=0, maximum=10000)


def get_auth_lockout_threshold() -> int:
    return _int_env("AUTH_LOGIN_LOCKOUT_THRESHOLD", 5, minimum=1, maximum=1000)


def get_auth_lockout_base_seconds() -> int:
    return _int_env("AUTH_LOGIN_LOCKOUT_BASE_SECONDS", 2, minimum=1, maximum=3600)


def get_auth_lockout_max_seconds() -> int:
    return _int_env("AUTH_LOGIN_LOCKOUT_MAX_SECONDS", 900, minimum=1, maximum=86400)


def get_auth_lockout_reset_window_seconds() -> int:
    return _int_env("AUTH_LOGIN_LOCKOUT_RESET_WINDOW_SECONDS", 1800, minimum=1, maximum=86400)


def get_rate_limit_sensitive_admin_window_seconds() -> int:
    return _int_env("RATE_LIMIT_SENSITIVE_ADMIN_WINDOW_SECONDS", 60, minimum=1, maximum=3600)


def get_rate_limit_sensitive_admin_limit() -> int:
    return _int_env("RATE_LIMIT_SENSITIVE_ADMIN_LIMIT", 10, minimum=0, maximum=10000)


def get_rate_limit_general_window_seconds() -> int:
    return _int_env("RATE_LIMIT_GENERAL_WINDOW_SECONDS", 60, minimum=1, maximum=3600)


def get_rate_limit_general_limit() -> int:
    return _int_env("RATE_LIMIT_GENERAL_LIMIT", 120, minimum=0, maximum=100000)


def get_rate_limit_redis_url() -> str | None:
    raw = os.getenv("RATE_LIMIT_REDIS_URL", os.getenv("REDIS_URL", "")).strip()
    return raw or None


def is_rate_limit_service_bypass_enabled() -> bool:
    return is_enabled(os.getenv("RATE_LIMIT_SERVICE_BYPASS", "false"))


def _rate_limit_class_window_env_name(traffic_class: str) -> str:
    return f"RATE_LIMIT_{str(traffic_class).strip().upper()}_WINDOW_SECONDS"


def _rate_limit_class_limit_env_name(traffic_class: str) -> str:
    return f"RATE_LIMIT_{str(traffic_class).strip().upper()}_LIMIT"


def _rate_limit_class_burst_limit_env_name(traffic_class: str) -> str:
    return f"RATE_LIMIT_{str(traffic_class).strip().upper()}_BURST_LIMIT"


def _rate_limit_class_burst_window_env_name(traffic_class: str) -> str:
    return f"RATE_LIMIT_{str(traffic_class).strip().upper()}_BURST_WINDOW_SECONDS"


def _rate_limit_class_defaults(traffic_class: str) -> tuple[int, int, int, int]:
    normalized = str(traffic_class).strip().lower()
    if normalized == "read":
        return (60, 12000, 5, 2500)
    if normalized == "write":
        return (60, 8000, 5, 1800)
    if normalized == "jobs":
        return (60, 4000, 5, 1200)
    if normalized == "auth":
        return (60, 300, 10, 120)
    if normalized == "internal":
        return (60, 30000, 5, 5000)
    # Backward compatibility fallback for unknown class.
    return (get_rate_limit_general_window_seconds(), get_rate_limit_general_limit(), 5, 1000)


def get_rate_limit_class_window_seconds(traffic_class: str) -> int:
    default_window, _, _, _ = _rate_limit_class_defaults(traffic_class)
    return _int_env(
        _rate_limit_class_window_env_name(traffic_class),
        default_window,
        minimum=1,
        maximum=3600,
    )


def get_rate_limit_class_limit(traffic_class: str) -> int:
    _, default_limit, _, _ = _rate_limit_class_defaults(traffic_class)
    return _int_env(
        _rate_limit_class_limit_env_name(traffic_class),
        default_limit,
        minimum=0,
        maximum=500000,
    )


def get_rate_limit_class_burst_window_seconds(traffic_class: str) -> int:
    _, _, default_window, _ = _rate_limit_class_defaults(traffic_class)
    return _int_env(
        _rate_limit_class_burst_window_env_name(traffic_class),
        default_window,
        minimum=1,
        maximum=120,
    )


def get_rate_limit_class_burst_limit(traffic_class: str) -> int:
    _, _, _, default_limit = _rate_limit_class_defaults(traffic_class)
    return _int_env(
        _rate_limit_class_burst_limit_env_name(traffic_class),
        default_limit,
        minimum=0,
        maximum=500000,
    )


def get_rate_limit_endpoint_overrides() -> list[dict[str, object]]:
    raw = os.getenv("RATE_LIMIT_ENDPOINT_OVERRIDES_JSON", "").strip()
    if not raw:
        return []
    try:
        payload = json.loads(raw)
    except Exception:
        return []
    if not isinstance(payload, list):
        return []

    normalized: list[dict[str, object]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        path_pattern = str(item.get("path_pattern", "")).strip()
        if not path_pattern:
            continue
        traffic_class = str(item.get("class", "")).strip().lower()
        if traffic_class not in {"read", "write", "jobs", "auth", "internal"}:
            continue
        method = str(item.get("method", "*")).strip().upper() or "*"
        normalized_item: dict[str, object] = {
            "path_pattern": path_pattern,
            "class": traffic_class,
            "method": method,
        }
        if isinstance(item.get("limit"), int):
            normalized_item["limit"] = int(item["limit"])
        if isinstance(item.get("window_seconds"), int):
            normalized_item["window_seconds"] = int(item["window_seconds"])
        if isinstance(item.get("burst_limit"), int):
            normalized_item["burst_limit"] = int(item["burst_limit"])
        if isinstance(item.get("burst_window_seconds"), int):
            normalized_item["burst_window_seconds"] = int(item["burst_window_seconds"])
        normalized.append(normalized_item)
    return normalized


def get_metrics_allowed_ips() -> set[str]:
    raw = os.getenv("METRICS_ALLOWED_IPS", "").strip()
    if not raw:
        return set()
    return {item.strip() for item in raw.split(",") if item.strip()}


def is_production_mode() -> bool:
    raw = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()
    return raw in {"prod", "production"}


def is_platform_self_service_enabled() -> bool:
    raw = os.getenv("PLATFORM_SELF_SERVICE_ENABLED", "").strip().lower()
    if raw:
        return is_enabled(raw)
    return not is_production_mode()


def get_metrics_token() -> str | None:
    """Optional static bearer token required to read /metrics.

    Set METRICS_TOKEN to a strong random value in production.
    When unset the endpoint is accessible only from trusted network segments
    (e.g. blocked at nginx for external traffic).
    """
    raw = os.getenv("METRICS_TOKEN", "").strip()
    return raw or None


def get_trusted_hosts() -> list[str]:
    """Return allowed host patterns for TrustedHostMiddleware.

    Default to the local edge/runtime hosts used by the Docker stack.
    Operators can still override this with TRUSTED_HOSTS explicitly.
    """
    default_hosts = ["localhost", "127.0.0.1", "backend", "nginx"]
    raw = os.getenv("TRUSTED_HOSTS", "").strip()
    if not raw:
        return default_hosts
    hosts = [item.strip() for item in raw.split(",") if item.strip()]
    if is_production_mode() and "*" in hosts:
        raise RuntimeError("TRUSTED_HOSTS must not include wildcard host in production")
    return hosts or default_hosts


def get_ops_alert_webhook_url() -> str | None:
    raw = os.getenv("OPS_ALERT_WEBHOOK_URL", "").strip()
    return raw or None


def get_ops_alert_cooldown_seconds() -> int:
    return _int_env("OPS_ALERT_COOLDOWN_SECONDS", 300, minimum=30, maximum=3600)


def get_ops_login_failure_spike_threshold() -> int:
    return _int_env("OPS_LOGIN_FAILURE_SPIKE_THRESHOLD", 5, minimum=1, maximum=10000)


def get_ops_jobs_failure_spike_threshold() -> int:
    return _int_env("OPS_JOBS_FAILURE_SPIKE_THRESHOLD", 5, minimum=1, maximum=10000)


def get_ops_latency_p95_threshold_ms() -> int:
    return _int_env("OPS_LATENCY_P95_THRESHOLD_MS", 1000, minimum=50, maximum=60000)


def get_ops_latency_p99_threshold_ms() -> int:
    return _int_env("OPS_LATENCY_P99_THRESHOLD_MS", 2500, minimum=50, maximum=120000)


def get_ops_worker_stale_seconds() -> int:
    return _int_env("OPS_WORKER_STALE_SECONDS", 180, minimum=10, maximum=3600)


def is_worker_health_required() -> bool:
    default = "true" if is_production_mode() else "false"
    return is_enabled(os.getenv("OPS_REQUIRE_WORKER_HEALTH", default))


def get_ops_scheduler_stale_seconds() -> int:
    return _int_env("OPS_SCHEDULER_STALE_SECONDS", 300, minimum=10, maximum=7200)


def get_ops_probe_timeout_seconds() -> int:
    return _int_env("OPS_PROBE_TIMEOUT_SECONDS", 2, minimum=1, maximum=15)


def get_required_runtime_config() -> dict[str, str]:
    return {
        "DATABASE_URL": os.getenv("DATABASE_URL", "").strip(),
        "REDIS_URL": os.getenv("REDIS_URL", "").strip(),
        "JWT_SECRET": os.getenv("JWT_SECRET", "").strip(),
        "INTERNAL_API_TOKEN": os.getenv("INTERNAL_API_TOKEN", "").strip(),
        "INTEGRATIONS_ENCRYPTION_KEY": os.getenv("INTEGRATIONS_ENCRYPTION_KEY", "").strip(),
    }


def get_internal_api_token() -> str:
    canonical = os.getenv("INTERNAL_API_TOKEN", "").strip()
    legacy = os.getenv("PLATFORM_INTERNAL_TOKEN", "").strip()

    if canonical and legacy and not hmac.compare_digest(canonical, legacy):
        raise RuntimeError("INTERNAL_API_TOKEN and PLATFORM_INTERNAL_TOKEN must match when both are set")

    token = canonical or legacy
    if not token:
        raise RuntimeError("INTERNAL_API_TOKEN must be configured")
    return token


_LEGACY_INTERNAL_API_FULL_SCOPES = {
    "jobs.run",
    "jobs.retry",
    "worker.run_once",
    "module_jobs.run_once",
    "events.outbox.run_once",
    "runtime.rehydrate",
    "scheduler.run_once",
    "notifications.read",
    "webhooks.retry_failed",
    "webhooks.failed_deliveries.read",
    "analytics.kpis.refresh",
    "platform.kpi.refresh_all",
    "platform.kpi.refresh_tenant",
    "platform.automation.evaluate",
    "context.student.read",
    "platform.ai_copilot.rebuild_cache",
}


def get_internal_api_allowed_scopes() -> set[str]:
    raw = os.getenv("INTERNAL_API_ALLOWED_SCOPES", "").strip()
    if not raw:
        if is_production_mode():
            raise RuntimeError("INTERNAL_API_ALLOWED_SCOPES must be explicitly configured in production")
        # Backward-compatible default; operators can explicitly tighten via env.
        return set(_LEGACY_INTERNAL_API_FULL_SCOPES)

    scopes = {item.strip() for item in raw.split(",") if item.strip()}
    if "*" in scopes:
        if is_production_mode():
            raise RuntimeError("INTERNAL_API_ALLOWED_SCOPES must not include wildcard in production")
        return {"*"}
    return scopes


def _is_https_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def _is_postgres_dsn(value: str) -> bool:
    return value.startswith("postgresql://") or value.startswith("postgresql+psycopg://")


def _is_redis_dsn(value: str) -> bool:
    return value.startswith("redis://") or value.startswith("rediss://")


def _contains_forbidden_runtime_host(value: str) -> bool:
    lowered = value.strip().lower()
    loopback_host = "local" + "host"
    loopback_ip = "127.0.0" + ".1"
    docker_host = "host.docker" + ".internal"
    return any(token in lowered for token in (loopback_host, loopback_ip, docker_host))


def _is_placeholder_secret(value: str) -> bool:
    lowered = value.strip().lower()
    return lowered in {"change_me", "changeme", "replace_me", "example", "test", "secret"}


def validate_required_environment() -> None:
    config = get_required_runtime_config()
    missing = [name for name, value in config.items() if not value]
    if missing:
        raise RuntimeError(f"missing required environment variables: {', '.join(sorted(missing))}")
    if len(config["JWT_SECRET"]) < 32:
        raise RuntimeError("JWT_SECRET must be at least 32 characters long")
    if not _is_postgres_dsn(config["DATABASE_URL"]):
        raise RuntimeError("DATABASE_URL must be a PostgreSQL DSN")
    if _contains_forbidden_runtime_host(config["DATABASE_URL"]):
        raise RuntimeError("DATABASE_URL must not reference loopback or host-container bridge endpoints")
    if not _is_redis_dsn(config["REDIS_URL"]):
        raise RuntimeError("REDIS_URL must be a Redis DSN")
    if _contains_forbidden_runtime_host(config["REDIS_URL"]):
        raise RuntimeError("REDIS_URL must not reference loopback or host-container bridge endpoints")
    if _is_placeholder_secret(config["INTERNAL_API_TOKEN"]):
        raise RuntimeError("INTERNAL_API_TOKEN must not use a placeholder value")
    if len(config["INTEGRATIONS_ENCRYPTION_KEY"]) < 32:
        raise RuntimeError("INTEGRATIONS_ENCRYPTION_KEY must be at least 32 characters long")
    get_internal_api_token()
