from __future__ import annotations

import json
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock
from typing import Any

from fastapi import Request

from app.core.config import (
    get_rate_limit_general_limit,
    get_rate_limit_general_window_seconds,
    get_rate_limit_login_identifier_limit,
    get_rate_limit_login_ip_limit,
    get_rate_limit_login_window_seconds,
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


def _prune(bucket: deque[float], now: float, window_seconds: int) -> None:
    cutoff = now - window_seconds
    while bucket and bucket[0] <= cutoff:
        bucket.popleft()


def _extract_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for.strip():
        return forwarded_for.split(",")[0].strip() or "unknown"
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
    if normalized_method == "POST" and path.startswith("/api/admin/ai/providers/") and path.endswith("/validate"):
        return True
    if normalized_method == "PUT" and path.startswith("/api/admin/integrations/ai/"):
        return True
    return False


def _should_apply_general_api_limit(path: str) -> bool:
    return path.startswith("/api/") and path not in _GENERAL_EXEMPT_PATHS


def _enforce_checks(scope: str, checks: list[LimitCheck], window_seconds: int) -> RateLimitDecision | None:
    if window_seconds <= 0:
        return None
    effective_checks = [item for item in checks if item.limit > 0]
    if not effective_checks:
        return None

    now = time.time()
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
    return path.startswith("/api/auth/") or path.startswith("/api/admin/")


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