"""
disability_support_services service.py — L2 Foundation Contract

Deterministic foundation contract for disability support request governance.
Tenant fail-closed validation.
No autonomy, no provider calls, no KPI, no Brain, no L3+ claims.
"""

# Constants
MODULE_NAME = "disability_support_services"
UCE_ID = "UCE-081"
TARGET_LEVEL = "L2"
CONTRACT_VERSION = "A-027.4"
FOUNDATION_STATUS = "FOUNDATION_READY"

# Lifecycle statuses
LIFECYCLE_STATUSES = [
    "REQUESTED",
    "DOCUMENTATION_REVIEW",
    "ACCOMMODATION_REVIEW",
    "APPROVED_MANUAL",
    "CLOSED",
]

# Allowed actions (deterministic constants only)
ALLOWED_ACTIONS = [
    "REVIEW_SUPPORT_REQUEST",
    "REQUEST_DOCUMENTATION",
    "MARK_READY_FOR_ACCOMMODATION_REVIEW",
]

# Forbidden actions (deterministic constraints only)
FORBIDDEN_ACTIONS = [
    "AUTO_APPROVE_ACCOMMODATION",
    "AUTO_DENY_SUPPORT",
    "AUTO_DISCLOSE_DISABILITY_DATA",
]

# Required evidence
REQUIRED_EVIDENCE = [
    "support_request",
    "consent_record",
    "documentation_evidence",
]

# Safety flags
SAFETY_FLAGS = {
    "no_api_claim": True,
    "no_frontend_claim": True,
    "no_live_integration_claim": True,
    "no_provider_call": True,
    "no_kpi_claim": True,
    "no_brain_claim": True,
    "no_autonomous_execution": True,
    "no_external_side_effects": True,
    "no_l3_claim": True,
    "no_l4_claim": True,
    "no_l5_claim": True,
    "no_l6_claim": True,
}


def validate_tenant_id(tenant_id):
    """Fail-closed tenant validation."""
    if tenant_id is None:
        raise ValueError("tenant_id cannot be None")
    if not isinstance(tenant_id, int):
        raise TypeError(f"tenant_id must be int, got {type(tenant_id)}")
    if tenant_id <= 0:
        raise ValueError(f"tenant_id must be positive, got {tenant_id}")
    return tenant_id


def get_disability_support_services_foundation_contract(tenant_id, payload=None):
    """
    Generate deterministic L2 foundation contract for disability support services.
    
    Args:
        tenant_id: Integer tenant identifier
        payload: Optional dict (unused at L2)
    
    Returns:
        dict: Deterministic foundation contract
    """
    tenant_id = validate_tenant_id(tenant_id)
    
    return {
        "tenant_id": tenant_id,
        "module": MODULE_NAME,
        "uce_id": UCE_ID,
        "maturity_level": TARGET_LEVEL,
        "expansion_layer": "university_completeness",
        "contract_status": "FOUNDATION_READY",
        "service_contract_ready": True,
        "tenant_scoped": True,
        "deterministic": True,
        "lifecycle_statuses": LIFECYCLE_STATUSES,
        "allowed_actions": ALLOWED_ACTIONS,
        "forbidden_actions": FORBIDDEN_ACTIONS,
        "required_evidence": REQUIRED_EVIDENCE,
        "next_maturity_gap": "L3 deterministic logic required",
        "sensitive_boundary": {
            "no_medical_diagnosis": True,
            "no_automatic_accommodation_decision": True,
            "no_disclosure_of_sensitive_data": True,
        },
        "safety_flags": SAFETY_FLAGS,
    }


def get_disability_support_sensitive_readiness_foundation(tenant_id):
    """A-030.3-RUNTIME: Sensitive-domain readiness foundation."""
    tenant_id = validate_tenant_id(tenant_id)
    return {
        "tenant_id": tenant_id,
        "uce_id": "UCE-081",
        "module_key": "disability_support_services",
        "module_name": "Disability Support Services",
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
            "accommodation_request_evidence": "accommodation_request_form",
            "supporting_document_reference": "medical_or_accessibility_documentation",
            "course_or_exam_context_evidence": "course_exam_schedule",
            "accessibility_policy_reference": "institutional_accessibility_policy",
            "reviewer_assignment_evidence": "assigned_accessibility_officer_record",
            "audit_log_evidence": "accommodation_workflow_audit_trail",
        },
        "required_evidence": [
            "accommodation_request_evidence",
            "supporting_document_reference",
            "accessibility_policy_reference",
            "reviewer_assignment_evidence",
        ],
        "missing_evidence_categories": ["medical documentation", "accessibility evidence"],
        "human_review_reasons": [
            "non_discrimination_review_required",
            "reviewer_independence_required",
            "reasonable_adjustment_context_required",
            "privacy_minimization_required",
        ],
        "appeal_boundary_map": {
            "accommodation_request_boundary": "request_eligible_for_review",
            "reviewer_assignment_boundary": "reviewer_must_be_accessibility_expert",
            "appeal_or_reconsideration_boundary": "appeal_process_available",
            "accessibility_policy_boundary": "policy_based_determination",
            "auditability_boundary": "all_actions_logged",
        },
        "audit_event_category_map": {
            "request_submission_event": "accommodation_request_received",
            "documentation_review_event": "supporting_documents_reviewed",
            "reviewer_assignment_event": "accessibility_officer_assigned",
            "review_started_event": "accommodation_review_commenced",
            "decision_pending_event": "awaiting_human_decision",
            "review_closed_event": "accommodation_review_concluded",
        },
        "fairness_review_checkpoints": [
            "non_discrimination_review_required",
            "reviewer_independence_required",
            "reasonable_adjustment_context_required",
            "privacy_minimization_required",
        ],
        "legal_review_checkpoints": [
            "accessibility_policy_basis_required",
            "privacy_boundary_required",
            "medical_data_minimization_required",
            "record_retention_boundary_required",
        ],
        "governance_risk_classification": {
            "domain": "disability_support_governance",
            "risk_boundary": "NO_ACCOMMODATION_APPROVAL_NO_ACCOMMODATION_DENIAL",
        },
        "allowed_outputs": ["readiness_metadata", "evidence_source_map", "required_evidence_list", "missing_evidence_list", "human_review_reasons", "appeal_boundary_map", "audit_event_category_map", "fairness_review_checkpoints", "legal_review_checkpoints", "governance_risk_classification", "next_safe_setup_steps"],
        "forbidden_outputs": ["accommodation_approval", "accommodation_denial", "medical_inference", "eligibility_decision", "hidden_disability_score", "recommendation"],
        "next_safe_setup_steps": ["Collect accommodation_request_evidence", "Review privacy_boundary requirements", "Assign qualified accessibility_officer", "Verify supporting_document_reference", "Prepare fairness_review_checkpoints", "Complete legal_review_checkpoints", "Human reviewer assesses accommodation readiness", "Log all audit_events"],
    }
