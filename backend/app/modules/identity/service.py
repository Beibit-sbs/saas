from __future__ import annotations

import json
import secrets
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any
from urllib.parse import urlencode

from app.modules.integrations.service import get_setting, save_setting


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

    issuer = str(config.get("issuer", "")).strip().rstrip("/")
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


def exchange_oidc_code_for_identity(*, provider_config: dict[str, Any], code: str) -> OidcExternalIdentity:
    raise NotImplementedError("oidc code exchange is not implemented yet")
