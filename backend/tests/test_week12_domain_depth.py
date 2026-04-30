"""Week 12 — Domain Depth: budget planning ↔ expense controls integrity.

Tests:
  W12.1 – budget allocation guard: sum(allocations) must not exceed plan total_amount
  W12.2 – budget plan approval wires to expense_controls cost center
  W12.3 – expense_controls budget guard blocks overspend and emits signal
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _clear_entity(entity_key: str, tenant_id: int) -> None:
    from app.modules.university_core import shared

    with shared._state_lock:
        shared._state.data.setdefault(entity_key, {})
        keys_to_del = [
            key
            for key, value in shared._state.data[entity_key].items()
            if str(value.get("tenant_id")) == str(tenant_id)
        ]
        for key in keys_to_del:
            del shared._state.data[entity_key][key]


def _reset_week12_state(tenant_id: int) -> None:
    for entity in ("budget_plans", "budget_allocations", "cost_centers", "expense_records"):
        _clear_entity(entity, tenant_id)


# ---------------------------------------------------------------------------
# W12.1 – budget allocation guard
# ---------------------------------------------------------------------------


class TestBudgetAllocationGuard:
    def test_source_contains_plan_total_guard(self) -> None:
        import inspect

        from app.modules.budget_planning import service as svc

        src = inspect.getsource(svc.create_budget_allocation)
        assert "Allocation exceeds plan total_amount" in src

    def test_allocation_exceeding_plan_total_is_blocked(self) -> None:
        from app.modules.budget_planning import service as svc
        from app.modules.university_core.tenant_entity_service import create_entity_for_tenant

        tenant_id = 50121
        _reset_week12_state(tenant_id)

        plan = create_entity_for_tenant(
            "budget_plans",
            {
                "department_id": "FIN",
                "fiscal_year": 2026,
                "total_amount": 100.0,
                "currency": "USD",
                "status": "approved",
            },
            tenant_id,
        )

        create_entity_for_tenant(
            "budget_allocations",
            {
                "plan_id": int(plan["id"]),
                "category": "ops",
                "allocated_amount": 80.0,
                "spent_amount": "0.01",
                "currency": "USD",
            },
            tenant_id,
        )

        with pytest.raises(ValueError, match="Allocation exceeds plan total_amount"):
            svc.create_budget_allocation(
                {
                    "plan_id": int(plan["id"]),
                    "category": "travel",
                    "allocated_amount": 30.0,
                    "spent_amount": "0.01",
                    "currency": "USD",
                },
                tenant_id,
            )


# ---------------------------------------------------------------------------
# W12.2 – budget plan approval wiring
# ---------------------------------------------------------------------------


class TestBudgetPlanApprovalWiring:
    def test_source_wires_approved_plan_to_cost_center(self) -> None:
        import inspect

        from app.modules.budget_planning import service as svc

        src = inspect.getsource(svc.update_budget_plan_status)
        assert "_ensure_cost_center_for_approved_plan" in src

    def test_approved_budget_plan_creates_cost_center(self) -> None:
        from app.modules.budget_planning import service as svc
        from app.modules.university_core.tenant_entity_service import (
            create_entity_for_tenant,
            list_entities_for_tenant,
        )

        tenant_id = 50122
        _reset_week12_state(tenant_id)

        plan = create_entity_for_tenant(
            "budget_plans",
            {
                "department_id": "SCIENCE",
                "fiscal_year": 2026,
                "total_amount": 5000.0,
                "currency": "USD",
                "status": "draft",
            },
            tenant_id,
        )
        plan_id = int(plan["id"])

        first = svc.update_budget_plan_status(tenant_id, plan_id, "submitted")
        assert first is not None
        assert first["status"] == "submitted"

        second = svc.update_budget_plan_status(tenant_id, plan_id, "approved")
        assert second is not None
        assert second["status"] == "approved"

        cost_centers = list_entities_for_tenant("cost_centers", tenant_id)
        expected_code = "BP-SCIENCE-2026"
        matched = [row for row in cost_centers if str(row.get("code") or "") == expected_code]
        assert matched, "Approving budget plan must auto-create mapped cost center"


# ---------------------------------------------------------------------------
# W12.3 – expense_controls budget guard
# ---------------------------------------------------------------------------


class TestExpenseControlsBudgetGuard:
    def test_source_contains_budget_limit_guard(self) -> None:
        import inspect

        from app.modules.expense_controls import service as svc

        src = inspect.getsource(svc.create_expense_record)
        assert "Expense exceeds cost center budget_limit" in src

    def test_expense_overspend_is_blocked_and_signal_emitted(self) -> None:
        from app.modules.expense_controls import service as svc

        tenant_id = 50123
        payload = {
            "cost_center_id": 10,
            "category": "equipment",
            "amount": 120.0,
            "currency": "USD",
            "status": "pending",
        }

        def fake_list(name: str, _tid: int) -> list[dict]:
            if name == "cost_centers":
                return [
                    {
                        "id": 10,
                        "name": "CC",
                        "code": "CC-1",
                        "department_id": "FIN",
                        "budget_limit": 100.0,
                        "currency": "USD",
                        "active": True,
                        "tenant_id": tenant_id,
                    }
                ]
            if name == "expense_records":
                return []
            return []

        with (
            patch("app.modules.expense_controls.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.expense_controls.service.create_entity_for_tenant") as create_mock,
            patch("app.modules.expense_controls.service.EventPublisher") as pub_cls,
        ):
            publisher = MagicMock()
            pub_cls.return_value = publisher
            with pytest.raises(ValueError, match="budget_limit"):
                svc.create_expense_record(payload, tenant_id)

        create_mock.assert_not_called()
        publisher.publish_event.assert_called_once()

    def test_expense_within_budget_is_created(self) -> None:
        from app.modules.expense_controls import service as svc

        tenant_id = 50124
        payload = {
            "cost_center_id": 11,
            "category": "office",
            "amount": 40.0,
            "currency": "USD",
            "status": "pending",
        }

        created_record = {
            "id": 1,
            **payload,
            "tenant_id": tenant_id,
        }

        def fake_list(name: str, _tid: int) -> list[dict]:
            if name == "cost_centers":
                return [
                    {
                        "id": 11,
                        "name": "CC",
                        "code": "CC-2",
                        "department_id": "OPS",
                        "budget_limit": 100.0,
                        "currency": "USD",
                        "active": True,
                        "tenant_id": tenant_id,
                    }
                ]
            if name == "expense_records":
                return [{"id": 90, "cost_center_id": 11, "amount": 30.0, "status": "approved"}]
            return []

        with (
            patch("app.modules.expense_controls.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.expense_controls.service.create_entity_for_tenant", return_value=created_record),
            patch("app.modules.expense_controls.service.EventPublisher") as pub_cls,
        ):
            publisher = MagicMock()
            pub_cls.return_value = publisher
            result = svc.create_expense_record(payload, tenant_id)

        assert result["id"] == 1
        assert result["amount"] == 40.0
        publisher.publish_event.assert_not_called()
