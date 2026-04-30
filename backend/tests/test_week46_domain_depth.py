"""W46 domain depth tests — budget_planning module."""
from __future__ import annotations

import pytest

from app.modules.budget_planning.service import (
    _ACTIVE_PLAN_STATUSES,
    _BUDGET_PLAN_STATUS_MAX_ACTIVE,
    _OVERRUN_RISK_STATUSES,
    create_budget_plan,
    _ensure_overrun_alert_record,
)


def test_budget_plan_status_cap_dict_structure():
    """Cap dict covers expected statuses with positive caps."""
    assert isinstance(_BUDGET_PLAN_STATUS_MAX_ACTIVE, dict)
    for key, val in _BUDGET_PLAN_STATUS_MAX_ACTIVE.items():
        assert isinstance(key, str)
        assert isinstance(val, int) and val > 0


def test_active_plan_statuses_and_overrun_risk_statuses():
    """Frozensets are non-empty, disjoint, and contain expected members."""
    assert isinstance(_ACTIVE_PLAN_STATUSES, frozenset)
    assert isinstance(_OVERRUN_RISK_STATUSES, frozenset)
    assert "draft" in _ACTIVE_PLAN_STATUSES
    assert "submitted" in _ACTIVE_PLAN_STATUSES
    assert "rejected" in _OVERRUN_RISK_STATUSES
    assert _ACTIVE_PLAN_STATUSES.isdisjoint(_OVERRUN_RISK_STATUSES)


def test_create_budget_plan_raises_when_cap_reached(monkeypatch):
    """create_budget_plan raises ValueError when active plan cap is filled."""
    cap = _BUDGET_PLAN_STATUS_MAX_ACTIVE.get("draft", 50)
    fake_plans = [{"status": "draft"} for _ in range(cap)]

    monkeypatch.setattr(
        "app.modules.budget_planning.service.list_entities_for_tenant",
        lambda entity, tid: fake_plans if entity == "budget_plans" else [],
    )
    monkeypatch.setattr(
        "app.modules.budget_planning.service.create_entity_for_tenant",
        lambda *a, **kw: {},
    )

    with pytest.raises(ValueError, match="cap reached"):
        create_budget_plan({"department_id": "CS", "fiscal_year": 2026, "total_amount": 10000.0, "status": "draft"}, tenant_id=1)


def test_ensure_overrun_alert_record_is_idempotent(monkeypatch):
    """_ensure_overrun_alert_record does not create a duplicate if one exists."""
    existing = [
        {
            "integration_source": "budget_overrun_queue",
            "source_entity_id": "7",
        }
    ]
    created: list = []

    monkeypatch.setattr(
        "app.modules.budget_planning.service.list_entities_for_tenant",
        lambda entity, tid: existing if entity == "budget_overrun_alerts" else [],
    )
    monkeypatch.setattr(
        "app.modules.budget_planning.service.create_entity_for_tenant",
        lambda entity, payload, tid: created.append(payload) or {},
    )

    _ensure_overrun_alert_record(plan_id=7, tenant_id=1)
    assert len(created) == 0
