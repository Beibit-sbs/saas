"""L2 foundation service contract for research_projects (A-026.7.L1L2)."""

from typing import Any, Mapping

MODULE_NAME = "research_projects"
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


def get_research_projects_foundation_contract(
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


def evaluate_research_project_readiness(tenant_id: int, project_payload: dict | None = None) -> dict[str, Any]:
    """Evaluate deterministic L3 readiness for research_projects."""
    normalized_tenant_id = validate_tenant_id(tenant_id)
    payload = project_payload if isinstance(project_payload, dict) else {}

    base_required_evidence = ['project_id', 'project_owner', 'scope_summary']
    missing_required = [key for key in base_required_evidence if payload.get(key) in (None, '', [], {})]

    allowed_actions = ['REVIEW_PROJECT', 'REQUEST_ETHICS_EVIDENCE', 'REQUEST_BUDGET_EVIDENCE', 'ESCALATE_SCOPE_REVIEW']
    forbidden_actions = ['AUTO_APPROVE_PROJECT', 'AUTO_ALLOCATE_BUDGET', 'AUTO_START_PROJECT']

    ethics_evidence_complete = bool(payload.get('ethics_evidence_complete'))
    budget_evidence_complete = bool(payload.get('budget_evidence_complete'))
    scope_review_required = bool(payload.get('scope_review_required'))

    if missing_required:
        classification = 'PROJECT_INPUT_INCOMPLETE'
        readiness_level = 'PENDING'
        risk_level = 'MEDIUM'
        next_step = 'COMPLETE_REQUIRED_PROJECT_FIELDS'
        rationale = 'Required project fields are missing'
    elif not ethics_evidence_complete:
        classification = 'ETHICS_EVIDENCE_REQUIRED'
        readiness_level = 'BLOCKED'
        risk_level = 'HIGH'
        next_step = 'REQUEST_ETHICS_EVIDENCE'
        rationale = 'Ethics evidence is required before project review'
    elif not budget_evidence_complete or scope_review_required:
        classification = 'BUDGET_SCOPE_REVIEW_REQUIRED'
        readiness_level = 'PENDING'
        risk_level = 'HIGH'
        next_step = 'ESCALATE_SCOPE_REVIEW'
        rationale = 'Budget/scope review is required for deterministic project readiness'
    elif bool(payload.get('manual_activation_requested')):
        classification = 'READY_FOR_MANUAL_PROJECT_ACTIVATION'
        readiness_level = 'READY'
        risk_level = 'LOW'
        next_step = 'REVIEW_PROJECT'
        rationale = 'Project is complete for manual activation review'
    else:
        classification = 'READY_FOR_RESEARCH_REVIEW'
        readiness_level = 'READY'
        risk_level = 'LOW'
        next_step = 'REVIEW_PROJECT'
        rationale = 'Project evidence is complete for deterministic research review'

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
