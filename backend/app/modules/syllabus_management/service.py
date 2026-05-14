"""Syllabus Management Foundation Service Contract - A-027.2 L2."""

MODULE_NAME = "syllabus_management"
UCE_ID = "UCE-015"
TARGET_LEVEL = "L2"
EXPANSION_LAYER = "university_completeness"


def validate_tenant_id(tenant_id: int) -> int:
    if not tenant_id or tenant_id <= 0:
        raise ValueError(f"invalid_tenant_id: {tenant_id}")
    return tenant_id


def get_syllabus_management_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """
    Return L2 foundation contract for syllabus management.

    Tenant validation:
    - None/0/-1 rejected
    - positive int accepted

    Manages syllabus lifecycle. No publication automation, deterministic only.
    """

    validate_tenant_id(tenant_id)

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
            "DEPARTMENT_REVIEW",
            "QUALITY_REVIEW",
            "APPROVED_MANUAL",
            "ARCHIVED",
        ],
        "allowed_actions": [
            "CREATE_SYLLABUS",
            "SUBMIT_FOR_DEPARTMENT_REVIEW",
            "SUBMIT_FOR_QUALITY_REVIEW",
            "APPROVE_SYLLABUS",
            "ARCHIVE_SYLLABUS",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_SYLLABUS",
            "AUTO_PUBLISH_SYLLABUS",
            "AUTO_CHANGE_COURSE_POLICY",
            "AUTO_DELETE_SYLLABUS",
        ],
        "required_evidence": [
            "syllabus_id",
            "course_id",
            "academic_term",
        ],
        "next_maturity_gap": "L3 deterministic logic: policy compliance checking, quality metrics validation",
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


def classify_syllabus_management_readiness(tenant_id: int, evidence: dict | None = None) -> dict:
    validate_tenant_id(tenant_id)
    required_evidence = ["syllabus_content", "learning_outcomes", "department_review"]
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
        recommended_next_step = "COLLECT_REQUIRED_EVIDENCE"
    else:
        readiness_status = "BLOCKED_MISSING_EVIDENCE"
        risk_band = "BLOCKED"
        recommended_next_step = "BLOCK_UNTIL_REQUIRED_EVIDENCE_PRESENT"

    return {
        "tenant_id": tenant_id,
        "module": MODULE_NAME,
        "uce_id": UCE_ID,
        "maturity_level": "L3",
        "expansion_layer": EXPANSION_LAYER,
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
            "AUTO_APPROVE_SYLLABUS",
            "AUTO_CHANGE_ASSESSMENT_RULES",
            "AUTO_PUBLISH_SYLLABUS",
        ],
        "l2_contract_preserved": True,
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
            "no_l4_claim": True,
            "no_l5_claim": True,
            "no_l6_claim": True,
        },
    }


def get_syllabus_management_l4_visibility_summary(tenant_id: int, evidence: dict | None = None) -> dict:
    """
    L4 read-only visibility summary for syllabus management.

    Wraps L3 deterministic readiness with L4 visibility surface.
    No mutations, no provider calls, no fake KPI, no L5/L6 claims.
    Tenant-safe fail-closed behavior.
    """
    validate_tenant_id(tenant_id)

    l3_readiness = classify_syllabus_management_readiness(tenant_id, evidence)

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
