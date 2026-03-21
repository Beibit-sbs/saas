from __future__ import annotations

import json
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from functools import lru_cache
from threading import Lock
from typing import Any
from uuid import uuid4

from fastapi import Request

from app.core.config import (
    get_rate_limit_general_limit,
    get_rate_limit_general_window_seconds,
    get_rate_limit_login_identifier_limit,
    get_rate_limit_login_ip_limit,
    get_rate_limit_login_window_seconds,
    get_rate_limit_redis_url,
    get_rate_limit_sensitive_admin_limit,
    get_rate_limit_sensitive_admin_window_seconds,
    is_rate_limit_enabled,
)


@dataclass(frozen=True)
class LimitCheck:
    bucket_key: tuple[str, ...]
    limit: int
    label: str


@dataclass(frozen=True)
class RateLimitDecision:
    scope: str
    retry_after: int
    label: str


_limit_lock = Lock()
_limit_events: dict[tuple[str, ...], deque[float]] = defaultdict(deque)

_LOGIN_PATHS = {
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/demo-login"),
    ("POST", "/api/auth/mock-login"),
    ("POST", "/api/auth/ldap-login"),
}
_SENSITIVE_ADMIN_PATHS = {
    ("POST", "/api/admin/ldap/test-connection"),
    ("PUT", "/api/admin/integrations/ldap"),
    ("POST", "/api/admin/backups/run"),
    ("POST", "/api/admin/backups/restore"),
    ("POST", "/api/admin/backups/retention/apply"),
}
_GENERAL_EXEMPT_PATHS = {"/health", "/api/health", "/metrics"}


def clear_rate_limit_state() -> None:
    with _limit_lock:
        _limit_events.clear()
    redis_client = _get_rate_limit_redis_client()
    if redis_client is not None:
        try:
            for key in redis_client.scan_iter("rate_limit:*"):
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


def _match_login_path(method: str, path: str) -> bool:
    return (method.upper(), path) in _LOGIN_PATHS


def _match_sensitive_admin_path(method: str, path: str) -> bool:
    normalized_method = method.upper()
    if (normalized_method, path) in _SENSITIVE_ADMIN_PATHS:
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


def _enforce_checks(scope: str, checks: list[LimitCheck], window_seconds: int) -> RateLimitDecision | None:
    if window_seconds <= 0:
        return None
    effective_checks = [item for item in checks if item.limit > 0]
    if not effective_checks:
        return None

    now = time.time()

    redis_client = _get_rate_limit_redis_client()
    if redis_client is not None:
        try:
            return _enforce_checks_redis(redis_client, scope, effective_checks, window_seconds, now)
        except Exception:
            # Fail open to in-memory limiter when Redis path is unavailable.
            pass

    with _limit_lock:
        for item in effective_checks:
            bucket = _limit_events[item.bucket_key]
            _prune(bucket, now, window_seconds)
            if len(bucket) >= item.limit:
                retry_after = max(1, int(window_seconds - (now - bucket[0]))) if bucket else window_seconds
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
    route = bucket_key[1] if len(bucket_key) > 1 else "global"
    subject = bucket_key[-1] if bucket_key else "unknown"
    return f"rate_limit:{subject}:{route}"


def _enforce_checks_redis(
    redis_client,
    scope: str,
    checks: list[LimitCheck],
    window_seconds: int,
    now: float,
) -> RateLimitDecision | None:
    cutoff = now - window_seconds
    for item in checks:
        key = _rate_limit_redis_key(item.bucket_key)
        redis_client.zremrangebyscore(key, 0, cutoff)
        current_count = redis_client.zcard(key)
        if int(current_count) >= item.limit:
            oldest = redis_client.zrange(key, 0, 0, withscores=True)
            if oldest:
                oldest_ts = float(oldest[0][1])
                retry_after = max(1, int(window_seconds - (now - oldest_ts)))
            else:
                retry_after = window_seconds
            return RateLimitDecision(scope=scope, retry_after=retry_after, label=item.label)

    member = f"{now}:{uuid4()}"
    for item in checks:
        key = _rate_limit_redis_key(item.bucket_key)
        redis_client.zadd(key, {member: now})
        redis_client.expire(key, max(1, window_seconds + 1))
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

    if _match_login_path(method, path):
        login_identifier = _extract_login_identifier(body)
        checks = [
            LimitCheck(
                bucket_key=("login-ip", path, client_ip),
                limit=get_rate_limit_login_ip_limit(),
                label=f"login-ip:{path}",
            ),
        ]
        if login_identifier:
            checks.append(
                LimitCheck(
                    bucket_key=("login-identifier", path, login_identifier),
                    limit=get_rate_limit_login_identifier_limit(),
                    label=f"login-identifier:{path}",
                )
            )
        return _enforce_checks("auth_login", checks, get_rate_limit_login_window_seconds())

    if _match_sensitive_admin_path(method, path):
        subject = (actor or client_ip).strip().lower() or "unknown"
        key_kind = "actor" if actor else "ip"
        checks = [
            LimitCheck(
                bucket_key=("sensitive-admin", path, key_kind, subject),
                limit=get_rate_limit_sensitive_admin_limit(),
                label=f"sensitive-admin:{key_kind}:{path}",
            )
        ]
        return _enforce_checks("sensitive_admin", checks, get_rate_limit_sensitive_admin_window_seconds())

    if _should_apply_general_api_limit(path):
        checks = [
            LimitCheck(
                bucket_key=("general-api", client_ip),
                limit=get_rate_limit_general_limit(),
                label="general-api:ip",
            )
        ]
        return _enforce_checks("api_general", checks, get_rate_limit_general_window_seconds())

    return None


def should_audit_rate_limit(path: str) -> bool:
    return (
        path.startswith("/api/auth/")
        or path.startswith("/api/admin/")
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