"""International Office Foundation Service Contract - A-027.2 L2."""

MODULE_NAME = "international_office"
UCE_ID = "UCE-019"
TARGET_LEVEL = "L2"
EXPANSION_LAYER = "university_completeness"
A02710_L3_READY = True
MATURITY_LEVEL = "L3"
HUMAN_REVIEW_REQUIRED = True
L2_CONTRACT_PRESERVED = True


def get_international_office_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """
    Return L2 foundation contract for international office.
    
    Tenant validation:
    - None/0/-1 rejected
    - positive int accepted
    
    Manages international student operations. No visa authority, deterministic only.
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
            "REQUESTED",
            "DOCUMENT_REVIEW",
            "PARTNER_REVIEW",
            "APPROVED_MANUAL",
            "CLOSED",
        ],
        "allowed_actions": [
            "CREATE_MOBILITY_REQUEST",
            "SUBMIT_DOCUMENTS",
            "NOTIFY_PARTNER",
            "APPROVE_MOBILITY",
            "CLOSE_REQUEST",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_MOBILITY",
            "AUTO_ISSUE_VISA_DECISION",
            "AUTO_CONFIRM_PARTNERSHIP",
            "AUTO_GRANT_VISA",
        ],
        "required_evidence": [
            "request_id",
            "student_profile",
            "destination_country",
        ],
        "next_maturity_gap": "L3 deterministic logic: visa requirement validation, partner agreement workflow",
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


def _validate_l3_tenant_id(tenant_id: int) -> int:
    if tenant_id is None:
        raise ValueError("tenant_id cannot be None")
    if not isinstance(tenant_id, int):
        raise TypeError(f"tenant_id must be int, got {type(tenant_id)}")
    if tenant_id <= 0:
        raise ValueError(f"tenant_id must be positive, got {tenant_id}")
    return tenant_id


def _normalize_present_evidence(present_evidence: list[str] | set[str] | tuple[str, ...] | None) -> set[str]:
    if present_evidence is None:
        return set()
    if isinstance(present_evidence, (list, set, tuple)):
        return {str(item) for item in present_evidence if item}
    raise TypeError("present_evidence must be list[str], set[str], tuple[str, ...], or None")


def _build_safety_flags() -> dict:
    return {
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
        "human_review_required": True,
        "no_l4_claim": True,
        "no_l5_claim": True,
        "no_l6_claim": True,
        "tenant_fail_closed": True,
        "l2_contract_preserved": True,
    }


def classify_international_office_readiness(
    tenant_id: int, present_evidence: list[str] | set[str] | tuple[str, ...] | None = None
) -> dict:
    tenant_id = _validate_l3_tenant_id(tenant_id)
    evidence_set = _normalize_present_evidence(present_evidence)

    required_evidence = [
        "mobility_request_documented",
        "visa_requirements_checked",
        "partner_agreement_verified",
        "student_profile_validated",
        "country_compliance_review_required",
    ]

    present = [item for item in required_evidence if item in evidence_set]
    missing = [item for item in required_evidence if item not in evidence_set]
    total = len(required_evidence)
    present_count = len(present)
    evidence_completeness = int(round((present_count / total) * 100)) if total else 0
    threshold = max(1, total // 2)

    if present_count == total:
        readiness_status = "READY_FOR_REVIEW"
        risk_band = "LOW"
        recommended_next_step = "READY_FOR_HUMAN_REVIEW"
    elif present_count == 0:
        readiness_status = "BLOCKED_MISSING_EVIDENCE"
        risk_band = "BLOCKED"
        recommended_next_step = "BLOCK_UNTIL_REQUIRED_EVIDENCE_PRESENT"
    elif present_count < threshold:
        readiness_status = "INCOMPLETE_EVIDENCE"
        risk_band = "HIGH"
        recommended_next_step = "REQUEST_MISSING_EVIDENCE"
    else:
        readiness_status = "PARTIAL_EVIDENCE"
        risk_band = "MEDIUM"
        recommended_next_step = "REQUEST_MISSING_EVIDENCE"

    return {
        "tenant_id": tenant_id,
        "module": MODULE_NAME,
        "uce_id": UCE_ID,
        "maturity_level": MATURITY_LEVEL,
        "expansion_layer": EXPANSION_LAYER,
        "deterministic_logic_ready": A02710_L3_READY,
        "readiness_status": readiness_status,
        "risk_band": risk_band,
        "evidence_completeness": evidence_completeness,
        "required_evidence": required_evidence,
        "present_evidence": present,
        "missing_evidence": missing,
        "recommended_next_step": recommended_next_step,
        "human_review_required": HUMAN_REVIEW_REQUIRED,
        "allowed_actions": [
            "INTERNATIONAL_CASE_READINESS_CLASSIFICATION",
            "MISSING_EVIDENCE_IDENTIFICATION",
            "HUMAN_REVIEW_PREPARATION",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_MOBILITY",
            "AUTO_ISSUE_VISA_DECISION",
            "AUTO_CONFIRM_PARTNERSHIP",
            "AUTO_GRANT_VISA",
            "MUTATE_STUDENT_STATUS",
        ],
        "l2_contract_preserved": L2_CONTRACT_PRESERVED,
        "tenant_scoped": True,
        "next_maturity_gap": "L4 operational visibility/API surface required",
        "safety_flags": _build_safety_flags(),
    }
