"""L2 foundation service contract for publication_registry (A-026.7.L1L2)."""

from typing import Any, Mapping

MODULE_NAME = "publication_registry"
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


def get_publication_registry_foundation_contract(
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


def evaluate_publication_registry_readiness(tenant_id: int, publication_payload: dict | None = None) -> dict[str, Any]:
    """Evaluate deterministic L3 readiness for publication_registry."""
    normalized_tenant_id = validate_tenant_id(tenant_id)
    payload = publication_payload if isinstance(publication_payload, dict) else {}

    base_required_evidence = ['publication_id', 'author_id', 'publication_type']
    missing_required = [key for key in base_required_evidence if payload.get(key) in (None, '', [], {})]

    allowed_actions = ['REVIEW_PUBLICATION', 'REQUEST_AUTHORSHIP_EVIDENCE', 'REQUEST_INDEXING_EVIDENCE', 'MARK_READY_FOR_REGISTRATION']
    forbidden_actions = ['AUTO_REGISTER_PUBLICATION', 'AUTO_SCORE_PUBLICATION', 'AUTO_APPROVE_RESEARCH_OUTPUT']

    authorship_evidence_complete = bool(payload.get('authorship_evidence_complete'))
    indexing_evidence_complete = bool(payload.get('indexing_evidence_complete'))
    manual_registration_requested = bool(payload.get('manual_registration_requested'))

    if missing_required:
        classification = 'PUBLICATION_INPUT_INCOMPLETE'
        readiness_level = 'PENDING'
        risk_level = 'MEDIUM'
        next_step = 'COMPLETE_REQUIRED_PUBLICATION_FIELDS'
        rationale = 'Required publication fields are missing'
    elif not authorship_evidence_complete:
        classification = 'AUTHORSHIP_EVIDENCE_REQUIRED'
        readiness_level = 'BLOCKED'
        risk_level = 'HIGH'
        next_step = 'REQUEST_AUTHORSHIP_EVIDENCE'
        rationale = 'Authorship evidence is required before manual registration'
    elif not indexing_evidence_complete:
        classification = 'INDEXING_EVIDENCE_REQUIRED'
        readiness_level = 'BLOCKED'
        risk_level = 'HIGH'
        next_step = 'REQUEST_INDEXING_EVIDENCE'
        rationale = 'Indexing evidence is required before publication registry review'
    elif manual_registration_requested:
        classification = 'READY_FOR_MANUAL_REGISTRATION'
        readiness_level = 'READY'
        risk_level = 'LOW'
        next_step = 'MARK_READY_FOR_REGISTRATION'
        rationale = 'Publication is complete for manual registration'
    else:
        classification = 'READY_FOR_REGISTRY_REVIEW'
        readiness_level = 'READY'
        risk_level = 'LOW'
        next_step = 'REVIEW_PUBLICATION'
        rationale = 'Publication evidence is complete for deterministic registry review'

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
