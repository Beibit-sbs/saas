"""Test suite for A-027.3 new module foundation batch 2 (12 modules, L2 foundation contracts)."""

import pytest
from app.modules.competency_framework.service import get_competency_framework_foundation_contract
from app.modules.archive_retention_management.service import get_archive_retention_management_foundation_contract
from app.modules.leave_management.service import get_leave_management_foundation_contract
from app.modules.performance_appraisal.service import get_performance_appraisal_foundation_contract
from app.modules.disciplinary_case_management.service import get_disciplinary_case_management_foundation_contract
from app.modules.degree_audit.service import get_degree_audit_foundation_contract
from app.modules.transfer_credit_management.service import get_transfer_credit_management_foundation_contract
from app.modules.prerequisite_management.service import get_prerequisite_management_foundation_contract
from app.modules.course_catalog_management.service import get_course_catalog_management_foundation_contract
from app.modules.mou_lifecycle.service import get_mou_lifecycle_foundation_contract
from app.modules.partnership_registry.service import get_partnership_registry_foundation_contract
from app.modules.staff_exit_offboarding.service import get_staff_exit_offboarding_foundation_contract


# Test functions mapped to modules
MODULE_CONTRACTS = [
    ("competency_framework", get_competency_framework_foundation_contract),
    ("archive_retention_management", get_archive_retention_management_foundation_contract),
    ("leave_management", get_leave_management_foundation_contract),
    ("performance_appraisal", get_performance_appraisal_foundation_contract),
    ("disciplinary_case_management", get_disciplinary_case_management_foundation_contract),
    ("degree_audit", get_degree_audit_foundation_contract),
    ("transfer_credit_management", get_transfer_credit_management_foundation_contract),
    ("prerequisite_management", get_prerequisite_management_foundation_contract),
    ("course_catalog_management", get_course_catalog_management_foundation_contract),
    ("mou_lifecycle", get_mou_lifecycle_foundation_contract),
    ("partnership_registry", get_partnership_registry_foundation_contract),
    ("staff_exit_offboarding", get_staff_exit_offboarding_foundation_contract),
]

UCE_IDS = {
    "competency_framework": "UCE-016",
    "archive_retention_management": "UCE-012",
    "leave_management": "UCE-004",
    "performance_appraisal": "UCE-005",
    "disciplinary_case_management": "UCE-007",
    "degree_audit": "UCE-092",
    "transfer_credit_management": "UCE-075",
    "prerequisite_management": "UCE-074",
    "course_catalog_management": "UCE-076",
    "mou_lifecycle": "UCE-023",
    "partnership_registry": "UCE-022",
    "staff_exit_offboarding": "UCE-070",
}


class TestA0273FoundationImports:
    """Test 1: All modules can be imported successfully."""
    
    def test_all_imports_successful(self):
        """Verify all 12 modules import without errors."""
        assert len(MODULE_CONTRACTS) == 12, "Expected 12 modules"
        for name, func in MODULE_CONTRACTS:
            assert callable(func), f"{name} contract function not callable"


class TestA0273FailClosedValidation:
    """Tests 2-13: Fail-closed tenant validation (12 tests, one per module)."""
    
    @pytest.mark.parametrize("module_name,contract_func", MODULE_CONTRACTS)
    def test_tenant_fail_closed_none(self, module_name: str, contract_func):
        """Tenant ID None should raise ValueError."""
        with pytest.raises(ValueError, match="invalid_tenant_id"):
            contract_func(None)
    
    @pytest.mark.parametrize("module_name,contract_func", MODULE_CONTRACTS)
    def test_tenant_fail_closed_zero(self, module_name: str, contract_func):
        """Tenant ID 0 should raise ValueError."""
        with pytest.raises(ValueError, match="invalid_tenant_id"):
            contract_func(0)
    
    @pytest.mark.parametrize("module_name,contract_func", MODULE_CONTRACTS)
    def test_tenant_fail_closed_negative(self, module_name: str, contract_func):
        """Tenant ID negative should raise ValueError."""
        with pytest.raises(ValueError, match="invalid_tenant_id"):
            contract_func(-1)


class TestA0273OutputStructure:
    """Tests 14-25: Contract output structure validation (12 tests, one per module)."""
    
    @pytest.mark.parametrize("module_name,contract_func", MODULE_CONTRACTS)
    def test_contract_returns_dict(self, module_name: str, contract_func):
        """Contract function should return a dict."""
        result = contract_func(1)
        assert isinstance(result, dict), f"{module_name} returned {type(result)}"
    
    @pytest.mark.parametrize("module_name,contract_func", MODULE_CONTRACTS)
    def test_required_keys_present(self, module_name: str, contract_func):
        """Contract must contain all required keys."""
        result = contract_func(1)
        required_keys = {
            "tenant_id", "module", "uce_id", "maturity_level", "expansion_layer",
            "service_contract_ready", "tenant_scoped", "deterministic",
            "lifecycle_statuses", "allowed_actions", "forbidden_actions",
            "required_evidence", "next_maturity_gap", "safety_flags"
        }
        actual_keys = set(result.keys())
        missing = required_keys - actual_keys
        assert not missing, f"{module_name} missing keys: {missing}"


class TestA0273LifecycleValidation:
    """Tests 26-37: Lifecycle status lists validation (12 tests, one per module)."""
    
    @pytest.mark.parametrize("module_name,contract_func", MODULE_CONTRACTS)
    def test_lifecycle_is_list(self, module_name: str, contract_func):
        """Lifecycle statuses must be a list."""
        result = contract_func(1)
        assert isinstance(result["lifecycle_statuses"], list), f"{module_name} lifecycle not list"
    
    @pytest.mark.parametrize("module_name,contract_func", MODULE_CONTRACTS)
    def test_lifecycle_not_empty(self, module_name: str, contract_func):
        """Lifecycle statuses must not be empty."""
        result = contract_func(1)
        assert len(result["lifecycle_statuses"]) > 0, f"{module_name} lifecycle empty"
    
    @pytest.mark.parametrize("module_name,contract_func", MODULE_CONTRACTS)
    def test_lifecycle_all_strings(self, module_name: str, contract_func):
        """All lifecycle statuses must be strings."""
        result = contract_func(1)
        for status in result["lifecycle_statuses"]:
            assert isinstance(status, str), f"{module_name} lifecycle contains non-string: {status}"


class TestA0273ForbiddenActionsValidation:
    """Tests 38-49: Forbidden actions validation (12 tests, one per module)."""
    
    @pytest.mark.parametrize("module_name,contract_func", MODULE_CONTRACTS)
    def test_forbidden_is_list(self, module_name: str, contract_func):
        """Forbidden actions must be a list."""
        result = contract_func(1)
        assert isinstance(result["forbidden_actions"], list), f"{module_name} forbidden not list"
    
    @pytest.mark.parametrize("module_name,contract_func", MODULE_CONTRACTS)
    def test_forbidden_not_empty(self, module_name: str, contract_func):
        """Forbidden actions must not be empty."""
        result = contract_func(1)
        assert len(result["forbidden_actions"]) > 0, f"{module_name} forbidden empty"
    
    @pytest.mark.parametrize("module_name,contract_func", MODULE_CONTRACTS)
    def test_forbidden_all_strings(self, module_name: str, contract_func):
        """All forbidden actions must be strings."""
        result = contract_func(1)
        for action in result["forbidden_actions"]:
            assert isinstance(action, str), f"{module_name} forbidden contains non-string: {action}"


class TestA0273SafetyFlagsValidation:
    """Tests 50-61: Safety flags validation (12 tests, one per module)."""
    
    @pytest.mark.parametrize("module_name,contract_func", MODULE_CONTRACTS)
    def test_safety_flags_is_dict(self, module_name: str, contract_func):
        """Safety flags must be a dict."""
        result = contract_func(1)
        assert isinstance(result["safety_flags"], dict), f"{module_name} safety_flags not dict"
    
    @pytest.mark.parametrize("module_name,contract_func", MODULE_CONTRACTS)
    def test_all_safety_flags_present(self, module_name: str, contract_func):
        """All 12 safety flags must be present."""
        result = contract_func(1)
        required_flags = {
            "no_api_claim", "no_frontend_claim", "no_live_integration_claim",
            "no_provider_call", "no_kpi_claim", "no_brain_claim",
            "no_autonomous_execution", "no_external_side_effects",
            "no_l3_claim", "no_l4_claim", "no_l5_claim", "no_l6_claim"
        }
        actual_flags = set(result["safety_flags"].keys())
        missing = required_flags - actual_flags
        assert not missing, f"{module_name} missing flags: {missing}"
    
    @pytest.mark.parametrize("module_name,contract_func", MODULE_CONTRACTS)
    def test_all_safety_flags_true(self, module_name: str, contract_func):
        """All safety flags must be True (anti-inflation enforcement)."""
        result = contract_func(1)
        for flag_name, flag_value in result["safety_flags"].items():
            assert flag_value is True, f"{module_name} {flag_name} = {flag_value}, expected True"


class TestA0273Determinism:
    """Tests 62-73: Determinism validation (12 tests, one per module)."""
    
    @pytest.mark.parametrize("module_name,contract_func", MODULE_CONTRACTS)
    def test_same_tenant_same_contract(self, module_name: str, contract_func):
        """Same tenant should return identical contract on multiple calls."""
        result1 = contract_func(1)
        result2 = contract_func(1)
        assert result1 == result2, f"{module_name} returned different contracts for same tenant"
    
    @pytest.mark.parametrize("module_name,contract_func", MODULE_CONTRACTS)
    def test_deterministic_flag_true(self, module_name: str, contract_func):
        """Deterministic flag must be True."""
        result = contract_func(1)
        assert result["deterministic"] is True, f"{module_name} deterministic flag is False"


class TestA0273AntiInflationVerification:
    """Tests 74-78: Anti-inflation enforcement (5 tests covering cross-module validation)."""
    
    def test_no_autonomy_across_batch(self):
        """No module should claim autonomous execution."""
        for module_name, contract_func in MODULE_CONTRACTS:
            result = contract_func(1)
            assert result["safety_flags"]["no_autonomous_execution"] is True, \
                f"{module_name} claims autonomous_execution"
    
    def test_no_l3_logic_claims(self):
        """No module should claim L3 logic."""
        for module_name, contract_func in MODULE_CONTRACTS:
            result = contract_func(1)
            assert result["safety_flags"]["no_l3_claim"] is True, \
                f"{module_name} claims L3 logic"
    
    def test_no_higher_maturity_claims(self):
        """No module should claim L4, L5, or L6 logic."""
        for module_name, contract_func in MODULE_CONTRACTS:
            result = contract_func(1)
            assert result["maturity_level"] == "L2", \
                f"{module_name} maturity_level is {result['maturity_level']}"
            assert result["safety_flags"]["no_l4_claim"] is True
            assert result["safety_flags"]["no_l5_claim"] is True
            assert result["safety_flags"]["no_l6_claim"] is True
    
    def test_expansion_layer_consistency(self):
        """All modules must have expansion_layer='university_completeness'."""
        for module_name, contract_func in MODULE_CONTRACTS:
            result = contract_func(1)
            assert result["expansion_layer"] == "university_completeness", \
                f"{module_name} expansion_layer is {result['expansion_layer']}"
    
    def test_no_provider_calls_across_batch(self):
        """All modules must have no_provider_call=True."""
        for module_name, contract_func in MODULE_CONTRACTS:
            result = contract_func(1)
            assert result["safety_flags"]["no_provider_call"] is True, \
                f"{module_name} allows provider calls"


class TestA0273ModuleIntegrity:
    """Tests 79-82: Module integrity and UCE mappings (4 tests)."""
    
    def test_all_modules_present(self):
        """Verify all 12 selected modules are implemented."""
        module_names = {name for name, _ in MODULE_CONTRACTS}
        expected = {
            "competency_framework", "archive_retention_management",
            "leave_management", "performance_appraisal",
            "disciplinary_case_management", "degree_audit",
            "transfer_credit_management", "prerequisite_management",
            "course_catalog_management", "mou_lifecycle",
            "partnership_registry", "staff_exit_offboarding"
        }
        assert module_names == expected, f"Module mismatch: {module_names} vs {expected}"
    
    def test_uce_ids_correct(self):
        """Verify all UCE IDs match expected mappings."""
        for module_name, contract_func in MODULE_CONTRACTS:
            result = contract_func(1)
            expected_uce = UCE_IDS[module_name]
            assert result["uce_id"] == expected_uce, \
                f"{module_name} has UCE {result['uce_id']}, expected {expected_uce}"
    
    def test_module_names_in_contract(self):
        """Verify contract module field matches function module."""
        for module_name, contract_func in MODULE_CONTRACTS:
            result = contract_func(1)
            assert result["module"] == module_name, \
                f"Module {module_name} contract has module={result['module']}"
    
    def test_contract_status_ready(self):
        """Verify contract_status is FOUNDATION_READY."""
        for module_name, contract_func in MODULE_CONTRACTS:
            result = contract_func(1)
            assert result["contract_status"] == "FOUNDATION_READY", \
                f"{module_name} contract_status is {result['contract_status']}"


class TestA0273TenantIsolation:
    """Tests 83-85: Tenant data isolation (3 tests)."""
    
    def test_different_tenants_different_contracts(self):
        """Different tenants should return separate contract objects."""
        module_name, contract_func = MODULE_CONTRACTS[0]
        result1 = contract_func(1)
        result2 = contract_func(2)
        assert result1["tenant_id"] == 1
        assert result2["tenant_id"] == 2
        assert result1 is not result2
    
    def test_tenant_id_preserved_in_contract(self):
        """Tenant ID passed should be preserved in contract."""
        for tenant_id in [1, 42, 999]:
            for module_name, contract_func in MODULE_CONTRACTS:
                result = contract_func(tenant_id)
                assert result["tenant_id"] == tenant_id, \
                    f"{module_name} tenant_id mismatch: {result['tenant_id']} vs {tenant_id}"
    
    def test_no_cross_tenant_data_leakage(self):
        """Verify no data from other tenants in contract."""
        contract1 = MODULE_CONTRACTS[0][1](1)
        contract2 = MODULE_CONTRACTS[0][1](2)
        # Only tenant_id should differ, contract structure identical
        assert contract1.keys() == contract2.keys()
        for key in contract1.keys():
            if key != "tenant_id":
                assert contract1[key] == contract2[key], \
                    f"Cross-tenant leak in {key}: {contract1[key]} vs {contract2[key]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
