import os


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


def is_dev_demo_compatibility_mode() -> bool:
    # Explicit switch for temporary compatibility behavior in dev/demo only.
    return is_enabled(os.getenv("AUTH_DEV_DEMO_COMPATIBILITY", "false"))


def allow_legacy_header_auth() -> bool:
    # Legacy identity headers are disabled by default and can only be enabled
    # when explicit dev/demo compatibility mode is turned on.
    return is_dev_demo_compatibility_mode() and is_enabled(
        os.getenv("AUTH_ALLOW_LEGACY_HEADERS", "false")
    )


def allow_rbac_dev_fallback() -> bool:
    # Security default: in operational mode authorization must not trust client roles
    # when DB-backed RBAC is unavailable.
    return is_dev_demo_compatibility_mode() and is_enabled(
        os.getenv("RBAC_ALLOW_DEV_FALLBACK", "false")
    )


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


def get_metrics_allowed_ips() -> set[str]:
    raw = os.getenv("METRICS_ALLOWED_IPS", "").strip()
    if not raw:
        return set()
    return {item.strip() for item in raw.split(",") if item.strip()}


def is_production_mode() -> bool:
    raw = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()
    return raw in {"prod", "production"}


def get_metrics_token() -> str | None:
    """Optional static bearer token required to read /metrics.

    Set METRICS_TOKEN to a strong random value in production.
    When unset the endpoint is accessible only from trusted network segments
    (e.g. blocked at nginx for external traffic).
    """
    raw = os.getenv("METRICS_TOKEN", "").strip()
    return raw or None
