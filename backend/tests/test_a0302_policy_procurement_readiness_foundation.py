"""A-030.2 Policy/Procurement Readiness Foundation Batch — Targeted Tests.

Implements strict no-execution validation for:
  UCE-047 third_party_risk_policy
  UCE-048 data_retention_policy_control
  UCE-098 procurement_plan_approval_workflow

Assertions are intentionally broad (120+ range) to protect anti-fake boundaries.
"""
from __future__ import annotations

import importlib
from pathlib import Path
import re

import pytest


# Group 1 — module imports and function presence

def test_import_third_party_risk_policy_module():
    mod = importlib.import_module("app.modules.third_party_risk_policy.service")
    assert hasattr(mod, "get_third_party_risk_policy_readiness_foundation")


def test_import_data_retention_policy_control_module():
    mod = importlib.import_module("app.modules.data_retention_policy_control.service")
    assert hasattr(mod, "get_data_retention_policy_control_readiness_foundation")


def test_import_procurement_plan_approval_workflow_module():
    mod = importlib.import_module("app.modules.procurement_plan_approval_workflow.service")
    assert hasattr(mod, "get_procurement_plan_approval_workflow_readiness_foundation")


from app.modules.third_party_risk_policy.service import (  # noqa: E402
    get_third_party_risk_policy_readiness_foundation,
)
from app.modules.data_retention_policy_control.service import (  # noqa: E402
    get_data_retention_policy_control_readiness_foundation,
)
from app.modules.procurement_plan_approval_workflow.service import (  # noqa: E402
    get_procurement_plan_approval_workflow_readiness_foundation,
)


VALID_TENANT = 1
ALT_TENANT = 42

ALL_FUNCS = [
    (
        "UCE-047",
        "third_party_risk_policy",
        "Third Party Risk Policy",
        get_third_party_risk_policy_readiness_foundation,
    ),
    (
        "UCE-048",
        "data_retention_policy_control",
        "Data Retention Policy Control",
        get_data_retention_policy_control_readiness_foundation,
    ),
    (
        "UCE-098",
        "procurement_plan_approval_workflow",
        "Procurement Plan Approval Workflow",
        get_procurement_plan_approval_workflow_readiness_foundation,
    ),
]

INVALID_TENANTS = [None, 0, -1, "abc", 1.5]

ALLOWED_OUTPUTS_EXACT = {
    "readiness_metadata",
    "evidence_source_map",
    "required_evidence_list",
    "missing_evidence_list",
    "compliance_evidence_map",
    "human_review_reasons",
    "audit_event_category_map",
    "governance_risk_classification",
    "next_safe_setup_steps",
}

FORBIDDEN_OUTPUTS_COMMON = {
    "final approval",
    "final rejection",
    "procurement award",
    "vendor ranking",
    "financial commitment",
    "contract execution",
    "external submission",
    "payment action",
    "hidden score",
    "synthetic score",
    "autonomous decision",
    "workflow execution",
}

DISALLOWED_OUTPUT_TOKENS = [
    "approve",
    "reject",
    "award",
    "rank",
    "score",
    "recommend",
    "commitment",
    "contract",
    "payment",
    "submission",
]

CHANGED_RUNTIME_FILES = [
    Path("app/modules/third_party_risk_policy/service.py"),
    Path("app/modules/data_retention_policy_control/service.py"),
    Path("app/modules/procurement_plan_approval_workflow/service.py"),
]


def _result(fn):
    return fn(VALID_TENANT)


# Groups 2, 58, 59 — deterministic output and tenant scoping
@pytest.mark.parametrize("uce,module_key,module_name,fn", ALL_FUNCS)
def test_valid_tenant_returns_deterministic_dict(uce, module_key, module_name, fn):
    out1 = fn(VALID_TENANT)
    out2 = fn(VALID_TENANT)
    assert isinstance(out1, dict)
    assert out1 == out2


@pytest.mark.parametrize("uce,module_key,module_name,fn", ALL_FUNCS)
def test_different_valid_tenant_is_tenant_scoped(uce, module_key, module_name, fn):
    out1 = fn(VALID_TENANT)
    out2 = fn(ALT_TENANT)
    assert out1["tenant_id"] == VALID_TENANT
    assert out2["tenant_id"] == ALT_TENANT
    comparable1 = {k: v for k, v in out1.items() if k != "tenant_id"}
    comparable2 = {k: v for k, v in out2.items() if k != "tenant_id"}
    assert comparable1 == comparable2


# Group 3 — tenant fail-closed behavior
@pytest.mark.parametrize("_bad_tenant", INVALID_TENANTS)
@pytest.mark.parametrize("uce,module_key,module_name,fn", ALL_FUNCS)
def test_invalid_tenant_fail_closed(uce, module_key, module_name, fn, _bad_tenant):
    with pytest.raises((ValueError, TypeError)):
        fn(_bad_tenant)


# Groups 4..32 — contract invariants
@pytest.mark.parametrize("uce,module_key,module_name,fn", ALL_FUNCS)
def test_common_contract_invariants(uce, module_key, module_name, fn):
    result = _result(fn)

    assert result["uce_id"] == uce
    assert result["module_key"] == module_key
    assert result["module_name"] == module_name

    assert result["policy_procurement_layer"] == "FOUNDATION"
    assert result["policy_procurement_version"] == "A-030.2"
    assert result["maturity_target"] == "L3_DETERMINISTIC_READINESS_GOVERNANCE"
    assert result["readiness_mode"] == "READINESS_AND_EVIDENCE_ONLY"
    assert result["execution_mode"] == "NO_EXECUTION"

    assert result["approval_execution_enabled"] is False
    assert result["rejection_execution_enabled"] is False
    assert result["award_execution_enabled"] is False
    assert result["financial_commitment_enabled"] is False
    assert result["contract_execution_enabled"] is False
    assert result["external_submission_enabled"] is False
    assert result["ranking_enabled"] is False
    assert result["hidden_scoring_enabled"] is False
    assert result["synthetic_score_enabled"] is False
    assert result["autonomous_decision_enabled"] is False

    assert result["human_review_required"] is True
    assert result["tenant_scoped"] is True
    assert result["read_only"] is True
    assert result["no_mutation"] is True

    assert result["no_policy_execution"] is True
    assert result["no_procurement_execution"] is True
    assert result["no_auto_approval"] is True
    assert result["no_auto_rejection"] is True
    assert result["no_award_decision"] is True
    assert result["no_vendor_ranking"] is True
    assert result["no_financial_commitment"] is True
    assert result["no_contract_execution"] is True
    assert result["no_external_submission"] is True
    assert result["no_l5_claim"] is True
    assert result["no_l6_claim"] is True


# Groups 33, 34, 56, 57 — output boundary checks
@pytest.mark.parametrize("uce,module_key,module_name,fn", ALL_FUNCS)
def test_allowed_outputs_are_evidence_metadata_only(uce, module_key, module_name, fn):
    outputs = set(_result(fn)["allowed_outputs"])
    assert outputs == ALLOWED_OUTPUTS_EXACT


@pytest.mark.parametrize("uce,module_key,module_name,fn", ALL_FUNCS)
def test_forbidden_outputs_include_common_prohibitions(uce, module_key, module_name, fn):
    forbidden = set(_result(fn)["forbidden_outputs"])
    assert FORBIDDEN_OUTPUTS_COMMON.issubset(forbidden)


@pytest.mark.parametrize("uce,module_key,module_name,fn", ALL_FUNCS)
def test_no_recommendation_output_exists(uce, module_key, module_name, fn):
    result = _result(fn)
    assert "recommendation" not in result
    assert "recommendations" not in result
    assert "recommended_action" not in result


@pytest.mark.parametrize("uce,module_key,module_name,fn", ALL_FUNCS)
def test_no_score_or_ranking_fields_exist(uce, module_key, module_name, fn):
    result = _result(fn)
    keys = {k.lower() for k in result.keys()}
    disallowed = {
        "readiness_score",
        "risk_score",
        "weighted_score",
        "synthetic_score",
        "vendor_ranking",
        "ranking",
    }
    assert disallowed.isdisjoint(keys)


# Groups 40..44 — candidate-specific maps and forbidden actions

def test_candidate_specific_maps_exist():
    out047 = get_third_party_risk_policy_readiness_foundation(VALID_TENANT)
    out048 = get_data_retention_policy_control_readiness_foundation(VALID_TENANT)
    out098 = get_procurement_plan_approval_workflow_readiness_foundation(VALID_TENANT)

    assert "vendor_registry_evidence" in out047["evidence_source_map"]
    assert "risk_assessment_policy_evidence" in out047["evidence_source_map"]
    assert "contract_review_evidence" in out047["evidence_source_map"]
    assert "data_processing_agreement_evidence" in out047["evidence_source_map"]
    assert "audit_log_evidence" in out047["evidence_source_map"]

    assert "retention_schedule_evidence" in out048["evidence_source_map"]
    assert "data_category_evidence" in out048["evidence_source_map"]
    assert "legal_basis_evidence" in out048["evidence_source_map"]
    assert "deletion_hold_evidence" in out048["evidence_source_map"]
    assert "audit_log_evidence" in out048["evidence_source_map"]

    assert "procurement_plan_evidence" in out098["evidence_source_map"]
    assert "budget_alignment_evidence" in out098["evidence_source_map"]
    assert "approval_chain_evidence" in out098["evidence_source_map"]
    assert "conflict_of_interest_evidence" in out098["evidence_source_map"]
    assert "audit_log_evidence" in out098["evidence_source_map"]


@pytest.mark.parametrize("fn,required", [
    (
        get_third_party_risk_policy_readiness_foundation,
        ["vendor approval", "vendor rejection", "vendor ranking", "risk score", "contract execution"],
    ),
    (
        get_data_retention_policy_control_readiness_foundation,
        ["automatic deletion", "legal compliance claim", "retention override", "external report"],
    ),
    (
        get_procurement_plan_approval_workflow_readiness_foundation,
        [
            "procurement approval",
            "procurement rejection",
            "procurement award",
            "vendor ranking",
            "financial commitment",
            "contract execution",
            "payment action",
        ],
    ),
])
def test_candidate_specific_forbidden_actions_exist(fn, required):
    forbidden = set(fn(VALID_TENANT)["forbidden_outputs"])
    for token in required:
        assert token in forbidden


# Groups 35..39 — static scope and safety scans in changed files

def _read_runtime_sources() -> str:
    chunks: list[str] = []
    for rel in CHANGED_RUNTIME_FILES:
        abs_path = Path(__file__).parents[1] / rel
        chunks.append(abs_path.read_text(encoding="utf-8"))
    return "\n".join(chunks).lower()


def test_no_provider_llm_http_libraries_in_changed_files():
    source = _read_runtime_sources()
    banned = [
        "requests.get(", "requests.post(", "httpx", "aiohttp", "urllib", "socket", "subprocess",
        "ldap3", "smtplib", "boto3", "openai", "anthropic", "ollama", "deepseek", "langchain", "llama",
    ]
    for token in banned:
        assert token not in source


def test_no_credentials_or_secrets_in_changed_files():
    source = _read_runtime_sources()
    banned_patterns = [
        r"\bpassword\s*=",
        r"\bsecret\s*=",
        r"\bapi_key\s*=",
        r"\btoken\s*=",
        r"\bcredential\s*=",
        r"\bclient_secret\s*=",
        r"\bprivate_key\s*=",
        r"\bcertificate\s*=",
        r"\brefresh_token\s*=",
        r"\baccess_token\s*=",
        r"\bmodel_key\s*=",
        r"\bprovider_key\s*=",
    ]
    for pattern in banned_patterns:
        assert re.search(pattern, source) is None


def test_no_db_mutation_in_changed_files():
    source = _read_runtime_sources()
    banned = [".add(", ".delete(", ".commit(", "insert into", "update ", "delete from"]
    for token in banned:
        assert token not in source


def test_no_route_api_or_frontend_scope_in_changed_files():
    source = _read_runtime_sources()
    banned = ["@router.", "react", "useeffect", "nextresponse", "apirouter", "@app.get", "@app.post"]
    for token in banned:
        assert token not in source


# Groups 45..55 — tracker/report metric anchors and namespace separation
def _read_optional_repo_doc(filename: str) -> str:
    candidates = [
        Path(__file__).parents[2] / filename,
        Path(__file__).parents[1] / filename,
        Path(__file__).parents[1].parent / filename,
    ]
    for path in candidates:
        if path.exists():
            return path.read_text(encoding="utf-8")
    return ""


SBS_UB_TEXT = _read_optional_repo_doc("SBS_UB.md")
SPEC_REPORT_TEXT = _read_optional_repo_doc(
    "A-030.2-SPEC-POLICY_PROCUREMENT_READINESS_FOUNDATION_REPORT.md"
)


def test_tracker_contains_policy_procurement_metric_targets():
    if not SBS_UB_TEXT:
        pytest.skip("SBS_UB.md is not mounted in backend-only Docker tests")
    assert "A0302_policy_procurement_foundation_count" in SBS_UB_TEXT
    assert "policy_procurement_foundation_count" in SBS_UB_TEXT
    assert "policy_execution_count" in SBS_UB_TEXT
    assert "procurement_execution_count" in SBS_UB_TEXT
    assert "procurement_award_count" in SBS_UB_TEXT
    assert "procurement_financial_commitment_count" in SBS_UB_TEXT
    assert "policy_procurement_external_submission_count" in SBS_UB_TEXT
    assert "policy_procurement_hidden_score_count" in SBS_UB_TEXT
    assert "policy_procurement_synthetic_score_count" in SBS_UB_TEXT


def test_tracker_or_report_policy_procurement_expected_values_are_three_and_zero():
    if not SBS_UB_TEXT and not SPEC_REPORT_TEXT:
        pytest.skip("tracker/report docs are not mounted in backend-only Docker tests")
    text = SBS_UB_TEXT + "\n" + SPEC_REPORT_TEXT
    assert "A0302_policy_procurement_foundation_count: 3" in text or "A0302_policy_procurement_foundation_count = 3" in text
    assert "policy_procurement_foundation_count: 3" in text or "policy_procurement_foundation_count = 3" in text
    assert "policy_execution_count: 0" in text or "policy_execution_count = 0" in text
    assert "procurement_execution_count: 0" in text or "procurement_execution_count = 0" in text
    assert "procurement_award_count: 0" in text or "procurement_award_count = 0" in text
    assert "procurement_financial_commitment_count: 0" in text or "procurement_financial_commitment_count = 0" in text
    assert "policy_procurement_external_submission_count: 0" in text or "policy_procurement_external_submission_count = 0" in text
    assert "policy_procurement_hidden_score_count: 0" in text or "policy_procurement_hidden_score_count = 0" in text
    assert "policy_procurement_synthetic_score_count: 0" in text or "policy_procurement_synthetic_score_count = 0" in text


def test_namespace_non_movement_markers_present():
    if not SBS_UB_TEXT:
        pytest.skip("SBS_UB.md is not mounted in backend-only Docker tests")
    assert "A0301_brain_governance_foundation_count" in SBS_UB_TEXT
    assert "brain_governance_foundation_count" in SBS_UB_TEXT
    assert "brain_execution_count" in SBS_UB_TEXT
    assert "brain_llm_call_count" in SBS_UB_TEXT
    assert "provider_readiness_foundation_count" in SBS_UB_TEXT
    assert "provider_l3_deterministic_logic_count" in SBS_UB_TEXT
    assert "provider_l4_visibility_count" in SBS_UB_TEXT
    assert "provider_l4_api_route_count" in SBS_UB_TEXT
    assert "provider_l4_consolidated_summary_count" in SBS_UB_TEXT
    assert "expansion_L2_foundation_count" in SBS_UB_TEXT
    assert "expansion_runtime_implemented_count" in SBS_UB_TEXT
    assert "expansion_L3_logic_count" in SBS_UB_TEXT
    assert "remaining_L2_only" in SBS_UB_TEXT
    assert "remaining_L3_not_L4" in SBS_UB_TEXT
    assert "L0=0" in SBS_UB_TEXT
    assert "L1=0" in SBS_UB_TEXT
    assert "L2=0" in SBS_UB_TEXT
    assert "L3=55" in SBS_UB_TEXT
    assert "L4=68" in SBS_UB_TEXT
    assert "L5=25" in SBS_UB_TEXT
    assert "L6=2" in SBS_UB_TEXT
    assert "maturity_arithmetic_check" in SBS_UB_TEXT


def test_policy_procurement_namespace_is_separated_from_others():
    if not SBS_UB_TEXT:
        pytest.skip("SBS_UB.md is not mounted in backend-only Docker tests")
    assert "baseline_impact: 0" in SBS_UB_TEXT or "baseline_impact=0" in SBS_UB_TEXT
    assert "extension_impact: 0" in SBS_UB_TEXT or "extension_impact=0" in SBS_UB_TEXT
    assert "ordinary_expansion_impact: 0" in SBS_UB_TEXT or "ordinary_expansion_impact=0" in SBS_UB_TEXT
    assert "provider_readiness_impact: 0" in SBS_UB_TEXT or "provider_readiness_impact=0" in SBS_UB_TEXT
    assert "brain_governance_impact: 0" in SBS_UB_TEXT or "brain_governance_impact=0" in SBS_UB_TEXT
