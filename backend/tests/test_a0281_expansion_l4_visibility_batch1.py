"""A-028.1 targeted tests for expansion L3->L4 read-only visibility batch 1."""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture(autouse=True)
def reset_shared_state() -> None:
    # Keep this read-only contract suite isolated from heavy global reset overhead.
    yield


MODULE_CONFIGS = [
    {
        "id": "document_workflow",
        "module_path": "app.modules.document_workflow.service",
        "l3_func": "classify_document_workflow_readiness",
        "l4_func": "get_document_workflow_l4_visibility_summary",
        "l3_arg_name": "evidence",
        "l3_input_kind": "dict",
        "evidence": ["document_record", "routing_policy", "approval_matrix"],
        "forbidden": ["AUTO_ROUTE_DOCUMENT", "AUTO_APPROVE_DOCUMENT", "AUTO_SIGN_DOCUMENT", "AUTO_DELETE_DOCUMENT"],
        "visibility_type": "document_workflow_read_only_summary",
    },
    {
        "id": "order_decree_registry",
        "module_path": "app.modules.order_decree_registry.service",
        "l3_func": "classify_order_decree_registry_readiness",
        "l4_func": "get_order_decree_registry_l4_visibility_summary",
        "l3_arg_name": "evidence",
        "l3_input_kind": "dict",
        "evidence": ["order_draft", "legal_basis", "approval_authority"],
        "forbidden": ["AUTO_ISSUE_DECREE", "AUTO_REGISTER_ORDER", "AUTO_SIGN_ORDER", "AUTO_ARCHIVE_WITHOUT_REVIEW"],
        "visibility_type": "order_decree_registry_governance_summary",
    },
    {
        "id": "incoming_outgoing_correspondence",
        "module_path": "app.modules.incoming_outgoing_correspondence.service",
        "l3_func": "classify_incoming_outgoing_correspondence_readiness",
        "l4_func": "get_incoming_outgoing_correspondence_l4_visibility_summary",
        "l3_arg_name": "evidence",
        "l3_input_kind": "dict",
        "evidence": ["correspondence_record", "routing_log", "response_owner"],
        "forbidden": ["AUTO_SEND_OFFICIAL_RESPONSE", "AUTO_DELETE_CORRESPONDENCE", "AUTO_CLOSE_WITHOUT_REVIEW"],
        "visibility_type": "incoming_outgoing_correspondence_operational_visibility",
    },
    {
        "id": "document_template_library",
        "module_path": "app.modules.document_template_library.service",
        "l3_func": "classify_document_template_library_readiness",
        "l4_func": "get_document_template_library_l4_visibility_summary",
        "l3_arg_name": "evidence",
        "l3_input_kind": "dict",
        "evidence": ["template_content", "owner_review", "legal_review"],
        "forbidden": ["AUTO_APPROVE_TEMPLATE", "AUTO_PUBLISH_TEMPLATE", "AUTO_DELETE_TEMPLATE"],
        "visibility_type": "document_template_library_evidence_visibility",
    },
    {
        "id": "committee_decision_registry",
        "module_path": "app.modules.committee_decision_registry.service",
        "l3_func": "classify_committee_decision_registry_readiness",
        "l4_func": "get_committee_decision_registry_l4_visibility_summary",
        "l3_arg_name": "present_evidence",
        "l3_input_kind": "iterable",
        "evidence": [
            "committee_agenda_recorded",
            "decision_rationale_documented",
            "quorum_validation_recorded",
            "meeting_minutes_prepared",
            "signature_workflow_defined",
        ],
        "forbidden": ["AUTO_RECORD_DECISION", "AUTO_APPROVE_MINUTES", "AUTO_SIGN_PROTOCOL", "AUTO_PUBLISH_DECISION"],
        "visibility_type": "committee_decision_registry_review_queue_summary",
    },
    {
        "id": "rector_resolution_tracking_workflow",
        "module_path": "app.modules.rector_resolution_tracking_workflow.service",
        "l3_func": "classify_rector_resolution_tracking_workflow_readiness",
        "l4_func": "get_rector_resolution_tracking_workflow_l4_visibility_summary",
        "l3_arg_name": "evidence",
        "l3_input_kind": "dict",
        "evidence": ["resolution_record", "responsible_owner_matrix", "status_review_policy"],
        "forbidden": ["AUTO_EXECUTE_WORKFLOW", "AUTO_ROUTE_RESOLUTION", "AUTO_APPROVE_RESOLUTION"],
        "visibility_type": "rector_resolution_workflow_visibility_summary",
    },
    {
        "id": "compliance_calendar_dashboard",
        "module_path": "app.modules.compliance_calendar_dashboard.service",
        "l3_func": "classify_compliance_calendar_dashboard_readiness",
        "l4_func": "get_compliance_calendar_dashboard_l4_visibility_summary",
        "l3_arg_name": "evidence",
        "l3_input_kind": "dict",
        "evidence": ["compliance_calendar_source", "deadline_owner_matrix", "escalation_policy"],
        "forbidden": ["AUTO_RENDER_DASHBOARD", "AUTO_COMPUTE_KPI", "AUTO_PUBLISH_METRIC"],
        "visibility_type": "compliance_calendar_readiness_visibility",
    },
    {
        "id": "accreditation_dashboard",
        "module_path": "app.modules.accreditation_dashboard.service",
        "l3_func": "classify_accreditation_dashboard_readiness",
        "l4_func": "get_accreditation_dashboard_l4_visibility_summary",
        "l3_arg_name": "evidence",
        "l3_input_kind": "dict",
        "evidence": ["accreditation_standard_mapping", "evidence_source_registry", "reviewer_role_matrix"],
        "forbidden": ["AUTO_RENDER_DASHBOARD", "AUTO_COMPUTE_KPI", "AUTO_CERTIFY_ACCREDITATION"],
        "visibility_type": "accreditation_evidence_visibility_summary",
    },
    {
        "id": "ministry_reporting_dashboard",
        "module_path": "app.modules.ministry_reporting_dashboard.service",
        "l3_func": "classify_ministry_reporting_dashboard_readiness",
        "l4_func": "get_ministry_reporting_dashboard_l4_visibility_summary",
        "l3_arg_name": "evidence",
        "l3_input_kind": "dict",
        "evidence": ["reporting_template_registry", "reporting_period_policy", "approval_workflow_policy"],
        "forbidden": ["AUTO_RENDER_DASHBOARD", "AUTO_COMPUTE_KPI", "AUTO_SUBMIT_REPORT"],
        "visibility_type": "ministry_reporting_readiness_summary",
    },
    {
        "id": "rector_strategy_dashboard",
        "module_path": "app.modules.rector_strategy_dashboard.service",
        "l3_func": "classify_rector_strategy_dashboard_readiness",
        "l4_func": "get_rector_strategy_dashboard_l4_visibility_summary",
        "l3_arg_name": "evidence",
        "l3_input_kind": "dict",
        "evidence": ["strategic_kpi_source_registry", "governance_review_policy", "executive_visibility_boundary"],
        "forbidden": ["AUTO_RENDER_DASHBOARD", "AUTO_COMPUTE_KPI", "AUTO_PUBLISH_EXECUTIVE_VIEW"],
        "visibility_type": "rector_strategy_executive_visibility_summary",
    },
    {
        "id": "archive_retention_management",
        "module_path": "app.modules.archive_retention_management.service",
        "l3_func": "classify_archive_retention_management_readiness",
        "l4_func": "get_archive_retention_management_l4_visibility_summary",
        "l3_arg_name": "present_evidence",
        "l3_input_kind": "iterable",
        "evidence": [
            "retention_policy_defined",
            "legal_basis_documented",
            "record_inventory_verified",
            "disposal_review_checkpoint_required",
            "compliance_signoff_required",
        ],
        "forbidden": ["AUTO_DELETE_ARCHIVE", "AUTO_PURGE_RECORDS", "AUTO_CHANGE_RETENTION_PERIOD", "AUTO_EXECUTE_DISPOSAL"],
        "visibility_type": "archive_retention_readiness_visibility_report",
    },
    {
        "id": "international_office",
        "module_path": "app.modules.international_office.service",
        "l3_func": "classify_international_office_readiness",
        "l4_func": "get_international_office_l4_visibility_summary",
        "l3_arg_name": "present_evidence",
        "l3_input_kind": "iterable",
        "evidence": [
            "mobility_request_documented",
            "visa_requirements_checked",
            "partner_agreement_verified",
            "student_profile_validated",
            "country_compliance_review_required",
        ],
        "forbidden": ["AUTO_APPROVE_MOBILITY", "AUTO_ISSUE_VISA_DECISION", "AUTO_CONFIRM_PARTNERSHIP", "AUTO_GRANT_VISA"],
        "visibility_type": "international_operations_readiness_summary",
    },
]

COMMON_FIELDS = {
    "tenant_id",
    "module",
    "uce_id",
    "visibility_level",
    "source_maturity_level",
    "visibility_type",
    "readiness_summary",
    "risk_summary",
    "evidence_summary",
    "missing_evidence_summary",
    "human_review_queue_summary",
    "allowed_actions",
    "forbidden_actions",
    "tenant_scoped",
    "read_only",
    "no_mutation",
    "no_provider_call",
    "no_brain_execution",
    "no_autonomous_execution",
    "no_decision_execution",
    "no_fake_kpi",
    "no_synthetic_dashboard",
    "l3_contract_preserved",
    "audit_visibility_ready",
    "next_maturity_gap",
    "no_l5_claim",
    "no_l6_claim",
    "safety_flags",
}


def _load_module(cfg: dict) -> object:
    return importlib.import_module(cfg["module_path"])


def _build_l3_input(cfg: dict, evidence: list[str]) -> object:
    if cfg["l3_input_kind"] == "dict":
        return {item: True for item in evidence}
    return list(evidence)


def _call_l3(cfg: dict, *, tenant_id: int = 1, evidence: list[str] | None = None) -> dict:
    module = _load_module(cfg)
    l3_func = getattr(module, cfg["l3_func"])
    evidence = cfg["evidence"] if evidence is None else evidence
    return l3_func(tenant_id=tenant_id, **{cfg["l3_arg_name"]: _build_l3_input(cfg, evidence)})


def _call_l4(cfg: dict, *, tenant_id: int = 1, evidence: list[str] | None = None) -> dict:
    module = _load_module(cfg)
    l4_func = getattr(module, cfg["l4_func"])
    evidence = cfg["evidence"] if evidence is None else evidence
    return l4_func(tenant_id=tenant_id, present_evidence=list(evidence))


@pytest.mark.parametrize("cfg", MODULE_CONFIGS, ids=[cfg["id"] for cfg in MODULE_CONFIGS])
def test_a0281_import_validation_for_all_selected_modules(cfg: dict) -> None:
    assert _load_module(cfg) is not None


@pytest.mark.parametrize("cfg", MODULE_CONFIGS, ids=[cfg["id"] for cfg in MODULE_CONFIGS])
def test_a0281_existing_l3_functions_still_exist(cfg: dict) -> None:
    module = _load_module(cfg)
    assert hasattr(module, cfg["l3_func"])


@pytest.mark.parametrize("cfg", MODULE_CONFIGS, ids=[cfg["id"] for cfg in MODULE_CONFIGS])
def test_a0281_l4_summary_functions_exist(cfg: dict) -> None:
    module = _load_module(cfg)
    assert hasattr(module, cfg["l4_func"])


@pytest.mark.parametrize("invalid_tenant", [None, 0, -1, "1"])
@pytest.mark.parametrize("cfg", MODULE_CONFIGS, ids=[cfg["id"] for cfg in MODULE_CONFIGS])
def test_a0281_tenant_fail_closed_rejects_invalid_values(cfg: dict, invalid_tenant: object) -> None:
    with pytest.raises((ValueError, TypeError)):
        _call_l4(cfg, tenant_id=invalid_tenant)  # type: ignore[arg-type]


@pytest.mark.parametrize("cfg", MODULE_CONFIGS, ids=[cfg["id"] for cfg in MODULE_CONFIGS])
def test_a0281_valid_tenant_is_accepted_and_common_fields_exist(cfg: dict) -> None:
    out = _call_l4(cfg)
    assert COMMON_FIELDS.issubset(set(out))
    assert out["tenant_id"] == 1
    assert out["visibility_level"] == "L4"
    assert out["source_maturity_level"] == "L3"
    assert out["visibility_type"] == cfg["visibility_type"]
    assert out["tenant_scoped"] is True
    assert out["read_only"] is True
    assert out["no_mutation"] is True
    assert out["l3_contract_preserved"] is True
    assert out["no_provider_call"] is True
    assert out["no_brain_execution"] is True
    assert out["no_autonomous_execution"] is True
    assert out["no_decision_execution"] is True
    assert out["no_fake_kpi"] is True
    assert out["no_synthetic_dashboard"] is True
    assert out["audit_visibility_ready"] is True
    assert out["no_l5_claim"] is True
    assert out["no_l6_claim"] is True
    assert out["next_maturity_gap"] == "L5 governance/KPI/evidence automation required"
    assert out["allowed_actions"]
    assert out["forbidden_actions"]


@pytest.mark.parametrize("cfg", MODULE_CONFIGS, ids=[cfg["id"] for cfg in MODULE_CONFIGS])
def test_a0281_readiness_risk_and_evidence_summaries_are_backed_by_l3_output(cfg: dict) -> None:
    l3_out = _call_l3(cfg)
    l4_out = _call_l4(cfg)
    assert l4_out["readiness_summary"]["status"] == l3_out["readiness_status"]
    assert l4_out["readiness_summary"]["evidence_completeness"] == l3_out["evidence_completeness"]
    assert l4_out["risk_summary"]["risk_band"] == l3_out["risk_band"]
    assert l4_out["evidence_summary"]["required_evidence_count"] == len(l3_out["required_evidence"])
    assert l4_out["evidence_summary"]["present_evidence_count"] == len(l3_out["present_evidence"])
    assert l4_out["missing_evidence_summary"]["count"] == len(l3_out["missing_evidence"])
    assert l4_out["missing_evidence_summary"]["items"] == list(l3_out["missing_evidence"])
    assert l4_out["human_review_queue_summary"]["candidate_count"] == 1
    assert l4_out["human_review_queue_summary"]["ready_for_human_review_count"] == 1


@pytest.mark.parametrize("cfg", MODULE_CONFIGS, ids=[cfg["id"] for cfg in MODULE_CONFIGS])
def test_a0281_partial_evidence_produces_deterministic_missing_evidence_and_queue_summary(cfg: dict) -> None:
    partial_evidence = cfg["evidence"][:1]
    out = _call_l4(cfg, evidence=partial_evidence)
    assert out["readiness_summary"]["status"] != "READY_FOR_REVIEW"
    assert out["missing_evidence_summary"]["count"] == len(cfg["evidence"]) - 1
    assert out["missing_evidence_summary"]["has_missing_evidence"] is True
    assert out["human_review_queue_summary"]["candidate_count"] == 1
    assert out["human_review_queue_summary"]["pending_manual_evidence_count"] in {0, 1}
    assert out["no_decision_execution"] is True


@pytest.mark.parametrize("cfg", MODULE_CONFIGS, ids=[cfg["id"] for cfg in MODULE_CONFIGS])
def test_a0281_candidate_specific_forbidden_actions_are_present(cfg: dict) -> None:
    out = _call_l4(cfg)
    for forbidden_action in cfg["forbidden"]:
        assert forbidden_action in out["forbidden_actions"]


@pytest.mark.parametrize("cfg", MODULE_CONFIGS, ids=[cfg["id"] for cfg in MODULE_CONFIGS])
def test_a0281_same_input_produces_same_output(cfg: dict) -> None:
    first = _call_l4(cfg)
    second = _call_l4(cfg)
    assert first == second


@pytest.mark.parametrize("cfg", MODULE_CONFIGS, ids=[cfg["id"] for cfg in MODULE_CONFIGS])
def test_a0281_l4_summary_preserves_l3_callable_contract(cfg: dict) -> None:
    l3_out = _call_l3(cfg)
    assert l3_out["maturity_level"] == "L3"
    assert l3_out["l2_contract_preserved"] is True
    assert l3_out["next_maturity_gap"] == "L4 operational visibility/API surface required"