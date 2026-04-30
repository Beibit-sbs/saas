"""W70 — procurement: Cross-entity vendor SLA breach guard on contract approval.

Real-world problem: update_contract_status() allowed APPROVED transition even
when the vendor has sla_breach_rate >= 0.8.  Vendor performance data existed
in the system but was never consulted during contract approval — contracts could
reach PO_ISSUED state via a chronically underperforming vendor without any
system-level guard.

Fix: Before persisting APPROVED, lookup vendor by vendor_code and raise
ValueError if vendor.sla_breach_rate >= _HIGH_RISK_SCORE_THRESHOLD (0.8).
"""
from __future__ import annotations

import pytest

from app.modules.procurement.service import (
    _HIGH_RISK_SCORE_THRESHOLD,
    update_contract_status,
)
from app.modules.procurement.schemas import ContractStatusUpdateSchema


# ---------------------------------------------------------------------------
# 1. SLA threshold constant sanity
# ---------------------------------------------------------------------------

def test_w70_sla_threshold_is_float_in_range():
    """_HIGH_RISK_SCORE_THRESHOLD must be a float between 0 and 1 exclusive."""
    assert isinstance(_HIGH_RISK_SCORE_THRESHOLD, float)
    assert 0.0 < _HIGH_RISK_SCORE_THRESHOLD < 1.0


# ---------------------------------------------------------------------------
# Helper: build monkeypatched update_contract_status environment
# ---------------------------------------------------------------------------

def _make_contract(vendor_code: str, status: str = "SUBMITTED") -> dict:
    return {
        "id": 1,
        "tenant_id": "1",
        "contract_code": "C-001",
        "vendor_code": vendor_code,
        "title": "Test Contract",
        "status": status,
        "risk_score": 0.5,
        "sla_target_met": True,
        "value": 10000.0,
        "owner_id": "proc-team",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
    }


def _make_vendor(vendor_code: str, sla_breach_rate: float) -> dict:
    return {
        "id": 10,
        "vendor_code": vendor_code,
        "name": "ACME Corp",
        "category": "it",
        "sla_breach_rate": sla_breach_rate,
        "on_time_delivery_rate": 0.9,
        "status": "active",
        "contact_name": "Jane",
    }


# ---------------------------------------------------------------------------
# 2. Approval blocked when vendor SLA breach >= threshold
# ---------------------------------------------------------------------------

def test_w70_approve_blocked_when_vendor_sla_breach_at_threshold(monkeypatch):
    """Transition SUBMITTED → APPROVED must be blocked for vendor with sla_breach_rate = 0.8."""
    contract = _make_contract("V-BAD", status="SUBMITTED")
    vendor = _make_vendor("V-BAD", sla_breach_rate=0.8)

    def mock_list(entity_name, tenant_id):
        if entity_name == "procurement_contracts":
            return [contract]
        if entity_name == "procurement_vendors":
            return [vendor]
        return []

    def mock_update(entity_name, entity_id, payload, tenant_id):
        return {**contract, **payload}

    monkeypatch.setattr("app.modules.procurement.service.list_entities_for_tenant", mock_list)
    monkeypatch.setattr("app.modules.procurement.service.update_entity_for_tenant", mock_update)

    req = ContractStatusUpdateSchema(status="APPROVED")
    with pytest.raises(ValueError, match="SLA breach rate"):
        update_contract_status(
            tenant_id=1, contract_id=1, request=req, actor="test"
        )


def test_w70_approve_blocked_when_vendor_sla_breach_above_threshold(monkeypatch):
    """Transition SUBMITTED → APPROVED must be blocked for vendor with sla_breach_rate = 0.95."""
    contract = _make_contract("V-BAD2", status="SUBMITTED")
    vendor = _make_vendor("V-BAD2", sla_breach_rate=0.95)

    def mock_list(entity_name, tenant_id):
        if entity_name == "procurement_contracts":
            return [contract]
        if entity_name == "procurement_vendors":
            return [vendor]
        return []

    def mock_update(entity_name, entity_id, payload, tenant_id):
        return {**contract, **payload}

    monkeypatch.setattr("app.modules.procurement.service.list_entities_for_tenant", mock_list)
    monkeypatch.setattr("app.modules.procurement.service.update_entity_for_tenant", mock_update)

    req = ContractStatusUpdateSchema(status="APPROVED")
    with pytest.raises(ValueError, match="Cannot approve contract"):
        update_contract_status(
            tenant_id=1, contract_id=1, request=req, actor="test"
        )


# ---------------------------------------------------------------------------
# 3. Approval allowed when vendor SLA breach below threshold
# ---------------------------------------------------------------------------

def test_w70_approve_allowed_when_vendor_sla_acceptable(monkeypatch):
    """Transition SUBMITTED → APPROVED must succeed when vendor sla_breach_rate = 0.3."""
    contract = _make_contract("V-GOOD", status="SUBMITTED")
    vendor = _make_vendor("V-GOOD", sla_breach_rate=0.3)
    updated_contract = {**contract, "status": "APPROVED", "tenant_id": "1"}

    def mock_list(entity_name, tenant_id):
        if entity_name == "procurement_contracts":
            return [contract]
        if entity_name == "procurement_vendors":
            return [vendor]
        return []

    def mock_update(entity_name, entity_id, payload, tenant_id):
        return updated_contract

    monkeypatch.setattr("app.modules.procurement.service.list_entities_for_tenant", mock_list)
    monkeypatch.setattr("app.modules.procurement.service.update_entity_for_tenant", mock_update)
    monkeypatch.setattr("app.modules.procurement.service.log_admin_action", lambda **kw: None)

    req = ContractStatusUpdateSchema(status="APPROVED")
    result = update_contract_status(
        tenant_id=1, contract_id=1, request=req, actor="test"
    )
    assert result is not None
    assert result.status == "APPROVED"


# ---------------------------------------------------------------------------
# 4. Approval not blocked when vendor not found (no vendor record)
# ---------------------------------------------------------------------------

def test_w70_approve_not_blocked_when_vendor_not_found(monkeypatch):
    """If vendor record is missing, approval must proceed (data integrity is separate concern)."""
    contract = _make_contract("V-MISSING", status="SUBMITTED")
    updated_contract = {**contract, "status": "APPROVED", "tenant_id": "1"}

    def mock_list(entity_name, tenant_id):
        if entity_name == "procurement_contracts":
            return [contract]
        return []  # no vendors

    def mock_update(entity_name, entity_id, payload, tenant_id):
        return updated_contract

    monkeypatch.setattr("app.modules.procurement.service.list_entities_for_tenant", mock_list)
    monkeypatch.setattr("app.modules.procurement.service.update_entity_for_tenant", mock_update)
    monkeypatch.setattr("app.modules.procurement.service.log_admin_action", lambda **kw: None)

    req = ContractStatusUpdateSchema(status="APPROVED")
    result = update_contract_status(
        tenant_id=1, contract_id=1, request=req, actor="test"
    )
    assert result is not None


# ---------------------------------------------------------------------------
# 5. PO_ISSUED transition not blocked by vendor SLA (only APPROVED is gated)
# ---------------------------------------------------------------------------

def test_w70_po_issued_not_blocked_by_vendor_sla(monkeypatch):
    """PO_ISSUED transition from APPROVED must not re-check vendor SLA breach rate."""
    contract = _make_contract("V-BAD3", status="APPROVED")
    vendor = _make_vendor("V-BAD3", sla_breach_rate=0.95)
    updated_contract = {**contract, "status": "PO_ISSUED", "tenant_id": "1"}

    call_log: list[str] = []

    def mock_list(entity_name, tenant_id):
        call_log.append(entity_name)
        if entity_name == "procurement_contracts":
            return [contract]
        if entity_name == "procurement_vendors":
            return [vendor]
        return []

    def mock_update(entity_name, entity_id, payload, tenant_id):
        return updated_contract

    monkeypatch.setattr("app.modules.procurement.service.list_entities_for_tenant", mock_list)
    monkeypatch.setattr("app.modules.procurement.service.update_entity_for_tenant", mock_update)
    monkeypatch.setattr("app.modules.procurement.service.log_admin_action", lambda **kw: None)
    monkeypatch.setattr(
        "app.modules.procurement.service._ensure_asset_inventory_registration_for_po_issue",
        lambda *a, **kw: None,
    )

    req = ContractStatusUpdateSchema(status="PO_ISSUED")
    result = update_contract_status(
        tenant_id=1, contract_id=1, request=req, actor="test"
    )
    assert result is not None
    # vendor lookup must NOT have been triggered (no vendor check on PO_ISSUED)
    assert "procurement_vendors" not in call_log, (
        "Vendor SLA check must only run on APPROVED transition, not PO_ISSUED"
    )
