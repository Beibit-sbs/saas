"""A-027.6 envelope foundation runtime tests.

These tests verify deterministic L2 envelope contracts only.
No execution, side effects, or maturity inflation is allowed.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest


SELECTED = [
    ("UCE-054", "brain_decision_audit_trail", "AUDIT_EVIDENCE_CAPABILITY", "audit_evidence_contract"),
    ("UCE-049", "student_risk_signal_registry", "BRAIN_SIGNAL", "brain_signal_envelope"),
    ("UCE-050", "finance_anomaly_signal_registry", "BRAIN_SIGNAL", "brain_signal_envelope"),
    ("UCE-129", "procurement_risk_signal_registry", "BRAIN_SIGNAL", "brain_signal_envelope"),
    ("UCE-051", "academic_quality_signal_registry", "BRAIN_SIGNAL", "brain_signal_envelope"),
    ("UCE-122", "compliance_calendar_dashboard", "REPORT_DASHBOARD", "report_dashboard_contract"),
    ("UCE-032", "ministry_reporting_dashboard", "REPORT_DASHBOARD", "report_dashboard_contract"),
    ("UCE-114", "accreditation_dashboard", "REPORT_DASHBOARD", "report_dashboard_contract"),
    ("UCE-031", "rector_strategy_dashboard", "REPORT_DASHBOARD", "report_dashboard_contract"),
    ("UCE-048", "data_retention_policy_control", "POLICY_CONTROL", "policy_control_contract"),
    ("UCE-046", "consent_management_policy", "POLICY_CONTROL", "policy_control_contract"),
    ("UCE-047", "third_party_risk_policy", "POLICY_CONTROL", "policy_control_contract"),
    ("UCE-099", "rector_resolution_tracking_workflow", "WORKFLOW", "workflow_contract"),
    ("UCE-037", "scholarship_committee_workflow", "WORKFLOW", "workflow_contract"),
    ("UCE-038", "student_appeals_workflow", "WORKFLOW", "workflow_contract"),
    ("UCE-098", "procurement_plan_approval_workflow", "WORKFLOW", "workflow_contract"),
    ("UCE-145", "safe_evidence_summary_agent", "AUTONOMOUS_WORKFLOW_CANDIDATE", "autonomous_candidate_envelope"),
    ("UCE-146", "safe_task_drafting_agent", "AUTONOMOUS_WORKFLOW_CANDIDATE", "autonomous_candidate_envelope"),
]


def _import_pair(module_name: str):
    pkg = importlib.import_module(f"app.modules.{module_name}")
    service = importlib.import_module(f"app.modules.{module_name}.service")
    return pkg, service


def _get_contract(service_module, module_name: str, tenant_id: int):
    fn = getattr(service_module, f"get_{module_name}_envelope_contract")
    return fn(tenant_id=tenant_id, payload={"probe": "yes"})


@pytest.mark.parametrize("_uce,module_name,_ctype,_kind", SELECTED)
def test_import_validation_and_callable(_uce, module_name, _ctype, _kind):
    pkg, service = _import_pair(module_name)
    assert pkg is not None
    assert service is not None
    fn = getattr(service, f"get_{module_name}_envelope_contract", None)
    assert callable(fn)


@pytest.mark.parametrize("uce,module_name,ctype,_kind", SELECTED)
def test_package_metadata_validation(uce, module_name, ctype, _kind):
    pkg, _ = _import_pair(module_name)
    assert pkg.MODULE_NAME == module_name
    assert pkg.UCE_ID == uce
    assert pkg.CANDIDATE_TYPE == ctype
    assert pkg.TARGET_LEVEL == "L2"
    assert pkg.CONTRACT_VERSION == "A-027.6"
    assert pkg.ENVELOPE_ONLY is True
    assert pkg.RUNTIME_EXECUTION_ALLOWED is False


@pytest.mark.parametrize("_uce,module_name,_ctype,_kind", SELECTED)
def test_tenant_fail_closed_none_rejected(_uce, module_name, _ctype, _kind):
    _, service = _import_pair(module_name)
    with pytest.raises(ValueError):
        _get_contract(service, module_name, None)


@pytest.mark.parametrize("_uce,module_name,_ctype,_kind", SELECTED)
def test_tenant_fail_closed_zero_rejected(_uce, module_name, _ctype, _kind):
    _, service = _import_pair(module_name)
    with pytest.raises(ValueError):
        _get_contract(service, module_name, 0)


@pytest.mark.parametrize("_uce,module_name,_ctype,_kind", SELECTED)
def test_tenant_fail_closed_negative_rejected(_uce, module_name, _ctype, _kind):
    _, service = _import_pair(module_name)
    with pytest.raises(ValueError):
        _get_contract(service, module_name, -1)


@pytest.mark.parametrize("_uce,module_name,_ctype,_kind", SELECTED)
def test_tenant_positive_accepted(_uce, module_name, _ctype, _kind):
    _, service = _import_pair(module_name)
    out = _get_contract(service, module_name, 1)
    assert out["tenant_id"] == 1


@pytest.mark.parametrize("uce,module_name,ctype,kind", SELECTED)
def test_envelope_output_validation(uce, module_name, ctype, kind):
    _, service = _import_pair(module_name)
    out = _get_contract(service, module_name, 1)

    assert isinstance(out, dict)
    assert out["tenant_id"] == 1
    assert out["module"] == module_name
    assert out["uce_id"] == uce
    assert out["candidate_type"] == ctype
    assert out["maturity_level"] == "L2"
    assert out["expansion_layer"] == "university_completeness"
    assert out["contract_status"] == "ENVELOPE_READY"
    assert out["envelope_only"] is True
    assert out["runtime_execution_allowed"] is False
    assert out["human_approval_required"] is True
    assert out["tenant_scoped"] is True
    assert out["deterministic"] is True
    assert out["contract_kind"] == kind


@pytest.mark.parametrize("_uce,module_name,ctype,_kind", SELECTED)
def test_type_specific_contract_fields(_uce, module_name, ctype, _kind):
    _, service = _import_pair(module_name)
    out = _get_contract(service, module_name, 1)

    if ctype == "WORKFLOW":
        assert "workflow_stages" in out
        assert "actor_roles" in out
        assert "transition_boundaries" in out
        assert "required_evidence" in out
    elif ctype == "REPORT_DASHBOARD":
        assert "report_scope" in out
        assert "evidence_sources" in out
        assert "allowed_filters" in out
        assert "metric_boundary" in out
    elif ctype == "POLICY_CONTROL":
        assert "policy_scope" in out
        assert "rule_boundaries" in out
        assert "enforcement_boundary" in out
    elif ctype == "BRAIN_SIGNAL":
        assert "signal_scope" in out
        assert "required_signal_inputs" in out
        assert "confidence_boundary" in out
        assert "evidence_lineage_requirements" in out
    elif ctype == "AUDIT_EVIDENCE_CAPABILITY":
        assert "evidence_scope" in out
        assert "source_reference_model" in out
        assert "lineage_boundary" in out
        assert "auditability_boundary" in out
    elif ctype == "AUTONOMOUS_WORKFLOW_CANDIDATE":
        assert "allowed_draft_actions" in out
        assert "required_human_approval" in out
        assert "execution_forbidden_actions" in out
        assert "autonomy_safety_boundary" in out
    else:
        pytest.fail(f"Unsupported candidate type in test: {ctype}")


@pytest.mark.parametrize("_uce,module_name,_ctype,_kind", SELECTED)
def test_evidence_and_boundaries_non_empty(_uce, module_name, _ctype, _kind):
    _, service = _import_pair(module_name)
    out = _get_contract(service, module_name, 1)
    assert out["evidence_requirements"]
    assert out["human_review_boundary"]
    assert out["tenant_security_boundary"]


@pytest.mark.parametrize("_uce,module_name,ctype,_kind", SELECTED)
def test_no_brain_execution_validation(_uce, module_name, ctype, _kind):
    _, service = _import_pair(module_name)
    out = _get_contract(service, module_name, 1)
    assert out["runtime_execution_allowed"] is False
    assert out["safety_flags"]["no_brain_execution"] is True
    if ctype == "BRAIN_SIGNAL":
        assert "BRAIN_EXECUTE_DECISION" in out["forbidden_actions"]

    src = Path(service.__file__).read_text(encoding="utf-8")
    assert "def execute_" not in src
    assert "brain_execute" not in src


@pytest.mark.parametrize("_uce,module_name,_ctype,_kind", SELECTED)
def test_no_autonomous_execution_validation(_uce, module_name, _ctype, _kind):
    _, service = _import_pair(module_name)
    out = _get_contract(service, module_name, 1)
    assert out["safety_flags"]["no_autonomous_execution"] is True
    assert "AUTO_EXECUTE" in out["forbidden_actions"]
    assert "AUTONOMOUS_DECISION" in out["forbidden_actions"]
    assert out["human_approval_required"] is True


@pytest.mark.parametrize("_uce,module_name,ctype,_kind", SELECTED)
def test_no_fake_dashboard_or_kpi_validation(_uce, module_name, ctype, _kind):
    _, service = _import_pair(module_name)
    out = _get_contract(service, module_name, 1)
    if ctype == "REPORT_DASHBOARD":
        assert "kpi_value" not in out
        assert "metric_values" not in out
        assert out["safety_flags"]["no_fake_dashboard"] is True
        assert out["safety_flags"]["no_kpi_value_claim"] is True


@pytest.mark.parametrize("_uce,module_name,_ctype,_kind", SELECTED)
def test_safety_flags_validation(_uce, module_name, _ctype, _kind):
    _, service = _import_pair(module_name)
    out = _get_contract(service, module_name, 1)
    flags = out["safety_flags"]

    assert flags["no_api_claim"] is True
    assert flags["no_frontend_claim"] is True
    assert flags["no_db_claim"] is True
    assert flags["no_kpi_value_claim"] is True
    assert flags["no_fake_dashboard"] is True
    assert flags["no_brain_execution"] is True
    assert flags["no_autonomous_execution"] is True
    assert flags["human_approval_required"] is True
    assert flags["no_external_side_effects"] is True
    assert flags["no_provider_call"] is True
    assert flags["no_live_notification"] is True
    assert flags["no_document_signature"] is True
    assert flags["no_decision_enforcement"] is True
    assert flags["no_l3_claim"] is True
    assert flags["no_l4_claim"] is True
    assert flags["no_l5_claim"] is True
    assert flags["no_l6_claim"] is True


@pytest.mark.parametrize("_uce,module_name,_ctype,_kind", SELECTED)
def test_determinism_validation(_uce, module_name, _ctype, _kind):
    _, service = _import_pair(module_name)
    out1 = _get_contract(service, module_name, 11)
    out2 = _get_contract(service, module_name, 11)
    assert out1 == out2


def test_anti_inflation_validation_source_scan():
    forbidden_runtime_tokens = [
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
    ]

    for _uce, module_name, _ctype, _kind in SELECTED:
        _, service = _import_pair(module_name)
        src = Path(service.__file__).read_text(encoding="utf-8")
        for token in forbidden_runtime_tokens:
            assert token not in src, f"{module_name} contains forbidden token: {token}"
