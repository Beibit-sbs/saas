"""XCVII - Budget Planning Service Hardening (canonical 10-step hooks).

Verifies:
1. create_budget_plan uses canonical EventPublisher constructor and records metric.
2. update_budget_plan_status uses canonical EventPublisher constructor and records metric.
3. create_budget_allocation survives outcome hook failure and still records metric.
4. update_budget_plan_status blocks invalid transitions (guard remains fail-closed).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.modules.budget_planning import service as svc

MODULE = "app.modules.budget_planning.service"


def _plan(*, status: str = "draft") -> dict[str, object]:
    return {
        "id": 10,
        "department_id": "FIN",
        "fiscal_year": 2026,
        "total_amount": 100000.0,
        "currency": "USD",
        "status": status,
    }


def test_create_budget_plan_uses_canonical_event_publisher_and_metric() -> None:
    metrics: list[tuple[int, str, int]] = []

    def _capture_metric(tenant_id: int, metric: str, value: int = 1) -> None:
        metrics.append((tenant_id, metric, value))

    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[]),
        patch(f"{MODULE}.create_entity_for_tenant", return_value=_plan(status="draft")),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
            patch(f"{MODULE}._metric", side_effect=_capture_metric),
        patch(f"{MODULE}.log_admin_action"),
        patch("app.modules.brain_core.service.brain_core_service"),
    ):
        result = svc.create_budget_plan(
            {
                "department_id": "FIN",
                "fiscal_year": 2026,
                "total_amount": 100000.0,
                "status": "draft",
            },
            tenant_id=1,
            actor="admin@test.com",
        )

    assert int(result["id"]) == 10
    mock_ep.assert_called_once_with()
    mock_ep.return_value.publish_event.assert_called_once()
    assert (1, "budget_plans_created", 1) in metrics


def test_update_budget_plan_status_uses_canonical_event_publisher_and_metric() -> None:
    rows = [_plan(status="draft")]
    metrics: list[tuple[int, str, int]] = []

    def _capture_metric(tenant_id: int, metric: str, value: int = 1) -> None:
        metrics.append((tenant_id, metric, value))

    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=rows),
        patch(
            f"{MODULE}.update_entity_for_tenant",
            return_value={**rows[0], "status": "submitted"},
        ),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
            patch(f"{MODULE}._metric", side_effect=_capture_metric),
        patch(f"{MODULE}.log_admin_action"),
        patch("app.modules.brain_core.service.brain_core_service"),
    ):
        updated = svc.update_budget_plan_status(
            tenant_id=1,
            plan_id=10,
            status="submitted",
            actor="admin@test.com",
        )

    assert updated is not None
    assert updated["status"] == "submitted"
    mock_ep.assert_called_once_with()
    mock_ep.return_value.publish_event.assert_called_once()
    assert (1, "budget_plan_status_transitions", 1) in metrics


def test_create_budget_allocation_survives_outcome_failure_and_records_metric() -> None:
    metrics: list[tuple[int, str, int]] = []

    def _capture_metric(tenant_id: int, metric: str, value: int = 1) -> None:
        metrics.append((tenant_id, metric, value))

    def _list(entity: str, tenant_id: int) -> list[dict[str, object]]:
        if entity == "budget_plans":
            return [_plan(status="approved")]
        if entity == "budget_allocations":
            return []
        return []

    created = {
        "id": 99,
        "plan_id": 10,
        "category": "equipment",
        "allocated_amount": 10000.0,
        "spent_amount": 1000.0,
    }

    with (
        patch(f"{MODULE}.list_entities_for_tenant", side_effect=_list),
        patch(f"{MODULE}.create_entity_for_tenant", return_value=created),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
        patch(f"{MODULE}._metric", side_effect=_capture_metric),
        patch(f"{MODULE}.log_admin_action"),
        patch("app.modules.brain_core.service.brain_core_service") as mock_brain,
    ):
        mock_brain.record_dispatch_outcome.side_effect = RuntimeError("brain down")
        result = svc.create_budget_allocation(
            {
                "plan_id": 10,
                "category": "equipment",
                "allocated_amount": 10000.0,
                "spent_amount": 1000.0,
            },
            tenant_id=1,
            actor="admin@test.com",
        )

    assert int(result["id"]) == 99
    mock_ep.assert_called_once_with()
    mock_ep.return_value.publish_event.assert_called_once()
    assert (1, "budget_allocations_created", 1) in metrics


def test_update_budget_plan_status_rejects_invalid_transition_fail_closed() -> None:
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[_plan(status="draft")]):
        with pytest.raises(ValueError, match="Invalid budget plan transition"):
            svc.update_budget_plan_status(
                tenant_id=1,
                plan_id=10,
                status="approved",
                actor="admin@test.com",
            )
