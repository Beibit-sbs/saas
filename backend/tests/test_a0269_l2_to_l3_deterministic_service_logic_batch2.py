"""A-026.9 targeted tests for L2->L3 deterministic service logic batch 2."""

from __future__ import annotations

import importlib
import inspect
from typing import Any

import pytest

MODULE_SPECS: dict[str, dict[str, Any]] = {
    "parking_permit_ops": {
        "function": "evaluate_parking_permit_ops_readiness",
        "payload_arg": "permit_payload",
        "required_fields": ["permit_id", "vehicle_context", "permit_type", "compliance_context"],
        "ready_payload": {
            "permit_id": "PERMIT-1",
            "vehicle_context": "vehicle-context",
            "permit_type": "resident",
            "compliance_context": "compliance-context",
            "eligibility_verified": True,
        },
        "blocked_payload": {
            "permit_id": "PERMIT-1",
            "vehicle_context": "vehicle-context",
            "permit_type": "resident",
            "compliance_context": "compliance-context",
            "eligibility_verified": False,
        },
        "expected_ready_classification": "READY_FOR_PERMIT_REVIEW",
    },
    "parking_enforcement": {
        "function": "evaluate_parking_enforcement_readiness",
        "payload_arg": "enforcement_payload",
        "required_fields": ["case_id", "violation_context", "evidence_snapshot", "policy_context"],
        "ready_payload": {
            "case_id": "CASE-1",
            "violation_context": "violation-context",
            "evidence_snapshot": "evidence-snapshot",
            "policy_context": "policy-context",
            "reviewable_case": True,
            "high_conflict": False,
        },
        "blocked_payload": {
            "case_id": "CASE-1",
            "violation_context": "violation-context",
            "evidence_snapshot": "evidence-snapshot",
            "policy_context": "policy-context",
            "reviewable_case": False,
        },
        "expected_ready_classification": "READY_FOR_ENFORCEMENT_REVIEW",
    },
    "event_registration_portal": {
        "function": "evaluate_event_registration_portal_readiness",
        "payload_arg": "registration_payload",
        "required_fields": ["registration_id", "event_id", "eligibility_context", "capacity_context"],
        "ready_payload": {
            "registration_id": "REG-1",
            "event_id": "EVT-1",
            "eligibility_context": "eligibility-context",
            "capacity_context": "capacity-context",
            "eligibility_verified": True,
            "capacity_conflict": False,
        },
        "blocked_payload": {
            "registration_id": "REG-1",
            "event_id": "EVT-1",
            "eligibility_context": "eligibility-context",
            "capacity_context": "capacity-context",
            "eligibility_verified": False,
        },
        "expected_ready_classification": "READY_FOR_REGISTRATION_REVIEW",
    },
    "parent_engagement": {
        "function": "evaluate_parent_engagement_readiness",
        "payload_arg": "engagement_payload",
        "required_fields": ["engagement_id", "contact_context", "consent_context", "outreach_context"],
        "ready_payload": {
            "engagement_id": "ENG-1",
            "contact_context": "contact-context",
            "consent_context": "consent-context",
            "outreach_context": "outreach-context",
            "consent_verified": True,
            "outreach_conflict": False,
        },
        "blocked_payload": {
            "engagement_id": "ENG-1",
            "contact_context": "contact-context",
            "consent_context": "consent-context",
            "outreach_context": "outreach-context",
            "consent_verified": False,
        },
        "expected_ready_classification": "READY_FOR_OUTREACH_REVIEW",
    },
    "alumni_relations_ops": {
        "function": "evaluate_alumni_relations_ops_readiness",
        "payload_arg": "alumni_payload",
        "required_fields": ["alumni_id", "contact_context", "consent_context", "profile_context"],
        "ready_payload": {
            "alumni_id": "AL-1",
            "contact_context": "contact-context",
            "consent_context": "consent-context",
            "profile_context": "profile-context",
            "consent_verified": True,
            "relationship_risk_high": False,
        },
        "blocked_payload": {
            "alumni_id": "AL-1",
            "contact_context": "contact-context",
            "consent_context": "consent-context",
            "profile_context": "profile-context",
            "consent_verified": False,
        },
        "expected_ready_classification": "READY_FOR_OUTREACH_REVIEW",
    },
    "donations_fundraising": {
        "function": "evaluate_donations_fundraising_readiness",
        "payload_arg": "fundraising_payload",
        "required_fields": ["campaign_id", "campaign_context", "compliance_context", "donor_context"],
        "ready_payload": {
            "campaign_id": "CAM-1",
            "campaign_context": "campaign-context",
            "compliance_context": "compliance-context",
            "donor_context": "donor-context",
            "compliance_verified": True,
            "budget_allocation_requested": False,
        },
        "blocked_payload": {
            "campaign_id": "CAM-1",
            "campaign_context": "campaign-context",
            "compliance_context": "compliance-context",
            "donor_context": "donor-context",
            "compliance_verified": False,
        },
        "expected_ready_classification": "READY_FOR_CAMPAIGN_REVIEW",
    },
    "exam_integrity_analytics": {
        "function": "evaluate_exam_integrity_analytics_readiness",
        "payload_arg": "exam_payload",
        "required_fields": ["exam_id", "exam_context", "integrity_context", "review_context"],
        "ready_payload": {
            "exam_id": "EXAM-1",
            "exam_context": "exam-context",
            "integrity_context": "integrity-context",
            "review_context": "review-context",
            "reviewable_signal": True,
            "escalation_required": False,
        },
        "blocked_payload": {
            "exam_id": "EXAM-1",
            "exam_context": "exam-context",
            "integrity_context": "integrity-context",
            "review_context": "review-context",
            "reviewable_signal": False,
        },
        "expected_ready_classification": "READY_FOR_INTEGRITY_REVIEW",
    },
    "mobile_push_gateway": {
        "function": "evaluate_mobile_push_gateway_readiness",
        "payload_arg": "push_payload",
        "required_fields": ["notification_id", "notification_context", "template_context", "consent_context"],
        "ready_payload": {
            "notification_id": "NOTIF-1",
            "notification_context": "notification-context",
            "template_context": "template-context",
            "consent_context": "consent-context",
            "provider_preview_allowed": True,
            "template_review_requested": False,
        },
        "blocked_payload": {
            "notification_id": "NOTIF-1",
            "notification_context": "notification-context",
            "template_context": "template-context",
            "consent_context": "consent-context",
            "provider_preview_allowed": False,
        },
        "expected_ready_classification": "READY_FOR_PREVIEW",
    },
}

FORBIDDEN_SOURCE_TOKENS = [
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
def test_a0269_import_validation(module_name: str) -> None:
    service = _load_service(module_name)
    assert service is not None


# ============================================================================
# Group 2: Function signature and existence
# ============================================================================


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a0269_required_l3_function_exists(module_name: str) -> None:
    spec = MODULE_SPECS[module_name]
    service = _load_service(module_name)
    assert hasattr(service, "validate_tenant_id")
    assert callable(service.validate_tenant_id)
    assert hasattr(service, spec["function"])
    assert callable(getattr(service, spec["function"]))


# ============================================================================
# Group 3: Tenant fail-closed validation
# ============================================================================


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
@pytest.mark.parametrize("bad_tenant", [None, 0, -1])
def test_a0269_tenant_fail_closed(module_name: str, bad_tenant: Any) -> None:
    with pytest.raises(ValueError):
        _call_eval(module_name, bad_tenant, {})


# ============================================================================
# Group 4: Output schema validation
# ============================================================================


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a0269_output_schema_and_safety(module_name: str) -> None:
    spec = MODULE_SPECS[module_name]
    result = _call_eval(module_name, 1, spec["ready_payload"])

    assert result["tenant_id"] == 1
    assert result["module"] == module_name
    assert result["maturity_level"] == "L3"
    assert result["evaluation_status"] == "EVALUATED"
    assert result["classification"] == spec["expected_ready_classification"]
    assert result["readiness_level"] in {"READY", "PENDING", "BLOCKED"}
    assert result["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
    assert isinstance(result["required_evidence"], list)
    assert isinstance(result["missing_required_evidence"], list)
    assert isinstance(result["allowed_actions"], list)
    assert isinstance(result["forbidden_actions"], list)
    assert result["human_review_required"] is True
    assert isinstance(result["next_recommended_step"], str)
    assert isinstance(result["rationale_notes"], str)

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
def test_a0269_determinism_same_input_same_output(module_name: str) -> None:
    payload = dict(MODULE_SPECS[module_name]["ready_payload"])
    first = _call_eval(module_name, 7, payload)
    second = _call_eval(module_name, 7, payload)
    assert first == second


# ============================================================================
# Group 6: Classification behavior validation
# ============================================================================


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a0269_missing_required_fields_classification(module_name: str) -> None:
    spec = MODULE_SPECS[module_name]
    result = _call_eval(module_name, 1, {})

    assert result["classification"].endswith("_INPUT_INCOMPLETE")
    assert result["readiness_level"] == "PENDING"
    assert result["risk_level"] in {"MEDIUM", "HIGH"}
    assert sorted(result["missing_required_evidence"]) == sorted(spec["required_fields"])


# ============================================================================
# Group 7: Ready and blocked paths
# ============================================================================


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a0269_ready_path(module_name: str) -> None:
    result = _call_eval(module_name, 1, MODULE_SPECS[module_name]["ready_payload"])
    assert result["readiness_level"] == "READY"
    assert result["risk_level"] == "LOW"
    assert result["human_review_required"] is True
    assert result["missing_required_evidence"] == []


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a0269_blocked_or_pending_path(module_name: str) -> None:
    result = _call_eval(module_name, 1, MODULE_SPECS[module_name]["blocked_payload"])
    assert result["classification"] != MODULE_SPECS[module_name]["expected_ready_classification"]
    assert result["readiness_level"] in {"PENDING", "BLOCKED", "READY"}
    assert result["human_review_required"] is True


# ============================================================================
# Group 8: Anti-inflation and forbidden source boundary checks
# ============================================================================


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a0269_no_forbidden_source_boundaries(module_name: str) -> None:
    service = _load_service(module_name)
    source = inspect.getsource(service)
    for token in FORBIDDEN_SOURCE_TOKENS:
        assert token not in source


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a0269_foundation_and_l3_function_are_distinct(module_name: str) -> None:
    spec = MODULE_SPECS[module_name]
    service = _load_service(module_name)
    foundation_name = f"get_{module_name}_foundation_contract"
    assert hasattr(service, foundation_name)
    assert spec["function"] != foundation_name
    assert callable(getattr(service, foundation_name))
    assert callable(getattr(service, spec["function"]))


# ============================================================================
# Group 9: Provider boundary behavior where relevant
# ============================================================================


def test_a0269_mobile_push_gateway_provider_preview_boundary() -> None:
    result = _call_eval(
        "mobile_push_gateway",
        11,
        {
            "notification_id": "NOTIF-2",
            "notification_context": "notification-context",
            "template_context": "template-context",
            "consent_context": "consent-context",
            "provider_preview_allowed": False,
        },
    )

    assert result["classification"] == "PROVIDER_BOUNDARY_BLOCKED"
    assert result["readiness_level"] == "BLOCKED"
    assert result["risk_level"] == "HIGH"
    assert "AUTO_CALL_PROVIDER" in result["forbidden_actions"]
    assert result["safety_flags"]["no_external_provider_call"] is True
