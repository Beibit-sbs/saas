"""A-027.8 targeted tests for expansion L2->L3 deterministic logic batch 2."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest


SELECTED = [
    {
        "module": "student_information_system_integration",
        "type": "INTEGRATION",
        "id_key": "original_uce_id",
        "id_value": "UCE-024",
        "l2_fn": "get_student_information_system_integration_integration_contract",
        "classifier": "classify_student_information_system_integration_readiness",
        "required_evidence": [
            "provider_contract_document",
            "tenant_mapping_policy",
            "data_schema_mapping",
        ],
        "forbidden_actions": [
            "LIVE_PLATONUS_CALL",
            "AUTO_SYNC_STUDENTS",
            "AUTO_MUTATE_SIS_DATA",
        ],
        "provider_profile": "PLATONUS_KZ",
        "provider_placeholder": "SA_SIS_PROVIDER",
    },
    {
        "module": "learning_management_system_integration",
        "type": "INTEGRATION",
        "id_key": "original_uce_id",
        "id_value": "UCE-106",
        "l2_fn": "get_learning_management_system_integration_integration_contract",
        "classifier": "classify_learning_management_system_integration_readiness",
        "required_evidence": [
            "lms_provider_contract",
            "course_mapping_policy",
            "grade_sync_boundary_policy",
        ],
        "forbidden_actions": [
            "LIVE_LMS_CALL",
            "AUTO_SYNC_GRADES",
            "AUTO_CREATE_COURSE",
        ],
        "provider_profile": "LMS_KZ",
        "provider_placeholder": "SA_LMS_PROVIDER",
    },
    {
        "module": "regulatory_reporting_integration",
        "type": "INTEGRATION",
        "id_key": "original_uce_id",
        "id_value": "UCE-112",
        "l2_fn": "get_regulatory_reporting_integration_integration_contract",
        "classifier": "classify_regulatory_reporting_integration_readiness",
        "required_evidence": [
            "reporting_template_registry",
            "ministry_channel_policy",
            "approval_workflow_policy",
        ],
        "forbidden_actions": [
            "LIVE_MINISTRY_SUBMISSION",
            "AUTO_SUBMIT_REPORT",
            "AUTO_CERTIFY_REPORT",
        ],
        "provider_profile": "MINISTRY_KZ",
        "provider_placeholder": "SA_REGULATORY_REPORTING_PROVIDER",
    },
    {
        "module": "digital_signature_integration",
        "type": "INTEGRATION",
        "id_key": "original_uce_id",
        "id_value": "UCE-109",
        "l2_fn": "get_digital_signature_integration_integration_contract",
        "classifier": "classify_digital_signature_integration_readiness",
        "required_evidence": [
            "signature_provider_policy",
            "key_management_boundary",
            "signer_authorization_policy",
        ],
        "forbidden_actions": [
            "LIVE_EDS_SIGNING",
            "AUTO_SIGN_DOCUMENT",
            "STORE_PRIVATE_KEY",
        ],
        "provider_profile": "EDS_KZ",
        "provider_placeholder": "SA_DIGITAL_SIGNATURE_PROVIDER",
    },
    {
        "module": "compliance_calendar_dashboard",
        "type": "REPORT_DASHBOARD",
        "id_key": "uce_id",
        "id_value": "UCE-122",
        "l2_fn": "get_compliance_calendar_dashboard_envelope_contract",
        "classifier": "classify_compliance_calendar_dashboard_readiness",
        "required_evidence": [
            "compliance_calendar_source",
            "deadline_owner_matrix",
            "escalation_policy",
        ],
        "forbidden_actions": [
            "AUTO_RENDER_DASHBOARD",
            "AUTO_COMPUTE_KPI",
            "AUTO_PUBLISH_METRIC",
        ],
    },
    {
        "module": "ministry_reporting_dashboard",
        "type": "REPORT_DASHBOARD",
        "id_key": "uce_id",
        "id_value": "UCE-032",
        "l2_fn": "get_ministry_reporting_dashboard_envelope_contract",
        "classifier": "classify_ministry_reporting_dashboard_readiness",
        "required_evidence": [
            "reporting_template_registry",
            "reporting_period_policy",
            "approval_workflow_policy",
        ],
        "forbidden_actions": [
            "AUTO_RENDER_DASHBOARD",
            "AUTO_COMPUTE_KPI",
            "AUTO_SUBMIT_REPORT",
        ],
    },
    {
        "module": "accreditation_dashboard",
        "type": "REPORT_DASHBOARD",
        "id_key": "uce_id",
        "id_value": "UCE-114",
        "l2_fn": "get_accreditation_dashboard_envelope_contract",
        "classifier": "classify_accreditation_dashboard_readiness",
        "required_evidence": [
            "accreditation_standard_mapping",
            "evidence_source_registry",
            "reviewer_role_matrix",
        ],
        "forbidden_actions": [
            "AUTO_RENDER_DASHBOARD",
            "AUTO_COMPUTE_KPI",
            "AUTO_CERTIFY_ACCREDITATION",
        ],
    },
    {
        "module": "rector_strategy_dashboard",
        "type": "REPORT_DASHBOARD",
        "id_key": "uce_id",
        "id_value": "UCE-031",
        "l2_fn": "get_rector_strategy_dashboard_envelope_contract",
        "classifier": "classify_rector_strategy_dashboard_readiness",
        "required_evidence": [
            "strategic_kpi_source_registry",
            "governance_review_policy",
            "executive_visibility_boundary",
        ],
        "forbidden_actions": [
            "AUTO_RENDER_DASHBOARD",
            "AUTO_COMPUTE_KPI",
            "AUTO_PUBLISH_EXECUTIVE_VIEW",
        ],
    },
    {
        "module": "data_retention_policy_control",
        "type": "POLICY_CONTROL",
        "id_key": "uce_id",
        "id_value": "UCE-048",
        "l2_fn": "get_data_retention_policy_control_envelope_contract",
        "classifier": "classify_data_retention_policy_control_readiness",
        "required_evidence": [
            "retention_schedule",
            "data_category_mapping",
            "approval_authority",
        ],
        "forbidden_actions": [
            "AUTO_ENFORCE_POLICY",
            "AUTO_DELETE_RECORD",
            "AUTO_BLOCK_PROCESSING",
        ],
    },
    {
        "module": "consent_management_policy",
        "type": "POLICY_CONTROL",
        "id_key": "uce_id",
        "id_value": "UCE-046",
        "l2_fn": "get_consent_management_policy_envelope_contract",
        "classifier": "classify_consent_management_policy_readiness",
        "required_evidence": [
            "consent_template_registry",
            "consent_scope_mapping",
            "revocation_policy",
        ],
        "forbidden_actions": [
            "AUTO_ENFORCE_POLICY",
            "AUTO_APPROVE_CONSENT",
            "AUTO_REVOKE_CONSENT",
        ],
    },
    {
        "module": "rector_resolution_tracking_workflow",
        "type": "WORKFLOW",
        "id_key": "uce_id",
        "id_value": "UCE-099",
        "l2_fn": "get_rector_resolution_tracking_workflow_envelope_contract",
        "classifier": "classify_rector_resolution_tracking_workflow_readiness",
        "required_evidence": [
            "resolution_record",
            "responsible_owner_matrix",
            "status_review_policy",
        ],
        "forbidden_actions": [
            "AUTO_EXECUTE_WORKFLOW",
            "AUTO_ROUTE_RESOLUTION",
            "AUTO_APPROVE_RESOLUTION",
        ],
    },
    {
        "module": "procurement_plan_approval_workflow",
        "type": "WORKFLOW",
        "id_key": "uce_id",
        "id_value": "UCE-098",
        "l2_fn": "get_procurement_plan_approval_workflow_envelope_contract",
        "classifier": "classify_procurement_plan_approval_workflow_readiness",
        "required_evidence": [
            "procurement_plan",
            "budget_reference",
            "approval_matrix",
        ],
        "forbidden_actions": [
            "AUTO_EXECUTE_WORKFLOW",
            "AUTO_ROUTE_APPROVAL",
            "AUTO_APPROVE_PROCUREMENT_PLAN",
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


@pytest.mark.parametrize("entry", SELECTED)
def test_import_validation(entry):
    _, service = _import_pair(entry["module"])
    assert callable(getattr(service, entry["l2_fn"], None))
    assert callable(getattr(service, entry["classifier"], None))


@pytest.mark.parametrize("entry", SELECTED)
def test_l2_contract_envelope_preservation(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l2(service, entry, 1)

    assert out["maturity_level"] == "L2"
    flags = out["safety_flags"]
    assert flags["no_api_claim"] is True
    assert flags["no_frontend_claim"] is True
    assert flags["no_provider_call"] is True
    assert flags["no_autonomous_execution"] is True

    if entry["type"] == "INTEGRATION":
        assert out["country_adapter_ready"] is True
        assert out["live_provider_call_allowed"] is False
    else:
        assert out["envelope_only"] is True
        assert out["runtime_execution_allowed"] is False


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


@pytest.mark.parametrize("entry", SELECTED)
def test_tenant_positive_accepted(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 1, {})
    assert out["tenant_id"] == 1


@pytest.mark.parametrize("entry", SELECTED)
def test_l3_output_structure_validation(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 11, {})

    assert isinstance(out, dict)
    assert out["tenant_id"] == 11
    assert out["module"] == entry["module"]
    assert out[entry["id_key"]] == entry["id_value"]
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
    assert isinstance(out["l3_boundary"], str)
    assert out["next_maturity_gap"] == "L4 operational visibility/API surface required"


@pytest.mark.parametrize("entry", SELECTED)
def test_evidence_completeness_validation(entry):
    _, service = _import_pair(entry["module"])
    required = entry["required_evidence"]

    full = {k: True for k in required}
    two = {required[0]: True, required[1]: True}
    one = {required[0]: True}

    out_full = _call_l3(service, entry, 7, full)
    out_two = _call_l3(service, entry, 7, two)
    out_one = _call_l3(service, entry, 7, one)
    out_zero = _call_l3(service, entry, 7, {})

    assert out_full["evidence_completeness"] == 100
    assert 1 <= out_two["evidence_completeness"] <= 99
    assert 1 <= out_one["evidence_completeness"] <= 99
    assert out_zero["evidence_completeness"] == 0


@pytest.mark.parametrize("entry", SELECTED)
def test_readiness_classification_validation(entry):
    _, service = _import_pair(entry["module"])
    required = entry["required_evidence"]

    out_full = _call_l3(service, entry, 3, {k: True for k in required})
    out_partial = _call_l3(service, entry, 3, {required[0]: True, required[1]: True})
    out_zero = _call_l3(service, entry, 3, {})

    assert out_full["readiness_status"] == "READY_FOR_REVIEW"
    assert out_partial["readiness_status"] in {"PARTIAL_EVIDENCE", "INCOMPLETE_EVIDENCE"}
    assert out_zero["readiness_status"] == "BLOCKED_MISSING_EVIDENCE"


@pytest.mark.parametrize("entry", SELECTED)
def test_risk_band_validation(entry):
    _, service = _import_pair(entry["module"])
    required = entry["required_evidence"]

    out_full = _call_l3(service, entry, 5, {k: True for k in required})
    out_partial = _call_l3(service, entry, 5, {required[0]: True})
    out_zero = _call_l3(service, entry, 5, {})

    assert out_full["risk_band"] == "LOW"
    assert out_partial["risk_band"] in {"MEDIUM", "HIGH"}
    assert out_zero["risk_band"] == "BLOCKED"


@pytest.mark.parametrize("entry", SELECTED)
def test_missing_evidence_validation(entry):
    _, service = _import_pair(entry["module"])
    required = entry["required_evidence"]

    out_none = _call_l3(service, entry, 9, {})
    assert out_none["present_evidence"] == []
    assert out_none["missing_evidence"] == required

    out_two = _call_l3(service, entry, 9, {required[0]: True, required[1]: True})
    assert out_two["present_evidence"] == [required[0], required[1]]
    assert out_two["missing_evidence"] == [required[2]]


@pytest.mark.parametrize("entry", SELECTED)
def test_recommended_next_step_validation(entry):
    _, service = _import_pair(entry["module"])
    required = entry["required_evidence"]

    out_full = _call_l3(service, entry, 13, {k: True for k in required})
    out_partial = _call_l3(service, entry, 13, {required[0]: True})
    out_zero = _call_l3(service, entry, 13, {})

    assert out_full["recommended_next_step"] == "READY_FOR_HUMAN_REVIEW"
    assert out_partial["recommended_next_step"] == "REQUEST_MISSING_EVIDENCE"
    assert out_zero["recommended_next_step"] == "BLOCK_UNTIL_REQUIRED_EVIDENCE_PRESENT"


@pytest.mark.parametrize("entry", SELECTED)
def test_human_review_boundary_validation(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 17, {})

    assert out["human_review_required"] is True
    assert all("AUTO_" not in action for action in out["allowed_actions"])
    for forbidden in entry["forbidden_actions"]:
        assert forbidden in out["forbidden_actions"]


@pytest.mark.parametrize("entry", [e for e in SELECTED if e["type"] == "INTEGRATION"])
def test_integration_readiness_boundary_validation(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 21, {})

    assert out["live_provider_call_allowed"] is False
    assert out["credentials_required_for_contract"] is False
    assert out["country_adapter_ready"] is True
    assert out["default_country_code"] == "KZ"
    assert out["default_provider_profile"] == entry["provider_profile"]
    assert entry["provider_placeholder"] in out["future_provider_profile_placeholders"]
    assert "LIVE_" not in " ".join(out["allowed_actions"])


@pytest.mark.parametrize("entry", [e for e in SELECTED if e["type"] == "REPORT_DASHBOARD"])
def test_dashboard_anti_fake_validation(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 25, {})

    flags = out["safety_flags"]
    assert flags["no_kpi_value_claim"] is True
    assert flags["no_fake_dashboard"] is True
    assert flags["no_frontend_claim"] is True
    assert "kpi" not in " ".join(out["allowed_actions"]).lower()
    assert "render" not in " ".join(out["allowed_actions"]).lower()


@pytest.mark.parametrize("entry", [e for e in SELECTED if e["type"] == "POLICY_CONTROL"])
def test_policy_non_enforcement_validation(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 27, {})

    flags = out["safety_flags"]
    assert flags["no_policy_enforcement"] is True
    assert any(token in " ".join(out["forbidden_actions"]) for token in ["AUTO_ENFORCE", "AUTO_DELETE", "AUTO_BLOCK", "AUTO_APPROVE"])
    assert "policy_readiness_only" in out["l3_boundary"]


@pytest.mark.parametrize("entry", [e for e in SELECTED if e["type"] == "WORKFLOW"])
def test_workflow_non_execution_validation(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 31, {})

    assert "workflow_readiness_only" in out["l3_boundary"]
    assert any(token in " ".join(out["forbidden_actions"]) for token in ["AUTO_EXECUTE", "AUTO_ROUTE", "AUTO_APPROVE"])


@pytest.mark.parametrize("entry", SELECTED)
def test_safety_flags_validation(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 19, {})
    flags = out["safety_flags"]

    assert flags["no_api_claim"] is True
    assert flags["no_frontend_claim"] is True
    assert flags["no_provider_call"] is True
    assert flags["no_live_integration_call"] is True
    assert flags["no_credential_use"] is True
    assert flags["no_secret_storage"] is True
    assert flags["no_kpi_value_claim"] is True
    assert flags["no_fake_dashboard"] is True
    assert flags["no_policy_enforcement"] is True
    assert flags["no_report_submission"] is True
    assert flags["no_document_signature"] is True
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

    out1 = _call_l3(service, entry, 23, evidence)
    out2 = _call_l3(service, entry, 23, evidence)
    assert out1 == out2


@pytest.mark.parametrize("entry", SELECTED)
def test_anti_inflation_validation(entry):
    _, service = _import_pair(entry["module"])
    out = _call_l3(service, entry, 29, {})

    assert out["maturity_level"] == "L3"
    assert out["deterministic_logic_ready"] is True

    src = Path(service.__file__).read_text(encoding="utf-8")
    forbidden_tokens = [
        "APIRouter",
        "@router",
        "@app.get",
        "@app.post",
        "publish_event",
        "execute_brain",
        "brain_execute",
        "send_email",
        "send_sms",
        "push_provider",
        "auto_apply",
        "autonomous_decision",
        "openai",
        "llm",
        "provider.call",
        "requests.post",
        "httpx",
        "aiohttp",
    ]
    for token in forbidden_tokens:
        assert token not in src
