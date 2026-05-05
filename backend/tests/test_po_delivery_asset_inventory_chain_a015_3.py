from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.procurement.schemas import ContractStatusUpdateSchema
from app.modules.procurement.service import (
    _ensure_asset_inventory_registration_for_po_delivery,
    update_contract_status,
)
from app.modules.university_core.tenant_entity_api import list_entities_for_tenant as api_list
from app.modules.university_core.tenant_entity_service import create_entity_for_tenant


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


def _make_contract(*, tenant_id: int, contract_code: str, status: str = "APPROVED") -> dict:
    _clear_entity("procurement_contracts", tenant_id)
    return create_entity_for_tenant(
        "procurement_contracts",
        {
            "contract_code": contract_code,
            "vendor_code": f"V-{tenant_id}",
            "title": f"Delivered asset flow {contract_code}",
            "risk_score": 0.1,
            "sla_target_met": True,
            "status": status,
        },
        tenant_id,
    )


def test_delivered_contract_creates_asset_inventory_item() -> None:
    tenant_id = 51001
    _clear_entity("asset_inventory_items", tenant_id)
    contract = _make_contract(tenant_id=tenant_id, contract_code="CON-A0153-001", status="PO_ISSUED")

    result = update_contract_status(
        tenant_id,
        int(contract["id"]),
        ContractStatusUpdateSchema(status="DELIVERED"),
        "asset-admin",
    )

    assert result is not None
    assert result.status == "DELIVERED"
    items = api_list("asset_inventory_items", tenant_id)
    matching = [item for item in items if str(item.get("asset_code") or "") == "PROC-CON-A0153-001"]
    assert len(matching) == 1


def test_duplicate_delivery_ensure_does_not_duplicate_asset() -> None:
    tenant_id = 51002
    _clear_entity("asset_inventory_items", tenant_id)
    contract = _make_contract(tenant_id=tenant_id, contract_code="CON-A0153-002", status="DELIVERED")

    first = _ensure_asset_inventory_registration_for_po_delivery(contract, tenant_id, "asset-admin")
    second = _ensure_asset_inventory_registration_for_po_delivery(contract, tenant_id, "asset-admin")

    items = api_list("asset_inventory_items", tenant_id)
    matching = [item for item in items if str(item.get("asset_code") or "") == "PROC-CON-A0153-002"]
    assert len(matching) == 1
    assert first["created"] is True
    assert second["created"] is False


def test_po_issued_but_not_delivered_does_not_create_asset() -> None:
    tenant_id = 51003
    _clear_entity("asset_inventory_items", tenant_id)
    contract = _make_contract(tenant_id=tenant_id, contract_code="CON-A0153-003", status="APPROVED")

    result = update_contract_status(
        tenant_id,
        int(contract["id"]),
        ContractStatusUpdateSchema(status="PO_ISSUED"),
        "asset-admin",
    )

    assert result is not None
    assert result.status == "PO_ISSUED"
    items = api_list("asset_inventory_items", tenant_id)
    assert [item for item in items if "CON-A0153-003" in str(item.get("asset_code") or "")] == []


def test_rejected_contract_does_not_create_asset() -> None:
    tenant_id = 51004
    _clear_entity("asset_inventory_items", tenant_id)
    contract = _make_contract(tenant_id=tenant_id, contract_code="CON-A0153-004", status="SUBMITTED")

    result = update_contract_status(
        tenant_id,
        int(contract["id"]),
        ContractStatusUpdateSchema(status="REJECTED"),
        "asset-admin",
    )

    assert result is not None
    assert result.status == "REJECTED"
    items = api_list("asset_inventory_items", tenant_id)
    assert [item for item in items if "CON-A0153-004" in str(item.get("asset_code") or "")] == []


def test_missing_tenant_id_fails_closed() -> None:
    contract = {"id": 1, "contract_code": "CON-A0153-005", "status": "DELIVERED"}

    with pytest.raises(DomainValidationError, match="tenant_id is required"):
        _ensure_asset_inventory_registration_for_po_delivery(contract, 0, "asset-admin")


def test_cross_tenant_delivery_asset_creation_is_isolated() -> None:
    tenant_a = 51005
    tenant_b = 51006
    _clear_entity("asset_inventory_items", tenant_a)
    _clear_entity("asset_inventory_items", tenant_b)
    contract_a = _make_contract(tenant_id=tenant_a, contract_code="CON-A0153-006", status="DELIVERED")
    contract_b = _make_contract(tenant_id=tenant_b, contract_code="CON-A0153-006", status="DELIVERED")

    _ensure_asset_inventory_registration_for_po_delivery(contract_a, tenant_a, "asset-admin")
    _ensure_asset_inventory_registration_for_po_delivery(contract_b, tenant_b, "asset-admin")

    items_a = api_list("asset_inventory_items", tenant_a)
    items_b = api_list("asset_inventory_items", tenant_b)
    assert len([item for item in items_a if str(item.get("asset_code") or "") == "PROC-CON-A0153-006"]) == 1
    assert len([item for item in items_b if str(item.get("asset_code") or "") == "PROC-CON-A0153-006"]) == 1
    assert str(items_a[0].get("tenant_id")) != str(items_b[0].get("tenant_id"))


def test_asset_creation_emits_procurement_asset_lineage_event() -> None:
    tenant_id = 51007
    _clear_entity("asset_inventory_items", tenant_id)
    contract = _make_contract(tenant_id=tenant_id, contract_code="CON-A0153-007", status="PO_ISSUED")

    with patch("app.modules.procurement.service.EventPublisher") as mock_cls:
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub
        result = update_contract_status(
            tenant_id,
            int(contract["id"]),
            ContractStatusUpdateSchema(status="DELIVERED"),
            "asset-admin",
        )

    assert result is not None
    event_types = [call.kwargs.get("event_type") for call in mock_pub.publish_event.call_args_list]
    assert "procurement.delivered" in event_types
    assert "procurement.asset_created" in event_types

    asset_call = next(
        call for call in mock_pub.publish_event.call_args_list if call.kwargs.get("event_type") == "procurement.asset_created"
    )
    payload = asset_call.kwargs["payload_json"]
    assert payload["contract_id"] == int(contract["id"])
    assert payload["contract_code"] == "CON-A0153-007"
    assert payload["asset_code"] == "PROC-CON-A0153-007"
    assert payload["delivery_status"] == "DELIVERED"