"""Week 61 domain-depth tests: dining — meal type active cap + capacity exceeded alert."""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Test 1: Cap dict structure
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_meal_type_max_active_menus_dict_structure():
    from app.modules.dining.service import _MEAL_TYPE_MAX_ACTIVE_MENUS

    assert isinstance(_MEAL_TYPE_MAX_ACTIVE_MENUS, dict)
    assert len(_MEAL_TYPE_MAX_ACTIVE_MENUS) >= 2
    for k, v in _MEAL_TYPE_MAX_ACTIVE_MENUS.items():
        assert isinstance(k, str) and len(k) > 0
        assert isinstance(v, int) and v > 0


# ---------------------------------------------------------------------------
# Test 2: Frozenset constants
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_active_menu_statuses_and_capacity_exceeded_risk_statuses_are_frozensets():
    from app.modules.dining.service import _ACTIVE_MENU_STATUSES, _CAPACITY_EXCEEDED_RISK_STATUSES

    assert isinstance(_ACTIVE_MENU_STATUSES, frozenset)
    assert isinstance(_CAPACITY_EXCEEDED_RISK_STATUSES, frozenset)
    assert len(_ACTIVE_MENU_STATUSES) >= 1
    assert len(_CAPACITY_EXCEEDED_RISK_STATUSES) >= 1
    assert all(isinstance(s, str) for s in _ACTIVE_MENU_STATUSES)
    assert all(isinstance(s, str) for s in _CAPACITY_EXCEEDED_RISK_STATUSES)


# ---------------------------------------------------------------------------
# Test 3: create_dining_menu raises when active cap reached
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_dining_menu_raises_when_active_cap_reached(monkeypatch):
    from app.modules.dining import service

    meal_type = next(iter(service._MEAL_TYPE_MAX_ACTIVE_MENUS))
    cap = service._MEAL_TYPE_MAX_ACTIVE_MENUS[meal_type]
    active_status = next(iter(service._ACTIVE_MENU_STATUSES))

    fake_records = [
        {"meal_type": meal_type, "status": active_status, "id": i}
        for i in range(cap)
    ]

    monkeypatch.setattr(
        service, "list_entities_for_tenant",
        lambda entity, tenant_id: fake_records,
    )

    payload = {
        "menu_code": "MENU-001",
        "facility_code": "FAC-001",
        "meal_type": meal_type,
        "status": active_status,
        "capacity": 100,
        "available_capacity": 50,
    }

    with pytest.raises(ValueError, match="active menu cap exceeded"):
        service.create_dining_menu(payload=payload, tenant_id=1)


# ---------------------------------------------------------------------------
# Test 4: _ensure_capacity_alert_record is idempotent
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ensure_capacity_alert_record_is_idempotent(monkeypatch):
    from app.modules.dining import service

    calls_to_create: list = []

    monkeypatch.setattr(
        service, "list_entities_for_tenant",
        lambda entity, tenant_id: (
            [{"integration_source": "dining_capacity", "source_entity_id": "77"}]
            if entity == "dining_capacity_alert_records"
            else []
        ),
    )
    monkeypatch.setattr(
        service, "create_entity_for_tenant",
        lambda entity, data, tenant_id: calls_to_create.append((entity, data)) or data,
    )

    service._ensure_capacity_alert_record(
        menu={"id": "77", "menu_code": "MENU-001", "facility_code": "FAC-001", "meal_type": "lunch"},
        tenant_id=1,
    )

    # Already exists → no new create
    assert len(calls_to_create) == 0
