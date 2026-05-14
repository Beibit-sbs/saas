"""Staff Recruitment Foundation Service Contract - A-027.2 L2."""

MODULE_NAME = "staff_recruitment"
UCE_ID = "UCE-001"
TARGET_LEVEL = "L2"
EXPANSION_LAYER = "university_completeness"


def get_staff_recruitment_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """
    Return L2 foundation contract for staff recruitment.
    
    Tenant validation:
    - None/0/-1 rejected
    - positive int accepted
    
    No provider calls, no autonomy, deterministic only.
    """
    
    # Tenant fail-closed validation
    if not tenant_id or tenant_id <= 0:
        raise ValueError(f"invalid_tenant_id: {tenant_id}")
    
    return {
        "tenant_id": tenant_id,
        "module": MODULE_NAME,
        "uce_id": UCE_ID,
        "maturity_level": "L2",
        "expansion_layer": EXPANSION_LAYER,
        "contract_status": "FOUNDATION_READY",
        "service_contract_ready": True,
        "tenant_scoped": True,
        "deterministic": True,
        "lifecycle_statuses": [
            "DRAFT",
            "SCREENING",
            "INTERVIEW",
            "OFFER_REVIEW",
            "CLOSED",
        ],
        "allowed_actions": [
            "CREATE_RECRUITMENT_REQUEST",
            "ADD_SCREENING_NOTES",
            "RECORD_INTERVIEW",
            "SUBMIT_OFFER_FOR_REVIEW",
            "CLOSE_RECRUITMENT",
        ],
        "forbidden_actions": [
            "AUTO_HIRE",
            "AUTO_REJECT_CANDIDATE",
            "AUTO_APPROVE_OFFER",
            "AUTO_SEND_OFFER_LETTER",
        ],
        "required_evidence": [
            "recruitment_request_id",
            "candidate_profile",
            "screening_criteria",
        ],
        "next_maturity_gap": "L3 deterministic logic: candidate qualification scoring, screening workflow",
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
            "no_l6_claim": True,
        },
    }


# A-027.11 deterministic L3 readiness overlay constants
A02711_L3_READY = True
MATURITY_LEVEL = "L3"
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
    "vacancy_request_present",
    "position_profile_available",
    "hiring_committee_review_required",
    "candidate_evidence_policy_available",
    "human_hr_review_required",
]
A02711_MIN_COMPLETENESS_THRESHOLD = 60

A02711_ALLOWED_ACTIONS = [
    "RECRUITMENT_READINESS_CLASSIFICATION",
    "MISSING_EVIDENCE_IDENTIFICATION",
    "HUMAN_REVIEW_PREPARATION",
]

A02711_FORBIDDEN_ACTIONS = [
    "AUTO_HIRE_CANDIDATE",
    "AUTO_REJECT_CANDIDATE",
    "AUTO_RANK_CANDIDATE",
    "AUTO_SCORE_CANDIDATE",
    "AUTO_CREATE_EMPLOYMENT_CONTRACT",
    "MUTATE_HR_RECORD",
]


def _validate_tenant_id_l3(tenant_id: int) -> int:
    if tenant_id is None:
        raise ValueError("invalid_tenant_id: None")
    if not isinstance(tenant_id, int):
        raise ValueError("invalid_tenant_id_type")
    if tenant_id <= 0:
        raise ValueError(f"invalid_tenant_id: {tenant_id}")
    return tenant_id


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


def classify_staff_recruitment_readiness(
    tenant_id: int,
    present_evidence: list[str] | set[str] | None = None,
) -> dict:
    """Deterministic L3 readiness classification for UCE-001 without hiring decisions."""
    tenant_id = _validate_tenant_id_l3(tenant_id)
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


# A-028.9 L4 Visibility Summary - UCE-001 staff_recruitment

def _build_staff_recruitment_l4_visibility_summary(l3_output: dict) -> dict:
    """Build L4 visibility wrapper for staff recruitment L3 readiness."""
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


def get_staff_recruitment_l4_visibility_summary(
    tenant_id: int, present_evidence: list[str] | set[str] | dict | None = None
) -> dict:
    """L4 read-only visibility summary for staff recruitment (UCE-001)."""
    tenant_id = _validate_tenant_id_l3(tenant_id)
    evidence = present_evidence if isinstance(present_evidence, dict) else present_evidence
    l3_output = classify_staff_recruitment_readiness(
        tenant_id=tenant_id,
        present_evidence=evidence if isinstance(evidence, (list, set)) else None,
    )
    return _build_staff_recruitment_l4_visibility_summary(l3_output)
