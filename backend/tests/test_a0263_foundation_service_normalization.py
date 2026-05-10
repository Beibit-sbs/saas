"""
A-026.3 Foundation Service Normalization Batch Test Suite

Tests for 8 modules achieving L2 contract readiness:
1. human_approved_timetable_workflow
2. timetable_change_proposal
3. timetable_change_simulation
4. timetable_recommendation_bridge
5. timetable_approval_queue
6. timetable_change_kpi_dashboard
7. workload_management
8. notification_center

Test coverage:
- Import validation
- Tenant validation (fail-closed)
- Contract output validation
- Module-specific constants
- Anti-inflation validation
- Determinism tests
"""

import pytest
from typing import Any

# Import all 8 modules
from app.modules.human_approved_timetable_workflow import service as human_workflow_service
from app.modules.timetable_change_proposal import service as proposal_service
from app.modules.timetable_change_simulation import service as simulation_service
from app.modules.timetable_recommendation_bridge import service as bridge_service
from app.modules.timetable_approval_queue import service as approval_queue_service
from app.modules.timetable_change_kpi_dashboard import service as kpi_dashboard_service
from app.modules.workload_management import service as workload_service
from app.modules.notification_center import service as notification_service


# ============================================================================
# Test Group 1: Import Validation
# ============================================================================

class TestImportValidation:
    """Verify all 8 modules import successfully."""

    def test_a0263_all_modules_import(self):
        """Test that all 8 module services import without error."""
        assert human_workflow_service is not None
        assert proposal_service is not None
        assert simulation_service is not None
        assert bridge_service is not None
        assert approval_queue_service is not None
        assert kpi_dashboard_service is not None
        assert workload_service is not None
        assert notification_service is not None

    def test_a0263_required_functions_callable(self):
        """Test that all required functions are callable."""
        # Workflow
        assert callable(human_workflow_service.validate_workflow_tenant)
        assert callable(human_workflow_service.get_workflow_status_contract)

        # Proposal
        assert callable(proposal_service.validate_proposal_tenant)
        assert callable(proposal_service.validate_proposal_payload)

        # Simulation
        assert callable(simulation_service.validate_simulation_tenant)
        assert callable(simulation_service.get_simulation_readiness_response)

        # Bridge
        assert callable(bridge_service.validate_bridge_tenant)
        assert callable(bridge_service.create_recommendation_envelope)

        # Queue
        assert callable(approval_queue_service.validate_queue_tenant)
        assert callable(approval_queue_service.enqueue_for_review)

        # KPI Dashboard
        assert callable(kpi_dashboard_service.validate_kpi_dashboard_tenant)
        assert callable(kpi_dashboard_service.get_kpi_readiness_contract)

        # Workload
        assert callable(workload_service.validate_workload_tenant)
        assert callable(workload_service.get_workload_readiness_contract)

        # Notification
        assert callable(notification_service.validate_notification_tenant)
        assert callable(notification_service.build_notification_contract)


# ============================================================================
# Test Group 2: Tenant Validation (Fail-Closed - CRITICAL)
# ============================================================================

class TestTenantValidation:
    """Verify all modules fail-closed on invalid tenant_id."""

    def test_workflow_tenant_validation_fail_closed(self):
        """Test human_approved_timetable_workflow tenant validation."""
        assert human_workflow_service.validate_workflow_tenant(None) is False
        assert human_workflow_service.validate_workflow_tenant(0) is False
        assert human_workflow_service.validate_workflow_tenant(-1) is False
        assert human_workflow_service.validate_workflow_tenant("invalid") is False
        assert human_workflow_service.validate_workflow_tenant(1) is True

    def test_proposal_tenant_validation_fail_closed(self):
        """Test timetable_change_proposal tenant validation."""
        assert proposal_service.validate_proposal_tenant(None) is False
        assert proposal_service.validate_proposal_tenant(0) is False
        assert proposal_service.validate_proposal_tenant(-1) is False
        assert proposal_service.validate_proposal_tenant(1) is True

    def test_simulation_tenant_validation_fail_closed(self):
        """Test timetable_change_simulation tenant validation."""
        assert simulation_service.validate_simulation_tenant(None) is False
        assert simulation_service.validate_simulation_tenant(0) is False
        assert simulation_service.validate_simulation_tenant(-1) is False
        assert simulation_service.validate_simulation_tenant(1) is True

    def test_bridge_tenant_validation_fail_closed(self):
        """Test timetable_recommendation_bridge tenant validation."""
        assert bridge_service.validate_bridge_tenant(None) is False
        assert bridge_service.validate_bridge_tenant(0) is False
        assert bridge_service.validate_bridge_tenant(-1) is False
        assert bridge_service.validate_bridge_tenant(1) is True

    def test_queue_tenant_validation_fail_closed(self):
        """Test timetable_approval_queue tenant validation."""
        assert approval_queue_service.validate_queue_tenant(None) is False
        assert approval_queue_service.validate_queue_tenant(0) is False
        assert approval_queue_service.validate_queue_tenant(-1) is False
        assert approval_queue_service.validate_queue_tenant(1) is True

    def test_kpi_tenant_validation_fail_closed(self):
        """Test timetable_change_kpi_dashboard tenant validation."""
        assert kpi_dashboard_service.validate_kpi_dashboard_tenant(None) is False
        assert kpi_dashboard_service.validate_kpi_dashboard_tenant(0) is False
        assert kpi_dashboard_service.validate_kpi_dashboard_tenant(-1) is False
        assert kpi_dashboard_service.validate_kpi_dashboard_tenant(1) is True

    def test_workload_tenant_validation_fail_closed(self):
        """Test workload_management tenant validation."""
        assert workload_service.validate_workload_tenant(None) is False
        assert workload_service.validate_workload_tenant(0) is False
        assert workload_service.validate_workload_tenant(-1) is False
        assert workload_service.validate_workload_tenant(1) is True

    def test_notification_tenant_validation_fail_closed_critical(self):
        """Test notification_center tenant validation (CRITICAL)."""
        # Most critical: notification must fail-closed absolutely
        assert notification_service.validate_notification_tenant(None) is False
        assert notification_service.validate_notification_tenant(0) is False
        assert notification_service.validate_notification_tenant(-1) is False
        assert notification_service.validate_notification_tenant("invalid") is False
        assert notification_service.validate_notification_tenant(1) is True


# ============================================================================
# Test Group 3: Contract Output Validation
# ============================================================================

class TestContractOutput:
    """Verify all modules return deterministic contract outputs."""

    def test_workflow_contract_output(self):
        """Test workflow contract has required fields."""
        contract = human_workflow_service.get_workflow_status_contract(1)
        assert "tenant_id" in contract
        assert contract["tenant_id"] == 1
        assert "module" in contract
        assert "readiness_status" in contract
        assert "target_level" in contract
        assert contract["target_level"] == "L2"

    def test_proposal_contract_output(self):
        """Test proposal contract has required fields."""
        contract = proposal_service.get_proposal_readiness_contract(1)
        assert "tenant_id" in contract
        assert contract["tenant_id"] == 1
        assert "module" in contract
        assert "readiness_status" in contract
        assert "target_level" in contract

    def test_simulation_contract_output(self):
        """Test simulation contract has required fields."""
        contract = simulation_service.get_simulation_readiness_response(1)
        assert "tenant_id" in contract
        assert contract["tenant_id"] == 1
        assert "module" in contract
        assert "readiness_status" in contract

    def test_bridge_contract_output(self):
        """Test bridge contract has required fields."""
        contract = bridge_service.get_bridge_readiness_contract(1)
        assert "tenant_id" in contract
        assert contract["tenant_id"] == 1
        assert "module" in contract
        assert "readiness_status" in contract

    def test_queue_contract_output(self):
        """Test queue contract has required fields."""
        contract = approval_queue_service.get_queue_status_contract(1)
        assert "tenant_id" in contract
        assert contract["tenant_id"] == 1
        assert "module" in contract
        assert "readiness_status" in contract

    def test_kpi_contract_output(self):
        """Test KPI contract has required fields."""
        contract = kpi_dashboard_service.get_kpi_readiness_contract(1)
        assert "tenant_id" in contract
        assert contract["tenant_id"] == 1
        assert "module" in contract
        assert "readiness_status" in contract

    def test_workload_contract_output(self):
        """Test workload contract has required fields."""
        contract = workload_service.get_workload_readiness_contract(1)
        assert "tenant_id" in contract
        assert contract["tenant_id"] == 1
        assert "module" in contract
        assert "readiness_status" in contract

    def test_notification_contract_output(self):
        """Test notification contract has required fields (CRITICAL tenant_id)."""
        contract = notification_service.get_notification_readiness_contract(1)
        assert "tenant_id" in contract
        assert contract["tenant_id"] == 1
        assert contract["tenant_isolation"] is True


# ============================================================================
# Test Group 4: Module-Specific Constants
# ============================================================================

class TestModuleConstants:
    """Verify all modules have correct constants."""

    def test_workflow_status_constants_valid(self):
        """Test workflow status constants."""
        assert "DRAFT" in human_workflow_service.WORKFLOW_STATUS
        assert "PENDING_HUMAN_REVIEW" in human_workflow_service.WORKFLOW_STATUS
        assert "HUMAN_APPROVED" in human_workflow_service.WORKFLOW_STATUS
        assert human_workflow_service.HUMAN_APPROVAL_REQUIRED is True

    def test_proposal_status_constants_valid(self):
        """Test proposal status constants."""
        assert "SUBMITTED" in proposal_service.PROPOSAL_STATUS
        assert "UNDER_REVIEW" in proposal_service.PROPOSAL_STATUS
        assert "READY_FOR_SIMULATION" in proposal_service.PROPOSAL_STATUS

    def test_simulation_status_constants_valid(self):
        """Test simulation status constants."""
        assert "PENDING" in simulation_service.SIMULATION_STATUS
        assert "SIMULATED" in simulation_service.SIMULATION_STATUS
        assert len(simulation_service.FORBIDDEN_MUTATIONS) > 0

    def test_bridge_mode_constant_valid(self):
        """Test bridge mode constant."""
        assert simulation_service.BRIDGE_MODE == "DETERMINISTIC_ENVELOPE_ONLY"

    def test_queue_forbidden_actions_defined(self):
        """Test queue forbidden auto actions."""
        assert "AUTO_APPROVE" in approval_queue_service.FORBIDDEN_AUTO_ACTIONS
        assert "AUTO_APPLY" in approval_queue_service.FORBIDDEN_AUTO_ACTIONS

    def test_workload_status_constants_valid(self):
        """Test workload status constants."""
        assert "PLANNING" in workload_service.WORKLOAD_STATUS
        assert "READY_FOR_ASSIGNMENT" in workload_service.WORKLOAD_STATUS
        assert len(workload_service.FORBIDDEN_AUTO_ACTIONS) > 0

    def test_notification_types_constants_valid(self):
        """Test notification type constants."""
        assert "WORKFLOW_APPROVED" in notification_service.NOTIFICATION_TYPE
        assert "WORKLOAD_ASSIGNED" in notification_service.NOTIFICATION_TYPE
        assert notification_service.NO_SENDING is True
        assert notification_service.TENANT_ISOLATION_REQUIRED is True


# ============================================================================
# Test Group 5: Anti-Inflation Validation
# ============================================================================

class TestAntiInflation:
    """Verify no overclaims for API, frontend, KPI, Brain."""

    def test_workflow_anti_inflation(self):
        """Test workflow has anti-inflation flags."""
        assert human_workflow_service.SAFETY_FLAGS["no_api_claim"] is True
        assert human_workflow_service.SAFETY_FLAGS["no_frontend_claim"] is True
        assert human_workflow_service.SAFETY_FLAGS["no_brain_claim"] is True

    def test_proposal_anti_inflation(self):
        """Test proposal has anti-inflation flags."""
        assert proposal_service.SAFETY_FLAGS["no_api_claim"] is True
        assert proposal_service.SAFETY_FLAGS["no_frontend_claim"] is True

    def test_simulation_anti_inflation(self):
        """Test simulation has anti-inflation flags."""
        assert simulation_service.SAFETY_FLAGS["no_api_claim"] is True
        assert simulation_service.SAFETY_FLAGS["no_real_mutation"] is True

    def test_bridge_anti_inflation(self):
        """Test bridge has anti-inflation flags."""
        assert bridge_service.SAFETY_FLAGS["no_api_claim"] is True
        assert bridge_service.SAFETY_FLAGS["no_ai_provider_calls"] is True

    def test_queue_anti_inflation(self):
        """Test queue has anti-inflation flags."""
        assert approval_queue_service.SAFETY_FLAGS["no_automatic_decision"] is True

    def test_kpi_anti_inflation(self):
        """Test KPI dashboard has no frontend/Brain claims."""
        assert kpi_dashboard_service.SAFETY_FLAGS["no_frontend_claim"] is True
        assert kpi_dashboard_service.SAFETY_FLAGS["no_brain_claim"] is True

    def test_workload_anti_inflation(self):
        """Test workload has anti-inflation flags."""
        assert workload_service.SAFETY_FLAGS["no_payroll_mutation"] is True
        assert workload_service.SAFETY_FLAGS["no_automatic_assignment"] is True

    def test_notification_anti_inflation(self):
        """Test notification has anti-inflation flags."""
        assert notification_service.SAFETY_FLAGS["no_actual_sending"] is True
        assert notification_service.SAFETY_FLAGS["no_cross_tenant_broadcast"] is True


# ============================================================================
# Test Group 6: Determinism
# ============================================================================

class TestDeterminism:
    """Verify contract functions produce deterministic outputs."""

    def test_workflow_determinism(self):
        """Test workflow contract is deterministic."""
        result1 = human_workflow_service.get_workflow_status_contract(1)
        result2 = human_workflow_service.get_workflow_status_contract(1)
        assert result1 == result2

    def test_proposal_determinism(self):
        """Test proposal contract is deterministic."""
        result1 = proposal_service.get_proposal_readiness_contract(1)
        result2 = proposal_service.get_proposal_readiness_contract(1)
        assert result1 == result2

    def test_simulation_determinism(self):
        """Test simulation contract is deterministic."""
        result1 = simulation_service.get_simulation_readiness_response(1)
        result2 = simulation_service.get_simulation_readiness_response(1)
        assert result1 == result2

    def test_bridge_determinism(self):
        """Test bridge contract is deterministic."""
        result1 = bridge_service.get_bridge_readiness_contract(1)
        result2 = bridge_service.get_bridge_readiness_contract(1)
        assert result1 == result2

    def test_queue_determinism(self):
        """Test queue contract is deterministic."""
        result1 = approval_queue_service.get_queue_status_contract(1)
        result2 = approval_queue_service.get_queue_status_contract(1)
        assert result1 == result2

    def test_kpi_determinism(self):
        """Test KPI contract is deterministic."""
        result1 = kpi_dashboard_service.get_kpi_readiness_contract(1)
        result2 = kpi_dashboard_service.get_kpi_readiness_contract(1)
        assert result1 == result2

    def test_workload_determinism(self):
        """Test workload contract is deterministic."""
        result1 = workload_service.get_workload_readiness_contract(1)
        result2 = workload_service.get_workload_readiness_contract(1)
        assert result1 == result2

    def test_notification_determinism(self):
        """Test notification contract is deterministic."""
        result1 = notification_service.get_notification_readiness_contract(1)
        result2 = notification_service.get_notification_readiness_contract(1)
        assert result1 == result2
