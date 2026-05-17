"""Disciplinary_Case_Management L2 Foundation Service Contract (UCE-007)."""

from . import MODULE_NAME, UCE_ID, TARGET_LEVEL, CONTRACT_VERSION, FOUNDATION_STATUS


def validate_tenant_id(tenant_id: int) -> int:
    """Fail-closed tenant validation."""
    if not tenant_id or tenant_id <= 0:
        raise ValueError(f"invalid_tenant_id: {tenant_id}")
    return tenant_id


def get_disciplinary_case_management_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """L2 foundation contract for disciplinary_case_management. No provider calls, no autonomy, deterministic only."""
    validate_tenant_id(tenant_id)
    
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
        
        "lifecycle_statuses": [
            "CASE_OPENED",
            "EVIDENCE_COLLECTION",
            "HR_LEGAL_REVIEW",
            "DECISION_PENDING",
            "CLOSED"
        ],
        
        "allowed_actions": [
            "REVIEW_DISCIPLINARY_CASE",
            "REQUEST_EVIDENCE",
            "MARK_READY_FOR_HUMAN_DECISION"
        ],
        
        "forbidden_actions": [
            "NO_AUTO_PENALIZE_EMPLOYEE",
            "NO_AUTO_TERMINATE_EMPLOYEE",
            "NO_AUTO_RECORD_DISCIPLINARY_DECISION"
        ],
        
        "required_evidence": [
            "case_record",
            "evidence_bundle",
            "hearing_record"
        ],
        
        "next_maturity_gap": "L3 deterministic logic: case lifecycle management and escalation rules",
        
        "safety_flags": {
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
            "no_l6_claim": True
        }
    }


def get_disciplinary_sensitive_readiness_foundation(tenant_id: int) -> dict:
    """A-030.4-RUNTIME: Sensitive-domain readiness foundation for disciplinary case management."""
    tenant_id = validate_tenant_id(tenant_id)
    return {
        "tenant_id": tenant_id,
        "uce_id": "UCE-007",
        "module_key": "disciplinary_case_management",
        "module_name": "Disciplinary Case Management",
        "sensitive_domain_layer": "FOUNDATION",
        "sensitive_domain_version": "A-030.4",
        "maturity_target": "L3_DETERMINISTIC_READINESS_GOVERNANCE",
        "sensitive_type": "disciplinary_governance",
        "readiness_mode": "READINESS_AND_EVIDENCE_ONLY",
        "execution_mode": "NO_EXECUTION",
        "human_review_required": True,
        "appeal_boundary_required": True,
        "audit_trail_required": True,
        "fairness_review_required": True,
        "legal_review_required": True,
        "automatic_outcome_enabled": False,
        "sanction_execution_enabled": False,
        "disciplinary_decision_enabled": False,
        "academic_integrity_decision_enabled": False,
        "academic_outcome_change_enabled": False,
        "appeal_decision_enabled": False,
        "notification_execution_enabled": False,
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
        "no_auto_disciplinary_decision": True,
        "no_auto_academic_integrity_decision": True,
        "no_academic_outcome_change": True,
        "no_appeal_decision": True,
        "no_notification_execution": True,
        "no_hidden_score": True,
        "no_discriminatory_score": True,
        "no_synthetic_score": True,
        "no_ranking": True,
        "no_recommendation": True,
        "no_external_submission": True,
        "no_l5_claim": True,
        "no_l6_claim": True,
        "evidence_source_map": {
            "case_record_evidence": "disciplinary_case_record",
            "policy_reference_evidence": "disciplinary_policy_document",
            "hearing_notice_evidence": "hearing_notice_issued",
            "respondent_statement_evidence": "respondent_response_recorded",
            "reviewer_assignment_evidence": "assigned_reviewer_record",
            "audit_log_evidence": "disciplinary_case_audit_trail",
        },
        "required_evidence": [
            "case_record_evidence",
            "policy_reference_evidence",
            "hearing_notice_evidence",
            "respondent_statement_evidence",
            "reviewer_assignment_evidence",
            "audit_log_evidence",
        ],
        "missing_evidence_categories": [
            "case_record_if_absent",
            "policy_reference_if_absent",
            "hearing_notice_if_absent",
            "respondent_statement_if_absent",
            "reviewer_assignment_if_absent",
            "audit_log_if_absent",
        ],
        "human_review_reasons": [
            "disciplinary_outcome_requires_human_review",
            "sanction_requires_human_review",
            "conduct_finding_requires_human_review",
            "appeal_rights_require_human_review",
            "fairness_review_required_before_any_outcome",
        ],
        "appeal_boundary_map": {
            "disciplinary_policy_boundary": "policy_applies_to_respondent",
            "hearing_notice_boundary": "respondent_received_notice",
            "respondent_response_boundary": "respondent_had_chance_to_respond",
            "independent_reviewer_boundary": "reviewer_is_independent",
            "appeal_rights_boundary": "appeal_rights_exist",
            "auditability_boundary": "all_actions_audit_logged",
        },
        "audit_event_category_map": {
            "disciplinary_case_opened_reference": "case_opened_event",
            "evidence_added_reference": "evidence_collection_event",
            "reviewer_assignment_reference": "reviewer_assigned_event",
            "hearing_notice_reference": "hearing_notice_event",
            "appeal_boundary_reference": "appeal_rights_established_event",
            "human_review_reference": "human_review_initiated_event",
        },
        "fairness_review_checkpoints": [
            "reviewer_independence_required",
            "conflict_of_interest_review_required",
            "evidence_completeness_required",
            "proportionality_review_required",
            "equal_treatment_review_required",
        ],
        "legal_review_checkpoints": [
            "policy_basis_required",
            "due_process_notice_required",
            "record_retention_boundary_required",
            "appeal_rights_notice_required",
        ],
        "governance_risk_classification": {
            "domain": "disciplinary_governance",
            "risk_boundary": "NO_SANCTION_NO_DISCIPLINARY_OUTCOME",
            "risk_level": "HIGH",
            "requires_human_review": True,
            "requires_appeal_boundary": True,
            "requires_legal_review": True,
        },
        "allowed_outputs": [
            "readiness_metadata",
            "evidence_source_map",
            "required_evidence_list",
            "missing_evidence_list",
            "human_review_reasons",
            "appeal_boundary_map",
            "audit_event_category_map",
            "fairness_review_checkpoints",
            "legal_review_checkpoints",
            "governance_risk_classification",
            "next_safe_setup_steps",
        ],
        "forbidden_outputs": [
            "sanction",
            "guilt_finding",
            "disciplinary_decision",
            "disciplinary_outcome",
            "student_status_change",
            "notification_execution",
            "hidden_conduct_score",
            "recommendation",
            "ranking",
            "external_submission",
        ],
        "next_safe_setup_steps": [
            "Verify case_record_evidence collection",
            "Verify policy_reference_evidence availability",
            "Verify hearing_notice_evidence delivery",
            "Collect respondent_statement_evidence",
            "Assign independent reviewer",
            "Document appeal_rights boundary",
            "Prepare fairness_review_checkpoints",
            "Complete legal_review_checkpoints",
            "Enable audit_log_evidence collection",
            "Human review manager verifies readiness",
        ],
    }
