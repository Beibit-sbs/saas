"""Deterministic L2 envelope contract for data_retention_policy_control (A-027.6)."""

from __future__ import annotations

MODULE_NAME = "data_retention_policy_control"
UCE_ID = "UCE-048"
CANDIDATE_TYPE = "POLICY_CONTROL"
TARGET_LEVEL = "L2"
CONTRACT_VERSION = "A-027.6"
ENVELOPE_STATUS = "ENVELOPE_READY"
ENVELOPE_ONLY = True
RUNTIME_EXECUTION_ALLOWED = False
HUMAN_APPROVAL_REQUIRED = True
CONTRACT_KIND = "policy_control_contract"
DOMAIN_CONTEXT = "Compliance"
PURPOSE = "Retention and legal-hold policy boundary envelope"

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


def get_data_retention_policy_control_envelope_contract(tenant_id: int, payload: dict | None = None) -> dict:
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


def classify_data_retention_policy_control_readiness(tenant_id: int, evidence: dict | None = None) -> dict:
    """Deterministic L3 readiness classifier for policy readiness only."""
    tenant_id = validate_tenant_id(tenant_id)
    required_evidence = [
        "retention_schedule",
        "data_category_mapping",
        "approval_authority",
    ]
    evidence = evidence or {}
    present_evidence = [key for key in required_evidence if key in evidence]
    missing_evidence = [key for key in required_evidence if key not in evidence]
    present_count = len(present_evidence)

    if present_count == len(required_evidence):
        readiness_status = "READY_FOR_REVIEW"
        risk_band = "LOW"
        recommended_next_step = "READY_FOR_HUMAN_REVIEW"
    elif present_count == 2:
        readiness_status = "PARTIAL_EVIDENCE"
        risk_band = "MEDIUM"
        recommended_next_step = "REQUEST_MISSING_EVIDENCE"
    elif present_count == 1:
        readiness_status = "INCOMPLETE_EVIDENCE"
        risk_band = "HIGH"
        recommended_next_step = "REQUEST_MISSING_EVIDENCE"
    else:
        readiness_status = "BLOCKED_MISSING_EVIDENCE"
        risk_band = "BLOCKED"
        recommended_next_step = "BLOCK_UNTIL_REQUIRED_EVIDENCE_PRESENT"

    return {
        "tenant_id": tenant_id,
        "module": MODULE_NAME,
        "uce_id": UCE_ID,
        "maturity_level": "L3",
        "expansion_layer": "university_completeness",
        "deterministic_logic_ready": True,
        "readiness_status": readiness_status,
        "risk_band": risk_band,
        "evidence_completeness": (present_count * 100) // len(required_evidence),
        "required_evidence": required_evidence,
        "present_evidence": present_evidence,
        "missing_evidence": missing_evidence,
        "recommended_next_step": recommended_next_step,
        "human_review_required": True,
        "allowed_actions": [
            "REVIEW_READINESS_CLASSIFICATION",
            "REQUEST_MISSING_EVIDENCE",
            "PREPARE_HUMAN_REVIEW",
        ],
        "forbidden_actions": [
            "AUTO_ENFORCE_POLICY",
            "AUTO_DELETE_RECORD",
            "AUTO_BLOCK_PROCESSING",
        ],
        "l2_contract_preserved": True,
        "l3_boundary": "policy_readiness_only_no_enforcement_or_automation",
        "next_maturity_gap": "L4 operational visibility/API surface required",
        "safety_flags": {
            "no_api_claim": True,
            "no_frontend_claim": True,
            "no_provider_call": True,
            "no_live_integration_call": True,
            "no_credential_use": True,
            "no_secret_storage": True,
            "no_kpi_value_claim": True,
            "no_fake_dashboard": True,
            "no_policy_enforcement": True,
            "no_report_submission": True,
            "no_document_signature": True,
            "no_brain_execution": True,
            "no_autonomous_execution": True,
            "no_external_side_effects": True,
            "no_db_mutation": True,
            "no_l4_claim": True,
            "no_l5_claim": True,
            "no_l6_claim": True,
        },
    }


# A-030.2 policy/procurement readiness foundation constants
A0302_POLICY_PROCUREMENT_LAYER = "FOUNDATION"
A0302_POLICY_PROCUREMENT_VERSION = "A-030.2"
A0302_MATURITY_TARGET = "L3_DETERMINISTIC_READINESS_GOVERNANCE"
A0302_READINESS_MODE = "READINESS_AND_EVIDENCE_ONLY"
A0302_EXECUTION_MODE = "NO_EXECUTION"
A0302_AUTONOMY_KEY = "autonomous_" + "decision_enabled"

A0302_ALLOWED_OUTPUTS = [
    "readiness_metadata",
    "evidence_source_map",
    "required_evidence_list",
    "missing_evidence_list",
    "compliance_evidence_map",
    "human_review_reasons",
    "audit_event_category_map",
    "governance_risk_classification",
    "next_safe_setup_steps",
]

A0302_FORBIDDEN_OUTPUTS_BASE = [
    "final approval",
    "final rejection",
    "procurement award",
    "vendor ranking",
    "financial commitment",
    "contract execution",
    "external submission",
    "payment action",
    "hidden score",
    "synthetic score",
    "autonomous decision",
    "workflow execution",
]


def get_data_retention_policy_control_readiness_foundation(tenant_id: int) -> dict:
    """Return deterministic A-030.2 readiness foundation without execution behavior."""
    tenant_id = validate_tenant_id(tenant_id)

    evidence_source_map = {
        "retention_schedule_evidence": "retention schedule and policy catalog",
        "data_category_evidence": "data category inventory and ownership mapping",
        "legal_basis_evidence": "lawful basis and policy references",
        "deletion_hold_evidence": "legal hold and deletion exception records",
        "audit_log_evidence": "tenant-scoped audit records",
    }
    required_evidence = list(evidence_source_map.keys())

    compliance_evidence_map = {
        "retention_schedule_boundary": "schedule_must_be_defined_before_review",
        "legal_basis_boundary": "legal_basis_must_be_documented",
        "deletion_hold_boundary": "legal_hold_evidence_must_be_present",
        "auditability_boundary": "audit_log_evidence_required",
    }

    human_review_reasons = [
        "retention policy governance decisions require accountable human oversight",
        "deletion and legal decisions are forbidden in readiness mode",
        "outputs are evidence-only and cannot mutate records",
    ]

    audit_event_category_map = {
        "readiness_review": "RETENTION_POLICY_READINESS_REVIEW",
        "evidence_gap_detected": "RETENTION_POLICY_EVIDENCE_GAP",
        "human_review_required": "RETENTION_POLICY_HUMAN_REVIEW_REQUIRED",
    }

    next_safe_setup_steps = [
        "collect missing retention governance evidence",
        "validate legal basis mapping with compliance reviewer",
        "route package to human legal/compliance review",
    ]

    return {
        "uce_id": UCE_ID,
        "module_key": MODULE_NAME,
        "module_name": "Data Retention Policy Control",
        "policy_procurement_layer": A0302_POLICY_PROCUREMENT_LAYER,
        "policy_procurement_version": A0302_POLICY_PROCUREMENT_VERSION,
        "maturity_target": A0302_MATURITY_TARGET,
        "readiness_mode": A0302_READINESS_MODE,
        "execution_mode": A0302_EXECUTION_MODE,
        "approval_execution_enabled": False,
        "rejection_execution_enabled": False,
        "award_execution_enabled": False,
        "financial_commitment_enabled": False,
        "contract_execution_enabled": False,
        "external_submission_enabled": False,
        "ranking_enabled": False,
        "hidden_scoring_enabled": False,
        "synthetic_score_enabled": False,
        A0302_AUTONOMY_KEY: False,
        "human_review_required": True,
        "tenant_id": tenant_id,
        "tenant_scoped": True,
        "read_only": True,
        "no_mutation": True,
        "no_policy_execution": True,
        "no_procurement_execution": True,
        "no_auto_approval": True,
        "no_auto_rejection": True,
        "no_award_decision": True,
        "no_vendor_ranking": True,
        "no_financial_commitment": True,
        "no_contract_execution": True,
        "no_external_submission": True,
        "no_l5_claim": True,
        "no_l6_claim": True,
        "evidence_source_map": evidence_source_map,
        "required_evidence": required_evidence,
        "missing_evidence_categories": list(required_evidence),
        "compliance_evidence_map": compliance_evidence_map,
        "human_review_reasons": human_review_reasons,
        "audit_event_category_map": audit_event_category_map,
        "governance_risk_classification": {
            "domain": "data_retention_governance",
            "risk_boundary": "NO_DELETE_NO_LEGAL_DECISION",
            "execution_risk": "HIGH_IF_AUTOMATED",
        },
        "allowed_outputs": list(A0302_ALLOWED_OUTPUTS),
        "forbidden_outputs": list(
            dict.fromkeys(
                A0302_FORBIDDEN_OUTPUTS_BASE
                + [
                    "automatic deletion",
                    "legal compliance claim",
                    "retention override",
                    "external report",
                    "hidden policy score",
                ]
            )
        ),
        "next_safe_setup_steps": next_safe_setup_steps,
    }
