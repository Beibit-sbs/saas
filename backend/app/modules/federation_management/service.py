"""A-023.3 — Federation Management service skeleton (L2).

Tracks tenant-scoped identity provider metadata and mapping policies only.
"""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


FEDERATION_STATES: frozenset[str] = frozenset({"DRAFT", "ACTIVE", "RETIRED"})


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def register_identity_provider(
    tenant_id: int,
    *,
    provider_name: str,
    protocol: str,
    metadata_url: str,
) -> dict:
    """Register identity provider metadata in DRAFT state."""
    _validate_tenant(tenant_id)
    if not provider_name:
        raise ValueError("provider_name is required")
    if not protocol:
        raise ValueError("protocol is required")
    if not metadata_url:
        raise ValueError("metadata_url is required")

    row = create_entity_for_tenant(
        tenant_id,
        "federation_identity_providers",
        {
            "provider_name": provider_name,
            "protocol": protocol,
            "metadata_url": metadata_url,
            "status": "DRAFT",
            "tenant_id": tenant_id,
        },
    )
    return {"provider_id": row["id"], "status": "DRAFT"}


def set_provider_status(
    tenant_id: int,
    *,
    provider_id: str,
    status: str,
) -> dict:
    """Set provider status with explicit operator intent only."""
    _validate_tenant(tenant_id)
    if status not in FEDERATION_STATES:
        raise ValueError(f"status must be one of {sorted(FEDERATION_STATES)}")

    for row in list_entities_for_tenant(tenant_id, "federation_identity_providers"):
        if row.get("id") == provider_id:
            row["status"] = status
            return {"provider_id": provider_id, "status": status}

    raise ValueError(f"Provider {provider_id!r} not found for tenant {tenant_id}")


def list_identity_providers(
    tenant_id: int,
    *,
    status: str | None = None,
) -> list[dict]:
    """List tenant-scoped identity providers with optional status filter."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "federation_identity_providers")
    if status:
        rows = [row for row in rows if row.get("status") == status]
    return rows


def evaluate_federation_management_readiness(
    tenant_id: int,
    federation_payload: dict | None = None,
) -> dict:
    """Return deterministic L3 readiness classification for federation trust workflows."""
    _validate_tenant(tenant_id)
    payload = federation_payload or {}

    required_evidence = [
        "trust_link_id",
        "partner_org_context",
        "protocol_context",
        "security_review_context",
    ]
    missing_evidence = [key for key in required_evidence if not payload.get(key)]

    protocol_mismatch = bool(payload.get("protocol_mismatch"))
    security_gap = bool(payload.get("security_evidence_gap"))

    if missing_evidence:
        classification = "FEDERATION_INPUT_INCOMPLETE"
        evaluation_status = "INCOMPLETE"
        readiness_level = "PENDING"
        risk_level = "MEDIUM"
        next_step = "collect_missing_federation_evidence"
        rationale = "Federation trust evidence is incomplete."
    elif protocol_mismatch:
        classification = "FEDERATION_PROTOCOL_REVIEW_REQUIRED"
        evaluation_status = "REVIEW_REQUIRED"
        readiness_level = "PENDING"
        risk_level = "HIGH"
        next_step = "route_protocol_mismatch_for_manual_review"
        rationale = "Protocol mismatch requires human federation review."
    elif security_gap:
        classification = "FEDERATION_SECURITY_EVIDENCE_REQUIRED"
        evaluation_status = "REVIEW_REQUIRED"
        readiness_level = "PENDING"
        risk_level = "HIGH"
        next_step = "collect_security_evidence_before_approval"
        rationale = "Security evidence gap blocks trust-link approval."
    elif payload.get("manual_approval_ready"):
        classification = "READY_FOR_MANUAL_FEDERATION_APPROVAL"
        evaluation_status = "READY"
        readiness_level = "READY"
        risk_level = "LOW"
        next_step = "submit_trust_link_for_manual_approval"
        rationale = "Trust-link package is complete for human approval."
    else:
        classification = "READY_FOR_FEDERATION_REVIEW"
        evaluation_status = "READY"
        readiness_level = "READY"
        risk_level = "LOW"
        next_step = "start_manual_federation_review"
        rationale = "Federation evidence is sufficient for deterministic review."

    return {
        "tenant_id": tenant_id,
        "module": "federation_management",
        "maturity_level": "L3",
        "evaluation_status": evaluation_status,
        "classification": classification,
        "readiness_level": readiness_level,
        "risk_level": risk_level,
        "required_evidence": required_evidence,
        "missing_evidence": missing_evidence,
        "allowed_actions": [
            "REVIEW_TRUST_LINK",
            "REQUEST_EVIDENCE",
            "ESCALATE_REVIEW",
        ],
        "forbidden_actions": [
            "AUTO_ENABLE_FEDERATION",
            "AUTO_GRANT_TRUST",
            "AUTO_SYNC_CROSS_TENANT_ACCESS",
        ],
        "human_review_required": True,
        "next_recommended_step": next_step,
        "rationale_notes": rationale,
        "safety_flags": {
            "tenant_scoped": True,
            "deterministic": True,
            "no_api_claim": True,
            "no_frontend_claim": True,
            "no_kpi_claim": True,
            "no_brain_claim": True,
            "no_autonomous_execution": True,
            "no_external_provider_call": True,
            "no_l4_claim": True,
            "no_l5_claim": True,
            "no_l6_claim": True,
        },
    }
