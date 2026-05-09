"""A-024.2 targeted validation for AI Copilot Ops + Procurement Approval Workflow L2->L3 lift."""

from __future__ import annotations

import importlib

import pytest

from app.modules.ai_copilot_ops import service as ai_copilot_ops_service
from app.modules.procurement_approval_workflow import service as procurement_service


@pytest.mark.parametrize(
    "module_name",
    [
        "app.modules.ai_copilot_ops.service",
        "app.modules.procurement_approval_workflow.service",
    ],
)
def test_a0242_modules_are_importable(module_name: str) -> None:
    importlib.import_module(module_name)


def test_a0242_ai_copilot_l3_constants_exposed() -> None:
    assert isinstance(ai_copilot_ops_service.COPILOT_MODES, frozenset)
    assert {"disabled", "monitor_only", "advisory", "review_required"}.issubset(
        ai_copilot_ops_service.COPILOT_MODES
    )
    assert isinstance(ai_copilot_ops_service.COPILOT_REQUEST_STATUSES, frozenset)
    assert {"advisory_allowed", "review_required", "blocked"}.issubset(
        ai_copilot_ops_service.COPILOT_REQUEST_STATUSES
    )


def test_a0242_procurement_l3_constants_exposed() -> None:
    assert isinstance(procurement_service.PROCUREMENT_APPROVAL_STATUSES, frozenset)
    assert {"review_required", "ready_for_human_approval", "blocked"}.issubset(
        procurement_service.PROCUREMENT_APPROVAL_STATUSES
    )
    assert isinstance(procurement_service.PROCUREMENT_RISK_LEVELS, frozenset)


@pytest.mark.parametrize("tenant_id", [0, -1])
def test_a0242_ai_copilot_rejects_invalid_tenant(tenant_id: int) -> None:
    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        ai_copilot_ops_service.build_ai_copilot_ops_decision(
            tenant_id=tenant_id,
            user_role="operator",
            requested_action="summarize_dashboard",
            data_classification="internal",
            target_domain="platform_ops",
            estimated_cost=12.0,
            purpose="ops triage",
            mode="advisory",
            source_entity_type="incident",
            source_entity_id="inc-1",
        )


@pytest.mark.parametrize("tenant_id", [0, -1])
def test_a0242_procurement_rejects_invalid_tenant(tenant_id: int) -> None:
    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        procurement_service.build_procurement_approval_review(
            tenant_id=tenant_id,
            request_id="req-1",
            amount=1000.0,
            currency="usd",
            procurement_method="rfq",
            has_budget_reference=True,
            has_required_documents=True,
            is_single_source=False,
            requester_role="manager",
            source_entity_type="procurement_request",
            source_entity_id="req-1",
        )


def test_a0242_ai_copilot_requires_mode_from_allowed_set() -> None:
    with pytest.raises(ValueError, match="mode must be one of"):
        ai_copilot_ops_service.build_ai_copilot_ops_decision(
            tenant_id=1,
            user_role="operator",
            requested_action="summarize_dashboard",
            data_classification="internal",
            target_domain="platform_ops",
            estimated_cost=1.0,
            purpose="ops triage",
            mode="auto",
            source_entity_type="incident",
            source_entity_id="inc-1",
        )


def test_a0242_ai_copilot_rejects_negative_cost() -> None:
    with pytest.raises(ValueError, match="estimated_cost must be >= 0"):
        ai_copilot_ops_service.build_ai_copilot_ops_decision(
            tenant_id=1,
            user_role="operator",
            requested_action="summarize_dashboard",
            data_classification="internal",
            target_domain="platform_ops",
            estimated_cost=-1,
            purpose="ops triage",
            mode="advisory",
            source_entity_type="incident",
            source_entity_id="inc-1",
        )


def test_a0242_ai_copilot_disabled_mode_blocks_request() -> None:
    result = ai_copilot_ops_service.build_ai_copilot_ops_decision(
        tenant_id=2,
        user_role="operator",
        requested_action="summarize_dashboard",
        data_classification="internal",
        target_domain="platform_ops",
        estimated_cost=10,
        purpose="ops triage",
        mode="disabled",
        source_entity_type="incident",
        source_entity_id="inc-2",
    )
    assert result["request_status"] == "blocked"
    assert result["risk_level"] == "critical"
    assert result["review_required"] is True


def test_a0242_ai_copilot_destructive_action_is_blocked() -> None:
    result = ai_copilot_ops_service.build_ai_copilot_ops_decision(
        tenant_id=2,
        user_role="admin",
        requested_action="approve_payment",
        data_classification="internal",
        target_domain="finance_procurement",
        estimated_cost=20,
        purpose="ops triage",
        mode="advisory",
        source_entity_type="request",
        source_entity_id="r-1",
    )
    assert result["request_status"] == "blocked"
    assert "DESTRUCTIVE_ACTION_NOT_ALLOWED" in result["safety_reasons"]


def test_a0242_ai_copilot_sensitive_data_requires_review() -> None:
    result = ai_copilot_ops_service.build_ai_copilot_ops_decision(
        tenant_id=2,
        user_role="manager",
        requested_action="draft_summary",
        data_classification="restricted",
        target_domain="governance",
        estimated_cost=15,
        purpose="governance prep",
        mode="advisory",
        source_entity_type="ticket",
        source_entity_id="t-1",
    )
    assert result["request_status"] == "review_required"
    assert result["risk_level"] in {"high", "critical"}


def test_a0242_ai_copilot_unknown_domain_requires_review() -> None:
    result = ai_copilot_ops_service.build_ai_copilot_ops_decision(
        tenant_id=2,
        user_role="manager",
        requested_action="draft_summary",
        data_classification="internal",
        target_domain="new_domain",
        estimated_cost=10,
        purpose="ops review",
        mode="advisory",
        source_entity_type="ticket",
        source_entity_id="t-2",
    )
    assert result["request_status"] == "review_required"
    assert "UNKNOWN_TARGET_DOMAIN" in result["safety_reasons"]


def test_a0242_ai_copilot_guest_is_blocked() -> None:
    result = ai_copilot_ops_service.build_ai_copilot_ops_decision(
        tenant_id=2,
        user_role="guest",
        requested_action="draft_summary",
        data_classification="internal",
        target_domain="platform_ops",
        estimated_cost=10,
        purpose="ops review",
        mode="advisory",
        source_entity_type="ticket",
        source_entity_id="t-3",
    )
    assert result["request_status"] == "blocked"
    assert result["risk_level"] == "critical"


def test_a0242_ai_copilot_monitor_only_keeps_policy_reason() -> None:
    result = ai_copilot_ops_service.build_ai_copilot_ops_decision(
        tenant_id=2,
        user_role="manager",
        requested_action="draft_summary",
        data_classification="internal",
        target_domain="platform_ops",
        estimated_cost=100,
        purpose="ops review",
        mode="monitor_only",
        source_entity_type="ticket",
        source_entity_id="t-4",
    )
    assert "COPILOT_MODE_MONITOR_ONLY" in result["policy_reasons"]


def test_a0242_ai_copilot_happy_path_is_advisory_allowed() -> None:
    result = ai_copilot_ops_service.build_ai_copilot_ops_decision(
        tenant_id=10,
        user_role="manager",
        requested_action="summarize_dashboard",
        data_classification="internal",
        target_domain="platform_ops",
        estimated_cost=90,
        purpose="ops review",
        mode="advisory",
        source_entity_type="incident",
        source_entity_id="inc-10",
    )
    assert result["request_status"] == "advisory_allowed"
    assert result["risk_level"] == "low"
    assert result["event_readiness"] == "ai.copilot.advisory_allowed"


def test_a0242_ai_copilot_sets_no_action_flags() -> None:
    result = ai_copilot_ops_service.build_ai_copilot_ops_decision(
        tenant_id=10,
        user_role="manager",
        requested_action="summarize_dashboard",
        data_classification="internal",
        target_domain="platform_ops",
        estimated_cost=90,
        purpose="ops review",
        mode="advisory",
        source_entity_type="incident",
        source_entity_id="inc-11",
    )
    assert result["no_external_call"] is True
    assert result["no_autonomous_execution"] is True
    assert result["no_tool_execution"] is True


def test_a0242_ai_copilot_is_deterministic_for_same_inputs() -> None:
    payload = dict(
        tenant_id=10,
        user_role="manager",
        requested_action="summarize_dashboard",
        data_classification="internal",
        target_domain="platform_ops",
        estimated_cost=42.0,
        purpose="ops review",
        mode="advisory",
        source_entity_type="incident",
        source_entity_id="inc-12",
    )
    assert ai_copilot_ops_service.build_ai_copilot_ops_decision(**payload) == (
        ai_copilot_ops_service.build_ai_copilot_ops_decision(**payload)
    )


def test_a0242_procurement_rejects_non_positive_amount() -> None:
    with pytest.raises(ValueError, match="amount must be > 0"):
        procurement_service.build_procurement_approval_review(
            tenant_id=1,
            request_id="req-2",
            amount=0,
            currency="USD",
            procurement_method="rfq",
            has_budget_reference=True,
            has_required_documents=True,
            is_single_source=False,
            requester_role="manager",
            source_entity_type="procurement_request",
            source_entity_id="req-2",
        )


def test_a0242_procurement_requires_request_id() -> None:
    with pytest.raises(ValueError, match="request_id is required"):
        procurement_service.build_procurement_approval_review(
            tenant_id=1,
            request_id="",
            amount=100,
            currency="USD",
            procurement_method="rfq",
            has_budget_reference=True,
            has_required_documents=True,
            is_single_source=False,
            requester_role="manager",
            source_entity_type="procurement_request",
            source_entity_id="req-3",
        )


def test_a0242_procurement_missing_documents_blocks_request() -> None:
    result = procurement_service.build_procurement_approval_review(
        tenant_id=2,
        request_id="req-4",
        amount=1000,
        currency="usd",
        procurement_method="rfq",
        has_budget_reference=True,
        has_required_documents=False,
        is_single_source=False,
        requester_role="manager",
        source_entity_type="procurement_request",
        source_entity_id="req-4",
    )
    assert result["approval_status"] == "blocked"
    assert result["risk_level"] in {"high", "critical"}
    assert "required_documents" in result["missing_requirements"]


def test_a0242_procurement_missing_budget_requires_review() -> None:
    result = procurement_service.build_procurement_approval_review(
        tenant_id=2,
        request_id="req-5",
        amount=1000,
        currency="usd",
        procurement_method="rfq",
        has_budget_reference=False,
        has_required_documents=True,
        is_single_source=False,
        requester_role="manager",
        source_entity_type="procurement_request",
        source_entity_id="req-5",
    )
    assert result["approval_status"] == "review_required"
    assert "budget_reference" in result["missing_requirements"]


def test_a0242_procurement_single_source_requires_review() -> None:
    result = procurement_service.build_procurement_approval_review(
        tenant_id=2,
        request_id="req-6",
        amount=1000,
        currency="usd",
        procurement_method="single_source",
        has_budget_reference=True,
        has_required_documents=True,
        is_single_source=True,
        requester_role="manager",
        source_entity_type="procurement_request",
        source_entity_id="req-6",
    )
    assert result["approval_status"] == "review_required"
    assert "SINGLE_SOURCE_REQUIRES_REVIEW" in result["policy_reasons"]


def test_a0242_procurement_high_amount_requires_review() -> None:
    result = procurement_service.build_procurement_approval_review(
        tenant_id=2,
        request_id="req-7",
        amount=125000,
        currency="usd",
        procurement_method="rfq",
        has_budget_reference=True,
        has_required_documents=True,
        is_single_source=False,
        requester_role="director",
        source_entity_type="procurement_request",
        source_entity_id="req-7",
    )
    assert result["approval_status"] == "review_required"
    assert "HIGH_AMOUNT_THRESHOLD" in result["policy_reasons"]


def test_a0242_procurement_insufficient_role_blocks() -> None:
    result = procurement_service.build_procurement_approval_review(
        tenant_id=2,
        request_id="req-8",
        amount=1000,
        currency="usd",
        procurement_method="rfq",
        has_budget_reference=True,
        has_required_documents=True,
        is_single_source=False,
        requester_role="intern",
        source_entity_type="procurement_request",
        source_entity_id="req-8",
    )
    assert result["approval_status"] == "blocked"
    assert result["risk_level"] == "critical"


def test_a0242_procurement_unknown_method_returns_for_revision() -> None:
    result = procurement_service.build_procurement_approval_review(
        tenant_id=2,
        request_id="req-9",
        amount=1000,
        currency="usd",
        procurement_method="unknown",
        has_budget_reference=True,
        has_required_documents=True,
        is_single_source=False,
        requester_role="manager",
        source_entity_type="procurement_request",
        source_entity_id="req-9",
    )
    assert result["approval_status"] == "returned_for_revision"
    assert result["event_readiness"] == "procurement.approval.returned_for_revision"


def test_a0242_procurement_happy_path_ready_for_human_approval() -> None:
    result = procurement_service.build_procurement_approval_review(
        tenant_id=3,
        request_id="req-10",
        amount=5000,
        currency="usd",
        procurement_method="rfq",
        has_budget_reference=True,
        has_required_documents=True,
        is_single_source=False,
        requester_role="manager",
        source_entity_type="procurement_request",
        source_entity_id="req-10",
        vendor_id="vendor-10",
    )
    assert result["approval_status"] == "ready_for_human_approval"
    assert result["review_required"] is False
    assert result["event_readiness"] == "procurement.approval.ready_for_human_approval"


def test_a0242_procurement_sets_no_execution_flags() -> None:
    result = procurement_service.build_procurement_approval_review(
        tenant_id=3,
        request_id="req-11",
        amount=5000,
        currency="usd",
        procurement_method="rfq",
        has_budget_reference=True,
        has_required_documents=True,
        is_single_source=False,
        requester_role="manager",
        source_entity_type="procurement_request",
        source_entity_id="req-11",
    )
    assert result["no_auto_approval"] is True
    assert result["no_payment_execution"] is True
    assert result["no_contract_execution"] is True


def test_a0242_procurement_is_deterministic_for_same_inputs() -> None:
    payload = dict(
        tenant_id=3,
        request_id="req-12",
        amount=9999,
        currency="usd",
        procurement_method="rfq",
        has_budget_reference=True,
        has_required_documents=True,
        is_single_source=False,
        requester_role="manager",
        source_entity_type="procurement_request",
        source_entity_id="req-12",
    )
    assert procurement_service.build_procurement_approval_review(**payload) == (
        procurement_service.build_procurement_approval_review(**payload)
    )


def test_a0242_procurement_blocked_event_readiness_when_documents_missing() -> None:
    result = procurement_service.build_procurement_approval_review(
        tenant_id=4,
        request_id="req-13",
        amount=1200,
        currency="usd",
        procurement_method="rfq",
        has_budget_reference=False,
        has_required_documents=False,
        is_single_source=False,
        requester_role="manager",
        source_entity_type="procurement_request",
        source_entity_id="req-13",
    )
    assert result["approval_status"] == "blocked"
    assert result["event_readiness"] == "procurement.approval.blocked"
