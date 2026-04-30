"""Week 30 — Transport Routes: Active Vehicle-Type Cap + Disruption Record Side Effect."""
from __future__ import annotations

import inspect
import uuid

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE = "/api/admin/transport"

HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="week30.transport@example.com",
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
        for key in ("transport_routes", "transport_disruption_records"):
            if key in university_shared._state.data:
                university_shared._state.data[key].clear()
                university_shared._state.counters[key] = 0


def setup_module(_: object) -> None:
    _reset_state()


def teardown_function(_: object) -> None:
    _reset_state()


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _create_route(*, vehicle_type: str = "bus", status: str = "active") -> dict:
    resp = client.post(
        f"{BASE}/routes",
        headers=HEADERS,
        json={
            "route_code": f"RT-{_uid()}",
            "route_name": f"Route {_uid()}",
            "status": status,
            "vehicle_type": vehicle_type,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_w30_source_contains_cap_dict_and_disruption_helper() -> None:
    from app.modules.transport import service as transport_service

    src = inspect.getsource(transport_service)
    assert "_VEHICLE_TYPE_MAX_ACTIVE_ROUTES" in src
    assert "_ensure_transport_disruption_record" in src


def test_w30_van_route_cap_exceeded_returns_422() -> None:
    # van cap = 5
    for _ in range(5):
        _create_route(vehicle_type="van", status="active")

    resp = client.post(
        f"{BASE}/routes",
        headers=HEADERS,
        json={
            "route_code": f"RT-{_uid()}",
            "route_name": "Extra Van Route",
            "status": "active",
            "vehicle_type": "van",
        },
    )
    assert resp.status_code == 422, resp.text
    assert "cap exceeded" in resp.text.lower()


def test_w30_disrupted_route_creates_disruption_record() -> None:
    from app.modules.university_core import shared as university_shared

    result = _create_route(vehicle_type="shuttle", status="disrupted")
    route_id = result["record"]["id"]

    with university_shared._state_lock:
        records = list(
            university_shared._state.data.get("transport_disruption_records", {}).values()
        )

    matched = [
        r for r in records
        if str(r.get("source_entity_id") or "") == str(route_id)
        and str(r.get("integration_source") or "") == "transport_disruption"
    ]
    assert matched, f"No disruption record found for route_id={route_id}"
    assert matched[0]["disruption_status"] == "disrupted"


def test_w30_disruption_record_is_idempotent() -> None:
    from app.modules.university_core import shared as university_shared
    from app.modules.transport.service import _ensure_transport_disruption_record

    fake_route: dict[str, object] = {
        "id": 9901,
        "route_code": "IDEMPOT-001",
        "vehicle_type": "bus",
        "status": "disrupted",
    }
    _ensure_transport_disruption_record(fake_route, tenant_id=1)
    _ensure_transport_disruption_record(fake_route, tenant_id=1)
    _ensure_transport_disruption_record(fake_route, tenant_id=1)

    with university_shared._state_lock:
        records = list(
            university_shared._state.data.get("transport_disruption_records", {}).values()
        )

    matched = [
        r for r in records
        if str(r.get("source_entity_id") or "") == "9901"
        and str(r.get("integration_source") or "") == "transport_disruption"
    ]
    assert len(matched) == 1, f"Expected 1 idempotent record, got {len(matched)}"
