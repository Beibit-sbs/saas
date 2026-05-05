"""W91 — procurement: DELIVERED requires asset_inventory registration (fail-closed)."""
from __future__ import annotations

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.procurement.schemas import ContractStatusUpdateSchema
from app.modules.procurement.service import update_contract_status



def _make_contract(*, contract_code: str = "C-101", status: str = "APPROVED") -> dict:
    return {
        "id": 1,
        "tenant_id": "1",
        "contract_code": contract_code,
        "vendor_code": "V-1",
        "title": "Campus Lab Equipment",
        "status": status,
        "risk_score": 0.2,
        "sla_target_met": True,
    }



def test_w91_guard_function_exists_and_callable():
    from app.modules.procurement.service import _ensure_asset_inventory_registration_for_po_delivery

    assert callable(_ensure_asset_inventory_registration_for_po_delivery)



def test_w91_blocked_when_contract_code_missing(monkeypatch):
    contract = _make_contract(contract_code="", status="PO_ISSUED")

    def _list(entity_name, _tenant_id):
        if entity_name == "procurement_contracts":
            return [contract]
        return []

    monkeypatch.setattr("app.modules.procurement.service.list_entities_for_tenant", _list)

    with pytest.raises(DomainValidationError, match="contract_code is missing"):
        update_contract_status(
            tenant_id=1,
            contract_id=1,
            request=ContractStatusUpdateSchema(status="DELIVERED"),
            actor="test",
        )



def test_w91_blocked_when_asset_inventory_lookup_fails(monkeypatch):
    contract = _make_contract(status="PO_ISSUED")

    def _list(entity_name, _tenant_id):
        if entity_name == "procurement_contracts":
            return [contract]
        if entity_name == "asset_inventory_items":
            raise RuntimeError("asset db unavailable")
        return []

    monkeypatch.setattr("app.modules.procurement.service.list_entities_for_tenant", _list)

    with pytest.raises(DomainValidationError, match="asset_inventory lookup failed"):
        update_contract_status(
            tenant_id=1,
            contract_id=1,
            request=ContractStatusUpdateSchema(status="DELIVERED"),
            actor="test",
        )



def test_w91_delivered_allowed_when_asset_already_registered(monkeypatch):
    contract = _make_contract(contract_code="C-111", status="PO_ISSUED")
    updated_contract = {**contract, "status": "DELIVERED", "tenant_id": "1"}

    def _list(entity_name, _tenant_id):
        if entity_name == "procurement_contracts":
            return [contract]
        if entity_name == "asset_inventory_items":
            return [{"id": 77, "asset_code": "PROC-C-111", "tenant_id": "1"}]
        return []

    monkeypatch.setattr("app.modules.procurement.service.list_entities_for_tenant", _list)
    monkeypatch.setattr("app.modules.procurement.service.update_entity_for_tenant", lambda *a, **k: updated_contract)
    monkeypatch.setattr("app.modules.procurement.service.log_admin_action", lambda **kw: None)

    result = update_contract_status(
        tenant_id=1,
        contract_id=1,
        request=ContractStatusUpdateSchema(status="DELIVERED"),
        actor="test",
    )
    assert result.status == "DELIVERED"


def test_w91_delivered_creates_asset_when_missing(monkeypatch):
    contract = _make_contract(contract_code="C-121", status="PO_ISSUED")
    updated_contract = {**contract, "status": "DELIVERED", "tenant_id": "1"}

    calls: dict[str, int] = {"create_asset": 0}

    def _list(entity_name, _tenant_id):
        if entity_name == "procurement_contracts":
            return [contract]
        if entity_name == "asset_inventory_items":
            return []
        return []

    def _fake_create_asset_item(*, tenant_id, request, actor):
        calls["create_asset"] += 1
        assert tenant_id == 1
        assert request.asset_code == "PROC-C-121"
        assert actor == "test"
        return {"id": 99}

    monkeypatch.setattr("app.modules.procurement.service.list_entities_for_tenant", _list)
    monkeypatch.setattr("app.modules.procurement.service.update_entity_for_tenant", lambda *a, **k: updated_contract)
    monkeypatch.setattr("app.modules.procurement.service.log_admin_action", lambda **kw: None)
    monkeypatch.setattr("app.modules.procurement.service.create_asset_item", _fake_create_asset_item, raising=False)

    # monkeypatch import target by injecting into module globals
    import app.modules.procurement.service as svc
    monkeypatch.setattr(svc, "create_asset_item", _fake_create_asset_item, raising=False)

    # Ensure helper uses patched symbol by patching inside function import path fallback:
    # easiest path is monkeypatching module used during runtime import.
    import app.modules.asset_inventory.service as asset_service
    monkeypatch.setattr(asset_service, "create_asset_item", _fake_create_asset_item)

    result = update_contract_status(
        tenant_id=1,
        contract_id=1,
        request=ContractStatusUpdateSchema(status="DELIVERED"),
        actor="test",
    )

    assert result.status == "DELIVERED"
    assert calls["create_asset"] == 1



def test_w91_blocked_when_asset_creation_fails(monkeypatch):
    contract = _make_contract(contract_code="C-131", status="PO_ISSUED")

    def _list(entity_name, _tenant_id):
        if entity_name == "procurement_contracts":
            return [contract]
        if entity_name == "asset_inventory_items":
            return []
        return []

    def _fake_create_asset_item(*args, **kwargs):
        raise RuntimeError("asset write failed")

    monkeypatch.setattr("app.modules.procurement.service.list_entities_for_tenant", _list)
    import app.modules.asset_inventory.service as asset_service
    monkeypatch.setattr(asset_service, "create_asset_item", _fake_create_asset_item)

    with pytest.raises(DomainValidationError, match="asset inventory registration failed"):
        update_contract_status(
            tenant_id=1,
            contract_id=1,
            request=ContractStatusUpdateSchema(status="DELIVERED"),
            actor="test",
        )



def test_w91_non_delivered_transition_skips_asset_inventory_lookup(monkeypatch):
    contract = _make_contract(status="SUBMITTED")
    updated_contract = {**contract, "status": "APPROVED", "tenant_id": "1"}
    calls: list[str] = []

    def _list(entity_name, _tenant_id):
        calls.append(entity_name)
        if entity_name == "procurement_contracts":
            return [contract]
        if entity_name == "procurement_vendors":
            return [{"vendor_code": "V-1", "sla_breach_rate": 0.1}]
        if entity_name == "asset_inventory_items":
            raise AssertionError("asset_inventory lookup must not run for APPROVED transition")
        return []

    monkeypatch.setattr("app.modules.procurement.service.list_entities_for_tenant", _list)
    monkeypatch.setattr("app.modules.procurement.service.update_entity_for_tenant", lambda *a, **k: updated_contract)
    monkeypatch.setattr("app.modules.procurement.service.log_admin_action", lambda **kw: None)

    result = update_contract_status(
        tenant_id=1,
        contract_id=1,
            request=ContractStatusUpdateSchema(status="APPROVED"),
        actor="test",
    )
    assert result.status == "APPROVED"
    assert "asset_inventory_items" not in calls



def test_w91_error_message_contains_contract_code(monkeypatch):
    contract = _make_contract(contract_code="C-141", status="PO_ISSUED")

    def _list(entity_name, _tenant_id):
        if entity_name == "procurement_contracts":
            return [contract]
        if entity_name == "asset_inventory_items":
            return []
        return []

    def _fake_create_asset_item(*args, **kwargs):
        raise RuntimeError("asset write failed")

    monkeypatch.setattr("app.modules.procurement.service.list_entities_for_tenant", _list)
    import app.modules.asset_inventory.service as asset_service
    monkeypatch.setattr(asset_service, "create_asset_item", _fake_create_asset_item)

    with pytest.raises(DomainValidationError) as exc_info:
        update_contract_status(
            tenant_id=1,
            contract_id=1,
            request=ContractStatusUpdateSchema(status="DELIVERED"),
            actor="test",
        )

    assert "C-141" in str(exc_info.value)
