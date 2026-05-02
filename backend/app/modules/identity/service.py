from __future__ import annotations

import base64
import json
import secrets
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any
from urllib.parse import urlencode

import httpx
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_der_public_key
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPublicNumbers,
)
from cryptography.hazmat.backends import default_backend

from app.modules.integrations.service import get_setting, save_setting
from app.modules.security.url_validation import validate_external_https_url


_IDP_CONFIG_KEY = "identity.providers_json"


@dataclass
class OidcExternalIdentity:
    subject: str
    email: str | None = None
    display_name: str | None = None


_state_lock = Lock()
_oidc_states: dict[str, dict[str, Any]] = {}


def _load_provider_rows(*, tenant_id: int) -> list[dict[str, Any]]:
    entry = get_setting(_IDP_CONFIG_KEY, tenant_id=tenant_id)
    if entry is None or not entry.value:
        return []
    try:
        payload = json.loads(entry.value)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    result: list[dict[str, Any]] = []
    for item in payload:
        if isinstance(item, dict):
            result.append(dict(item))
    return result


def _save_provider_rows(*, tenant_id: int, rows: list[dict[str, Any]]) -> None:
    save_setting(_IDP_CONFIG_KEY, json.dumps(rows), is_secret=True, tenant_id=tenant_id)


def list_identity_providers(*, tenant_id: int) -> list[dict[str, Any]]:
    return _load_provider_rows(tenant_id=tenant_id)


def upsert_identity_provider(*, tenant_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    provider = str(payload.get("provider", "")).strip().lower()
    provider_type = str(payload.get("type", "")).strip().lower()
    if provider_type not in {"oidc", "saml"}:
        raise ValueError("identity provider type must be oidc or saml")
    if not provider:
        raise ValueError("provider is required")

    row = {
        "provider": provider,
        "type": provider_type,
        "enabled": bool(payload.get("enabled", True)),
        "issuer": str(payload.get("issuer", "")).strip(),
        "client_id": str(payload.get("client_id", "")).strip(),
        "client_secret": str(payload.get("client_secret", "")).strip(),
        "redirect_uri": str(payload.get("redirect_uri", "")).strip(),
        "scopes": [str(item).strip() for item in payload.get("scopes", []) if str(item).strip()],
        # SAML-ready shape
        "saml_metadata_url": str(payload.get("saml_metadata_url", "")).strip(),
        "saml_sso_url": str(payload.get("saml_sso_url", "")).strip(),
        "saml_entity_id": str(payload.get("saml_entity_id", "")).strip(),
        "tenant_scope": str(payload.get("tenant_scope", "tenant")).strip().lower() or "tenant",
    }

    if provider_type == "oidc" and row["issuer"]:
        row["issuer"] = validate_external_https_url(row["issuer"]).rstrip("/")

    rows = _load_provider_rows(tenant_id=tenant_id)
    replaced = False
    for index, existing in enumerate(rows):
        if str(existing.get("provider", "")).strip().lower() == provider:
            rows[index] = row
            replaced = True
            break
    if not replaced:
        rows.append(row)
    _save_provider_rows(tenant_id=tenant_id, rows=rows)
    return row


def get_provider(*, tenant_id: int, provider: str) -> dict[str, Any] | None:
    normalized_provider = str(provider).strip().lower()
    if not normalized_provider:
        return None
    rows = _load_provider_rows(tenant_id=tenant_id)
    for item in rows:
        if str(item.get("provider", "")).strip().lower() == normalized_provider:
            return item
    return None


def create_oidc_login_challenge(*, tenant_id: int, provider: str) -> dict[str, Any]:
    config = get_provider(tenant_id=tenant_id, provider=provider)
    if config is None:
        raise ValueError("identity provider not found")
    if str(config.get("type", "")).strip().lower() != "oidc":
        raise ValueError("identity provider is not oidc")
    if not bool(config.get("enabled", False)):
        raise ValueError("identity provider is disabled")

    issuer = validate_external_https_url(str(config.get("issuer", "")).strip()).rstrip("/")
    client_id = str(config.get("client_id", "")).strip()
    redirect_uri = str(config.get("redirect_uri", "")).strip()
    scopes = list(config.get("scopes") or ["openid", "profile", "email"])
    if not issuer or not client_id or not redirect_uri:
        raise ValueError("oidc provider configuration is incomplete")

    state = secrets.token_urlsafe(24)
    nonce = secrets.token_urlsafe(24)
    with _state_lock:
        _oidc_states[state] = {
            "tenant_id": int(tenant_id),
            "provider": str(provider).strip().lower(),
            "nonce": nonce,
            "created_at": int(time.time()),
        }

    query = urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "nonce": nonce,
        }
    )
    authorize_url = f"{issuer}/authorize?{query}"
    return {
        "provider": provider,
        "authorize_url": authorize_url,
        "state": state,
        "nonce": nonce,
    }


def consume_oidc_state(*, state: str, max_age_seconds: int = 600) -> dict[str, Any] | None:
    normalized = str(state).strip()
    if not normalized:
        return None
    with _state_lock:
        payload = _oidc_states.pop(normalized, None)
    if payload is None:
        return None
    created_at = int(payload.get("created_at", 0))
    if int(time.time()) - created_at > max_age_seconds:
        return None
    return payload


def _jwk_to_rsa_public_key(jwk: dict[str, Any]) -> RSAPublicKey:
    def _b64url_to_int(val: str) -> int:
        padded = val + "=" * (-len(val) % 4)
        return int.from_bytes(base64.urlsafe_b64decode(padded), "big")

    n = _b64url_to_int(jwk["n"])
    e = _b64url_to_int(jwk["e"])
    return RSAPublicNumbers(e=e, n=n).public_key(default_backend())


def _fetch_jwks(issuer: str) -> list[dict[str, Any]]:
    # Try OIDC discovery first, fall back to direct JWKS endpoint
    discovery_url = f"{issuer}/.well-known/openid-configuration"
    try:
        resp = httpx.get(discovery_url, timeout=10.0, follow_redirects=False)
        resp.raise_for_status()
        jwks_uri = resp.json().get("jwks_uri", "")
    except Exception:
        jwks_uri = f"{issuer}/.well-known/jwks.json"

    if not jwks_uri:
        raise ValueError("could not determine jwks_uri from OIDC discovery")
    jwks_uri = validate_external_https_url(jwks_uri)
    resp = httpx.get(jwks_uri, timeout=10.0, follow_redirects=False)
    resp.raise_for_status()
    return resp.json().get("keys", [])


def _verify_jwt_rs256(token: str, issuer: str, audience: str, nonce: str | None = None) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("invalid JWT structure")

    def _b64_decode(segment: str) -> bytes:
        padded = segment + "=" * (-len(segment) % 4)
        return base64.urlsafe_b64decode(padded)

    header = json.loads(_b64_decode(parts[0]))
    payload = json.loads(_b64_decode(parts[1]))
    signing_input = f"{parts[0]}.{parts[1]}".encode()
    signature = _b64_decode(parts[2])

    alg = header.get("alg", "RS256")
    kid = header.get("kid", "")

    keys = _fetch_jwks(issuer)
    matched: list[dict[str, Any]] = [
        k for k in keys
        if k.get("kty") == "RSA"
        and (not kid or k.get("kid") == kid)
        and k.get("use", "sig") == "sig"
    ]
    if not matched:
        matched = [k for k in keys if k.get("kty") == "RSA"]
    if not matched:
        raise ValueError("no matching RSA key found in JWKS")

    verified = False
    for jwk in matched:
        pub_key = _jwk_to_rsa_public_key(jwk)
        hash_alg: hashes.HashAlgorithm
        if alg in ("RS256",):
            hash_alg = hashes.SHA256()
        elif alg in ("RS384",):
            hash_alg = hashes.SHA384()
        elif alg in ("RS512",):
            hash_alg = hashes.SHA512()
        else:
            raise ValueError(f"unsupported JWT algorithm: {alg}")
        try:
            pub_key.verify(signature, signing_input, padding.PKCS1v15(), hash_alg)
            verified = True
            break
        except InvalidSignature:
            continue

    if not verified:
        raise ValueError("JWT signature verification failed")

    now = int(time.time())
    exp = int(payload.get("exp", 0))
    nbf = int(payload.get("nbf", now))
    iss = str(payload.get("iss", ""))
    aud = payload.get("aud")

    if exp and now > exp:
        raise ValueError("JWT has expired")
    if nbf and now < nbf - 30:
        raise ValueError("JWT not yet valid")
    if iss.rstrip("/") != issuer.rstrip("/"):
        raise ValueError(f"JWT issuer mismatch: {iss!r} != {issuer!r}")

    audiences = [aud] if isinstance(aud, str) else (aud or [])
    if audience not in audiences:
        raise ValueError(f"JWT audience mismatch")

    if nonce and payload.get("nonce") != nonce:
        raise ValueError("JWT nonce mismatch")

    return payload


def exchange_oidc_code_for_identity(*, provider_config: dict[str, Any], code: str, nonce: str | None = None) -> OidcExternalIdentity:
    issuer = validate_external_https_url(str(provider_config.get("issuer", "")).strip()).rstrip("/")
    client_id = str(provider_config.get("client_id", "")).strip()
    client_secret = str(provider_config.get("client_secret", "")).strip()
    redirect_uri = str(provider_config.get("redirect_uri", "")).strip()

    if not issuer or not client_id or not redirect_uri:
        raise ValueError("oidc provider configuration is incomplete")

    token_endpoint = f"{issuer}/token"
    # Prefer token_endpoint from OIDC discovery if available
    try:
        discovery_url = validate_external_https_url(f"{issuer}/.well-known/openid-configuration")
        disc_resp = httpx.get(discovery_url, timeout=10.0, follow_redirects=False)
        if disc_resp.status_code == 200:
            discovered_token_ep = disc_resp.json().get("token_endpoint", "")
            if discovered_token_ep:
                token_endpoint = validate_external_https_url(discovered_token_ep)
    except Exception:
        pass

    resp = httpx.post(
        token_endpoint,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Accept": "application/json"},
        timeout=15.0,
        follow_redirects=False,
    )
    resp.raise_for_status()
    token_response = resp.json()

    id_token = token_response.get("id_token", "")
    if not id_token:
        raise ValueError("no id_token in token response")

    claims = _verify_jwt_rs256(id_token, issuer=issuer, audience=client_id, nonce=nonce)

    subject = str(claims.get("sub", "")).strip()
    if not subject:
        raise ValueError("id_token missing sub claim")

    email: str | None = claims.get("email") or None
    display_name: str | None = (
        claims.get("name")
        or claims.get("preferred_username")
        or claims.get("given_name")
        or None
    )

    return OidcExternalIdentity(subject=subject, email=email, display_name=display_name)
