"""Week 27 — Domain Depth: Operations Work Orders active-status cap + dispatch side effect."""
from __future__ import annotations

import inspect
import uuid

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE = "/api/admin/operations"

HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="week27.operations@example.com",
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
        for key in ("operations_work_orders", "operations_dispatch_records"):
            if key in university_shared._state.data:
                university_shared._state.data[key].clear()
                university_shared._state.counters[key] = 0


def setup_module(_: object) -> None:
    _reset_state()


def teardown_function(_: object) -> None:
    _reset_state()


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _create_work_order(*, status: str = "open", assigned_team: str | None = None) -> dict:
    payload = {
        "work_order_code": f"OP-WO-{_uid()}",
        "facility_code": f"FAC-{_uid()}",
        "summary": "Operations work order",
        "status": status,
    }
    if assigned_team is not None:
        payload["assigned_team"] = assigned_team
    response = client.post(f"{BASE}/work-orders", headers=HEADERS, json=payload)
    assert response.status_code in (200, 201), response.text
    return response.json()


def test_w27_source_contains_status_cap_and_dispatch_helper() -> None:
    from app.modules.operations import service as operations_service

    source = inspect.getsource(operations_service)
    assert "_WORK_ORDER_STATUS_MAX_ACTIVE" in source
    assert "_ensure_dispatch_record" in source


def test_w27_assigned_cap_exceeded_returns_422() -> None:
    for _ in range(8):
        _create_work_order(status="assigned")

    payload = {
        "work_order_code": f"OP-WO-{_uid()}",
        "facility_code": f"FAC-{_uid()}",
        "summary": "Cap exceeded",
        "status": "assigned",
    }
    response = client.post(f"{BASE}/work-orders", headers=HEADERS, json=payload)
    assert response.status_code == 422, response.text
    assert "cap exceeded" in response.text.lower() or "assigned" in response.text.lower()


def test_w27_assigned_team_creates_dispatch_record() -> None:
    from app.modules.university_core import shared as university_shared

    _create_work_order(status="open", assigned_team="dispatch-alpha")

    with university_shared._state_lock:
        rows = list(university_shared._state.data.get("operations_dispatch_records", {}).values())
    assert len(rows) >= 1
    assert any(row.get("integration_source") == "operations_work_order" for row in rows)


def test_w27_dispatch_record_is_idempotent() -> None:
    from app.modules.operations.service import _ensure_dispatch_record
    from app.modules.university_core import shared as university_shared

    work_order = {
        "id": "9090",
        "work_order_code": "OP-WO-IDEMPOTENT",
        "facility_code": "FAC-OPS-1",
        "status": "assigned",
    }

    _ensure_dispatch_record(work_order, 1, "dispatch-alpha")
    _ensure_dispatch_record(work_order, 1, "dispatch-alpha")
    _ensure_dispatch_record(work_order, 1, "dispatch-alpha")

    with university_shared._state_lock:
        rows = [
            row
            for row in university_shared._state.data.get("operations_dispatch_records", {}).values()
            if str(row.get("source_entity_id") or "") == "9090"
            and str(row.get("integration_source") or "") == "operations_work_order"
        ]
    assert len(rows) == 1