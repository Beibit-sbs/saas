"""L2 foundation service contract for digital_certificates (A-026.7.L1L2)."""

from typing import Any, Mapping

MODULE_NAME = "digital_certificates"
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


def get_digital_certificates_foundation_contract(
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


def evaluate_digital_certificate_readiness(tenant_id: int, certificate_payload: dict | None = None) -> dict[str, Any]:
    """Evaluate deterministic L3 readiness for digital_certificates."""
    normalized_tenant_id = validate_tenant_id(tenant_id)
    payload = certificate_payload if isinstance(certificate_payload, dict) else {}

    base_required_evidence = ['request_id', 'student_id', 'program_id']
    missing_required = [key for key in base_required_evidence if payload.get(key) in (None, '', [], {})]

    allowed_actions = ['REVIEW_CERTIFICATE_REQUEST', 'REQUEST_IDENTITY_EVIDENCE', 'REQUEST_ACADEMIC_EVIDENCE', 'MARK_READY_FOR_MANUAL_ISSUANCE']
    forbidden_actions = ['AUTO_ISSUE_CERTIFICATE', 'AUTO_SIGN_CERTIFICATE', 'AUTO_PUBLISH_CERTIFICATE']

    identity_ok = bool(payload.get('identity_evidence_complete'))
    academic_ok = bool(payload.get('academic_evidence_complete'))
    manual_issuance_requested = bool(payload.get('manual_issuance_requested'))

    if missing_required:
        classification = 'CERTIFICATE_INPUT_INCOMPLETE'
        readiness_level = 'PENDING'
        risk_level = 'MEDIUM'
        next_step = 'COMPLETE_REQUIRED_CERTIFICATE_FIELDS'
        rationale = 'Required certificate input fields are missing'
    elif not identity_ok:
        classification = 'BLOCKED_MISSING_IDENTITY_EVIDENCE'
        readiness_level = 'BLOCKED'
        risk_level = 'HIGH'
        next_step = 'REQUEST_IDENTITY_EVIDENCE'
        rationale = 'Identity evidence is required before manual issuance review'
    elif not academic_ok:
        classification = 'BLOCKED_MISSING_ACADEMIC_EVIDENCE'
        readiness_level = 'BLOCKED'
        risk_level = 'HIGH'
        next_step = 'REQUEST_ACADEMIC_EVIDENCE'
        rationale = 'Academic evidence is required before certificate preparation'
    elif manual_issuance_requested:
        classification = 'READY_FOR_MANUAL_ISSUANCE_REVIEW'
        readiness_level = 'READY'
        risk_level = 'LOW'
        next_step = 'MARK_READY_FOR_MANUAL_ISSUANCE'
        rationale = 'Certificate request is complete and ready for human issuance review'
    else:
        classification = 'READY_FOR_DIGITAL_CERTIFICATE_PREPARATION'
        readiness_level = 'READY'
        risk_level = 'LOW'
        next_step = 'REVIEW_CERTIFICATE_REQUEST'
        rationale = 'Certificate request is complete and ready for deterministic preparation checks'

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
