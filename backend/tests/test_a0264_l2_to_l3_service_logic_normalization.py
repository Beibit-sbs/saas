"""
A-026.4 L2→L3 Service Logic Normalization Test Suite

Tests for 8 modules achieving L3 deterministic backend business logic:
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
- Tenant fail-closed validation
- Deterministic domain logic
- Classification/status outputs
- Forbidden action protection
- Anti-inflation validation
- A-026.3 compatibility continuity
"""

import json

import pytest

from app.modules.human_approved_timetable_workflow import service as human_workflow_service
from app.modules.timetable_change_proposal import service as proposal_service
from app.modules.timetable_change_simulation import service as simulation_service
from app.modules.timetable_recommendation_bridge import service as bridge_service
from app.modules.timetable_approval_queue import service as approval_queue_service
from app.modules.timetable_change_kpi_dashboard import service as kpi_dashboard_service
from app.modules.workload_management import service as workload_service
from app.modules.notification_center import service as notification_service


MODULES = [
    (
        "human_approved_timetable_workflow",
        human_workflow_service,
        human_workflow_service.evaluate_human_workflow_state,
        {"status": "DRAFT"},
        {"status": "HUMAN_APPROVED"},
    ),
    (
        "timetable_change_proposal",
        proposal_service,
        proposal_service.evaluate_timetable_change_proposal,
        {"proposal_type": "CHANGE"},
        {"proposal_type": "CHANGE", "description": "desc", "reason": "why", "impact": "low"},
    ),
    (
        "timetable_change_simulation",
        simulation_service,
        simulation_service.assess_simulation_readiness,
        {"proposal_id": 1},
        {"proposal_id": 1, "simulation_type": "what_if", "baseline_snapshot": {"courses": 1}},
    ),
    (
        "timetable_recommendation_bridge",
        bridge_service,
        bridge_service.evaluate_recommendation_bridge,
        {"proposal_id": 1},
        {"proposal_id": 1, "simulation_type": "what_if", "readiness_status": "READY_FOR_APPROVAL"},
    ),
    (
        "timetable_approval_queue",
        approval_queue_service,
        approval_queue_service.evaluate_queue_item,
        {},
        {"queue_status": "PENDING_REVIEW"},
    ),
    (
        "timetable_change_kpi_dashboard",
        kpi_dashboard_service,
        kpi_dashboard_service.classify_kpi_readiness,
        {},
        {"backend_contract_ready": True},
    ),
    (
        "workload_management",
        workload_service,
        workload_service.evaluate_workload_plan,
        {"workload_type": "TEACHING"},
        {"workload_type": "TEACHING", "units": 3},
    ),
    (
        "notification_center",
        notification_service,
        notification_service.classify_notification_readiness,
        {"notification_type": "UNKNOWN"},
        {"notification_type": "WORKFLOW_APPROVED", "subject": "s", "message": "m", "provider_configured": True},
    ),
]


def assert_serializable(result):
    json.dumps(result)
    assert isinstance(result, dict)


@pytest.mark.parametrize("module_name, service_module, l3_func, incomplete_input, valid_input", MODULES)
def test_imports_and_callable_l3_functions(module_name, service_module, l3_func, incomplete_input, valid_input):
    assert service_module is not None
    assert callable(l3_func)


@pytest.mark.parametrize("module_name, service_module, l3_func, incomplete_input, valid_input", MODULES)
def test_tenant_fail_closed(module_name, service_module, l3_func, incomplete_input, valid_input):
    for bad_tenant in [None, 0, -1]:
        result = l3_func(bad_tenant, valid_input)
        assert result["tenant_id"] is None
        assert result["maturity_level"] == "L3"
        assert result["safety_flags"]["target_level"] == "L3"
    result = l3_func(1, valid_input)
    assert result["tenant_id"] == 1


@pytest.mark.parametrize("module_name, service_module, l3_func, incomplete_input, valid_input", MODULES)
def test_deterministic_outputs(module_name, service_module, l3_func, incomplete_input, valid_input):
    result1 = l3_func(1, valid_input)
    result2 = l3_func(1, valid_input)
    assert result1 == result2
    assert_serializable(result1)


def test_human_workflow_classification_and_forbidden_actions():
    incomplete = human_workflow_service.evaluate_human_workflow_state(1, {"status": "DRAFT"})
    approved = human_workflow_service.evaluate_human_workflow_state(1, {"status": "HUMAN_APPROVED"})
    rejected = human_workflow_service.evaluate_human_workflow_state(1, {"status": "REJECTED"})
    cancelled = human_workflow_service.evaluate_human_workflow_state(1, {"status": "CANCELLED"})
    assert incomplete["classification"] == "NEEDS_HUMAN_REVIEW"
    assert approved["classification"] == "READY_FOR_MANUAL_APPROVAL"
    assert rejected["classification"] == "REJECTED_BY_POLICY"
    assert cancelled["classification"] == "CANCELLED_OR_CLOSED"
    assert "AUTO_APPLY" in approved["forbidden_actions"]
    assert approved["HUMAN_APPROVAL_REQUIRED"] is True


def test_proposal_classification_and_forbidden_actions():
    incomplete = proposal_service.evaluate_timetable_change_proposal(1, {"proposal_type": "CHANGE"})
    ready = proposal_service.evaluate_timetable_change_proposal(1, {"proposal_type": "CHANGE", "description": "d", "reason": "r", "impact": "i"})
    simulation = proposal_service.evaluate_timetable_change_proposal(1, {"proposal_type": "SIMULATION", "description": "d", "reason": "r", "impact": "i", "requires_simulation": True})
    policy = proposal_service.evaluate_timetable_change_proposal(1, {"proposal_type": "CHANGE", "description": "d", "reason": "r", "impact": "i", "policy_review_required": True})
    assert incomplete["classification"] == "INCOMPLETE_PROPOSAL"
    assert ready["classification"] == "READY_FOR_REVIEW"
    assert simulation["classification"] == "READY_FOR_SIMULATION"
    assert policy["classification"] == "POLICY_REVIEW_REQUIRED"
    assert "AUTO_APPLY" in ready["forbidden_actions"]


def test_simulation_classification_and_forbidden_actions():
    incomplete = simulation_service.assess_simulation_readiness(1, {"proposal_id": 1})
    ready = simulation_service.assess_simulation_readiness(1, {"proposal_id": 1, "simulation_type": "what_if", "baseline_snapshot": {"c": 1}})
    scope = simulation_service.assess_simulation_readiness(1, {"proposal_id": 1, "simulation_type": "what_if", "baseline_snapshot": {"c": 1}, "requires_human_scope_review": True})
    final = simulation_service.assess_simulation_readiness(1, {"proposal_id": 1, "simulation_type": "what_if", "baseline_snapshot": {"c": 1}, "simulation_result_ready": True})
    assert incomplete["classification"] == "NOT_READY"
    assert ready["classification"] == "READY_FOR_SIMULATION"
    assert scope["classification"] == "SIMULATION_REQUIRES_HUMAN_SCOPE_REVIEW"
    assert final["classification"] == "SIMULATION_RESULT_READY_FOR_APPROVAL"
    assert "APPLY_TIMETABLE" in ready["forbidden_mutations"]


def test_bridge_classification_and_forbidden_actions():
    incomplete = bridge_service.evaluate_recommendation_bridge(1, {"proposal_id": 1})
    ready = bridge_service.evaluate_recommendation_bridge(1, {"proposal_id": 1, "simulation_type": "what_if", "readiness_status": "READY_FOR_APPROVAL"})
    blocked = bridge_service.evaluate_recommendation_bridge(1, {"proposal_id": 1, "simulation_type": "what_if", "policy_review_required": True})
    assert incomplete["classification"] == "RECOMMENDATION_BLOCKED_BY_INCOMPLETE_SIMULATION"
    assert ready["classification"] == "RECOMMENDATION_READY_FOR_HUMAN_REVIEW"
    assert blocked["classification"] == "RECOMMENDATION_REQUIRES_POLICY_REVIEW"
    assert ready["BRIDGE_MODE"] == "DETERMINISTIC_ENVELOPE_ONLY"
    assert "AI_PROVIDER_CALL" in ready["forbidden_actions"]


def test_queue_classification_and_forbidden_actions():
    invalid = approval_queue_service.evaluate_queue_item(1, {})
    ready = approval_queue_service.evaluate_queue_item(1, {"queue_status": "PENDING_REVIEW"})
    progress = approval_queue_service.evaluate_queue_item(1, {"queue_status": "IN_PROGRESS"})
    manual = approval_queue_service.evaluate_queue_item(1, {"queue_status": "READY_FOR_MANUAL_DECISION"})
    blocked = approval_queue_service.evaluate_queue_item(1, {"queue_status": "BLOCKED_REQUIRES_MORE_INFO"})
    assert invalid["classification"] == "QUEUE_ITEM_INVALID"
    assert ready["classification"] == "READY_FOR_REVIEW"
    assert progress["classification"] == "REVIEW_IN_PROGRESS"
    assert manual["classification"] == "READY_FOR_MANUAL_DECISION"
    assert blocked["classification"] == "BLOCKED_REQUIRES_MORE_INFO"
    assert "AUTO_APPROVE" in ready["forbidden_actions"]


def test_kpi_classification_and_forbidden_flags():
    incomplete = kpi_dashboard_service.classify_kpi_readiness(1, {})
    ready = kpi_dashboard_service.classify_kpi_readiness(1, {"backend_contract_ready": True})
    values = kpi_dashboard_service.classify_kpi_readiness(1, {"backend_contract_ready": True, "values_requested": True})
    frontend = kpi_dashboard_service.classify_kpi_readiness(1, {"backend_contract_ready": True, "frontend_claimed": True})
    assert incomplete["kpi_readiness_status"] == "KPI_BACKEND_CONTRACT_INCOMPLETE"
    assert ready["kpi_readiness_status"] == "KPI_BACKEND_CONTRACT_READY"
    assert values["kpi_readiness_status"] == "KPI_VALUES_NOT_AVAILABLE"
    assert frontend["kpi_readiness_status"] == "KPI_FRONTEND_NOT_CLAIMED"
    assert ready["frontend_claim"] is False
    assert ready["kpi_values_available"] is False
    assert ready["brain_mapping_status"] == "NOT_AVAILABLE"


def test_workload_classification_and_forbidden_actions():
    incomplete = workload_service.evaluate_workload_plan(1, {"workload_type": "TEACHING"})
    review = workload_service.evaluate_workload_plan(1, {"workload_type": "TEACHING", "units": 3})
    assignment = workload_service.evaluate_workload_plan(1, {"workload_type": "TEACHING", "units": 3, "assignment_context": True})
    overload = workload_service.evaluate_workload_plan(1, {"workload_type": "TEACHING", "units": 3, "overload_risk": True})
    policy = workload_service.evaluate_workload_plan(1, {"workload_type": "TEACHING", "units": 3, "policy_review_required": True})
    assert incomplete["classification"] == "WORKLOAD_INPUT_INCOMPLETE"
    assert review["classification"] == "READY_FOR_HUMAN_REVIEW"
    assert assignment["classification"] == "READY_FOR_ASSIGNMENT_PLANNING"
    assert overload["classification"] == "OVERLOAD_RISK_REVIEW_REQUIRED"
    assert policy["classification"] == "POLICY_REVIEW_REQUIRED"
    assert "AUTO_ASSIGN" in review["forbidden_actions"]


def test_notification_classification_and_forbidden_flags():
    incomplete = notification_service.classify_notification_readiness(1, {"notification_type": "WORKFLOW_APPROVED"})
    unsupported = notification_service.classify_notification_readiness(1, {"notification_type": "NOT_REAL", "subject": "s", "message": "m", "provider_configured": True})
    provider = notification_service.classify_notification_readiness(1, {"notification_type": "WORKFLOW_APPROVED", "subject": "s", "message": "m"})
    review = notification_service.classify_notification_readiness(1, {"notification_type": "WORKFLOW_APPROVED", "subject": "s", "message": "m", "provider_configured": True, "send_requested": True})
    compose = notification_service.classify_notification_readiness(1, {"notification_type": "WORKFLOW_APPROVED", "subject": "s", "message": "m", "provider_configured": True})
    assert incomplete["classification"] == "NOTIFICATION_INPUT_INCOMPLETE"
    assert unsupported["classification"] == "BLOCKED_UNSUPPORTED_TYPE"
    assert provider["classification"] == "PROVIDER_NOT_CONFIGURED"
    assert review["classification"] == "READY_FOR_MANUAL_DISPATCH_REVIEW"
    assert compose["classification"] == "READY_TO_COMPOSE"
    assert compose["NO_SENDING"] is True
    assert compose["NO_PROVIDER_CALLS"] is True
    assert compose["TENANT_ISOLATION_REQUIRED"] is True


@pytest.mark.parametrize("module_name, service_module, l3_func, incomplete_input, valid_input", MODULES)
def test_anti_inflation_flags(module_name, service_module, l3_func, incomplete_input, valid_input):
    result = l3_func(1, valid_input)
    assert result["maturity_level"] == "L3"
    assert result["safety_flags"]["no_api_claim"] is True
    assert result["safety_flags"]["no_frontend_claim"] is True
    assert result["safety_flags"]["no_brain_claim"] is True
    assert result["safety_flags"]["no_kpi_lineage_claim"] is True
    assert result["safety_flags"]["no_autonomous_execution"] is True
    assert result["safety_flags"]["no_e2e_claim"] is True
    assert result["safety_flags"]["target_level"] == "L3"


def test_a0263_l2_contract_continuity():
    assert human_workflow_service.get_workflow_status_contract(1)["target_level"] == "L2"
    assert proposal_service.get_proposal_readiness_contract(1)["target_level"] == "L2"
    assert simulation_service.get_simulation_readiness_response(1)["target_level"] == "L2"
    assert bridge_service.get_bridge_readiness_contract(1)["target_level"] == "L2"
    assert approval_queue_service.get_queue_status_contract(1)["target_level"] == "L2"
    assert kpi_dashboard_service.get_kpi_readiness_contract(1)["target_level"] == "L2"
    assert workload_service.get_workload_readiness_contract(1)["target_level"] == "L2"
    assert notification_service.get_notification_readiness_contract(1)["target_level"] == "L2"