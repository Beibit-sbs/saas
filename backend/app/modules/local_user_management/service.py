"""A-023.3 — Local User Management service skeleton (L2).

Defines tenant-scoped local user profile operations without automatic lockouts.
"""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


ACCOUNT_STATES: frozenset[str] = frozenset({"ACTIVE", "SUSPENDED", "ARCHIVED"})


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def create_local_user(
    tenant_id: int,
    *,
    username: str,
    email: str,
    display_name: str,
) -> dict:
    """Create local user metadata in ACTIVE state."""
    _validate_tenant(tenant_id)
    if not username:
        raise ValueError("username is required")
    if not email:
        raise ValueError("email is required")
    if not display_name:
        raise ValueError("display_name is required")

    row = create_entity_for_tenant(
        tenant_id,
        "local_user_accounts",
        {
            "username": username,
            "email": email,
            "display_name": display_name,
            "status": "ACTIVE",
            "tenant_id": tenant_id,
        },
    )
    return {"user_id": row["id"], "status": "ACTIVE"}


def update_account_status(
    tenant_id: int,
    *,
    user_id: str,
    status: str,
) -> dict:
    """Update account status with explicit, non-automatic transition calls."""
    _validate_tenant(tenant_id)
    if status not in ACCOUNT_STATES:
        raise ValueError(f"status must be one of {sorted(ACCOUNT_STATES)}")

    for row in list_entities_for_tenant(tenant_id, "local_user_accounts"):
        if row.get("id") == user_id:
            row["status"] = status
            return {"user_id": user_id, "status": status}

    raise ValueError(f"Local user {user_id!r} not found for tenant {tenant_id}")


def list_local_users(
    tenant_id: int,
    *,
    status: str | None = None,
) -> list[dict]:
    """List tenant-scoped local users with optional status filter."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "local_user_accounts")
    if status:
        rows = [row for row in rows if row.get("status") == status]
    return rows


def evaluate_local_user_management_readiness(
    tenant_id: int,
    user_payload: dict | None = None,
) -> dict:
    """Return deterministic L3 readiness classification for local user governance."""
    _validate_tenant(tenant_id)
    payload = user_payload or {}

    required_evidence = [
        "user_id",
        "account_status",
        "identity_context",
        "review_context",
    ]
    missing_evidence = [key for key in required_evidence if not payload.get(key)]

    identity_gap = bool(payload.get("identity_evidence_missing"))
    privilege_risk = bool(payload.get("privilege_risk_flag"))

    if missing_evidence:
        classification = "LOCAL_USER_INPUT_INCOMPLETE"
        evaluation_status = "INCOMPLETE"
        readiness_level = "PENDING"
        risk_level = "MEDIUM"
        next_step = "collect_missing_local_user_evidence"
        rationale = "Local user governance evidence is incomplete."
    elif identity_gap:
        classification = "IDENTITY_EVIDENCE_REQUIRED"
        evaluation_status = "REVIEW_REQUIRED"
        readiness_level = "PENDING"
        risk_level = "HIGH"
        next_step = "request_identity_evidence_for_manual_review"
        rationale = "Identity evidence is required before account action."
    elif privilege_risk:
        classification = "PRIVILEGE_RISK_REVIEW_REQUIRED"
        evaluation_status = "REVIEW_REQUIRED"
        readiness_level = "PENDING"
        risk_level = "HIGH"
        next_step = "escalate_privilege_risk_to_manual_security_review"
        rationale = "Privilege risk requires security owner review."
    elif payload.get("manual_action_ready"):
        classification = "READY_FOR_MANUAL_USER_ACTION"
        evaluation_status = "READY"
        readiness_level = "READY"
        risk_level = "LOW"
        next_step = "route_user_action_for_manual_approval"
        rationale = "User account packet is complete for bounded action."
    else:
        classification = "READY_FOR_ACCOUNT_REVIEW"
        evaluation_status = "READY"
        readiness_level = "READY"
        risk_level = "LOW"
        next_step = "start_manual_account_review"
        rationale = "Input evidence is sufficient for deterministic review."

    return {
        "tenant_id": tenant_id,
        "module": "local_user_management",
        "maturity_level": "L3",
        "evaluation_status": evaluation_status,
        "classification": classification,
        "readiness_level": readiness_level,
        "risk_level": risk_level,
        "required_evidence": required_evidence,
        "missing_evidence": missing_evidence,
        "allowed_actions": [
            "REVIEW_ACCOUNT",
            "REQUEST_EVIDENCE",
            "ESCALATE_REVIEW",
        ],
        "forbidden_actions": [
            "AUTO_LOCK_ACCOUNT",
            "AUTO_GRANT_PRIVILEGES",
            "AUTO_DISABLE_USER",
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
