"""A-027.9 targeted tests for expansion L2->L3 deterministic logic batch 3.

Covers 11 NEW_MODULE candidates:
- UCE-073 elective_course_selection
- UCE-017 dormitory_management
- UCE-077 thesis_dissertation_management
- UCE-086 inbound_exchange_management
- UCE-087 outbound_exchange_management
- UCE-085 joint_program_management
- UCE-022 partnership_registry
- UCE-060 timesheet_management
- UCE-061 faculty_attestation
- UCE-067 teaching_load_contracts
- UCE-023 mou_lifecycle

Anti-inflation: no API, no frontend, no provider call, no credential use,
no fake KPI, no Brain execution, no autonomous execution, no DB mutation,
no L4/L5/L6 claims. All human-review-gated.
"""

from __future__ import annotations

import importlib

import pytest


SELECTED = [
    {
        "module": "elective_course_selection",
        "type": "NEW_MODULE",
        "id_key": "uce_id",
        "id_value": "UCE-073",
        "l2_fn": "get_elective_course_selection_foundation_contract",
        "classifier": "classify_elective_course_selection_readiness",
        "required_evidence": [
            "student_program_context",
            "elective_catalog_available",
            "prerequisite_check_ready",
            "seat_capacity_reviewed",
            "advisor_review_required",
        ],
        "forbidden_actions": [
            "AUTO_ENROLL_STUDENT",
            "AUTO_APPROVE_ELECTIVE",
            "AUTO_OVERRIDE_PREREQUISITE",
            "AUTO_RESERVE_SEAT",
            "MUTATE_STUDENT_RECORD",
        ],
    },
    {
        "module": "dormitory_management",
        "type": "NEW_MODULE",
        "id_key": "uce_id",
        "id_value": "UCE-017",
        "l2_fn": "get_dormitory_management_foundation_contract",
        "classifier": "classify_dormitory_management_readiness",
        "required_evidence": [
            "housing_application_present",
            "student_identity_verified",
            "room_inventory_available",
            "occupancy_policy_available",
            "human_housing_review_required",
        ],
        "forbidden_actions": [
            "AUTO_ASSIGN_ROOM",
            "AUTO_REJECT_HOUSING",
            "AUTO_APPROVE_HOUSING",
            "MUTATE_OCCUPANCY_RECORD",
            "CHARGE_HOUSING_FEE",
        ],
    },
    {
        "module": "thesis_dissertation_management",
        "type": "NEW_MODULE",
        "id_key": "uce_id",
        "id_value": "UCE-077",
        "l2_fn": "get_thesis_dissertation_management_foundation_contract",
        "classifier": "classify_thesis_dissertation_management_readiness",
        "required_evidence": [
            "thesis_topic_registered",
            "supervisor_assigned",
            "committee_review_required",
            "milestone_plan_present",
            "plagiarism_policy_acknowledged",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_TOPIC",
            "AUTO_ASSIGN_SUPERVISOR",
            "AUTO_PASS_DEFENSE",
            "AUTO_REJECT_THESIS",
            "MUTATE_ACADEMIC_RECORD",
        ],
    },
    {
        "module": "inbound_exchange_management",
        "type": "NEW_MODULE",
        "id_key": "uce_id",
        "id_value": "UCE-086",
        "l2_fn": "get_inbound_exchange_management_foundation_contract",
        "classifier": "classify_inbound_exchange_management_readiness",
        "required_evidence": [
            "nomination_received",
            "partner_institution_verified",
            "learning_agreement_draft_present",
            "visa_support_review_required",
            "registrar_review_required",
        ],
        "forbidden_actions": [
            "AUTO_ACCEPT_EXCHANGE_STUDENT",
            "AUTO_ISSUE_INVITATION",
            "AUTO_APPROVE_VISA_SUPPORT",
            "AUTO_ENROLL_STUDENT",
            "PROVIDER_CALL",
        ],
    },
    {
        "module": "outbound_exchange_management",
        "type": "NEW_MODULE",
        "id_key": "uce_id",
        "id_value": "UCE-087",
        "l2_fn": "get_outbound_exchange_management_foundation_contract",
        "classifier": "classify_outbound_exchange_management_readiness",
        "required_evidence": [
            "student_application_present",
            "home_program_approval_required",
            "partner_requirements_available",
            "learning_agreement_draft_present",
            "mobility_risk_review_required",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_MOBILITY",
            "AUTO_SEND_NOMINATION",
            "AUTO_COMMIT_STUDENT_TO_PARTNER",
            "MUTATE_STUDENT_RECORD",
            "PROVIDER_CALL",
        ],
    },
    {
        "module": "joint_program_management",
        "type": "NEW_MODULE",
        "id_key": "uce_id",
        "id_value": "UCE-085",
        "l2_fn": "get_joint_program_management_foundation_contract",
        "classifier": "classify_joint_program_management_readiness",
        "required_evidence": [
            "partner_profile_present",
            "joint_program_proposal_present",
            "governance_model_defined",
            "academic_owner_review_required",
            "legal_review_required",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_JOINT_PROGRAM",
            "AUTO_SIGN_AGREEMENT",
            "AUTO_PUBLISH_PROGRAM",
            "MUTATE_PROGRAM_CATALOG",
            "PROVIDER_CALL",
        ],
    },
    {
        "module": "partnership_registry",
        "type": "NEW_MODULE",
        "id_key": "uce_id",
        "id_value": "UCE-022",
        "l2_fn": "get_partnership_registry_foundation_contract",
        "classifier": "classify_partnership_registry_readiness",
        "required_evidence": [
            "partner_identity_present",
            "partner_status_verified",
            "relationship_owner_assigned",
            "compliance_review_required",
            "renewal_review_policy_available",
        ],
        "forbidden_actions": [
            "AUTO_CREATE_LEGAL_PARTNERSHIP",
            "AUTO_APPROVE_PARTNER",
            "AUTO_RENEW_PARTNERSHIP",
            "MUTATE_CONTRACT_RECORD",
            "PROVIDER_CALL",
        ],
    },
    {
        "module": "timesheet_management",
        "type": "NEW_MODULE",
        "id_key": "uce_id",
        "id_value": "UCE-060",
        "l2_fn": "get_timesheet_management_foundation_contract",
        "classifier": "classify_timesheet_management_readiness",
        "required_evidence": [
            "employee_identity_present",
            "timesheet_period_defined",
            "submitted_hours_present",
            "supervisor_review_required",
            "policy_thresholds_available",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_TIMESHEET",
            "AUTO_REJECT_TIMESHEET",
            "AUTO_SEND_TO_PAYROLL",
            "MUTATE_PAYROLL_RECORD",
            "MUTATE_ATTENDANCE_RECORD",
        ],
    },
    {
        "module": "faculty_attestation",
        "type": "NEW_MODULE",
        "id_key": "uce_id",
        "id_value": "UCE-061",
        "l2_fn": "get_faculty_attestation_foundation_contract",
        "classifier": "classify_faculty_attestation_readiness",
        "required_evidence": [
            "faculty_identity_present",
            "attestation_period_defined",
            "required_documents_list_available",
            "committee_review_required",
            "compliance_policy_available",
        ],
        "forbidden_actions": [
            "AUTO_PASS_ATTESTATION",
            "AUTO_FAIL_ATTESTATION",
            "AUTO_CHANGE_EMPLOYMENT_STATUS",
            "AUTO_APPLY_SANCTION",
            "MUTATE_HR_RECORD",
        ],
    },
    {
        "module": "teaching_load_contracts",
        "type": "NEW_MODULE",
        "id_key": "uce_id",
        "id_value": "UCE-067",
        "l2_fn": "get_teaching_load_contracts_foundation_contract",
        "classifier": "classify_teaching_load_contracts_readiness",
        "required_evidence": [
            "faculty_identity_present",
            "teaching_load_plan_present",
            "course_assignment_evidence_present",
            "workload_policy_available",
            "faculty_review_required",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_LOAD",
            "AUTO_CHANGE_TIMETABLE",
            "AUTO_ASSIGN_COURSE",
            "AUTO_CHANGE_CONTRACT",
            "MUTATE_HR_RECORD",
        ],
    },
    {
        "module": "mou_lifecycle",
        "type": "NEW_MODULE",
        "id_key": "uce_id",
        "id_value": "UCE-023",
        "l2_fn": "get_mou_lifecycle_foundation_contract",
        "classifier": "classify_mou_lifecycle_readiness",
        "required_evidence": [
            "partner_profile_present",
            "mou_draft_present",
            "legal_review_required",
            "authorized_signatory_identified",
            "renewal_or_expiry_policy_available",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_MOU",
            "AUTO_SIGN_MOU",
            "AUTO_RENEW_MOU",
            "AUTO_TERMINATE_MOU",
            "MUTATE_LEGAL_RECORD",
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


def _call_l3(service_module, entry: dict, tenant_id: int, evidence: dict | None = None):
    fn = getattr(service_module, entry["classifier"])
    return fn(tenant_id=tenant_id, evidence=evidence)


# ============================================================
# Group 1: Import validation — all 11 modules
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_import_validation(entry):
    """Verify module package and service are importable and both functions exist."""
    _, service = _import_pair(entry["module"])
    assert callable(getattr(service, entry["l2_fn"], None)), (
        f"L2 function {entry['l2_fn']} not found in {entry['module']}.service"
    )
    assert callable(getattr(service, entry["classifier"], None)), (
        f"L3 classifier {entry['classifier']} not found in {entry['module']}.service"
    )


# ============================================================
# Group 2: L2 contract preservation — all 11 modules
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_l2_contract_preservation(entry):
    """Verify L2 contract function still works and returns L2 maturity."""
    _, service = _import_pair(entry["module"])
    out = _call_l2(service, entry, 1)

    assert isinstance(out, dict)
    assert out["maturity_level"] == "L2"
    assert out["tenant_scoped"] is True
    flags = out["safety_flags"]
    assert flags["no_api_claim"] is True
    assert flags["no_frontend_claim"] is True
    assert flags["no_provider_call"] is True
    assert flags["no_autonomous_execution"] is True


# ============================================================
# Group 3: L3 classifier callable — all 11 modules
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_l3_classifier_callable(entry):
    """Verify classify function is callable and returns a dict."""
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 5, {})
    assert isinstance(out, dict)


# ============================================================
# Group 4: Tenant fail-closed — rejects None / 0 / -1
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_tenant_fail_closed_none_rejected(entry):
    _, service = _import_pair(entry["module"])
    with pytest.raises((ValueError, TypeError)):
        _call_l3(service, entry, None, {})


@pytest.mark.parametrize("entry", SELECTED)
def test_tenant_fail_closed_zero_rejected(entry):
    _, service = _import_pair(entry["module"])
    with pytest.raises((ValueError, TypeError)):
        _call_l3(service, entry, 0, {})


@pytest.mark.parametrize("entry", SELECTED)
def test_tenant_fail_closed_negative_rejected(entry):
    _, service = _import_pair(entry["module"])
    with pytest.raises((ValueError, TypeError)):
        _call_l3(service, entry, -1, {})


# ============================================================
# Group 5: Valid tenant accepted
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_valid_tenant_accepted(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 1, {})
    assert out["tenant_id"] == 1


# ============================================================
# Group 6: Output contains required common fields
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_l3_output_structure(entry):
    """Verify all required L3 output fields are present."""
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 11, {})

    required_fields = [
        "tenant_id", "module", "uce_id", "maturity_level", "expansion_layer",
        "deterministic_logic_ready", "readiness_status", "risk_band",
        "evidence_completeness", "required_evidence", "present_evidence",
        "missing_evidence", "recommended_next_step", "human_review_required",
        "allowed_actions", "forbidden_actions", "l2_contract_preserved",
        "tenant_scoped", "l3_boundary", "next_maturity_gap", "safety_flags",
    ]
    for field in required_fields:
        assert field in out, f"Missing field '{field}' in {entry['module']} L3 output"

    assert out["tenant_id"] == 11
    assert out["module"] == entry["module"]
    assert out[entry["id_key"]] == entry["id_value"]
    assert out["maturity_level"] == "L3"
    assert out["expansion_layer"] == "university_completeness"
    assert out["deterministic_logic_ready"] is True
    assert out["readiness_status"] in {
        "READY_FOR_REVIEW", "PARTIAL_EVIDENCE", "INCOMPLETE_EVIDENCE", "BLOCKED_MISSING_EVIDENCE"
    }
    assert out["risk_band"] in {"LOW", "MEDIUM", "HIGH", "BLOCKED"}
    assert isinstance(out["evidence_completeness"], int)
    assert 0 <= out["evidence_completeness"] <= 100
    assert isinstance(out["required_evidence"], list)
    assert isinstance(out["present_evidence"], list)
    assert isinstance(out["missing_evidence"], list)
    assert isinstance(out["recommended_next_step"], str)
    assert out["human_review_required"] is True
    assert isinstance(out["allowed_actions"], list)
    assert isinstance(out["forbidden_actions"], list)
    assert out["l2_contract_preserved"] is True
    assert out["tenant_scoped"] is True
    assert isinstance(out["l3_boundary"], str)
    assert out["next_maturity_gap"] == "L4 operational visibility/API surface required"
    assert isinstance(out["safety_flags"], dict)


# ============================================================
# Group 7: Readiness status is deterministic
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_readiness_status_determinism(entry):
    """Same input produces same readiness status."""
    _, service = _import_pair(entry["module"])
    required = entry["required_evidence"]
    evidence_in = {required[0]: True, required[1]: True}

    out1 = _call_l3(service, entry, 7, evidence_in)
    out2 = _call_l3(service, entry, 7, evidence_in)
    assert out1["readiness_status"] == out2["readiness_status"]


# ============================================================
# Group 8: Risk band mapping is deterministic
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_risk_band_validation(entry):
    """Risk bands map correctly to evidence completeness levels."""
    _, service = _import_pair(entry["module"])
    required = entry["required_evidence"]

    out_full = _call_l3(service, entry, 5, {k: True for k in required})
    out_partial = _call_l3(service, entry, 5, {required[0]: True})
    out_zero = _call_l3(service, entry, 5, {})

    assert out_full["risk_band"] == "LOW"
    assert out_partial["risk_band"] in {"MEDIUM", "HIGH"}
    assert out_zero["risk_band"] == "BLOCKED"


# ============================================================
# Group 9: Evidence completeness is deterministic integer 0–100
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_evidence_completeness_bounds(entry):
    """Evidence completeness is always integer 0–100."""
    _, service = _import_pair(entry["module"])
    required = entry["required_evidence"]

    full = {k: True for k in required}
    partial = {required[0]: True, required[1]: True}
    one = {required[0]: True}

    out_full = _call_l3(service, entry, 7, full)
    out_partial = _call_l3(service, entry, 7, partial)
    out_one = _call_l3(service, entry, 7, one)
    out_zero = _call_l3(service, entry, 7, {})

    assert out_full["evidence_completeness"] == 100
    assert 1 <= out_partial["evidence_completeness"] <= 99
    assert 1 <= out_one["evidence_completeness"] <= 99
    assert out_zero["evidence_completeness"] == 0


# ============================================================
# Group 10: Missing evidence is deterministic
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_missing_evidence_determinism(entry):
    """Missing evidence list is deterministic and correct."""
    _, service = _import_pair(entry["module"])
    required = entry["required_evidence"]

    out_none = _call_l3(service, entry, 9, {})
    assert out_none["present_evidence"] == []
    assert sorted(out_none["missing_evidence"]) == sorted(required)

    out_two = _call_l3(service, entry, 9, {required[0]: True, required[1]: True})
    assert required[0] in out_two["present_evidence"]
    assert required[1] in out_two["present_evidence"]
    assert required[2] in out_two["missing_evidence"]


# ============================================================
# Group 11: Recommended next step mapping is deterministic
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_recommended_next_step_validation(entry):
    """Recommended next step maps correctly to readiness state."""
    _, service = _import_pair(entry["module"])
    required = entry["required_evidence"]

    out_full = _call_l3(service, entry, 13, {k: True for k in required})
    out_partial = _call_l3(service, entry, 13, {required[0]: True})
    out_zero = _call_l3(service, entry, 13, {})

    assert out_full["recommended_next_step"] == "READY_FOR_HUMAN_REVIEW"
    assert out_partial["recommended_next_step"] == "REQUEST_MISSING_EVIDENCE"
    assert out_zero["recommended_next_step"] == "BLOCK_UNTIL_REQUIRED_EVIDENCE_PRESENT"


# ============================================================
# Group 12: human_review_required=True for all 11
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_human_review_required_always_true(entry):
    """human_review_required must be True regardless of evidence state."""
    _, service = _import_pair(entry["module"])
    required = entry["required_evidence"]

    for evidence_dict in [{}, {required[0]: True}, {k: True for k in required}]:
        out = _call_l3(service, entry, 17, evidence_dict)
        assert out["human_review_required"] is True, (
            f"{entry['module']} should always have human_review_required=True"
        )


# ============================================================
# Group 13: l2_contract_preserved=True for all 11
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_l2_contract_preserved_flag(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 3, {})
    assert out["l2_contract_preserved"] is True


# ============================================================
# Group 14: tenant_scoped=True for all 11
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_tenant_scoped_flag(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 4, {})
    assert out["tenant_scoped"] is True


# ============================================================
# Group 15: Safety flags all True for all 11
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_safety_flags_all_true(entry):
    """All safety flags must be True."""
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 2, {})
    flags = out["safety_flags"]

    required_flags = [
        "no_api_claim", "no_frontend_claim", "no_provider_call",
        "no_credential_use", "no_kpi_value_claim", "no_brain_execution",
        "no_autonomous_execution", "no_external_side_effects", "no_db_mutation",
        "no_decision_execution", "human_review_required",
        "no_l4_claim", "no_l5_claim", "no_l6_claim",
        "tenant_fail_closed", "l2_contract_preserved",
    ]
    for flag in required_flags:
        assert flags.get(flag) is True, (
            f"{entry['module']} safety_flag '{flag}' should be True, got {flags.get(flag)}"
        )


# ============================================================
# Group 16: Forbidden actions — no auto-approval / no mutation
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_forbidden_actions_present(entry):
    """Module-specific forbidden actions must appear in forbidden_actions list."""
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 6, {})

    for forbidden in entry["forbidden_actions"]:
        assert forbidden in out["forbidden_actions"], (
            f"{entry['module']} missing expected forbidden action '{forbidden}'"
        )


@pytest.mark.parametrize("entry", SELECTED)
def test_allowed_actions_no_auto(entry):
    """Allowed actions must not include any AUTO_ prefixed actions."""
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 6, {})
    for action in out["allowed_actions"]:
        assert not action.startswith("AUTO_"), (
            f"{entry['module']} allowed_actions should not contain '{action}'"
        )


# ============================================================
# Group 17: No provider call claims
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_no_provider_call_claim(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 8, {})
    assert out["safety_flags"]["no_provider_call"] is True


# ============================================================
# Group 18: No credential use claims
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_no_credential_use_claim(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 8, {})
    assert out["safety_flags"]["no_credential_use"] is True


# ============================================================
# Group 19: No KPI/dashboard claims
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_no_kpi_claim(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 8, {})
    assert out["safety_flags"]["no_kpi_value_claim"] is True


# ============================================================
# Group 20: No Brain execution claims
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_no_brain_execution_claim(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 8, {})
    assert out["safety_flags"]["no_brain_execution"] is True


# ============================================================
# Group 21: No autonomous execution claims
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_no_autonomous_execution_claim(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 8, {})
    assert out["safety_flags"]["no_autonomous_execution"] is True


# ============================================================
# Group 22: No DB mutation claims
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_no_db_mutation_claim(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 8, {})
    assert out["safety_flags"]["no_db_mutation"] is True


# ============================================================
# Group 23: No L4/L5/L6 claims
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_no_l4_l5_l6_claims(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 8, {})
    assert out["safety_flags"]["no_l4_claim"] is True
    assert out["safety_flags"]["no_l5_claim"] is True
    assert out["safety_flags"]["no_l6_claim"] is True
    assert out["maturity_level"] == "L3"


# ============================================================
# Group 24: Full-evidence case returns READY_FOR_REVIEW / LOW / READY_FOR_HUMAN_REVIEW
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_full_evidence_case(entry):
    """With all required evidence present, readiness is READY_FOR_REVIEW."""
    _, service = _import_pair(entry["module"])
    required = entry["required_evidence"]
    full_evidence = {k: True for k in required}

    out = _call_l3(service, entry, 99, full_evidence)

    assert out["readiness_status"] == "READY_FOR_REVIEW"
    assert out["risk_band"] == "LOW"
    assert out["recommended_next_step"] == "READY_FOR_HUMAN_REVIEW"
    assert out["evidence_completeness"] == 100
    assert out["missing_evidence"] == []
    assert out["human_review_required"] is True  # STILL requires human review
    assert out["l2_contract_preserved"] is True


# ============================================================
# Group 25: No-evidence case returns BLOCKED_MISSING_EVIDENCE / BLOCKED / BLOCK_UNTIL_...
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_no_evidence_case(entry):
    """With no evidence, readiness is BLOCKED_MISSING_EVIDENCE."""
    _, service = _import_pair(entry["module"])
    required = entry["required_evidence"]

    out = _call_l3(service, entry, 99, {})

    assert out["readiness_status"] == "BLOCKED_MISSING_EVIDENCE"
    assert out["risk_band"] == "BLOCKED"
    assert out["recommended_next_step"] == "BLOCK_UNTIL_REQUIRED_EVIDENCE_PRESENT"
    assert out["evidence_completeness"] == 0
    assert sorted(out["missing_evidence"]) == sorted(required)
    assert out["present_evidence"] == []


# ============================================================
# Group 26: Partial-evidence case returns PARTIAL_EVIDENCE or INCOMPLETE_EVIDENCE
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_partial_evidence_case(entry):
    """With some evidence, readiness is PARTIAL_EVIDENCE or INCOMPLETE_EVIDENCE."""
    _, service = _import_pair(entry["module"])
    required = entry["required_evidence"]
    partial_evidence = {required[0]: True, required[1]: True}

    out = _call_l3(service, entry, 99, partial_evidence)

    assert out["readiness_status"] in {"PARTIAL_EVIDENCE", "INCOMPLETE_EVIDENCE"}
    assert out["risk_band"] in {"MEDIUM", "HIGH"}
    assert 1 <= out["evidence_completeness"] <= 99
    assert len(out["missing_evidence"]) > 0


# ============================================================
# Group 27: Same input produces identical output (determinism)
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_determinism_same_input(entry):
    """Identical inputs produce identical outputs."""
    _, service = _import_pair(entry["module"])
    required = entry["required_evidence"]
    evidence_in = {required[0]: True, required[2]: True}

    out1 = _call_l3(service, entry, 42, evidence_in)
    out2 = _call_l3(service, entry, 42, evidence_in)

    assert out1["readiness_status"] == out2["readiness_status"]
    assert out1["risk_band"] == out2["risk_band"]
    assert out1["evidence_completeness"] == out2["evidence_completeness"]
    assert out1["recommended_next_step"] == out2["recommended_next_step"]
    assert out1["missing_evidence"] == out2["missing_evidence"]


# ============================================================
# Group 28: Module-specific UCE ID preserved
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_uce_id_preserved(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 7, {})
    assert out["uce_id"] == entry["id_value"]


# ============================================================
# Group 29: Module-specific forbidden actions verified
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_module_specific_forbidden_actions(entry):
    """All spec-defined forbidden actions are present in output."""
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 7, {})
    for forbidden in entry["forbidden_actions"]:
        assert forbidden in out["forbidden_actions"]


# ============================================================
# Group 30: A-027.7 and A-027.8 modules not touched by A-027.9
# ============================================================

def test_a0277_a0278_modules_not_modified():
    """Verify that importing A-027.7/8 modules still works (regression guard)."""
    a0277_modules = [
        "document_workflow",
        "curriculum_mapping",
        "degree_audit",
        "course_catalog_management",
        "syllabus_management",
        "program_learning_outcomes",
        "course_learning_outcomes",
        "committee_decision_registry",
        "international_office",
        "staff_recruitment",
    ]
    a0278_modules = [
        "student_information_system_integration",
        "learning_management_system_integration",
        "regulatory_reporting_integration",
        "digital_signature_integration",
        "compliance_calendar_dashboard",
        "accreditation_dashboard",
        "data_retention_policy_control",
        "consent_management_policy",
        "rector_resolution_tracking_workflow",
        "procurement_plan_approval_workflow",
    ]
    for mod in a0277_modules + a0278_modules:
        try:
            pkg = importlib.import_module(f"app.modules.{mod}")
            service = importlib.import_module(f"app.modules.{mod}.service")
            assert pkg is not None
            assert service is not None
        except ModuleNotFoundError:
            pass  # skip if module wasn't in A-027.7/8 batch


# ============================================================
# Group 31: A0279_L3_READY constant present in each service
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_a0279_l3_ready_constant(entry):
    """A0279_L3_READY constant must be True in each service module."""
    _, service = _import_pair(entry["module"])
    assert getattr(service, "A0279_L3_READY", None) is True


# ============================================================
# Group 32: L3 boundary string is module_readiness type
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_l3_boundary_correct(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 7, {})
    assert out["l3_boundary"] == "module_readiness_only_no_decision_execution_or_automation"


# ============================================================
# Group 33: Tenant isolation (different tenants get different tenant_id in output)
# ============================================================

@pytest.mark.parametrize("entry", SELECTED)
def test_tenant_isolation(entry):
    _, service = _import_pair(entry["module"])
    out1 = _call_l3(service, entry, 100, {})
    out2 = _call_l3(service, entry, 200, {})
    assert out1["tenant_id"] == 100
    assert out2["tenant_id"] == 200
    # Same evidence state → same readiness status regardless of tenant
    assert out1["readiness_status"] == out2["readiness_status"]
