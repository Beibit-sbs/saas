"""A-023.5 — AI Cost Governance service skeleton (L2).

Tracks tenant-scoped governance policy metadata only.
"""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


POLICY_STATES: frozenset[str] = frozenset(
    {"DRAFT", "ACTIVE", "SUSPENDED", "RETIRED"}
)
SAFETY_GUARDS: frozenset[str] = frozenset(
    {
        "NO_FAKE_MINISTRY_SUBMISSION",
        "NO_FAKE_COMPLIANCE_SCORE",
        "NO_SYNTHETIC_KPI_DASHBOARD_VALUES",
        "NO_AUTOMATIC_POLICY_ENFORCEMENT",
    }
)


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def register_cost_policy(
    tenant_id: int,
    *,
    policy_name: str,
    budget_scope: str,
    governance_note: str,
) -> dict:
    """Register AI cost-governance policy metadata in DRAFT state."""
    _validate_tenant(tenant_id)
    if not policy_name:
        raise ValueError("policy_name is required")
    if not budget_scope:
        raise ValueError("budget_scope is required")
    if not governance_note:
        raise ValueError("governance_note is required")

    row = create_entity_for_tenant(
        tenant_id,
        "ai_cost_governance_policies",
        {
            "policy_name": policy_name,
            "budget_scope": budget_scope,
            "governance_note": governance_note,
            "status": "DRAFT",
            "tenant_id": tenant_id,
        },
    )
    return {"policy_id": row["id"], "status": "DRAFT"}


def set_policy_status(
    tenant_id: int,
    *,
    policy_id: str,
    status: str,
) -> dict:
    """Set governance policy status explicitly, without auto-application."""
    _validate_tenant(tenant_id)
    if status not in POLICY_STATES:
        raise ValueError(f"status must be one of {sorted(POLICY_STATES)}")

    for row in list_entities_for_tenant(tenant_id, "ai_cost_governance_policies"):
        if row.get("id") == policy_id:
            row["status"] = status
            return {"policy_id": policy_id, "status": status}

    raise ValueError(f"Policy {policy_id!r} not found for tenant {tenant_id}")


def list_policies(
    tenant_id: int,
    *,
    status: str | None = None,
) -> list[dict]:
    """List tenant-scoped governance policy metadata entries."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "ai_cost_governance_policies")
    if status:
        rows = [row for row in rows if row.get("status") == status]
    return rows


def evaluate_ai_cost_governance_readiness(
    tenant_id: int,
    cost_payload: dict | None = None,
) -> dict:
    """Return deterministic L3 readiness classification for AI cost governance."""
    _validate_tenant(tenant_id)
    payload = cost_payload or {}

    required_evidence = [
        "policy_id",
        "budget_limit",
        "period_usage",
        "governance_owner",
    ]
    missing_evidence = [key for key in required_evidence if payload.get(key) in (None, "")]

    threshold_breached = bool(payload.get("threshold_breached"))
    usage_evidence_gap = bool(payload.get("usage_evidence_gap"))

    if missing_evidence:
        classification = "AI_COST_INPUT_INCOMPLETE"
        evaluation_status = "INCOMPLETE"
        readiness_level = "PENDING"
        risk_level = "MEDIUM"
        next_step = "collect_missing_cost_governance_evidence"
        rationale = "Required cost governance evidence is incomplete."
    elif threshold_breached:
        classification = "BUDGET_THRESHOLD_REVIEW_REQUIRED"
        evaluation_status = "REVIEW_REQUIRED"
        readiness_level = "PENDING"
        risk_level = "HIGH"
        next_step = "route_threshold_breach_to_manual_governance_review"
        rationale = "Budget threshold breach requires manual policy review."
    elif usage_evidence_gap:
        classification = "USAGE_EVIDENCE_REQUIRED"
        evaluation_status = "REVIEW_REQUIRED"
        readiness_level = "PENDING"
        risk_level = "HIGH"
        next_step = "collect_usage_evidence_before_policy_review"
        rationale = "Usage evidence gap blocks deterministic review closure."
    elif payload.get("governance_ready"):
        classification = "READY_FOR_MANUAL_COST_GOVERNANCE_REVIEW"
        evaluation_status = "READY"
        readiness_level = "READY"
        risk_level = "LOW"
        next_step = "submit_for_manual_cost_governance_review"
        rationale = "Cost governance inputs are complete for human review."
    else:
        classification = "READY_FOR_COST_POLICY_REVIEW"
        evaluation_status = "READY"
        readiness_level = "READY"
        risk_level = "LOW"
        next_step = "start_manual_cost_policy_review"
        rationale = "Policy data is sufficient for bounded deterministic review."

    return {
        "tenant_id": tenant_id,
        "module": "ai_cost_governance",
        "maturity_level": "L3",
        "evaluation_status": evaluation_status,
        "classification": classification,
        "readiness_level": readiness_level,
        "risk_level": risk_level,
        "required_evidence": required_evidence,
        "missing_evidence": missing_evidence,
        "allowed_actions": [
            "REVIEW_COST_POLICY",
            "REQUEST_EVIDENCE",
            "ESCALATE_REVIEW",
        ],
        "forbidden_actions": [
            "AUTO_ENFORCE_COST_POLICY",
            "AUTO_SUSPEND_AI_ACCESS",
            "AUTO_CHANGE_BUDGET_LIMITS",
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
