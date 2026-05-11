"""A-026.8 targeted tests for L2->L3 deterministic service logic."""

from __future__ import annotations

import importlib
import inspect
from typing import Any

import pytest

MODULE_SPECS: dict[str, dict[str, Any]] = {
    "digital_certificates": {
        "function": "evaluate_digital_certificate_readiness",
        "payload_arg": "certificate_payload",
        "required_fields": ["request_id", "student_id", "program_id"],
        "ready_payload": {
            "request_id": "REQ-1",
            "student_id": "STD-1",
            "program_id": "PROG-1",
            "identity_evidence_complete": True,
            "academic_evidence_complete": True,
            "manual_issuance_requested": True,
        },
        "expected_ready_classification": "READY_FOR_MANUAL_ISSUANCE_REVIEW",
    },
    "records_hub": {
        "function": "evaluate_records_hub_readiness",
        "payload_arg": "records_payload",
        "required_fields": ["record_batch_id", "source_system", "record_count"],
        "ready_payload": {
            "record_batch_id": "BATCH-1",
            "source_system": "sis",
            "record_count": 10,
            "source_records_present": True,
            "inconsistency_detected": False,
            "reconciliation_requested": True,
        },
        "expected_ready_classification": "READY_FOR_MANUAL_RECORDS_SYNC",
    },
    "student_success_analytics": {
        "function": "evaluate_student_success_readiness",
        "payload_arg": "analytics_payload",
        "required_fields": ["student_id", "term_id", "signal_snapshot"],
        "ready_payload": {
            "student_id": "STD-1",
            "term_id": "2025-T1",
            "signal_snapshot": "S1",
            "attendance_evidence_complete": True,
            "grade_evidence_complete": True,
            "intervention_required": False,
            "advisor_triage_ready": True,
        },
        "expected_ready_classification": "READY_FOR_ADVISOR_TRIAGE",
    },
    "publication_registry": {
        "function": "evaluate_publication_registry_readiness",
        "payload_arg": "publication_payload",
        "required_fields": ["publication_id", "author_id", "publication_type"],
        "ready_payload": {
            "publication_id": "PUB-1",
            "author_id": "AUTH-1",
            "publication_type": "journal",
            "authorship_evidence_complete": True,
            "indexing_evidence_complete": True,
            "manual_registration_requested": True,
        },
        "expected_ready_classification": "READY_FOR_MANUAL_REGISTRATION",
    },
    "research_projects": {
        "function": "evaluate_research_project_readiness",
        "payload_arg": "project_payload",
        "required_fields": ["project_id", "project_owner", "scope_summary"],
        "ready_payload": {
            "project_id": "PRJ-1",
            "project_owner": "PI-1",
            "scope_summary": "baseline scope",
            "ethics_evidence_complete": True,
            "budget_evidence_complete": True,
            "scope_review_required": False,
            "manual_activation_requested": True,
        },
        "expected_ready_classification": "READY_FOR_MANUAL_PROJECT_ACTIVATION",
    },
    "lms_assessment_center": {
        "function": "evaluate_lms_assessment_readiness",
        "payload_arg": "assessment_payload",
        "required_fields": ["assessment_id", "course_id", "assessment_type"],
        "ready_payload": {
            "assessment_id": "ASM-1",
            "course_id": "CSC101",
            "assessment_type": "exam",
            "rubric_evidence_complete": True,
            "integrity_evidence_complete": True,
            "integrity_review_required": False,
            "manual_publication_review_requested": True,
        },
        "expected_ready_classification": "READY_FOR_MANUAL_PUBLICATION_REVIEW",
    },
    "lab_operations": {
        "function": "evaluate_lab_operations_readiness",
        "payload_arg": "lab_payload",
        "required_fields": ["lab_request_id", "lab_id", "requested_slot"],
        "ready_payload": {
            "lab_request_id": "LABREQ-1",
            "lab_id": "LAB-1",
            "requested_slot": "2025-09-01T09:00",
            "safety_evidence_complete": True,
            "capacity_evidence_complete": True,
            "scheduling_review_requested": True,
        },
        "expected_ready_classification": "READY_FOR_MANUAL_SCHEDULING_REVIEW",
    },
    "internship_marketplace": {
        "function": "evaluate_internship_marketplace_readiness",
        "payload_arg": "internship_payload",
        "required_fields": ["internship_request_id", "student_id", "employer_id"],
        "ready_payload": {
            "internship_request_id": "INT-1",
            "student_id": "STD-1",
            "employer_id": "EMP-1",
            "employer_evidence_complete": True,
            "student_eligibility_complete": True,
            "manual_matching_requested": True,
        },
        "expected_ready_classification": "READY_FOR_MANUAL_MATCHING_REVIEW",
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



def _call_eval(module_name: str, tenant_id: int, payload: dict | None):
    spec = MODULE_SPECS[module_name]
    service = _load_service(module_name)
    fn = getattr(service, spec["function"])
    return fn(tenant_id=tenant_id, **{spec["payload_arg"]: payload})


# ============================================================================
# Group 1: Import validation
# ============================================================================


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a0268_import_validation(module_name: str) -> None:
    service = _load_service(module_name)
    assert service is not None


# ============================================================================
# Group 2: Function signature and existence
# ============================================================================


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a0268_required_l3_function_exists(module_name: str) -> None:
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
def test_a0268_tenant_fail_closed(module_name: str, bad_tenant: Any) -> None:
    with pytest.raises(ValueError):
        _call_eval(module_name, bad_tenant, {})


# ============================================================================
# Group 4: Output schema validation
# ============================================================================


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a0268_output_schema_and_safety(module_name: str) -> None:
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
def test_a0268_determinism_same_input_same_output(module_name: str) -> None:
    payload = dict(MODULE_SPECS[module_name]["ready_payload"])
    first = _call_eval(module_name, 7, payload)
    second = _call_eval(module_name, 7, payload)
    assert first == second


# ============================================================================
# Group 6: Classification behavior validation
# ============================================================================


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a0268_missing_required_fields_classification(module_name: str) -> None:
    spec = MODULE_SPECS[module_name]
    result = _call_eval(module_name, 1, {})

    assert result["classification"].endswith("_INPUT_INCOMPLETE")
    assert result["readiness_level"] == "PENDING"
    assert result["risk_level"] in {"MEDIUM", "HIGH"}
    assert sorted(result["missing_required_evidence"]) == sorted(spec["required_fields"])


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a0268_ready_payload_has_no_missing_required_fields(module_name: str) -> None:
    spec = MODULE_SPECS[module_name]
    result = _call_eval(module_name, 1, spec["ready_payload"])
    assert result["missing_required_evidence"] == []


# ============================================================================
# Group 7: Forbidden-action boundary validation
# ============================================================================


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a0268_forbidden_actions_are_non_empty_and_auto_oriented(module_name: str) -> None:
    spec = MODULE_SPECS[module_name]
    result = _call_eval(module_name, 1, spec["ready_payload"])

    assert result["forbidden_actions"]
    assert all(action.startswith("AUTO_") for action in result["forbidden_actions"])
    assert result["human_review_required"] is True


# ============================================================================
# Group 8: Anti-inflation source guard validation
# ============================================================================


@pytest.mark.parametrize("module_name", list(MODULE_SPECS.keys()))
def test_a0268_no_router_or_provider_tokens_in_service_source(module_name: str) -> None:
    service = _load_service(module_name)
    source = inspect.getsource(service)

    for token in FORBIDDEN_SOURCE_TOKENS:
        assert token not in source
