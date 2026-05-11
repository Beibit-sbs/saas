"""A-023.6 — Developer Portal service skeleton (L2)."""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


PORTAL_STATES: frozenset[str] = frozenset({"DRAFT", "ACTIVE", "MAINTENANCE", "RETIRED"})
SAFETY_GUARDS: frozenset[str] = frozenset(
    {
        "NO_FAKE_OBSERVABILITY_ALERTS",
        "NO_FAKE_KPI_DASHBOARD_VALUES",
        "NO_AUTONOMOUS_EXECUTION",
        "NO_EXTERNAL_PROVIDER_REGISTRATION",
    }
)


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def register_portal_channel(
    tenant_id: int,
    *,
    channel_name: str,
    audience: str,
    governance_note: str,
) -> dict:
    """Register developer portal channel metadata in DRAFT state."""
    _validate_tenant(tenant_id)
    if not channel_name:
        raise ValueError("channel_name is required")
    if not audience:
        raise ValueError("audience is required")
    if not governance_note:
        raise ValueError("governance_note is required")

    row = create_entity_for_tenant(
        tenant_id,
        "developer_portal_channels",
        {
            "channel_name": channel_name,
            "audience": audience,
            "governance_note": governance_note,
            "status": "DRAFT",
            "tenant_id": tenant_id,
        },
    )
    return {"channel_id": row["id"], "status": "DRAFT"}


def list_portal_channels(tenant_id: int, *, status: str | None = None) -> list[dict]:
    """List tenant-scoped developer portal channels."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "developer_portal_channels")
    if status:
        rows = [row for row in rows if row.get("status") == status]
    return rows


def evaluate_developer_portal_readiness(
    tenant_id: int,
    portal_payload: dict | None = None,
) -> dict:
    """Return deterministic L3 readiness classification for developer portal enablement."""
    _validate_tenant(tenant_id)
    payload = portal_payload or {}

    required_evidence = [
        "channel_id",
        "api_access_scope",
        "security_review_context",
        "governance_owner",
    ]
    missing_evidence = [key for key in required_evidence if not payload.get(key)]

    api_access_gap = bool(payload.get("api_access_evidence_missing"))
    security_review_required = bool(payload.get("security_review_required"))

    if missing_evidence:
        classification = "DEVELOPER_PORTAL_INPUT_INCOMPLETE"
        evaluation_status = "INCOMPLETE"
        readiness_level = "PENDING"
        risk_level = "MEDIUM"
        next_step = "collect_missing_developer_portal_evidence"
        rationale = "Developer portal enablement evidence is incomplete."
    elif api_access_gap:
        classification = "API_ACCESS_EVIDENCE_REQUIRED"
        evaluation_status = "REVIEW_REQUIRED"
        readiness_level = "PENDING"
        risk_level = "HIGH"
        next_step = "request_api_access_evidence_for_manual_review"
        rationale = "API access evidence is required before enablement review."
    elif security_review_required:
        classification = "SECURITY_REVIEW_REQUIRED"
        evaluation_status = "REVIEW_REQUIRED"
        readiness_level = "PENDING"
        risk_level = "HIGH"
        next_step = "route_portal_request_to_manual_security_review"
        rationale = "Security review must complete before portal enablement."
    elif payload.get("enablement_ready"):
        classification = "READY_FOR_MANUAL_DEVELOPER_ENABLEMENT"
        evaluation_status = "READY"
        readiness_level = "READY"
        risk_level = "LOW"
        next_step = "route_for_manual_developer_enablement"
        rationale = "Evidence is complete for bounded human enablement."
    else:
        classification = "READY_FOR_ONBOARDING_REVIEW"
        evaluation_status = "READY"
        readiness_level = "READY"
        risk_level = "LOW"
        next_step = "start_manual_onboarding_review"
        rationale = "Portal onboarding evidence supports manual review."

    return {
        "tenant_id": tenant_id,
        "module": "developer_portal",
        "maturity_level": "L3",
        "evaluation_status": evaluation_status,
        "classification": classification,
        "readiness_level": readiness_level,
        "risk_level": risk_level,
        "required_evidence": required_evidence,
        "missing_evidence": missing_evidence,
        "allowed_actions": [
            "REVIEW_PROFILE",
            "REQUEST_EVIDENCE",
            "ESCALATE_REVIEW",
        ],
        "forbidden_actions": [
            "AUTO_GRANT_API_ACCESS",
            "AUTO_CREATE_PRODUCTION_TOKEN",
            "AUTO_BYPASS_SECURITY_REVIEW",
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
