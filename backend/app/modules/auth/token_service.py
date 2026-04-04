import base64
import binascii
import hashlib
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional
from uuid import uuid4

_logger = logging.getLogger(__name__)

from fastapi import Request

from app.core.config import (
    get_auth_access_token_ttl_minutes,
    get_auth_cookie_name,
    get_auth_refresh_cookie_name,
    get_auth_refresh_token_ttl_minutes,
    get_auth_revocation_redis_url,
)


@dataclass(frozen=True)
class AccessTokenClaims:
    user_id: str
    roles: list[str]
    permissions: list[str]
    auth_source: str
    tenant_id: int
    jti: str
    token_type: str
    session_id: str | None
    platform_global: bool
    issued_at: int
    expires_at: int


@dataclass(frozen=True)
class RefreshTokenClaims:
    user_id: str
    roles: list[str]
    auth_source: str
    tenant_id: int
    jti: str
    session_id: str
    issued_at: int
    expires_at: int


class TokenValidationError(ValueError):
    pass


_revoked_tokens_memory: dict[str, int] = {}


def _prune_revoked_tokens_memory(now: int | None = None) -> None:
    current = int(time.time()) if now is None else now
    expired = [jti for jti, exp in _revoked_tokens_memory.items() if exp <= current]
    for jti in expired:
        _revoked_tokens_memory.pop(jti, None)


@lru_cache(maxsize=1)
def _get_redis_client():
    redis_url = get_auth_revocation_redis_url()
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


def _revoked_token_key(jti: str) -> str:
    return f"auth:revoked:{jti}"


def revoke_token(jti: str, *, expires_at: int | None = None) -> None:
    normalized_jti = str(jti).strip()
    if not normalized_jti:
        return

    now = int(time.time())
    effective_expires_at = expires_at if isinstance(expires_at, int) else now + (24 * 60 * 60)
    ttl_seconds = max(1, effective_expires_at - now)

    client = _get_redis_client()
    if client is not None:
        try:
            client.setex(_revoked_token_key(normalized_jti), ttl_seconds, "1")
            return
        except Exception:
            pass

    _prune_revoked_tokens_memory(now)
    _revoked_tokens_memory[normalized_jti] = effective_expires_at


def is_token_revoked(jti: str) -> bool:
    normalized_jti = str(jti).strip()
    if not normalized_jti:
        return False

    client = _get_redis_client()
    if client is not None:
        try:
            return bool(client.exists(_revoked_token_key(normalized_jti)))
        except Exception:
            # Redis is configured but unreachable: fail-closed to prevent accepting
            # tokens that were revoked in Redis but absent from the in-memory store.
            _logger.warning(
                "token_revocation_redis_unavailable: treating token as revoked (fail-closed)",
                extra={"jti": normalized_jti},
            )
            return True

    _prune_revoked_tokens_memory()
    return normalized_jti in _revoked_tokens_memory


def clear_token_revocation_state() -> None:
    _revoked_tokens_memory.clear()
    _get_redis_client.cache_clear()


def _signing_secret() -> bytes:
    raw = os.getenv("JWT_SECRET", "").strip()
    if not raw or raw in {"change_me", "change_me_jwt_secret"}:
        raise RuntimeError("JWT_SECRET must be configured with a strong non-default value")
    return raw.encode("utf-8")


def validate_token_signing_config() -> None:
    _signing_secret()


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * ((4 - len(data) % 4) % 4)
    try:
        return base64.urlsafe_b64decode((data + padding).encode("ascii"))
    except (binascii.Error, ValueError) as exc:
        raise TokenValidationError("invalid token encoding") from exc


def _encode_json(data: dict[str, object]) -> str:
    return _b64url_encode(json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def _decode_json(data: str) -> dict[str, object]:
    try:
        parsed = json.loads(_b64url_decode(data).decode("utf-8"))
    except Exception as exc:  # pragma: no cover - defensive decode guard
        raise TokenValidationError("invalid token payload") from exc
    if not isinstance(parsed, dict):
        raise TokenValidationError("invalid token payload")
    return parsed


def create_access_token(
    user_id: str,
    roles: list[str],
    auth_source: str,
    tenant_id: int,
    *,
    session_id: str | None = None,
    permissions: list[str] | None = None,
) -> str:
    now = int(time.time())
    ttl_seconds = get_auth_access_token_ttl_minutes() * 60
    normalized_tenant_id = int(tenant_id)
    if normalized_tenant_id <= 0:
        raise ValueError("tenant_id must be positive")

    normalized_permissions = sorted({str(item).strip() for item in (permissions or []) if str(item).strip()})

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "roles": roles,
        "scp": normalized_permissions,
        "src": auth_source,
        "tid": normalized_tenant_id,
        "jti": str(uuid4()),
        "pg": False,
        "iat": now,
        "exp": now + ttl_seconds,
        "token_type": "access",
        "ver": 1,
    }
    if session_id and str(session_id).strip():
        payload["sid"] = str(session_id).strip()

    header_b64 = _encode_json(header)
    payload_b64 = _encode_json(payload)
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(_signing_secret(), signing_input, hashlib.sha256).digest()
    signature_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def create_refresh_token(
    user_id: str,
    roles: list[str],
    auth_source: str,
    tenant_id: int,
    *,
    session_id: str,
) -> str:
    now = int(time.time())
    ttl_seconds = get_auth_refresh_token_ttl_minutes() * 60
    normalized_tenant_id = int(tenant_id)
    if normalized_tenant_id <= 0:
        raise ValueError("tenant_id must be positive")

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "roles": roles,
        "src": auth_source,
        "tid": normalized_tenant_id,
        "jti": str(uuid4()),
        "sid": str(session_id).strip(),
        "iat": now,
        "exp": now + ttl_seconds,
        "token_type": "refresh",
        "ver": 1,
    }

    header_b64 = _encode_json(header)
    payload_b64 = _encode_json(payload)
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(_signing_secret(), signing_input, hashlib.sha256).digest()
    signature_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def create_service_token(
    *,
    service_account_id: str,
    permissions: list[str],
    tenant_id: int,
    platform_global: bool = False,
) -> str:
    now = int(time.time())
    ttl_seconds = get_auth_access_token_ttl_minutes() * 60
    normalized_tenant_id = int(tenant_id)
    if normalized_tenant_id <= 0:
        raise ValueError("tenant_id must be positive")
    normalized_permissions = [str(item).strip() for item in permissions if str(item).strip()]
    if not normalized_permissions:
        raise ValueError("service permissions are required")

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(service_account_id).strip(),
        "roles": [],
        "scp": normalized_permissions,
        "src": "service_account",
        "tid": normalized_tenant_id,
        "jti": str(uuid4()),
        "sid": str(uuid4()),
        "pg": bool(platform_global),
        "iat": now,
        "exp": now + ttl_seconds,
        "token_type": "service",
        "ver": 1,
    }

    header_b64 = _encode_json(header)
    payload_b64 = _encode_json(payload)
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(_signing_secret(), signing_input, hashlib.sha256).digest()
    signature_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        return None
    token = authorization[len(prefix) :].strip()
    return token or None


def parse_access_token_from_header(authorization: str | None) -> AccessTokenClaims | None:
    token = _extract_bearer_token(authorization)
    if not token:
        return None
    return verify_access_token(token)


def parse_access_token_from_cookie(request: Request) -> Optional[AccessTokenClaims]:
    token = request.cookies.get(get_auth_cookie_name())
    if not token:
        return None
    return verify_access_token(token)


def parse_access_token_from_request(
    request: Request,
    authorization: str | None,
) -> Optional[AccessTokenClaims]:
    claims = parse_access_token_from_header(authorization)
    if claims is not None:
        return claims
    return parse_access_token_from_cookie(request)


def parse_refresh_token_from_cookie(request: Request) -> Optional[RefreshTokenClaims]:
    token = request.cookies.get(get_auth_refresh_cookie_name())
    if not token:
        return None
    return verify_refresh_token(token)


def verify_access_token(token: str) -> AccessTokenClaims:
    payload = _verify_token_payload(token, expected_token_type={"access", "service"})
    return AccessTokenClaims(
        user_id=payload["user_id"],
        roles=payload["roles"],
        permissions=payload["permissions"],
        auth_source=payload["auth_source"],
        tenant_id=payload["tenant_id"],
        jti=payload["jti"],
        token_type=payload["token_type"],
        session_id=payload["session_id"],
        platform_global=payload["platform_global"],
        issued_at=payload["iat"],
        expires_at=payload["exp"],
    )


def verify_refresh_token(token: str) -> RefreshTokenClaims:
    payload = _verify_token_payload(token, expected_token_type={"refresh"})
    return RefreshTokenClaims(
        user_id=payload["user_id"],
        roles=payload["roles"],
        auth_source=payload["auth_source"],
        tenant_id=payload["tenant_id"],
        jti=payload["jti"],
        session_id=str(payload["session_id"]),
        issued_at=payload["iat"],
        expires_at=payload["exp"],
    )


def _verify_token_payload(token: str, *, expected_token_type: set[str]) -> dict[str, object]:
    parts = token.split(".")
    if len(parts) != 3:
        raise TokenValidationError("invalid token format")

    header_b64, payload_b64, signature_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected = hmac.new(_signing_secret(), signing_input, hashlib.sha256).digest()
    provided = _b64url_decode(signature_b64)
    if not hmac.compare_digest(expected, provided):
        raise TokenValidationError("invalid token signature")

    payload = _decode_json(payload_b64)

    token_type = payload.get("token_type")
    if not isinstance(token_type, str) or token_type not in expected_token_type:
        raise TokenValidationError("invalid token type")

    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub.strip():
        raise TokenValidationError("invalid token subject")

    roles_raw = payload.get("roles")
    if not isinstance(roles_raw, list):
        raise TokenValidationError("invalid token roles")
    roles = [str(role).strip() for role in roles_raw if str(role).strip()]

    permissions_raw = payload.get("scp", [])
    if not isinstance(permissions_raw, list):
        raise TokenValidationError("invalid token scopes")
    permissions = [str(item).strip() for item in permissions_raw if str(item).strip()]

    src = payload.get("src")
    auth_source = str(src).strip() if isinstance(src, str) else "unknown"

    jti_raw = payload.get("jti")
    if not isinstance(jti_raw, str) or not jti_raw.strip():
        raise TokenValidationError("invalid token jti")
    normalized_jti = jti_raw.strip()

    tenant_raw = payload.get("tid")
    if not isinstance(tenant_raw, int) or tenant_raw <= 0:
        raise TokenValidationError("invalid token tenant")

    session_raw = payload.get("sid")
    if session_raw is not None and (not isinstance(session_raw, str) or not session_raw.strip()):
        raise TokenValidationError("invalid token session")
    normalized_session = str(session_raw).strip() if isinstance(session_raw, str) else None

    platform_global_raw = payload.get("pg", False)
    if not isinstance(platform_global_raw, bool):
        raise TokenValidationError("invalid token platform scope")

    iat = payload.get("iat")
    exp = payload.get("exp")
    if not isinstance(iat, int) or not isinstance(exp, int):
        raise TokenValidationError("invalid token timestamps")

    now = int(time.time())
    if exp <= now:
        raise TokenValidationError("token expired")
    if is_token_revoked(normalized_jti):
        from app.modules.observability.security_signals import record_security_signal

        record_security_signal(
            signal="auth.token.revoked_reuse",
            outcome="denied",
            actor=sub,
            tenant_id=tenant_raw,
        )
        raise TokenValidationError("token revoked")
    if normalized_session is not None and token_type != "service":
        try:
            from app.modules.auth.session_service import is_session_active

            if not is_session_active(normalized_session):
                raise TokenValidationError("session revoked")
        except TokenValidationError:
            raise
        except Exception as exc:
            raise TokenValidationError("session store unavailable") from exc

    return {
        "user_id": sub,
        "roles": roles,
        "permissions": permissions,
        "auth_source": auth_source,
        "tenant_id": tenant_raw,
        "jti": normalized_jti,
        "token_type": token_type,
        "session_id": normalized_session,
        "platform_global": platform_global_raw,
        "iat": iat,
        "exp": exp,
    }
