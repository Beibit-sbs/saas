"""Mou_Lifecycle L2 Foundation Service Contract (UCE-023)."""

from . import MODULE_NAME, UCE_ID, TARGET_LEVEL, CONTRACT_VERSION, FOUNDATION_STATUS


def validate_tenant_id(tenant_id: int) -> int:
    """Fail-closed tenant validation."""
    if not tenant_id or tenant_id <= 0:
        raise ValueError(f"invalid_tenant_id: {tenant_id}")
    return tenant_id


def get_mou_lifecycle_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """L2 foundation contract for mou_lifecycle. No provider calls, no autonomy, deterministic only."""
    validate_tenant_id(tenant_id)
    
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
        
        "lifecycle_statuses": [
            "DRAFT",
            "PARTNER_REVIEW",
            "LEGAL_REVIEW",
            "SIGNATURE_PENDING",
            "ACTIVE",
            "EXPIRED"
        ],
        
        "allowed_actions": [
            "REVIEW_MOU",
            "REQUEST_LEGAL_EVIDENCE",
            "MARK_READY_FOR_SIGNATURE_REVIEW"
        ],
        
        "forbidden_actions": [
            "NO_AUTO_SIGN_MOU",
            "NO_AUTO_ACTIVATE_PARTNERSHIP",
            "NO_AUTO_TERMINATE_MOU"
        ],
        
        "required_evidence": [
            "mou_draft",
            "partner_approval",
            "legal_review"
        ],
        
        "next_maturity_gap": "L3 deterministic logic: MOU lifecycle management and renewal rules",
        
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
            "no_l6_claim": True
        }
    }


# --- L3 Deterministic Readiness Classifier (A-027.9) ---

A0279_L3_READY = True


def classify_mou_lifecycle_readiness(tenant_id: int, evidence: dict | None = None) -> dict:
    """Deterministic L3 readiness classifier. No decision execution, no autonomy, no provider calls."""
    validate_tenant_id(tenant_id)
    required_evidence = [
        "partner_profile_present",
        "mou_draft_present",
        "legal_review_required",
        "authorized_signatory_identified",
        "renewal_or_expiry_policy_available",
    ]
    evidence = evidence or {}
    present_evidence = [key for key in required_evidence if key in evidence]
    missing_evidence = [key for key in required_evidence if key not in evidence]
    present_count = len(present_evidence)

    if present_count == len(required_evidence):
        readiness_status = "READY_FOR_REVIEW"
        risk_band = "LOW"
        recommended_next_step = "READY_FOR_HUMAN_REVIEW"
    elif present_count >= 3:
        readiness_status = "PARTIAL_EVIDENCE"
        risk_band = "MEDIUM"
        recommended_next_step = "REQUEST_MISSING_EVIDENCE"
    elif present_count >= 1:
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
            "MOU_READINESS_CLASSIFICATION",
            "LEGAL_EVIDENCE_CHECK",
            "HUMAN_REVIEW_PREPARATION",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_MOU",
            "AUTO_SIGN_MOU",
            "AUTO_RENEW_MOU",
            "AUTO_TERMINATE_MOU",
            "MUTATE_LEGAL_RECORD",
        ],
        "l2_contract_preserved": True,
        "tenant_scoped": True,
        "l3_boundary": "module_readiness_only_no_decision_execution_or_automation",
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
            "human_review_required": True,
            "no_l4_claim": True,
            "no_l5_claim": True,
            "no_l6_claim": True,
            "tenant_fail_closed": True,
            "l2_contract_preserved": True,
        },
    }


# A-028.9 L4 Visibility Summary - UCE-023 mou_lifecycle

def _build_mou_lifecycle_l4_visibility_summary(l3_output: dict) -> dict:
    """Build L4 visibility wrapper for mou_lifecycle L3 readiness."""
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


def get_mou_lifecycle_l4_visibility_summary(
    tenant_id: int, present_evidence: list[str] | set[str] | dict | None = None
) -> dict:
    """L4 read-only visibility summary for mou_lifecycle (UCE-023)."""
    tenant_id = validate_tenant_id(tenant_id)
    evidence = present_evidence if isinstance(present_evidence, dict) else present_evidence
    l3_output = classify_mou_lifecycle_readiness(
        tenant_id=tenant_id,
        evidence=present_evidence if isinstance(present_evidence, dict) else None,
    )
    return _build_mou_lifecycle_l4_visibility_summary(l3_output)
