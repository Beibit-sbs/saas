"""Week 62 domain-depth tests: expense_controls — budget risk detection + alert."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Test 1: Cap dict and active statuses structure
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_expense_category_max_active_dict_structure():
    from app.modules.expense_controls.service import _EXPENSE_CATEGORY_MAX_ACTIVE

    assert isinstance(_EXPENSE_CATEGORY_MAX_ACTIVE, dict)
    assert len(_EXPENSE_CATEGORY_MAX_ACTIVE) >= 2
    for k, v in _EXPENSE_CATEGORY_MAX_ACTIVE.items():
        assert isinstance(k, str) and len(k) > 0
        assert isinstance(v, int) and v > 0


# ---------------------------------------------------------------------------
# Test 2: Frozenset constants for active and risk statuses
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_active_and_budget_risk_statuses_are_frozensets():
    from app.modules.expense_controls.service import _ACTIVE_STATUSES_EC, _BUDGET_RISK_STATUSES

    assert isinstance(_ACTIVE_STATUSES_EC, frozenset)
    assert isinstance(_BUDGET_RISK_STATUSES, frozenset)
    assert len(_ACTIVE_STATUSES_EC) >= 1
    assert len(_BUDGET_RISK_STATUSES) >= 1
    assert all(isinstance(s, str) for s in _ACTIVE_STATUSES_EC)
    assert all(isinstance(s, str) for s in _BUDGET_RISK_STATUSES)


# ---------------------------------------------------------------------------
# Test 3: create_expense_record raises when active cap reached
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_expense_record_raises_when_active_cap_reached(monkeypatch):
    from app.modules.expense_controls import service

    category = next(iter(service._EXPENSE_CATEGORY_MAX_ACTIVE))
    cap = service._EXPENSE_CATEGORY_MAX_ACTIVE[category]
    active_status = next(iter(service._ACTIVE_STATUSES_EC))

    fake_expense_records = [
        {"id": i, "category": category, "status": active_status, "cost_center_id": 1, "amount": 100.0}
        for i in range(cap)
    ]
    fake_cost_centers = [
        {"id": 1, "budget_limit": 10000.0, "active": True}
    ]

    def mock_list_entities(entity, tenant_id):
        if entity == "expense_records":
            return fake_expense_records
        elif entity == "cost_centers":
            return fake_cost_centers
        return []

    monkeypatch.setattr(service, "list_entities_for_tenant", mock_list_entities)

    payload = {
        "cost_center_id": 1,
        "category": category,
        "status": active_status,
        "amount": 500.0,
        "currency": "USD",
    }

    with pytest.raises(ValueError, match="Active expense cap exceeded"):
        service.create_expense_record(payload=payload, tenant_id=1)


# ---------------------------------------------------------------------------
# Test 4: _ensure_budget_exceeded_risk_alert_record is idempotent + EventPublisher
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ensure_budget_exceeded_risk_alert_record_is_idempotent_with_event(monkeypatch):
    from app.modules.expense_controls import service

    calls_to_create: list = []

    # Mock: existing alert already exists
    monkeypatch.setattr(
        service, "list_entities_for_tenant",
        lambda entity, tenant_id: (
            [{"integration_source": "budget_exceeded_risk", "source_entity_id": "99"}]
            if entity == "expense_budget_exceeded_alerts"
            else []
        ),
    )
    monkeypatch.setattr(
        service, "create_entity_for_tenant",
        lambda entity, data, tenant_id: calls_to_create.append((entity, data)) or data,
    )

    # Mock: EventPublisher.publish_event
    mock_publisher = MagicMock()
    monkeypatch.setattr(
        "app.platform.events.publisher.EventPublisher.publish_event",
        mock_publisher,
    )

    service._ensure_budget_exceeded_risk_alert_record(
        tenant_id=1,
        expense_id=99,
        expense_data={
            "cost_center_id": 5,
            "category": "travel",
            "amount": 2000.0,
        },
    )

    # Alert already exists → no new create and no new event
    assert len(calls_to_create) == 0
    assert mock_publisher.call_count == 0


# ---------------------------------------------------------------------------
# Test 4b: _ensure_budget_exceeded_risk_alert_record creates alert when not exists
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ensure_budget_exceeded_risk_alert_record_creates_when_not_exists(monkeypatch):
    from app.modules.expense_controls import service

    calls_to_create: list = []

    # Mock: no existing alerts
    monkeypatch.setattr(
        service, "list_entities_for_tenant",
        lambda entity, tenant_id: [],
    )
    monkeypatch.setattr(
        service, "create_entity_for_tenant",
        lambda entity, data, tenant_id: calls_to_create.append((entity, data)) or data,
    )

    # Mock: EventPublisher.publish_event
    mock_publisher = MagicMock()
    monkeypatch.setattr(
        "app.platform.events.publisher.EventPublisher.publish_event",
        mock_publisher,
    )

    service._ensure_budget_exceeded_risk_alert_record(
        tenant_id=1,
        expense_id=88,
        expense_data={
            "cost_center_id": 4,
            "category": "software",
            "amount": 3000.0,
        },
    )

    # Should create alert + publish event
    assert len(calls_to_create) == 1
    assert calls_to_create[0][0] == "expense_budget_exceeded_alerts"
    assert calls_to_create[0][1]["expense_id"] == 88
    assert calls_to_create[0][1]["integration_source"] == "budget_exceeded_risk"
    
    # Event should be published once
    assert mock_publisher.call_count == 1
    call_kwargs = mock_publisher.call_args[1]
    assert call_kwargs["event_type"] == "campus.expense_controls.budget_exceeded_risk_detected"
    assert call_kwargs["tenant_id"] == 1
