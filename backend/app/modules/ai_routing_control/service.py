"""A-024.1 — AI Routing Control operational contract (L3 evidence).

This module intentionally provides deterministic policy/risk evidence only.
It does not call external AI providers and does not perform autonomous execution.
"""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


ROUTING_STATES: frozenset[str] = frozenset({"DRAFT", "ACTIVE", "SUSPENDED", "RETIRED"})
SAFETY_GUARDS: frozenset[str] = frozenset(
    {
        "NO_AUTONOMOUS_EXECUTION",
        "NO_EXTERNAL_LLM_PROVIDER_CALLS",
        "NO_FAKE_BRAIN_DECISIONS",
        "NO_SYNTHETIC_OBSERVABILITY_ALERTS",
    }
)

ROUTING_MODES: frozenset[str] = frozenset({"disabled", "monitor_only", "advisory", "controlled"})
ROUTING_DECISION_STATUSES: frozenset[str] = frozenset(
    {"allowed", "review_required", "blocked", "unavailable"}
)
ROUTING_RISK_LEVELS: frozenset[str] = frozenset({"low", "medium", "high", "critical"})
ROUTING_EVENT_READINESS: dict[str, str] = {
    "allowed": "ai.routing.allowed",
    "review_required": "ai.routing.review_required",
    "blocked": "ai.routing.blocked",
}

KNOWN_CAPABILITIES: frozenset[str] = frozenset(
    {
        "summarization",
        "classification",
        "policy_analysis",
        "academic_assist",
        "risk_flagging",
        "workflow_recommendation",
    }
)
SENSITIVE_DATA_CLASSIFICATIONS: frozenset[str] = frozenset(
    {"restricted", "regulated", "confidential", "pii", "financial_sensitive"}
)


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _validate_mode(policy_mode: str) -> str:
    mode = (policy_mode or "").strip().lower()
    if mode not in ROUTING_MODES:
        raise ValueError(f"policy_mode must be one of {sorted(ROUTING_MODES)}")
    return mode


def _normalize_text(value: str, *, field: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise ValueError(f"{field} is required")
    return normalized


def build_ai_routing_control_decision(
    *,
    tenant_id: int,
    requested_capability: str,
    data_classification: str,
    estimated_cost: float,
    user_role: str,
    purpose: str,
    policy_mode: str,
    source_entity_type: str,
    source_entity_id: str,
) -> dict[str, object]:
    """Build deterministic routing evidence without executing any AI call."""
    _validate_tenant(tenant_id)
    capability = _normalize_text(requested_capability, field="requested_capability").lower()
    classification = _normalize_text(data_classification, field="data_classification").lower()
    role = _normalize_text(user_role, field="user_role").lower()
    routing_purpose = _normalize_text(purpose, field="purpose")
    mode = _validate_mode(policy_mode)
    source_type = _normalize_text(source_entity_type, field="source_entity_type")
    source_id = _normalize_text(source_entity_id, field="source_entity_id")

    if estimated_cost < 0:
        raise ValueError("estimated_cost must be >= 0")

    safety_reasons: list[str] = []
    policy_reasons: list[str] = []
    risk_level = "low"
    decision_status = "allowed"
    review_required = False

    if mode == "disabled":
        decision_status = "blocked"
        review_required = True
        risk_level = "critical"
        policy_reasons.append("POLICY_MODE_DISABLED")

    if capability not in KNOWN_CAPABILITIES:
        review_required = True
        if decision_status != "blocked":
            decision_status = "review_required"
        risk_level = "high"
        safety_reasons.append("UNKNOWN_CAPABILITY")

    if classification in SENSITIVE_DATA_CLASSIFICATIONS:
        review_required = True
        if decision_status == "allowed":
            decision_status = "review_required"
        if risk_level in {"low", "medium"}:
            risk_level = "high"
        safety_reasons.append("SENSITIVE_DATA_CLASSIFICATION")

    if estimated_cost >= 1000:
        review_required = True
        if decision_status == "allowed":
            decision_status = "review_required"
        if risk_level == "low":
            risk_level = "medium"
        safety_reasons.append("HIGH_ESTIMATED_COST")

    if role in {"anonymous", "guest"}:
        review_required = True
        decision_status = "blocked"
        risk_level = "critical"
        safety_reasons.append("INSUFFICIENT_ROLE_FOR_ROUTING")

    if mode in {"monitor_only", "advisory", "controlled"}:
        policy_reasons.append(f"POLICY_MODE_{mode.upper()}")

    policy_reasons.append("NO_EXTERNAL_CALLS_IN_A0241")
    policy_reasons.append("NO_AUTONOMOUS_EXECUTION_IN_A0241")

    if decision_status not in ROUTING_DECISION_STATUSES:
        decision_status = "unavailable"
        review_required = True
        risk_level = "critical"

    if decision_status == "allowed" and review_required:
        decision_status = "review_required"

    event_name = ROUTING_EVENT_READINESS.get(decision_status, "ai.routing.review_required")
    audit_action = f"ai_routing_control.{decision_status}"

    return {
        "tenant_id": tenant_id,
        "requested_capability": capability,
        "data_classification": classification,
        "estimated_cost": float(estimated_cost),
        "user_role": role,
        "purpose": routing_purpose,
        "policy_mode": mode,
        "source_entity_type": source_type,
        "source_entity_id": source_id,
        "decision_status": decision_status,
        "risk_level": risk_level,
        "review_required": review_required,
        "safety_reasons": sorted(set(safety_reasons)),
        "policy_reasons": sorted(set(policy_reasons)),
        "audit_action": audit_action,
        "event_readiness": event_name,
        "no_external_call": True,
        "no_autonomous_execution": True,
    }


def register_routing_policy(
    tenant_id: int,
    *,
    policy_name: str,
    route_scope: str,
    governance_note: str,
) -> dict[str, object]:
    """Register routing policy metadata in DRAFT state."""
    _validate_tenant(tenant_id)
    if not policy_name:
        raise ValueError("policy_name is required")
    if not route_scope:
        raise ValueError("route_scope is required")
    if not governance_note:
        raise ValueError("governance_note is required")

    row = create_entity_for_tenant(
        "ai_routing_control_policies",
        {
            "policy_name": policy_name,
            "route_scope": route_scope,
            "governance_note": governance_note,
            "status": "DRAFT",
            "tenant_id": tenant_id,
        },
        tenant_id,
    )
    return {"policy_id": row["id"], "status": "DRAFT"}


def list_routing_policies(tenant_id: int, *, status: str | None = None) -> list[dict[str, object]]:
    """List tenant-scoped routing policies with optional status filter."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant("ai_routing_control_policies", tenant_id)
    if status:
        rows = [row for row in rows if row.get("status") == status]
    return rows
