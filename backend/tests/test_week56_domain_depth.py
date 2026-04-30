"""Week 56 domain-depth tests: asset_inventory — condemned cap + write-off risk alert."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Test 1: Cap dict structure
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_asset_category_max_condemned_dict_structure():
    from app.modules.asset_inventory.service import _ASSET_CATEGORY_MAX_CONDEMNED

    assert isinstance(_ASSET_CATEGORY_MAX_CONDEMNED, dict)
    assert len(_ASSET_CATEGORY_MAX_CONDEMNED) >= 2
    for k, v in _ASSET_CATEGORY_MAX_CONDEMNED.items():
        assert isinstance(k, str) and len(k) > 0
        assert isinstance(v, int) and v > 0


# ---------------------------------------------------------------------------
# Test 2: Frozenset constants
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_condemned_and_writeoff_risk_statuses_are_frozensets():
    from app.modules.asset_inventory.service import (
        _CONDEMNED_ASSET_STATUSES,
        _WRITEOFF_RISK_STATUSES,
    )

    assert isinstance(_CONDEMNED_ASSET_STATUSES, frozenset)
    assert isinstance(_WRITEOFF_RISK_STATUSES, frozenset)
    assert len(_CONDEMNED_ASSET_STATUSES) >= 1
    assert len(_WRITEOFF_RISK_STATUSES) >= 1
    assert all(isinstance(s, str) for s in _CONDEMNED_ASSET_STATUSES)
    assert all(isinstance(s, str) for s in _WRITEOFF_RISK_STATUSES)


# ---------------------------------------------------------------------------
# Test 3: create_asset_item raises when condemned cap reached
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_asset_item_raises_when_condemned_cap_reached(monkeypatch):
    from app.modules.asset_inventory import service
    from app.modules.asset_inventory.schemas import AssetItemCreateSchema

    # Use a category that has a cap
    category = next(iter(service._ASSET_CATEGORY_MAX_CONDEMNED))
    cap = service._ASSET_CATEGORY_MAX_CONDEMNED[category]
    condemned_status = next(iter(service._CONDEMNED_ASSET_STATUSES))

    # Simulate already-at-cap condemned items
    fake_items = [
        {"category": category, "condition": condemned_status, "status": "active", "id": i}
        for i in range(cap)
    ]

    monkeypatch.setattr(
        service, "list_entities_for_tenant",
        lambda entity, tenant_id: fake_items,
    )

    request = AssetItemCreateSchema(
        asset_code="ASSET-W56",
        name="Test Asset W56",
        category=category,
        location="Building A",
        condition=condemned_status,
        purchase_year=2020,
        status="active",
    )

    with pytest.raises(ValueError, match="condemned asset cap reached for category"):
        service.create_asset_item(tenant_id=1, request=request, actor="test")


# ---------------------------------------------------------------------------
# Test 4: _ensure_asset_condemned_risk_alert is idempotent
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ensure_asset_condemned_risk_alert_is_idempotent(monkeypatch):
    from app.modules.asset_inventory import service

    calls_to_create: list = []
    event_mock = MagicMock()

    monkeypatch.setattr(
        service, "list_entities_for_tenant",
        lambda entity, tenant_id: (
            [{"integration_source": "asset_condemned_queue", "source_entity_id": "99"}]
            if entity == "asset_condemned_risk_alerts"
            else []
        ),
    )
    monkeypatch.setattr(
        service, "create_entity_for_tenant",
        lambda entity, data, tenant_id: calls_to_create.append((entity, data)) or data,
    )

    with patch(
        "app.platform.events.publisher.EventPublisher.publish_event",
        event_mock,
    ):
        service._ensure_asset_condemned_risk_alert(
            tenant_id=1,
            asset_id=99,
            asset_data={"asset_code": "A99", "category": "it_equipment", "condition": "condemned"},
        )

    # Already exists → no new create, no event emitted
    assert len(calls_to_create) == 0
    event_mock.assert_not_called()
