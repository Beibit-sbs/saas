"""Phase V-V2: Expense controls module tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.modules.expense_controls import service as expense_service
from tests.conftest import ADMIN_HEADERS, client as test_client


# ---------------------------------------------------------------------------
# Service-level unit tests
# ---------------------------------------------------------------------------


def test_list_expense_records_empty(monkeypatch) -> None:
    monkeypatch.setattr(expense_service, "list_entities_for_tenant", lambda name, tid: [])
    result = expense_service.list_expense_records(tenant_id=1)
    assert result == []


def test_list_expense_records_filter_by_cost_center(monkeypatch) -> None:
    rows = [
        {
            "id": 1,
            "cost_center_id": 10,
            "category": "office",
            "amount": 500.0,
            "currency": "USD",
            "status": "pending",
            "description": None,
            "payroll_ref": None,
            "tenant_id": 1,
        },
        {
            "id": 2,
            "cost_center_id": 20,
            "category": "travel",
            "amount": 1200.0,
            "currency": "USD",
            "status": "approved",
            "description": None,
            "payroll_ref": None,
            "tenant_id": 1,
        },
    ]
    monkeypatch.setattr(expense_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = expense_service.list_expense_records(tenant_id=1, cost_center_id=10)
    assert len(result) == 1
    assert result[0]["cost_center_id"] == 10


def test_list_expense_records_filter_by_status(monkeypatch) -> None:
    rows = [
        {
            "id": 1,
            "cost_center_id": 10,
            "category": "office",
            "amount": 500.0,
            "currency": "USD",
            "status": "pending",
            "description": None,
            "payroll_ref": None,
            "tenant_id": 1,
        },
        {
            "id": 2,
            "cost_center_id": 20,
            "category": "travel",
            "amount": 1200.0,
            "currency": "USD",
            "status": "approved",
            "description": None,
            "payroll_ref": None,
            "tenant_id": 1,
        },
    ]
    monkeypatch.setattr(expense_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = expense_service.list_expense_records(tenant_id=1, status="approved")
    assert len(result) == 1
    assert result[0]["status"] == "approved"


def test_create_expense_record_no_signal(monkeypatch) -> None:
    created = {
        "id": 5,
        "cost_center_id": 10,
        "category": "office",
        "amount": 300.0,
        "currency": "USD",
        "status": "pending",
        "description": None,
        "payroll_ref": None,
        "tenant_id": 1,
    }
    cc_row = {
        "id": 10,
        "name": "Admin CC",
        "code": "ADM-01",
        "department_id": None,
        "budget_limit": 1000.0,
        "currency": "USD",
        "active": True,
        "tenant_id": 1,
    }

    def fake_list(name: str, tid: int) -> list:
        if name == "cost_centers":
            return [cc_row]
        return []

    monkeypatch.setattr(expense_service, "list_entities_for_tenant", fake_list)
    monkeypatch.setattr(expense_service, "create_entity_for_tenant", lambda name, data, tid: created)

    with patch("app.modules.expense_controls.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        record = expense_service.create_expense_record(
            {"cost_center_id": 10, "category": "office", "amount": 300.0, "status": "pending"},
            tenant_id=1,
        )

    assert record["id"] == 5
    publisher.publish_event.assert_not_called()


def test_create_expense_record_budget_exceeded_fires_signal(monkeypatch) -> None:
    created = {
        "id": 6,
        "cost_center_id": 10,
        "category": "equipment",
        "amount": 1500.0,
        "currency": "USD",
        "status": "pending",
        "description": None,
        "payroll_ref": None,
        "tenant_id": 1,
    }
    cc_row = {
        "id": 10,
        "name": "Tech CC",
        "code": "TECH-01",
        "department_id": None,
        "budget_limit": 1000.0,
        "currency": "USD",
        "active": True,
        "tenant_id": 1,
    }

    def fake_list(name: str, tid: int) -> list:
        if name == "cost_centers":
            return [cc_row]
        return []

    monkeypatch.setattr(expense_service, "list_entities_for_tenant", fake_list)
    monkeypatch.setattr(expense_service, "create_entity_for_tenant", lambda name, data, tid: created)

    with patch("app.modules.expense_controls.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        with pytest.raises(ValueError, match="budget_limit"):
            expense_service.create_expense_record(
                {"cost_center_id": 10, "category": "equipment", "amount": 1500.0, "status": "pending"},
                tenant_id=1,
            )

    publisher.publish_event.assert_called_once()
    call_kwargs = publisher.publish_event.call_args.kwargs
    assert call_kwargs["event_type"] == "finance.expense.budget_exceeded"
    assert call_kwargs["tenant_id"] == 1
    assert call_kwargs["payload_json"]["amount"] == 1500.0
    assert call_kwargs["payload_json"]["budget_limit"] == 1000.0


def test_get_expense_brain_context_empty(monkeypatch) -> None:
    monkeypatch.setattr(expense_service, "list_entities_for_tenant", lambda name, tid: [])
    ctx = expense_service.get_expense_brain_context(tenant_id=3)
    assert ctx["module"] == "expense_controls"
    assert ctx["tenant_id"] == 3
    assert ctx["total_expenses"] == 0
    assert ctx["budget_exceeded_alerts"] == 0
    assert ctx["risk_level"] == "low"


def test_get_expense_brain_context_high_risk(monkeypatch) -> None:
    cc_row = {
        "id": 10,
        "name": "CC",
        "code": "C1",
        "department_id": None,
        "budget_limit": 500.0,
        "currency": "USD",
        "active": True,
        "tenant_id": 3,
    }
    expense_rows = [
        {
            "id": 1,
            "cost_center_id": 10,
            "category": "travel",
            "amount": 800.0,
            "currency": "USD",
            "status": "pending",
            "description": None,
            "payroll_ref": None,
            "tenant_id": 3,
        },
    ]

    def fake_list(name: str, tid: int) -> list:
        if name == "cost_centers":
            return [cc_row]
        return expense_rows

    monkeypatch.setattr(expense_service, "list_entities_for_tenant", fake_list)
    ctx = expense_service.get_expense_brain_context(tenant_id=3)
    assert ctx["budget_exceeded_alerts"] == 1
    assert ctx["risk_level"] == "high"


# ---------------------------------------------------------------------------
# HTTP endpoint tests
# ---------------------------------------------------------------------------


def test_http_list_expense_records_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.modules.expense_controls.service.list_expense_records",
        lambda tenant_id, cost_center_id=None, status=None: [],
    )
    resp = test_client.get("/api/admin/expense-controls/expenses", headers=dict(ADMIN_HEADERS))
    assert resp.status_code == 200
    assert resp.json()["records"] == []


def test_http_create_expense_record(monkeypatch: pytest.MonkeyPatch) -> None:
    created = {
        "id": 99,
        "cost_center_id": 10,
        "category": "office",
        "amount": 450.0,
        "currency": "USD",
        "status": "pending",
        "description": None,
        "payroll_ref": None,
        "tenant_id": 1,
    }
    monkeypatch.setattr(
        "app.modules.expense_controls.service.create_expense_record",
        lambda payload, tenant_id: created,
    )
    payload = {
        "cost_center_id": 10,
        "category": "office",
        "amount": 450.0,
        "currency": "USD",
        "status": "pending",
    }
    resp = test_client.post("/api/admin/expense-controls/expenses", json=payload, headers=dict(ADMIN_HEADERS))
    assert resp.status_code == 201
    data = resp.json()
    assert data["record"]["id"] == 99
    assert data["record"]["category"] == "office"


def test_http_get_brain_context(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = {
        "module": "expense_controls",
        "tenant_id": 1,
        "total_expenses": 5,
        "total_cost_centers": 2,
        "pending_expenses": 2,
        "approved_expenses": 3,
        "budget_exceeded_alerts": 0,
        "risk_level": "low",
    }
    monkeypatch.setattr(
        "app.modules.expense_controls.service.get_expense_brain_context",
        lambda tenant_id: ctx,
    )
    resp = test_client.get("/api/admin/expense-controls/brain-context", headers=dict(ADMIN_HEADERS))
    assert resp.status_code == 200
    data = resp.json()
    assert data["module"] == "expense_controls"
    assert data["risk_level"] == "low"
    assert data["total_expenses"] == 5
