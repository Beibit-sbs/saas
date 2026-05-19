"""
A-030.6-RUNTIME Gate: Academic Appeals Workflow Sensitive-Domain Readiness Foundation.

UCE-093 / academic_appeals_workflow
Contract: L3_DETERMINISTIC_READINESS_GOVERNANCE
Boundary: NO_EXECUTION + NO_APPEAL_DECISION_NO_ACADEMIC_RULING
Related: UCE-007 (disciplinary_case_management), UCE-078 (academic_integrity_case_management)
"""
import pytest

from app.modules.academic_appeals_workflow.service import (
    get_academic_appeals_workflow_sensitive_readiness_foundation,
    validate_tenant_id,
)


@pytest.fixture(autouse=True)
def reset_shared_state(monkeypatch):
    """Module-local harness override — prevents global conftest reset from triggering
    expensive DB/LDAP connections for pure Python service tests (A-030.6 pattern)."""
    monkeypatch.setenv("RBAC_ALLOW_DEV_FALLBACK", "true")
    yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _output(tenant_id=1):
    return get_academic_appeals_workflow_sensitive_readiness_foundation(tenant_id=tenant_id)


# ===========================================================================
# 1. Imports / function existence
# ===========================================================================

class TestImports:
    """Verify importable symbols."""

    def test_main_function_importable(self):
        assert callable(get_academic_appeals_workflow_sensitive_readiness_foundation)

    def test_validate_tenant_id_importable(self):
        assert callable(validate_tenant_id)

    def test_module_constants_importable(self):
        from app.modules.academic_appeals_workflow import (
            MODULE_NAME,
            UCE_ID,
            TARGET_LEVEL,
            CONTRACT_VERSION,
            FOUNDATION_STATUS,
        )
        assert MODULE_NAME == "academic_appeals_workflow"
        assert UCE_ID == "UCE-093"
        assert TARGET_LEVEL == "L3"
        assert CONTRACT_VERSION == "A-030.6"
        assert FOUNDATION_STATUS == "SENSITIVE_READINESS_FOUNDATION"


# ===========================================================================
# 2-3. Tenant validation — fail-closed
# ===========================================================================

class TestTenantValidationFailClosed:
    """validate_tenant_id — all invalid inputs raise ValueError."""

    def test_none_rejected(self):
        with pytest.raises(ValueError):
            validate_tenant_id(None)

    def test_zero_rejected(self):
        with pytest.raises(ValueError):
            validate_tenant_id(0)

    def test_negative_rejected(self):
        with pytest.raises(ValueError):
            validate_tenant_id(-1)

    def test_large_negative_rejected(self):
        with pytest.raises(ValueError):
            validate_tenant_id(-9999)

    def test_true_bool_rejected(self):
        with pytest.raises(ValueError):
            validate_tenant_id(True)

    def test_false_bool_rejected(self):
        with pytest.raises(ValueError):
            validate_tenant_id(False)

    def test_string_rejected(self):
        with pytest.raises(ValueError):
            validate_tenant_id("1")

    def test_float_rejected(self):
        with pytest.raises(ValueError):
            validate_tenant_id(1.5)

    def test_list_rejected(self):
        with pytest.raises(ValueError):
            validate_tenant_id([1])

    def test_positive_int_accepted(self):
        assert validate_tenant_id(1) == 1

    def test_large_positive_accepted(self):
        assert validate_tenant_id(9999) == 9999


class TestMainFunctionTenantFailClosed:
    """Main function also enforces fail-closed tenant validation."""

    def test_none_rejected(self):
        with pytest.raises(ValueError):
            get_academic_appeals_workflow_sensitive_readiness_foundation(None)

    def test_zero_rejected(self):
        with pytest.raises(ValueError):
            get_academic_appeals_workflow_sensitive_readiness_foundation(0)

    def test_negative_rejected(self):
        with pytest.raises(ValueError):
            get_academic_appeals_workflow_sensitive_readiness_foundation(-1)

    def test_bool_true_rejected(self):
        with pytest.raises(ValueError):
            get_academic_appeals_workflow_sensitive_readiness_foundation(True)

    def test_bool_false_rejected(self):
        with pytest.raises(ValueError):
            get_academic_appeals_workflow_sensitive_readiness_foundation(False)

    def test_string_rejected(self):
        with pytest.raises(ValueError):
            get_academic_appeals_workflow_sensitive_readiness_foundation("1")

    def test_float_rejected(self):
        with pytest.raises(ValueError):
            get_academic_appeals_workflow_sensitive_readiness_foundation(1.5)


# ===========================================================================
# 4. Deterministic output
# ===========================================================================

class TestDeterministicOutput:
    """Same input → identical output on every call."""

    def test_returns_dict(self):
        assert isinstance(_output(1), dict)

    def test_tenant_id_echoed(self):
        assert _output(42)["tenant_id"] == 42

    def test_deterministic_same_tenant(self):
        assert _output(1) == _output(1)

    def test_no_side_effects(self):
        _output(1)
        _output(2)
        assert _output(1)["tenant_id"] == 1


# ===========================================================================
# 5. Multi-tenant separation
# ===========================================================================

class TestMultiTenantSeparation:
    """Different tenants differ only by tenant_id."""

    def test_different_tenant_ids(self):
        assert _output(1)["tenant_id"] != _output(2)["tenant_id"]

    def test_module_same_across_tenants(self):
        assert _output(1)["module"] == _output(99)["module"]

    def test_uce_same_across_tenants(self):
        assert _output(1)["uce_id"] == _output(99)["uce_id"]


# ===========================================================================
# 6. Top-level identity fields
# ===========================================================================

class TestTopLevelIdentityFields:
    """Contract identity fields at top level."""

    def test_module_name(self):
        assert _output()["module"] == "academic_appeals_workflow"

    def test_uce_id(self):
        assert _output()["uce_id"] == "UCE-093"

    def test_maturity(self):
        assert _output()["maturity"] == "L3_DETERMINISTIC_READINESS_GOVERNANCE"

    def test_readiness_layer(self):
        assert _output()["readiness_layer"] == "SENSITIVE_DOMAIN_FOUNDATION"

    def test_execution_mode(self):
        assert _output()["execution_mode"] == "NO_EXECUTION"

    def test_boundary(self):
        assert _output()["boundary"] == "NO_APPEAL_DECISION_NO_ACADEMIC_RULING"

    def test_all_envelope_sections_present(self):
        out = _output()
        for key in [
            "academic_appeals_governance",
            "appeal_intake_envelope",
            "evidence_review_envelope",
            "policy_reference_envelope",
            "committee_review_envelope",
            "fairness_review_envelope",
            "due_process_envelope",
            "conflict_of_interest_envelope",
            "decision_boundary",
            "audit_trail_readiness",
            "related_case_boundaries",
            "forbidden_actions",
            "anti_fake_flags",
            "metric_contract",
        ]:
            assert key in out, f"Missing section: {key}"


# ===========================================================================
# 7. Academic appeals governance
# ===========================================================================

class TestAcademicAppealsGovernance:
    """academic_appeals_governance section — readiness-only flags."""

    def test_readiness_only(self):
        assert _output()["academic_appeals_governance"]["readiness_only"] is True

    def test_no_workflow_execution(self):
        assert _output()["academic_appeals_governance"]["no_workflow_execution"] is True

    def test_no_appeal_decision(self):
        assert _output()["academic_appeals_governance"]["no_appeal_decision"] is True

    def test_no_academic_ruling(self):
        assert _output()["academic_appeals_governance"]["no_academic_ruling"] is True

    def test_no_grade_or_status_change(self):
        assert _output()["academic_appeals_governance"]["no_grade_or_status_change"] is True


# ===========================================================================
# 8. Appeal intake envelope (12)
# ===========================================================================

class TestAppealIntakeEnvelope:
    """Appeal intake metadata only — no execution."""

    def test_intake_metadata_supported(self):
        assert _output()["appeal_intake_envelope"]["appeal_intake_metadata_supported"] is True

    def test_intake_metadata_only(self):
        assert _output()["appeal_intake_envelope"]["appeal_intake_metadata_only"] is True

    def test_no_external_submission(self):
        assert _output()["appeal_intake_envelope"]["appeal_submitted_externally"] is False

    def test_no_notification_executed(self):
        assert _output()["appeal_intake_envelope"]["notification_executed"] is False


# ===========================================================================
# 9. Evidence review envelope (13)
# ===========================================================================

class TestEvidenceReviewEnvelope:
    """Evidence review — no outcome or scoring."""

    def test_evidence_review_required(self):
        assert _output()["evidence_review_envelope"]["evidence_review_required"] is True

    def test_no_outcome_generated(self):
        assert _output()["evidence_review_envelope"]["evidence_outcome_generated"] is False

    def test_no_weighting_generated(self):
        assert _output()["evidence_review_envelope"]["evidence_weighting_generated"] is False

    def test_no_score_generated(self):
        assert _output()["evidence_review_envelope"]["evidence_score_generated"] is False


# ===========================================================================
# 10. Policy reference envelope (14)
# ===========================================================================

class TestPolicyReferenceEnvelope:
    """Policy reference — no automated interpretation or decision."""

    def test_policy_reference_required(self):
        assert _output()["policy_reference_envelope"]["policy_reference_required"] is True

    def test_no_automated_interpretation(self):
        assert _output()["policy_reference_envelope"]["policy_interpretation_automated"] is False

    def test_no_policy_decision_generated(self):
        assert _output()["policy_reference_envelope"]["policy_decision_generated"] is False


# ===========================================================================
# 11. Committee review envelope (8)
# ===========================================================================

class TestCommitteeReviewEnvelope:
    """Committee review — required, no automated outcome."""

    def test_committee_review_required(self):
        assert _output()["committee_review_envelope"]["committee_review_required"] is True

    def test_routing_metadata_supported(self):
        assert _output()["committee_review_envelope"]["committee_routing_metadata_supported"] is True

    def test_no_committee_outcome_generated(self):
        assert _output()["committee_review_envelope"]["committee_outcome_generated"] is False

    def test_no_committee_decision_executed(self):
        assert _output()["committee_review_envelope"]["committee_decision_executed"] is False


# ===========================================================================
# 12. Fairness review envelope (9)
# ===========================================================================

class TestFairnessReviewEnvelope:
    """Fairness review — required, no automated scoring."""

    def test_fairness_review_required(self):
        assert _output()["fairness_review_envelope"]["fairness_review_required"] is True

    def test_bias_check_required(self):
        assert _output()["fairness_review_envelope"]["bias_check_required"] is True

    def test_no_discriminatory_score(self):
        assert _output()["fairness_review_envelope"]["discriminatory_score_generated"] is False


# ===========================================================================
# 13. Due process envelope (10)
# ===========================================================================

class TestDueProcessEnvelope:
    """Due process — all rights confirmed, no automated execution."""

    def test_due_process_review_required(self):
        assert _output()["due_process_envelope"]["due_process_review_required"] is True

    def test_student_notification_right(self):
        assert _output()["due_process_envelope"]["student_notification_right"] is True

    def test_representation_right(self):
        assert _output()["due_process_envelope"]["representation_right"] is True

    def test_timeline_right(self):
        assert _output()["due_process_envelope"]["timeline_right"] is True

    def test_no_due_process_decision_generated(self):
        assert _output()["due_process_envelope"]["due_process_decision_generated"] is False


# ===========================================================================
# 14. Conflict-of-interest envelope (11)
# ===========================================================================

class TestConflictOfInterestEnvelope:
    """Conflict-of-interest review — required, no automated action."""

    def test_conflict_review_required(self):
        assert _output()["conflict_of_interest_envelope"]["conflict_of_interest_review_required"] is True

    def test_recusal_metadata_supported(self):
        assert _output()["conflict_of_interest_envelope"]["recusal_metadata_supported"] is True

    def test_no_conflict_decision_generated(self):
        assert _output()["conflict_of_interest_envelope"]["conflict_decision_generated"] is False


# ===========================================================================
# 15. Audit trail readiness
# ===========================================================================

class TestAuditTrailReadiness:
    """Audit trail — required, no write yet."""

    def test_audit_trail_required(self):
        assert _output()["audit_trail_readiness"]["audit_trail_required"] is True

    def test_due_process_trace_required(self):
        assert _output()["audit_trail_readiness"]["due_process_trace_required"] is True

    def test_no_immutable_record_written(self):
        assert _output()["audit_trail_readiness"]["immutable_record_written"] is False

    def test_no_external_submission_performed(self):
        assert _output()["audit_trail_readiness"]["external_submission_performed"] is False


# ===========================================================================
# 16-23. Decision boundary — all outcomes forbidden
# ===========================================================================

class TestDecisionBoundary:
    """Decision boundary — no automated decision of any kind."""

    def test_no_appeal_decision_generated(self):
        assert _output()["decision_boundary"]["appeal_decision_generated"] is False

    def test_no_appeal_approval_generated(self):
        assert _output()["decision_boundary"]["appeal_approval_generated"] is False

    def test_no_appeal_rejection_generated(self):
        assert _output()["decision_boundary"]["appeal_rejection_generated"] is False

    def test_no_academic_ruling_generated(self):
        assert _output()["decision_boundary"]["academic_ruling_generated"] is False

    def test_no_grade_change_generated(self):
        assert _output()["decision_boundary"]["grade_change_generated"] is False

    def test_no_penalty_reversal_generated(self):
        assert _output()["decision_boundary"]["penalty_reversal_generated"] is False

    def test_no_disciplinary_reversal_generated(self):
        assert _output()["decision_boundary"]["disciplinary_reversal_generated"] is False

    def test_no_sanction_reversal_generated(self):
        assert _output()["decision_boundary"]["sanction_reversal_generated"] is False

    def test_no_student_status_change_generated(self):
        assert _output()["decision_boundary"]["student_status_change_generated"] is False


# ===========================================================================
# 24. Related case boundaries (38-39)
# ===========================================================================

class TestRelatedCaseBoundaries:
    """Related case boundaries — UCE-007 and UCE-078 referenced, no override."""

    def test_uce_078_referenced(self):
        assert _output()["related_case_boundaries"]["academic_integrity_case_management_reference"] == "UCE-078"

    def test_uce_007_referenced(self):
        assert _output()["related_case_boundaries"]["disciplinary_case_management_reference"] == "UCE-007"

    def test_no_cross_case_decision_execution(self):
        assert _output()["related_case_boundaries"]["no_cross_case_decision_execution"] is True

    def test_no_integrity_finding_override(self):
        assert _output()["related_case_boundaries"]["no_integrity_finding_override"] is True

    def test_no_disciplinary_outcome_override(self):
        assert _output()["related_case_boundaries"]["no_disciplinary_outcome_override"] is True

    def test_uce_078_not_imported(self):
        """UCE-078 module is not imported in this service — only referenced as a string."""
        import app.modules.academic_appeals_workflow.service as svc
        assert not hasattr(svc, "get_academic_integrity_case_management_sensitive_readiness_foundation")

    def test_uce_007_not_imported(self):
        """UCE-007 module is not imported in this service — only referenced as a string."""
        import app.modules.academic_appeals_workflow.service as svc
        assert not hasattr(svc, "get_disciplinary_case_management_sensitive_readiness_foundation")


# ===========================================================================
# 25. Forbidden actions (32)
# ===========================================================================

class TestForbiddenActionsList:
    """Forbidden actions list — 20 items, all specific tokens present."""

    def test_is_list(self):
        assert isinstance(_output()["forbidden_actions"], list)

    def test_count_is_20(self):
        assert len(_output()["forbidden_actions"]) == 20

    def test_appeal_decision_present(self):
        assert "appeal_decision" in _output()["forbidden_actions"]

    def test_appeal_approval_present(self):
        assert "appeal_approval" in _output()["forbidden_actions"]

    def test_appeal_rejection_present(self):
        assert "appeal_rejection" in _output()["forbidden_actions"]

    def test_academic_ruling_present(self):
        assert "academic_ruling" in _output()["forbidden_actions"]

    def test_grade_change_present(self):
        assert "grade_change" in _output()["forbidden_actions"]

    def test_penalty_reversal_present(self):
        assert "penalty_reversal" in _output()["forbidden_actions"]

    def test_disciplinary_reversal_present(self):
        assert "disciplinary_reversal" in _output()["forbidden_actions"]

    def test_sanction_reversal_present(self):
        assert "sanction_reversal" in _output()["forbidden_actions"]

    def test_student_status_change_present(self):
        assert "student_status_change" in _output()["forbidden_actions"]

    def test_notification_execution_present(self):
        assert "notification_execution" in _output()["forbidden_actions"]

    def test_recommendation_present(self):
        assert "recommendation" in _output()["forbidden_actions"]

    def test_ranking_present(self):
        assert "ranking" in _output()["forbidden_actions"]

    def test_prioritization_score_present(self):
        assert "prioritization_score" in _output()["forbidden_actions"]

    def test_external_submission_present(self):
        assert "external_submission" in _output()["forbidden_actions"]

    def test_hidden_score_present(self):
        assert "hidden_score" in _output()["forbidden_actions"]

    def test_synthetic_score_present(self):
        assert "synthetic_score" in _output()["forbidden_actions"]

    def test_discriminatory_score_present(self):
        assert "discriminatory_score" in _output()["forbidden_actions"]

    def test_llm_call_present(self):
        assert "llm_call" in _output()["forbidden_actions"]

    def test_brain_execution_present(self):
        assert "brain_execution" in _output()["forbidden_actions"]

    def test_autonomous_decision_present(self):
        assert "autonomous_decision" in _output()["forbidden_actions"]


# ===========================================================================
# 26. Anti-fake flags (33)
# ===========================================================================

class TestAntiFakeFlags:
    """Anti-fake flags — 30 flags, all True."""

    def test_is_dict(self):
        assert isinstance(_output()["anti_fake_flags"], dict)

    def test_count_is_30(self):
        assert len(_output()["anti_fake_flags"]) == 30

    def test_all_flags_are_true(self):
        for k, v in _output()["anti_fake_flags"].items():
            assert v is True, f"anti_fake_flags[{k!r}] expected True, got {v!r}"

    def test_no_appeal_decision(self):
        assert _output()["anti_fake_flags"]["no_appeal_decision"] is True

    def test_no_appeal_approval(self):
        assert _output()["anti_fake_flags"]["no_appeal_approval"] is True

    def test_no_appeal_rejection(self):
        assert _output()["anti_fake_flags"]["no_appeal_rejection"] is True

    def test_no_academic_ruling(self):
        assert _output()["anti_fake_flags"]["no_academic_ruling"] is True

    def test_no_grade_change(self):
        assert _output()["anti_fake_flags"]["no_grade_change"] is True

    def test_no_penalty_reversal(self):
        assert _output()["anti_fake_flags"]["no_penalty_reversal"] is True

    def test_no_disciplinary_reversal(self):
        assert _output()["anti_fake_flags"]["no_disciplinary_reversal"] is True

    def test_no_sanction_reversal(self):
        assert _output()["anti_fake_flags"]["no_sanction_reversal"] is True

    def test_no_student_status_change(self):
        assert _output()["anti_fake_flags"]["no_student_status_change"] is True

    def test_no_notification_execution(self):
        assert _output()["anti_fake_flags"]["no_notification_execution"] is True

    def test_no_recommendation(self):
        assert _output()["anti_fake_flags"]["no_recommendation"] is True

    def test_no_ranking(self):
        assert _output()["anti_fake_flags"]["no_ranking"] is True

    def test_no_prioritization_score(self):
        assert _output()["anti_fake_flags"]["no_prioritization_score"] is True

    def test_no_external_submission(self):
        assert _output()["anti_fake_flags"]["no_external_submission"] is True

    def test_no_hidden_score(self):
        assert _output()["anti_fake_flags"]["no_hidden_score"] is True

    def test_no_synthetic_score(self):
        assert _output()["anti_fake_flags"]["no_synthetic_score"] is True

    def test_no_discriminatory_score(self):
        assert _output()["anti_fake_flags"]["no_discriminatory_score"] is True

    def test_no_llm_call(self):
        assert _output()["anti_fake_flags"]["no_llm_call"] is True

    def test_no_brain_execution(self):
        assert _output()["anti_fake_flags"]["no_brain_execution"] is True

    def test_no_autonomous_decision(self):
        assert _output()["anti_fake_flags"]["no_autonomous_decision"] is True

    def test_no_cross_case_decision_execution(self):
        assert _output()["anti_fake_flags"]["no_cross_case_decision_execution"] is True

    def test_no_integrity_finding_override(self):
        assert _output()["anti_fake_flags"]["no_integrity_finding_override"] is True

    def test_no_disciplinary_outcome_override(self):
        assert _output()["anti_fake_flags"]["no_disciplinary_outcome_override"] is True

    def test_human_review_required(self):
        assert _output()["anti_fake_flags"]["human_review_required"] is True

    def test_committee_review_required(self):
        assert _output()["anti_fake_flags"]["committee_review_required"] is True

    def test_fairness_review_required(self):
        assert _output()["anti_fake_flags"]["fairness_review_required"] is True

    def test_due_process_review_required(self):
        assert _output()["anti_fake_flags"]["due_process_review_required"] is True

    def test_conflict_of_interest_review_required(self):
        assert _output()["anti_fake_flags"]["conflict_of_interest_review_required"] is True

    def test_no_l5_claim(self):
        assert _output()["anti_fake_flags"]["no_l5_claim"] is True

    def test_no_l6_claim(self):
        assert _output()["anti_fake_flags"]["no_l6_claim"] is True


# ===========================================================================
# 27. Metric contract (34)
# ===========================================================================

class TestMetricContract:
    """Metric contract — counts and zero-execution anchors."""

    def test_a0306_count_is_1(self):
        assert _output()["metric_contract"]["A0306_academic_appeals_sensitive_foundation_count"] == 1

    def test_sensitive_domain_count_after_runtime_is_6(self):
        assert _output()["metric_contract"]["sensitive_domain_foundation_count_after_runtime"] == 6

    def test_sensitive_execution_count_is_0(self):
        assert _output()["metric_contract"]["sensitive_execution_count"] == 0

    def test_sensitive_auto_sanction_count_is_0(self):
        assert _output()["metric_contract"]["sensitive_auto_sanction_count"] == 0

    def test_sensitive_auto_disciplinary_decision_count_is_0(self):
        assert _output()["metric_contract"]["sensitive_auto_disciplinary_decision_count"] == 0

    def test_sensitive_auto_academic_integrity_decision_count_is_0(self):
        assert _output()["metric_contract"]["sensitive_auto_academic_integrity_decision_count"] == 0

    def test_sensitive_auto_appeal_decision_count_is_0(self):
        assert _output()["metric_contract"]["sensitive_auto_appeal_decision_count"] == 0

    def test_sensitive_hidden_score_count_is_0(self):
        assert _output()["metric_contract"]["sensitive_hidden_score_count"] == 0

    def test_sensitive_discriminatory_score_count_is_0(self):
        assert _output()["metric_contract"]["sensitive_discriminatory_score_count"] == 0

    def test_sensitive_synthetic_score_count_is_0(self):
        assert _output()["metric_contract"]["sensitive_synthetic_score_count"] == 0

    def test_sensitive_recommendation_count_is_0(self):
        assert _output()["metric_contract"]["sensitive_recommendation_count"] == 0

    def test_sensitive_external_submission_count_is_0(self):
        assert _output()["metric_contract"]["sensitive_external_submission_count"] == 0

    def test_baseline_impact_is_0(self):
        assert _output()["metric_contract"]["baseline_impact"] == 0

    def test_extension_impact_is_0(self):
        assert _output()["metric_contract"]["extension_impact"] == 0

    def test_ordinary_expansion_impact_is_0(self):
        assert _output()["metric_contract"]["ordinary_expansion_impact"] == 0

    def test_provider_readiness_impact_is_0(self):
        assert _output()["metric_contract"]["provider_readiness_impact"] == 0

    def test_brain_governance_impact_is_0(self):
        assert _output()["metric_contract"]["brain_governance_impact"] == 0

    def test_policy_procurement_impact_is_0(self):
        assert _output()["metric_contract"]["policy_procurement_impact"] == 0


# ===========================================================================
# 28. No executable outcome fields (40)
# ===========================================================================

class TestNoOutcomeFields:
    """Output must not contain any executable outcome field names at top level."""

    _FORBIDDEN_KEYS = {
        "appeal_decision",
        "appeal_outcome",
        "academic_ruling",
        "grade_change",
        "penalty_reversal",
        "disciplinary_reversal",
        "sanction_reversal",
        "student_status",
        "notification",
        "llm_response",
        "brain_response",
        "recommendation_result",
        "ranking_result",
        "prioritization_result",
        "external_submission_result",
    }

    def test_no_executable_outcome_keys_at_top_level(self):
        out = _output()
        for forbidden_key in self._FORBIDDEN_KEYS:
            assert forbidden_key not in out, f"Forbidden top-level key found: {forbidden_key!r}"


# ===========================================================================
# 29. L5/L6 boundary (37)
# ===========================================================================

class TestL5L6Boundary:
    """No L5/L6 claim in any output field."""

    def test_no_l5_claim_flag(self):
        assert _output()["anti_fake_flags"]["no_l5_claim"] is True

    def test_no_l6_claim_flag(self):
        assert _output()["anti_fake_flags"]["no_l6_claim"] is True

    def test_maturity_is_l3_not_l5(self):
        assert "L5" not in _output()["maturity"]

    def test_maturity_is_l3_not_l6(self):
        assert "L6" not in _output()["maturity"]
