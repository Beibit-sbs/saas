"""A-027.10 targeted tests for expansion L2->L3 deterministic logic batch 4.

Covers 12 NEW_MODULE candidates:
- UCE-002 staff_onboarding
- UCE-003 employee_records
- UCE-004 leave_management
- UCE-005 performance_appraisal
- UCE-070 staff_exit_offboarding
- UCE-057 staff_probation_review
- UCE-016 competency_framework
- UCE-012 archive_retention_management
- UCE-071 program_learning_outcomes
- UCE-072 course_learning_outcomes
- UCE-090 committee_decision_registry
- UCE-019 international_office

Anti-inflation boundaries:
- no API/frontend/provider/credential claims
- no KPI fabrication, no Brain execution
- no autonomous execution, no DB mutation
- human review required and no decision execution
"""

from __future__ import annotations

import importlib

import pytest


SELECTED = [
    {
        "module": "staff_onboarding",
        "uce_id": "UCE-002",
        "l2_fn": "get_staff_onboarding_foundation_contract",
        "classifier": "classify_staff_onboarding_readiness",
        "required_evidence": [
            "employee_profile_created",
            "onboarding_checklist_available",
            "role_assignment_review_required",
            "policy_acknowledgement_required",
            "equipment_access_review_required",
        ],
        "forbidden_actions": [
            "AUTO_COMPLETE_ONBOARDING",
            "AUTO_ASSIGN_ROLE",
            "AUTO_GRANT_ACCESS",
            "AUTO_ISSUE_EQUIPMENT",
            "MUTATE_HR_RECORD",
        ],
    },
    {
        "module": "employee_records",
        "uce_id": "UCE-003",
        "l2_fn": "get_employee_records_foundation_contract",
        "classifier": "classify_employee_records_readiness",
        "required_evidence": [
            "employee_identity_verified",
            "employment_terms_recorded",
            "contract_classification_reviewed",
            "role_assignment_recorded",
            "compliance_documents_verified",
        ],
        "forbidden_actions": [
            "AUTO_CREATE_EMPLOYEE_DECISION",
            "AUTO_UPDATE_EMPLOYMENT_STATUS",
            "AUTO_CHANGE_PAYROLL_DATA",
            "AUTO_TERMINATE_EMPLOYEE",
            "MUTATE_HR_RECORD",
        ],
    },
    {
        "module": "leave_management",
        "uce_id": "UCE-004",
        "l2_fn": "get_leave_management_foundation_contract",
        "classifier": "classify_leave_management_readiness",
        "required_evidence": [
            "leave_request_documented",
            "leave_balance_verified",
            "manager_review_recorded",
            "policy_rule_validation_required",
            "hr_review_required",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_LEAVE",
            "AUTO_REJECT_LEAVE",
            "AUTO_CHANGE_BALANCE",
            "AUTO_DECIDE_LEAVE_CASE",
            "MUTATE_HR_RECORD",
        ],
    },
    {
        "module": "performance_appraisal",
        "uce_id": "UCE-005",
        "l2_fn": "get_performance_appraisal_foundation_contract",
        "classifier": "classify_performance_appraisal_readiness",
        "required_evidence": [
            "appraisal_record_available",
            "manager_assessment_recorded",
            "employee_feedback_recorded",
            "objective_completion_evidence_present",
            "hr_review_required",
        ],
        "forbidden_actions": [
            "AUTO_SCORE_EMPLOYEE",
            "AUTO_CHANGE_SALARY",
            "AUTO_DISCIPLINARY_ACTION",
            "AUTO_PROMOTE_EMPLOYEE",
            "MUTATE_HR_RECORD",
        ],
    },
    {
        "module": "staff_exit_offboarding",
        "uce_id": "UCE-070",
        "l2_fn": "get_staff_exit_offboarding_foundation_contract",
        "classifier": "classify_staff_exit_offboarding_readiness",
        "required_evidence": [
            "exit_request_documented",
            "asset_return_checklist_available",
            "access_closure_review_recorded",
            "hr_clearance_review_required",
            "knowledge_transfer_review_required",
        ],
        "forbidden_actions": [
            "AUTO_DISABLE_ACCOUNT",
            "AUTO_DELETE_EMPLOYEE_RECORD",
            "AUTO_FINALIZE_EXIT",
            "AUTO_CLOSE_CONTRACT",
            "MUTATE_HR_RECORD",
        ],
    },
    {
        "module": "staff_probation_review",
        "uce_id": "UCE-057",
        "l2_fn": "get_staff_probation_review_foundation_contract",
        "classifier": "classify_staff_probation_review_readiness",
        "required_evidence": [
            "probation_plan_available",
            "manager_feedback_recorded",
            "performance_observation_recorded",
            "policy_compliance_review_required",
            "hr_decision_review_required",
        ],
        "forbidden_actions": [
            "AUTO_CONFIRM_EMPLOYMENT",
            "AUTO_TERMINATE_EMPLOYEE",
            "AUTO_CHANGE_CONTRACT",
            "AUTO_DECIDE_PROBATION_OUTCOME",
            "MUTATE_HR_RECORD",
        ],
    },
    {
        "module": "competency_framework",
        "uce_id": "UCE-016",
        "l2_fn": "get_competency_framework_foundation_contract",
        "classifier": "classify_competency_framework_readiness",
        "required_evidence": [
            "competency_structure_defined",
            "program_alignment_documented",
            "taxonomy_review_recorded",
            "quality_assurance_review_required",
            "governance_signoff_required",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_COMPETENCY",
            "AUTO_CHANGE_PROGRAM_OUTCOMES",
            "AUTO_DELETE_FRAMEWORK",
            "AUTO_ENFORCE_POLICY",
            "MUTATE_ACADEMIC_RECORD",
        ],
    },
    {
        "module": "archive_retention_management",
        "uce_id": "UCE-012",
        "l2_fn": "get_archive_retention_management_foundation_contract",
        "classifier": "classify_archive_retention_management_readiness",
        "required_evidence": [
            "retention_policy_defined",
            "legal_basis_documented",
            "record_inventory_verified",
            "disposal_review_checkpoint_required",
            "compliance_signoff_required",
        ],
        "forbidden_actions": [
            "AUTO_DELETE_ARCHIVE",
            "AUTO_PURGE_RECORDS",
            "AUTO_CHANGE_RETENTION_PERIOD",
            "AUTO_EXECUTE_DISPOSAL",
            "MUTATE_ARCHIVE_RECORD",
        ],
    },
    {
        "module": "program_learning_outcomes",
        "uce_id": "UCE-071",
        "l2_fn": "get_program_learning_outcomes_foundation_contract",
        "classifier": "classify_program_learning_outcomes_readiness",
        "required_evidence": [
            "program_outcome_defined",
            "competency_alignment_documented",
            "assessment_strategy_defined",
            "governance_review_recorded",
            "curriculum_committee_review_required",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_OUTCOME",
            "AUTO_CHANGE_ACCREDITATION_MAPPING",
            "AUTO_PUBLISH_CURRICULUM_CHANGE",
            "AUTO_ENFORCE_POLICY",
            "MUTATE_ACADEMIC_RECORD",
        ],
    },
    {
        "module": "course_learning_outcomes",
        "uce_id": "UCE-072",
        "l2_fn": "get_course_learning_outcomes_foundation_contract",
        "classifier": "classify_course_learning_outcomes_readiness",
        "required_evidence": [
            "course_outcome_defined",
            "plo_mapping_documented",
            "assessment_rubric_defined",
            "faculty_review_recorded",
            "quality_assurance_review_required",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_CLO",
            "AUTO_CHANGE_ASSESSMENT_MAPPING",
            "AUTO_PUBLISH_COURSE_OUTCOME",
            "AUTO_ENFORCE_POLICY",
            "MUTATE_ACADEMIC_RECORD",
        ],
    },
    {
        "module": "committee_decision_registry",
        "uce_id": "UCE-090",
        "l2_fn": "get_committee_decision_registry_foundation_contract",
        "classifier": "classify_committee_decision_registry_readiness",
        "required_evidence": [
            "committee_agenda_recorded",
            "decision_rationale_documented",
            "quorum_validation_recorded",
            "meeting_minutes_prepared",
            "signature_workflow_defined",
        ],
        "forbidden_actions": [
            "AUTO_RECORD_DECISION",
            "AUTO_APPROVE_MINUTES",
            "AUTO_SIGN_PROTOCOL",
            "AUTO_PUBLISH_DECISION",
            "MUTATE_GOVERNANCE_RECORD",
        ],
    },
    {
        "module": "international_office",
        "uce_id": "UCE-019",
        "l2_fn": "get_international_office_foundation_contract",
        "classifier": "classify_international_office_readiness",
        "required_evidence": [
            "mobility_request_documented",
            "visa_requirements_checked",
            "partner_agreement_verified",
            "student_profile_validated",
            "country_compliance_review_required",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_MOBILITY",
            "AUTO_ISSUE_VISA_DECISION",
            "AUTO_CONFIRM_PARTNERSHIP",
            "AUTO_GRANT_VISA",
            "MUTATE_STUDENT_STATUS",
        ],
    },
]


def _import_pair(module_name: str):
    pkg = importlib.import_module(f"app.modules.{module_name}")
    service = importlib.import_module(f"app.modules.{module_name}.service")
    return pkg, service


def _call_l2(service_module, entry: dict, tenant_id: int):
    fn = getattr(service_module, entry["l2_fn"])
    return fn(tenant_id=tenant_id, payload={"probe": "yes"})


def _call_l3(service_module, entry: dict, tenant_id: int, present_evidence=None):
    fn = getattr(service_module, entry["classifier"])
    return fn(tenant_id=tenant_id, present_evidence=present_evidence)


# Group 1: Import validation
@pytest.mark.parametrize("entry", SELECTED)
def test_import_validation(entry):
    _, service = _import_pair(entry["module"])
    assert callable(getattr(service, entry["l2_fn"], None))
    assert callable(getattr(service, entry["classifier"], None))


# Group 2: L2 contract preservation
@pytest.mark.parametrize("entry", SELECTED)
def test_l2_contract_preservation(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l2(service, entry, 1)
    assert isinstance(out, dict)
    assert out["maturity_level"] == "L2"
    assert out["tenant_scoped"] is True


# Group 3: L3 callable
@pytest.mark.parametrize("entry", SELECTED)
def test_l3_classifier_callable(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 5, [])
    assert isinstance(out, dict)


# Group 4: tenant fail-closed None
@pytest.mark.parametrize("entry", SELECTED)
def test_tenant_fail_closed_none_rejected(entry):
    _, service = _import_pair(entry["module"])
    with pytest.raises((ValueError, TypeError)):
        _call_l3(service, entry, None, [])


# Group 5: tenant fail-closed zero
@pytest.mark.parametrize("entry", SELECTED)
def test_tenant_fail_closed_zero_rejected(entry):
    _, service = _import_pair(entry["module"])
    with pytest.raises((ValueError, TypeError)):
        _call_l3(service, entry, 0, [])


# Group 6: tenant fail-closed negative
@pytest.mark.parametrize("entry", SELECTED)
def test_tenant_fail_closed_negative_rejected(entry):
    _, service = _import_pair(entry["module"])
    with pytest.raises((ValueError, TypeError)):
        _call_l3(service, entry, -1, [])


# Group 7: tenant fail-closed non-integer
@pytest.mark.parametrize("entry", SELECTED)
def test_tenant_fail_closed_non_integer_rejected(entry):
    _, service = _import_pair(entry["module"])
    with pytest.raises((ValueError, TypeError)):
        _call_l3(service, entry, "tenant", [])


# Group 8: valid tenant accepted
@pytest.mark.parametrize("entry", SELECTED)
def test_valid_tenant_accepted(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 9, [])
    assert out["tenant_id"] == 9


# Group 9: required common output fields
@pytest.mark.parametrize("entry", SELECTED)
def test_l3_output_structure(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 11, [])

    required_fields = [
        "tenant_id",
        "module",
        "uce_id",
        "maturity_level",
        "expansion_layer",
        "deterministic_logic_ready",
        "readiness_status",
        "risk_band",
        "evidence_completeness",
        "required_evidence",
        "present_evidence",
        "missing_evidence",
        "recommended_next_step",
        "human_review_required",
        "allowed_actions",
        "forbidden_actions",
        "l2_contract_preserved",
        "tenant_scoped",
        "next_maturity_gap",
        "safety_flags",
    ]
    for field in required_fields:
        assert field in out

    assert out["module"] == entry["module"]
    assert out["uce_id"] == entry["uce_id"]
    assert out["maturity_level"] == "L3"
    assert out["expansion_layer"] == "university_completeness"


# Group 10: deterministic readiness status
@pytest.mark.parametrize("entry", SELECTED)
def test_readiness_status_determinism(entry):
    _, service = _import_pair(entry["module"])
    req = entry["required_evidence"]
    input_evidence = [req[0], req[1]]
    out1 = _call_l3(service, entry, 17, input_evidence)
    out2 = _call_l3(service, entry, 17, input_evidence)
    assert out1["readiness_status"] == out2["readiness_status"]


# Group 11: deterministic risk band
@pytest.mark.parametrize("entry", SELECTED)
def test_risk_band_determinism(entry):
    _, service = _import_pair(entry["module"])
    req = entry["required_evidence"]
    input_evidence = [req[0], req[1], req[2]]
    out1 = _call_l3(service, entry, 3, input_evidence)
    out2 = _call_l3(service, entry, 3, input_evidence)
    assert out1["risk_band"] == out2["risk_band"]


# Group 12: evidence completeness bounds
@pytest.mark.parametrize("entry", SELECTED)
def test_evidence_completeness_bounds(entry):
    _, service = _import_pair(entry["module"])
    req = entry["required_evidence"]
    out_full = _call_l3(service, entry, 6, req)
    out_zero = _call_l3(service, entry, 6, [])
    assert out_full["evidence_completeness"] == 100
    assert out_zero["evidence_completeness"] == 0


# Group 13: missing evidence behavior
@pytest.mark.parametrize("entry", SELECTED)
def test_missing_evidence_behavior(entry):
    _, service = _import_pair(entry["module"])
    req = entry["required_evidence"]
    out = _call_l3(service, entry, 8, [req[0], req[1]])
    assert req[0] in out["present_evidence"]
    assert req[1] in out["present_evidence"]
    assert req[2] in out["missing_evidence"]


# Group 14: recommended next step mapping
@pytest.mark.parametrize("entry", SELECTED)
def test_recommended_next_step_mapping(entry):
    _, service = _import_pair(entry["module"])
    req = entry["required_evidence"]

    out_full = _call_l3(service, entry, 4, req)
    assert out_full["recommended_next_step"] == "READY_FOR_HUMAN_REVIEW"

    out_none = _call_l3(service, entry, 4, [])
    assert out_none["recommended_next_step"] == "BLOCK_UNTIL_REQUIRED_EVIDENCE_PRESENT"


# Group 15: human review always true
@pytest.mark.parametrize("entry", SELECTED)
def test_human_review_required(entry):
    _, service = _import_pair(entry["module"])
    req = entry["required_evidence"]
    for evidence in ([], [req[0]], req):
        out = _call_l3(service, entry, 10, evidence)
        assert out["human_review_required"] is True


# Group 16: l2 contract preserved flag true
@pytest.mark.parametrize("entry", SELECTED)
def test_l2_contract_preserved_flag(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 2, [])
    assert out["l2_contract_preserved"] is True


# Group 17: tenant scoped true
@pytest.mark.parametrize("entry", SELECTED)
def test_tenant_scoped_flag(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 2, [])
    assert out["tenant_scoped"] is True


# Group 18: safety flags all true
@pytest.mark.parametrize("entry", SELECTED)
def test_safety_flags_all_true(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 2, [])
    flags = out["safety_flags"]
    required_flags = [
        "no_api_claim",
        "no_frontend_claim",
        "no_provider_call",
        "no_credential_use",
        "no_kpi_value_claim",
        "no_brain_execution",
        "no_autonomous_execution",
        "no_external_side_effects",
        "no_db_mutation",
        "no_decision_execution",
        "human_review_required",
        "no_l4_claim",
        "no_l5_claim",
        "no_l6_claim",
        "tenant_fail_closed",
        "l2_contract_preserved",
    ]
    for flag in required_flags:
        assert flags.get(flag) is True


# Group 19: forbidden actions present
@pytest.mark.parametrize("entry", SELECTED)
def test_forbidden_actions_present(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 2, [])
    for forbidden in entry["forbidden_actions"]:
        assert forbidden in out["forbidden_actions"]


# Group 20: allowed actions are not AUTO_*
@pytest.mark.parametrize("entry", SELECTED)
def test_allowed_actions_no_auto(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 2, [])
    for action in out["allowed_actions"]:
        assert not action.startswith("AUTO_")


# Group 21: no provider call claim
@pytest.mark.parametrize("entry", SELECTED)
def test_no_provider_call_claim(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 2, [])
    assert out["safety_flags"]["no_provider_call"] is True


# Group 22: no credential use claim
@pytest.mark.parametrize("entry", SELECTED)
def test_no_credential_use_claim(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 2, [])
    assert out["safety_flags"]["no_credential_use"] is True


# Group 23: no kpi claim
@pytest.mark.parametrize("entry", SELECTED)
def test_no_kpi_claim(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 2, [])
    assert out["safety_flags"]["no_kpi_value_claim"] is True


# Group 24: no brain execution claim
@pytest.mark.parametrize("entry", SELECTED)
def test_no_brain_execution_claim(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 2, [])
    assert out["safety_flags"]["no_brain_execution"] is True


# Group 25: no autonomous execution claim
@pytest.mark.parametrize("entry", SELECTED)
def test_no_autonomous_execution_claim(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 2, [])
    assert out["safety_flags"]["no_autonomous_execution"] is True


# Group 26: no DB mutation claim
@pytest.mark.parametrize("entry", SELECTED)
def test_no_db_mutation_claim(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 2, [])
    assert out["safety_flags"]["no_db_mutation"] is True


# Group 27: no L4/L5/L6 claims
@pytest.mark.parametrize("entry", SELECTED)
def test_no_l4_l5_l6_claims(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 2, [])
    assert out["safety_flags"]["no_l4_claim"] is True
    assert out["safety_flags"]["no_l5_claim"] is True
    assert out["safety_flags"]["no_l6_claim"] is True


# Group 28: full evidence case
@pytest.mark.parametrize("entry", SELECTED)
def test_full_evidence_case(entry):
    _, service = _import_pair(entry["module"])
    req = entry["required_evidence"]
    out = _call_l3(service, entry, 99, req)
    assert out["readiness_status"] == "READY_FOR_REVIEW"
    assert out["risk_band"] == "LOW"
    assert out["recommended_next_step"] == "READY_FOR_HUMAN_REVIEW"
    assert out["evidence_completeness"] == 100
    assert out["missing_evidence"] == []


# Group 29: no evidence case
@pytest.mark.parametrize("entry", SELECTED)
def test_no_evidence_case(entry):
    _, service = _import_pair(entry["module"])
    req = entry["required_evidence"]
    out = _call_l3(service, entry, 99, [])
    assert out["readiness_status"] == "BLOCKED_MISSING_EVIDENCE"
    assert out["risk_band"] == "BLOCKED"
    assert out["recommended_next_step"] == "BLOCK_UNTIL_REQUIRED_EVIDENCE_PRESENT"
    assert out["evidence_completeness"] == 0
    assert sorted(out["missing_evidence"]) == sorted(req)


# Group 30: tenant isolation and A02710 constant present
@pytest.mark.parametrize("entry", SELECTED)
def test_tenant_isolation_and_a02710_constant(entry):
    _, service = _import_pair(entry["module"])
    out1 = _call_l3(service, entry, 100, [])
    out2 = _call_l3(service, entry, 200, [])
    assert out1["tenant_id"] == 100
    assert out2["tenant_id"] == 200
    assert out1["readiness_status"] == out2["readiness_status"]
    assert getattr(service, "A02710_L3_READY", None) is True
