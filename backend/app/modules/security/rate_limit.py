from __future__ import annotations

import json
import time
from fnmatch import fnmatch
from collections import defaultdict, deque
from dataclasses import dataclass
from functools import lru_cache
from threading import Lock
from typing import Any
from urllib.parse import quote
from uuid import uuid4

from fastapi import Request

from app.core.config import (
    get_auth_lockout_base_seconds,
    get_auth_lockout_max_seconds,
    get_auth_lockout_reset_window_seconds,
    get_auth_lockout_threshold,
    get_rate_limit_class_burst_limit,
    get_rate_limit_class_burst_window_seconds,
    get_rate_limit_class_limit,
    get_rate_limit_class_window_seconds,
    get_rate_limit_endpoint_overrides,
    get_rate_limit_login_identifier_limit,
    get_rate_limit_login_ip_limit,
    get_rate_limit_login_window_seconds,
    get_rate_limit_redis_url,
    get_rate_limit_sensitive_admin_limit,
    get_rate_limit_sensitive_admin_window_seconds,
    is_rate_limit_service_bypass_enabled,
    is_rate_limit_enabled,
)
from app.modules.auth.token_service import TokenValidationError, parse_access_token_from_request


@dataclass(frozen=True)
class LimitCheck:
    bucket_key: tuple[str, ...]
    window_seconds: int
    limit: int
    label: str


@dataclass(frozen=True)
class RateLimitDecision:
    scope: str
    retry_after: int
    label: str


@dataclass
class _AuthFailureState:
    failures: int = 0
    last_failure_at: float = 0.0
    locked_until: float = 0.0


_limit_lock = Lock()
_limit_events: dict[tuple[str, ...], deque[float]] = defaultdict(deque)
_auth_failure_lock = Lock()
_auth_failures: dict[tuple[str, ...], _AuthFailureState] = {}
_RATE_LIMIT_REDIS_PREFIX = "rate_limit:v2"

_LOGIN_PATHS = {
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/ldap-login"),
    ("POST", "/api/auth/refresh"),
    ("POST", "/api/auth/mfa/enable"),
    ("POST", "/api/auth/mfa/verify"),
    ("POST", "/api/auth/mfa/disable"),
}
_SENSITIVE_ADMIN_PATHS = {
    ("POST", "/api/admin/ldap/test-connection"),
    ("PUT", "/api/admin/integrations/ldap"),
    ("POST", "/api/admin/backups/run"),
    ("POST", "/api/admin/backups/restore"),
    ("POST", "/api/admin/backups/retention/apply"),
}
_GENERAL_EXEMPT_PATHS = {"/health", "/api/health", "/metrics"}
_TRAFFIC_CLASSES = {"read", "write", "jobs", "auth", "internal"}


_ATOMIC_ZSET_CHECK_AND_ADD_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window_seconds = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]
local expire_seconds = tonumber(ARGV[5])

if not now or not window_seconds or not limit then
    return {0, 1}
end

local cutoff = now - window_seconds
redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)

local current = tonumber(redis.call('ZCARD', key))
if current >= limit then
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    if oldest and oldest[2] then
        local retry_after = math.ceil(window_seconds - (now - tonumber(oldest[2])))
        if retry_after < 1 then
            retry_after = 1
        end
        return {0, retry_after}
    end
    return {0, window_seconds}
end

redis.call('ZADD', key, now, member)
redis.call('EXPIRE', key, expire_seconds)
return {1, 0}
"""


def clear_rate_limit_state() -> None:
    with _limit_lock:
        _limit_events.clear()
    with _auth_failure_lock:
        _auth_failures.clear()
    redis_client = _get_rate_limit_redis_client()
    if redis_client is not None:
        try:
            for key in redis_client.scan_iter("rate_limit:*"):
                redis_client.delete(key)
            for key in redis_client.scan_iter(f"{_RATE_LIMIT_REDIS_PREFIX}:*"):
                redis_client.delete(key)
        except Exception:
            pass
    cache_clear = getattr(_get_rate_limit_redis_client, "cache_clear", None)
    if callable(cache_clear):
        cache_clear()


def _prune(bucket: deque[float], now: float, window_seconds: int) -> None:
    cutoff = now - window_seconds
    while bucket and bucket[0] <= cutoff:
        bucket.popleft()


def _extract_client_ip(request: Request) -> str:
    # Prefer X-Real-IP set by the trusted reverse proxy (nginx: proxy_set_header).
    real_ip = request.headers.get("x-real-ip", "").strip()
    if real_ip:
        return real_ip
    # Fall back to rightmost IP in X-Forwarded-For.  The rightmost entry is
    # appended by the outermost trusted proxy and cannot be forged by the client.
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for.strip():
        ips = [ip.strip() for ip in forwarded_for.split(",") if ip.strip()]
        if ips:
            return ips[-1]
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _extract_tenant_id(request: Request, claims) -> int:
    raw = request.headers.get("x-tenant-id", "").strip()
    if raw:
        try:
            value = int(raw)
            if value > 0:
                return value
        except (TypeError, ValueError):
            pass
    if claims is not None:
        try:
            value = int(claims.tenant_id)
            if value > 0:
                return value
        except Exception:
            pass
    # Keep unauthenticated/invalid-tenant traffic in an isolated "unknown" bucket
    # instead of assigning it to a real tenant implicitly.
    return 0


def _resolve_claims_for_rate_limit(request: Request):
    authorization = request.headers.get("authorization")
    try:
        return parse_access_token_from_request(request, authorization)
    except TokenValidationError:
        return None
    except Exception:
        return None


def _build_subject(*, actor: str | None, client_ip: str) -> str:
    normalized_actor = str(actor or "").strip().lower()
    if normalized_actor:
        return f"actor:{normalized_actor}"
    return f"ip:{client_ip}"


def _extract_login_identifier(body: bytes) -> str:
    if not body:
        return ""
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ""
    if not isinstance(payload, dict):
        return ""
    for key in ("login", "user_id", "username"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return ""


def _auth_failure_keys(*, tenant_id: int, client_ip: str, login_identifier: str | None) -> list[tuple[tuple[str, ...], str]]:
    keys: list[tuple[tuple[str, ...], str]] = [
        (("tenant", str(tenant_id), "auth-failure", "ip", client_ip), "auth-lockout:ip"),
    ]
    normalized_identifier = str(login_identifier or "").strip().lower()
    if normalized_identifier:
        keys.append(
            (("tenant", str(tenant_id), "auth-failure", "login", normalized_identifier), "auth-lockout:login")
        )
    return keys


def _prune_auth_failures(now: float) -> None:
    reset_window = float(get_auth_lockout_reset_window_seconds())
    expired: list[tuple[str, ...]] = []
    for key, state in _auth_failures.items():
        if state.locked_until > now:
            continue
        if state.last_failure_at > 0 and (now - state.last_failure_at) <= reset_window:
            continue
        expired.append(key)
    for key in expired:
        _auth_failures.pop(key, None)


def get_auth_lockout_decision(
    request: Request,
    *,
    tenant_id: int,
    login_identifier: str | None,
) -> RateLimitDecision | None:
    now = time.time()
    client_ip = _extract_client_ip(request)
    with _auth_failure_lock:
        _prune_auth_failures(now)
        strongest: RateLimitDecision | None = None
        for bucket_key, label in _auth_failure_keys(
            tenant_id=int(tenant_id),
            client_ip=client_ip,
            login_identifier=login_identifier,
        ):
            state = _auth_failures.get(bucket_key)
            if state is None or state.locked_until <= now:
                continue
            retry_after = max(1, int(state.locked_until - now + 0.999))
            if strongest is None or retry_after > strongest.retry_after:
                strongest = RateLimitDecision(scope="auth_lockout", retry_after=retry_after, label=label)
        return strongest


def record_auth_failure(
    request: Request,
    *,
    tenant_id: int,
    login_identifier: str | None,
) -> RateLimitDecision | None:
    now = time.time()
    threshold = int(get_auth_lockout_threshold())
    base_seconds = int(get_auth_lockout_base_seconds())
    max_seconds = int(get_auth_lockout_max_seconds())
    reset_window = float(get_auth_lockout_reset_window_seconds())
    client_ip = _extract_client_ip(request)

    strongest: RateLimitDecision | None = None
    with _auth_failure_lock:
        _prune_auth_failures(now)
        for bucket_key, label in _auth_failure_keys(
            tenant_id=int(tenant_id),
            client_ip=client_ip,
            login_identifier=login_identifier,
        ):
            state = _auth_failures.setdefault(bucket_key, _AuthFailureState())
            if state.last_failure_at > 0 and (now - state.last_failure_at) > reset_window:
                state.failures = 0
                state.locked_until = 0.0
            state.failures += 1
            state.last_failure_at = now
            if state.failures < threshold:
                continue
            backoff_seconds = min(max_seconds, base_seconds * (2 ** (state.failures - threshold)))
            state.locked_until = max(state.locked_until, now + backoff_seconds)
            retry_after = max(1, int(state.locked_until - now + 0.999))
            if strongest is None or retry_after > strongest.retry_after:
                strongest = RateLimitDecision(scope="auth_lockout", retry_after=retry_after, label=label)
    return strongest


def clear_auth_failures(
    request: Request,
    *,
    tenant_id: int,
    login_identifier: str | None,
) -> None:
    client_ip = _extract_client_ip(request)
    with _auth_failure_lock:
        for bucket_key, _ in _auth_failure_keys(
            tenant_id=int(tenant_id),
            client_ip=client_ip,
            login_identifier=login_identifier,
        ):
            _auth_failures.pop(bucket_key, None)


def _match_login_path(method: str, path: str) -> bool:
    return (method.upper(), path) in _LOGIN_PATHS


def _match_sensitive_admin_path(method: str, path: str) -> bool:
    normalized_method = method.upper()
    if (normalized_method, path) in _SENSITIVE_ADMIN_PATHS:
        return True
    if normalized_method == "POST" and path == "/api/platform/tenants":
        return True
    if normalized_method in {"POST", "PUT", "PATCH", "DELETE"} and (
        path == "/platform" or path.startswith("/platform/")
    ):
        return True
    if normalized_method == "POST" and path.startswith("/api/admin/ai/providers/") and path.endswith("/validate"):
        return True
    if normalized_method == "PUT" and path.startswith("/api/admin/integrations/ai/"):
        return True
    return False


def _should_apply_general_api_limit(path: str) -> bool:
    if path in _GENERAL_EXEMPT_PATHS:
        return False
    return path.startswith("/api/") or path == "/platform" or path.startswith("/platform/")


def _resolve_traffic_class(method: str, path: str, claims, override: dict[str, object] | None) -> str | None:
    if override is not None:
        override_class = str(override.get("class", "")).strip().lower()
        if override_class in _TRAFFIC_CLASSES:
            return override_class

    if _match_login_path(method, path):
        return "auth"

    if claims is not None and str(getattr(claims, "token_type", "")).strip().lower() == "service":
        return "internal"

    if path.startswith("/api/admin/jobs"):
        return "jobs"

    if not _should_apply_general_api_limit(path):
        return None

    if method in {"GET", "HEAD", "OPTIONS"}:
        return "read"

    if method in {"POST", "PUT", "PATCH", "DELETE"}:
        return "write"

    return "read"


def _match_endpoint_override(method: str, path: str) -> dict[str, object] | None:
    for item in get_rate_limit_endpoint_overrides():
        pattern = str(item.get("path_pattern", "")).strip()
        if not pattern:
            continue
        configured_method = str(item.get("method", "*")).strip().upper() or "*"
        if configured_method not in {"*", method}:
            continue
        if fnmatch(path, pattern):
            return item
    return None


def _get_effective_policy(traffic_class: str, override: dict[str, object] | None) -> tuple[int, int, int, int]:
    window_seconds = int(get_rate_limit_class_window_seconds(traffic_class))
    limit = int(get_rate_limit_class_limit(traffic_class))
    burst_window_seconds = int(get_rate_limit_class_burst_window_seconds(traffic_class))
    burst_limit = int(get_rate_limit_class_burst_limit(traffic_class))

    if override is not None:
        if isinstance(override.get("window_seconds"), int):
            window_seconds = max(1, int(override["window_seconds"]))
        if isinstance(override.get("limit"), int):
            limit = max(0, int(override["limit"]))
        if isinstance(override.get("burst_window_seconds"), int):
            burst_window_seconds = max(1, int(override["burst_window_seconds"]))
        if isinstance(override.get("burst_limit"), int):
            burst_limit = max(0, int(override["burst_limit"]))

    return window_seconds, limit, burst_window_seconds, burst_limit


def _enforce_checks(scope: str, checks: list[LimitCheck]) -> RateLimitDecision | None:
    effective_checks = [item for item in checks if item.limit > 0]
    if not effective_checks:
        return None

    now = time.time()

    redis_client = _get_rate_limit_redis_client()
    if redis_client is not None:
        try:
            return _enforce_checks_redis(redis_client, scope, effective_checks, now)
        except Exception:
            # Fail open to in-memory limiter when Redis path is unavailable.
            pass

    with _limit_lock:
        for item in effective_checks:
            bucket = _limit_events[item.bucket_key]
            _prune(bucket, now, item.window_seconds)
            if len(bucket) >= item.limit:
                retry_after = max(1, int(item.window_seconds - (now - bucket[0]))) if bucket else item.window_seconds
                return RateLimitDecision(scope=scope, retry_after=retry_after, label=item.label)

        for item in effective_checks:
            _limit_events[item.bucket_key].append(now)

    return None


@lru_cache(maxsize=1)
def _get_rate_limit_redis_client():
    redis_url = get_rate_limit_redis_url()
    if not redis_url:
        return None
    try:
        import redis
    except Exception:
        return None
    try:
        client = redis.Redis.from_url(redis_url, decode_responses=True, socket_timeout=1)
        client.ping()
        return client
    except Exception:
        return None


def _rate_limit_redis_key(bucket_key: tuple[str, ...]) -> str:
    safe_segments = [quote(str(item), safe="") for item in bucket_key]
    return f"{_RATE_LIMIT_REDIS_PREFIX}:{':'.join(safe_segments)}"


def _redis_check_and_add(redis_client, *, key: str, now: float, window_seconds: int, limit: int) -> tuple[bool, int]:
    member = f"{now}:{uuid4()}"
    result = redis_client.eval(
        _ATOMIC_ZSET_CHECK_AND_ADD_SCRIPT,
        1,
        key,
        now,
        int(window_seconds),
        int(limit),
        member,
        max(1, int(window_seconds) + 1),
    )
    if not isinstance(result, (list, tuple)) or len(result) < 2:
        return False, max(1, int(window_seconds))
    allowed = int(result[0]) == 1
    retry_after = max(1, int(result[1]))
    return allowed, retry_after


def _enforce_checks_redis(
    redis_client,
    scope: str,
    checks: list[LimitCheck],
    now: float,
) -> RateLimitDecision | None:
    for item in checks:
        key = _rate_limit_redis_key(item.bucket_key)
        allowed, retry_after = _redis_check_and_add(
            redis_client,
            key=key,
            now=now,
            window_seconds=item.window_seconds,
            limit=item.limit,
        )
        if not allowed:
            return RateLimitDecision(scope=scope, retry_after=retry_after, label=item.label)
    return None


def check_request_rate_limit(
    request: Request,
    *,
    actor: str | None = None,
    body: bytes = b"",
) -> RateLimitDecision | None:
    if not is_rate_limit_enabled():
        return None

    method = request.method.upper()
    path = request.url.path
    client_ip = _extract_client_ip(request)
    claims = _resolve_claims_for_rate_limit(request)
    tenant_id = _extract_tenant_id(request, claims)
    actor_value = actor
    if not actor_value and claims is not None:
        actor_value = str(getattr(claims, "user_id", "")).strip() or None

    token_type = str(getattr(claims, "token_type", "")).strip().lower() if claims is not None else ""
    if token_type == "service" and is_rate_limit_service_bypass_enabled():
        return None

    override = _match_endpoint_override(method, path)
    traffic_class = _resolve_traffic_class(method, path, claims, override)
    if traffic_class is None:
        return None

    subject = _build_subject(actor=actor_value, client_ip=client_ip)
    checks: list[LimitCheck] = []

    class_window_seconds, class_limit, class_burst_window_seconds, class_burst_limit = _get_effective_policy(
        traffic_class,
        override,
    )
    checks.append(
        LimitCheck(
            bucket_key=("tenant", str(tenant_id), "class", traffic_class, "subject", subject, "window"),
            window_seconds=class_window_seconds,
            limit=class_limit,
            label=f"class:{traffic_class}:window",
        )
    )
    checks.append(
        LimitCheck(
            bucket_key=("tenant", str(tenant_id), "class", traffic_class, "subject", subject, "burst"),
            window_seconds=class_burst_window_seconds,
            limit=class_burst_limit,
            label=f"class:{traffic_class}:burst",
        )
    )

    if _match_login_path(method, path):
        login_identifier = _extract_login_identifier(body)
        login_window = get_rate_limit_login_window_seconds()
        checks.extend(
            [
                LimitCheck(
                    bucket_key=("tenant", str(tenant_id), "auth", "login-ip", path, client_ip),
                    window_seconds=login_window,
                    limit=get_rate_limit_login_ip_limit(),
                    label=f"login-ip:{path}",
                ),
            ]
        )
        if login_identifier:
            checks.append(
                LimitCheck(
                    bucket_key=("tenant", str(tenant_id), "auth", "login-identifier", path, login_identifier),
                    window_seconds=login_window,
                    limit=get_rate_limit_login_identifier_limit(),
                    label=f"login-identifier:{path}",
                )
            )

        return _enforce_checks("auth_login", checks)

    if _match_sensitive_admin_path(method, path):
        sensitive_window = get_rate_limit_sensitive_admin_window_seconds()
        key_kind = "actor" if actor_value else "ip"
        sensitive_subject = _build_subject(actor=actor_value, client_ip=client_ip)
        checks.append(
            LimitCheck(
                bucket_key=("tenant", str(tenant_id), "sensitive-admin", path, key_kind, sensitive_subject),
                window_seconds=sensitive_window,
                limit=get_rate_limit_sensitive_admin_limit(),
                label=f"sensitive-admin:{key_kind}:{path}",
            )
        )
        return _enforce_checks("sensitive_admin", checks)

    return _enforce_checks(f"traffic_{traffic_class}", checks)


def should_audit_rate_limit(path: str) -> bool:
    return (
        path.startswith("/api/auth/")
        or path.startswith("/api/admin/")
        or path.startswith("/api/platform/")
        or path == "/platform"
        or path.startswith("/platform/")
    )


def get_rate_limit_audit_metadata(
    request: Request,
    decision: RateLimitDecision,
    *,
    actor: str | None = None,
) -> dict[str, Any]:
    return {
        "scope": decision.scope,
        "retry_after": decision.retry_after,
        "label": decision.label,
        "method": request.method.upper(),
        "path": request.url.path,
        "actor": actor or "anonymous",
        "client_ip": _extract_client_ip(request),
    }