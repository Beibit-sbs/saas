"""Phase LV — SSO SAML 2.0 service."""
from __future__ import annotations

import secrets
import urllib.parse
from dataclasses import dataclass

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher

IDP_STATUSES = {"active", "inactive", "error"}
SESSION_STATUSES = {"initiated", "authenticated", "expired", "revoked"}
BINDING_TYPES = {"post", "redirect"}


class SSOError(Exception):
    """Raised on invalid SSO SAML service input."""


@dataclass
class SAMLIdentityProvider:
    idp_id: int
    tenant_id: int
    entity_id: str
    sso_url: str
    status: str


@dataclass
class SAMLSession:
    session_id: int
    tenant_id: int
    user_id: int | None
    idp_id: int
    status: str
    relay_state: str


@dataclass
class SAMLAttributeMapping:
    mapping_id: int
    tenant_id: int
    idp_id: int
    saml_attribute: str
    local_field: str


# ---------------------------------------------------------------------------
# Identity Provider management
# ---------------------------------------------------------------------------


def register_idp(
    *,
    entity_id: str,
    sso_url: str,
    slo_url: str,
    certificate: str,
    binding: str,
    tenant_id: int,
) -> SAMLIdentityProvider:
    """Register a SAML 2.0 Identity Provider."""
    if not entity_id or not entity_id.strip():
        raise SSOError("entity_id is required")
    if not sso_url or not sso_url.strip():
        raise SSOError("sso_url is required")
    if binding not in BINDING_TYPES:
        raise SSOError(f"invalid binding: {binding!r}; must be one of {BINDING_TYPES}")
    if not certificate or not certificate.strip():
        raise SSOError("certificate is required")

    record = create_entity_for_tenant(
        "saml_identity_providers",
        {
            "entity_id": entity_id.strip(),
            "sso_url": sso_url.strip(),
            "slo_url": slo_url.strip() if slo_url else "",
            "certificate": certificate.strip(),
            "binding": binding,
            "status": "active",
        },
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="sso.idp_registered",
            payload={"idp_id": record["id"], "entity_id": entity_id},
        )
    except Exception:
        pass

    return SAMLIdentityProvider(
        idp_id=record["id"],
        tenant_id=tenant_id,
        entity_id=entity_id,
        sso_url=sso_url,
        status="active",
    )


def deactivate_idp(*, idp_id: int, tenant_id: int) -> SAMLIdentityProvider:
    """Deactivate an Identity Provider."""
    providers = list_entities_for_tenant("saml_identity_providers", tenant_id)
    matched = [p for p in providers if p["id"] == idp_id]
    if not matched:
        raise SSOError(f"IdP {idp_id} not found")

    idp = matched[0]
    if idp["status"] == "inactive":
        raise SSOError("IdP is already inactive")

    update_entity_for_tenant(
        "saml_identity_providers", idp_id, {"status": "inactive"}, tenant_id
    )

    return SAMLIdentityProvider(
        idp_id=idp_id,
        tenant_id=tenant_id,
        entity_id=idp["entity_id"],
        sso_url=idp["sso_url"],
        status="inactive",
    )


def reactivate_idp(*, idp_id: int, tenant_id: int) -> SAMLIdentityProvider:
    """Reactivate a previously deactivated IdP."""
    providers = list_entities_for_tenant("saml_identity_providers", tenant_id)
    matched = [p for p in providers if p["id"] == idp_id]
    if not matched:
        raise SSOError(f"IdP {idp_id} not found")

    idp = matched[0]
    if idp["status"] == "active":
        raise SSOError("IdP is already active")

    update_entity_for_tenant(
        "saml_identity_providers", idp_id, {"status": "active"}, tenant_id
    )

    return SAMLIdentityProvider(
        idp_id=idp_id,
        tenant_id=tenant_id,
        entity_id=idp["entity_id"],
        sso_url=idp["sso_url"],
        status="active",
    )


def list_idps(*, tenant_id: int) -> list[SAMLIdentityProvider]:
    """List all IdPs for a tenant."""
    rows = list_entities_for_tenant("saml_identity_providers", tenant_id)
    return [
        SAMLIdentityProvider(
            idp_id=r["id"],
            tenant_id=tenant_id,
            entity_id=r["entity_id"],
            sso_url=r["sso_url"],
            status=r["status"],
        )
        for r in rows
    ]


# ---------------------------------------------------------------------------
# SSO Sessions
# ---------------------------------------------------------------------------


def initiate_sso(*, idp_id: int, relay_state: str, tenant_id: int) -> SAMLSession:
    """Initiate an SSO login flow — generate AuthnRequest."""
    providers = list_entities_for_tenant("saml_identity_providers", tenant_id)
    matched = [p for p in providers if p["id"] == idp_id]
    if not matched:
        raise SSOError(f"IdP {idp_id} not found")

    idp = matched[0]
    if idp["status"] != "active":
        raise SSOError(f"IdP {idp_id} is not active")

    # Generate a random SAML request ID
    request_id = secrets.token_hex(16)

    record = create_entity_for_tenant(
        "saml_sessions",
        {
            "idp_id": idp_id,
            "user_id": None,
            "status": "initiated",
            "relay_state": relay_state or "",
            "request_id": request_id,
        },
        tenant_id,
    )

    return SAMLSession(
        session_id=record["id"],
        tenant_id=tenant_id,
        user_id=None,
        idp_id=idp_id,
        status="initiated",
        relay_state=relay_state or "",
    )


def process_saml_response(
    *,
    session_id: int,
    user_id: int,
    name_id: str,
    attributes: dict,
    tenant_id: int,
) -> SAMLSession:
    """Process incoming SAML Response — authenticate the user."""
    if not user_id or user_id <= 0:
        raise SSOError("user_id is required")
    if not name_id or not name_id.strip():
        raise SSOError("name_id is required")

    sessions = list_entities_for_tenant("saml_sessions", tenant_id)
    matched = [s for s in sessions if s["id"] == session_id]
    if not matched:
        raise SSOError(f"session {session_id} not found")

    session = matched[0]
    if session["status"] != "initiated":
        raise SSOError(
            f"session is in status {session['status']!r}; expected 'initiated'"
        )

    update_entity_for_tenant(
        "saml_sessions",
        session_id,
        {"user_id": user_id, "status": "authenticated", "name_id": name_id},
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="sso.login_success",
            payload={"user_id": user_id, "idp_id": session["idp_id"], "name_id": name_id},
        )
    except Exception:
        pass

    return SAMLSession(
        session_id=session_id,
        tenant_id=tenant_id,
        user_id=user_id,
        idp_id=session["idp_id"],
        status="authenticated",
        relay_state=session.get("relay_state", ""),
    )


def logout_sso(*, session_id: int, tenant_id: int) -> SAMLSession:
    """Perform SAML Single Logout."""
    sessions = list_entities_for_tenant("saml_sessions", tenant_id)
    matched = [s for s in sessions if s["id"] == session_id]
    if not matched:
        raise SSOError(f"session {session_id} not found")

    session = matched[0]
    if session["status"] not in ("authenticated",):
        raise SSOError(
            f"only authenticated sessions can be logged out; current: {session['status']!r}"
        )

    update_entity_for_tenant(
        "saml_sessions", session_id, {"status": "revoked"}, tenant_id
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="sso.logout",
            payload={"user_id": session.get("user_id"), "session_id": session_id},
        )
    except Exception:
        pass

    return SAMLSession(
        session_id=session_id,
        tenant_id=tenant_id,
        user_id=session.get("user_id"),
        idp_id=session["idp_id"],
        status="revoked",
        relay_state=session.get("relay_state", ""),
    )


def expire_session(*, session_id: int, tenant_id: int) -> SAMLSession:
    """Expire a stale initiated session (TTL enforcement)."""
    sessions = list_entities_for_tenant("saml_sessions", tenant_id)
    matched = [s for s in sessions if s["id"] == session_id]
    if not matched:
        raise SSOError(f"session {session_id} not found")

    session = matched[0]
    if session["status"] not in ("initiated", "authenticated"):
        raise SSOError(
            f"session cannot be expired from status {session['status']!r}"
        )

    update_entity_for_tenant(
        "saml_sessions", session_id, {"status": "expired"}, tenant_id
    )

    return SAMLSession(
        session_id=session_id,
        tenant_id=tenant_id,
        user_id=session.get("user_id"),
        idp_id=session["idp_id"],
        status="expired",
        relay_state=session.get("relay_state", ""),
    )


# ---------------------------------------------------------------------------
# Attribute Mappings
# ---------------------------------------------------------------------------


def add_attribute_mapping(
    *,
    idp_id: int,
    saml_attribute: str,
    local_field: str,
    tenant_id: int,
) -> SAMLAttributeMapping:
    """Map a SAML attribute to a local user field."""
    if not saml_attribute or not saml_attribute.strip():
        raise SSOError("saml_attribute is required")
    if not local_field or not local_field.strip():
        raise SSOError("local_field is required")

    record = create_entity_for_tenant(
        "saml_attribute_mappings",
        {
            "idp_id": idp_id,
            "saml_attribute": saml_attribute.strip(),
            "local_field": local_field.strip(),
        },
        tenant_id,
    )

    return SAMLAttributeMapping(
        mapping_id=record["id"],
        tenant_id=tenant_id,
        idp_id=idp_id,
        saml_attribute=saml_attribute,
        local_field=local_field,
    )


def list_attribute_mappings(*, idp_id: int, tenant_id: int) -> list[SAMLAttributeMapping]:
    """List attribute mappings for a given IdP."""
    rows = list_entities_for_tenant("saml_attribute_mappings", tenant_id)
    return [
        SAMLAttributeMapping(
            mapping_id=r["id"],
            tenant_id=tenant_id,
            idp_id=r["idp_id"],
            saml_attribute=r["saml_attribute"],
            local_field=r["local_field"],
        )
        for r in rows
        if r.get("idp_id") == idp_id
    ]
