"""Week 25 — Domain Depth: Facilities Work Orders Priority SLA Cap + Assignment Record Side Effect.

Tests:
  W25.1 - Source guard: _PRIORITY_MAX_OPEN and _ensure_sla_assignment_record present
  W25.2 - Exceeding open 'critical' work orders cap returns 422
  W25.3 - Creating a work order with assigned_to auto-creates facilities_sla_assignment_records entry
  W25.4 - Multiple _ensure_sla_assignment_record calls for same order_id are idempotent
"""
from __future__ import annotations

import inspect
import uuid

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE = "/api/admin/facilities"

HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="week25.facilities@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["facilities.read", "facilities.write"],
        )
    )
}


def _reset_state() -> None:
    from app.modules.university_core import shared as university_shared

    with university_shared._state_lock:
        for key in ("facilities_work_orders", "facilities_sla_assignment_records"):
            if key in university_shared._state.data:
                university_shared._state.data[key].clear()
                university_shared._state.counters[key] = 0


def setup_module(_: object) -> None:
    _reset_state()


def teardown_function(_: object) -> None:
    _reset_state()


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _create_wo(priority: str = "medium", assigned_to: str | None = None) -> dict:
    payload = {
        "order_code": f"WO-{_uid()}",
        "facility_code": f"FAC-{_uid()}",
        "title": "Test work order",
        "work_type": "repair",
        "priority": priority,
        "status": "open",
    }
    if assigned_to is not None:
        payload["assigned_to"] = assigned_to
    resp = client.post(f"{BASE}/work-orders", headers=HEADERS, json=payload)
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# W25.1 – Source guard
# ---------------------------------------------------------------------------

def test_w25_source_contains_priority_cap_and_sla_helper() -> None:
    from app.modules.facilities_work_orders import service as fwo_service

    src = inspect.getsource(fwo_service)
    assert "_PRIORITY_MAX_OPEN" in src, (
        "_PRIORITY_MAX_OPEN dict must exist in facilities_work_orders service"
    )
    assert "_ensure_sla_assignment_record" in src, (
        "_ensure_sla_assignment_record helper must exist in facilities_work_orders service"
    )


# ---------------------------------------------------------------------------
# W25.2 – Cap guard: exceeding open 'critical' work orders → 422
# ---------------------------------------------------------------------------

def test_w25_critical_cap_exceeded_returns_422() -> None:
    """critical max=3; fourth open critical order must return 422."""
    for _ in range(3):
        _create_wo(priority="critical")
    # fourth must fail
    payload = {
        "order_code": f"WO-{_uid()}",
        "facility_code": f"FAC-{_uid()}",
        "title": "Over cap critical",
        "work_type": "repair",
        "priority": "critical",
        "status": "open",
    }
    resp = client.post(f"{BASE}/work-orders", headers=HEADERS, json=payload)
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    assert "cap exceeded" in resp.text.lower() or "critical" in resp.text.lower()


# ---------------------------------------------------------------------------
# W25.3 – Creating work order with assigned_to creates SLA assignment record
# ---------------------------------------------------------------------------

def test_w25_assigned_wo_creates_sla_assignment_record() -> None:
    from app.modules.university_core import shared as university_shared

    _create_wo(priority="medium", assigned_to="technician.001")

    with university_shared._state_lock:
        records = list(
            university_shared._state.data.get("facilities_sla_assignment_records", {}).values()
        )
    assert len(records) >= 1, "SLA assignment record should be auto-created for assigned work order"
    assert any(r.get("integration_source") == "facilities_assignment" for r in records)


# ---------------------------------------------------------------------------
# W25.4 – Idempotency of _ensure_sla_assignment_record
# ---------------------------------------------------------------------------

def test_w25_sla_assignment_record_is_idempotent() -> None:
    from app.modules.facilities_work_orders.service import _ensure_sla_assignment_record
    from app.modules.university_core import shared as university_shared

    fake_order = {
        "id": "8888",
        "order_code": "WO-TEST",
        "facility_code": "FAC-001",
        "priority": "high",
        "assigned_to": "tech.99",
    }
    tenant_id = 1

    _ensure_sla_assignment_record(fake_order, tenant_id)
    _ensure_sla_assignment_record(fake_order, tenant_id)
    _ensure_sla_assignment_record(fake_order, tenant_id)

    with university_shared._state_lock:
        records = [
            r for r in university_shared._state.data.get("facilities_sla_assignment_records", {}).values()
            if str(r.get("source_entity_id") or "") == "8888"
            and str(r.get("integration_source") or "") == "facilities_assignment"
        ]
    assert len(records) == 1, f"Expected exactly 1 SLA assignment record, got {len(records)}"
