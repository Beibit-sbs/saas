"""Deterministic L2 envelope contract for rector_strategy_dashboard (A-027.6)."""

from __future__ import annotations

MODULE_NAME = "rector_strategy_dashboard"
UCE_ID = "UCE-031"
CANDIDATE_TYPE = "REPORT_DASHBOARD"
TARGET_LEVEL = "L2"
CONTRACT_VERSION = "A-027.6"
ENVELOPE_STATUS = "ENVELOPE_READY"
ENVELOPE_ONLY = True
RUNTIME_EXECUTION_ALLOWED = False
HUMAN_APPROVAL_REQUIRED = True
CONTRACT_KIND = "report_dashboard_contract"
DOMAIN_CONTEXT = "Governance / Rectorate / Strategy"
PURPOSE = "Executive strategy visibility envelope contract"

EVIDENCE_REQUIREMENTS = [
    "governance_policy_reference",
    "tenant_scope_context",
    "human_review_record",
]

ALLOWED_ACTIONS = [
    "DESCRIBE_CONTRACT",
    "VALIDATE_EVIDENCE_REQUIREMENTS",
    "MARK_READY_FOR_HUMAN_REVIEW",
]

FORBIDDEN_ACTIONS = [
    "AUTO_EXECUTE",
    "AUTO_APPROVE",
    "AUTO_SEND",
    "AUTO_ENFORCE",
    "AUTO_MUTATE_RECORD",
    "BRAIN_EXECUTE_DECISION",
    "AUTONOMOUS_DECISION",
]

HUMAN_REVIEW_BOUNDARY = {
    "human_approval_required": True,
    "execution_without_human": False,
    "manual_verification_required": True,
}

TENANT_SECURITY_BOUNDARY = {
    "tenant_scoped": True,
    "cross_tenant_access_allowed": False,
    "tenant_validation_fail_closed": True,
}

BRAIN_BOUNDARY = {
    "brain_execution_allowed": False,
    "recommendation_execution_allowed": False,
    "signal_scoring_allowed": False,
}

AUTONOMY_BOUNDARY = {
    "autonomous_execution_allowed": False,
    "auto_approval_allowed": False,
    "auto_routing_allowed": False,
    "auto_notification_allowed": False,
}

SAFETY_FLAGS = {
    "no_api_claim": True,
    "no_frontend_claim": True,
    "no_db_claim": True,
    "no_kpi_value_claim": True,
    "no_fake_dashboard": True,
    "no_brain_execution": True,
    "no_autonomous_execution": True,
    "human_approval_required": True,
    "no_external_side_effects": True,
    "no_provider_call": True,
    "no_live_notification": True,
    "no_document_signature": True,
    "no_decision_enforcement": True,
    "no_l3_claim": True,
    "no_l4_claim": True,
    "no_l5_claim": True,
    "no_l6_claim": True,
}


def validate_tenant_id(tenant_id: int) -> int:
    """Fail-closed tenant validation for envelope contracts."""
    if tenant_id is None:
        raise ValueError("tenant_id is required")
    if not isinstance(tenant_id, int):
        raise TypeError("tenant_id must be an int")
    if tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")
    return tenant_id


def get_rector_strategy_dashboard_envelope_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """Return deterministic L2 envelope metadata without runtime execution."""
    tenant_id = validate_tenant_id(tenant_id)
    _ = payload

    return {
        "tenant_id": tenant_id,
        "module": MODULE_NAME,
        "uce_id": UCE_ID,
        "candidate_type": CANDIDATE_TYPE,
        "maturity_level": TARGET_LEVEL,
        "expansion_layer": "university_completeness",
        "contract_status": ENVELOPE_STATUS,
        "envelope_only": ENVELOPE_ONLY,
        "runtime_execution_allowed": RUNTIME_EXECUTION_ALLOWED,
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "tenant_scoped": True,
        "deterministic": True,
        "contract_kind": CONTRACT_KIND,
        "purpose": PURPOSE,
        "domain_context": DOMAIN_CONTEXT,
        "evidence_requirements": list(EVIDENCE_REQUIREMENTS),
        "allowed_actions": list(ALLOWED_ACTIONS),
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "human_review_boundary": dict(HUMAN_REVIEW_BOUNDARY),
        "tenant_security_boundary": dict(TENANT_SECURITY_BOUNDARY),
        "brain_boundary": dict(BRAIN_BOUNDARY),
        "autonomy_boundary": dict(AUTONOMY_BOUNDARY),
        "report_scope": {
            "domain": DOMAIN_CONTEXT,
            "view_mode": "contract_only",
            "rendering_enabled": False,
        },
        "evidence_sources": list(EVIDENCE_REQUIREMENTS),
        "allowed_filters": ["tenant_id", "time_window", "domain_segment"],
        "visibility_boundary": {
            "frontend_rendering_allowed": False,
            "api_exposure_allowed": False,
            "tenant_scope_required": True,
        },
        "metric_boundary": {
            "kpi_computation_allowed": False,
            "fake_metric_allowed": False,
            "static_contract_shape_only": True,
        },
        "next_maturity_gap": "L3 deterministic envelope readiness logic required",
        "safety_flags": dict(SAFETY_FLAGS),
    }


def classify_rector_strategy_dashboard_readiness(tenant_id: int, evidence: dict | None = None) -> dict:
    """Deterministic L3 readiness classifier for report evidence readiness only."""
    tenant_id = validate_tenant_id(tenant_id)
    required_evidence = [
        "strategic_kpi_source_registry",
        "governance_review_policy",
        "executive_visibility_boundary",
    ]
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
            "REVIEW_READINESS_CLASSIFICATION",
            "REQUEST_MISSING_EVIDENCE",
            "PREPARE_HUMAN_REVIEW",
        ],
        "forbidden_actions": [
            "AUTO_RENDER_DASHBOARD",
            "AUTO_COMPUTE_KPI",
            "AUTO_PUBLISH_EXECUTIVE_VIEW",
        ],
        "l2_contract_preserved": True,
        "l3_boundary": "dashboard_source_readiness_only_no_frontend_or_kpi_computation",
        "next_maturity_gap": "L4 operational visibility/API surface required",
        "safety_flags": {
            "no_api_claim": True,
            "no_frontend_claim": True,
            "no_provider_call": True,
            "no_live_integration_call": True,
            "no_credential_use": True,
            "no_secret_storage": True,
            "no_kpi_value_claim": True,
            "no_fake_dashboard": True,
            "no_policy_enforcement": True,
            "no_report_submission": True,
            "no_document_signature": True,
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


def _build_rector_strategy_dashboard_l4_visibility_summary(l3_output: dict) -> dict:
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
        "source_l3_function": "classify_rector_strategy_dashboard_readiness",
        "visibility_type": "rector_strategy_executive_visibility_summary",
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


def get_rector_strategy_dashboard_l4_visibility_summary(
    tenant_id: int, present_evidence: list[str] | set[str] | tuple[str, ...] | dict | None = None
) -> dict:
    l3_output = classify_rector_strategy_dashboard_readiness(
        tenant_id=tenant_id,
        evidence=_normalize_l4_evidence(present_evidence),
    )
    return _build_rector_strategy_dashboard_l4_visibility_summary(l3_output)
