"""Deterministic L2 envelope contract for third_party_risk_policy (A-027.6)."""

from __future__ import annotations

MODULE_NAME = "third_party_risk_policy"
UCE_ID = "UCE-047"
CANDIDATE_TYPE = "POLICY_CONTROL"
TARGET_LEVEL = "L2"
CONTRACT_VERSION = "A-027.6"
ENVELOPE_STATUS = "ENVELOPE_READY"
ENVELOPE_ONLY = True
RUNTIME_EXECUTION_ALLOWED = False
HUMAN_APPROVAL_REQUIRED = True
CONTRACT_KIND = "policy_control_contract"
DOMAIN_CONTEXT = "Security / Legal"
PURPOSE = "Third-party risk policy boundary envelope"

EVIDENCE_REQUIREMENTS = [
    "governance_policy_reference",
    "tenant_scope_context",
    "human_review_record",
]

ALLOWED_ACTIONS = [
    "DESCRIBE_CONTRACT",
    "VALIDATE_EVIDENCE_REQUIREMENTS",
    "MARK_READY_FOR_HUMAN_REVIEW",
]

FORBIDDEN_ACTIONS = [
    "AUTO_EXECUTE",
    "AUTO_APPROVE",
    "AUTO_SEND",
    "AUTO_ENFORCE",
    "AUTO_MUTATE_RECORD",
    "BRAIN_EXECUTE_DECISION",
    "AUTONOMOUS_DECISION",
]

HUMAN_REVIEW_BOUNDARY = {
    "human_approval_required": True,
    "execution_without_human": False,
    "manual_verification_required": True,
}

TENANT_SECURITY_BOUNDARY = {
    "tenant_scoped": True,
    "cross_tenant_access_allowed": False,
    "tenant_validation_fail_closed": True,
}

BRAIN_BOUNDARY = {
    "brain_execution_allowed": False,
    "recommendation_execution_allowed": False,
    "signal_scoring_allowed": False,
}

AUTONOMY_BOUNDARY = {
    "autonomous_execution_allowed": False,
    "auto_approval_allowed": False,
    "auto_routing_allowed": False,
    "auto_notification_allowed": False,
}

SAFETY_FLAGS = {
    "no_api_claim": True,
    "no_frontend_claim": True,
    "no_db_claim": True,
    "no_kpi_value_claim": True,
    "no_fake_dashboard": True,
    "no_brain_execution": True,
    "no_autonomous_execution": True,
    "human_approval_required": True,
    "no_external_side_effects": True,
    "no_provider_call": True,
    "no_live_notification": True,
    "no_document_signature": True,
    "no_decision_enforcement": True,
    "no_l3_claim": True,
    "no_l4_claim": True,
    "no_l5_claim": True,
    "no_l6_claim": True,
}


def validate_tenant_id(tenant_id: int) -> int:
    """Fail-closed tenant validation for envelope contracts."""
    if tenant_id is None:
        raise ValueError("tenant_id is required")
    if not isinstance(tenant_id, int):
        raise TypeError("tenant_id must be an int")
    if tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")
    return tenant_id


def get_third_party_risk_policy_envelope_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """Return deterministic L2 envelope metadata without runtime execution."""
    tenant_id = validate_tenant_id(tenant_id)
    _ = payload

    return {
        "tenant_id": tenant_id,
        "module": MODULE_NAME,
        "uce_id": UCE_ID,
        "candidate_type": CANDIDATE_TYPE,
        "maturity_level": TARGET_LEVEL,
        "expansion_layer": "university_completeness",
        "contract_status": ENVELOPE_STATUS,
        "envelope_only": ENVELOPE_ONLY,
        "runtime_execution_allowed": RUNTIME_EXECUTION_ALLOWED,
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "tenant_scoped": True,
        "deterministic": True,
        "contract_kind": CONTRACT_KIND,
        "purpose": PURPOSE,
        "domain_context": DOMAIN_CONTEXT,
        "evidence_requirements": list(EVIDENCE_REQUIREMENTS),
        "allowed_actions": list(ALLOWED_ACTIONS),
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "human_review_boundary": dict(HUMAN_REVIEW_BOUNDARY),
        "tenant_security_boundary": dict(TENANT_SECURITY_BOUNDARY),
        "brain_boundary": dict(BRAIN_BOUNDARY),
        "autonomy_boundary": dict(AUTONOMY_BOUNDARY),
        "policy_scope": {
            "domain": DOMAIN_CONTEXT,
            "policy_layer": "governance_boundary",
        },
        "rule_boundaries": {
            "automatic_enforcement_allowed": False,
            "blocking_action_allowed": False,
            "financial_or_academic_action_allowed": False,
        },
        "evidence_required": list(EVIDENCE_REQUIREMENTS),
        "enforcement_boundary": {
            "auto_enforcement": False,
            "human_decision_required": True,
        },
        "next_maturity_gap": "L3 deterministic envelope readiness logic required",
        "safety_flags": dict(SAFETY_FLAGS),
    }


# A-027.11 deterministic L3 readiness overlay constants
A02711_L3_READY = True
MATURITY_LEVEL = "L3"
EXPANSION_LAYER = "university_completeness"
HUMAN_REVIEW_REQUIRED = True
L2_CONTRACT_PRESERVED = True

READINESS_READY = "READY_FOR_REVIEW"
READINESS_PARTIAL = "PARTIAL_EVIDENCE"
READINESS_INCOMPLETE = "INCOMPLETE_EVIDENCE"
READINESS_BLOCKED = "BLOCKED_MISSING_EVIDENCE"

RISK_LOW = "LOW"
RISK_MEDIUM = "MEDIUM"
RISK_HIGH = "HIGH"
RISK_BLOCKED = "BLOCKED"

NEXT_READY = "READY_FOR_HUMAN_REVIEW"
NEXT_REQUEST = "REQUEST_MISSING_EVIDENCE"
NEXT_BLOCK = "BLOCK_UNTIL_REQUIRED_EVIDENCE_PRESENT"

A02711_REQUIRED_EVIDENCE = [
    "third_party_scope_defined",
    "risk_categories_defined",
    "owner_assigned",
    "review_cycle_defined",
    "human_policy_review_required",
]
A02711_MIN_COMPLETENESS_THRESHOLD = 60

A02711_ALLOWED_ACTIONS = [
    "POLICY_READINESS_CLASSIFICATION",
    "MISSING_CONTROL_IDENTIFICATION",
    "HUMAN_REVIEW_PREPARATION",
]

A02711_FORBIDDEN_ACTIONS = [
    "ENFORCE_POLICY",
    "AUTO_BLOCK_VENDOR",
    "AUTO_APPROVE_VENDOR",
    "AUTO_REJECT_VENDOR",
    "MUTATE_PROCUREMENT_RECORD",
    "MUTATE_LEGAL_RECORD",
]


def _normalize_present_evidence(present_evidence: list[str] | set[str] | None) -> list[str]:
    if present_evidence is None:
        return []
    if isinstance(present_evidence, set):
        evidence_values = list(present_evidence)
    elif isinstance(present_evidence, list):
        evidence_values = present_evidence
    else:
        raise ValueError("present_evidence must be list[str], set[str], or None")

    normalized = {str(item).strip() for item in evidence_values if str(item).strip()}
    return sorted(normalized)


def classify_third_party_risk_policy_readiness(
    tenant_id: int,
    present_evidence: list[str] | set[str] | None = None,
) -> dict:
    """Deterministic L3 readiness classification for UCE-047 without policy enforcement."""
    tenant_id = validate_tenant_id(tenant_id)
    present = _normalize_present_evidence(present_evidence)

    required = list(A02711_REQUIRED_EVIDENCE)
    missing = [item for item in required if item not in present]

    if required:
        completeness = int(((len(required) - len(missing)) / len(required)) * 100)
    else:
        completeness = 100

    if not present:
        readiness = READINESS_BLOCKED
    elif not missing:
        readiness = READINESS_READY
    elif completeness < A02711_MIN_COMPLETENESS_THRESHOLD:
        readiness = READINESS_INCOMPLETE
    else:
        readiness = READINESS_PARTIAL

    risk_band = {
        READINESS_READY: RISK_LOW,
        READINESS_PARTIAL: RISK_MEDIUM,
        READINESS_INCOMPLETE: RISK_HIGH,
        READINESS_BLOCKED: RISK_BLOCKED,
    }[readiness]

    recommended_next_step = {
        READINESS_READY: NEXT_READY,
        READINESS_PARTIAL: NEXT_REQUEST,
        READINESS_INCOMPLETE: NEXT_REQUEST,
        READINESS_BLOCKED: NEXT_BLOCK,
    }[readiness]

    return {
        "tenant_id": tenant_id,
        "module": MODULE_NAME,
        "uce_id": UCE_ID,
        "maturity_level": MATURITY_LEVEL,
        "expansion_layer": EXPANSION_LAYER,
        "deterministic_logic_ready": A02711_L3_READY,
        "readiness_status": readiness,
        "risk_band": risk_band,
        "evidence_completeness": completeness,
        "required_evidence": required,
        "present_evidence": present,
        "missing_evidence": missing,
        "recommended_next_step": recommended_next_step,
        "human_review_required": HUMAN_REVIEW_REQUIRED,
        "allowed_actions": list(A02711_ALLOWED_ACTIONS),
        "forbidden_actions": list(A02711_FORBIDDEN_ACTIONS),
        "l2_contract_preserved": L2_CONTRACT_PRESERVED,
        "tenant_scoped": True,
        "next_maturity_gap": "L4 operational visibility/API surface required",
        "safety_flags": {
            "no_api_claim": True,
            "no_frontend_claim": True,
            "no_provider_call": True,
            "no_credential_use": True,
            "no_kpi_value_claim": True,
            "no_brain_execution": True,
            "no_autonomous_execution": True,
            "no_external_side_effects": True,
            "no_db_mutation": True,
            "no_decision_execution": True,
            "no_policy_enforcement": True,
            "no_workflow_execution": True,
            "human_review_required": True,
            "no_l4_claim": True,
            "no_l5_claim": True,
            "no_l6_claim": True,
            "tenant_fail_closed": True,
            "l2_contract_preserved": True,
        },
    }
