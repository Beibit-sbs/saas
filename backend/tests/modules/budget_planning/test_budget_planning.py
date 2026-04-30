"""Phase V-V1: Budget planning module tests — plans, allocations, drift signal, brain-context."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.modules.budget_planning import service as budget_service
from tests.conftest import ADMIN_HEADERS, client as test_client


# ---------------------------------------------------------------------------
# Service-level unit tests
# ---------------------------------------------------------------------------


def test_list_budget_plans_empty(monkeypatch) -> None:
    monkeypatch.setattr(budget_service, "list_entities_for_tenant", lambda name, tid: [])
    result = budget_service.list_budget_plans(tenant_id=1)
    assert result == []


def test_list_budget_plans_filter_by_department(monkeypatch) -> None:
    rows = [
        {"id": 1, "department_id": "DEPT-A", "fiscal_year": 2026, "total_amount": 100000.0, "currency": "USD", "status": "draft", "description": None, "tenant_id": "1"},
        {"id": 2, "department_id": "DEPT-B", "fiscal_year": 2026, "total_amount": 50000.0, "currency": "USD", "status": "approved", "description": None, "tenant_id": "1"},
    ]
    monkeypatch.setattr(budget_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = budget_service.list_budget_plans(tenant_id=1, department_id="DEPT-A")
    assert len(result) == 1
    assert result[0]["department_id"] == "DEPT-A"


def test_list_budget_plans_filter_by_fiscal_year(monkeypatch) -> None:
    rows = [
        {"id": 1, "department_id": "DEPT-A", "fiscal_year": 2025, "total_amount": 80000.0, "currency": "USD", "status": "closed", "description": None, "tenant_id": "1"},
        {"id": 2, "department_id": "DEPT-A", "fiscal_year": 2026, "total_amount": 100000.0, "currency": "USD", "status": "draft", "description": None, "tenant_id": "1"},
    ]
    monkeypatch.setattr(budget_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = budget_service.list_budget_plans(tenant_id=1, fiscal_year=2026)
    assert len(result) == 1
    assert result[0]["fiscal_year"] == 2026


def test_create_budget_plan(monkeypatch) -> None:
    created = {
        "id": 10,
        "department_id": "DEPT-C",
        "fiscal_year": 2026,
        "total_amount": 200000.0,
        "currency": "USD",
        "status": "draft",
        "description": "Annual plan",
        "tenant_id": "1",
    }
    monkeypatch.setattr(budget_service, "create_entity_for_tenant", lambda name, payload, tid: created)
    result = budget_service.create_budget_plan(
        {"department_id": "DEPT-C", "fiscal_year": 2026, "total_amount": 200000.0, "status": "draft"},
        tenant_id=1,
    )
    assert result["id"] == 10
    assert result["department_id"] == "DEPT-C"


def test_create_budget_plan_rejects_non_draft_initial_status() -> None:
    with pytest.raises(ValueError, match="must be created in 'draft' status"):
        budget_service.create_budget_plan(
            {
                "department_id": "DEPT-C",
                "fiscal_year": 2026,
                "total_amount": 200000.0,
                "status": "approved",
            },
            tenant_id=1,
        )


def test_update_budget_plan_status_happy_path(monkeypatch) -> None:
    rows = [
        {
            "id": 10,
            "department_id": "DEPT-C",
            "fiscal_year": 2026,
            "total_amount": 200000.0,
            "currency": "USD",
            "status": "draft",
            "description": "Annual plan",
            "tenant_id": "1",
        }
    ]
    monkeypatch.setattr(budget_service, "list_entities_for_tenant", lambda name, tid: rows)
    monkeypatch.setattr(
        budget_service,
        "update_entity_for_tenant",
        lambda name, item_id, payload, tid: {**payload, "id": item_id, "tenant_id": "1"},
    )

    updated = budget_service.update_budget_plan_status(tenant_id=1, plan_id=10, status="submitted")

    assert updated is not None
    assert updated["status"] == "submitted"


def test_update_budget_plan_status_rejects_invalid_transition(monkeypatch) -> None:
    rows = [
        {
            "id": 10,
            "department_id": "DEPT-C",
            "fiscal_year": 2026,
            "total_amount": 200000.0,
            "currency": "USD",
            "status": "draft",
            "description": "Annual plan",
            "tenant_id": "1",
        }
    ]
    monkeypatch.setattr(budget_service, "list_entities_for_tenant", lambda name, tid: rows)

    with pytest.raises(ValueError, match="Invalid budget plan transition"):
        budget_service.update_budget_plan_status(tenant_id=1, plan_id=10, status="approved")


def test_create_budget_allocation_no_signal(monkeypatch) -> None:
    """Allocation with low drift should NOT fire a brain signal."""
    created = {
        "id": 20,
        "plan_id": 10,
        "category": "salaries",
        "allocated_amount": 50000.0,
        "spent_amount": 10000.0,  # drift 0.2 — below threshold
        "currency": "USD",
        "notes": None,
        "tenant_id": "1",
    }
    monkeypatch.setattr(budget_service, "create_entity_for_tenant", lambda name, payload, tid: created)
    monkeypatch.setattr(
        budget_service,
        "list_entities_for_tenant",
        lambda name, tid: (
            [{"id": 10, "total_amount": 100000.0, "status": "approved"}] if name == "budget_plans" else []
        ),
    )

    with patch("app.modules.budget_planning.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        record = budget_service.create_budget_allocation(
            {"plan_id": 10, "category": "salaries", "allocated_amount": 50000.0, "spent_amount": 10000.0},
            tenant_id=1,
        )

    assert record["id"] == 20
    publisher.publish_event.assert_not_called()


def test_create_budget_allocation_drift_fires_signal(monkeypatch) -> None:
    """Allocation with spent/allocated > 0.9 should fire finance.budget_drift.critical_threshold."""
    created = {
        "id": 21,
        "plan_id": 10,
        "category": "equipment",
        "allocated_amount": 10000.0,
        "spent_amount": 9500.0,  # drift 0.95 — above threshold
        "currency": "USD",
        "notes": None,
        "tenant_id": "1",
    }
    monkeypatch.setattr(budget_service, "create_entity_for_tenant", lambda name, payload, tid: created)
    monkeypatch.setattr(
        budget_service,
        "list_entities_for_tenant",
        lambda name, tid: (
            [{"id": 10, "total_amount": 100000.0, "status": "approved"}] if name == "budget_plans" else []
        ),
    )

    with patch("app.modules.budget_planning.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        record = budget_service.create_budget_allocation(
            {"plan_id": 10, "category": "equipment", "allocated_amount": 10000.0, "spent_amount": 9500.0},
            tenant_id=1,
        )

    assert record["id"] == 21
    publisher.publish_event.assert_called_once()
    call_kwargs = publisher.publish_event.call_args.kwargs
    assert call_kwargs["event_type"] == "finance.budget_drift.critical_threshold"
    assert call_kwargs["tenant_id"] == 1
    assert call_kwargs["payload_json"]["category"] == "equipment"
    assert call_kwargs["payload_json"]["drift_rate"] > 0.9


def test_get_budget_brain_context_empty(monkeypatch) -> None:
    monkeypatch.setattr(budget_service, "list_entities_for_tenant", lambda name, tid: [])
    ctx = budget_service.get_budget_brain_context(tenant_id=5)
    assert ctx["module"] == "budget_planning"
    assert ctx["tenant_id"] == 5
    assert ctx["total_plans"] == 0
    assert ctx["drift_alerts"] == 0
    assert ctx["risk_level"] == "low"


def test_get_budget_brain_context_high_risk(monkeypatch) -> None:
    plans = [
        {"id": 1, "department_id": "DEPT-A", "fiscal_year": 2026, "total_amount": 100000.0, "currency": "USD", "status": "approved", "tenant_id": "5"},
    ]
    allocations = [
        {"id": 1, "plan_id": 1, "category": "salaries", "allocated_amount": 50000.0, "spent_amount": 49000.0, "currency": "USD", "tenant_id": "5"},
        {"id": 2, "plan_id": 1, "category": "equipment", "allocated_amount": 10000.0, "spent_amount": 9600.0, "currency": "USD", "tenant_id": "5"},
    ]

    def fake_list(name: str, tid: int) -> list:
        if name == "budget_plans":
            return plans
        return allocations

    monkeypatch.setattr(budget_service, "list_entities_for_tenant", fake_list)
    ctx = budget_service.get_budget_brain_context(tenant_id=5)
    assert ctx["total_plans"] == 1
    assert ctx["drift_alerts"] >= 1
    assert ctx["risk_level"] == "high"


# ---------------------------------------------------------------------------
# HTTP endpoint tests (router level)
# ---------------------------------------------------------------------------


def test_http_list_budget_plans_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.modules.budget_planning.service.list_budget_plans",
        lambda tenant_id, department_id=None, fiscal_year=None: [],
    )
    resp = test_client.get("/api/admin/budget-planning/plans", headers=dict(ADMIN_HEADERS))
    assert resp.status_code == 200
    assert resp.json()["records"] == []


def test_http_create_budget_plan(monkeypatch: pytest.MonkeyPatch) -> None:
    created = {
        "id": 30,
        "department_id": "DEPT-X",
        "fiscal_year": 2026,
        "total_amount": 75000.0,
        "currency": "USD",
        "status": "draft",
        "description": None,
        "tenant_id": "1",
    }
    monkeypatch.setattr(
        "app.modules.budget_planning.service.create_budget_plan",
        lambda payload, tenant_id: created,
    )
    payload = {
        "department_id": "DEPT-X",
        "fiscal_year": 2026,
        "total_amount": 75000.0,
        "currency": "USD",
        "status": "draft",
    }
    resp = test_client.post("/api/admin/budget-planning/plans", json=payload, headers=dict(ADMIN_HEADERS))
    assert resp.status_code == 201
    data = resp.json()
    assert data["record"]["id"] == 30
    assert data["record"]["department_id"] == "DEPT-X"


def test_http_update_budget_plan_status_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    updated = {
        "id": 30,
        "department_id": "DEPT-X",
        "fiscal_year": 2026,
        "total_amount": 75000.0,
        "currency": "USD",
        "status": "submitted",
        "description": None,
        "tenant_id": "1",
    }
    monkeypatch.setattr(
        "app.modules.budget_planning.service.update_budget_plan_status",
        lambda tenant_id, plan_id, status: updated,
    )

    resp = test_client.patch(
        "/api/admin/budget-planning/plans/30/status",
        json={"status": "submitted"},
        headers=dict(ADMIN_HEADERS),
    )

    assert resp.status_code == 200
    assert resp.json()["record"]["status"] == "submitted"


def test_http_update_budget_plan_status_rejects_invalid_transition(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise_invalid_transition(tenant_id: int, plan_id: int, status: str) -> dict:
        raise ValueError("Invalid budget plan transition from 'draft' to 'approved'")

    monkeypatch.setattr(
        "app.modules.budget_planning.service.update_budget_plan_status",
        _raise_invalid_transition,
    )

    resp = test_client.patch(
        "/api/admin/budget-planning/plans/30/status",
        json={"status": "approved"},
        headers=dict(ADMIN_HEADERS),
    )

    assert resp.status_code == 422
    assert "Invalid budget plan transition" in resp.json()["detail"]


def test_http_get_brain_context(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = {
        "module": "budget_planning",
        "tenant_id": 1,
        "total_plans": 2,
        "total_budget": 150000.0,
        "total_allocated": 80000.0,
        "total_spent": 20000.0,
        "drift_rate": 0.25,
        "drift_alerts": 0,
        "by_status": {"draft": 1, "approved": 1},
        "risk_level": "low",
    }
    monkeypatch.setattr(
        "app.modules.budget_planning.service.get_budget_brain_context",
        lambda tenant_id: ctx,
    )
    resp = test_client.get("/api/admin/budget-planning/brain-context", headers=dict(ADMIN_HEADERS))
    assert resp.status_code == 200
    data = resp.json()
    assert data["module"] == "budget_planning"
    assert data["risk_level"] == "low"
    assert data["total_plans"] == 2
