"""Week 29 — Dining Menus Active Cap + Capacity Alert Side Effect."""
from __future__ import annotations

import inspect
import uuid

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE = "/api/admin/dining"

HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="week29.dining@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["operations.read", "operations.write"],
        )
    )
}


def _reset_state() -> None:
    from app.modules.university_core import shared as university_shared

    with university_shared._state_lock:
        for key in ("dining_menus", "dining_capacity_alert_records"):
            if key in university_shared._state.data:
                university_shared._state.data[key].clear()
                university_shared._state.counters[key] = 0


def setup_module(_: object) -> None:
    _reset_state()


def teardown_function(_: object) -> None:
    _reset_state()


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _create_menu(*, meal_type: str = "lunch", available_capacity: int = 10) -> dict:
    resp = client.post(
        f"{BASE}/menus",
        headers=HEADERS,
        json={
            "menu_code": f"MENU-{_uid()}",
            "facility_code": f"CAF-{_uid()}",
            "meal_type": meal_type,
            "status": "active",
            "capacity": 50,
            "available_capacity": available_capacity,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_w29_source_contains_menu_cap_and_capacity_helper() -> None:
    from app.modules.dining import service as dining_service

    src = inspect.getsource(dining_service)
    assert "_MEAL_TYPE_MAX_ACTIVE_MENUS" in src
    assert "_ensure_capacity_alert_record" in src


def test_w29_breakfast_menu_cap_exceeded_returns_422() -> None:
    _create_menu(meal_type="breakfast")
    _create_menu(meal_type="breakfast")

    resp = client.post(
        f"{BASE}/menus",
        headers=HEADERS,
        json={
            "menu_code": f"MENU-{_uid()}",
            "facility_code": f"CAF-{_uid()}",
            "meal_type": "breakfast",
            "status": "active",
            "capacity": 30,
            "available_capacity": 12,
        },
    )
    assert resp.status_code == 422, resp.text
    assert "cap exceeded" in resp.text.lower()


def test_w29_capacity_exhausted_menu_creates_alert_record() -> None:
    from app.modules.university_core import shared as university_shared

    result = _create_menu(meal_type="lunch", available_capacity=0)
    menu_id = result["record"]["id"]

    with university_shared._state_lock:
        records = list(university_shared._state.data.get("dining_capacity_alert_records", {}).values())

    matched = [
        row
        for row in records
        if str(row.get("source_entity_id")) == str(menu_id)
        and str(row.get("integration_source")) == "dining_capacity"
    ]
    assert len(matched) == 1, f"Expected 1 alert record, got {len(matched)}"
    assert matched[0]["alert_level"] == "high"
    assert matched[0]["status"] == "open"


def test_w29_capacity_alert_helper_is_idempotent() -> None:
    from app.modules.dining.service import _ensure_capacity_alert_record
    from app.modules.university_core import shared as university_shared

    menu = {
        "id": "7701",
        "menu_code": "MENU-IDEMPOTENT",
        "facility_code": "CAF-1",
        "meal_type": "dinner",
    }

    _ensure_capacity_alert_record(menu, 1)
    _ensure_capacity_alert_record(menu, 1)
    _ensure_capacity_alert_record(menu, 1)

    with university_shared._state_lock:
        records = [
            row
            for row in university_shared._state.data.get("dining_capacity_alert_records", {}).values()
            if str(row.get("source_entity_id")) == "7701"
            and str(row.get("integration_source")) == "dining_capacity"
        ]
    assert len(records) == 1, f"Expected exactly 1 alert record, got {len(records)}"