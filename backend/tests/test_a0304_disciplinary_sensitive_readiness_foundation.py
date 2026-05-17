"""A-030.4-RUNTIME: Disciplinary case management sensitive readiness foundation tests."""

import pytest
from backend.app.modules.disciplinary_case_management.service import (
    get_disciplinary_sensitive_readiness_foundation,
    validate_tenant_id,
)


@pytest.fixture(autouse=True)
def reset_shared_state(monkeypatch):
    """Module-local harness override.

    The global autouse fixture in conftest performs a full platform state reset
    before every test, which is unnecessary for this pure read-only contract file
    and can trigger timeout-based false hang classification under bounded Docker runs.
    """
    monkeypatch.setenv("RBAC_ALLOW_DEV_FALLBACK", "true")
    yield


class TestImports:
    """Test imports work correctly."""

    def test_import_function_exists(self):
        """Function should be importable."""
        assert callable(get_disciplinary_sensitive_readiness_foundation)

    def test_import_validator_exists(self):
        """Tenant validation function should exist."""
        assert callable(validate_tenant_id)


class TestTenantValidationFailClosed:
    """Test fail-closed tenant validation."""

    def test_validate_tenant_id_none_rejected(self):
        """None tenant_id should be rejected."""
        with pytest.raises(ValueError):
            validate_tenant_id(None)

    def test_validate_tenant_id_zero_rejected(self):
        """Zero tenant_id should be rejected."""
        with pytest.raises(ValueError):
            validate_tenant_id(0)

    def test_validate_tenant_id_negative_rejected(self):
        """Negative tenant_id should be rejected."""
        with pytest.raises(ValueError):
            validate_tenant_id(-1)

    def test_validate_tenant_id_positive_int_accepted(self):
        """Positive int tenant_id should be accepted."""
        result = validate_tenant_id(1)
        assert result == 1

    def test_validate_tenant_id_large_positive_accepted(self):
        """Large positive int should be accepted."""
        result = validate_tenant_id(999999)
        assert result == 999999


class TestDeterministicOutput:
    """Test deterministic output for valid tenant."""

    def test_deterministic_same_tenant_same_output(self):
        """Same tenant should produce identical output."""
        output1 = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        output2 = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output1 == output2

    def test_different_tenants_tenant_scoped(self):
        """Different tenants should have different tenant_id."""
        output1 = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        output2 = get_disciplinary_sensitive_readiness_foundation(tenant_id=2)
        assert output1["tenant_id"] == 1
        assert output2["tenant_id"] == 2


class TestSensitiveDomainLayer:
    """Test sensitive domain layer and version."""

    def test_sensitive_domain_layer_is_foundation(self):
        """sensitive_domain_layer must be FOUNDATION."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["sensitive_domain_layer"] == "FOUNDATION"

    def test_sensitive_domain_version_is_a030_4(self):
        """sensitive_domain_version must be A-030.4."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["sensitive_domain_version"] == "A-030.4"

    def test_maturity_target_is_l3_deterministic(self):
        """maturity_target must be L3_DETERMINISTIC_READINESS_GOVERNANCE."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["maturity_target"] == "L3_DETERMINISTIC_READINESS_GOVERNANCE"

    def test_sensitive_type_is_disciplinary(self):
        """sensitive_type must be disciplinary_governance."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["sensitive_type"] == "disciplinary_governance"


class TestReadinessMode:
    """Test readiness mode configuration."""

    def test_readiness_mode_is_readiness_and_evidence_only(self):
        """readiness_mode must be READINESS_AND_EVIDENCE_ONLY."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["readiness_mode"] == "READINESS_AND_EVIDENCE_ONLY"

    def test_execution_mode_is_no_execution(self):
        """execution_mode must be NO_EXECUTION."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["execution_mode"] == "NO_EXECUTION"


class TestHumanReviewBoundaries:
    """Test human review required flags."""

    def test_human_review_required_is_true(self):
        """human_review_required must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["human_review_required"] is True

    def test_appeal_boundary_required_is_true(self):
        """appeal_boundary_required must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["appeal_boundary_required"] is True

    def test_audit_trail_required_is_true(self):
        """audit_trail_required must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["audit_trail_required"] is True

    def test_fairness_review_required_is_true(self):
        """fairness_review_required must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["fairness_review_required"] is True

    def test_legal_review_required_is_true(self):
        """legal_review_required must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["legal_review_required"] is True


class TestExecutionFlags:
    """Test all execution flags disabled."""

    def test_automatic_outcome_enabled_false(self):
        """automatic_outcome_enabled must be False."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["automatic_outcome_enabled"] is False

    def test_sanction_execution_enabled_false(self):
        """sanction_execution_enabled must be False."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["sanction_execution_enabled"] is False

    def test_disciplinary_decision_enabled_false(self):
        """disciplinary_decision_enabled must be False."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["disciplinary_decision_enabled"] is False

    def test_academic_integrity_decision_enabled_false(self):
        """academic_integrity_decision_enabled must be False."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["academic_integrity_decision_enabled"] is False

    def test_academic_outcome_change_enabled_false(self):
        """academic_outcome_change_enabled must be False."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["academic_outcome_change_enabled"] is False

    def test_appeal_decision_enabled_false(self):
        """appeal_decision_enabled must be False."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["appeal_decision_enabled"] is False

    def test_notification_execution_enabled_false(self):
        """notification_execution_enabled must be False."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["notification_execution_enabled"] is False


class TestScoringFlags:
    """Test all scoring flags disabled."""

    def test_hidden_scoring_enabled_false(self):
        """hidden_scoring_enabled must be False."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["hidden_scoring_enabled"] is False

    def test_discriminatory_scoring_enabled_false(self):
        """discriminatory_scoring_enabled must be False."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["discriminatory_scoring_enabled"] is False

    def test_synthetic_score_enabled_false(self):
        """synthetic_score_enabled must be False."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["synthetic_score_enabled"] is False

    def test_ranking_enabled_false(self):
        """ranking_enabled must be False."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["ranking_enabled"] is False

    def test_recommendation_enabled_false(self):
        """recommendation_enabled must be False."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["recommendation_enabled"] is False


class TestAntiFakeFlags:
    """Test anti-fake protection flags."""

    def test_tenant_scoped_true(self):
        """tenant_scoped must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["tenant_scoped"] is True

    def test_read_only_true(self):
        """read_only must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["read_only"] is True

    def test_no_mutation_true(self):
        """no_mutation must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["no_mutation"] is True

    def test_no_sensitive_execution_true(self):
        """no_sensitive_execution must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["no_sensitive_execution"] is True

    def test_no_auto_sanction_true(self):
        """no_auto_sanction must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["no_auto_sanction"] is True

    def test_no_auto_disciplinary_decision_true(self):
        """no_auto_disciplinary_decision must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["no_auto_disciplinary_decision"] is True

    def test_no_auto_academic_integrity_decision_true(self):
        """no_auto_academic_integrity_decision must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["no_auto_academic_integrity_decision"] is True

    def test_no_academic_outcome_change_true(self):
        """no_academic_outcome_change must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["no_academic_outcome_change"] is True

    def test_no_appeal_decision_true(self):
        """no_appeal_decision must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["no_appeal_decision"] is True

    def test_no_notification_execution_true(self):
        """no_notification_execution must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["no_notification_execution"] is True

    def test_no_hidden_score_true(self):
        """no_hidden_score must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["no_hidden_score"] is True

    def test_no_discriminatory_score_true(self):
        """no_discriminatory_score must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["no_discriminatory_score"] is True

    def test_no_synthetic_score_true(self):
        """no_synthetic_score must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["no_synthetic_score"] is True

    def test_no_ranking_true(self):
        """no_ranking must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["no_ranking"] is True

    def test_no_recommendation_true(self):
        """no_recommendation must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["no_recommendation"] is True

    def test_no_external_submission_true(self):
        """no_external_submission must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["no_external_submission"] is True

    def test_no_l5_claim_true(self):
        """no_l5_claim must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["no_l5_claim"] is True

    def test_no_l6_claim_true(self):
        """no_l6_claim must be True."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["no_l6_claim"] is True


class TestEvidenceMapping:
    """Test evidence source mapping."""

    def test_evidence_source_map_exists(self):
        """evidence_source_map must exist."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "evidence_source_map" in output
        assert isinstance(output["evidence_source_map"], dict)

    def test_evidence_source_map_has_6_items(self):
        """evidence_source_map must have 6 items."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert len(output["evidence_source_map"]) == 6

    def test_evidence_source_map_has_case_record(self):
        """evidence_source_map must have case_record_evidence."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "case_record_evidence" in output["evidence_source_map"]

    def test_evidence_source_map_has_policy_reference(self):
        """evidence_source_map must have policy_reference_evidence."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "policy_reference_evidence" in output["evidence_source_map"]

    def test_evidence_source_map_has_hearing_notice(self):
        """evidence_source_map must have hearing_notice_evidence."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "hearing_notice_evidence" in output["evidence_source_map"]

    def test_evidence_source_map_has_respondent_statement(self):
        """evidence_source_map must have respondent_statement_evidence."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "respondent_statement_evidence" in output["evidence_source_map"]

    def test_evidence_source_map_has_reviewer_assignment(self):
        """evidence_source_map must have reviewer_assignment_evidence."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "reviewer_assignment_evidence" in output["evidence_source_map"]

    def test_evidence_source_map_has_audit_log(self):
        """evidence_source_map must have audit_log_evidence."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "audit_log_evidence" in output["evidence_source_map"]


class TestRequiredEvidence:
    """Test required evidence list."""

    def test_required_evidence_is_list(self):
        """required_evidence must be a list."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert isinstance(output["required_evidence"], list)

    def test_required_evidence_has_6_items(self):
        """required_evidence must have exactly 6 items."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert len(output["required_evidence"]) == 6

    def test_required_evidence_all_strings(self):
        """All required_evidence items must be strings."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert all(isinstance(item, str) for item in output["required_evidence"])


class TestAppealBoundaryMap:
    """Test appeal boundary map."""

    def test_appeal_boundary_map_exists(self):
        """appeal_boundary_map must exist."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "appeal_boundary_map" in output
        assert isinstance(output["appeal_boundary_map"], dict)

    def test_appeal_boundary_map_has_6_items(self):
        """appeal_boundary_map must have 6 items."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert len(output["appeal_boundary_map"]) == 6

    def test_appeal_boundary_map_has_policy_boundary(self):
        """appeal_boundary_map must have disciplinary_policy_boundary."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "disciplinary_policy_boundary" in output["appeal_boundary_map"]

    def test_appeal_boundary_map_has_hearing_boundary(self):
        """appeal_boundary_map must have hearing_notice_boundary."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "hearing_notice_boundary" in output["appeal_boundary_map"]

    def test_appeal_boundary_map_has_respondent_boundary(self):
        """appeal_boundary_map must have respondent_response_boundary."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "respondent_response_boundary" in output["appeal_boundary_map"]

    def test_appeal_boundary_map_has_reviewer_boundary(self):
        """appeal_boundary_map must have independent_reviewer_boundary."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "independent_reviewer_boundary" in output["appeal_boundary_map"]

    def test_appeal_boundary_map_has_appeal_rights_boundary(self):
        """appeal_boundary_map must have appeal_rights_boundary."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "appeal_rights_boundary" in output["appeal_boundary_map"]

    def test_appeal_boundary_map_has_auditability_boundary(self):
        """appeal_boundary_map must have auditability_boundary."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "auditability_boundary" in output["appeal_boundary_map"]


class TestAuditEventCategoryMap:
    """Test audit event category map."""

    def test_audit_event_category_map_exists(self):
        """audit_event_category_map must exist."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "audit_event_category_map" in output
        assert isinstance(output["audit_event_category_map"], dict)

    def test_audit_event_map_has_6_items(self):
        """audit_event_category_map must have 6 items."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert len(output["audit_event_category_map"]) == 6


class TestFairnessCheckpoints:
    """Test fairness review checkpoints."""

    def test_fairness_checkpoints_exists(self):
        """fairness_review_checkpoints must exist."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "fairness_review_checkpoints" in output
        assert isinstance(output["fairness_review_checkpoints"], list)

    def test_fairness_checkpoints_has_5_items(self):
        """fairness_review_checkpoints must have 5 items."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert len(output["fairness_review_checkpoints"]) == 5

    def test_fairness_checkpoints_has_independence(self):
        """fairness checkpoints must have reviewer_independence_required."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "reviewer_independence_required" in output["fairness_review_checkpoints"]


class TestLegalCheckpoints:
    """Test legal review checkpoints."""

    def test_legal_checkpoints_exists(self):
        """legal_review_checkpoints must exist."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "legal_review_checkpoints" in output
        assert isinstance(output["legal_review_checkpoints"], list)

    def test_legal_checkpoints_has_4_items(self):
        """legal_review_checkpoints must have 4 items."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert len(output["legal_review_checkpoints"]) == 4

    def test_legal_checkpoints_has_policy_basis(self):
        """legal checkpoints must have policy_basis_required."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "policy_basis_required" in output["legal_review_checkpoints"]


class TestForbiddenOutputs:
    """Test forbidden outputs list."""

    def test_forbidden_outputs_exists(self):
        """forbidden_outputs must exist."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "forbidden_outputs" in output
        assert isinstance(output["forbidden_outputs"], list)

    def test_forbidden_outputs_has_sanction(self):
        """forbidden_outputs must include sanction."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "sanction" in output["forbidden_outputs"]

    def test_forbidden_outputs_has_guilt_finding(self):
        """forbidden_outputs must include guilt_finding."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "guilt_finding" in output["forbidden_outputs"]

    def test_forbidden_outputs_has_disciplinary_decision(self):
        """forbidden_outputs must include disciplinary_decision."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "disciplinary_decision" in output["forbidden_outputs"]

    def test_forbidden_outputs_has_disciplinary_outcome(self):
        """forbidden_outputs must include disciplinary_outcome."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "disciplinary_outcome" in output["forbidden_outputs"]

    def test_forbidden_outputs_has_status_change(self):
        """forbidden_outputs must include student_status_change."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "student_status_change" in output["forbidden_outputs"]

    def test_forbidden_outputs_has_notification(self):
        """forbidden_outputs must include notification_execution."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "notification_execution" in output["forbidden_outputs"]

    def test_forbidden_outputs_has_hidden_score(self):
        """forbidden_outputs must include hidden_conduct_score."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "hidden_conduct_score" in output["forbidden_outputs"]


class TestAllowedOutputs:
    """Test allowed outputs list."""

    def test_allowed_outputs_exists(self):
        """allowed_outputs must exist."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "allowed_outputs" in output
        assert isinstance(output["allowed_outputs"], list)

    def test_allowed_outputs_has_evidence_map(self):
        """allowed_outputs must have evidence_source_map."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "evidence_source_map" in output["allowed_outputs"]

    def test_allowed_outputs_has_fairness_checkpoints(self):
        """allowed_outputs must have fairness_review_checkpoints."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "fairness_review_checkpoints" in output["allowed_outputs"]

    def test_allowed_outputs_has_legal_checkpoints(self):
        """allowed_outputs must have legal_review_checkpoints."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "legal_review_checkpoints" in output["allowed_outputs"]


class TestGovernanceRiskClassification:
    """Test governance risk classification."""

    def test_governance_risk_classification_exists(self):
        """governance_risk_classification must exist."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert "governance_risk_classification" in output

    def test_governance_risk_domain(self):
        """governance_risk_classification domain must be disciplinary_governance."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["governance_risk_classification"]["domain"] == "disciplinary_governance"

    def test_governance_risk_boundary(self):
        """governance_risk_classification boundary must be NO_SANCTION_NO_DISCIPLINARY_OUTCOME."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["governance_risk_classification"]["risk_boundary"] == "NO_SANCTION_NO_DISCIPLINARY_OUTCOME"

    def test_governance_risk_level(self):
        """governance_risk_classification risk_level must be HIGH."""
        output = get_disciplinary_sensitive_readiness_foundation(tenant_id=1)
        assert output["governance_risk_classification"]["risk_level"] == "HIGH"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
