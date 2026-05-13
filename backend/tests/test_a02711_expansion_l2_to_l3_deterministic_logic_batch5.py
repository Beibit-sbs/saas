"""A-027.11 targeted tests for expansion L2->L3 deterministic logic batch 5.

Covers selected constrained-safe candidates:
- UCE-054 brain_decision_audit_trail
- UCE-047 third_party_risk_policy
- UCE-001 staff_recruitment
- UCE-037 scholarship_committee_workflow
- UCE-038 student_appeals_workflow
"""

from __future__ import annotations

import importlib

import pytest


SELECTED = [
    {
        "module": "brain_decision_audit_trail",
        "uce_id": "UCE-054",
        "l2_fn": "get_brain_decision_audit_trail_envelope_contract",
        "classifier": "classify_brain_decision_audit_trail_readiness",
        "required_evidence": [
            "decision_context_defined",
            "recommendation_source_identified",
            "human_reviewer_required",
            "audit_lineage_schema_available",
            "retention_policy_linked",
        ],
        "forbidden_actions": [
            "EXECUTE_BRAIN_RECOMMENDATION",
            "AUTO_APPROVE_DECISION",
            "AUTO_REJECT_DECISION",
            "CALL_MODEL_PROVIDER",
            "MUTATE_AUDIT_RECORD",
            "PROCESS_SIGNAL",
            "AUTONOMOUS_ACTION",
        ],
    },
    {
        "module": "third_party_risk_policy",
        "uce_id": "UCE-047",
        "l2_fn": "get_third_party_risk_policy_envelope_contract",
        "classifier": "classify_third_party_risk_policy_readiness",
        "required_evidence": [
            "third_party_scope_defined",
            "risk_categories_defined",
            "owner_assigned",
            "review_cycle_defined",
            "human_policy_review_required",
        ],
        "forbidden_actions": [
            "ENFORCE_POLICY",
            "AUTO_BLOCK_VENDOR",
            "AUTO_APPROVE_VENDOR",
            "AUTO_REJECT_VENDOR",
            "MUTATE_PROCUREMENT_RECORD",
            "MUTATE_LEGAL_RECORD",
        ],
    },
    {
        "module": "staff_recruitment",
        "uce_id": "UCE-001",
        "l2_fn": "get_staff_recruitment_foundation_contract",
        "classifier": "classify_staff_recruitment_readiness",
        "required_evidence": [
            "vacancy_request_present",
            "position_profile_available",
            "hiring_committee_review_required",
            "candidate_evidence_policy_available",
            "human_hr_review_required",
        ],
        "forbidden_actions": [
            "AUTO_HIRE_CANDIDATE",
            "AUTO_REJECT_CANDIDATE",
            "AUTO_RANK_CANDIDATE",
            "AUTO_SCORE_CANDIDATE",
            "AUTO_CREATE_EMPLOYMENT_CONTRACT",
            "MUTATE_HR_RECORD",
        ],
    },
    {
        "module": "scholarship_committee_workflow",
        "uce_id": "UCE-037",
        "l2_fn": "get_scholarship_committee_workflow_envelope_contract",
        "classifier": "classify_scholarship_committee_workflow_readiness",
        "required_evidence": [
            "scholarship_policy_available",
            "applicant_evidence_present",
            "committee_membership_defined",
            "conflict_of_interest_review_required",
            "human_committee_review_required",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_SCHOLARSHIP",
            "AUTO_REJECT_SCHOLARSHIP",
            "AUTO_RANK_APPLICANT",
            "AUTO_SCORE_APPLICANT",
            "AUTO_ASSIGN_AID_AMOUNT",
            "MUTATE_FINANCIAL_AID_RECORD",
        ],
    },
    {
        "module": "student_appeals_workflow",
        "uce_id": "UCE-038",
        "l2_fn": "get_student_appeals_workflow_envelope_contract",
        "classifier": "classify_student_appeals_workflow_readiness",
        "required_evidence": [
            "appeal_request_present",
            "appeal_category_defined",
            "case_evidence_present",
            "review_committee_required",
            "human_appeals_review_required",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_APPEAL",
            "AUTO_REJECT_APPEAL",
            "AUTO_CHANGE_GRADE",
            "AUTO_REVERSE_SANCTION",
            "AUTO_CHANGE_STUDENT_STATUS",
            "MUTATE_ACADEMIC_RECORD",
        ],
    },
]


A0277_TO_A02710_ALREADY_L3 = {
    "document_workflow",
    "order_decree_registry",
    "incoming_outgoing_correspondence",
    "document_template_library",
    "course_catalog_management",
    "syllabus_management",
    "curriculum_mapping",
    "prerequisite_management",
    "degree_audit",
    "transfer_credit_management",
    "student_information_system_integration",
    "learning_management_system_integration",
    "regulatory_reporting_integration",
    "digital_signature_integration",
    "compliance_calendar_dashboard",
    "ministry_reporting_dashboard",
    "accreditation_dashboard",
    "rector_strategy_dashboard",
    "data_retention_policy_control",
    "consent_management_policy",
    "rector_resolution_tracking_workflow",
    "procurement_plan_approval_workflow",
    "elective_course_selection",
    "dormitory_management",
    "thesis_dissertation_management",
    "inbound_exchange_management",
    "outbound_exchange_management",
    "joint_program_management",
    "partnership_registry",
    "timesheet_management",
    "faculty_attestation",
    "teaching_load_contracts",
    "mou_lifecycle",
    "staff_onboarding",
    "employee_records",
    "leave_management",
    "performance_appraisal",
    "staff_exit_offboarding",
    "staff_probation_review",
    "competency_framework",
    "archive_retention_management",
    "program_learning_outcomes",
    "course_learning_outcomes",
    "committee_decision_registry",
    "international_office",
}


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


@pytest.mark.parametrize("entry", SELECTED)
def test_01_import_validation(entry):
    _, service = _import_pair(entry["module"])
    assert callable(getattr(service, entry["l2_fn"], None))
    assert callable(getattr(service, entry["classifier"], None))


@pytest.mark.parametrize("entry", SELECTED)
def test_02_l2_contract_preservation(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l2(service, entry, 1)
    assert isinstance(out, dict)
    assert out["maturity_level"] == "L2"
    assert out["tenant_scoped"] is True


@pytest.mark.parametrize("entry", SELECTED)
def test_03_l3_classifier_exists_and_callable(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 2, [])
    assert isinstance(out, dict)


@pytest.mark.parametrize("entry", SELECTED)
def test_04_tenant_fail_closed_none(entry):
    _, service = _import_pair(entry["module"])
    with pytest.raises((ValueError, TypeError)):
        _call_l3(service, entry, None, [])


@pytest.mark.parametrize("entry", SELECTED)
def test_05_tenant_fail_closed_zero(entry):
    _, service = _import_pair(entry["module"])
    with pytest.raises((ValueError, TypeError)):
        _call_l3(service, entry, 0, [])


@pytest.mark.parametrize("entry", SELECTED)
def test_06_tenant_fail_closed_negative(entry):
    _, service = _import_pair(entry["module"])
    with pytest.raises((ValueError, TypeError)):
        _call_l3(service, entry, -1, [])


@pytest.mark.parametrize("entry", SELECTED)
def test_07_tenant_fail_closed_non_int(entry):
    _, service = _import_pair(entry["module"])
    with pytest.raises((ValueError, TypeError)):
        _call_l3(service, entry, "tenant", [])


@pytest.mark.parametrize("entry", SELECTED)
def test_08_valid_tenant_accepted(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 9, [])
    assert out["tenant_id"] == 9


@pytest.mark.parametrize("entry", SELECTED)
def test_09_output_required_fields(entry):
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


@pytest.mark.parametrize("entry", SELECTED)
def test_10_readiness_deterministic(entry):
    _, service = _import_pair(entry["module"])
    req = entry["required_evidence"]
    evidence = [req[0], req[1]]
    out1 = _call_l3(service, entry, 13, evidence)
    out2 = _call_l3(service, entry, 13, evidence)
    assert out1["readiness_status"] == out2["readiness_status"]


@pytest.mark.parametrize("entry", SELECTED)
def test_11_risk_band_mapping_deterministic(entry):
    _, service = _import_pair(entry["module"])
    req = entry["required_evidence"]
    evidence = [req[0], req[1], req[2]]
    out1 = _call_l3(service, entry, 13, evidence)
    out2 = _call_l3(service, entry, 13, evidence)
    assert out1["risk_band"] == out2["risk_band"]


@pytest.mark.parametrize("entry", SELECTED)
def test_12_evidence_completeness_deterministic_int(entry):
    _, service = _import_pair(entry["module"])
    req = entry["required_evidence"]
    out = _call_l3(service, entry, 15, [req[0], req[1]])
    assert isinstance(out["evidence_completeness"], int)
    assert 0 <= out["evidence_completeness"] <= 100


@pytest.mark.parametrize("entry", SELECTED)
def test_13_missing_evidence_deterministic(entry):
    _, service = _import_pair(entry["module"])
    req = entry["required_evidence"]
    out1 = _call_l3(service, entry, 17, [req[0], req[1]])
    out2 = _call_l3(service, entry, 17, [req[0], req[1]])
    assert out1["missing_evidence"] == out2["missing_evidence"]


@pytest.mark.parametrize("entry", SELECTED)
def test_14_recommended_next_step_mapping(entry):
    _, service = _import_pair(entry["module"])
    req = entry["required_evidence"]

    out_ready = _call_l3(service, entry, 21, req)
    out_blocked = _call_l3(service, entry, 21, [])

    assert out_ready["recommended_next_step"] == "READY_FOR_HUMAN_REVIEW"
    assert out_blocked["recommended_next_step"] == "BLOCK_UNTIL_REQUIRED_EVIDENCE_PRESENT"


@pytest.mark.parametrize("entry", SELECTED)
def test_15_human_review_required_true(entry):
    _, service = _import_pair(entry["module"])
    req = entry["required_evidence"]
    for evidence in ([], [req[0]], req):
        out = _call_l3(service, entry, 2, evidence)
        assert out["human_review_required"] is True


@pytest.mark.parametrize("entry", SELECTED)
def test_16_l2_contract_preserved_true(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 2, [])
    assert out["l2_contract_preserved"] is True


@pytest.mark.parametrize("entry", SELECTED)
def test_17_tenant_scoped_true(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 2, [])
    assert out["tenant_scoped"] is True


@pytest.mark.parametrize("entry", SELECTED)
def test_18_safety_flags_all_true(entry):
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
        "no_policy_enforcement",
        "no_workflow_execution",
        "human_review_required",
        "no_l4_claim",
        "no_l5_claim",
        "no_l6_claim",
        "tenant_fail_closed",
        "l2_contract_preserved",
    ]
    for flag in required_flags:
        assert flags.get(flag) is True


@pytest.mark.parametrize("entry", SELECTED)
def test_19_module_specific_forbidden_actions(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 3, [])
    for forbidden in entry["forbidden_actions"]:
        assert forbidden in out["forbidden_actions"]


@pytest.mark.parametrize("entry", SELECTED)
def test_20_no_provider_call_claim(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 3, [])
    assert out["safety_flags"]["no_provider_call"] is True


@pytest.mark.parametrize("entry", SELECTED)
def test_21_no_credential_use_claim(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 3, [])
    assert out["safety_flags"]["no_credential_use"] is True


@pytest.mark.parametrize("entry", SELECTED)
def test_22_no_kpi_dashboard_claims(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 3, [])
    assert out["safety_flags"]["no_kpi_value_claim"] is True


@pytest.mark.parametrize("entry", SELECTED)
def test_23_no_brain_execution_claim(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 3, [])
    assert out["safety_flags"]["no_brain_execution"] is True


@pytest.mark.parametrize("entry", SELECTED)
def test_24_no_autonomous_execution_claim(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 3, [])
    assert out["safety_flags"]["no_autonomous_execution"] is True


@pytest.mark.parametrize("entry", SELECTED)
def test_25_no_policy_or_workflow_execution_claims(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 3, [])
    assert out["safety_flags"]["no_policy_enforcement"] is True
    assert out["safety_flags"]["no_workflow_execution"] is True


@pytest.mark.parametrize("entry", SELECTED)
def test_26_full_evidence_ready_case(entry):
    _, service = _import_pair(entry["module"])
    req = entry["required_evidence"]
    out = _call_l3(service, entry, 99, req)
    assert out["readiness_status"] == "READY_FOR_REVIEW"
    assert out["risk_band"] == "LOW"
    assert out["recommended_next_step"] == "READY_FOR_HUMAN_REVIEW"


@pytest.mark.parametrize("entry", SELECTED)
def test_27_no_evidence_blocked_case(entry):
    _, service = _import_pair(entry["module"])
    req = entry["required_evidence"]
    out = _call_l3(service, entry, 99, [])
    assert out["readiness_status"] == "BLOCKED_MISSING_EVIDENCE"
    assert out["risk_band"] == "BLOCKED"
    assert out["recommended_next_step"] == "BLOCK_UNTIL_REQUIRED_EVIDENCE_PRESENT"
    assert sorted(out["missing_evidence"]) == sorted(req)


@pytest.mark.parametrize("entry", SELECTED)
def test_28_partial_or_incomplete_case(entry):
    _, service = _import_pair(entry["module"])
    req = entry["required_evidence"]
    out = _call_l3(service, entry, 44, [req[0], req[1]])
    assert out["readiness_status"] in {"PARTIAL_EVIDENCE", "INCOMPLETE_EVIDENCE"}
    assert out["risk_band"] in {"MEDIUM", "HIGH"}
    assert out["recommended_next_step"] == "REQUEST_MISSING_EVIDENCE"


@pytest.mark.parametrize("entry", SELECTED)
def test_29_same_input_identical_output(entry):
    _, service = _import_pair(entry["module"])
    req = entry["required_evidence"]
    evidence = [req[0], req[1], req[2]]
    out1 = _call_l3(service, entry, 51, evidence)
    out2 = _call_l3(service, entry, 51, evidence)
    assert out1 == out2


@pytest.mark.parametrize("entry", SELECTED)
def test_30_module_specific_uce_id_preserved(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 3, [])
    assert out["uce_id"] == entry["uce_id"]


def test_31_brain_decision_audit_no_brain_model_signal_behavior():
    _, service = _import_pair("brain_decision_audit_trail")
    out = service.classify_brain_decision_audit_trail_readiness(tenant_id=1, present_evidence=[])
    forbidden = out["forbidden_actions"]
    assert "EXECUTE_BRAIN_RECOMMENDATION" in forbidden
    assert "CALL_MODEL_PROVIDER" in forbidden
    assert "PROCESS_SIGNAL" in forbidden


def test_32_third_party_risk_policy_no_policy_enforcement():
    _, service = _import_pair("third_party_risk_policy")
    out = service.classify_third_party_risk_policy_readiness(tenant_id=1, present_evidence=[])
    forbidden = out["forbidden_actions"]
    assert "ENFORCE_POLICY" in forbidden
    assert "AUTO_BLOCK_VENDOR" in forbidden


def test_33_staff_recruitment_no_rank_score_hire_reject():
    _, service = _import_pair("staff_recruitment")
    out = service.classify_staff_recruitment_readiness(tenant_id=1, present_evidence=[])
    forbidden = out["forbidden_actions"]
    assert "AUTO_HIRE_CANDIDATE" in forbidden
    assert "AUTO_REJECT_CANDIDATE" in forbidden
    assert "AUTO_RANK_CANDIDATE" in forbidden
    assert "AUTO_SCORE_CANDIDATE" in forbidden


def test_34_scholarship_no_approve_reject_score_assign_aid():
    _, service = _import_pair("scholarship_committee_workflow")
    out = service.classify_scholarship_committee_workflow_readiness(tenant_id=1, present_evidence=[])
    forbidden = out["forbidden_actions"]
    assert "AUTO_APPROVE_SCHOLARSHIP" in forbidden
    assert "AUTO_REJECT_SCHOLARSHIP" in forbidden
    assert "AUTO_RANK_APPLICANT" in forbidden
    assert "AUTO_SCORE_APPLICANT" in forbidden
    assert "AUTO_ASSIGN_AID_AMOUNT" in forbidden


def test_35_appeals_no_approve_reject_grade_sanction_status_mutation():
    _, service = _import_pair("student_appeals_workflow")
    out = service.classify_student_appeals_workflow_readiness(tenant_id=1, present_evidence=[])
    forbidden = out["forbidden_actions"]
    assert "AUTO_APPROVE_APPEAL" in forbidden
    assert "AUTO_REJECT_APPEAL" in forbidden
    assert "AUTO_CHANGE_GRADE" in forbidden
    assert "AUTO_REVERSE_SANCTION" in forbidden
    assert "AUTO_CHANGE_STUDENT_STATUS" in forbidden


def test_36_l2_functions_still_available_for_selected_modules():
    for entry in SELECTED:
        _, service = _import_pair(entry["module"])
        assert callable(getattr(service, entry["l2_fn"], None))


def test_37_no_a0277_to_a02710_already_l3_module_selected_again():
    selected_modules = {entry["module"] for entry in SELECTED}
    assert selected_modules.isdisjoint(A0277_TO_A02710_ALREADY_L3)
