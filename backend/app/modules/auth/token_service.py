import base64
import binascii
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Optional

from fastapi import Request

from app.core.config import get_auth_access_token_ttl_minutes, get_auth_cookie_name


@dataclass(frozen=True)
class AccessTokenClaims:
    user_id: str
    roles: list[str]
    auth_source: str
    issued_at: int
    expires_at: int


class TokenValidationError(ValueError):
    pass


def _signing_secret() -> bytes:
    return os.getenv("JWT_SECRET", "change_me_jwt_secret").encode("utf-8")


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


def create_access_token(user_id: str, roles: list[str], auth_source: str) -> str:
    now = int(time.time())
    ttl_seconds = get_auth_access_token_ttl_minutes() * 60

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "roles": roles,
        "src": auth_source,
        "iat": now,
        "exp": now + ttl_seconds,
        "token_type": "access",
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


def verify_access_token(token: str) -> AccessTokenClaims:
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
    if token_type != "access":
        raise TokenValidationError("invalid token type")

    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub.strip():
        raise TokenValidationError("invalid token subject")

    roles_raw = payload.get("roles")
    if not isinstance(roles_raw, list):
        raise TokenValidationError("invalid token roles")
    roles = [str(role).strip() for role in roles_raw if str(role).strip()]

    src = payload.get("src")
    auth_source = str(src).strip() if isinstance(src, str) else "unknown"

    iat = payload.get("iat")
    exp = payload.get("exp")
    if not isinstance(iat, int) or not isinstance(exp, int):
        raise TokenValidationError("invalid token timestamps")

    now = int(time.time())
    if exp <= now:
        raise TokenValidationError("token expired")

    return AccessTokenClaims(
        user_id=sub,
        roles=roles,
        auth_source=auth_source,
        issued_at=iat,
        expires_at=exp,
    )
