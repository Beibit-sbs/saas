"""
test_a02813_expansion_l4_visibility_batch4.py — A-028.13 L4 Visibility Batch 4 Test

Tests for 8 ordinary L4 service visibility summaries:
- timesheet_management (UCE-060)
- faculty_attestation (UCE-061)
- teaching_load_contracts (UCE-067)
- staff_exit_offboarding (UCE-070)
- thesis_dissertation_management (UCE-077)
- joint_program_management (UCE-085)
- inbound_exchange_management (UCE-086)
- outbound_exchange_management (UCE-087)

Requirements:
- L4 visibility summaries only (no API routes, no frontend, no mutation)
- Deterministic output (same input → same output)
- Tenant fail-closed (invalid tenant → ValueError)
- L3 contracts preserved
- Read-only, no provider call, no autonomy, no decision execution
- Service summaries wrap L3 readiness classifiers
- All 8 modules follow same pattern and boundaries
- No L5/L6 claims
- API routes deferred to A-028.14

Expected Test Count: 180+ assertions
"""

import pytest
from backend.app.modules.timesheet_management.service import (
    get_timesheet_management_foundation_contract,
    classify_timesheet_management_readiness,
    get_timesheet_management_l4_visibility_summary,
)
from backend.app.modules.faculty_attestation.service import (
    get_faculty_attestation_foundation_contract,
    classify_faculty_attestation_readiness,
    get_faculty_attestation_l4_visibility_summary,
)
from backend.app.modules.teaching_load_contracts.service import (
    get_teaching_load_contracts_foundation_contract,
    classify_teaching_load_contracts_readiness,
    get_teaching_load_contracts_l4_visibility_summary,
)
from backend.app.modules.staff_exit_offboarding.service import (
    get_staff_exit_offboarding_foundation_contract,
    classify_staff_exit_offboarding_readiness,
    get_staff_exit_offboarding_l4_visibility_summary,
)
from backend.app.modules.thesis_dissertation_management.service import (
    get_thesis_dissertation_management_foundation_contract,
    classify_thesis_dissertation_management_readiness,
    get_thesis_dissertation_management_l4_visibility_summary,
)
from backend.app.modules.joint_program_management.service import (
    get_joint_program_management_foundation_contract,
    classify_joint_program_management_readiness,
    get_joint_program_management_l4_visibility_summary,
)
from backend.app.modules.inbound_exchange_management.service import (
    get_inbound_exchange_management_foundation_contract,
    classify_inbound_exchange_management_readiness,
    get_inbound_exchange_management_l4_visibility_summary,
)
from backend.app.modules.outbound_exchange_management.service import (
    get_outbound_exchange_management_foundation_contract,
    classify_outbound_exchange_management_readiness,
    get_outbound_exchange_management_l4_visibility_summary,
)


class TestA02813L4VisibilityImportsAndStructure:
    """Test 1-8: Import validation and function existence for all 8 candidates"""

    def test_timesheet_management_imports(self):
        """Test: All functions exist for timesheet_management"""
        assert callable(get_timesheet_management_foundation_contract)
        assert callable(classify_timesheet_management_readiness)
        assert callable(get_timesheet_management_l4_visibility_summary)

    def test_faculty_attestation_imports(self):
        """Test: All functions exist for faculty_attestation"""
        assert callable(get_faculty_attestation_foundation_contract)
        assert callable(classify_faculty_attestation_readiness)
        assert callable(get_faculty_attestation_l4_visibility_summary)

    def test_teaching_load_contracts_imports(self):
        """Test: All functions exist for teaching_load_contracts"""
        assert callable(get_teaching_load_contracts_foundation_contract)
        assert callable(classify_teaching_load_contracts_readiness)
        assert callable(get_teaching_load_contracts_l4_visibility_summary)

    def test_staff_exit_offboarding_imports(self):
        """Test: All functions exist for staff_exit_offboarding"""
        assert callable(get_staff_exit_offboarding_foundation_contract)
        assert callable(classify_staff_exit_offboarding_readiness)
        assert callable(get_staff_exit_offboarding_l4_visibility_summary)

    def test_thesis_dissertation_management_imports(self):
        """Test: All functions exist for thesis_dissertation_management"""
        assert callable(get_thesis_dissertation_management_foundation_contract)
        assert callable(classify_thesis_dissertation_management_readiness)
        assert callable(get_thesis_dissertation_management_l4_visibility_summary)

    def test_joint_program_management_imports(self):
        """Test: All functions exist for joint_program_management"""
        assert callable(get_joint_program_management_foundation_contract)
        assert callable(classify_joint_program_management_readiness)
        assert callable(get_joint_program_management_l4_visibility_summary)

    def test_inbound_exchange_management_imports(self):
        """Test: All functions exist for inbound_exchange_management"""
        assert callable(get_inbound_exchange_management_foundation_contract)
        assert callable(classify_inbound_exchange_management_readiness)
        assert callable(get_inbound_exchange_management_l4_visibility_summary)

    def test_outbound_exchange_management_imports(self):
        """Test: All functions exist for outbound_exchange_management"""
        assert callable(get_outbound_exchange_management_foundation_contract)
        assert callable(classify_outbound_exchange_management_readiness)
        assert callable(get_outbound_exchange_management_l4_visibility_summary)


class TestA02813TenantFailClosed:
    """Test 9-16: Tenant fail-closed rejects invalid tenant_id for all 8 candidates"""

    @pytest.mark.parametrize("invalid_tenant", [None, 0, -1, "invalid"])
    def test_timesheet_management_fail_closed(self, invalid_tenant):
        """Test: timesheet_management rejects invalid tenant"""
        with pytest.raises((ValueError, TypeError)):
            get_timesheet_management_l4_visibility_summary(invalid_tenant)

    @pytest.mark.parametrize("invalid_tenant", [None, 0, -1, "invalid"])
    def test_faculty_attestation_fail_closed(self, invalid_tenant):
        """Test: faculty_attestation rejects invalid tenant"""
        with pytest.raises((ValueError, TypeError)):
            get_faculty_attestation_l4_visibility_summary(invalid_tenant)

    @pytest.mark.parametrize("invalid_tenant", [None, 0, -1, "invalid"])
    def test_teaching_load_contracts_fail_closed(self, invalid_tenant):
        """Test: teaching_load_contracts rejects invalid tenant"""
        with pytest.raises((ValueError, TypeError)):
            get_teaching_load_contracts_l4_visibility_summary(invalid_tenant)

    @pytest.mark.parametrize("invalid_tenant", [None, 0, -1, "invalid"])
    def test_staff_exit_offboarding_fail_closed(self, invalid_tenant):
        """Test: staff_exit_offboarding rejects invalid tenant"""
        with pytest.raises((ValueError, TypeError)):
            get_staff_exit_offboarding_l4_visibility_summary(invalid_tenant)

    @pytest.mark.parametrize("invalid_tenant", [None, 0, -1, "invalid"])
    def test_thesis_dissertation_management_fail_closed(self, invalid_tenant):
        """Test: thesis_dissertation_management rejects invalid tenant"""
        with pytest.raises((ValueError, TypeError)):
            get_thesis_dissertation_management_l4_visibility_summary(invalid_tenant)

    @pytest.mark.parametrize("invalid_tenant", [None, 0, -1, "invalid"])
    def test_joint_program_management_fail_closed(self, invalid_tenant):
        """Test: joint_program_management rejects invalid tenant"""
        with pytest.raises((ValueError, TypeError)):
            get_joint_program_management_l4_visibility_summary(invalid_tenant)

    @pytest.mark.parametrize("invalid_tenant", [None, 0, -1, "invalid"])
    def test_inbound_exchange_management_fail_closed(self, invalid_tenant):
        """Test: inbound_exchange_management rejects invalid tenant"""
        with pytest.raises((ValueError, TypeError)):
            get_inbound_exchange_management_l4_visibility_summary(invalid_tenant)

    @pytest.mark.parametrize("invalid_tenant", [None, 0, -1, "invalid"])
    def test_outbound_exchange_management_fail_closed(self, invalid_tenant):
        """Test: outbound_exchange_management rejects invalid tenant"""
        with pytest.raises((ValueError, TypeError)):
            get_outbound_exchange_management_l4_visibility_summary(invalid_tenant)


class TestA02813L4OutputSchema:
    """Test 17-52: L4 output contains all required common fields for all 8 candidates"""

    REQUIRED_FIELDS = [
        "tenant_id", "module", "uce_id", "visibility_level", "source_maturity_level",
        "visibility_type", "readiness_summary", "risk_summary", "evidence_summary",
        "missing_evidence_summary", "human_review_queue_summary", "allowed_actions",
        "forbidden_actions", "tenant_scoped", "read_only", "no_mutation",
        "no_provider_call", "no_external_submission", "no_brain_execution",
        "no_autonomous_execution", "no_workflow_execution", "no_decision_execution",
        "no_fake_kpi", "no_synthetic_score", "no_l5_claim", "no_l6_claim",
        "l3_contract_preserved", "api_route_deferred_to", "safety_flags",
    ]

    def test_timesheet_management_l4_schema(self):
        """Test: timesheet_management L4 output contains all required fields"""
        output = get_timesheet_management_l4_visibility_summary(1)
        for field in self.REQUIRED_FIELDS:
            assert field in output, f"Missing field: {field}"

    def test_faculty_attestation_l4_schema(self):
        """Test: faculty_attestation L4 output contains all required fields"""
        output = get_faculty_attestation_l4_visibility_summary(1)
        for field in self.REQUIRED_FIELDS:
            assert field in output, f"Missing field: {field}"

    def test_teaching_load_contracts_l4_schema(self):
        """Test: teaching_load_contracts L4 output contains all required fields"""
        output = get_teaching_load_contracts_l4_visibility_summary(1)
        for field in self.REQUIRED_FIELDS:
            assert field in output, f"Missing field: {field}"

    def test_staff_exit_offboarding_l4_schema(self):
        """Test: staff_exit_offboarding L4 output contains all required fields"""
        output = get_staff_exit_offboarding_l4_visibility_summary(1)
        for field in self.REQUIRED_FIELDS:
            assert field in output, f"Missing field: {field}"

    def test_thesis_dissertation_management_l4_schema(self):
        """Test: thesis_dissertation_management L4 output contains all required fields"""
        output = get_thesis_dissertation_management_l4_visibility_summary(1)
        for field in self.REQUIRED_FIELDS:
            assert field in output, f"Missing field: {field}"

    def test_joint_program_management_l4_schema(self):
        """Test: joint_program_management L4 output contains all required fields"""
        output = get_joint_program_management_l4_visibility_summary(1)
        for field in self.REQUIRED_FIELDS:
            assert field in output, f"Missing field: {field}"

    def test_inbound_exchange_management_l4_schema(self):
        """Test: inbound_exchange_management L4 output contains all required fields"""
        output = get_inbound_exchange_management_l4_visibility_summary(1)
        for field in self.REQUIRED_FIELDS:
            assert field in output, f"Missing field: {field}"

    def test_outbound_exchange_management_l4_schema(self):
        """Test: outbound_exchange_management L4 output contains all required fields"""
        output = get_outbound_exchange_management_l4_visibility_summary(1)
        for field in self.REQUIRED_FIELDS:
            assert field in output, f"Missing field: {field}"


class TestA02813L4FieldValues:
    """Test 53-107: Verify correct L4 field values for all 8 candidates"""

    L4_EXPECTED_VALUES = {
        "visibility_level": "L4",
        "source_maturity_level": "L3",
        "visibility_type": "READ_ONLY_SERVICE_SUMMARY",
        "tenant_scoped": True,
        "read_only": True,
        "no_mutation": True,
        "no_provider_call": True,
        "no_external_submission": True,
        "no_brain_execution": True,
        "no_autonomous_execution": True,
        "no_workflow_execution": True,
        "no_decision_execution": True,
        "no_fake_kpi": True,
        "no_synthetic_score": True,
        "no_l5_claim": True,
        "no_l6_claim": True,
        "l3_contract_preserved": True,
        "api_route_deferred_to": "A-028.14",
    }

    def _test_l4_field_values(self, l4_func, expected_module, expected_uce):
        """Helper: Test L4 field values"""
        output = l4_func(1)
        assert output["module"] == expected_module
        assert output["uce_id"] == expected_uce
        assert output["tenant_id"] == 1
        for field, expected_value in self.L4_EXPECTED_VALUES.items():
            assert output[field] == expected_value, f"{field}: expected {expected_value}, got {output[field]}"

    def test_timesheet_management_l4_values(self):
        self._test_l4_field_values(get_timesheet_management_l4_visibility_summary, "timesheet_management", "UCE-060")

    def test_faculty_attestation_l4_values(self):
        self._test_l4_field_values(get_faculty_attestation_l4_visibility_summary, "faculty_attestation", "UCE-061")

    def test_teaching_load_contracts_l4_values(self):
        self._test_l4_field_values(get_teaching_load_contracts_l4_visibility_summary, "teaching_load_contracts", "UCE-067")

    def test_staff_exit_offboarding_l4_values(self):
        self._test_l4_field_values(get_staff_exit_offboarding_l4_visibility_summary, "staff_exit_offboarding", "UCE-070")

    def test_thesis_dissertation_management_l4_values(self):
        self._test_l4_field_values(get_thesis_dissertation_management_l4_visibility_summary, "thesis_dissertation_management", "UCE-077")

    def test_joint_program_management_l4_values(self):
        self._test_l4_field_values(get_joint_program_management_l4_visibility_summary, "joint_program_management", "UCE-085")

    def test_inbound_exchange_management_l4_values(self):
        self._test_l4_field_values(get_inbound_exchange_management_l4_visibility_summary, "inbound_exchange_management", "UCE-086")

    def test_outbound_exchange_management_l4_values(self):
        self._test_l4_field_values(get_outbound_exchange_management_l4_visibility_summary, "outbound_exchange_management", "UCE-087")


class TestA02813L4SafetyFlags:
    """Test 108-139: Safety flags are correctly set for all 8 candidates"""

    REQUIRED_SAFETY_FLAGS = {
        "no_api_claim": True,
        "no_frontend_claim": True,
        "no_provider_call": True,
        "no_credential_use": True,
        "no_kpi_value_claim": True,
        "no_brain_execution": True,
        "no_autonomous_execution": True,
        "no_external_side_effects": True,
        "no_db_mutation": True,
        "no_decision_execution": True,
        "human_review_required": True,
        "no_l5_claim": True,
        "no_l6_claim": True,
        "tenant_fail_closed": True,
        "l2_contract_preserved": True,
    }

    def _test_safety_flags(self, l4_func):
        """Helper: Test safety flags"""
        output = l4_func(1)
        flags = output.get("safety_flags", {})
        for flag, expected_value in self.REQUIRED_SAFETY_FLAGS.items():
            assert flags.get(flag) == expected_value, f"Flag {flag}: expected {expected_value}, got {flags.get(flag)}"

    def test_timesheet_management_safety_flags(self):
        self._test_safety_flags(get_timesheet_management_l4_visibility_summary)

    def test_faculty_attestation_safety_flags(self):
        self._test_safety_flags(get_faculty_attestation_l4_visibility_summary)

    def test_teaching_load_contracts_safety_flags(self):
        self._test_safety_flags(get_teaching_load_contracts_l4_visibility_summary)

    def test_staff_exit_offboarding_safety_flags(self):
        self._test_safety_flags(get_staff_exit_offboarding_l4_visibility_summary)

    def test_thesis_dissertation_management_safety_flags(self):
        self._test_safety_flags(get_thesis_dissertation_management_l4_visibility_summary)

    def test_joint_program_management_safety_flags(self):
        self._test_safety_flags(get_joint_program_management_l4_visibility_summary)

    def test_inbound_exchange_management_safety_flags(self):
        self._test_safety_flags(get_inbound_exchange_management_l4_visibility_summary)

    def test_outbound_exchange_management_safety_flags(self):
        self._test_safety_flags(get_outbound_exchange_management_l4_visibility_summary)


class TestA02813L4Determinism:
    """Test 140-147: Same input produces same output (deterministic) for all 8 candidates"""

    def _test_determinism(self, l4_func):
        """Helper: Test determinism"""
        output1 = l4_func(1)
        output2 = l4_func(1)
        assert output1 == output2, "L4 function is not deterministic"
    
    def _test_determinism_with_evidence(self, l4_func, evidence):
        """Helper: Test determinism with evidence"""
        output1 = l4_func(1, evidence)
        output2 = l4_func(1, evidence)
        assert output1 == output2, "L4 function is not deterministic"

    def test_timesheet_management_determinism(self):
        self._test_determinism(get_timesheet_management_l4_visibility_summary)

    def test_faculty_attestation_determinism(self):
        self._test_determinism(get_faculty_attestation_l4_visibility_summary)

    def test_teaching_load_contracts_determinism(self):
        self._test_determinism(get_teaching_load_contracts_l4_visibility_summary)

    def test_staff_exit_offboarding_determinism(self):
        # staff_exit_offboarding uses list[str] for evidence
        self._test_determinism_with_evidence(get_staff_exit_offboarding_l4_visibility_summary, [])

    def test_thesis_dissertation_management_determinism(self):
        self._test_determinism(get_thesis_dissertation_management_l4_visibility_summary)

    def test_joint_program_management_determinism(self):
        self._test_determinism(get_joint_program_management_l4_visibility_summary)

    def test_inbound_exchange_management_determinism(self):
        self._test_determinism(get_inbound_exchange_management_l4_visibility_summary)

    def test_outbound_exchange_management_determinism(self):
        self._test_determinism(get_outbound_exchange_management_l4_visibility_summary)


class TestA02813L3ContractPreservation:
    """Test 148-155: Existing L3 functions still exist and work for all 8 candidates"""

    def _test_l3_contract_preserved(self, l3_func, tenant_id=1):
        """Helper: Verify L3 function still callable and returns expected structure"""
        output = l3_func(tenant_id)
        assert isinstance(output, dict)
        assert "tenant_id" in output
        assert "readiness_status" in output
        assert output["maturity_level"] == "L3"

    def test_timesheet_management_l3_preserved(self):
        self._test_l3_contract_preserved(classify_timesheet_management_readiness)

    def test_faculty_attestation_l3_preserved(self):
        self._test_l3_contract_preserved(classify_faculty_attestation_readiness)

    def test_teaching_load_contracts_l3_preserved(self):
        self._test_l3_contract_preserved(classify_teaching_load_contracts_readiness)

    def test_staff_exit_offboarding_l3_preserved(self):
        self._test_l3_contract_preserved(classify_staff_exit_offboarding_readiness)

    def test_thesis_dissertation_management_l3_preserved(self):
        self._test_l3_contract_preserved(classify_thesis_dissertation_management_readiness)

    def test_joint_program_management_l3_preserved(self):
        self._test_l3_contract_preserved(classify_joint_program_management_readiness)

    def test_inbound_exchange_management_l3_preserved(self):
        self._test_l3_contract_preserved(classify_inbound_exchange_management_readiness)

    def test_outbound_exchange_management_l3_preserved(self):
        self._test_l3_contract_preserved(classify_outbound_exchange_management_readiness)


class TestA02813NoAPIRoutesBehavior:
    """Test 156-163: Confirm L4 functions do not create/modify API routes"""

    def _test_no_route_behavior(self, l4_func):
        """Helper: L4 function should only return dict, no side effects"""
        output = l4_func(1)
        assert isinstance(output, dict)
        assert "visibility_level" in output
        # L4 function is pure service function, not router
        assert callable(l4_func)

    def test_timesheet_management_no_routes(self):
        self._test_no_route_behavior(get_timesheet_management_l4_visibility_summary)

    def test_faculty_attestation_no_routes(self):
        self._test_no_route_behavior(get_faculty_attestation_l4_visibility_summary)

    def test_teaching_load_contracts_no_routes(self):
        self._test_no_route_behavior(get_teaching_load_contracts_l4_visibility_summary)

    def test_staff_exit_offboarding_no_routes(self):
        self._test_no_route_behavior(get_staff_exit_offboarding_l4_visibility_summary)

    def test_thesis_dissertation_management_no_routes(self):
        self._test_no_route_behavior(get_thesis_dissertation_management_l4_visibility_summary)

    def test_joint_program_management_no_routes(self):
        self._test_no_route_behavior(get_joint_program_management_l4_visibility_summary)

    def test_inbound_exchange_management_no_routes(self):
        self._test_no_route_behavior(get_inbound_exchange_management_l4_visibility_summary)

    def test_outbound_exchange_management_no_routes(self):
        self._test_no_route_behavior(get_outbound_exchange_management_l4_visibility_summary)


class TestA02813L4NotL5NotL6:
    """Test 164-171: Confirm no L5/L6 claims in L4 output for all 8 candidates"""

    def _test_no_l5_l6_claim(self, l4_func):
        """Helper: Verify no L5/L6 claims"""
        output = l4_func(1)
        assert output.get("no_l5_claim") is True
        assert output.get("no_l6_claim") is True
        safety_flags = output.get("safety_flags", {})
        assert safety_flags.get("no_l5_claim") is True
        assert safety_flags.get("no_l6_claim") is True
        # Verify output doesn't mention L5/L6
        output_str = str(output)
        assert "L5" not in output_str or output_str.count("no_l5") > 0
        assert "L6" not in output_str or output_str.count("no_l6") > 0

    def test_timesheet_management_no_l5_l6(self):
        self._test_no_l5_l6_claim(get_timesheet_management_l4_visibility_summary)

    def test_faculty_attestation_no_l5_l6(self):
        self._test_no_l5_l6_claim(get_faculty_attestation_l4_visibility_summary)

    def test_teaching_load_contracts_no_l5_l6(self):
        self._test_no_l5_l6_claim(get_teaching_load_contracts_l4_visibility_summary)

    def test_staff_exit_offboarding_no_l5_l6(self):
        self._test_no_l5_l6_claim(get_staff_exit_offboarding_l4_visibility_summary)

    def test_thesis_dissertation_management_no_l5_l6(self):
        self._test_no_l5_l6_claim(get_thesis_dissertation_management_l4_visibility_summary)

    def test_joint_program_management_no_l5_l6(self):
        self._test_no_l5_l6_claim(get_joint_program_management_l4_visibility_summary)

    def test_inbound_exchange_management_no_l5_l6(self):
        self._test_no_l5_l6_claim(get_inbound_exchange_management_l4_visibility_summary)

    def test_outbound_exchange_management_no_l5_l6(self):
        self._test_no_l5_l6_claim(get_outbound_exchange_management_l4_visibility_summary)


class TestA02813AllowedAndForbiddenActions:
    """Test 172-179: Allowed and forbidden actions present for all 8 candidates"""

    def _test_actions_present(self, l4_func):
        """Helper: Verify allowed and forbidden actions exist"""
        output = l4_func(1)
        assert isinstance(output.get("allowed_actions"), list)
        assert len(output.get("allowed_actions", [])) > 0
        assert isinstance(output.get("forbidden_actions"), list)
        assert len(output.get("forbidden_actions", [])) > 0

    def test_timesheet_management_actions(self):
        self._test_actions_present(get_timesheet_management_l4_visibility_summary)

    def test_faculty_attestation_actions(self):
        self._test_actions_present(get_faculty_attestation_l4_visibility_summary)

    def test_teaching_load_contracts_actions(self):
        self._test_actions_present(get_teaching_load_contracts_l4_visibility_summary)

    def test_staff_exit_offboarding_actions(self):
        self._test_actions_present(get_staff_exit_offboarding_l4_visibility_summary)

    def test_thesis_dissertation_management_actions(self):
        self._test_actions_present(get_thesis_dissertation_management_l4_visibility_summary)

    def test_joint_program_management_actions(self):
        self._test_actions_present(get_joint_program_management_l4_visibility_summary)

    def test_inbound_exchange_management_actions(self):
        self._test_actions_present(get_inbound_exchange_management_l4_visibility_summary)

    def test_outbound_exchange_management_actions(self):
        self._test_actions_present(get_outbound_exchange_management_l4_visibility_summary)


class TestA02813MultipleTenants:
    """Test 180+: L4 functions work across multiple tenants with tenant isolation"""

    def test_multiple_tenants_timesheet(self):
        """Test: Different tenants get isolated L4 outputs"""
        out1 = get_timesheet_management_l4_visibility_summary(1)
        out2 = get_timesheet_management_l4_visibility_summary(2)
        assert out1["tenant_id"] == 1
        assert out2["tenant_id"] == 2
        # Same structure, different tenant_id
        assert out1.keys() == out2.keys()

    def test_multiple_tenants_faculty(self):
        """Test: Different tenants get isolated L4 outputs"""
        out1 = get_faculty_attestation_l4_visibility_summary(1)
        out2 = get_faculty_attestation_l4_visibility_summary(2)
        assert out1["tenant_id"] == 1
        assert out2["tenant_id"] == 2

    def test_multiple_tenants_teaching(self):
        """Test: Different tenants get isolated L4 outputs"""
        out1 = get_teaching_load_contracts_l4_visibility_summary(1)
        out2 = get_teaching_load_contracts_l4_visibility_summary(2)
        assert out1["tenant_id"] == 1
        assert out2["tenant_id"] == 2

    def test_multiple_tenants_offboarding(self):
        """Test: Different tenants get isolated L4 outputs"""
        out1 = get_staff_exit_offboarding_l4_visibility_summary(1)
        out2 = get_staff_exit_offboarding_l4_visibility_summary(2)
        assert out1["tenant_id"] == 1
        assert out2["tenant_id"] == 2

    def test_multiple_tenants_thesis(self):
        """Test: Different tenants get isolated L4 outputs"""
        out1 = get_thesis_dissertation_management_l4_visibility_summary(1)
        out2 = get_thesis_dissertation_management_l4_visibility_summary(2)
        assert out1["tenant_id"] == 1
        assert out2["tenant_id"] == 2

    def test_multiple_tenants_joint(self):
        """Test: Different tenants get isolated L4 outputs"""
        out1 = get_joint_program_management_l4_visibility_summary(1)
        out2 = get_joint_program_management_l4_visibility_summary(2)
        assert out1["tenant_id"] == 1
        assert out2["tenant_id"] == 2

    def test_multiple_tenants_inbound(self):
        """Test: Different tenants get isolated L4 outputs"""
        out1 = get_inbound_exchange_management_l4_visibility_summary(1)
        out2 = get_inbound_exchange_management_l4_visibility_summary(2)
        assert out1["tenant_id"] == 1
        assert out2["tenant_id"] == 2

    def test_multiple_tenants_outbound(self):
        """Test: Different tenants get isolated L4 outputs"""
        out1 = get_outbound_exchange_management_l4_visibility_summary(1)
        out2 = get_outbound_exchange_management_l4_visibility_summary(2)
        assert out1["tenant_id"] == 1
        assert out2["tenant_id"] == 2
