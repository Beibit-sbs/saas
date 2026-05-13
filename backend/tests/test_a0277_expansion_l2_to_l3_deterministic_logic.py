"""A-027.7 targeted tests for expansion L2->L3 deterministic logic."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest


SELECTED = [
    {
        "module": "document_workflow",
        "uce_id": "UCE-009",
        "classifier": "classify_document_workflow_readiness",
        "required_evidence": ["document_record", "routing_policy", "approval_matrix"],
        "forbidden_actions": [
            "AUTO_ROUTE_DOCUMENT",
            "AUTO_APPROVE_DOCUMENT",
            "AUTO_SIGN_DOCUMENT",
            "AUTO_DELETE_DOCUMENT",
        ],
    },
    {
        "module": "order_decree_registry",
        "uce_id": "UCE-011",
        "classifier": "classify_order_decree_registry_readiness",
        "required_evidence": ["order_draft", "legal_basis", "approval_authority"],
        "forbidden_actions": [
            "AUTO_ISSUE_DECREE",
            "AUTO_REGISTER_ORDER",
            "AUTO_SIGN_ORDER",
            "AUTO_ARCHIVE_WITHOUT_REVIEW",
        ],
    },
    {
        "module": "incoming_outgoing_correspondence",
        "uce_id": "UCE-013",
        "classifier": "classify_incoming_outgoing_correspondence_readiness",
        "required_evidence": ["correspondence_record", "routing_log", "response_owner"],
        "forbidden_actions": [
            "AUTO_SEND_OFFICIAL_RESPONSE",
            "AUTO_DELETE_CORRESPONDENCE",
            "AUTO_CLOSE_WITHOUT_REVIEW",
        ],
    },
    {
        "module": "document_template_library",
        "uce_id": "UCE-089",
        "classifier": "classify_document_template_library_readiness",
        "required_evidence": ["template_content", "owner_review", "legal_review"],
        "forbidden_actions": [
            "AUTO_APPROVE_TEMPLATE",
            "AUTO_PUBLISH_TEMPLATE",
            "AUTO_DELETE_TEMPLATE",
        ],
    },
    {
        "module": "course_catalog_management",
        "uce_id": "UCE-076",
        "classifier": "classify_course_catalog_management_readiness",
        "required_evidence": ["course_description", "syllabus_reference", "department_approval"],
        "forbidden_actions": [
            "AUTO_PUBLISH_COURSE",
            "AUTO_DELETE_COURSE",
            "AUTO_CHANGE_CREDIT_VALUE",
        ],
    },
    {
        "module": "syllabus_management",
        "uce_id": "UCE-015",
        "classifier": "classify_syllabus_management_readiness",
        "required_evidence": ["syllabus_content", "learning_outcomes", "department_review"],
        "forbidden_actions": [
            "AUTO_APPROVE_SYLLABUS",
            "AUTO_CHANGE_ASSESSMENT_RULES",
            "AUTO_PUBLISH_SYLLABUS",
        ],
    },
    {
        "module": "curriculum_mapping",
        "uce_id": "UCE-014",
        "classifier": "classify_curriculum_mapping_readiness",
        "required_evidence": ["curriculum_structure", "outcome_mapping", "approval_record"],
        "forbidden_actions": [
            "AUTO_CHANGE_CURRICULUM",
            "AUTO_APPROVE_OUTCOME_MAPPING",
            "AUTO_MODIFY_PROGRAM_REQUIREMENTS",
        ],
    },
    {
        "module": "prerequisite_management",
        "uce_id": "UCE-074",
        "classifier": "classify_prerequisite_management_readiness",
        "required_evidence": ["curriculum_rule", "course_dependency", "approval_record"],
        "forbidden_actions": [
            "AUTO_CHANGE_PREREQUISITE",
            "AUTO_OVERRIDE_STUDENT_ELIGIBILITY",
            "AUTO_REGISTER_STUDENT",
        ],
    },
    {
        "module": "degree_audit",
        "uce_id": "UCE-092",
        "classifier": "classify_degree_audit_readiness",
        "required_evidence": ["transcript", "curriculum_requirements", "exception_approval"],
        "forbidden_actions": [
            "AUTO_GRADUATE_STUDENT",
            "AUTO_OVERRIDE_REQUIREMENT",
            "AUTO_CHANGE_TRANSCRIPT",
        ],
    },
    {
        "module": "transfer_credit_management",
        "uce_id": "UCE-075",
        "classifier": "classify_transfer_credit_management_readiness",
        "required_evidence": ["external_transcript", "equivalency_mapping", "approval_record"],
        "forbidden_actions": [
            "AUTO_APPROVE_CREDIT",
            "AUTO_CHANGE_GPA",
            "AUTO_MODIFY_ACADEMIC_RECORD",
        ],
    },
]


def _import_pair(module_name: str):
    pkg = importlib.import_module(f"app.modules.{module_name}")
    service = importlib.import_module(f"app.modules.{module_name}.service")
    return pkg, service


def _foundation_fn_name(module_name: str) -> str:
    return f"get_{module_name}_foundation_contract"


def _call_foundation(service_module, module_name: str, tenant_id: int):
    fn = getattr(service_module, _foundation_fn_name(module_name))
    return fn(tenant_id=tenant_id, payload={"probe": "yes"})


def _call_classifier(service_module, classifier_name: str, tenant_id: int, evidence: dict | None = None):
    fn = getattr(service_module, classifier_name)
    return fn(tenant_id=tenant_id, evidence=evidence)


@pytest.mark.parametrize("entry", SELECTED)
def test_import_validation(entry):
    module_name = entry["module"]
    _, service = _import_pair(module_name)

    foundation_fn = getattr(service, _foundation_fn_name(module_name), None)
    classifier_fn = getattr(service, entry["classifier"], None)

    assert callable(foundation_fn)
    assert callable(classifier_fn)


@pytest.mark.parametrize("entry", SELECTED)
def test_l2_contract_preservation(entry):
    module_name = entry["module"]
    _, service = _import_pair(module_name)
    out = _call_foundation(service, module_name, 1)

    assert out["maturity_level"] == "L2"
    assert out["service_contract_ready"] is True or "FOUNDATION" in str(out.get("contract_status", ""))
    flags = out["safety_flags"]
    assert flags["no_api_claim"] is True
    assert flags["no_frontend_claim"] is True
    assert flags["no_provider_call"] is True
    assert flags["no_autonomous_execution"] is True


@pytest.mark.parametrize("entry", SELECTED)
def test_tenant_fail_closed_none_rejected(entry):
    _, service = _import_pair(entry["module"])
    with pytest.raises((ValueError, TypeError)):
        _call_classifier(service, entry["classifier"], None, {})


@pytest.mark.parametrize("entry", SELECTED)
def test_tenant_fail_closed_zero_rejected(entry):
    _, service = _import_pair(entry["module"])
    with pytest.raises((ValueError, TypeError)):
        _call_classifier(service, entry["classifier"], 0, {})


@pytest.mark.parametrize("entry", SELECTED)
def test_tenant_fail_closed_negative_rejected(entry):
    _, service = _import_pair(entry["module"])
    with pytest.raises((ValueError, TypeError)):
        _call_classifier(service, entry["classifier"], -1, {})


@pytest.mark.parametrize("entry", SELECTED)
def test_tenant_positive_accepted(entry):
    _, service = _import_pair(entry["module"])
    out = _call_classifier(service, entry["classifier"], 1, {})
    assert out["tenant_id"] == 1


@pytest.mark.parametrize("entry", SELECTED)
def test_l3_output_structure_validation(entry):
    _, service = _import_pair(entry["module"])
    out = _call_classifier(service, entry["classifier"], 11, {})

    assert isinstance(out, dict)
    assert out["tenant_id"] == 11
    assert out["module"] == entry["module"]
    assert out["uce_id"] == entry["uce_id"]
    assert out["maturity_level"] == "L3"
    assert out["expansion_layer"] == "university_completeness"
    assert out["deterministic_logic_ready"] is True
    assert out["readiness_status"] in {
        "READY_FOR_REVIEW",
        "PARTIAL_EVIDENCE",
        "INCOMPLETE_EVIDENCE",
        "BLOCKED_MISSING_EVIDENCE",
    }
    assert out["risk_band"] in {"LOW", "MEDIUM", "HIGH", "BLOCKED"}
    assert isinstance(out["evidence_completeness"], int)
    assert isinstance(out["missing_evidence"], list)
    assert isinstance(out["recommended_next_step"], str)
    assert out["human_review_required"] is True
    assert out["l2_contract_preserved"] is True
    assert out["next_maturity_gap"] == "L4 operational visibility/API surface required"


@pytest.mark.parametrize("entry", SELECTED)
def test_evidence_completeness_validation(entry):
    _, service = _import_pair(entry["module"])
    required = entry["required_evidence"]

    full = {k: True for k in required}
    two = {required[0]: True, required[1]: True}
    one = {required[0]: True}

    out_full = _call_classifier(service, entry["classifier"], 7, full)
    out_two = _call_classifier(service, entry["classifier"], 7, two)
    out_one = _call_classifier(service, entry["classifier"], 7, one)
    out_zero = _call_classifier(service, entry["classifier"], 7, {})

    assert out_full["evidence_completeness"] == 100
    assert 1 <= out_two["evidence_completeness"] <= 99
    assert 1 <= out_one["evidence_completeness"] <= 99
    assert out_zero["evidence_completeness"] == 0


@pytest.mark.parametrize("entry", SELECTED)
def test_readiness_classification_validation(entry):
    _, service = _import_pair(entry["module"])
    required = entry["required_evidence"]

    full = {k: True for k in required}
    two = {required[0]: True, required[1]: True}
    one = {required[0]: True}

    out_full = _call_classifier(service, entry["classifier"], 3, full)
    out_two = _call_classifier(service, entry["classifier"], 3, two)
    out_one = _call_classifier(service, entry["classifier"], 3, one)
    out_zero = _call_classifier(service, entry["classifier"], 3, {})

    assert out_full["readiness_status"] == "READY_FOR_REVIEW"
    assert out_two["readiness_status"] == "PARTIAL_EVIDENCE"
    assert out_one["readiness_status"] == "INCOMPLETE_EVIDENCE"
    assert out_zero["readiness_status"] == "BLOCKED_MISSING_EVIDENCE"


@pytest.mark.parametrize("entry", SELECTED)
def test_risk_band_validation(entry):
    _, service = _import_pair(entry["module"])
    required = entry["required_evidence"]

    out_full = _call_classifier(service, entry["classifier"], 5, {k: True for k in required})
    out_two = _call_classifier(service, entry["classifier"], 5, {required[0]: True, required[1]: True})
    out_one = _call_classifier(service, entry["classifier"], 5, {required[0]: True})
    out_zero = _call_classifier(service, entry["classifier"], 5, {})

    assert out_full["risk_band"] == "LOW"
    assert out_two["risk_band"] == "MEDIUM"
    assert out_one["risk_band"] == "HIGH"
    assert out_zero["risk_band"] == "BLOCKED"


@pytest.mark.parametrize("entry", SELECTED)
def test_missing_evidence_validation(entry):
    _, service = _import_pair(entry["module"])
    required = entry["required_evidence"]

    out_none = _call_classifier(service, entry["classifier"], 9, {})
    assert out_none["present_evidence"] == []
    assert out_none["missing_evidence"] == required

    out_two = _call_classifier(service, entry["classifier"], 9, {required[0]: True, required[1]: True})
    assert out_two["present_evidence"] == [required[0], required[1]]
    assert out_two["missing_evidence"] == [required[2]]


@pytest.mark.parametrize("entry", SELECTED)
def test_recommended_next_step_validation(entry):
    _, service = _import_pair(entry["module"])
    required = entry["required_evidence"]

    out_full = _call_classifier(service, entry["classifier"], 13, {k: True for k in required})
    out_two = _call_classifier(service, entry["classifier"], 13, {required[0]: True, required[1]: True})
    out_one = _call_classifier(service, entry["classifier"], 13, {required[0]: True})
    out_zero = _call_classifier(service, entry["classifier"], 13, {})

    assert out_full["recommended_next_step"] == "READY_FOR_HUMAN_REVIEW"
    assert out_two["recommended_next_step"] == "REQUEST_MISSING_EVIDENCE"
    assert out_one["recommended_next_step"] == "COLLECT_REQUIRED_EVIDENCE"
    assert out_zero["recommended_next_step"] == "BLOCK_UNTIL_REQUIRED_EVIDENCE_PRESENT"


@pytest.mark.parametrize("entry", SELECTED)
def test_human_review_boundary_validation(entry):
    _, service = _import_pair(entry["module"])
    out = _call_classifier(service, entry["classifier"], 17, {})

    assert out["human_review_required"] is True
    assert all("AUTO_" not in action for action in out["allowed_actions"])
    for forbidden in entry["forbidden_actions"]:
        assert forbidden in out["forbidden_actions"]


def test_uce_id_regression_validation():
    _, degree_service = _import_pair("degree_audit")
    _, transfer_service = _import_pair("transfer_credit_management")

    out_degree = _call_classifier(degree_service, "classify_degree_audit_readiness", 1, {})
    out_transfer = _call_classifier(transfer_service, "classify_transfer_credit_management_readiness", 1, {})

    assert out_degree["uce_id"] == "UCE-092"
    assert out_transfer["uce_id"] == "UCE-075"
    assert out_degree["uce_id"] != "UCE-081"
    assert out_transfer["uce_id"] != "UCE-082"


@pytest.mark.parametrize("entry", SELECTED)
def test_safety_flags_validation(entry):
    _, service = _import_pair(entry["module"])
    out = _call_classifier(service, entry["classifier"], 19, {})
    flags = out["safety_flags"]

    assert flags["no_api_claim"] is True
    assert flags["no_frontend_claim"] is True
    assert flags["no_provider_call"] is True
    assert flags["no_credential_use"] is True
    assert flags["no_kpi_value_claim"] is True
    assert flags["no_brain_execution"] is True
    assert flags["no_autonomous_execution"] is True
    assert flags["no_external_side_effects"] is True
    assert flags["no_db_mutation"] is True
    assert flags["no_l4_claim"] is True
    assert flags["no_l5_claim"] is True
    assert flags["no_l6_claim"] is True


@pytest.mark.parametrize("entry", SELECTED)
def test_determinism_validation(entry):
    _, service = _import_pair(entry["module"])
    required = entry["required_evidence"]
    evidence = {required[0]: True, required[2]: True}

    out1 = _call_classifier(service, entry["classifier"], 23, evidence)
    out2 = _call_classifier(service, entry["classifier"], 23, evidence)
    assert out1 == out2


@pytest.mark.parametrize("entry", SELECTED)
def test_anti_inflation_validation(entry):
    _, service = _import_pair(entry["module"])
    out = _call_classifier(service, entry["classifier"], 29, {})

    assert out["maturity_level"] == "L3"
    assert out["deterministic_logic_ready"] is True

    src = Path(service.__file__).read_text(encoding="utf-8")
    forbidden_tokens = [
        "APIRouter",
        "@router",
        "@app.get",
        "@app.post",
        "requests.",
        "httpx",
        "aiohttp",
        "send_email",
        "send_sms",
        "provider.call",
        "openai",
        "llm",
        "execute_brain",
        "brain_execute",
    ]
    for token in forbidden_tokens:
        assert token not in src
