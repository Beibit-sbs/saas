"""
document_template_library service.py — L2 Foundation Contract
"""

MODULE_NAME = "document_template_library"
UCE_ID = "UCE-089"
TARGET_LEVEL = "L2"
CONTRACT_VERSION = "A-027.4"
FOUNDATION_STATUS = "FOUNDATION_READY"

LIFECYCLE_STATUSES = ["TEMPLATE_DRAFT", "OWNER_REVIEW", "LEGAL_REVIEW", "APPROVED_MANUAL", "ARCHIVED"]
ALLOWED_ACTIONS = ["REVIEW_TEMPLATE", "REQUEST_LEGAL_EVIDENCE", "MARK_READY_FOR_TEMPLATE_APPROVAL"]
FORBIDDEN_ACTIONS = ["AUTO_APPROVE_TEMPLATE", "AUTO_PUBLISH_TEMPLATE", "AUTO_DELETE_TEMPLATE"]
REQUIRED_EVIDENCE = ["template_content", "owner_review", "legal_review"]

SAFETY_FLAGS = {
    "no_api_claim": True, "no_frontend_claim": True, "no_live_integration_claim": True,
    "no_provider_call": True, "no_kpi_claim": True, "no_brain_claim": True,
    "no_autonomous_execution": True, "no_external_side_effects": True,
    "no_l3_claim": True, "no_l4_claim": True, "no_l5_claim": True, "no_l6_claim": True,
}

def validate_tenant_id(tenant_id):
    if tenant_id is None:
        raise ValueError("tenant_id cannot be None")
    if not isinstance(tenant_id, int):
        raise TypeError(f"tenant_id must be int, got {type(tenant_id)}")
    if tenant_id <= 0:
        raise ValueError(f"tenant_id must be positive, got {tenant_id}")
    return tenant_id

def get_document_template_library_foundation_contract(tenant_id, payload=None):
    tenant_id = validate_tenant_id(tenant_id)
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
        "lifecycle_statuses": LIFECYCLE_STATUSES,
        "allowed_actions": ALLOWED_ACTIONS,
        "forbidden_actions": FORBIDDEN_ACTIONS,
        "required_evidence": REQUIRED_EVIDENCE,
        "next_maturity_gap": "L3 deterministic logic required",
        "sensitive_boundary": {
            "no_automatic_template_approval": True,
            "no_automatic_template_publication": True,
            "no_automatic_template_deletion": True,
        },
        "safety_flags": SAFETY_FLAGS,
    }


def classify_document_template_library_readiness(tenant_id: int, evidence: dict | None = None) -> dict:
    tenant_id = validate_tenant_id(tenant_id)
    required_evidence = ["template_content", "owner_review", "legal_review"]
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
            "AUTO_APPROVE_TEMPLATE",
            "AUTO_PUBLISH_TEMPLATE",
            "AUTO_DELETE_TEMPLATE",
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


def _normalize_l4_evidence(present_evidence: list[str] | set[str] | tuple[str, ...] | dict | None) -> dict:
    if present_evidence is None:
        return {}
    if isinstance(present_evidence, dict):
        return {str(key): value for key, value in present_evidence.items() if key}
    if isinstance(present_evidence, (list, set, tuple)):
        return {str(item): True for item in present_evidence if item}
    raise TypeError("present_evidence must be list[str], set[str], tuple[str, ...], dict, or None")


def _build_document_template_library_l4_visibility_summary(l3_output: dict) -> dict:
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
        "source_l3_function": "classify_document_template_library_readiness",
        "visibility_type": "document_template_library_evidence_visibility",
        "readiness_summary": {
            "status": status,
            "evidence_completeness": l3_output.get("evidence_completeness", 0),
            "recommended_next_step": l3_output.get("recommended_next_step"),
            "ready_for_human_review": status == "READY_FOR_REVIEW",
            "summary_count": 1,
        },
        "risk_summary": {
            "risk_band": l3_output.get("risk_band"),
            "summary_count": 1,
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
            "has_missing_evidence": bool(missing_evidence),
        },
        "human_review_queue_summary": {
            "candidate_count": 1 if human_review_required else 0,
            "ready_for_human_review_count": 1 if status == "READY_FOR_REVIEW" else 0,
            "pending_manual_evidence_count": 1 if human_review_required and status not in {"READY_FOR_REVIEW", "BLOCKED_MISSING_EVIDENCE"} else 0,
            "blocked_count": 1 if status == "BLOCKED_MISSING_EVIDENCE" else 0,
        },
        "allowed_actions": list(dict.fromkeys(["VIEW_L4_VISIBILITY_SUMMARY", *list(l3_output.get("allowed_actions", []))])),
        "forbidden_actions": list(dict.fromkeys(list(l3_output.get("forbidden_actions", [])))),
        "tenant_scoped": True,
        "read_only": True,
        "no_mutation": True,
        "no_provider_call": True,
        "no_brain_execution": True,
        "no_autonomous_execution": True,
        "no_decision_execution": True,
        "no_fake_kpi": True,
        "no_synthetic_dashboard": True,
        "l3_contract_preserved": True,
        "audit_visibility_ready": True,
        "human_review_required": human_review_required,
        "source_evidence_keys": required_evidence,
        "no_l5_claim": True,
        "no_l6_claim": True,
        "next_maturity_gap": "L5 governance/KPI/evidence automation required",
        "safety_flags": {
            **dict(l3_output.get("safety_flags", {})),
            "tenant_safe_visibility": True,
            "read_only": True,
            "no_db_mutation": True,
            "no_provider_call": True,
            "no_external_submission": True,
            "no_brain_execution": True,
            "no_autonomous_execution": True,
            "no_workflow_execution": True,
            "no_decision_execution": True,
            "no_fake_kpi": True,
            "no_synthetic_dashboard": True,
            "no_l5_claim": True,
            "no_l6_claim": True,
            "l3_contract_preserved": True,
        },
    }


def get_document_template_library_l4_visibility_summary(
    tenant_id: int, present_evidence: list[str] | set[str] | tuple[str, ...] | dict | None = None
) -> dict:
    tenant_id = validate_tenant_id(tenant_id)
    l3_output = classify_document_template_library_readiness(
        tenant_id=tenant_id,
        evidence=_normalize_l4_evidence(present_evidence),
    )
    return _build_document_template_library_l4_visibility_summary(l3_output)
