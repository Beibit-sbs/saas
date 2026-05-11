"""A-026.10 targeted tests for final L2->L3 deterministic service logic cleanup."""

from __future__ import annotations

import importlib
import inspect
from typing import Any

import pytest

MODULE_SPECS: dict[str, dict[str, Any]] = {
    "accreditation_compliance": {
        "function": "evaluate_accreditation_compliance_readiness",
        "payload_arg": "compliance_payload",
        "required_fields": ["program_id", "cycle_id", "standard_ref", "evidence_bundle"],
        "ready_payload": {
            "program_id": "PRG-1",
            "cycle_id": "CYCLE-1",
            "standard_ref": "STD-1",
            "evidence_bundle": "bundle-ref",
            "package_ready": True,
        },
        "review_payload": {
            "program_id": "PRG-1",
            "cycle_id": "CYCLE-1",
            "standard_ref": "STD-1",
            "evidence_bundle": "bundle-ref",
            "deadline_at_risk": True,
        },
        "expected_ready_classification": "READY_FOR_MANUAL_ACCREDITATION_PACKAGE_REVIEW",
        "expected_review_classification": "DEADLINE_RISK_REVIEW_REQUIRED",
    },
    "ai_cost_governance": {
        "function": "evaluate_ai_cost_governance_readiness",
        "payload_arg": "cost_payload",
        "required_fields": ["policy_id", "budget_limit", "period_usage", "governance_owner"],
        "ready_payload": {
            "policy_id": "POL-1",
            "budget_limit": 5000,
            "period_usage": 1800,
            "governance_owner": "owner-1",
            "governance_ready": True,
        },
        "review_payload": {
            "policy_id": "POL-1",
            "budget_limit": 5000,
            "period_usage": 5100,
            "governance_owner": "owner-1",
            "threshold_breached": True,
        },
        "expected_ready_classification": "READY_FOR_MANUAL_COST_GOVERNANCE_REVIEW",
        "expected_review_classification": "BUDGET_THRESHOLD_REVIEW_REQUIRED",
    },
    "ai_plagiarism": {
        "function": "evaluate_ai_plagiarism_readiness",
        "payload_arg": "plagiarism_payload",
        "required_fields": ["document_id", "submission_id", "integrity_policy_ref", "review_context"],
        "ready_payload": {
            "document_id": "DOC-1",
            "submission_id": "SUB-1",
            "integrity_policy_ref": "POL-INT-1",
            "review_context": "context",
            "manual_case_ready": True,
        },
        "review_payload": {
            "document_id": "DOC-1",
            "submission_id": "SUB-1",
            "integrity_policy_ref": "POL-INT-1",
            "review_context": "context",
            "similarity_evidence_missing": True,
        },
        "expected_ready_classification": "READY_FOR_MANUAL_CASE_TRIAGE",
        "expected_review_classification": "SIMILARITY_EVIDENCE_REQUIRED",
    },
    "conference_management": {
        "function": "evaluate_conference_management_readiness",
        "payload_arg": "conference_payload",
        "required_fields": ["conference_id", "speaker_plan", "venue_plan", "schedule_plan"],
        "ready_payload": {
            "conference_id": "CONF-1",
            "speaker_plan": "speaker-plan",
            "venue_plan": "venue-plan",
            "schedule_plan": "schedule-plan",
            "approval_packet_ready": True,
        },
        "review_payload": {
            "conference_id": "CONF-1",
            "speaker_plan": "speaker-plan",
            "venue_plan": "venue-plan",
            "schedule_plan": "schedule-plan",
            "speaker_evidence_gap": True,
        },
        "expected_ready_classification": "READY_FOR_MANUAL_EVENT_APPROVAL",
        "expected_review_classification": "SPEAKER_EVIDENCE_REQUIRED",
    },
    "contracts_legal_repository": {
        "function": "evaluate_contracts_legal_readiness",
        "payload_arg": "contract_payload",
        "required_fields": ["contract_id", "party_context", "signature_context", "expiry_context"],
        "ready_payload": {
            "contract_id": "CTR-1",
            "party_context": "party",
            "signature_context": "signature",
            "expiry_context": "expiry",
            "manual_action_ready": True,
        },
        "review_payload": {
            "contract_id": "CTR-1",
            "party_context": "party",
            "signature_context": "signature",
            "expiry_context": "expiry",
            "signature_evidence_gap": True,
        },
        "expected_ready_classification": "READY_FOR_MANUAL_CONTRACT_ACTION",
        "expected_review_classification": "SIGNATURE_EVIDENCE_REQUIRED",
    },
    "counseling_case_management": {
        "function": "evaluate_counseling_case_readiness",
        "payload_arg": "case_payload",
        "required_fields": ["case_id", "student_id", "consent_context", "risk_context"],
        "ready_payload": {
            "case_id": "CASE-1",
            "student_id": "STU-1",
            "consent_context": "consent",
            "risk_context": "risk",
            "manual_triage_ready": True,
        },
        "review_payload": {
            "case_id": "CASE-1",
            "student_id": "STU-1",
            "consent_context": "consent",
            "risk_context": "risk",
            "risk_escalation_flag": True,
        },
        "expected_ready_classification": "READY_FOR_MANUAL_CASE_TRIAGE",
        "expected_review_classification": "RISK_ESCALATION_REVIEW_REQUIRED",
    },
    "developer_portal": {
        "function": "evaluate_developer_portal_readiness",
        "payload_arg": "portal_payload",
        "required_fields": ["channel_id", "api_access_scope", "security_review_context", "governance_owner"],
        "ready_payload": {
            "channel_id": "CH-1",
            "api_access_scope": "read-only",
            "security_review_context": "sec-review",
            "governance_owner": "owner-1",
            "enablement_ready": True,
        },
        "review_payload": {
            "channel_id": "CH-1",
            "api_access_scope": "read-only",
            "security_review_context": "sec-review",
            "governance_owner": "owner-1",
            "api_access_evidence_missing": True,
        },
        "expected_ready_classification": "READY_FOR_MANUAL_DEVELOPER_ENABLEMENT",
        "expected_review_classification": "API_ACCESS_EVIDENCE_REQUIRED",
    },
    "federation_management": {
        "function": "evaluate_federation_management_readiness",
        "payload_arg": "federation_payload",
        "required_fields": ["trust_link_id", "partner_org_context", "protocol_context", "security_review_context"],
        "ready_payload": {
            "trust_link_id": "TL-1",
            "partner_org_context": "partner",
            "protocol_context": "saml",
            "security_review_context": "sec-review",
            "manual_approval_ready": True,
        },
        "review_payload": {
            "trust_link_id": "TL-1",
            "partner_org_context": "partner",
            "protocol_context": "saml",
            "security_review_context": "sec-review",
            "protocol_mismatch": True,
        },
        "expected_ready_classification": "READY_FOR_MANUAL_FEDERATION_APPROVAL",
        "expected_review_classification": "FEDERATION_PROTOCOL_REVIEW_REQUIRED",
    },
    "health_services": {
        "function": "evaluate_health_services_readiness",
        "payload_arg": "health_payload",
        "required_fields": ["case_id", "student_id", "consent_context", "triage_context"],
        "ready_payload": {
            "case_id": "HC-1",
            "student_id": "STU-1",
            "consent_context": "consent",
            "triage_context": "triage",
            "manual_triage_ready": True,
        },
        "review_payload": {
            "case_id": "HC-1",
            "student_id": "STU-1",
            "consent_context": "consent",
            "triage_context": "triage",
            "urgent_risk_flag": True,
        },
        "expected_ready_classification": "READY_FOR_MANUAL_HEALTH_TRIAGE",
        "expected_review_classification": "URGENT_HEALTH_REVIEW_REQUIRED",
    },
    "library_circulation": {
        "function": "evaluate_library_circulation_readiness",
        "payload_arg": "circulation_payload",
        "required_fields": ["loan_id", "item_id", "student_id", "due_date"],
        "ready_payload": {
            "loan_id": "LOAN-1",
            "item_id": "ITEM-1",
            "student_id": "STU-1",
            "due_date": "2026-12-31",
            "manual_review_ready": True,
        },
        "review_payload": {
            "loan_id": "LOAN-1",
            "item_id": "ITEM-1",
            "student_id": "STU-1",
            "due_date": "2026-12-31",
            "overdue_risk": True,
        },
        "expected_ready_classification": "READY_FOR_MANUAL_CIRCULATION_REVIEW",
        "expected_review_classification": "OVERDUE_RISK_REVIEW_REQUIRED",
    },
    "local_user_management": {
        "function": "evaluate_local_user_management_readiness",
        "payload_arg": "user_payload",
        "required_fields": ["user_id", "account_status", "identity_context", "review_context"],
        "ready_payload": {
            "user_id": "USER-1",
            "account_status": "ACTIVE",
            "identity_context": "identity",
            "review_context": "review",
            "manual_action_ready": True,
        },
        "review_payload": {
            "user_id": "USER-1",
            "account_status": "ACTIVE",
            "identity_context": "identity",
            "review_context": "review",
            "identity_evidence_missing": True,
        },
        "expected_ready_classification": "READY_FOR_MANUAL_USER_ACTION",
        "expected_review_classification": "IDENTITY_EVIDENCE_REQUIRED",
    },
    "research_grants": {
        "function": "evaluate_research_grants_readiness",
        "payload_arg": "grant_payload",
        "required_fields": ["grant_id", "pi_id", "funding_agency", "budget_context"],
        "ready_payload": {
            "grant_id": "GRANT-1",
            "pi_id": "PI-1",
            "funding_agency": "Agency",
            "budget_context": "budget",
            "manual_review_ready": True,
        },
        "review_payload": {
            "grant_id": "GRANT-1",
            "pi_id": "PI-1",
            "funding_agency": "Agency",
            "budget_context": "budget",
            "budget_evidence_gap": True,
        },
        "expected_ready_classification": "READY_FOR_MANUAL_GRANT_REVIEW",
        "expected_review_classification": "BUDGET_EVIDENCE_REQUIRED",
    },
    "student_ai_tutor": {
        "function": "evaluate_student_ai_tutor_readiness",
        "payload_arg": "tutor_payload",
        "required_fields": ["session_id", "student_id", "topic", "support_context"],
        "ready_payload": {
            "session_id": "SES-1",
            "student_id": "STU-1",
            "topic": "calculus",
            "support_context": "support",
            "manual_review_ready": True,
        },
        "review_payload": {
            "session_id": "SES-1",
            "student_id": "STU-1",
            "topic": "calculus",
            "support_context": "support",
            "struggle_escalation_flag": True,
        },
        "expected_ready_classification": "READY_FOR_MANUAL_TUTOR_REVIEW",
        "expected_review_classification": "STUDENT_SUPPORT_ESCALATION_REQUIRED",
    },
}

FORBIDDEN_EVALUATOR_TOKENS = [
    "APIRouter",
    "@router",
    "@app.get",
    "@app.post",
    "publish_event",
    "brain_signal",
    "execute_brain",
    "send_email",
    "send_sms",
    "push_provider",
]


def _load_service(module_name: str):
    return importlib.import_module(f"app.modules.{module_name}.service")


def _call_eval(module_name: str, tenant_id: int | None, payload: dict | None):
    spec = MODULE_SPECS[module_name]
    service = _load_service(module_name)
    fn = getattr(service, spec["function"])
    return fn(tenant_id=tenant_id, **{spec["payload_arg"]: payload})


# ============================================================================
# Group 1: Import validation
# ============================================================================


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a02610_import_validation(module_name: str) -> None:
    service = _load_service(module_name)
    assert service is not None


# ============================================================================
# Group 2: Function signature and existence
# ============================================================================


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a02610_required_l3_function_exists(module_name: str) -> None:
    spec = MODULE_SPECS[module_name]
    service = _load_service(module_name)
    assert hasattr(service, "_validate_tenant")
    assert callable(service._validate_tenant)
    assert hasattr(service, spec["function"])

    fn = getattr(service, spec["function"])
    assert callable(fn)
    signature = inspect.signature(fn)
    assert "tenant_id" in signature.parameters
    assert spec["payload_arg"] in signature.parameters


# ============================================================================
# Group 3: Tenant fail-closed validation
# ============================================================================


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
@pytest.mark.parametrize("bad_tenant", [0, -1])
def test_a02610_tenant_fail_closed(module_name: str, bad_tenant: Any) -> None:
    with pytest.raises(ValueError):
        _call_eval(module_name, bad_tenant, {})


# ============================================================================
# Group 4: Output schema validation
# ============================================================================


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a02610_output_schema_and_safety(module_name: str) -> None:
    spec = MODULE_SPECS[module_name]
    result = _call_eval(module_name, 1, spec["ready_payload"])

    assert result["tenant_id"] == 1
    assert result["module"] == module_name
    assert result["maturity_level"] == "L3"
    assert result["evaluation_status"] in {"INCOMPLETE", "REVIEW_REQUIRED", "READY"}
    assert result["readiness_level"] in {"READY", "PENDING"}
    assert result["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
    assert isinstance(result["required_evidence"], list)
    assert isinstance(result["missing_evidence"], list)
    assert isinstance(result["allowed_actions"], list)
    assert isinstance(result["forbidden_actions"], list)
    assert result["human_review_required"] is True
    assert isinstance(result["next_recommended_step"], str)
    assert result["next_recommended_step"]
    assert isinstance(result["rationale_notes"], str)
    assert result["rationale_notes"]

    flags = result["safety_flags"]
    assert flags["tenant_scoped"] is True
    assert flags["deterministic"] is True
    assert flags["no_api_claim"] is True
    assert flags["no_frontend_claim"] is True
    assert flags["no_kpi_claim"] is True
    assert flags["no_brain_claim"] is True
    assert flags["no_autonomous_execution"] is True
    assert flags["no_external_provider_call"] is True
    assert flags["no_l4_claim"] is True
    assert flags["no_l5_claim"] is True
    assert flags["no_l6_claim"] is True


# ============================================================================
# Group 5: Determinism validation
# ============================================================================


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a02610_determinism_same_input_same_output(module_name: str) -> None:
    payload = dict(MODULE_SPECS[module_name]["ready_payload"])
    first = _call_eval(module_name, 7, payload)
    second = _call_eval(module_name, 7, payload)
    assert first == second


# ============================================================================
# Group 6: Missing evidence classification
# ============================================================================


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a02610_missing_required_fields_classification(module_name: str) -> None:
    spec = MODULE_SPECS[module_name]
    result = _call_eval(module_name, 1, {})

    assert result["classification"].endswith("_INPUT_INCOMPLETE")
    assert result["evaluation_status"] == "INCOMPLETE"
    assert result["readiness_level"] == "PENDING"
    assert result["risk_level"] == "MEDIUM"
    assert sorted(result["missing_evidence"]) == sorted(spec["required_fields"])


# ============================================================================
# Group 7: Ready path validation
# ============================================================================


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a02610_ready_path(module_name: str) -> None:
    spec = MODULE_SPECS[module_name]
    result = _call_eval(module_name, 1, spec["ready_payload"])

    assert result["classification"] == spec["expected_ready_classification"]
    assert result["evaluation_status"] == "READY"
    assert result["readiness_level"] == "READY"
    assert result["risk_level"] == "LOW"
    assert result["human_review_required"] is True
    assert result["missing_evidence"] == []


# ============================================================================
# Group 8: Review-required path validation
# ============================================================================


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a02610_review_required_path(module_name: str) -> None:
    spec = MODULE_SPECS[module_name]
    result = _call_eval(module_name, 1, spec["review_payload"])

    assert result["classification"] == spec["expected_review_classification"]
    assert result["evaluation_status"] == "REVIEW_REQUIRED"
    assert result["readiness_level"] == "PENDING"
    assert result["risk_level"] == "HIGH"
    assert result["human_review_required"] is True


# ============================================================================
# Group 9: Evaluator anti-inflation boundary checks
# ============================================================================


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a02610_no_forbidden_tokens_in_evaluator_source(module_name: str) -> None:
    spec = MODULE_SPECS[module_name]
    service = _load_service(module_name)
    evaluator_source = inspect.getsource(getattr(service, spec["function"]))
    for token in FORBIDDEN_EVALUATOR_TOKENS:
        assert token not in evaluator_source
