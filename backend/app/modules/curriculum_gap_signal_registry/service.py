"""Deterministic L2 envelope + A-030.1 Brain Governance Foundation contract
for curriculum_gap_signal_registry (UCE-132).

L2 envelope: expansion registry base (A-029 planned).
A-030.1: L3 deterministic signal governance readiness logic.

NO Brain execution. NO LLM. NO autonomous decisions. Evidence map only.
Human review required before any action.
"""

from __future__ import annotations

# ──────────────────────────────────────────────────────────────────────────────
# L2 Envelope Foundation (expansion registry base)
# ──────────────────────────────────────────────────────────────────────────────

MODULE_NAME = "curriculum_gap_signal_registry"
UCE_ID = "UCE-132"
CANDIDATE_TYPE = "BRAIN_SIGNAL"
TARGET_LEVEL = "L2"
CONTRACT_VERSION = "A-030.1"
ENVELOPE_STATUS = "ENVELOPE_READY"
ENVELOPE_ONLY = True
RUNTIME_EXECUTION_ALLOWED = False
HUMAN_APPROVAL_REQUIRED = True
CONTRACT_KIND = "brain_signal_envelope"
DOMAIN_CONTEXT = "Curriculum Governance"
PURPOSE = "Signal taxonomy envelope for curriculum gap governance"

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
    """Fail-closed tenant validation."""
    if tenant_id is None:
        raise ValueError("tenant_id is required")
    if not isinstance(tenant_id, int):
        raise TypeError("tenant_id must be an int")
    if tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")
    return tenant_id


def get_curriculum_gap_signal_registry_envelope_contract(
    tenant_id: int, payload: dict | None = None
) -> dict:
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
        "signal_scope": {
            "domain": DOMAIN_CONTEXT,
            "registry_mode": "taxonomy_only",
            "execution_enabled": False,
        },
        "required_signal_inputs": ["approved_source_events", "reviewed_context_fields"],
        "evidence_lineage_requirements": list(EVIDENCE_REQUIREMENTS),
        "confidence_boundary": {
            "score_computation_allowed": False,
            "recommendation_execution_allowed": False,
        },
        "human_review_required": True,
        "next_maturity_gap": "L3 deterministic envelope readiness logic required",
        "safety_flags": dict(SAFETY_FLAGS),
    }


# ──────────────────────────────────────────────────────────────────────────────
# A-030.1 Brain Governance Foundation — L3 Deterministic Signal Governance Logic
# ──────────────────────────────────────────────────────────────────────────────

BRAIN_GOVERNANCE_LAYER = "FOUNDATION"
BRAIN_GOVERNANCE_VERSION = "A-030.1"
A0301_MATURITY_TARGET = "L3_DETERMINISTIC_SIGNAL_GOVERNANCE_LOGIC"
SIGNAL_REGISTRY_MODE = "READINESS_AND_EVIDENCE_ONLY"
EXECUTION_MODE = "NO_EXECUTION"

_A0301_EVIDENCE_SOURCE_MAP = {
    "course_learning_outcomes_evidence": "course_syllabus_records, clo_definition_docs, assessment_alignment_records",
    "program_learning_outcomes_evidence": "program_specification_docs, plo_matrix_records, graduate_attribute_mappings",
    "assessment_alignment_evidence": "assessment_task_records, learning_outcome_coverage_maps, gap_identification_logs",
    "curriculum_mapping_evidence": "curriculum_map_docs, subject_sequence_records, prerequisite_chain_docs",
    "accreditation_reference_evidence": "accreditation_standard_references, external_benchmark_docs, compliance_readiness_records",
}

_A0301_REQUIRED_EVIDENCE = [
    "course_learning_outcomes_evidence",
    "program_learning_outcomes_evidence",
    "assessment_alignment_evidence",
    "curriculum_mapping_evidence",
    "accreditation_reference_evidence",
]

_A0301_MISSING_EVIDENCE_CATEGORIES = [
    "automated_curriculum_map_feed",
    "real_time_accreditation_standard_sync",
    "assessment_gap_analysis_system_connection",
]

_A0301_EXPLAINABILITY_INPUT_MAP = {
    "signal_source": "course learning outcomes + program outcomes + curriculum maps",
    "human_readable_context": "Evidence map for curriculum committee to assess gap signal readiness",
    "explainability_level": "FOUNDATION_READINESS",
    "no_hidden_computation": True,
    "no_synthetic_output": True,
}

_A0301_HUMAN_REVIEW_REASONS = [
    "Curriculum gap classification requires human curriculum committee review",
    "No automatic curriculum change or department ranking is permitted",
    "Evidence completeness must be verified by responsible academic authority",
    "Any gap finding escalation requires human approval before any action",
]

_A0301_AUDIT_EVENT_CATEGORY_MAP = {
    "evidence_readiness_check": "AUDIT_GOVERNANCE",
    "human_review_trigger": "AUDIT_HUMAN_DECISION",
    "signal_gap_identified": "AUDIT_EVIDENCE_GAP",
    "governance_foundation_check": "AUDIT_FOUNDATION_VALIDATION",
}

_A0301_GOVERNANCE_RISK_CLASSIFICATION = {
    "domain": "curriculum_governance",
    "risk_boundary": "NO_CURRICULUM_CHANGE_NO_RANKING",
    "sensitivity": "HIGH",
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
    "final_decision",
    "recommendation_to_approve_or_reject",
    "synthetic_score",
    "hidden_ranking",
    "automated_action",
    "provider_call",
    "llm_generated_decision",
    "notification_send",
    "workflow_execution",
    "sensitive_eligibility_decision",
    "automatic_curriculum_change",
    "ranking_departments",
    "synthetic_gap_score",
    "accreditation_decision",
]

_A0301_NEXT_SAFE_SETUP_STEPS = [
    "Map verified course learning outcome records with curriculum committee approval",
    "Confirm program outcome schema alignment before any feed integration",
    "Validate assessment alignment gap identification format with academic team",
    "Define human reviewer assignment protocol for each curriculum gap signal category",
    "Document evidence lineage policy before any further maturity advance",
]


def get_curriculum_gap_signal_governance_foundation(tenant_id: int) -> dict:
    """Return deterministic L3 signal governance readiness contract (A-030.1).

    NO execution. NO LLM. NO autonomous decisions. Evidence map only.
    Human review required before any action.
    """
    tenant_id = validate_tenant_id(tenant_id)

    return {
        "uce_id": UCE_ID,
        "module_key": MODULE_NAME,
        "module_name": "Curriculum Gap Signal Registry",
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
