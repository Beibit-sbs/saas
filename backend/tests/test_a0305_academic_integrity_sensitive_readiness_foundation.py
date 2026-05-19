"""
A-030.5-RUNTIME Gate: Academic Integrity Case Management Sensitive-Domain Readiness Foundation.

UCE-078 / academic_integrity_case_management
Contract: L3_DETERMINISTIC_READINESS_GOVERNANCE
Boundary: NO_EXECUTION + NO_FINDING_NO_PENALTY
Deferred: UCE-093 (academic_appeals_workflow)
"""
import pytest

from app.modules.academic_integrity_case_management.service import (
    get_academic_integrity_case_management_sensitive_readiness_foundation,
    validate_tenant_id,
)


@pytest.fixture(autouse=True)
def reset_shared_state(monkeypatch):
    """Module-local harness override — prevents global conftest reset from triggering
    expensive DB/LDAP connections for pure Python service tests (A-030.5 pattern)."""
    monkeypatch.setenv("RBAC_ALLOW_DEV_FALLBACK", "true")
    yield


class TestImports:
    """Verify importable symbols."""

    def test_main_function_importable(self):
        assert callable(get_academic_integrity_case_management_sensitive_readiness_foundation)

    def test_validate_tenant_id_importable(self):
        assert callable(validate_tenant_id)


class TestTenantValidationFailClosed:
    """Tenant ID validation — fail-closed contract."""

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

    def test_positive_accepted(self):
        assert validate_tenant_id(1) == 1

    def test_large_positive_accepted(self):
        assert validate_tenant_id(9999) == 9999


class TestMainFunctionTenantFailClosed:
    """Main function tenant validation via main function call."""

    def test_none_rejected(self):
        with pytest.raises(ValueError):
            get_academic_integrity_case_management_sensitive_readiness_foundation(None)

    def test_zero_rejected(self):
        with pytest.raises(ValueError):
            get_academic_integrity_case_management_sensitive_readiness_foundation(0)

    def test_negative_rejected(self):
        with pytest.raises(ValueError):
            get_academic_integrity_case_management_sensitive_readiness_foundation(-1)

    def test_bool_true_rejected(self):
        with pytest.raises(ValueError):
            get_academic_integrity_case_management_sensitive_readiness_foundation(True)

    def test_bool_false_rejected(self):
        with pytest.raises(ValueError):
            get_academic_integrity_case_management_sensitive_readiness_foundation(False)

    def test_string_rejected(self):
        with pytest.raises(ValueError):
            get_academic_integrity_case_management_sensitive_readiness_foundation("1")

    def test_float_rejected(self):
        with pytest.raises(ValueError):
            get_academic_integrity_case_management_sensitive_readiness_foundation(1.5)


class TestDeterministicOutput:
    """Output structure and determinism."""

    def test_returns_dict(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert isinstance(output, dict)

    def test_tenant_id_echoed(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=42)
        assert output["tenant_id"] == 42

    def test_deterministic_same_tenant(self):
        out1 = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        out2 = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert out1 == out2

    def test_different_tenants_differ_by_id_only(self):
        out1 = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        out2 = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=2)
        assert out1["tenant_id"] != out2["tenant_id"]
        assert out1["module"] == out2["module"]

    def test_no_side_effects(self):
        get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=2)
        out = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert out["tenant_id"] == 1


class TestTopLevelIdentityFields:
    """Top-level contract identity fields."""

    def test_module_name(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["module"] == "academic_integrity_case_management"

    def test_uce_id(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["uce_id"] == "UCE-078"

    def test_maturity(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["maturity"] == "L3_DETERMINISTIC_READINESS_GOVERNANCE"

    def test_readiness_layer(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["readiness_layer"] == "SENSITIVE_DOMAIN_FOUNDATION"

    def test_execution_mode(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["execution_mode"] == "NO_EXECUTION"

    def test_boundary(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["boundary"] == "NO_FINDING_NO_PENALTY"


class TestSensitiveDomainLayer:
    """Sensitive-domain layer contract structure."""

    def test_academic_integrity_case_governance_present(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert "academic_integrity_case_governance" in output

    def test_evidence_envelope_present(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert "evidence_envelope" in output

    def test_policy_reference_envelope_present(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert "policy_reference_envelope" in output

    def test_human_review_envelope_present(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert "human_review_envelope" in output

    def test_committee_review_envelope_present(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert "committee_review_envelope" in output

    def test_fairness_review_envelope_present(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert "fairness_review_envelope" in output

    def test_appeal_boundary_present(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert "appeal_boundary" in output

    def test_audit_trail_readiness_present(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert "audit_trail_readiness" in output

    def test_forbidden_actions_present(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert "forbidden_actions" in output

    def test_anti_fake_flags_present(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert "anti_fake_flags" in output

    def test_metric_contract_present(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert "metric_contract" in output


class TestReadinessMode:
    """Readiness-only governance — no execution."""

    def test_readiness_only_true(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["academic_integrity_case_governance"]["readiness_only"] is True

    def test_no_case_execution(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["academic_integrity_case_governance"]["no_case_execution"] is True

    def test_no_official_finding(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["academic_integrity_case_governance"]["no_official_finding"] is True

    def test_no_penalty_execution(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["academic_integrity_case_governance"]["no_penalty_execution"] is True

    def test_no_student_status_change(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["academic_integrity_case_governance"]["no_student_status_change"] is True

    def test_allowed_states_present(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        states = output["academic_integrity_case_governance"]["allowed_states"]
        assert isinstance(states, list)
        assert len(states) >= 3

    def test_forbidden_auto_actions_present(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        forbidden = output["academic_integrity_case_governance"]["forbidden_auto_actions"]
        assert isinstance(forbidden, list)
        assert len(forbidden) >= 2


class TestEvidenceEnvelope:
    """Evidence envelope — no outcome or detection."""

    def test_evidence_intake_supported(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["evidence_envelope"]["evidence_intake_metadata_supported"] is True

    def test_evidence_review_required(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["evidence_envelope"]["evidence_review_required"] is True

    def test_no_evidence_outcome(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["evidence_envelope"]["evidence_outcome_generated"] is False

    def test_no_similarity_score(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["evidence_envelope"]["similarity_score_generated"] is False

    def test_no_plagiarism_detection(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["evidence_envelope"]["plagiarism_detection_performed"] is False

    def test_no_finding_generated(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["evidence_envelope"]["no_finding_generated"] is True

    def test_no_determination_generated(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["evidence_envelope"]["no_determination_generated"] is True


class TestPolicyReferenceEnvelope:
    """Policy reference — no auto interpretation or decision."""

    def test_policy_reference_required(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["policy_reference_envelope"]["policy_reference_required"] is True

    def test_no_auto_interpretation(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["policy_reference_envelope"]["policy_interpretation_automated"] is False

    def test_no_policy_decision(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["policy_reference_envelope"]["policy_decision_generated"] is False

    def test_no_auto_enforcement(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["policy_reference_envelope"]["no_auto_enforcement"] is True

    def test_human_interpretation_required(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["policy_reference_envelope"]["human_policy_interpretation_required"] is True


class TestHumanReviewBoundaries:
    """Human review required — no automated decision."""

    def test_human_review_required(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["human_review_envelope"]["human_review_required"] is True

    def test_reviewer_decision_required(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["human_review_envelope"]["reviewer_decision_required"] is True

    def test_no_automated_decision(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["human_review_envelope"]["automated_decision_allowed"] is False

    def test_no_automated_review(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["human_review_envelope"]["no_automated_review"] is True


class TestCommitteeReviewBoundaries:
    """Committee review required — no automated committee decision."""

    def test_committee_review_required(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["committee_review_envelope"]["committee_review_required"] is True

    def test_no_committee_outcome_generated(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["committee_review_envelope"]["committee_outcome_generated"] is False

    def test_no_committee_decision_executed(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["committee_review_envelope"]["committee_decision_executed"] is False

    def test_no_automated_committee_decision(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["committee_review_envelope"]["no_automated_committee_decision"] is True


class TestFairnessReviewBoundaries:
    """Fairness review required — no discriminatory scores."""

    def test_fairness_review_required(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["fairness_review_envelope"]["fairness_review_required"] is True

    def test_bias_check_required(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["fairness_review_envelope"]["bias_check_required"] is True

    def test_no_discriminatory_score(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["fairness_review_envelope"]["discriminatory_score_generated"] is False

    def test_no_automated_fairness_decision(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["fairness_review_envelope"]["no_automated_fairness_decision"] is True


class TestAppealBoundary:
    """Appeal boundary — metadata only, no execution, UCE-093 deferred."""

    def test_appeal_available(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["appeal_boundary"]["appeal_available"] is True

    def test_appeal_metadata_only(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["appeal_boundary"]["appeal_metadata_only"] is True

    def test_no_appeal_decision_generated(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["appeal_boundary"]["appeal_decision_generated"] is False

    def test_academic_appeals_workflow_deferred(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["appeal_boundary"]["academic_appeals_workflow_deferred"] is True

    def test_deferred_candidate_uce_093(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["appeal_boundary"]["deferred_candidate"] == "UCE-093"

    def test_no_appeal_waiver_by_automation(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["appeal_boundary"]["no_appeal_waiver_by_automation"] is True


class TestAuditTrailReadiness:
    """Audit trail — required, no immutable write yet."""

    def test_audit_trail_required(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["audit_trail_readiness"]["audit_trail_required"] is True

    def test_due_process_trace_required(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["audit_trail_readiness"]["due_process_trace_required"] is True

    def test_no_immutable_record_written(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["audit_trail_readiness"]["immutable_record_written"] is False

    def test_no_external_submission(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["audit_trail_readiness"]["external_submission_performed"] is False

    def test_audit_logging_ready(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["audit_trail_readiness"]["audit_logging_ready"] is True

    def test_no_hidden_action(self):
        output = get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)
        assert output["audit_trail_readiness"]["no_hidden_action"] is True


class TestForbiddenActionsList:
    """Forbidden actions — all 18 items present."""

    def _fa(self):
        return get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)["forbidden_actions"]

    def test_is_list(self):
        assert isinstance(self._fa(), list)

    def test_academic_integrity_finding_forbidden(self):
        assert "academic_integrity_finding" in self._fa()

    def test_plagiarism_finding_forbidden(self):
        assert "plagiarism_finding" in self._fa()

    def test_cheating_finding_forbidden(self):
        assert "cheating_finding" in self._fa()

    def test_guilt_determination_forbidden(self):
        assert "guilt_determination" in self._fa()

    def test_grade_penalty_forbidden(self):
        assert "grade_penalty" in self._fa()

    def test_disciplinary_penalty_forbidden(self):
        assert "disciplinary_penalty" in self._fa()

    def test_sanction_forbidden(self):
        assert "sanction" in self._fa()

    def test_student_status_change_forbidden(self):
        assert "student_status_change" in self._fa()

    def test_notification_execution_forbidden(self):
        assert "notification_execution" in self._fa()

    def test_recommendation_forbidden(self):
        assert "recommendation" in self._fa()

    def test_ranking_forbidden(self):
        assert "ranking" in self._fa()

    def test_external_submission_forbidden(self):
        assert "external_submission" in self._fa()

    def test_hidden_score_forbidden(self):
        assert "hidden_score" in self._fa()

    def test_synthetic_score_forbidden(self):
        assert "synthetic_score" in self._fa()

    def test_discriminatory_score_forbidden(self):
        assert "discriminatory_score" in self._fa()

    def test_llm_call_forbidden(self):
        assert "llm_call" in self._fa()

    def test_brain_execution_forbidden(self):
        assert "brain_execution" in self._fa()

    def test_autonomous_decision_forbidden(self):
        assert "autonomous_decision" in self._fa()

    def test_count_ge_18(self):
        assert len(self._fa()) >= 18


class TestAntiFakeFlags:
    """Anti-fake flags — all must be True (no hidden/synthetic/auto decisions)."""

    def _aff(self):
        return get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)["anti_fake_flags"]

    def test_no_academic_integrity_finding(self):
        assert self._aff()["no_academic_integrity_finding"] is True

    def test_no_plagiarism_finding(self):
        assert self._aff()["no_plagiarism_finding"] is True

    def test_no_cheating_finding(self):
        assert self._aff()["no_cheating_finding"] is True

    def test_no_guilt_determination(self):
        assert self._aff()["no_guilt_determination"] is True

    def test_no_grade_penalty(self):
        assert self._aff()["no_grade_penalty"] is True

    def test_no_disciplinary_penalty(self):
        assert self._aff()["no_disciplinary_penalty"] is True

    def test_no_sanction(self):
        assert self._aff()["no_sanction"] is True

    def test_no_student_status_change(self):
        assert self._aff()["no_student_status_change"] is True

    def test_no_notification_execution(self):
        assert self._aff()["no_notification_execution"] is True

    def test_no_recommendation(self):
        assert self._aff()["no_recommendation"] is True

    def test_no_ranking(self):
        assert self._aff()["no_ranking"] is True

    def test_no_external_submission(self):
        assert self._aff()["no_external_submission"] is True

    def test_no_hidden_score(self):
        assert self._aff()["no_hidden_score"] is True

    def test_no_synthetic_score(self):
        assert self._aff()["no_synthetic_score"] is True

    def test_no_discriminatory_score(self):
        assert self._aff()["no_discriminatory_score"] is True

    def test_no_llm_call(self):
        assert self._aff()["no_llm_call"] is True

    def test_no_brain_execution(self):
        assert self._aff()["no_brain_execution"] is True

    def test_no_autonomous_decision(self):
        assert self._aff()["no_autonomous_decision"] is True

    def test_no_l5_claim(self):
        assert self._aff()["no_l5_claim"] is True

    def test_no_l6_claim(self):
        assert self._aff()["no_l6_claim"] is True

    def test_human_review_required_flag(self):
        assert self._aff()["human_review_required"] is True

    def test_committee_review_required_flag(self):
        assert self._aff()["committee_review_required"] is True

    def test_fairness_review_required_flag(self):
        assert self._aff()["fairness_review_required"] is True

    def test_appeal_available_flag(self):
        assert self._aff()["appeal_available"] is True


class TestMetricContract:
    """Metric contract — A-030.5 counters and boundaries."""

    def _mc(self):
        return get_academic_integrity_case_management_sensitive_readiness_foundation(tenant_id=1)["metric_contract"]

    def test_a0305_count_is_1(self):
        assert self._mc()["A0305_academic_integrity_sensitive_foundation_count"] == 1

    def test_sensitive_foundation_count_after_runtime_is_5(self):
        assert self._mc()["sensitive_domain_foundation_count_after_runtime"] == 5

    def test_sensitive_execution_count_is_0(self):
        assert self._mc()["sensitive_execution_count"] == 0

    def test_sensitive_auto_sanction_count_is_0(self):
        assert self._mc()["sensitive_auto_sanction_count"] == 0

    def test_sensitive_auto_disciplinary_decision_count_is_0(self):
        assert self._mc()["sensitive_auto_disciplinary_decision_count"] == 0

    def test_sensitive_auto_academic_integrity_decision_count_is_0(self):
        assert self._mc()["sensitive_auto_academic_integrity_decision_count"] == 0

    def test_sensitive_hidden_score_count_is_0(self):
        assert self._mc()["sensitive_hidden_score_count"] == 0

    def test_sensitive_discriminatory_score_count_is_0(self):
        assert self._mc()["sensitive_discriminatory_score_count"] == 0

    def test_sensitive_synthetic_score_count_is_0(self):
        assert self._mc()["sensitive_synthetic_score_count"] == 0

    def test_sensitive_recommendation_count_is_0(self):
        assert self._mc()["sensitive_recommendation_count"] == 0

    def test_sensitive_external_submission_count_is_0(self):
        assert self._mc()["sensitive_external_submission_count"] == 0

    def test_baseline_impact_is_0(self):
        assert self._mc()["baseline_impact"] == 0

    def test_extension_impact_is_0(self):
        assert self._mc()["extension_impact"] == 0

    def test_ordinary_expansion_impact_is_0(self):
        assert self._mc()["ordinary_expansion_impact"] == 0

    def test_provider_readiness_impact_is_0(self):
        assert self._mc()["provider_readiness_impact"] == 0

    def test_brain_governance_impact_is_0(self):
        assert self._mc()["brain_governance_impact"] == 0

    def test_policy_procurement_impact_is_0(self):
        assert self._mc()["policy_procurement_impact"] == 0
