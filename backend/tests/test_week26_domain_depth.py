"""Week 26 — Domain Depth: Asset Inventory Depreciation Method Cap + Write-Off Side Effect.

Tests:
  W26.1 - Source guard: _METHOD_MAX_ACTIVE_DEPR and _ensure_asset_writeoff_record present
  W26.2 - Exceeding active 'declining_balance' depreciation records cap returns 422
  W26.3 - Creating a depreciation record with current_value=0 auto-creates asset_writeoff_records entry
  W26.4 - Multiple _ensure_asset_writeoff_record calls for same record are idempotent
"""
from __future__ import annotations

import inspect
import uuid

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE = "/api/admin/asset-inventory"

HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="week26.assets@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["asset_inventory.read", "asset_inventory.write"],
        )
    )
}


def _reset_state() -> None:
    from app.modules.university_core import shared as university_shared

    with university_shared._state_lock:
        for key in (
            "asset_inventory_items",
            "asset_depreciation_records",
            "asset_writeoff_records",
        ):
            if key in university_shared._state.data:
                university_shared._state.data[key].clear()
                university_shared._state.counters[key] = 0


def setup_module(_: object) -> None:
    _reset_state()


def teardown_function(_: object) -> None:
    _reset_state()


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _create_asset(asset_code: str | None = None) -> dict:
    code = asset_code or f"ASSET-{_uid()}"
    payload = {
        "asset_code": code,
        "name": "Test Asset",
        "category": "equipment",
        "location": "Building A",
        "condition": "good",
        "purchase_year": 2022,
        "status": "active",
    }
    resp = client.post(f"{BASE}/items", headers=HEADERS, json=payload)
    assert resp.status_code in (200, 201), resp.text
    return resp.json(), code


def _create_depr(asset_code: str, method: str = "straight_line", current_value: float = 1000.0) -> dict:
    payload = {
        "asset_code": asset_code,
        "depreciation_method": method,
        "original_value": 5000.0,
        "current_value": current_value,
        "depreciation_rate": 0.1,
        "status": "active",
    }
    resp = client.post(f"{BASE}/depreciation", headers=HEADERS, json=payload)
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# W26.1 – Source guard
# ---------------------------------------------------------------------------

def test_w26_source_contains_method_cap_and_writeoff_helper() -> None:
    from app.modules.asset_inventory import service as ai_service

    src = inspect.getsource(ai_service)
    assert "_METHOD_MAX_ACTIVE_DEPR" in src, (
        "_METHOD_MAX_ACTIVE_DEPR dict must exist in asset_inventory service"
    )
    assert "_ensure_asset_writeoff_record" in src, (
        "_ensure_asset_writeoff_record helper must exist in asset_inventory service"
    )


# ---------------------------------------------------------------------------
# W26.2 – Cap guard: exceeding active 'declining_balance' records → 422
# ---------------------------------------------------------------------------

def test_w26_declining_balance_cap_exceeded_returns_422() -> None:
    """declining_balance max=5; sixth active record must return 422."""
    for _ in range(5):
        _, code = _create_asset()
        _create_depr(code, method="declining_balance")

    _, extra_code = _create_asset()
    payload = {
        "asset_code": extra_code,
        "depreciation_method": "declining_balance",
        "original_value": 5000.0,
        "current_value": 1000.0,
        "depreciation_rate": 0.1,
        "status": "active",
    }
    resp = client.post(f"{BASE}/depreciation", headers=HEADERS, json=payload)
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    assert "declining_balance" in resp.text.lower() or "cap exceeded" in resp.text.lower()


# ---------------------------------------------------------------------------
# W26.3 – Fully depreciated record (current_value=0) creates write-off entry
# ---------------------------------------------------------------------------

def test_w26_zero_current_value_creates_writeoff_record() -> None:
    from app.modules.university_core import shared as university_shared

    _, code = _create_asset()
    _create_depr(code, method="straight_line", current_value=0.0)

    with university_shared._state_lock:
        records = list(
            university_shared._state.data.get("asset_writeoff_records", {}).values()
        )
    assert len(records) >= 1, "Write-off record should be auto-created when current_value=0"
    assert any(r.get("integration_source") == "asset_depreciation" for r in records)


# ---------------------------------------------------------------------------
# W26.4 – Idempotency of _ensure_asset_writeoff_record
# ---------------------------------------------------------------------------

def test_w26_writeoff_record_is_idempotent() -> None:
    from app.modules.asset_inventory.service import _ensure_asset_writeoff_record
    from app.modules.university_core import shared as university_shared

    fake_depr = {
        "id": "7777",
        "asset_code": "ASSET-IDEMPOTENT",
        "depreciation_method": "straight_line",
        "original_value": 3000.0,
        "current_value": 0.0,
    }
    tenant_id = 1

    _ensure_asset_writeoff_record(fake_depr, tenant_id)
    _ensure_asset_writeoff_record(fake_depr, tenant_id)
    _ensure_asset_writeoff_record(fake_depr, tenant_id)

    with university_shared._state_lock:
        records = [
            r for r in university_shared._state.data.get("asset_writeoff_records", {}).values()
            if str(r.get("source_entity_id") or "") == "7777"
            and str(r.get("integration_source") or "") == "asset_depreciation"
        ]
    assert len(records) == 1, f"Expected exactly 1 write-off record, got {len(records)}"
