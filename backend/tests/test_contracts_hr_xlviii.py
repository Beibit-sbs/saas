"""Phase XLVIII: Personnel Orders + Contracts HR Tests (20 tests)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import app.modules.contracts_hr.service as svc

TENANT = "uni-xlviii"
BAD_TENANT = "bad-tenant"


def _make_order(oid="o-1", order_type="HIRE", status="DRAFT", employee_id="emp-1"):
    return {
        "id": oid,
        "order_type": order_type,
        "employee_id": employee_id,
        "description": "Hire order",
        "status": status,
        "signed_by": None,
        "tenant_id": TENANT,
    }


def _make_contract(cid="c-1", status="DRAFT", employee_id="emp-1"):
    return {
        "id": cid,
        "employee_id": employee_id,
        "position": "Lecturer",
        "salary": 500_000.0,
        "start_date": "2026-09-01",
        "status": status,
        "tenant_id": TENANT,
    }


# ─── 1. Constants ─────────────────────────────────────────────────────────────

class TestConstants:
    def test_order_types_complete(self):
        assert {"HIRE", "DISMISS", "TRANSFER", "SALARY_CHANGE", "LEAVE", "DISCIPLINE"} == svc.ORDER_TYPES

    def test_order_states_complete(self):
        assert {"DRAFT", "HR_REVIEW", "DIRECTOR_APPROVAL", "SIGNED", "EXECUTED", "ARCHIVED"} == svc.ORDER_STATES

    def test_contract_states_complete(self):
        assert {"DRAFT", "ACTIVE", "SUSPENDED", "TERMINATED"} == svc.CONTRACT_STATES


# ─── 2. create_order ──────────────────────────────────────────────────────────

class TestCreateOrder:
    def test_create_order_fires_event(self):
        publisher = MagicMock()
        with patch("app.modules.contracts_hr.service.create_entity_for_tenant", return_value=_make_order()):
            with patch("app.modules.contracts_hr.service.EventPublisher", publisher):
                order = svc.create_order(TENANT, order_type="HIRE", employee_id="emp-1", description="Hire")
        assert order["status"] == "DRAFT"
        publisher.publish.assert_called_once()
        assert publisher.publish.call_args[0][0] == "order.created"

    def test_create_order_invalid_type(self):
        with pytest.raises(ValueError, match="order_type"):
            svc.create_order(TENANT, order_type="UNKNOWN", employee_id="emp-1", description="x")

    def test_create_order_missing_employee(self):
        with pytest.raises(ValueError, match="employee_id"):
            svc.create_order(TENANT, order_type="HIRE", employee_id="", description="x")

    def test_create_order_missing_description(self):
        with pytest.raises(ValueError, match="description"):
            svc.create_order(TENANT, order_type="HIRE", employee_id="emp-1", description="")

    def test_create_order_bad_tenant(self):
        with pytest.raises(ValueError, match="tenant"):
            svc.create_order(BAD_TENANT, order_type="HIRE", employee_id="emp-1", description="x")


# ─── 3. Order FSM ─────────────────────────────────────────────────────────────

class TestOrderFSM:
    def test_submit_for_hr_review_success(self):
        order = _make_order()
        with patch("app.modules.contracts_hr.service.list_entities_for_tenant", return_value=[order]):
            result = svc.submit_for_hr_review(TENANT, order_id="o-1")
        assert result["status"] == "HR_REVIEW"

    def test_submit_for_hr_review_wrong_status(self):
        order = _make_order(status="SIGNED")
        with patch("app.modules.contracts_hr.service.list_entities_for_tenant", return_value=[order]):
            with pytest.raises(ValueError, match="transition"):
                svc.submit_for_hr_review(TENANT, order_id="o-1")

    def test_approve_by_director_success(self):
        order = _make_order(status="HR_REVIEW")
        with patch("app.modules.contracts_hr.service.list_entities_for_tenant", return_value=[order]):
            result = svc.approve_by_director(TENANT, order_id="o-1")
        assert result["status"] == "DIRECTOR_APPROVAL"

    def test_sign_order_fires_event(self):
        order = _make_order(status="DIRECTOR_APPROVAL")
        publisher = MagicMock()
        with patch("app.modules.contracts_hr.service.list_entities_for_tenant", return_value=[order]):
            with patch("app.modules.contracts_hr.service.EventPublisher", publisher):
                result = svc.sign_order(TENANT, order_id="o-1", signed_by="DIRECTOR-CERT")
        assert result["status"] == "SIGNED"
        assert result["signed_by"] == "DIRECTOR-CERT"
        publisher.publish.assert_called_once()
        assert publisher.publish.call_args[0][0] == "order.signed"

    def test_sign_order_missing_cert(self):
        with pytest.raises(ValueError, match="signed_by"):
            svc.sign_order(TENANT, order_id="o-1", signed_by="")

    def test_execute_order_fires_event(self):
        order = _make_order(status="SIGNED")
        publisher = MagicMock()
        with patch("app.modules.contracts_hr.service.list_entities_for_tenant", return_value=[order]):
            with patch("app.modules.contracts_hr.service.EventPublisher", publisher):
                result = svc.execute_order(TENANT, order_id="o-1")
        assert result["status"] == "EXECUTED"
        # At least order.executed fired
        call_names = [c[0][0] for c in publisher.publish.call_args_list]
        assert "order.executed" in call_names

    def test_execute_dismiss_bulk_triggers_anomaly(self):
        """5 executed DISMISS orders → hr.anomaly_detected."""
        current_order = _make_order(oid="o-5", order_type="DISMISS", status="SIGNED")
        existing_executed = [
            _make_order(oid=f"o-{i}", order_type="DISMISS", status="EXECUTED")
            for i in range(1, 5)
        ]
        all_orders = existing_executed + [current_order]
        publisher = MagicMock()
        with patch("app.modules.contracts_hr.service.list_entities_for_tenant", return_value=all_orders):
            with patch("app.modules.contracts_hr.service.EventPublisher", publisher):
                svc.execute_order(TENANT, order_id="o-5")
        call_names = [c[0][0] for c in publisher.publish.call_args_list]
        assert "hr.anomaly_detected" in call_names

    def test_archive_order_success(self):
        order = _make_order(status="EXECUTED")
        with patch("app.modules.contracts_hr.service.list_entities_for_tenant", return_value=[order]):
            result = svc.archive_order(TENANT, order_id="o-1")
        assert result["status"] == "ARCHIVED"

    def test_list_orders_filter_by_type(self):
        orders = [
            _make_order("o-1", "HIRE", "DRAFT"),
            _make_order("o-2", "DISMISS", "DRAFT"),
            _make_order("o-3", "HIRE", "SIGNED"),
        ]
        with patch("app.modules.contracts_hr.service.list_entities_for_tenant", return_value=orders):
            result = svc.list_orders(TENANT, order_type="HIRE")
        assert len(result) == 2
        assert all(o["order_type"] == "HIRE" for o in result)


# ─── 4. Employment Contract ───────────────────────────────────────────────────

class TestContract:
    def test_create_contract_success(self):
        with patch("app.modules.contracts_hr.service.create_entity_for_tenant", return_value=_make_contract()):
            contract = svc.create_contract(
                TENANT, employee_id="emp-1", position="Lecturer",
                salary=500_000.0, start_date="2026-09-01"
            )
        assert contract["status"] == "DRAFT"

    def test_create_contract_missing_employee(self):
        with pytest.raises(ValueError, match="employee_id"):
            svc.create_contract(TENANT, employee_id="", position="Prof", salary=100.0, start_date="2026-01-01")

    def test_create_contract_zero_salary(self):
        with pytest.raises(ValueError, match="salary"):
            svc.create_contract(TENANT, employee_id="emp-1", position="Prof", salary=0, start_date="2026-01-01")

    def test_activate_contract_success(self):
        contract = _make_contract()
        with patch("app.modules.contracts_hr.service.list_entities_for_tenant", return_value=[contract]):
            result = svc.activate_contract(TENANT, contract_id="c-1")
        assert result["status"] == "ACTIVE"

    def test_activate_contract_wrong_status(self):
        contract = _make_contract(status="ACTIVE")
        with patch("app.modules.contracts_hr.service.list_entities_for_tenant", return_value=[contract]):
            with pytest.raises(ValueError, match="activate"):
                svc.activate_contract(TENANT, contract_id="c-1")

    def test_terminate_contract_success(self):
        contract = _make_contract(status="ACTIVE")
        with patch("app.modules.contracts_hr.service.list_entities_for_tenant", return_value=[contract]):
            result = svc.terminate_contract(TENANT, contract_id="c-1", reason="End of term")
        assert result["status"] == "TERMINATED"
        assert result["termination_reason"] == "End of term"

    def test_terminate_contract_missing_reason(self):
        with pytest.raises(ValueError, match="reason"):
            svc.terminate_contract(TENANT, contract_id="c-1", reason="")

    def test_list_contracts_filter_by_employee(self):
        contracts = [
            _make_contract("c-1", "ACTIVE", "emp-1"),
            _make_contract("c-2", "ACTIVE", "emp-2"),
            _make_contract("c-3", "TERMINATED", "emp-1"),
        ]
        with patch("app.modules.contracts_hr.service.list_entities_for_tenant", return_value=contracts):
            result = svc.list_contracts(TENANT, employee_id="emp-1")
        assert len(result) == 2
        assert all(c["employee_id"] == "emp-1" for c in result)
