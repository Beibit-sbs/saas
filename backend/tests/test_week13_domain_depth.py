"""Week 13 - Domain Depth: asset inventory and equipment booking integrity.

Tests:
  W13.1 - depreciation guard: current_value must not exceed original_value
  W13.2 - depreciation guard: depreciation record requires existing asset
  W13.3 - equipment booking guard: conflicting booking is blocked with 422
"""
from __future__ import annotations

import inspect
import uuid

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

ASSET_BASE_ITEMS = "/api/admin/asset-inventory/items"
ASSET_BASE_DEPR = "/api/admin/asset-inventory/depreciation"
BOOKING_BASE = "/api/admin/equipment-booking"

ASSET_HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="week13.asset@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["asset_inventory.read", "asset_inventory.write"],
        )
    )
}

RESEARCH_HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="week13.research@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["research.read", "research.write"],
        )
    )
}


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def test_w13_source_contains_asset_depreciation_guards() -> None:
    from app.modules.asset_inventory import service as asset_service

    src = inspect.getsource(asset_service.create_depreciation_record)
    assert "Asset not found for depreciation record" in src
    assert "current_value cannot exceed original_value" in src


def test_w13_depreciation_current_exceeds_original_returns_422() -> None:
    asset_code = _uid("ASSET-W13")
    create_asset = client.post(
        ASSET_BASE_ITEMS,
        headers=ASSET_HEADERS,
        json={
            "asset_code": asset_code,
            "name": "Week13 Asset",
            "category": "it_hardware",
            "location": "Lab 1",
            "condition": "good",
            "purchase_year": 2025,
            "vendor": "Vendor",
            "status": "active",
        },
    )
    assert create_asset.status_code == 200, create_asset.text

    bad_depr = client.post(
        ASSET_BASE_DEPR,
        headers=ASSET_HEADERS,
        json={
            "asset_code": asset_code,
            "depreciation_method": "straight_line",
            "original_value": 1000.0,
            "current_value": 1100.0,
            "depreciation_rate": 0.1,
            "status": "active",
        },
    )
    assert bad_depr.status_code == 422
    assert "cannot exceed" in bad_depr.text


def test_w13_depreciation_requires_existing_asset_returns_422() -> None:
    resp = client.post(
        ASSET_BASE_DEPR,
        headers=ASSET_HEADERS,
        json={
            "asset_code": _uid("ASSET-MISSING-W13"),
            "depreciation_method": "straight_line",
            "original_value": 500.0,
            "current_value": 400.0,
            "depreciation_rate": 0.1,
            "status": "active",
        },
    )
    assert resp.status_code == 422
    assert "Depreciation record blocked" in resp.text
    assert "not found" in resp.text


def test_w13_booking_conflict_is_blocked_with_422(monkeypatch) -> None:
    from app.modules.equipment_booking import service as booking_service

    equipment_code = _uid("EQ-W13")
    requester_1 = _uid("REQ1")
    requester_2 = _uid("REQ2")
    original_list_entities = booking_service.list_entities_for_tenant

    def _list_entities_with_enrollment_guard(entity_name: str, tenant_id: int):
        if entity_name == "student_enrollments":
            return [
                {"student_id": requester_1, "status": "active"},
                {"student_id": requester_2, "status": "active"},
            ]
        return original_list_entities(entity_name, tenant_id)

    monkeypatch.setattr(
        booking_service,
        "list_entities_for_tenant",
        _list_entities_with_enrollment_guard,
    )

    equipment_resp = client.post(
        f"{BOOKING_BASE}/equipment",
        headers=RESEARCH_HEADERS,
        json={
            "equipment_code": equipment_code,
            "name": "Microscope",
            "category": "microscopy",
            "location": "Lab B",
            "status": "available",
        },
    )
    assert equipment_resp.status_code == 201, equipment_resp.text

    first_booking = client.post(
        f"{BOOKING_BASE}/bookings",
        headers=RESEARCH_HEADERS,
        json={
            "equipment_code": equipment_code,
            "requester_id": requester_1,
            "start_time": "2026-04-26T09:00:00Z",
            "end_time": "2026-04-26T10:00:00Z",
            "booking_status": "confirmed",
            "conflict_flag": False,
        },
    )
    assert first_booking.status_code == 201, first_booking.text

    second_booking = client.post(
        f"{BOOKING_BASE}/bookings",
        headers=RESEARCH_HEADERS,
        json={
            "equipment_code": equipment_code,
            "requester_id": requester_2,
            "start_time": "2026-04-26T09:30:00Z",
            "end_time": "2026-04-26T10:30:00Z",
            "booking_status": "pending",
            "conflict_flag": False,
        },
    )
    assert second_booking.status_code == 422
    assert "Booking conflict detected" in second_booking.text
