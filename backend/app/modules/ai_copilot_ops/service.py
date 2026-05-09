"""A-024.2 — AI Copilot Ops operational contract (L3 evidence).

This module returns deterministic advisory/review evidence only.
No external AI calls, no autonomous execution, and no tool execution.
"""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


OPS_STATES: frozenset[str] = frozenset({"DRAFT", "ACTIVE", "PAUSED", "ARCHIVED"})
SAFETY_GUARDS: frozenset[str] = frozenset(
    {
        "NO_AUTONOMOUS_EXECUTION",
        "NO_EXTERNAL_LLM_PROVIDER_CALLS",
        "NO_FAKE_BRAIN_DECISIONS",
        "NO_SYNTHETIC_KPI_DASHBOARD_VALUES",
    }
)

COPILOT_MODES: frozenset[str] = frozenset({"disabled", "monitor_only", "advisory", "review_required"})
COPILOT_REQUEST_STATUSES: frozenset[str] = frozenset(
    {"advisory_allowed", "review_required", "blocked", "unavailable"}
)
COPILOT_RISK_LEVELS: frozenset[str] = frozenset({"low", "medium", "high", "critical"})
COPILOT_EVENT_READINESS: dict[str, str] = {
    "advisory_allowed": "ai.copilot.advisory_allowed",
    "review_required": "ai.copilot.review_required",
    "blocked": "ai.copilot.blocked",
}

KNOWN_TARGET_DOMAINS: frozenset[str] = frozenset(
    {
        "academic",
        "student_success",
        "governance",
        "platform_ops",
        "finance_procurement",
    }
)
DESTRUCTIVE_ACTIONS: frozenset[str] = frozenset(
    {
        "approve_payment",
        "execute_contract",
        "enforce_discipline",
        "auto_apply_schedule_mutation",
    }
)
SENSITIVE_DATA_CLASSIFICATIONS: frozenset[str] = frozenset(
    {"restricted", "regulated", "confidential", "pii", "financial_sensitive"}
)


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _normalize_required(value: str, *, field: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise ValueError(f"{field} is required")
    return normalized


def _normalize_mode(mode: str) -> str:
    normalized = (mode or "").strip().lower()
    if normalized not in COPILOT_MODES:
        raise ValueError(f"mode must be one of {sorted(COPILOT_MODES)}")
    return normalized


def build_ai_copilot_ops_decision(
    *,
    tenant_id: int,
    user_role: str,
    requested_action: str,
    data_classification: str,
    target_domain: str,
    estimated_cost: float,
    purpose: str,
    mode: str,
    source_entity_type: str,
    source_entity_id: str,
) -> dict[str, object]:
    """Build deterministic copilot advisory/review evidence."""
    _validate_tenant(tenant_id)
    role = _normalize_required(user_role, field="user_role").lower()
    action = _normalize_required(requested_action, field="requested_action").lower()
    classification = _normalize_required(data_classification, field="data_classification").lower()
    domain = _normalize_required(target_domain, field="target_domain").lower()
    copilot_purpose = _normalize_required(purpose, field="purpose")
    current_mode = _normalize_mode(mode)
    source_type = _normalize_required(source_entity_type, field="source_entity_type")
    source_id = _normalize_required(source_entity_id, field="source_entity_id")

    if estimated_cost < 0:
        raise ValueError("estimated_cost must be >= 0")

    safety_reasons: list[str] = []
    policy_reasons: list[str] = []
    request_status = "advisory_allowed"
    risk_level = "low"
    review_required = False

    if current_mode == "disabled":
        request_status = "blocked"
        risk_level = "critical"
        review_required = True
        policy_reasons.append("COPILOT_MODE_DISABLED")

    if action in DESTRUCTIVE_ACTIONS:
        request_status = "blocked"
        risk_level = "critical"
        review_required = True
        safety_reasons.append("DESTRUCTIVE_ACTION_NOT_ALLOWED")

    if classification in SENSITIVE_DATA_CLASSIFICATIONS:
        review_required = True
        if request_status == "advisory_allowed":
            request_status = "review_required"
        if risk_level in {"low", "medium"}:
            risk_level = "high"
        safety_reasons.append("SENSITIVE_DATA_CLASSIFICATION")

    if estimated_cost >= 1000:
        review_required = True
        if request_status == "advisory_allowed":
            request_status = "review_required"
        if risk_level == "low":
            risk_level = "medium"
        safety_reasons.append("HIGH_ESTIMATED_COST")

    if domain not in KNOWN_TARGET_DOMAINS:
        review_required = True
        if request_status == "advisory_allowed":
            request_status = "review_required"
        if risk_level in {"low", "medium"}:
            risk_level = "high"
        safety_reasons.append("UNKNOWN_TARGET_DOMAIN")

    if role in {"anonymous", "guest"}:
        request_status = "blocked"
        risk_level = "critical"
        review_required = True
        safety_reasons.append("INSUFFICIENT_ROLE")

    if current_mode == "review_required":
        if request_status != "blocked":
            request_status = "review_required"
        review_required = True
        policy_reasons.append("COPILOT_MODE_FORCE_REVIEW")
    elif current_mode in {"monitor_only", "advisory"}:
        policy_reasons.append(f"COPILOT_MODE_{current_mode.upper()}")

    policy_reasons.extend(
        [
            "NO_EXTERNAL_CALLS_IN_A0242",
            "NO_AUTONOMOUS_EXECUTION_IN_A0242",
            "NO_TOOL_EXECUTION_IN_A0242",
        ]
    )

    if request_status not in COPILOT_REQUEST_STATUSES:
        request_status = "unavailable"
        risk_level = "critical"
        review_required = True

    if request_status == "advisory_allowed" and review_required:
        request_status = "review_required"

    event_readiness = COPILOT_EVENT_READINESS.get(request_status, "ai.copilot.review_required")

    return {
        "tenant_id": tenant_id,
        "user_role": role,
        "requested_action": action,
        "data_classification": classification,
        "target_domain": domain,
        "estimated_cost": float(estimated_cost),
        "purpose": copilot_purpose,
        "mode": current_mode,
        "source_entity_type": source_type,
        "source_entity_id": source_id,
        "request_status": request_status,
        "risk_level": risk_level,
        "review_required": review_required,
        "safety_reasons": sorted(set(safety_reasons)),
        "policy_reasons": sorted(set(policy_reasons)),
        "audit_action": f"ai_copilot_ops.{request_status}",
        "event_readiness": event_readiness,
        "no_external_call": True,
        "no_autonomous_execution": True,
        "no_tool_execution": True,
    }


def register_ops_profile(
    tenant_id: int,
    *,
    profile_name: str,
    scope: str,
    policy_note: str,
) -> dict:
    """Register ops profile metadata in DRAFT state."""
    _validate_tenant(tenant_id)
    if not profile_name:
        raise ValueError("profile_name is required")
    if not scope:
        raise ValueError("scope is required")
    if not policy_note:
        raise ValueError("policy_note is required")

    row = create_entity_for_tenant(
        "ai_copilot_ops_profiles",
        {
            "profile_name": profile_name,
            "scope": scope,
            "policy_note": policy_note,
            "status": "DRAFT",
            "tenant_id": tenant_id,
        },
        tenant_id,
    )
    return {"profile_id": row["id"], "status": "DRAFT"}


def list_ops_profiles(tenant_id: int, *, status: str | None = None) -> list[dict]:
    """List tenant-scoped ops profiles with optional status filter."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant("ai_copilot_ops_profiles", tenant_id)
    if status:
        rows = [row for row in rows if row.get("status") == status]
    return rows
