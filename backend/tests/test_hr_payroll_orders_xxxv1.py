"""XXXV.1 — hr_payroll Personnel Orders tests.

Tests: 15
FSM: DRAFT → SIGNED → APPROVED → EXECUTED
Types: HIRE | DISMISS | TRANSFER | SALARY_CHANGE
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_order(
    order_id: int = 1,
    order_type: str = "HIRE",
    status: str = "DRAFT",
    employee_id: object = None,
) -> dict:
    return {
        "id": order_id,
        "order_type": order_type,
        "status": status,
        "employee_id": employee_id,
        "tenant_id": 1,
    }


# ---------------------------------------------------------------------------
# 1. create_personnel_order — valid HIRE (no employee required)
# ---------------------------------------------------------------------------

def test_create_hire_order_fires_created_event():
    with (
        patch("app.modules.hr_payroll.service.create_entity_for_tenant") as mock_create,
        patch("app.modules.hr_payroll.service.log_admin_action"),
        patch("app.modules.hr_payroll.service.EventPublisher") as MockPub,
    ):
        mock_create.return_value = _make_order(order_id=10, order_type="HIRE")
        pub_inst = MockPub.return_value

        from app.modules.hr_payroll.service import create_personnel_order
        result = create_personnel_order(
            tenant_id=1,
            payload={"order_type": "HIRE", "order_number": "ORD-001"},
            actor="admin",
        )

        assert result["order_type"] == "HIRE"
        pub_inst.publish_event.assert_called_once()
        call_kwargs = pub_inst.publish_event.call_args.kwargs
        assert call_kwargs["event_type"] == "hr.personnel_order.created"
        assert call_kwargs["tenant_id"] == 1


# ---------------------------------------------------------------------------
# 2. create_personnel_order — DISMISS requires employee
# ---------------------------------------------------------------------------

def test_create_dismiss_order_cross_entity_check():
    with (
        patch("app.modules.hr_payroll.service.list_entities_for_tenant") as mock_list,
        patch("app.modules.hr_payroll.service.create_entity_for_tenant") as mock_create,
        patch("app.modules.hr_payroll.service.log_admin_action"),
        patch("app.modules.hr_payroll.service.EventPublisher"),
    ):
        # employee exists
        mock_list.return_value = [{"id": 5, "status": "active"}]
        mock_create.return_value = _make_order(order_id=11, order_type="DISMISS", employee_id=5)

        from app.modules.hr_payroll.service import create_personnel_order
        result = create_personnel_order(
            tenant_id=1,
            payload={"order_type": "DISMISS", "employee_id": 5},
            actor="admin",
        )
        assert result["order_type"] == "DISMISS"


# ---------------------------------------------------------------------------
# 3. create_personnel_order — DISMISS with missing employee raises
# ---------------------------------------------------------------------------

def test_create_dismiss_order_missing_employee_raises():
    with (
        patch("app.modules.hr_payroll.service.list_entities_for_tenant") as mock_list,
        patch("app.modules.hr_payroll.service.EventPublisher"),
    ):
        mock_list.return_value = []  # no employees

        from app.modules.hr_payroll.service import create_personnel_order
        from app.core.module_helpers.service_validation import DomainValidationError

        with pytest.raises(DomainValidationError, match="employee_id=99"):
            create_personnel_order(
                tenant_id=1,
                payload={"order_type": "DISMISS", "employee_id": 99},
                actor="admin",
            )


# ---------------------------------------------------------------------------
# 4. create_personnel_order — invalid order type raises
# ---------------------------------------------------------------------------

def test_create_invalid_order_type_raises():
    with patch("app.modules.hr_payroll.service.EventPublisher"):
        from app.modules.hr_payroll.service import create_personnel_order
        with pytest.raises(ValueError, match="Invalid personnel order type"):
            create_personnel_order(
                tenant_id=1,
                payload={"order_type": "INVALID_TYPE"},
                actor="admin",
            )


# ---------------------------------------------------------------------------
# 5. TRANSFER order — also validates employee exists
# ---------------------------------------------------------------------------

def test_create_transfer_order_employee_missing_raises():
    with (
        patch("app.modules.hr_payroll.service.list_entities_for_tenant") as mock_list,
        patch("app.modules.hr_payroll.service.EventPublisher"),
    ):
        mock_list.return_value = []
        from app.modules.hr_payroll.service import create_personnel_order
        from app.core.module_helpers.service_validation import DomainValidationError
        with pytest.raises(DomainValidationError):
            create_personnel_order(
                tenant_id=1,
                payload={"order_type": "TRANSFER", "employee_id": 7},
                actor="admin",
            )


# ---------------------------------------------------------------------------
# 6. transition DRAFT → SIGNED — requires ecds_signature
# ---------------------------------------------------------------------------

def test_transition_draft_to_signed_requires_signature():
    order = _make_order(order_id=1, status="DRAFT")

    with (
        patch("app.modules.hr_payroll.service.list_entities_for_tenant") as mock_list,
        patch("app.modules.hr_payroll.service.EventPublisher"),
    ):
        mock_list.return_value = [order]
        from app.modules.hr_payroll.service import transition_personnel_order
        from app.core.module_helpers.service_validation import DomainValidationError

        with pytest.raises(DomainValidationError, match="ecds_signature is required"):
            transition_personnel_order(
                tenant_id=1,
                order_id=1,
                target_status="SIGNED",
                actor="admin",
                ecds_signature=None,
            )


# ---------------------------------------------------------------------------
# 7. transition DRAFT → SIGNED — with valid signature fires signed event
# ---------------------------------------------------------------------------

def test_transition_draft_to_signed_fires_event():
    order = _make_order(order_id=2, status="DRAFT")

    with (
        patch("app.modules.hr_payroll.service.list_entities_for_tenant") as mock_list,
        patch("app.modules.hr_payroll.service.update_entity_for_tenant") as mock_update,
        patch("app.modules.hr_payroll.service.log_admin_action"),
        patch("app.modules.hr_payroll.service.EventPublisher") as MockPub,
    ):
        mock_list.return_value = [order]
        mock_update.return_value = {**order, "status": "SIGNED"}
        pub_inst = MockPub.return_value

        from app.modules.hr_payroll.service import transition_personnel_order
        result = transition_personnel_order(
            tenant_id=1,
            order_id=2,
            target_status="SIGNED",
            actor="admin",
            ecds_signature="SIG-ABC-XYZ",
        )

        assert result["status"] == "SIGNED"
        pub_inst.publish_event.assert_called_once()
        assert pub_inst.publish_event.call_args.kwargs["event_type"] == "hr.personnel_order.signed"


# ---------------------------------------------------------------------------
# 8. transition SIGNED → APPROVED fires approved event
# ---------------------------------------------------------------------------

def test_transition_signed_to_approved_fires_event():
    order = _make_order(order_id=3, status="SIGNED")

    with (
        patch("app.modules.hr_payroll.service.list_entities_for_tenant") as mock_list,
        patch("app.modules.hr_payroll.service.update_entity_for_tenant") as mock_update,
        patch("app.modules.hr_payroll.service.log_admin_action"),
        patch("app.modules.hr_payroll.service.EventPublisher") as MockPub,
    ):
        mock_list.return_value = [order]
        mock_update.return_value = {**order, "status": "APPROVED"}
        pub_inst = MockPub.return_value

        from app.modules.hr_payroll.service import transition_personnel_order
        result = transition_personnel_order(
            tenant_id=1, order_id=3, target_status="APPROVED", actor="admin"
        )
        assert result["status"] == "APPROVED"
        assert pub_inst.publish_event.call_args.kwargs["event_type"] == "hr.personnel_order.approved"


# ---------------------------------------------------------------------------
# 9. transition APPROVED → EXECUTED fires executed event
# ---------------------------------------------------------------------------

def test_transition_approved_to_executed_fires_event():
    order = _make_order(order_id=4, status="APPROVED", order_type="HIRE")

    with (
        patch("app.modules.hr_payroll.service.list_entities_for_tenant") as mock_list,
        patch("app.modules.hr_payroll.service.update_entity_for_tenant") as mock_update,
        patch("app.modules.hr_payroll.service.log_admin_action"),
        patch("app.modules.hr_payroll.service.EventPublisher") as MockPub,
    ):
        mock_list.return_value = [order]
        mock_update.return_value = {**order, "status": "EXECUTED"}
        pub_inst = MockPub.return_value

        from app.modules.hr_payroll.service import transition_personnel_order
        result = transition_personnel_order(
            tenant_id=1, order_id=4, target_status="EXECUTED", actor="admin"
        )
        assert result["status"] == "EXECUTED"
        assert pub_inst.publish_event.call_args.kwargs["event_type"] == "hr.personnel_order.executed"


# ---------------------------------------------------------------------------
# 10. FSM guard — invalid transition raises ValueError
# ---------------------------------------------------------------------------

def test_invalid_fsm_transition_raises():
    order = _make_order(order_id=5, status="DRAFT")

    with (
        patch("app.modules.hr_payroll.service.list_entities_for_tenant") as mock_list,
        patch("app.modules.hr_payroll.service.EventPublisher"),
    ):
        mock_list.return_value = [order]
        from app.modules.hr_payroll.service import transition_personnel_order

        with pytest.raises(ValueError, match="Invalid personnel order transition"):
            transition_personnel_order(
                tenant_id=1, order_id=5, target_status="EXECUTED", actor="admin"
            )


# ---------------------------------------------------------------------------
# 11. FSM guard — EXECUTED is terminal; no further transitions
# ---------------------------------------------------------------------------

def test_executed_order_is_terminal():
    order = _make_order(order_id=6, status="EXECUTED")

    with (
        patch("app.modules.hr_payroll.service.list_entities_for_tenant") as mock_list,
        patch("app.modules.hr_payroll.service.EventPublisher"),
    ):
        mock_list.return_value = [order]
        from app.modules.hr_payroll.service import transition_personnel_order

        with pytest.raises(ValueError, match="terminal"):
            transition_personnel_order(
                tenant_id=1, order_id=6, target_status="APPROVED", actor="admin"
            )


# ---------------------------------------------------------------------------
# 12. transition not found raises LookupError
# ---------------------------------------------------------------------------

def test_transition_missing_order_raises_lookup():
    with (
        patch("app.modules.hr_payroll.service.list_entities_for_tenant") as mock_list,
        patch("app.modules.hr_payroll.service.EventPublisher"),
    ):
        mock_list.return_value = []
        from app.modules.hr_payroll.service import transition_personnel_order

        with pytest.raises(LookupError):
            transition_personnel_order(
                tenant_id=1, order_id=999, target_status="SIGNED", actor="admin"
            )


# ---------------------------------------------------------------------------
# 13. list_personnel_orders — filter by type
# ---------------------------------------------------------------------------

def test_list_personnel_orders_filter_by_type():
    orders = [
        _make_order(1, "HIRE", "DRAFT"),
        _make_order(2, "DISMISS", "SIGNED"),
        _make_order(3, "HIRE", "APPROVED"),
    ]
    with patch("app.modules.hr_payroll.service.list_entities_for_tenant") as mock_list:
        mock_list.return_value = orders
        from app.modules.hr_payroll.service import list_personnel_orders
        result = list_personnel_orders(tenant_id=1, order_type="HIRE")
        assert len(result) == 2
        assert all(r["order_type"] == "HIRE" for r in result)


# ---------------------------------------------------------------------------
# 14. list_personnel_orders — filter by status
# ---------------------------------------------------------------------------

def test_list_personnel_orders_filter_by_status():
    orders = [
        _make_order(1, "HIRE", "DRAFT"),
        _make_order(2, "DISMISS", "APPROVED"),
        _make_order(3, "TRANSFER", "DRAFT"),
    ]
    with patch("app.modules.hr_payroll.service.list_entities_for_tenant") as mock_list:
        mock_list.return_value = orders
        from app.modules.hr_payroll.service import list_personnel_orders
        result = list_personnel_orders(tenant_id=1, status="DRAFT")
        assert len(result) == 2


# ---------------------------------------------------------------------------
# 15. DISMISS EXECUTED — applies offboarding side-effect to employee
# ---------------------------------------------------------------------------

def test_dismiss_executed_applies_offboarding_to_employee():
    order = _make_order(order_id=7, order_type="DISMISS", status="APPROVED", employee_id=20)
    employee = {"id": 20, "status": "active", "department_id": "dept-1", "tenant_id": 1}

    with (
        patch("app.modules.hr_payroll.service.list_entities_for_tenant") as mock_list,
        patch("app.modules.hr_payroll.service.update_entity_for_tenant") as mock_update,
        patch("app.modules.hr_payroll.service.log_admin_action"),
        patch("app.modules.hr_payroll.service.EventPublisher") as MockPub,
    ):
        # First call: list orders; second call inside _apply: list employees
        mock_list.side_effect = [[order], [employee]]
        mock_update.return_value = {**order, "status": "EXECUTED"}

        from app.modules.hr_payroll.service import transition_personnel_order
        result = transition_personnel_order(
            tenant_id=1, order_id=7, target_status="EXECUTED", actor="admin"
        )
        assert result["status"] == "EXECUTED"

        # update_entity_for_tenant called twice: order update + employee offboarding
        assert mock_update.call_count == 2
        # Second call should set employee status to offboarding
        second_call_data = mock_update.call_args_list[1]
        assert second_call_data.args[2]["status"] == "offboarding"
