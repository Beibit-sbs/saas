from app.core.db import get_raw_conn
from app.core.config import is_runtime_schema_bootstrap_enabled
import os
import time
from base64 import urlsafe_b64encode
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from threading import Lock

from cryptography.fernet import Fernet, InvalidToken

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


@dataclass
class SettingEntry:
    key: str
    value: str
    is_secret: bool


_settings: dict[str, SettingEntry] = {}
_SECRET_PREFIX = "enc:v1:"
_settings_schema_lock = Lock()
_settings_schema_ready = False
# Short-lived read-through cache to avoid one DB connection per setting read on hot paths.
# TTL is conservative (10 s) so runtime updates propagate quickly.
_READ_CACHE_TTL_S: float = 10.0
_read_cache: dict[str, tuple[float, SettingEntry | None]] = {}
_read_cache_lock = Lock()


def _normalize_tenant_id(tenant_id: int | None) -> int | None:
    if tenant_id is None:
        return None
    normalized = int(tenant_id)
    if normalized <= 0:
        raise ValueError("tenant_id must be positive")
    return normalized


def _require_tenant_id(tenant_id: int | None, *, operation: str) -> int:
    normalized = _normalize_tenant_id(tenant_id)
    if normalized is None:
        raise ValueError(f"tenant_id is required for {operation}")
    return normalized


def _scoped_setting_key(key: str, tenant_id: int | None) -> str:
    normalized_tenant = _normalize_tenant_id(tenant_id)
    normalized_key = key.strip()
    if normalized_tenant is None:
        # Global settings are allowed, but callers must opt into them explicitly.
        return normalized_key
    return f"tenant:{normalized_tenant}:{normalized_key}"


def save_global_setting(key: str, value: str, is_secret: bool = False) -> None:
    save_setting(key, value, is_secret=is_secret, tenant_id=None)


def get_global_setting(key: str) -> SettingEntry | None:
    return get_setting(key, tenant_id=None)


def get_global_runtime_value(key: str, env_name: str, default: str = "") -> str:
    return get_runtime_value(key, env_name, default, tenant_id=None)


def _db_url() -> str | None:
    return os.getenv("DATABASE_URL")


def _raw_encryption_secret() -> str:
    explicit = os.getenv("INTEGRATIONS_ENCRYPTION_KEY", "").strip()
    if explicit:
        return explicit
    # Reuse JWT secret in local/dev if dedicated encryption secret is not set.
    return os.getenv("JWT_SECRET", "change_me_jwt_secret")


def _derive_fernet_key(secret: str) -> bytes:
    digest = sha256(secret.encode("utf-8")).digest()
    return urlsafe_b64encode(digest)


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    return Fernet(_derive_fernet_key(_raw_encryption_secret()))


def _encrypt_secret(value: str) -> str:
    if not value:
        return value
    token = _fernet().encrypt(value.encode("utf-8")).decode("utf-8")
    return f"{_SECRET_PREFIX}{token}"


def _decrypt_secret(value: str) -> str:
    if not value:
        return value
    if not value.startswith(_SECRET_PREFIX):
        # Backward compatibility for values saved before encryption-at-rest.
        return value

    token = value[len(_SECRET_PREFIX) :]
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return ""


def _use_database() -> bool:
    return bool(_db_url()) and psycopg is not None


def _should_fallback_to_memory(exc: Exception) -> bool:
    """Fallback only on DB availability/connectivity issues, not logic bugs."""
    if isinstance(exc, RuntimeError) and str(exc) == "database unavailable":
        return True
    if isinstance(exc, (ConnectionError, TimeoutError, OSError)):
        return True
    if psycopg is not None and isinstance(exc, (psycopg.OperationalError, psycopg.InterfaceError)):
        return True
    return False


def _ensure_table(conn) -> None:
    if not is_runtime_schema_bootstrap_enabled():
        return
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_integration_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                is_secret BOOLEAN NOT NULL DEFAULT FALSE,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    conn.commit()


def _ensure_table_once(conn) -> None:
    global _settings_schema_ready
    if _settings_schema_ready:
        return
    with _settings_schema_lock:
        if _settings_schema_ready:
            return
        _ensure_table(conn)
        _settings_schema_ready = True


def _save_db(key: str, value: str, is_secret: bool) -> None:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with get_raw_conn() as conn:
        _ensure_table_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_integration_settings(key, value, is_secret)
                VALUES (%s, %s, %s)
                ON CONFLICT (key)
                DO UPDATE SET value = EXCLUDED.value, is_secret = EXCLUDED.is_secret, updated_at = NOW()
                """,
                (key, value, is_secret),
            )
        conn.commit()


def _get_db(key: str) -> SettingEntry | None:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with get_raw_conn() as conn:
        _ensure_table_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT key, value, is_secret FROM app_integration_settings WHERE key = %s",
                (key,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return SettingEntry(key=row[0], value=row[1], is_secret=row[2])


def _get_db_batch(keys: list[str]) -> dict[str, SettingEntry]:
    """Fetch multiple settings in a single DB round-trip and populate read cache."""
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")
    if not keys:
        return {}

    with get_raw_conn() as conn:
        _ensure_table_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT key, value, is_secret FROM app_integration_settings WHERE key = ANY(%s)",
                (keys,),
            )
            rows = cur.fetchall()

    result: dict[str, SettingEntry] = {}
    now = time.monotonic()
    for row in rows:
        entry = SettingEntry(key=row[0], value=row[1], is_secret=row[2])
        result[row[0]] = entry
        with _read_cache_lock:
            _read_cache[row[0]] = (now, entry)

    # Cache misses (key not in DB) — cache None so we don't re-query
    for key in keys:
        if key not in result:
            with _read_cache_lock:
                _read_cache[key] = (now, None)
    return result


def prefetch_settings(keys: list[str], tenant_id: int | None = None) -> None:
    """Warm the read cache for a list of setting keys in one DB round-trip.
    Safe to call before any per-key get_setting(); does nothing if DB unavailable.
    """
    if not _use_database():
        return
    scoped_keys = [_scoped_setting_key(k, tenant_id) for k in keys if k.strip()]
    now = time.monotonic()
    fresh = []
    for sk in scoped_keys:
        with _read_cache_lock:
            cached = _read_cache.get(sk)
        if cached is not None and now - cached[0] < _READ_CACHE_TTL_S:
            continue
        fresh.append(sk)
    if not fresh:
        return
    try:
        _get_db_batch(fresh)
    except Exception:
        pass


def save_setting(key: str, value: str, is_secret: bool = False, tenant_id: int | None = None) -> None:
    normalized_key = key.strip()
    if not normalized_key:
        raise ValueError("setting key is required")

    scoped_key = _scoped_setting_key(normalized_key, tenant_id)

    value_to_store = _encrypt_secret(value) if is_secret else value

    if _use_database():
        try:
            _save_db(scoped_key, value_to_store, is_secret)
            _invalidate_setting_cache(scoped_key)
            return
        except Exception as exc:
            # Keep admin/runtime settings usable when DATABASE_URL points to an
            # unreachable host (for example, local tests outside docker network).
            if not _should_fallback_to_memory(exc):
                raise

    _settings[scoped_key] = SettingEntry(
        key=scoped_key,
        value=value_to_store,
        is_secret=is_secret,
    )
    _invalidate_setting_cache(scoped_key)


def _get_setting_cached(scoped_key: str) -> SettingEntry | None:
    """Return cached entry if fresh, else fetch from DB and cache result."""
    now = time.monotonic()
    with _read_cache_lock:
        cached = _read_cache.get(scoped_key)
    if cached is not None:
        cached_at, entry = cached
        if now - cached_at < _READ_CACHE_TTL_S:
            return entry

    try:
        entry = _get_db(scoped_key)
    except Exception as exc:
        if not _should_fallback_to_memory(exc):
            raise
        entry = _settings.get(scoped_key)

    with _read_cache_lock:
        _read_cache[scoped_key] = (now, entry)
    return entry


def _invalidate_setting_cache(scoped_key: str) -> None:
    with _read_cache_lock:
        _read_cache.pop(scoped_key, None)


def get_setting(key: str, tenant_id: int | None = None) -> SettingEntry | None:
    normalized_key = key.strip()
    if not normalized_key:
        return None

    scoped_key = _scoped_setting_key(normalized_key, tenant_id)

    if _use_database():
        entry = _get_setting_cached(scoped_key)
    else:
        entry = _settings.get(scoped_key)

    if entry is None:
        return None

    if entry.is_secret and entry.value and not entry.value.startswith(_SECRET_PREFIX):
        encrypted = _encrypt_secret(entry.value)
        if _use_database():
            try:
                _save_db(entry.key, encrypted, True)
            except Exception as exc:
                if not _should_fallback_to_memory(exc):
                    raise
                _settings[entry.key] = SettingEntry(key=entry.key, value=encrypted, is_secret=True)
        else:
            _settings[entry.key] = SettingEntry(key=entry.key, value=encrypted, is_secret=True)
        return SettingEntry(key=entry.key, value=entry.value, is_secret=True)

    value = _decrypt_secret(entry.value) if entry.is_secret else entry.value
    return SettingEntry(key=entry.key, value=value, is_secret=entry.is_secret)


def get_runtime_value(key: str, env_name: str, default: str = "", tenant_id: int | None = None) -> str:
    entry = get_setting(key, tenant_id=tenant_id)
    if entry is not None and entry.value is not None:
        return entry.value
    return os.getenv(env_name, default)


def _to_bool(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def get_ldap_config_for_admin(tenant_id: int | None = None) -> dict[str, object]:
    normalized_tenant_id = _require_tenant_id(tenant_id, operation="get_ldap_config_for_admin")
    config = get_ldap_runtime_config(tenant_id=normalized_tenant_id)
    return {
        "enabled": _to_bool(config["enabled"]),
        "server_uri": config["server_uri"],
        "bind_dn": config["bind_dn"],
        "has_bind_password": bool(config["bind_password"]),
        "base_dn": config["base_dn"],
        "user_filter": config["user_filter"],
        "display_name_attribute": config["display_name_attribute"],
        "login_attribute": config["login_attribute"],
        "group_attribute": config["group_attribute"],
        "group_role_map_json": config["group_role_map_json"],
        "default_role": config["default_role"],
        "timeout_seconds": config["timeout_seconds"],
    }


def get_ldap_runtime_config(tenant_id: int | None = None) -> dict[str, str]:
    normalized_tenant_id = _require_tenant_id(tenant_id, operation="get_ldap_runtime_config")
    prefetch_settings(
        [
            "ldap.enabled", "ldap.server_uri", "ldap.bind_dn", "ldap.bind_password",
            "ldap.base_dn", "ldap.user_filter", "ldap.display_name_attribute",
            "ldap.login_attribute", "ldap.group_attribute", "ldap.group_role_map_json",
            "ldap.default_role", "ldap.timeout_seconds",
        ],
        tenant_id=normalized_tenant_id,
    )
    return {
        "enabled": get_runtime_value("ldap.enabled", "AUTH_LDAP_ENABLED", "false", tenant_id=normalized_tenant_id),
        "server_uri": get_runtime_value("ldap.server_uri", "LDAP_SERVER_URI", "", tenant_id=normalized_tenant_id),
        "bind_dn": get_runtime_value("ldap.bind_dn", "LDAP_BIND_DN", "", tenant_id=normalized_tenant_id),
        "bind_password": get_runtime_value("ldap.bind_password", "LDAP_BIND_PASSWORD", "", tenant_id=normalized_tenant_id),
        "base_dn": get_runtime_value("ldap.base_dn", "LDAP_BASE_DN", "", tenant_id=normalized_tenant_id),
        "user_filter": get_runtime_value("ldap.user_filter", "LDAP_USER_FILTER", "(sAMAccountName={username})", tenant_id=normalized_tenant_id),
        "display_name_attribute": get_runtime_value("ldap.display_name_attribute", "LDAP_DISPLAY_NAME_ATTRIBUTE", "displayName", tenant_id=normalized_tenant_id),
        "login_attribute": get_runtime_value("ldap.login_attribute", "LDAP_LOGIN_ATTRIBUTE", "sAMAccountName", tenant_id=normalized_tenant_id),
        "group_attribute": get_runtime_value("ldap.group_attribute", "LDAP_GROUP_ATTRIBUTE", "memberOf", tenant_id=normalized_tenant_id),
        "group_role_map_json": get_runtime_value("ldap.group_role_map_json", "LDAP_GROUP_ROLE_MAP_JSON", "{}", tenant_id=normalized_tenant_id),
        "default_role": get_runtime_value("ldap.default_role", "LDAP_DEFAULT_ROLE", "student", tenant_id=normalized_tenant_id),
        "timeout_seconds": get_runtime_value("ldap.timeout_seconds", "LDAP_TIMEOUT_SECONDS", "5", tenant_id=normalized_tenant_id),
    }


def save_ldap_config(payload: dict[str, object], tenant_id: int | None = None) -> dict[str, object]:
    normalized_tenant_id = _require_tenant_id(tenant_id, operation="save_ldap_config")
    mapping = {
        "enabled": ("ldap.enabled", False),
        "server_uri": ("ldap.server_uri", False),
        "bind_dn": ("ldap.bind_dn", False),
        "bind_password": ("ldap.bind_password", True),
        "base_dn": ("ldap.base_dn", False),
        "user_filter": ("ldap.user_filter", False),
        "display_name_attribute": ("ldap.display_name_attribute", False),
        "login_attribute": ("ldap.login_attribute", False),
        "group_attribute": ("ldap.group_attribute", False),
        "group_role_map_json": ("ldap.group_role_map_json", False),
        "default_role": ("ldap.default_role", False),
        "timeout_seconds": ("ldap.timeout_seconds", False),
    }

    for field, (key, secret) in mapping.items():
        if field in payload and payload[field] is not None:
            save_setting(key, str(payload[field]).strip(), is_secret=secret, tenant_id=normalized_tenant_id)

    return get_ldap_config_for_admin(tenant_id=normalized_tenant_id)


def get_ai_provider_config_for_admin(provider: str, tenant_id: int | None = None) -> dict[str, object]:
    normalized_tenant_id = _require_tenant_id(tenant_id, operation="get_ai_provider_config_for_admin")
    runtime = get_ai_provider_runtime_config(provider, tenant_id=normalized_tenant_id)
    return {
        "provider": provider,
        "configured": bool(runtime["api_key"] or (provider == "custom" and runtime["validation_url"])),
        "has_api_key": bool(runtime["api_key"]),
        "validation_url": runtime["validation_url"],
    }


def get_ai_provider_runtime_config(provider: str, tenant_id: int | None = None) -> dict[str, str]:
    normalized_tenant_id = _require_tenant_id(tenant_id, operation="get_ai_provider_runtime_config")
    provider = provider.strip().lower()
    config_map = {
        "openai": {
            "api_key": ("ai.openai.api_key", "OPENAI_API_KEY", ""),
            "validation_url": ("ai.openai.validation_url", "", "https://api.openai.com/v1/models"),
        },
        "gemini": {
            "api_key": ("ai.gemini.api_key", "GEMINI_API_KEY", ""),
            "validation_url": ("ai.gemini.validation_url", "", "https://generativelanguage.googleapis.com/v1beta/models"),
        },
        "anthropic": {
            "api_key": ("ai.anthropic.api_key", "ANTHROPIC_API_KEY", ""),
            "validation_url": ("ai.anthropic.validation_url", "", "https://api.anthropic.com/v1/models"),
        },
        "custom": {
            "api_key": ("ai.custom.api_key", "AI_CUSTOM_PROVIDER_API_KEY", ""),
            "validation_url": ("ai.custom.validation_url", "AI_CUSTOM_PROVIDER_URL", ""),
        },
    }
    if provider not in config_map:
        raise ValueError("unknown provider")

    provider_config = config_map[provider]
    return {
        "api_key": get_runtime_value(*provider_config["api_key"], tenant_id=normalized_tenant_id),
        "validation_url": get_runtime_value(*provider_config["validation_url"], tenant_id=normalized_tenant_id),
    }


def save_ai_provider_config(
    provider: str,
    api_key: str | None,
    validation_url: str | None,
    tenant_id: int | None = None,
) -> dict[str, object]:
    normalized_tenant_id = _require_tenant_id(tenant_id, operation="save_ai_provider_config")
    provider = provider.strip().lower()
    if provider not in {"openai", "gemini", "anthropic", "custom"}:
        raise ValueError("unknown provider")

    if api_key is not None:
        save_setting(f"ai.{provider}.api_key", api_key.strip(), is_secret=True, tenant_id=normalized_tenant_id)
    if validation_url is not None:
        save_setting(f"ai.{provider}.validation_url", validation_url.strip(), is_secret=False, tenant_id=normalized_tenant_id)

    return get_ai_provider_config_for_admin(provider, tenant_id=normalized_tenant_id)


def list_ai_provider_config_for_admin(tenant_id: int | None = None) -> list[dict[str, object]]:
    normalized_tenant_id = _require_tenant_id(tenant_id, operation="list_ai_provider_config_for_admin")
    providers = ["openai", "gemini", "anthropic", "custom"]
    prefetch_settings(
        [
            "ai.openai.api_key", "ai.openai.validation_url",
            "ai.gemini.api_key", "ai.gemini.validation_url",
            "ai.anthropic.api_key", "ai.anthropic.validation_url",
            "ai.custom.api_key", "ai.custom.validation_url",
        ],
        tenant_id=normalized_tenant_id,
    )
    return [get_ai_provider_config_for_admin(provider, tenant_id=normalized_tenant_id) for provider in providers]
