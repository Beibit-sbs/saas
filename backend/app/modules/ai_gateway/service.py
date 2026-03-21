from __future__ import annotations

import json
import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Protocol

import httpx

from app.modules.integrations.service import get_ai_provider_runtime_config
from app.modules.integrations.service import get_runtime_value

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


_limit_lock = Lock()
_limit_events: dict[tuple[str, str], deque[float]] = defaultdict(deque)

_registry_lock = Lock()
_model_registry: dict[str, dict[str, object]] = {}

_usage_lock = Lock()
_usage_logs: deque[dict[str, object]] = deque(maxlen=2000)

SUPPORTED_PROVIDERS = ("openai", "gemini", "anthropic", "custom")


DEFAULT_MODELS: tuple[dict[str, object], ...] = (
    {
        "model_key": "openai.default.chat",
        "provider": "openai",
        "provider_model_id": "gpt-4o-mini",
        "display_name": "OpenAI Default Chat",
        "enabled": True,
        "priority": 100,
        "metadata": {},
    },
    {
        "model_key": "gemini.default.chat",
        "provider": "gemini",
        "provider_model_id": "gemini-1.5-flash",
        "display_name": "Gemini Default Chat",
        "enabled": True,
        "priority": 200,
        "metadata": {},
    },
    {
        "model_key": "anthropic.default.chat",
        "provider": "anthropic",
        "provider_model_id": "claude-3-5-haiku-latest",
        "display_name": "Anthropic Default Chat",
        "enabled": True,
        "priority": 300,
        "metadata": {},
    },
    {
        "model_key": "custom.default.chat",
        "provider": "custom",
        "provider_model_id": "default-chat",
        "display_name": "Custom Default Chat",
        "enabled": False,
        "priority": 400,
        "metadata": {},
    },
)


class AIGatewayError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        detail: str,
        audit_reason: str,
        provider: str | None = None,
        model: str | None = None,
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.audit_reason = audit_reason
        self.provider = provider
        self.model = model


class AIProviderTimeoutError(Exception):
    pass


class AIProviderExecutionError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class NormalizedChatResult:
    provider: str
    output_text: str
    finish_reason: str | None
    provider_response_id: str | None
    usage: dict[str, int | None]


class AIProviderAdapter(Protocol):
    provider: str

    def execute_chat(
        self,
        *,
        provider_model_id: str,
        messages: list[dict[str, str]],
        temperature: float | None,
        max_tokens: int | None,
        runtime_config: dict[str, str],
    ) -> NormalizedChatResult:
        ...


def _db_url() -> str | None:
    return os.getenv("DATABASE_URL")


def _use_database() -> bool:
    return bool(_db_url()) and psycopg is not None


def _should_fallback_to_memory(exc: Exception) -> bool:
    if isinstance(exc, RuntimeError) and str(exc) == "database unavailable":
        return True
    if isinstance(exc, (ConnectionError, TimeoutError, OSError, ValueError)):
        return True
    if psycopg is not None and isinstance(exc, (psycopg.OperationalError, psycopg.InterfaceError)):
        return True
    return False


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _timeout() -> float:
    raw = os.getenv("AI_PROVIDER_TIMEOUT_SECONDS", "8").strip()
    try:
        return max(1.0, float(raw))
    except ValueError:
        return 8.0


def _runtime_int(setting_key: str, env_name: str, default: int) -> int:
    raw = get_runtime_value(setting_key, env_name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        return default


def _rate_limit_window_seconds() -> int:
    return max(1, _runtime_int("ai.rate_limit.window_seconds", "AI_RATE_LIMIT_WINDOW_SECONDS", 60))


def _provider_limit(provider: str) -> int:
    env_name = f"AI_RATE_LIMIT_PROVIDER_{provider.upper()}_LIMIT"
    return max(0, _runtime_int(f"ai.rate_limit.provider.{provider}", env_name, 30))


def _user_limit(actor: str) -> int:
    normalized_actor = actor.strip().lower().replace("@", "_").replace(".", "_")
    env_name = f"AI_RATE_LIMIT_USER_{normalized_actor.upper()}_LIMIT"
    specific = _runtime_int(f"ai.rate_limit.user.{normalized_actor}", env_name, -1)
    if specific >= 0:
        return specific
    return max(0, _runtime_int("ai.rate_limit.user.default", "AI_RATE_LIMIT_USER_LIMIT", 10))


def _role_limit(role: str) -> int:
    normalized_role = role.strip().lower()
    env_name = f"AI_RATE_LIMIT_ROLE_{normalized_role.upper()}_LIMIT"
    specific = _runtime_int(f"ai.rate_limit.role.{normalized_role}", env_name, -1)
    if specific >= 0:
        return specific
    return max(0, _runtime_int("ai.rate_limit.role.default", "AI_RATE_LIMIT_ROLE_LIMIT", 50))


def clear_rate_limit_state() -> None:
    with _limit_lock:
        _limit_events.clear()


def clear_ai_gateway_state() -> None:
    clear_rate_limit_state()
    with _registry_lock:
        _model_registry.clear()
    with _usage_lock:
        _usage_logs.clear()


def _prune(bucket: deque[float], now: float, window_seconds: int) -> None:
    cutoff = now - window_seconds
    while bucket and bucket[0] <= cutoff:
        bucket.popleft()


def enforce_rate_limit(provider: str, actor: str, roles: list[str]) -> dict[str, Any]:
    window_seconds = _rate_limit_window_seconds()
    normalized_provider = provider.strip().lower()
    normalized_actor = actor.strip().lower()
    normalized_roles = [role.strip().lower() for role in roles if role.strip()]
    now = time.time()

    checks: list[tuple[tuple[str, str], int, str]] = [
        (("provider", normalized_provider), _provider_limit(normalized_provider), f"provider:{normalized_provider}"),
        (("user", normalized_actor), _user_limit(normalized_actor), f"user:{normalized_actor}"),
    ]
    for role in normalized_roles:
        checks.append((("role", role), _role_limit(role), f"role:{role}"))

    with _limit_lock:
        for key, limit, label in checks:
            bucket = _limit_events[key]
            _prune(bucket, now, window_seconds)
            if limit > 0 and len(bucket) >= limit:
                retry_after = max(1, int(window_seconds - (now - bucket[0]))) if bucket else window_seconds
                raise ValueError(f"AI Gateway rate limit exceeded for {label}; retry in {retry_after}s")

        for key, _, _ in checks:
            _limit_events[key].append(now)

        provider_bucket = _limit_events[("provider", normalized_provider)]
        user_bucket = _limit_events[("user", normalized_actor)]

    return {
        "window_seconds": window_seconds,
        "provider_limit": _provider_limit(normalized_provider),
        "provider_used": len(provider_bucket),
        "user_limit": _user_limit(normalized_actor),
        "user_used": len(user_bucket),
    }


def _ensure_ai_gateway_tables(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_ai_models (
                model_key TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                provider_model_id TEXT NOT NULL,
                display_name TEXT NOT NULL,
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                priority INTEGER NOT NULL DEFAULT 100,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_app_ai_models_provider_enabled ON app_ai_models (provider, enabled)"
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_ai_usage_logs (
                id BIGSERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                actor TEXT NOT NULL,
                provider TEXT NOT NULL,
                model_key TEXT NOT NULL,
                provider_model_id TEXT NOT NULL,
                outcome TEXT NOT NULL,
                latency_ms INTEGER NOT NULL,
                input_tokens INTEGER,
                output_tokens INTEGER,
                total_tokens INTEGER,
                failure_reason TEXT,
                correlation_id TEXT
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_app_ai_usage_logs_timestamp ON app_ai_usage_logs (timestamp DESC)"
        )
    conn.commit()


def _seed_default_models_db(conn) -> None:
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO app_ai_models (model_key, provider, provider_model_id, display_name, enabled, priority, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (model_key) DO NOTHING
            """,
            [
                (
                    item["model_key"],
                    item["provider"],
                    item["provider_model_id"],
                    item["display_name"],
                    item["enabled"],
                    item["priority"],
                    json.dumps(item.get("metadata") or {}, ensure_ascii=False),
                )
                for item in DEFAULT_MODELS
            ],
        )
    conn.commit()


def _seed_default_models_memory() -> None:
    with _registry_lock:
        if _model_registry:
            return
        for item in DEFAULT_MODELS:
            _model_registry[item["model_key"]] = {
                **item,
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
            }


def _normalize_model_key(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("model_key is required")
    if len(normalized) > 120:
        raise ValueError("model_key must be at most 120 characters")
    return normalized


def _normalize_provider(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in SUPPORTED_PROVIDERS:
        raise ValueError("unknown provider")
    return normalized


def _normalize_model_payload(
    model_key: str,
    provider: str,
    provider_model_id: str,
    display_name: str,
    enabled: bool,
    priority: int,
    metadata: dict[str, Any] | None,
) -> dict[str, object]:
    normalized_provider_model_id = provider_model_id.strip()
    normalized_display_name = display_name.strip()
    if not normalized_provider_model_id:
        raise ValueError("provider_model_id is required")
    if not normalized_display_name:
        raise ValueError("display_name is required")
    if len(normalized_provider_model_id) > 200:
        raise ValueError("provider_model_id must be at most 200 characters")
    if len(normalized_display_name) > 200:
        raise ValueError("display_name must be at most 200 characters")
    if priority < 0 or priority > 10_000:
        raise ValueError("priority must be between 0 and 10000")

    return {
        "model_key": _normalize_model_key(model_key),
        "provider": _normalize_provider(provider),
        "provider_model_id": normalized_provider_model_id,
        "display_name": normalized_display_name,
        "enabled": bool(enabled),
        "priority": int(priority),
        "metadata": metadata or {},
    }


def _model_row_to_dict(row: tuple[Any, ...]) -> dict[str, object]:
    metadata = row[6]
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            metadata = {}
    if not isinstance(metadata, dict):
        metadata = {}

    created_at = row[7].isoformat() if hasattr(row[7], "isoformat") else str(row[7])
    updated_at = row[8].isoformat() if hasattr(row[8], "isoformat") else str(row[8])

    return {
        "model_key": row[0],
        "provider": row[1],
        "provider_model_id": row[2],
        "display_name": row[3],
        "enabled": bool(row[4]),
        "priority": int(row[5]),
        "metadata": metadata,
        "created_at": created_at,
        "updated_at": updated_at,
    }


def _list_models_db(include_disabled: bool = True) -> list[dict[str, object]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_ai_gateway_tables(conn)
        _seed_default_models_db(conn)
        with conn.cursor() as cur:
            if include_disabled:
                cur.execute(
                    """
                    SELECT model_key, provider, provider_model_id, display_name, enabled, priority, metadata, created_at, updated_at
                    FROM app_ai_models
                    ORDER BY priority ASC, model_key ASC
                    """
                )
            else:
                cur.execute(
                    """
                    SELECT model_key, provider, provider_model_id, display_name, enabled, priority, metadata, created_at, updated_at
                    FROM app_ai_models
                    WHERE enabled = TRUE
                    ORDER BY priority ASC, model_key ASC
                    """
                )
            return [_model_row_to_dict(row) for row in cur.fetchall()]


def _upsert_model_db(entry: dict[str, object]) -> dict[str, object]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_ai_gateway_tables(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_ai_models (model_key, provider, provider_model_id, display_name, enabled, priority, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (model_key)
                DO UPDATE SET
                    provider = EXCLUDED.provider,
                    provider_model_id = EXCLUDED.provider_model_id,
                    display_name = EXCLUDED.display_name,
                    enabled = EXCLUDED.enabled,
                    priority = EXCLUDED.priority,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
                RETURNING model_key, provider, provider_model_id, display_name, enabled, priority, metadata, created_at, updated_at
                """,
                (
                    entry["model_key"],
                    entry["provider"],
                    entry["provider_model_id"],
                    entry["display_name"],
                    entry["enabled"],
                    entry["priority"],
                    json.dumps(entry.get("metadata") or {}, ensure_ascii=False),
                ),
            )
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise RuntimeError("failed to save model")
    return _model_row_to_dict(row)


def _set_model_enabled_db(model_key: str, enabled: bool) -> dict[str, object]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_ai_gateway_tables(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE app_ai_models
                SET enabled = %s,
                    updated_at = NOW()
                WHERE model_key = %s
                RETURNING model_key, provider, provider_model_id, display_name, enabled, priority, metadata, created_at, updated_at
                """,
                (bool(enabled), model_key),
            )
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise ValueError("model not found")
    return _model_row_to_dict(row)


def _resolve_model_db(model_key: str) -> dict[str, object] | None:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_ai_gateway_tables(conn)
        _seed_default_models_db(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT model_key, provider, provider_model_id, display_name, enabled, priority, metadata, created_at, updated_at
                FROM app_ai_models
                WHERE model_key = %s
                """,
                (model_key,),
            )
            row = cur.fetchone()

    if row is None:
        return None
    return _model_row_to_dict(row)


def _insert_usage_log_db(entry: dict[str, object]) -> None:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_ai_gateway_tables(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_ai_usage_logs (
                    timestamp,
                    actor,
                    provider,
                    model_key,
                    provider_model_id,
                    outcome,
                    latency_ms,
                    input_tokens,
                    output_tokens,
                    total_tokens,
                    failure_reason,
                    correlation_id
                )
                VALUES (
                    NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    entry["actor"],
                    entry["provider"],
                    entry["model_key"],
                    entry["provider_model_id"],
                    entry["outcome"],
                    entry["latency_ms"],
                    entry.get("input_tokens"),
                    entry.get("output_tokens"),
                    entry.get("total_tokens"),
                    entry.get("failure_reason"),
                    entry.get("correlation_id"),
                ),
            )
        conn.commit()


def _list_usage_logs_db(limit: int) -> list[dict[str, object]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_ai_gateway_tables(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT actor, provider, model_key, provider_model_id, outcome, latency_ms,
                       input_tokens, output_tokens, total_tokens, failure_reason, correlation_id,
                       timestamp
                FROM app_ai_usage_logs
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (max(1, min(limit, 500)),),
            )
            rows = cur.fetchall()

    result: list[dict[str, object]] = []
    for row in rows:
        ts = row[11].isoformat() if hasattr(row[11], "isoformat") else str(row[11])
        result.append(
            {
                "actor": row[0],
                "provider": row[1],
                "model_key": row[2],
                "provider_model_id": row[3],
                "outcome": row[4],
                "latency_ms": int(row[5]),
                "input_tokens": row[6],
                "output_tokens": row[7],
                "total_tokens": row[8],
                "failure_reason": row[9],
                "correlation_id": row[10],
                "timestamp": ts,
            }
        )
    return result


def list_models(include_disabled: bool = True) -> list[dict[str, object]]:
    if _use_database():
        try:
            return _list_models_db(include_disabled=include_disabled)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    _seed_default_models_memory()
    with _registry_lock:
        rows = list(_model_registry.values())

    if not include_disabled:
        rows = [item for item in rows if bool(item.get("enabled"))]
    return sorted(rows, key=lambda item: (int(item.get("priority", 100)), str(item.get("model_key", ""))))


def upsert_model(
    *,
    model_key: str,
    provider: str,
    provider_model_id: str,
    display_name: str,
    enabled: bool,
    priority: int,
    metadata: dict[str, Any] | None,
) -> dict[str, object]:
    entry = _normalize_model_payload(
        model_key=model_key,
        provider=provider,
        provider_model_id=provider_model_id,
        display_name=display_name,
        enabled=enabled,
        priority=priority,
        metadata=metadata,
    )

    if _use_database():
        try:
            return _upsert_model_db(entry)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    _seed_default_models_memory()
    now = _now_iso()
    with _registry_lock:
        previous = _model_registry.get(entry["model_key"])
        merged = {
            **entry,
            "created_at": previous.get("created_at") if previous else now,
            "updated_at": now,
        }
        _model_registry[entry["model_key"]] = merged
        return merged


def set_model_enabled(model_key: str, enabled: bool) -> dict[str, object]:
    normalized_key = _normalize_model_key(model_key)
    if _use_database():
        try:
            return _set_model_enabled_db(normalized_key, enabled)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    _seed_default_models_memory()
    with _registry_lock:
        current = _model_registry.get(normalized_key)
        if current is None:
            raise ValueError("model not found")
        current["enabled"] = bool(enabled)
        current["updated_at"] = _now_iso()
        return current


def _resolve_model(model_key: str) -> dict[str, object] | None:
    normalized_key = _normalize_model_key(model_key)
    if _use_database():
        try:
            return _resolve_model_db(normalized_key)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    _seed_default_models_memory()
    with _registry_lock:
        return _model_registry.get(normalized_key)


def _record_usage_log(
    *,
    actor: str,
    provider: str,
    model_key: str,
    provider_model_id: str,
    outcome: str,
    latency_ms: int,
    input_tokens: int | None,
    output_tokens: int | None,
    total_tokens: int | None,
    failure_reason: str | None,
    correlation_id: str | None,
) -> None:
    entry = {
        "actor": actor,
        "provider": provider,
        "model_key": model_key,
        "provider_model_id": provider_model_id,
        "outcome": outcome,
        "latency_ms": latency_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "failure_reason": failure_reason,
        "correlation_id": correlation_id,
        "timestamp": _now_iso(),
    }

    if _use_database():
        try:
            _insert_usage_log_db(entry)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    with _usage_lock:
        _usage_logs.appendleft(entry)


def list_usage_logs(limit: int = 100) -> list[dict[str, object]]:
    if _use_database():
        try:
            return _list_usage_logs_db(limit)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    with _usage_lock:
        return list(_usage_logs)[: max(1, min(limit, 500))]


def _provider_config(tenant_id: int | None = None) -> dict[str, dict[str, Any]]:
    openai_cfg = get_ai_provider_runtime_config("openai", tenant_id=tenant_id)
    gemini_cfg = get_ai_provider_runtime_config("gemini", tenant_id=tenant_id)
    anthropic_cfg = get_ai_provider_runtime_config("anthropic", tenant_id=tenant_id)
    custom_cfg = get_ai_provider_runtime_config("custom", tenant_id=tenant_id)

    return {
        "openai": {
            "configured": bool(openai_cfg["api_key"]),
            "validation_url": openai_cfg["validation_url"] or "https://api.openai.com/v1/models",
            "headers": lambda: {"Authorization": f"Bearer {openai_cfg['api_key']}"},
            "params": lambda: None,
        },
        "gemini": {
            "configured": bool(gemini_cfg["api_key"]),
            "validation_url": gemini_cfg["validation_url"] or "https://generativelanguage.googleapis.com/v1beta/models",
            "headers": lambda: {},
            "params": lambda: {"key": gemini_cfg["api_key"]},
        },
        "anthropic": {
            "configured": bool(anthropic_cfg["api_key"]),
            "validation_url": anthropic_cfg["validation_url"] or "https://api.anthropic.com/v1/models",
            "headers": lambda: {
                "x-api-key": anthropic_cfg["api_key"],
                "anthropic-version": "2023-06-01",
            },
            "params": lambda: None,
        },
        "custom": {
            "configured": bool(custom_cfg["validation_url"]),
            "validation_url": custom_cfg["validation_url"],
            "headers": lambda: (
                {"Authorization": f"Bearer {custom_cfg['api_key']}"}
                if custom_cfg["api_key"]
                else {}
            ),
            "params": lambda: None,
        },
    }


def _provider_runtime_config(provider: str, tenant_id: int | None = None) -> dict[str, str]:
    provider = provider.strip().lower()
    runtime = get_ai_provider_runtime_config(provider, tenant_id=tenant_id)

    if provider == "openai":
        runtime["chat_url"] = get_runtime_value(
            "ai.openai.chat_url",
            "AI_OPENAI_CHAT_URL",
            "https://api.openai.com/v1/chat/completions",
            tenant_id=tenant_id,
        )
    elif provider == "gemini":
        runtime["chat_url"] = get_runtime_value(
            "ai.gemini.chat_url",
            "AI_GEMINI_CHAT_URL",
            "https://generativelanguage.googleapis.com/v1beta/models",
            tenant_id=tenant_id,
        )
    elif provider == "anthropic":
        runtime["chat_url"] = get_runtime_value(
            "ai.anthropic.chat_url",
            "AI_ANTHROPIC_CHAT_URL",
            "https://api.anthropic.com/v1/messages",
            tenant_id=tenant_id,
        )
    elif provider == "custom":
        runtime["chat_url"] = get_runtime_value(
            "ai.custom.chat_url",
            "AI_CUSTOM_PROVIDER_CHAT_URL",
            runtime.get("validation_url", ""),
            tenant_id=tenant_id,
        )

    return runtime


def list_provider_status(tenant_id: int | None = None) -> list[dict[str, Any]]:
    providers = []
    for name, config in _provider_config(tenant_id=tenant_id).items():
        providers.append(
            {
                "provider": name,
                "configured": bool(config["configured"]),
                "validation_url": config["validation_url"],
            }
        )
    return providers


def _request(method: str, url: str, headers: dict[str, str], params: dict[str, str] | None) -> httpx.Response:
    with httpx.Client(timeout=_timeout(), follow_redirects=True) as client:
        return client.request(method, url, headers=headers, params=params)


def _request_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    params: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        with httpx.Client(timeout=_timeout(), follow_redirects=True) as client:
            response = client.request(method, url, headers=headers, params=params, json=payload)
    except httpx.TimeoutException as exc:
        raise AIProviderTimeoutError("provider timeout") from exc
    except httpx.HTTPError as exc:
        raise AIProviderExecutionError("provider request failed") from exc

    if response.status_code >= 400:
        detail = "provider request failed"
        try:
            data = response.json()
            if isinstance(data, dict):
                maybe_message = data.get("error") or data.get("message") or data.get("detail")
                if isinstance(maybe_message, dict):
                    maybe_message = maybe_message.get("message")
                if maybe_message:
                    detail = str(maybe_message)
        except Exception:
            if response.text:
                detail = response.text[:250]
        raise AIProviderExecutionError(detail, status_code=response.status_code)

    try:
        data = response.json()
    except Exception as exc:
        raise AIProviderExecutionError("provider returned non-JSON response") from exc

    if not isinstance(data, dict):
        raise AIProviderExecutionError("provider returned invalid response body")
    return data


def _coerce_message_content(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts).strip()
    return ""


class OpenAIAdapter:
    provider = "openai"

    def execute_chat(
        self,
        *,
        provider_model_id: str,
        messages: list[dict[str, str]],
        temperature: float | None,
        max_tokens: int | None,
        runtime_config: dict[str, str],
    ) -> NormalizedChatResult:
        if not runtime_config.get("api_key"):
            raise AIProviderExecutionError("openai is not configured")

        payload: dict[str, Any] = {
            "model": provider_model_id,
            "messages": messages,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        data = _request_json(
            "POST",
            runtime_config["chat_url"],
            headers={
                "Authorization": f"Bearer {runtime_config['api_key']}",
                "Content-Type": "application/json",
            },
            payload=payload,
        )

        choices = data.get("choices") or []
        first = choices[0] if choices else {}
        message = first.get("message") if isinstance(first, dict) else {}
        output_text = _coerce_message_content(message.get("content") if isinstance(message, dict) else "")
        usage = data.get("usage") or {}
        return NormalizedChatResult(
            provider=self.provider,
            output_text=output_text,
            finish_reason=first.get("finish_reason") if isinstance(first, dict) else None,
            provider_response_id=str(data.get("id")) if data.get("id") else None,
            usage={
                "input_tokens": usage.get("prompt_tokens"),
                "output_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
            },
        )


class GeminiAdapter:
    provider = "gemini"

    def execute_chat(
        self,
        *,
        provider_model_id: str,
        messages: list[dict[str, str]],
        temperature: float | None,
        max_tokens: int | None,
        runtime_config: dict[str, str],
    ) -> NormalizedChatResult:
        if not runtime_config.get("api_key"):
            raise AIProviderExecutionError("gemini is not configured")

        contents: list[dict[str, Any]] = []
        for item in messages:
            role = "model" if item.get("role") == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": item.get("content", "")}]})

        payload: dict[str, Any] = {"contents": contents}
        generation_config: dict[str, Any] = {}
        if temperature is not None:
            generation_config["temperature"] = temperature
        if max_tokens is not None:
            generation_config["maxOutputTokens"] = max_tokens
        if generation_config:
            payload["generationConfig"] = generation_config

        base_url = runtime_config["chat_url"].rstrip("/")
        url = f"{base_url}/{provider_model_id}:generateContent"
        data = _request_json(
            "POST",
            url,
            headers={"Content-Type": "application/json"},
            params={"key": runtime_config["api_key"]},
            payload=payload,
        )

        candidates = data.get("candidates") or []
        first = candidates[0] if candidates else {}
        content = first.get("content") if isinstance(first, dict) else {}
        parts = content.get("parts") if isinstance(content, dict) else []
        output_text = "\n".join(
            item.get("text", "")
            for item in parts
            if isinstance(item, dict) and isinstance(item.get("text"), str)
        ).strip()

        usage = data.get("usageMetadata") or {}
        return NormalizedChatResult(
            provider=self.provider,
            output_text=output_text,
            finish_reason=first.get("finishReason") if isinstance(first, dict) else None,
            provider_response_id=None,
            usage={
                "input_tokens": usage.get("promptTokenCount"),
                "output_tokens": usage.get("candidatesTokenCount"),
                "total_tokens": usage.get("totalTokenCount"),
            },
        )


class AnthropicAdapter:
    provider = "anthropic"

    def execute_chat(
        self,
        *,
        provider_model_id: str,
        messages: list[dict[str, str]],
        temperature: float | None,
        max_tokens: int | None,
        runtime_config: dict[str, str],
    ) -> NormalizedChatResult:
        if not runtime_config.get("api_key"):
            raise AIProviderExecutionError("anthropic is not configured")

        payload: dict[str, Any] = {
            "model": provider_model_id,
            "messages": [
                {"role": item.get("role"), "content": item.get("content", "")}
                for item in messages
                if item.get("role") in {"user", "assistant"}
            ],
            "max_tokens": max_tokens or 1024,
        }

        system_messages = [item.get("content", "") for item in messages if item.get("role") == "system"]
        if system_messages:
            payload["system"] = "\n".join(system_messages)
        if temperature is not None:
            payload["temperature"] = temperature

        data = _request_json(
            "POST",
            runtime_config["chat_url"],
            headers={
                "x-api-key": runtime_config["api_key"],
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            payload=payload,
        )

        content = data.get("content") or []
        output_text = "\n".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ).strip()

        usage = data.get("usage") or {}
        return NormalizedChatResult(
            provider=self.provider,
            output_text=output_text,
            finish_reason=data.get("stop_reason"),
            provider_response_id=str(data.get("id")) if data.get("id") else None,
            usage={
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
                "total_tokens": (
                    (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0)
                    if usage.get("input_tokens") is not None or usage.get("output_tokens") is not None
                    else None
                ),
            },
        )


class CustomAdapter:
    provider = "custom"

    def execute_chat(
        self,
        *,
        provider_model_id: str,
        messages: list[dict[str, str]],
        temperature: float | None,
        max_tokens: int | None,
        runtime_config: dict[str, str],
    ) -> NormalizedChatResult:
        chat_url = (runtime_config.get("chat_url") or "").strip()
        if not chat_url:
            raise AIProviderExecutionError("custom provider chat URL is not configured")

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if runtime_config.get("api_key"):
            headers["Authorization"] = f"Bearer {runtime_config['api_key']}"

        payload: dict[str, Any] = {
            "model": provider_model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        data = _request_json(
            "POST",
            chat_url,
            headers=headers,
            payload=payload,
        )

        output_text = ""
        if isinstance(data.get("output_text"), str):
            output_text = data["output_text"]
        elif isinstance(data.get("choices"), list) and data["choices"]:
            first = data["choices"][0]
            if isinstance(first, dict):
                msg = first.get("message")
                if isinstance(msg, dict):
                    output_text = _coerce_message_content(msg.get("content"))

        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        return NormalizedChatResult(
            provider=self.provider,
            output_text=output_text,
            finish_reason=data.get("finish_reason") if isinstance(data.get("finish_reason"), str) else None,
            provider_response_id=str(data.get("id")) if data.get("id") else None,
            usage={
                "input_tokens": usage.get("input_tokens") or usage.get("prompt_tokens"),
                "output_tokens": usage.get("output_tokens") or usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
            },
        )


_ADAPTERS: dict[str, AIProviderAdapter] = {
    "openai": OpenAIAdapter(),
    "gemini": GeminiAdapter(),
    "anthropic": AnthropicAdapter(),
    "custom": CustomAdapter(),
}


def _adapter_for_provider(provider: str) -> AIProviderAdapter:
    adapter = _ADAPTERS.get(provider)
    if adapter is None:
        raise AIGatewayError(
            status_code=400,
            detail="unsupported provider",
            audit_reason="unsupported_provider",
            provider=provider,
        )
    return adapter


def validate_provider_runtime(
    provider: str,
    actor: str | None = None,
    roles: list[str] | None = None,
    tenant_id: int | None = None,
) -> dict[str, Any]:
    config = _provider_config(tenant_id=tenant_id).get(provider)
    if config is None:
        raise ValueError("unknown provider")
    if not config["configured"]:
        raise ValueError(f"{provider} is not configured")

    url = str(config["validation_url"] or "").strip()
    if not url:
        raise ValueError(f"{provider} validation URL is not configured")

    limit_state = None
    if actor:
        limit_state = enforce_rate_limit(provider, actor=actor, roles=roles or [])

    response = _request("GET", url, config["headers"](), config["params"]())
    if response.status_code >= 400:
        detail = response.text[:300] if response.text else str(response.status_code)
        raise ValueError(f"{provider} validation failed: {detail}")

    result = {
        "provider": provider,
        "status": "validated",
        "http_status": response.status_code,
        "validation_url": url,
    }
    if limit_state is not None:
        result["rate_limit"] = limit_state
    return result


def execute_chat(
    payload: dict[str, Any],
    *,
    actor: str,
    roles: list[str],
    tenant_id: int | None = None,
    correlation_id: str | None = None,
) -> dict[str, object]:
    model_key = str(payload.get("model", "")).strip()
    if not model_key:
        raise AIGatewayError(status_code=400, detail="model is required", audit_reason="invalid_payload")

    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        raise AIGatewayError(status_code=400, detail="messages are required", audit_reason="invalid_payload", model=model_key)

    model_entry = _resolve_model(model_key)
    if model_entry is None:
        raise AIGatewayError(status_code=400, detail="unknown model", audit_reason="unknown_model", model=model_key)
    if not bool(model_entry.get("enabled")):
        raise AIGatewayError(status_code=400, detail="model is disabled", audit_reason="disabled_model", model=model_key)

    provider = str(model_entry["provider"])
    provider_model_id = str(model_entry["provider_model_id"])

    started = time.monotonic()
    try:
        enforce_rate_limit(provider, actor=actor, roles=roles)
    except ValueError as exc:
        latency_ms = max(1, int((time.monotonic() - started) * 1000))
        _record_usage_log(
            actor=actor,
            provider=provider,
            model_key=model_key,
            provider_model_id=provider_model_id,
            outcome="rate_limited",
            latency_ms=latency_ms,
            input_tokens=None,
            output_tokens=None,
            total_tokens=None,
            failure_reason=str(exc),
            correlation_id=correlation_id,
        )
        raise AIGatewayError(
            status_code=429,
            detail=str(exc),
            audit_reason="rate_limit",
            provider=provider,
            model=model_key,
        ) from exc

    adapter = _adapter_for_provider(provider)
    runtime_config = _provider_runtime_config(provider, tenant_id=tenant_id)
    normalized_messages = [
        {
            "role": str(item.get("role", "")),
            "content": str(item.get("content", "")),
        }
        for item in messages
        if isinstance(item, dict)
    ]

    try:
        result = adapter.execute_chat(
            provider_model_id=provider_model_id,
            messages=normalized_messages,
            temperature=payload.get("temperature"),
            max_tokens=payload.get("max_tokens"),
            runtime_config=runtime_config,
        )
    except AIProviderTimeoutError as exc:
        latency_ms = max(1, int((time.monotonic() - started) * 1000))
        _record_usage_log(
            actor=actor,
            provider=provider,
            model_key=model_key,
            provider_model_id=provider_model_id,
            outcome="timeout",
            latency_ms=latency_ms,
            input_tokens=None,
            output_tokens=None,
            total_tokens=None,
            failure_reason="provider_timeout",
            correlation_id=correlation_id,
        )
        raise AIGatewayError(
            status_code=504,
            detail="upstream AI provider timeout",
            audit_reason="provider_timeout",
            provider=provider,
            model=model_key,
        ) from exc
    except AIProviderExecutionError as exc:
        latency_ms = max(1, int((time.monotonic() - started) * 1000))
        _record_usage_log(
            actor=actor,
            provider=provider,
            model_key=model_key,
            provider_model_id=provider_model_id,
            outcome="failed",
            latency_ms=latency_ms,
            input_tokens=None,
            output_tokens=None,
            total_tokens=None,
            failure_reason=str(exc),
            correlation_id=correlation_id,
        )
        raise AIGatewayError(
            status_code=502,
            detail="upstream AI provider error",
            audit_reason="provider_error",
            provider=provider,
            model=model_key,
        ) from exc

    latency_ms = max(1, int((time.monotonic() - started) * 1000))
    _record_usage_log(
        actor=actor,
        provider=provider,
        model_key=model_key,
        provider_model_id=provider_model_id,
        outcome="success",
        latency_ms=latency_ms,
        input_tokens=result.usage.get("input_tokens") if isinstance(result.usage, dict) else None,
        output_tokens=result.usage.get("output_tokens") if isinstance(result.usage, dict) else None,
        total_tokens=result.usage.get("total_tokens") if isinstance(result.usage, dict) else None,
        failure_reason=None,
        correlation_id=correlation_id,
    )

    return {
        "model": model_key,
        "provider": provider,
        "provider_model_id": provider_model_id,
        "output_text": result.output_text,
        "finish_reason": result.finish_reason,
        "usage": {
            "input_tokens": result.usage.get("input_tokens") if isinstance(result.usage, dict) else None,
            "output_tokens": result.usage.get("output_tokens") if isinstance(result.usage, dict) else None,
            "total_tokens": result.usage.get("total_tokens") if isinstance(result.usage, dict) else None,
        },
        "latency_ms": latency_ms,
    }