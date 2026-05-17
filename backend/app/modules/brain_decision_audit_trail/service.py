"""Deterministic L2 envelope contract for brain_decision_audit_trail (A-027.6)."""

from __future__ import annotations

MODULE_NAME = "brain_decision_audit_trail"
UCE_ID = "UCE-054"
CANDIDATE_TYPE = "AUDIT_EVIDENCE_CAPABILITY"
TARGET_LEVEL = "L2"
CONTRACT_VERSION = "A-027.6"
ENVELOPE_STATUS = "ENVELOPE_READY"
ENVELOPE_ONLY = True
RUNTIME_EXECUTION_ALLOWED = False
HUMAN_APPROVAL_REQUIRED = True
CONTRACT_KIND = "audit_evidence_contract"
DOMAIN_CONTEXT = "AI Governance"
PURPOSE = "Audit evidence lineage envelope for recommendation-to-decision traceability"

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


def get_brain_decision_audit_trail_envelope_contract(tenant_id: int, payload: dict | None = None) -> dict:
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
        "evidence_scope": {
            "domain": DOMAIN_CONTEXT,
            "lineage_tracking_mode": "contract_metadata_only",
        },
        "source_reference_model": {
            "source_types": ["workflow_record", "policy_reference", "signal_reference"],
            "immutable_storage_claim": False,
        },
        "lineage_boundary": {
            "hash_chain_claim": False,
            "finality_claim": False,
            "human_verification_required": True,
        },
        "auditability_boundary": {
            "audit_ready_contract": True,
            "auto_attestation": False,
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
    "decision_context_defined",
    "recommendation_source_identified",
    "human_reviewer_required",
    "audit_lineage_schema_available",
    "retention_policy_linked",
]
A02711_MIN_COMPLETENESS_THRESHOLD = 60

A02711_ALLOWED_ACTIONS = [
    "AUDIT_TRAIL_READINESS_CLASSIFICATION",
    "MISSING_EVIDENCE_IDENTIFICATION",
    "HUMAN_REVIEW_PREPARATION",
]

A02711_FORBIDDEN_ACTIONS = [
    "EXECUTE_BRAIN_RECOMMENDATION",
    "AUTO_APPROVE_DECISION",
    "AUTO_REJECT_DECISION",
    "CALL_MODEL_PROVIDER",
    "MUTATE_AUDIT_RECORD",
    "PROCESS_SIGNAL",
    "AUTONOMOUS_ACTION",
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


def classify_brain_decision_audit_trail_readiness(
    tenant_id: int,
    present_evidence: list[str] | set[str] | None = None,
) -> dict:
    """Deterministic L3 readiness classification for UCE-054 without Brain execution."""
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


# ──────────────────────────────────────────────────────────────────────────────
# A-030.1 Brain Governance Foundation — L4 Read-Only Governance Visibility
# ──────────────────────────────────────────────────────────────────────────────

BRAIN_GOVERNANCE_LAYER = "FOUNDATION"
BRAIN_GOVERNANCE_VERSION = "A-030.1"
A0301_MATURITY_TARGET = "L4_READONLY_GOVERNANCE_VISIBILITY"
SIGNAL_REGISTRY_MODE = "READINESS_AND_EVIDENCE_ONLY"
EXECUTION_MODE = "NO_EXECUTION"

_A0301_EVIDENCE_SOURCE_MAP = {
    "decision_context_evidence": "decision_context_records, signal_input_snapshots, reasoning_context_docs",
    "source_evidence_refs": "evidence_lineage_references, source_document_links, approval_chain_refs",
    "human_reviewer_evidence": "human_reviewer_assignment_records, review_completion_logs, override_records",
    "override_reason_evidence": "override_justification_docs, escalation_reason_logs, exception_records",
    "timestamp_category_evidence": "decision_timestamp_logs, category_assignment_records, version_history",
}

_A0301_REQUIRED_EVIDENCE = [
    "decision_context_evidence",
    "source_evidence_refs",
    "human_reviewer_evidence",
    "override_reason_evidence",
    "timestamp_category_evidence",
]

_A0301_MISSING_EVIDENCE_CATEGORIES = [
    "structured_audit_trail_schema_definition",
    "human_reviewer_identity_binding_protocol",
    "immutable_audit_log_storage_readiness",
]

_A0301_EXPLAINABILITY_INPUT_MAP = {
    "signal_source": "decision context + source evidence refs + human reviewer records",
    "human_readable_context": "Governance audit visibility map for responsible AI officer review",
    "explainability_level": "L4_VISIBILITY_FOUNDATION",
    "no_hidden_computation": True,
    "no_synthetic_output": True,
}

_A0301_HUMAN_REVIEW_REASONS = [
    "Brain decision audit requires human governance officer review",
    "No actual decision execution is permitted by this module",
    "Audit trail categories must be verified by responsible AI governance officer",
    "Any audit finding escalation requires human approval before any action",
]

_A0301_AUDIT_EVENT_CATEGORY_MAP = {
    "audit_foundation_readiness_check": "AUDIT_GOVERNANCE",
    "human_reviewer_assignment": "AUDIT_HUMAN_DECISION",
    "evidence_gap_identified": "AUDIT_EVIDENCE_GAP",
    "governance_visibility_check": "AUDIT_FOUNDATION_VALIDATION",
    "override_reason_capture": "AUDIT_OVERRIDE_TRACKING",
}

_A0301_GOVERNANCE_RISK_CLASSIFICATION = {
    "domain": "brain_audit_governance",
    "risk_boundary": "NO_DECISION_EXECUTION",
    "sensitivity": "CRITICAL",
    "human_escalation_required": True,
}

_A0301_ALLOWED_OUTPUTS = [
    "signal_registry_metadata",
    "evidence_source_map",
    "required_evidence_list",
    "missing_evidence_list",
    "explainability_input_map",
    "human_review_reasons",
    "audit_event_category_map",
    "governance_risk_classification",
    "next_safe_setup_steps",
]

_A0301_FORBIDDEN_OUTPUTS = [
    "actual_decision_execution",
    "fake_past_decisions",
    "autonomous_approvals",
    "retroactive_audit_fabrication",
    "final_decision",
    "recommendation_to_approve_or_reject",
    "synthetic_score",
    "hidden_ranking",
    "automated_action",
    "provider_call",
    "llm_generated_decision",
    "notification_send",
    "workflow_execution",
]

_A0301_NEXT_SAFE_SETUP_STEPS = [
    "Define audit trail schema fields with AI governance committee",
    "Establish human reviewer identity binding protocol",
    "Map evidence lineage fields to immutable storage readiness requirements",
    "Define override reason capture categories with human approver",
    "Document audit event taxonomy before any further maturity advance",
]


def get_brain_decision_audit_trail_governance_visibility(tenant_id: int) -> dict:
    """Return deterministic L4 read-only governance visibility contract (A-030.1).

    NO execution. NO LLM. NO autonomous decisions. Audit event map only.
    Human review required before any action.
    """
    tenant_id = validate_tenant_id(tenant_id)

    return {
        "uce_id": UCE_ID,
        "module_key": MODULE_NAME,
        "module_name": "Brain Decision Audit Trail",
        "brain_governance_layer": BRAIN_GOVERNANCE_LAYER,
        "brain_governance_version": BRAIN_GOVERNANCE_VERSION,
        "maturity_target": A0301_MATURITY_TARGET,
        "signal_registry_mode": SIGNAL_REGISTRY_MODE,
        "execution_mode": EXECUTION_MODE,
        "llm_calls_enabled": False,
        "model_provider_configured": False,
        "autonomous_decision_enabled": False,
        "action_execution_enabled": False,
        "hidden_scoring_enabled": False,
        "synthetic_score_enabled": False,
        "human_review_required": True,
        "tenant_id": tenant_id,
        "tenant_scoped": True,
        "read_only": True,
        "no_mutation": True,
        "no_brain_execution": True,
        "no_llm_call": True,
        "no_autonomous_action": True,
        "no_auto_approval": True,
        "no_auto_rejection": True,
        "no_sensitive_decision": True,
        "no_procurement_decision": True,
        "no_l5_claim": True,
        "no_l6_claim": True,
        "evidence_source_map": dict(_A0301_EVIDENCE_SOURCE_MAP),
        "required_evidence": list(_A0301_REQUIRED_EVIDENCE),
        "missing_evidence_categories": list(_A0301_MISSING_EVIDENCE_CATEGORIES),
        "explainability_input_map": dict(_A0301_EXPLAINABILITY_INPUT_MAP),
        "human_review_reasons": list(_A0301_HUMAN_REVIEW_REASONS),
        "audit_event_category_map": dict(_A0301_AUDIT_EVENT_CATEGORY_MAP),
        "governance_risk_classification": dict(_A0301_GOVERNANCE_RISK_CLASSIFICATION),
        "allowed_outputs": list(_A0301_ALLOWED_OUTPUTS),
        "forbidden_outputs": list(_A0301_FORBIDDEN_OUTPUTS),
        "next_safe_setup_steps": list(_A0301_NEXT_SAFE_SETUP_STEPS),
    }
