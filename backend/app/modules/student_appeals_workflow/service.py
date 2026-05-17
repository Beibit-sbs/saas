"""Deterministic L2 envelope contract for student_appeals_workflow (A-027.6)."""

from __future__ import annotations

MODULE_NAME = "student_appeals_workflow"
UCE_ID = "UCE-038"
CANDIDATE_TYPE = "WORKFLOW"
TARGET_LEVEL = "L2"
CONTRACT_VERSION = "A-027.6"
ENVELOPE_STATUS = "ENVELOPE_READY"
ENVELOPE_ONLY = True
RUNTIME_EXECUTION_ALLOWED = False
HUMAN_APPROVAL_REQUIRED = True
CONTRACT_KIND = "workflow_contract"
DOMAIN_CONTEXT = "Student Lifecycle"
PURPOSE = "Student appeals lifecycle envelope"

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


def get_student_appeals_workflow_envelope_contract(tenant_id: int, payload: dict | None = None) -> dict:
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
        "workflow_stages": ["INTAKE", "REVIEW", "HUMAN_DECISION", "CLOSED"],
        "actor_roles": ["initiator", "reviewer", "approver"],
        "transition_boundaries": {
            "automatic_transition_allowed": False,
            "manual_review_required": True,
            "state_mutation_allowed": False,
        },
        "required_evidence": list(EVIDENCE_REQUIREMENTS),
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
    "appeal_request_present",
    "appeal_category_defined",
    "case_evidence_present",
    "review_committee_required",
    "human_appeals_review_required",
]
A02711_MIN_COMPLETENESS_THRESHOLD = 60

A02711_ALLOWED_ACTIONS = [
    "APPEALS_WORKFLOW_READINESS_CLASSIFICATION",
    "MISSING_EVIDENCE_IDENTIFICATION",
    "HUMAN_REVIEW_PREPARATION",
]

A02711_FORBIDDEN_ACTIONS = [
    "AUTO_APPROVE_APPEAL",
    "AUTO_REJECT_APPEAL",
    "AUTO_CHANGE_GRADE",
    "AUTO_REVERSE_SANCTION",
    "AUTO_CHANGE_STUDENT_STATUS",
    "MUTATE_ACADEMIC_RECORD",
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


def classify_student_appeals_workflow_readiness(
    tenant_id: int,
    present_evidence: list[str] | set[str] | None = None,
) -> dict:
    """Deterministic L3 readiness classification for UCE-038 without appeal decisions."""
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


# A-028.9 L4 Visibility Summary - UCE-038 student_appeals_workflow

def _build_student_appeals_workflow_l4_visibility_summary(l3_output: dict) -> dict:
    """Build L4 visibility wrapper for student_appeals_workflow L3 readiness."""
    status = str(l3_output.get("readiness_status", "UNKNOWN"))
    required_evidence = list(l3_output.get("required_evidence", []))
    present_evidence = list(l3_output.get("present_evidence", []))
    missing_evidence = list(l3_output.get("missing_evidence", []))
    human_review_required = bool(l3_output.get("human_review_required", True))

    return {
        "tenant_id": l3_output["tenant_id"],
        "module": MODULE_NAME,
        "uce_id": UCE_ID,
        "visibility_level": "L4",
        "source_maturity_level": "L3",
        "visibility_type": "READ_ONLY_SERVICE_SUMMARY",
        "readiness_summary": {
            "status": status,
            "evidence_completeness": l3_output.get("evidence_completeness", 0),
            "recommended_next_step": l3_output.get("recommended_next_step"),
            "ready_for_human_review": status == "READY_FOR_REVIEW",
        },
        "risk_summary": {
            "risk_band": l3_output.get("risk_band"),
        },
        "evidence_summary": {
            "required_evidence_count": len(required_evidence),
            "present_evidence_count": len(present_evidence),
            "missing_evidence_count": len(missing_evidence),
            "required_evidence": required_evidence,
            "present_evidence": present_evidence,
        },
        "missing_evidence_summary": {
            "count": len(missing_evidence),
            "items": missing_evidence,
        },
        "human_review_queue_summary": {
            "candidate_count": 1 if human_review_required else 0,
            "ready_for_human_review_count": 1 if status == "READY_FOR_REVIEW" else 0,
            "blocked_count": 1 if status == "BLOCKED_MISSING_EVIDENCE" else 0,
        },
        "allowed_actions": list(dict.fromkeys(["VIEW_L4_VISIBILITY_SUMMARY"] + list(l3_output.get("allowed_actions", [])))),
        "forbidden_actions": list(l3_output.get("forbidden_actions", [])),
        "tenant_scoped": True,
        "read_only": True,
        "no_mutation": True,
        "no_provider_call": True,
        "no_external_submission": True,
        "no_brain_execution": True,
        "no_autonomous_execution": True,
        "no_workflow_execution": True,
        "no_decision_execution": True,
        "no_fake_kpi": True,
        "no_synthetic_score": True,
        "no_synthetic_dashboard": True,
        "no_l5_claim": True,
        "no_l6_claim": True,
        "l3_contract_preserved": True,
        "api_route_deferred_to": "A-028.10",
    }


def get_student_appeals_workflow_l4_visibility_summary(
    tenant_id: int, present_evidence: list[str] | set[str] | dict | None = None
) -> dict:
    """L4 read-only visibility summary for student_appeals_workflow (UCE-038)."""
    tenant_id = validate_tenant_id(tenant_id)
    evidence = present_evidence if isinstance(present_evidence, dict) else present_evidence
    l3_output = classify_student_appeals_workflow_readiness(
        tenant_id=tenant_id,
        present_evidence=evidence if isinstance(evidence, (list, set)) else None,
    )
    return _build_student_appeals_workflow_l4_visibility_summary(l3_output)


def get_student_appeals_sensitive_readiness_foundation(tenant_id: int) -> dict:
    """A-030.3-RUNTIME: Sensitive-domain readiness foundation."""
    tenant_id = validate_tenant_id(tenant_id)
    return {
        "tenant_id": tenant_id,
        "uce_id": "UCE-038",
        "module_key": "student_appeals_workflow",
        "module_name": "Student Appeals Workflow",
        "sensitive_domain_layer": "FOUNDATION",
        "sensitive_domain_version": "A-030.3",
        "maturity_target": "L3_DETERMINISTIC_READINESS_GOVERNANCE",
        "readiness_mode": "READINESS_AND_EVIDENCE_ONLY",
        "execution_mode": "NO_EXECUTION",
        "human_review_required": True,
        "appeal_boundary_required": True,
        "audit_trail_required": True,
        "fairness_review_required": True,
        "legal_review_required": True,
        "automatic_outcome_enabled": False,
        "sanction_execution_enabled": False,
        "eligibility_decision_enabled": False,
        "aid_decision_enabled": False,
        "accommodation_decision_enabled": False,
        "disciplinary_decision_enabled": False,
        "academic_integrity_decision_enabled": False,
        "hidden_scoring_enabled": False,
        "discriminatory_scoring_enabled": False,
        "synthetic_score_enabled": False,
        "ranking_enabled": False,
        "recommendation_enabled": False,
        "autonomous_decision_enabled": False,
        "external_submission_enabled": False,
        "tenant_scoped": True,
        "read_only": True,
        "no_mutation": True,
        "no_sensitive_execution": True,
        "no_auto_sanction": True,
        "no_auto_eligibility_decision": True,
        "no_auto_aid_decision": True,
        "no_auto_accommodation_decision": True,
        "no_auto_disciplinary_decision": True,
        "no_auto_academic_integrity_decision": True,
        "no_hidden_score": True,
        "no_discriminatory_score": True,
        "no_synthetic_score": True,
        "no_ranking": True,
        "no_recommendation": True,
        "no_external_submission": True,
        "no_l5_claim": True,
        "no_l6_claim": True,
        "evidence_source_map": {
            "appeal_submission_evidence": "appeal_intake_form",
            "original_decision_reference": "prior_decision_document",
            "appeal_basis_evidence": "grounds_for_appeal",
            "reviewer_assignment_evidence": "assigned_reviewer_record",
            "deadline_evidence": "appeal_deadline_policy",
            "audit_log_evidence": "appeal_workflow_audit_trail",
        },
        "required_evidence": [
            "appeal_submission_evidence",
            "original_decision_reference",
            "reviewer_assignment_evidence",
            "deadline_evidence",
        ],
        "missing_evidence_categories": ["additional documentation", "supporting evidence"],
        "human_review_reasons": [
            "independent_reviewer_required",
            "original_decision_validation_required",
            "fairness_check_required",
            "appeal_merit_assessment_required",
        ],
        "appeal_boundary_map": {
            "appeal_submission_boundary": "appeal_eligible_for_review",
            "original_decision_reference_boundary": "decision_can_be_reviewed",
            "independent_reviewer_boundary": "reviewer_must_be_independent",
            "deadline_review_boundary": "review_deadline_enforced",
            "auditability_boundary": "all_actions_logged",
        },
        "audit_event_category_map": {
            "appeal_submission_event": "appeal_intake",
            "reviewer_assignment_event": "reviewer_assigned",
            "review_started_event": "review_commenced",
            "decision_pending_event": "awaiting_human_decision",
            "review_closed_event": "review_concluded",
        },
        "fairness_review_checkpoints": [
            "reviewer_independence_required",
            "deadline_consistency_required",
            "evidence_completeness_required",
            "conflict_of_interest_review_required",
            "equal_treatment_verification_required",
        ],
        "legal_review_checkpoints": [
            "policy_basis_required",
            "appeal_rights_notice_required",
            "record_retention_boundary_required",
            "regulatory_compliance_check_required",
        ],
        "governance_risk_classification": {
            "domain": "student_appeals_governance",
            "risk_boundary": "NO_APPEAL_APPROVAL_NO_APPEAL_REJECTION",
        },
        "allowed_outputs": ["readiness_metadata", "evidence_source_map", "required_evidence_list", "missing_evidence_list", "human_review_reasons", "appeal_boundary_map", "audit_event_category_map", "fairness_review_checkpoints", "legal_review_checkpoints", "governance_risk_classification", "next_safe_setup_steps"],
        "forbidden_outputs": ["appeal_approval", "appeal_rejection", "outcome_change", "notification_execution", "hidden_appeal_score", "recommendation"],
        "next_safe_setup_steps": ["Verify appeal_submission_evidence collection", "Assign independent reviewer", "Enforce deadline_evidence", "Prepare fairness_review_checkpoints", "Complete legal_review_checkpoints", "Human decision maker reviews readiness", "Log all audit_events"],
    }
