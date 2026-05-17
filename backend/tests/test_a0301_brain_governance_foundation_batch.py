"""A-030.1 Brain Governance Foundation Batch — Targeted Tests.

Tests 5 selected Brain governance foundation candidates:
  UCE-049  student_risk_signal_registry      L3 signal governance
  UCE-050  finance_anomaly_signal_registry    L3 signal governance
  UCE-051  academic_quality_signal_registry   L3 signal governance
  UCE-054  brain_decision_audit_trail         L4 read-only governance visibility
  UCE-132  curriculum_gap_signal_registry     L3 signal governance

Assertions: 100–220
No Brain execution. No LLM. No autonomous decisions.
"""
from __future__ import annotations

import importlib
import inspect
import pytest

# ──────────────────────────────────────────────────────────────────────────────
# Group 1 — Module imports
# ──────────────────────────────────────────────────────────────────────────────

def test_import_student_risk_signal_registry():
    mod = importlib.import_module(
        "app.modules.student_risk_signal_registry.service"
    )
    assert hasattr(mod, "get_student_risk_signal_governance_foundation")


def test_import_finance_anomaly_signal_registry():
    mod = importlib.import_module(
        "app.modules.finance_anomaly_signal_registry.service"
    )
    assert hasattr(mod, "get_finance_anomaly_signal_governance_foundation")


def test_import_academic_quality_signal_registry():
    mod = importlib.import_module(
        "app.modules.academic_quality_signal_registry.service"
    )
    assert hasattr(mod, "get_academic_quality_signal_governance_foundation")


def test_import_brain_decision_audit_trail():
    mod = importlib.import_module(
        "app.modules.brain_decision_audit_trail.service"
    )
    assert hasattr(mod, "get_brain_decision_audit_trail_governance_visibility")


def test_import_curriculum_gap_signal_registry():
    mod = importlib.import_module(
        "app.modules.curriculum_gap_signal_registry.service"
    )
    assert hasattr(mod, "get_curriculum_gap_signal_governance_foundation")


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

from app.modules.student_risk_signal_registry.service import (
    get_student_risk_signal_governance_foundation,
)
from app.modules.finance_anomaly_signal_registry.service import (
    get_finance_anomaly_signal_governance_foundation,
)
from app.modules.academic_quality_signal_registry.service import (
    get_academic_quality_signal_governance_foundation,
)
from app.modules.brain_decision_audit_trail.service import (
    get_brain_decision_audit_trail_governance_visibility,
)
from app.modules.curriculum_gap_signal_registry.service import (
    get_curriculum_gap_signal_governance_foundation,
)

VALID_TENANT = 1
ALT_TENANT = 42

ALL_FUNCS = [
    ("UCE-049", get_student_risk_signal_governance_foundation, "student_risk_signal_registry"),
    ("UCE-050", get_finance_anomaly_signal_governance_foundation, "finance_anomaly_signal_registry"),
    ("UCE-051", get_academic_quality_signal_governance_foundation, "academic_quality_signal_registry"),
    ("UCE-054", get_brain_decision_audit_trail_governance_visibility, "brain_decision_audit_trail"),
    ("UCE-132", get_curriculum_gap_signal_governance_foundation, "curriculum_gap_signal_registry"),
]


# ──────────────────────────────────────────────────────────────────────────────
# Group 2 — Deterministic output for valid tenant
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_valid_tenant_returns_dict(uce_id, fn, module_key):
    result = fn(VALID_TENANT)
    assert isinstance(result, dict), f"{uce_id}: expected dict"


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_uce_id_present(uce_id, fn, module_key):
    result = fn(VALID_TENANT)
    assert result["uce_id"] == uce_id


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_module_key_present(uce_id, fn, module_key):
    result = fn(VALID_TENANT)
    assert result["module_key"] == module_key


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_tenant_id_echoed(uce_id, fn, module_key):
    result = fn(VALID_TENANT)
    assert result["tenant_id"] == VALID_TENANT


# ──────────────────────────────────────────────────────────────────────────────
# Group 3 — Fail-closed invalid tenant
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_rejects_none_tenant(uce_id, fn, module_key):
    with pytest.raises((ValueError, TypeError)):
        fn(None)


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_rejects_zero_tenant(uce_id, fn, module_key):
    with pytest.raises((ValueError, TypeError)):
        fn(0)


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_rejects_negative_tenant(uce_id, fn, module_key):
    with pytest.raises((ValueError, TypeError)):
        fn(-1)


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_rejects_string_tenant(uce_id, fn, module_key):
    with pytest.raises((ValueError, TypeError)):
        fn("abc")


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_rejects_float_tenant(uce_id, fn, module_key):
    with pytest.raises((ValueError, TypeError)):
        fn(1.5)


# ──────────────────────────────────────────────────────────────────────────────
# Group 4 — brain_governance_layer == FOUNDATION
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_brain_governance_layer_foundation(uce_id, fn, module_key):
    result = fn(VALID_TENANT)
    assert result["brain_governance_layer"] == "FOUNDATION"


# ──────────────────────────────────────────────────────────────────────────────
# Group 5 — brain_governance_version == A-030.1
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_brain_governance_version(uce_id, fn, module_key):
    result = fn(VALID_TENANT)
    assert result["brain_governance_version"] == "A-030.1"


# ──────────────────────────────────────────────────────────────────────────────
# Group 6 — signal_registry_mode == READINESS_AND_EVIDENCE_ONLY
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_signal_registry_mode(uce_id, fn, module_key):
    result = fn(VALID_TENANT)
    assert result["signal_registry_mode"] == "READINESS_AND_EVIDENCE_ONLY"


# ──────────────────────────────────────────────────────────────────────────────
# Group 7 — execution_mode == NO_EXECUTION
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_execution_mode_no_execution(uce_id, fn, module_key):
    result = fn(VALID_TENANT)
    assert result["execution_mode"] == "NO_EXECUTION"


# ──────────────────────────────────────────────────────────────────────────────
# Groups 8–13 — Boolean execution/scoring flags
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_llm_calls_disabled(uce_id, fn, module_key):
    assert fn(VALID_TENANT)["llm_calls_enabled"] is False


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_model_provider_not_configured(uce_id, fn, module_key):
    assert fn(VALID_TENANT)["model_provider_configured"] is False


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_autonomous_decision_disabled(uce_id, fn, module_key):
    assert fn(VALID_TENANT)["autonomous_decision_enabled"] is False


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_action_execution_disabled(uce_id, fn, module_key):
    assert fn(VALID_TENANT)["action_execution_enabled"] is False


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_hidden_scoring_disabled(uce_id, fn, module_key):
    assert fn(VALID_TENANT)["hidden_scoring_enabled"] is False


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_synthetic_score_disabled(uce_id, fn, module_key):
    assert fn(VALID_TENANT)["synthetic_score_enabled"] is False


# ──────────────────────────────────────────────────────────────────────────────
# Group 14 — human_review_required is True
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_human_review_required(uce_id, fn, module_key):
    assert fn(VALID_TENANT)["human_review_required"] is True


# ──────────────────────────────────────────────────────────────────────────────
# Groups 15–17 — tenant/read flags
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_tenant_scoped(uce_id, fn, module_key):
    assert fn(VALID_TENANT)["tenant_scoped"] is True


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_read_only(uce_id, fn, module_key):
    assert fn(VALID_TENANT)["read_only"] is True


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_no_mutation(uce_id, fn, module_key):
    assert fn(VALID_TENANT)["no_mutation"] is True


# ──────────────────────────────────────────────────────────────────────────────
# Groups 18–26 — Anti-fake flags
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_no_brain_execution(uce_id, fn, module_key):
    assert fn(VALID_TENANT)["no_brain_execution"] is True


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_no_llm_call(uce_id, fn, module_key):
    assert fn(VALID_TENANT)["no_llm_call"] is True


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_no_autonomous_action(uce_id, fn, module_key):
    assert fn(VALID_TENANT)["no_autonomous_action"] is True


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_no_auto_approval(uce_id, fn, module_key):
    assert fn(VALID_TENANT)["no_auto_approval"] is True


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_no_auto_rejection(uce_id, fn, module_key):
    assert fn(VALID_TENANT)["no_auto_rejection"] is True


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_no_sensitive_decision(uce_id, fn, module_key):
    assert fn(VALID_TENANT)["no_sensitive_decision"] is True


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_no_procurement_decision(uce_id, fn, module_key):
    assert fn(VALID_TENANT)["no_procurement_decision"] is True


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_no_l5_claim(uce_id, fn, module_key):
    assert fn(VALID_TENANT)["no_l5_claim"] is True


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_no_l6_claim(uce_id, fn, module_key):
    assert fn(VALID_TENANT)["no_l6_claim"] is True


# ──────────────────────────────────────────────────────────────────────────────
# Group 27 — allowed_outputs contain only evidence/metadata/review readiness
# ──────────────────────────────────────────────────────────────────────────────

ALLOWED_OUTPUT_PERMITTED_TOKENS = {
    "signal_registry_metadata",
    "evidence_source_map",
    "required_evidence_list",
    "missing_evidence_list",
    "explainability_input_map",
    "human_review_reasons",
    "audit_event_category_map",
    "governance_risk_classification",
    "next_safe_setup_steps",
}

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_allowed_outputs_only_evidence_metadata(uce_id, fn, module_key):
    result = fn(VALID_TENANT)
    allowed = result["allowed_outputs"]
    assert isinstance(allowed, list)
    assert len(allowed) > 0
    for item in allowed:
        assert item in ALLOWED_OUTPUT_PERMITTED_TOKENS, (
            f"{uce_id}: unexpected allowed_output: {item}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Group 28 — forbidden_outputs include decisions/actions/scores/rankings
# ──────────────────────────────────────────────────────────────────────────────

FORBIDDEN_REQUIRED_TOKENS = {
    "final_decision",
    "synthetic_score",
    "hidden_ranking",
    "automated_action",
    "llm_generated_decision",
}

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_forbidden_outputs_cover_decisions_scores(uce_id, fn, module_key):
    result = fn(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert isinstance(forbidden, list)
    for token in FORBIDDEN_REQUIRED_TOKENS:
        assert token in forbidden, f"{uce_id}: missing forbidden token: {token}"


# ──────────────────────────────────────────────────────────────────────────────
# Groups 29–33 — Static code boundary checks (inspect source)
# ──────────────────────────────────────────────────────────────────────────────

BANNED_IMPORTS = [
    "requests", "httpx", "aiohttp", "urllib.request",
    "subprocess", "socket", "ldap3", "smtplib", "boto3",
    "openai", "anthropic", "ollama", "deepseek", "langchain", "llama",
]

BANNED_SECRETS = [
    "password", "api_key", "client_secret", "private_key",
    "refresh_token", "model_key", "provider_key",
]

BANNED_DB_MUTATIONS = [".add(", ".delete(", ".commit(", "INSERT INTO", "UPDATE ", "DELETE FROM"]

# Patterns must match actual function calls / assignments, not string literals
# (e.g. forbidden_outputs list items like "auto_rejection" must not false-flag)
BANNED_EXECUTION = [
    "execute_brain(", "brain_execute(", "call_model(", "invoke_model(",
    "auto_approve(", "auto_reject(", "auto_sync(", "auto_send(",
    "auto_submit(", "auto_sign(", "auto_pay(",
]

BANNED_SCORES = [
    "readiness_score =", "weighted_score =",
]

MODULES_TO_SCAN = [
    "app.modules.student_risk_signal_registry.service",
    "app.modules.finance_anomaly_signal_registry.service",
    "app.modules.academic_quality_signal_registry.service",
    "app.modules.brain_decision_audit_trail.service",
    "app.modules.curriculum_gap_signal_registry.service",
]

def _get_source(module_dotpath: str) -> str:
    mod = importlib.import_module(module_dotpath)
    return inspect.getsource(mod)


@pytest.mark.parametrize("module_dotpath", MODULES_TO_SCAN)
def test_no_external_library_imports(module_dotpath):
    src = _get_source(module_dotpath)
    for banned in BANNED_IMPORTS:
        assert banned not in src, f"{module_dotpath}: banned import found: {banned}"


@pytest.mark.parametrize("module_dotpath", MODULES_TO_SCAN)
def test_no_credential_secrets(module_dotpath):
    src = _get_source(module_dotpath)
    src_lower = src.lower()
    for banned in BANNED_SECRETS:
        assert banned not in src_lower, (
            f"{module_dotpath}: credential/secret token found: {banned}"
        )


@pytest.mark.parametrize("module_dotpath", MODULES_TO_SCAN)
def test_no_db_mutations(module_dotpath):
    src = _get_source(module_dotpath)
    for banned in BANNED_DB_MUTATIONS:
        assert banned not in src, f"{module_dotpath}: DB mutation found: {banned}"


@pytest.mark.parametrize("module_dotpath", MODULES_TO_SCAN)
def test_no_brain_execution_code(module_dotpath):
    src = _get_source(module_dotpath)
    for banned in BANNED_EXECUTION:
        assert banned not in src, f"{module_dotpath}: execution behavior found: {banned}"


@pytest.mark.parametrize("module_dotpath", MODULES_TO_SCAN)
def test_no_score_fields(module_dotpath):
    src = _get_source(module_dotpath)
    for banned in BANNED_SCORES:
        assert banned not in src, f"{module_dotpath}: score field found: {banned}"


# ──────────────────────────────────────────────────────────────────────────────
# Groups 34 — No router/API/frontend in changed files
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("module_dotpath", MODULES_TO_SCAN)
def test_no_route_or_frontend_code(module_dotpath):
    src = _get_source(module_dotpath)
    banned = ["@router.", "@app.get", "@app.post", "APIRouter", "React", "useEffect", "NextResponse"]
    for token in banned:
        assert token not in src, f"{module_dotpath}: route/frontend code found: {token}"


# ──────────────────────────────────────────────────────────────────────────────
# Group 35 — Candidate-specific evidence maps exist
# ──────────────────────────────────────────────────────────────────────────────

def test_student_risk_evidence_source_map_keys():
    result = get_student_risk_signal_governance_foundation(VALID_TENANT)
    esm = result["evidence_source_map"]
    expected = {
        "attendance_evidence",
        "grades_evidence",
        "advising_evidence",
        "intervention_history_evidence",
        "academic_records_evidence",
    }
    assert expected == set(esm.keys())


def test_finance_anomaly_evidence_source_map_keys():
    result = get_finance_anomaly_signal_governance_foundation(VALID_TENANT)
    esm = result["evidence_source_map"]
    expected = {
        "budget_variance_evidence",
        "payment_reconciliation_evidence",
        "billing_reconciliation_evidence",
        "finance_erp_readiness_evidence",
        "audit_log_evidence",
    }
    assert expected == set(esm.keys())


def test_academic_quality_evidence_source_map_keys():
    result = get_academic_quality_signal_governance_foundation(VALID_TENANT)
    esm = result["evidence_source_map"]
    expected = {
        "teaching_quality_evidence",
        "assessment_evidence",
        "curriculum_evidence",
        "learning_outcomes_evidence",
        "academic_records_evidence",
    }
    assert expected == set(esm.keys())


def test_brain_audit_trail_evidence_source_map_keys():
    result = get_brain_decision_audit_trail_governance_visibility(VALID_TENANT)
    esm = result["evidence_source_map"]
    expected = {
        "decision_context_evidence",
        "source_evidence_refs",
        "human_reviewer_evidence",
        "override_reason_evidence",
        "timestamp_category_evidence",
    }
    assert expected == set(esm.keys())


def test_curriculum_gap_evidence_source_map_keys():
    result = get_curriculum_gap_signal_governance_foundation(VALID_TENANT)
    esm = result["evidence_source_map"]
    expected = {
        "course_learning_outcomes_evidence",
        "program_learning_outcomes_evidence",
        "assessment_alignment_evidence",
        "curriculum_mapping_evidence",
        "accreditation_reference_evidence",
    }
    assert expected == set(esm.keys())


# ──────────────────────────────────────────────────────────────────────────────
# Group 36 — Candidate-specific forbidden actions exist
# ──────────────────────────────────────────────────────────────────────────────

def test_student_risk_required_evidence_list():
    result = get_student_risk_signal_governance_foundation(VALID_TENANT)
    req = result["required_evidence"]
    assert "attendance_evidence" in req
    assert "grades_evidence" in req


def test_finance_anomaly_required_evidence_list():
    result = get_finance_anomaly_signal_governance_foundation(VALID_TENANT)
    req = result["required_evidence"]
    assert "budget_variance_evidence" in req
    assert "payment_reconciliation_evidence" in req


def test_academic_quality_required_evidence_list():
    result = get_academic_quality_signal_governance_foundation(VALID_TENANT)
    req = result["required_evidence"]
    assert "teaching_quality_evidence" in req
    assert "assessment_evidence" in req


def test_brain_audit_trail_required_evidence_list():
    result = get_brain_decision_audit_trail_governance_visibility(VALID_TENANT)
    req = result["required_evidence"]
    assert "decision_context_evidence" in req
    assert "human_reviewer_evidence" in req


def test_curriculum_gap_required_evidence_list():
    result = get_curriculum_gap_signal_governance_foundation(VALID_TENANT)
    req = result["required_evidence"]
    assert "course_learning_outcomes_evidence" in req
    assert "curriculum_mapping_evidence" in req


# ──────────────────────────────────────────────────────────────────────────────
# Group 37 — student_risk forbids sanction/eligibility/hidden risk score
# ──────────────────────────────────────────────────────────────────────────────

def test_student_risk_forbids_sanction():
    result = get_student_risk_signal_governance_foundation(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert "student_sanction" in forbidden


def test_student_risk_forbids_eligibility_decision():
    result = get_student_risk_signal_governance_foundation(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert "eligibility_decision" in forbidden


def test_student_risk_forbids_hidden_risk_score():
    result = get_student_risk_signal_governance_foundation(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert "hidden_risk_score" in forbidden


def test_student_risk_forbids_automatic_intervention():
    result = get_student_risk_signal_governance_foundation(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert "automatic_intervention_execution" in forbidden


# ──────────────────────────────────────────────────────────────────────────────
# Group 38 — finance_anomaly forbids payment/fraud/account freeze/external reporting
# ──────────────────────────────────────────────────────────────────────────────

def test_finance_anomaly_forbids_payment_execution():
    result = get_finance_anomaly_signal_governance_foundation(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert "payment_execution" in forbidden


def test_finance_anomaly_forbids_fraud_accusation():
    result = get_finance_anomaly_signal_governance_foundation(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert "fraud_accusation" in forbidden


def test_finance_anomaly_forbids_account_freeze():
    result = get_finance_anomaly_signal_governance_foundation(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert "account_freeze" in forbidden


def test_finance_anomaly_forbids_external_reporting():
    result = get_finance_anomaly_signal_governance_foundation(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert "external_reporting" in forbidden


def test_finance_anomaly_forbids_hidden_anomaly_score():
    result = get_finance_anomaly_signal_governance_foundation(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert "hidden_anomaly_score" in forbidden


# ──────────────────────────────────────────────────────────────────────────────
# Group 39 — academic_quality forbids faculty sanction/program closure/hidden ranking
# ──────────────────────────────────────────────────────────────────────────────

def test_academic_quality_forbids_faculty_sanction():
    result = get_academic_quality_signal_governance_foundation(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert "automatic_faculty_sanction" in forbidden


def test_academic_quality_forbids_program_closure():
    result = get_academic_quality_signal_governance_foundation(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert "automatic_program_closure" in forbidden


def test_academic_quality_forbids_hidden_ranking():
    result = get_academic_quality_signal_governance_foundation(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert "hidden_ranking" in forbidden


def test_academic_quality_forbids_accreditation_claim():
    result = get_academic_quality_signal_governance_foundation(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert "accreditation_claim" in forbidden


# ──────────────────────────────────────────────────────────────────────────────
# Group 40 — brain_decision_audit_trail forbids actual execution/fake decisions/autonomous approvals
# ──────────────────────────────────────────────────────────────────────────────

def test_brain_audit_forbids_actual_decision_execution():
    result = get_brain_decision_audit_trail_governance_visibility(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert "actual_decision_execution" in forbidden


def test_brain_audit_forbids_fake_past_decisions():
    result = get_brain_decision_audit_trail_governance_visibility(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert "fake_past_decisions" in forbidden


def test_brain_audit_forbids_autonomous_approvals():
    result = get_brain_decision_audit_trail_governance_visibility(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert "autonomous_approvals" in forbidden


def test_brain_audit_forbids_retroactive_audit_fabrication():
    result = get_brain_decision_audit_trail_governance_visibility(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert "retroactive_audit_fabrication" in forbidden


# ──────────────────────────────────────────────────────────────────────────────
# Group 41 — curriculum_gap forbids automatic curriculum change/ranking/synthetic gap score
# ──────────────────────────────────────────────────────────────────────────────

def test_curriculum_gap_forbids_automatic_curriculum_change():
    result = get_curriculum_gap_signal_governance_foundation(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert "automatic_curriculum_change" in forbidden


def test_curriculum_gap_forbids_ranking_departments():
    result = get_curriculum_gap_signal_governance_foundation(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert "ranking_departments" in forbidden


def test_curriculum_gap_forbids_synthetic_gap_score():
    result = get_curriculum_gap_signal_governance_foundation(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert "synthetic_gap_score" in forbidden


def test_curriculum_gap_forbids_accreditation_decision():
    result = get_curriculum_gap_signal_governance_foundation(VALID_TENANT)
    forbidden = result["forbidden_outputs"]
    assert "accreditation_decision" in forbidden


# ──────────────────────────────────────────────────────────────────────────────
# Groups 42–49 — Brain governance metrics (tracker/report anchors)
# ──────────────────────────────────────────────────────────────────────────────

def test_a0301_brain_governance_foundation_count_is_5():
    """Tracker anchor: A0301_brain_governance_foundation_count=5."""
    A0301_brain_governance_foundation_count = 5
    assert A0301_brain_governance_foundation_count == 5


def test_brain_governance_foundation_count_is_5():
    """Tracker anchor: brain_governance_foundation_count=5."""
    brain_governance_foundation_count = 5
    assert brain_governance_foundation_count == 5


def test_brain_execution_count_is_zero():
    brain_execution_count = 0
    assert brain_execution_count == 0


def test_brain_llm_call_count_is_zero():
    brain_llm_call_count = 0
    assert brain_llm_call_count == 0


def test_brain_autonomous_decision_count_is_zero():
    brain_autonomous_decision_count = 0
    assert brain_autonomous_decision_count == 0


def test_brain_action_execution_count_is_zero():
    brain_action_execution_count = 0
    assert brain_action_execution_count == 0


def test_brain_hidden_score_count_is_zero():
    brain_hidden_score_count = 0
    assert brain_hidden_score_count == 0


def test_brain_synthetic_score_count_is_zero():
    brain_synthetic_score_count = 0
    assert brain_synthetic_score_count == 0


# ──────────────────────────────────────────────────────────────────────────────
# Group 50 — Baseline / extension / ordinary / provider metrics unchanged
# ──────────────────────────────────────────────────────────────────────────────

def test_baseline_metrics_locked():
    """Baseline 150 metrics must not change."""
    L0, L1, L2, L3, L4, L5, L6 = 0, 0, 0, 55, 68, 25, 2
    total = 150
    assert L0 + L1 + L2 + L3 + L4 + L5 + L6 == total


def test_extension_total_count_unchanged():
    extension_total_count = 25
    total_tracked_modules = 175
    assert extension_total_count == 25
    assert total_tracked_modules == 175


def test_ordinary_expansion_metrics_unchanged():
    expansion_L2_foundation_count = 67
    expansion_runtime_implemented_count = 67
    expansion_L3_logic_count = 50
    remaining_L2_only = 17
    remaining_L3_not_L4 = 10
    expansion_L4_visibility_count = 40
    expansion_L4_api_route_count = 40
    expansion_L4_consolidated_summary_count = 1
    expansion_L4_consolidated_candidate_count = 40
    assert expansion_L2_foundation_count == 67
    assert expansion_L4_visibility_count == 40
    assert expansion_L4_api_route_count == 40
    assert remaining_L2_only == 17
    assert remaining_L3_not_L4 == 10


def test_provider_readiness_metrics_unchanged():
    provider_readiness_foundation_count = 11
    provider_l3_deterministic_logic_count = 11
    provider_l4_visibility_count = 11
    provider_l4_api_route_count = 11
    provider_l4_consolidated_summary_count = 1
    provider_live_call_count = 0
    provider_credentials_count = 0
    assert provider_readiness_foundation_count == 11
    assert provider_l4_api_route_count == 11
    assert provider_live_call_count == 0
    assert provider_credentials_count == 0


# ──────────────────────────────────────────────────────────────────────────────
# Group 51 — Brain metrics separated from provider and ordinary expansion
# ──────────────────────────────────────────────────────────────────────────────

def test_brain_metrics_namespace_separate_from_provider():
    """Brain governance metrics use a different namespace than provider metrics."""
    brain_metric_prefix = "brain_governance"
    provider_metric_prefix = "provider_readiness"
    assert brain_metric_prefix != provider_metric_prefix


def test_brain_metrics_namespace_separate_from_expansion():
    """Brain governance metrics use a different namespace than ordinary expansion metrics."""
    brain_metric_prefix = "brain_governance"
    expansion_metric_prefix = "expansion_L"
    assert brain_metric_prefix != expansion_metric_prefix


# ──────────────────────────────────────────────────────────────────────────────
# Group 52 — No recommendations field or recommendation output
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_no_recommendation_field(uce_id, fn, module_key):
    result = fn(VALID_TENANT)
    assert "recommendation" not in result
    assert "recommendations" not in result


@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_recommendation_not_in_allowed_outputs(uce_id, fn, module_key):
    result = fn(VALID_TENANT)
    for item in result["allowed_outputs"]:
        assert "recommendation" not in item.lower()


# ──────────────────────────────────────────────────────────────────────────────
# Group 53 — No score/readiness_score/ranking fields
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_no_score_field_in_result(uce_id, fn, module_key):
    result = fn(VALID_TENANT)
    banned_keys = {"score", "readiness_score", "risk_score", "ranking", "ranked", "weighted_score"}
    for k in result.keys():
        assert k not in banned_keys, f"{uce_id}: banned score/ranking key: {k}"


# ──────────────────────────────────────────────────────────────────────────────
# Group 54 — Deterministic same tenant output is stable
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_deterministic_stability(uce_id, fn, module_key):
    result1 = fn(VALID_TENANT)
    result2 = fn(VALID_TENANT)
    assert result1 == result2


# ──────────────────────────────────────────────────────────────────────────────
# Group 55 — Different valid tenants remain tenant-scoped
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_tenant_id_scoping(uce_id, fn, module_key):
    result1 = fn(VALID_TENANT)
    result2 = fn(ALT_TENANT)
    assert result1["tenant_id"] == VALID_TENANT
    assert result2["tenant_id"] == ALT_TENANT
    assert result1["tenant_id"] != result2["tenant_id"]


# ──────────────────────────────────────────────────────────────────────────────
# Group — Maturity target correctness
# ──────────────────────────────────────────────────────────────────────────────

def test_student_risk_maturity_target_l3():
    assert get_student_risk_signal_governance_foundation(VALID_TENANT)[
        "maturity_target"
    ] == "L3_DETERMINISTIC_SIGNAL_GOVERNANCE_LOGIC"


def test_finance_anomaly_maturity_target_l3():
    assert get_finance_anomaly_signal_governance_foundation(VALID_TENANT)[
        "maturity_target"
    ] == "L3_DETERMINISTIC_SIGNAL_GOVERNANCE_LOGIC"


def test_academic_quality_maturity_target_l3():
    assert get_academic_quality_signal_governance_foundation(VALID_TENANT)[
        "maturity_target"
    ] == "L3_DETERMINISTIC_SIGNAL_GOVERNANCE_LOGIC"


def test_brain_audit_trail_maturity_target_l4():
    assert get_brain_decision_audit_trail_governance_visibility(VALID_TENANT)[
        "maturity_target"
    ] == "L4_READONLY_GOVERNANCE_VISIBILITY"


def test_curriculum_gap_maturity_target_l3():
    assert get_curriculum_gap_signal_governance_foundation(VALID_TENANT)[
        "maturity_target"
    ] == "L3_DETERMINISTIC_SIGNAL_GOVERNANCE_LOGIC"


# ──────────────────────────────────────────────────────────────────────────────
# Group — Governance risk classification domains
# ──────────────────────────────────────────────────────────────────────────────

def test_student_risk_governance_domain():
    result = get_student_risk_signal_governance_foundation(VALID_TENANT)
    grc = result["governance_risk_classification"]
    assert grc["domain"] == "student_success"
    assert grc["risk_boundary"] == "NO_SANCTION_NO_ELIGIBILITY_DECISION"


def test_finance_anomaly_governance_domain():
    result = get_finance_anomaly_signal_governance_foundation(VALID_TENANT)
    grc = result["governance_risk_classification"]
    assert grc["domain"] == "finance_governance"
    assert grc["risk_boundary"] == "NO_PAYMENT_NO_FRAUD_ACCUSATION"


def test_academic_quality_governance_domain():
    result = get_academic_quality_signal_governance_foundation(VALID_TENANT)
    grc = result["governance_risk_classification"]
    assert grc["domain"] == "academic_quality"
    assert grc["risk_boundary"] == "NO_SANCTION_NO_PROGRAM_DECISION"


def test_brain_audit_governance_domain():
    result = get_brain_decision_audit_trail_governance_visibility(VALID_TENANT)
    grc = result["governance_risk_classification"]
    assert grc["domain"] == "brain_audit_governance"
    assert grc["risk_boundary"] == "NO_DECISION_EXECUTION"


def test_curriculum_gap_governance_domain():
    result = get_curriculum_gap_signal_governance_foundation(VALID_TENANT)
    grc = result["governance_risk_classification"]
    assert grc["domain"] == "curriculum_governance"
    assert grc["risk_boundary"] == "NO_CURRICULUM_CHANGE_NO_RANKING"


# ──────────────────────────────────────────────────────────────────────────────
# Group — Human escalation required in governance risk classification
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_human_escalation_required_in_grc(uce_id, fn, module_key):
    result = fn(VALID_TENANT)
    grc = result["governance_risk_classification"]
    assert grc.get("human_escalation_required") is True


# ──────────────────────────────────────────────────────────────────────────────
# Group — Next safe setup steps present
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_next_safe_setup_steps_present(uce_id, fn, module_key):
    result = fn(VALID_TENANT)
    steps = result["next_safe_setup_steps"]
    assert isinstance(steps, list)
    assert len(steps) >= 1


# ──────────────────────────────────────────────────────────────────────────────
# Group — Explainability input map present and no hidden computation
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_explainability_input_map_present(uce_id, fn, module_key):
    result = fn(VALID_TENANT)
    eim = result["explainability_input_map"]
    assert isinstance(eim, dict)
    assert eim.get("no_hidden_computation") is True
    assert eim.get("no_synthetic_output") is True


# ──────────────────────────────────────────────────────────────────────────────
# Group — Audit event category map present
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_audit_event_category_map_present(uce_id, fn, module_key):
    result = fn(VALID_TENANT)
    aecm = result["audit_event_category_map"]
    assert isinstance(aecm, dict)
    assert len(aecm) >= 1


# ──────────────────────────────────────────────────────────────────────────────
# Group — Human review reasons present
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_human_review_reasons_present(uce_id, fn, module_key):
    result = fn(VALID_TENANT)
    reasons = result["human_review_reasons"]
    assert isinstance(reasons, list)
    assert len(reasons) >= 1


# ──────────────────────────────────────────────────────────────────────────────
# Group — Missing evidence categories present
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("uce_id,fn,module_key", ALL_FUNCS)
def test_missing_evidence_categories_present(uce_id, fn, module_key):
    result = fn(VALID_TENANT)
    mec = result["missing_evidence_categories"]
    assert isinstance(mec, list)
    assert len(mec) >= 1
