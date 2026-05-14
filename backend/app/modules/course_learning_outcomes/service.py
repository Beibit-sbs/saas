"""Course Learning Outcomes Foundation Service Contract - A-027.2 L2."""

MODULE_NAME = "course_learning_outcomes"
UCE_ID = "UCE-072"
TARGET_LEVEL = "L2"
EXPANSION_LAYER = "university_completeness"
A02710_L3_READY = True
MATURITY_LEVEL = "L3"
HUMAN_REVIEW_REQUIRED = True
L2_CONTRACT_PRESERVED = True


def get_course_learning_outcomes_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """
    Return L2 foundation contract for course learning outcomes.

    Tenant validation:
    - None/0/-1 rejected
    - positive int accepted

    Course-level outcomes definitions. No enforcement, deterministic only.
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
            "ALIGNMENT_REVIEW",
            "ASSESSMENT_MAPPING_REVIEW",
            "APPROVED_MANUAL",
        ],
        "allowed_actions": [
            "CREATE_CLO",
            "DEFINE_OUTCOME_STATEMENT",
            "LINK_TO_PLO",
            "SUBMIT_FOR_ALIGNMENT_REVIEW",
            "SUBMIT_FOR_ASSESSMENT_MAPPING",
            "APPROVE_CLO",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_CLO",
            "AUTO_CHANGE_ASSESSMENT_MAPPING",
            "AUTO_DELETE_CLO",
            "AUTO_PUBLISH_CLO",
        ],
        "required_evidence": [
            "clo_id",
            "course_id",
            "outcome_statement",
        ],
        "next_maturity_gap": "L3 deterministic logic: PLO mapping validation, assessment rubric workflow",
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


def classify_course_learning_outcomes_readiness(
    tenant_id: int, present_evidence: list[str] | set[str] | tuple[str, ...] | None = None
) -> dict:
    tenant_id = _validate_l3_tenant_id(tenant_id)
    evidence_set = _normalize_present_evidence(present_evidence)

    required_evidence = [
        "course_outcome_defined",
        "plo_mapping_documented",
        "assessment_rubric_defined",
        "faculty_review_recorded",
        "quality_assurance_review_required",
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
            "CLO_READINESS_CLASSIFICATION",
            "MISSING_EVIDENCE_IDENTIFICATION",
            "HUMAN_REVIEW_PREPARATION",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_CLO",
            "AUTO_CHANGE_ASSESSMENT_MAPPING",
            "AUTO_PUBLISH_COURSE_OUTCOME",
            "AUTO_ENFORCE_POLICY",
            "MUTATE_ACADEMIC_RECORD",
        ],
        "l2_contract_preserved": L2_CONTRACT_PRESERVED,
        "tenant_scoped": True,
        "next_maturity_gap": "L4 operational visibility/API surface required",
        "safety_flags": _build_safety_flags(),
    }


def get_course_learning_outcomes_l4_visibility_summary(tenant_id: int, evidence: dict | None = None) -> dict:
    """
    L4 read-only visibility summary for course learning outcomes.

    Wraps L3 deterministic readiness with L4 visibility surface.
    No mutations, no provider calls, no fake KPI, no L5/L6 claims.
    Tenant-safe fail-closed behavior.
    """
    if not tenant_id or tenant_id <= 0:
        raise ValueError(f"invalid_tenant_id: {tenant_id}")

    l3_readiness = classify_course_learning_outcomes_readiness(tenant_id, evidence)

    return {
        "tenant_id": tenant_id,
        "module": MODULE_NAME,
        "uce_id": UCE_ID,
        "visibility_level": "L4",
        "source_maturity_level": "L3",
        "visibility_type": "READ_ONLY_SERVICE_SUMMARY",
        "expansion_layer": EXPANSION_LAYER,
        "readiness_summary": {
            "status": l3_readiness.get("readiness_status"),
            "risk_band": l3_readiness.get("risk_band"),
            "evidence_completeness": l3_readiness.get("evidence_completeness"),
        },
        "risk_summary": {
            "risk_band": l3_readiness.get("risk_band"),
            "missing_evidence": l3_readiness.get("missing_evidence"),
            "required_next_step": l3_readiness.get("recommended_next_step"),
        },
        "evidence_summary": {
            "required": l3_readiness.get("required_evidence"),
            "present": l3_readiness.get("present_evidence"),
            "missing": l3_readiness.get("missing_evidence"),
        },
        "missing_evidence_summary": l3_readiness.get("missing_evidence"),
        "human_review_queue_summary": "REVIEW_READINESS_CLASSIFICATION" if l3_readiness.get("human_review_required") else None,
        "allowed_actions": l3_readiness.get("allowed_actions"),
        "forbidden_actions": l3_readiness.get("forbidden_actions"),
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
        "no_l5_claim": True,
        "no_l6_claim": True,
        "l3_contract_preserved": True,
        "api_route_deferred_to": "A-028.7",
        "deterministic": True,
        "created_at_action_id": "A-028.6-RUNTIME",
    }
