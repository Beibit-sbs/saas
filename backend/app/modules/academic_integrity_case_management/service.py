"""
academic_integrity_case_management service.py — L2 Foundation Contract
"""

MODULE_NAME = "academic_integrity_case_management"
UCE_ID = "UCE-078"
TARGET_LEVEL = "L2"
CONTRACT_VERSION = "A-027.4"
FOUNDATION_STATUS = "FOUNDATION_READY"

LIFECYCLE_STATUSES = ["CASE_OPENED", "EVIDENCE_COLLECTION", "COMMITTEE_REVIEW", "DECISION_PENDING", "CLOSED"]
ALLOWED_ACTIONS = ["REVIEW_INTEGRITY_CASE", "REQUEST_EVIDENCE", "MARK_READY_FOR_HUMAN_DECISION"]
FORBIDDEN_ACTIONS = ["AUTO_ACCUSATION", "AUTO_PENALTY", "AUTO_CHANGE_GRADE"]
REQUIRED_EVIDENCE = ["case_record", "evidence_bundle", "committee_record"]

SAFETY_FLAGS = {
    "no_api_claim": True, "no_frontend_claim": True, "no_live_integration_claim": True,
    "no_provider_call": True, "no_kpi_claim": True, "no_brain_claim": True,
    "no_autonomous_execution": True, "no_external_side_effects": True,
    "no_l3_claim": True, "no_l4_claim": True, "no_l5_claim": True, "no_l6_claim": True,
}

def validate_tenant_id(tenant_id):
    if tenant_id is None:
        raise ValueError("tenant_id cannot be None")
    if isinstance(tenant_id, bool):
        raise ValueError(f"invalid_tenant_id: bool not accepted: {tenant_id!r}")
    if not isinstance(tenant_id, int):
        raise ValueError(f"invalid_tenant_id: must be positive int, got {type(tenant_id).__name__}: {tenant_id!r}")
    if tenant_id <= 0:
        raise ValueError(f"tenant_id must be positive, got {tenant_id}")
    return tenant_id

def get_academic_integrity_case_management_foundation_contract(tenant_id, payload=None):
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
            "no_automatic_academic_misconduct_decision": True,
            "no_penalty_automation": True,
            "no_automatic_grade_change": True,
        },
        "safety_flags": SAFETY_FLAGS,
    }


def get_academic_integrity_case_management_sensitive_readiness_foundation(
    tenant_id: int,
) -> dict:
    """A-030.5-RUNTIME: Sensitive-domain readiness foundation for academic integrity case management.

    Boundary: READINESS_AND_EVIDENCE_ONLY + NO_EXECUTION + NO_FINDING_NO_PENALTY
    Contract: L3_DETERMINISTIC_READINESS_GOVERNANCE / UCE-078
    Deferred: UCE-093 (academic_appeals_workflow — execution layer)
    """
    tenant_id = validate_tenant_id(tenant_id)
    return {
        "module": "academic_integrity_case_management",
        "uce_id": "UCE-078",
        "maturity": "L3_DETERMINISTIC_READINESS_GOVERNANCE",
        "readiness_layer": "SENSITIVE_DOMAIN_FOUNDATION",
        "execution_mode": "NO_EXECUTION",
        "boundary": "NO_FINDING_NO_PENALTY",
        "tenant_id": tenant_id,
        "academic_integrity_case_governance": {
            "readiness_only": True,
            "no_case_execution": True,
            "no_official_finding": True,
            "no_penalty_execution": True,
            "no_student_status_change": True,
            "allowed_states": [
                "CASE_OPENED",
                "EVIDENCE_COLLECTION",
                "COMMITTEE_REVIEW",
                "DECISION_PENDING",
                "CLOSED",
            ],
            "allowed_human_actions": [
                "REVIEW_INTEGRITY_CASE",
                "REQUEST_EVIDENCE",
                "MARK_READY_FOR_HUMAN_DECISION",
            ],
            "forbidden_auto_actions": [
                "AUTO_ACCUSATION",
                "AUTO_PENALTY",
                "AUTO_CHANGE_GRADE",
            ],
        },
        "evidence_envelope": {
            "evidence_intake_metadata_supported": True,
            "evidence_review_required": True,
            "evidence_outcome_generated": False,
            "similarity_score_generated": False,
            "plagiarism_detection_performed": False,
            "case_record": "EVIDENCE_INTAKE_ONLY",
            "evidence_bundle": "EVIDENCE_INTAKE_ONLY",
            "committee_record": "EVIDENCE_INTAKE_ONLY",
            "no_finding_generated": True,
            "no_determination_generated": True,
        },
        "policy_reference_envelope": {
            "policy_reference_required": True,
            "policy_interpretation_automated": False,
            "policy_decision_generated": False,
            "academic_integrity_policy_reference": "POLICY_LINK_ONLY",
            "no_auto_enforcement": True,
            "human_policy_interpretation_required": True,
        },
        "human_review_envelope": {
            "human_review_required": True,
            "reviewer_decision_required": True,
            "automated_decision_allowed": False,
            "reviewer_role": "ACADEMIC_INTEGRITY_OFFICER",
            "no_automated_review": True,
        },
        "committee_review_envelope": {
            "committee_review_required": True,
            "committee_outcome_generated": False,
            "committee_decision_executed": False,
            "committee_type": "ACADEMIC_INTEGRITY_COMMITTEE",
            "no_automated_committee_decision": True,
        },
        "fairness_review_envelope": {
            "fairness_review_required": True,
            "bias_check_required": True,
            "discriminatory_score_generated": False,
            "no_automated_fairness_decision": True,
        },
        "appeal_boundary": {
            "appeal_available": True,
            "appeal_metadata_only": True,
            "appeal_decision_generated": False,
            "academic_appeals_workflow_deferred": True,
            "deferred_candidate": "UCE-093",
            "appeal_procedure": "FORMAL_ACADEMIC_APPEALS_PROCESS",
            "appeal_deadline_metadata": "POLICY_DEFINED",
            "no_appeal_waiver_by_automation": True,
        },
        "audit_trail_readiness": {
            "audit_trail_required": True,
            "due_process_trace_required": True,
            "immutable_record_written": False,
            "external_submission_performed": False,
            "audit_logging_ready": True,
            "all_actions_must_be_logged": True,
            "no_hidden_action": True,
        },
        "forbidden_actions": [
            "academic_integrity_finding",
            "plagiarism_finding",
            "cheating_finding",
            "guilt_determination",
            "grade_penalty",
            "disciplinary_penalty",
            "sanction",
            "student_status_change",
            "notification_execution",
            "recommendation",
            "ranking",
            "external_submission",
            "hidden_score",
            "synthetic_score",
            "discriminatory_score",
            "llm_call",
            "brain_execution",
            "autonomous_decision",
        ],
        "anti_fake_flags": {
            "no_academic_integrity_finding": True,
            "no_plagiarism_finding": True,
            "no_cheating_finding": True,
            "no_guilt_determination": True,
            "no_grade_penalty": True,
            "no_disciplinary_penalty": True,
            "no_sanction": True,
            "no_student_status_change": True,
            "no_notification_execution": True,
            "no_recommendation": True,
            "no_ranking": True,
            "no_external_submission": True,
            "no_hidden_score": True,
            "no_synthetic_score": True,
            "no_discriminatory_score": True,
            "no_llm_call": True,
            "no_brain_execution": True,
            "no_autonomous_decision": True,
            "no_l5_claim": True,
            "no_l6_claim": True,
            "human_review_required": True,
            "committee_review_required": True,
            "fairness_review_required": True,
            "appeal_available": True,
        },
        "metric_contract": {
            "A0305_academic_integrity_sensitive_foundation_count": 1,
            "sensitive_domain_foundation_count_after_runtime": 5,
            "sensitive_execution_count": 0,
            "sensitive_auto_sanction_count": 0,
            "sensitive_auto_disciplinary_decision_count": 0,
            "sensitive_auto_academic_integrity_decision_count": 0,
            "sensitive_hidden_score_count": 0,
            "sensitive_discriminatory_score_count": 0,
            "sensitive_synthetic_score_count": 0,
            "sensitive_recommendation_count": 0,
            "sensitive_external_submission_count": 0,
            "baseline_impact": 0,
            "extension_impact": 0,
            "ordinary_expansion_impact": 0,
            "provider_readiness_impact": 0,
            "brain_governance_impact": 0,
            "policy_procurement_impact": 0,
        },
    }
