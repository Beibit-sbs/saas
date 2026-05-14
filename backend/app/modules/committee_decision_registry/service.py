"""Committee Decision Registry Foundation Service Contract - A-027.2 L2."""

MODULE_NAME = "committee_decision_registry"
UCE_ID = "UCE-090"
TARGET_LEVEL = "L2"
EXPANSION_LAYER = "university_completeness"
A02710_L3_READY = True
MATURITY_LEVEL = "L3"
HUMAN_REVIEW_REQUIRED = True
L2_CONTRACT_PRESERVED = True


def get_committee_decision_registry_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """
    Return L2 foundation contract for committee decision registry.
    
    Tenant validation:
    - None/0/-1 rejected
    - positive int accepted
    
    Records formal committee decisions. No autonomous recording, deterministic only.
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
            "MEETING_REVIEW",
            "DECISION_RECORDED",
            "SIGNATURE_PENDING",
            "ARCHIVED",
        ],
        "allowed_actions": [
            "RECORD_DECISION",
            "DOCUMENT_MEETING_OUTCOMES",
            "PREPARE_MINUTES",
            "REQUEST_SIGNATURES",
            "ARCHIVE_DECISION",
        ],
        "forbidden_actions": [
            "AUTO_RECORD_DECISION",
            "AUTO_APPROVE_MINUTES",
            "AUTO_SIGN_PROTOCOL",
            "AUTO_PUBLISH_DECISION",
        ],
        "required_evidence": [
            "decision_id",
            "committee_id",
            "meeting_date",
        ],
        "next_maturity_gap": "L3 deterministic logic: decision lineage tracking, escalation workflows, evidence audit",
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


def classify_committee_decision_registry_readiness(
    tenant_id: int, present_evidence: list[str] | set[str] | tuple[str, ...] | None = None
) -> dict:
    tenant_id = _validate_l3_tenant_id(tenant_id)
    evidence_set = _normalize_present_evidence(present_evidence)

    required_evidence = [
        "committee_agenda_recorded",
        "decision_rationale_documented",
        "quorum_validation_recorded",
        "meeting_minutes_prepared",
        "signature_workflow_defined",
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
            "COMMITTEE_DECISION_READINESS_CLASSIFICATION",
            "MISSING_EVIDENCE_IDENTIFICATION",
            "HUMAN_REVIEW_PREPARATION",
        ],
        "forbidden_actions": [
            "AUTO_RECORD_DECISION",
            "AUTO_APPROVE_MINUTES",
            "AUTO_SIGN_PROTOCOL",
            "AUTO_PUBLISH_DECISION",
            "MUTATE_GOVERNANCE_RECORD",
        ],
        "l2_contract_preserved": L2_CONTRACT_PRESERVED,
        "tenant_scoped": True,
        "next_maturity_gap": "L4 operational visibility/API surface required",
        "safety_flags": _build_safety_flags(),
    }


def _build_committee_decision_registry_l4_visibility_summary(l3_output: dict) -> dict:
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
        "source_l3_function": "classify_committee_decision_registry_readiness",
        "visibility_type": "committee_decision_registry_review_queue_summary",
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
            **_build_safety_flags(),
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


def get_committee_decision_registry_l4_visibility_summary(
    tenant_id: int, present_evidence: list[str] | set[str] | tuple[str, ...] | None = None
) -> dict:
    l3_output = classify_committee_decision_registry_readiness(tenant_id=tenant_id, present_evidence=present_evidence)
    return _build_committee_decision_registry_l4_visibility_summary(l3_output)
