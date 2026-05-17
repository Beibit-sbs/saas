"""
student_financial_hardship service.py — L2 Foundation Contract
"""

MODULE_NAME = "student_financial_hardship"
UCE_ID = "UCE-082"
TARGET_LEVEL = "L2"
CONTRACT_VERSION = "A-027.4"
FOUNDATION_STATUS = "FOUNDATION_READY"

LIFECYCLE_STATUSES = ["REQUESTED", "DOCUMENTATION_REVIEW", "COMMITTEE_REVIEW", "DECISION_PENDING", "CLOSED"]
ALLOWED_ACTIONS = ["REVIEW_HARDSHIP_REQUEST", "REQUEST_FINANCIAL_EVIDENCE", "MARK_READY_FOR_COMMITTEE_REVIEW"]
FORBIDDEN_ACTIONS = ["AUTO_APPROVE_AID", "AUTO_REJECT_AID", "AUTO_CHANGE_BILLING_BALANCE"]
REQUIRED_EVIDENCE = ["hardship_request", "financial_evidence", "committee_record"]

SAFETY_FLAGS = {
    "no_api_claim": True, "no_frontend_claim": True, "no_live_integration_claim": True,
    "no_provider_call": True, "no_kpi_claim": True, "no_brain_claim": True,
    "no_autonomous_execution": True, "no_external_side_effects": True,
    "no_l3_claim": True, "no_l4_claim": True, "no_l5_claim": True, "no_l6_claim": True,
}

def validate_tenant_id(tenant_id):
    if tenant_id is None:
        raise ValueError("tenant_id cannot be None")
    if not isinstance(tenant_id, int):
        raise TypeError(f"tenant_id must be int, got {type(tenant_id)}")
    if tenant_id <= 0:
        raise ValueError(f"tenant_id must be positive, got {tenant_id}")
    return tenant_id

def get_student_financial_hardship_foundation_contract(tenant_id, payload=None):
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
            "no_automatic_aid_approval": True,
            "no_automatic_aid_rejection": True,
            "no_automatic_billing_changes": True,
        },
        "safety_flags": SAFETY_FLAGS,
    }


def get_student_financial_hardship_sensitive_readiness_foundation(tenant_id):
    """A-030.3-RUNTIME: Sensitive-domain readiness foundation."""
    tenant_id = validate_tenant_id(tenant_id)
    return {
        "tenant_id": tenant_id,
        "uce_id": "UCE-082",
        "module_key": "student_financial_hardship",
        "module_name": "Student Financial Hardship",
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
            "hardship_application_evidence": "hardship_application_form",
            "supporting_document_evidence": "financial_documentation",
            "tuition_or_balance_evidence": "student_account_statement",
            "eligibility_policy_reference": "hardship_policy_documentation",
            "reviewer_assignment_evidence": "assigned_reviewer_record",
            "audit_log_evidence": "hardship_workflow_audit_trail",
        },
        "required_evidence": [
            "hardship_application_evidence",
            "supporting_document_evidence",
            "tuition_or_balance_evidence",
            "eligibility_policy_reference",
            "reviewer_assignment_evidence",
        ],
        "missing_evidence_categories": ["financial documentation", "income verification"],
        "human_review_reasons": [
            "equal_treatment_review_required",
            "evidence_completeness_required",
            "conflict_of_interest_review_required",
            "reviewer_independence_required",
        ],
        "appeal_boundary_map": {
            "hardship_application_boundary": "application_eligible_for_review",
            "reviewer_assignment_boundary": "reviewer_must_be_qualified",
            "reconsideration_boundary": "reconsideration_process_available",
            "eligibility_policy_boundary": "policy_based_determination",
            "auditability_boundary": "all_actions_logged",
        },
        "audit_event_category_map": {
            "application_submission_event": "hardship_application_received",
            "documentation_review_event": "supporting_documents_reviewed",
            "reviewer_assignment_event": "reviewer_assigned",
            "review_started_event": "hardship_review_commenced",
            "decision_pending_event": "awaiting_human_decision",
            "review_closed_event": "hardship_review_concluded",
        },
        "fairness_review_checkpoints": [
            "equal_treatment_review_required",
            "evidence_completeness_required",
            "conflict_of_interest_review_required",
            "reviewer_independence_required",
        ],
        "legal_review_checkpoints": [
            "aid_policy_basis_required",
            "financial_data_privacy_boundary_required",
            "record_retention_boundary_required",
        ],
        "governance_risk_classification": {
            "domain": "student_financial_hardship_governance",
            "risk_boundary": "NO_AID_APPROVAL_NO_AID_REJECTION",
        },
        "allowed_outputs": ["readiness_metadata", "evidence_source_map", "required_evidence_list", "missing_evidence_list", "human_review_reasons", "appeal_boundary_map", "audit_event_category_map", "fairness_review_checkpoints", "legal_review_checkpoints", "governance_risk_classification", "next_safe_setup_steps"],
        "forbidden_outputs": ["aid_approval", "aid_rejection", "payment_execution", "debt_cancellation", "hidden_hardship_score", "recommendation"],
        "next_safe_setup_steps": ["Collect hardship_application_evidence", "Verify supporting_document_evidence", "Confirm tuition_or_balance_evidence accuracy", "Assign qualified reviewer", "Prepare fairness_review_checkpoints", "Complete legal_review_checkpoints", "Human reviewer assesses hardship readiness", "Log all audit_events"],
    }
