"""L2 foundation service contract for internship_marketplace (A-026.7.L1L2)."""

from typing import Any, Mapping

MODULE_NAME = "internship_marketplace"
TARGET_LEVEL = "L2"
CONTRACT_VERSION = "A-026.7.L1L2"

CONTRACT_STATUS = "FOUNDATION_CONTRACT_READY"
NEXT_MATURITY_GAP = "deterministic_service_logic_needed"

ALLOWED_ACTIONS = [
    "VALIDATE_TENANT",
    "READ_FOUNDATION_CONTRACT",
    "ASSESS_FOUNDATION_READINESS",
]

FORBIDDEN_ACTIONS = [
    "CREATE_API_ENDPOINT",
    "CREATE_FRONTEND_PAGE",
    "COMPUTE_KPI_VALUE",
    "MAP_BRAIN_SIGNAL",
    "EXECUTE_AUTONOMOUS_ACTION",
    "CALL_EXTERNAL_PROVIDER",
    "MUTATE_DATABASE",
    "PUBLISH_EVENT",
]

REQUIRED_EVIDENCE = [
    "service_contract_defined",
    "tenant_fail_closed_validation",
    "deterministic_contract_output",
    "anti_inflation_safety_flags",
]

SAFETY_FLAGS = {
    "no_api_claim": True,
    "no_frontend_claim": True,
    "no_kpi_claim": True,
    "no_brain_claim": True,
    "no_autonomous_execution": True,
    "no_external_provider_call": True,
    "no_l3_claim": True,
    "no_l4_claim": True,
    "no_l5_claim": True,
    "no_l6_claim": True,
}


def validate_tenant_id(tenant_id: Any) -> int:
    """Fail-closed tenant validator for L2 foundation contracts."""
    if tenant_id is None:
        raise ValueError("tenant_id is required")
    if not isinstance(tenant_id, int):
        raise ValueError("tenant_id must be an integer")
    if tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")
    return tenant_id


def get_internship_marketplace_foundation_contract(
    tenant_id: int,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a deterministic L2 foundation service contract for this module."""
    normalized_tenant_id = validate_tenant_id(tenant_id)
    normalized_payload = dict(payload) if isinstance(payload, Mapping) else {}

    return {
        "tenant_id": normalized_tenant_id,
        "module": MODULE_NAME,
        "maturity_level": TARGET_LEVEL,
        "contract_version": CONTRACT_VERSION,
        "contract_status": CONTRACT_STATUS,
        "service_contract_ready": True,
        "tenant_scoped": True,
        "deterministic": True,
        "allowed_actions": list(ALLOWED_ACTIONS),
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "required_evidence": list(REQUIRED_EVIDENCE),
        "next_maturity_gap": NEXT_MATURITY_GAP,
        "payload_keys": sorted(normalized_payload.keys()),
        "safety_flags": dict(SAFETY_FLAGS),
    }


def evaluate_internship_marketplace_readiness(tenant_id: int, internship_payload: dict | None = None) -> dict[str, Any]:
    """Evaluate deterministic L3 readiness for internship_marketplace."""
    normalized_tenant_id = validate_tenant_id(tenant_id)
    payload = internship_payload if isinstance(internship_payload, dict) else {}

    base_required_evidence = ['internship_request_id', 'student_id', 'employer_id']
    missing_required = [key for key in base_required_evidence if payload.get(key) in (None, '', [], {})]

    allowed_actions = ['REVIEW_INTERNSHIP_OPPORTUNITY', 'REQUEST_EMPLOYER_EVIDENCE', 'REQUEST_STUDENT_ELIGIBILITY_EVIDENCE', 'MARK_FOR_MANUAL_MATCHING']
    forbidden_actions = ['AUTO_MATCH_STUDENT', 'AUTO_APPROVE_EMPLOYER', 'AUTO_ASSIGN_INTERNSHIP']

    employer_evidence_complete = bool(payload.get('employer_evidence_complete'))
    student_eligibility_complete = bool(payload.get('student_eligibility_complete'))
    manual_matching_requested = bool(payload.get('manual_matching_requested'))

    if missing_required:
        classification = 'INTERNSHIP_INPUT_INCOMPLETE'
        readiness_level = 'PENDING'
        risk_level = 'MEDIUM'
        next_step = 'COMPLETE_REQUIRED_INTERNSHIP_FIELDS'
        rationale = 'Required internship fields are missing'
    elif not employer_evidence_complete:
        classification = 'EMPLOYER_EVIDENCE_REQUIRED'
        readiness_level = 'BLOCKED'
        risk_level = 'HIGH'
        next_step = 'REQUEST_EMPLOYER_EVIDENCE'
        rationale = 'Employer evidence is required before placement review'
    elif not student_eligibility_complete:
        classification = 'STUDENT_ELIGIBILITY_REVIEW_REQUIRED'
        readiness_level = 'PENDING'
        risk_level = 'HIGH'
        next_step = 'REQUEST_STUDENT_ELIGIBILITY_EVIDENCE'
        rationale = 'Student eligibility evidence is required for deterministic matching review'
    elif manual_matching_requested:
        classification = 'READY_FOR_MANUAL_MATCHING_REVIEW'
        readiness_level = 'READY'
        risk_level = 'LOW'
        next_step = 'MARK_FOR_MANUAL_MATCHING'
        rationale = 'Internship request is complete for manual matching review'
    else:
        classification = 'READY_FOR_PLACEMENT_REVIEW'
        readiness_level = 'READY'
        risk_level = 'LOW'
        next_step = 'REVIEW_INTERNSHIP_OPPORTUNITY'
        rationale = 'Internship request evidence is complete for deterministic placement review'

    l3_safety_flags = {
        **SAFETY_FLAGS,
        'tenant_scoped': True,
        'deterministic': True,
        'no_api_claim': True,
        'no_frontend_claim': True,
        'no_kpi_claim': True,
        'no_brain_claim': True,
        'no_autonomous_execution': True,
        'no_external_provider_call': True,
        'no_l4_claim': True,
        'no_l5_claim': True,
        'no_l6_claim': True,
    }

    required_evidence = list(base_required_evidence)

    return {
        'tenant_id': normalized_tenant_id,
        'module': MODULE_NAME,
        'maturity_level': 'L3',
        'evaluation_status': 'EVALUATED',
        'classification': classification,
        'readiness_level': readiness_level,
        'risk_level': risk_level,
        'required_evidence': required_evidence,
        'missing_required_evidence': missing_required,
        'allowed_actions': list(allowed_actions),
        'forbidden_actions': list(forbidden_actions),
        'human_review_required': True,
        'next_recommended_step': next_step,
        'rationale_notes': rationale,
        'safety_flags': l3_safety_flags,
    }
