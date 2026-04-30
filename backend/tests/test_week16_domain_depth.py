"""Week 16 — Domain Depth: Campus SLA Priority-Tier Enforcement + Escalation Work Order.

Tests:
  W16.1 - Source guard: _SLA_MAX_TARGET_BY_PRIORITY and _ensure_escalation_work_order present
  W16.2 - Priority 'critical' with target_sla_minutes > 60 returns 422
  W16.3 - Breached SLA record auto-creates escalation facilities work order (cross-module)
  W16.4 - Multiple breach submissions for same SLA record do not duplicate work order (idempotent)
"""
from __future__ import annotations

import inspect
import uuid

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE = "/api/admin/campus-sla"

HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="week16.campussla@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["operations.read", "operations.write"],
        )
    )
}


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _reset_state() -> None:
    from app.modules.university_core import shared as university_shared

    with university_shared._state_lock:
        for key in ("campus_sla_records", "facilities_work_orders"):
            if key in university_shared._state.data:
                university_shared._state.data[key].clear()
                university_shared._state.counters[key] = 0


def _seed_maintenance_request(facility_code: str, tenant_id: int = 1) -> None:
    """Seed an active maintenance request so the fail-closed guard passes."""
    from app.modules.university_core.shared import _state, _state_lock

    with _state_lock:
        _state.data.setdefault("facilities_maintenance_requests", {})
        _state.counters.setdefault("facilities_maintenance_requests", 0)
        _state.counters["facilities_maintenance_requests"] += 1
        req_id = _state.counters["facilities_maintenance_requests"]
        _state.data["facilities_maintenance_requests"][req_id] = {
            "id": req_id,
            "facility_code": facility_code,
            "status": "open",
            "description": "seeded for test",
            "tenant_id": tenant_id,
        }


def setup_module(_: object) -> None:
    _reset_state()


def teardown_function(_: object) -> None:
    _reset_state()


# ---------------------------------------------------------------------------
# W16.1 – Source guard
# ---------------------------------------------------------------------------

def test_w16_source_contains_priority_tier_guard_and_escalation_helper() -> None:
    from app.modules.campus_sla import service as campus_sla_service

    src = inspect.getsource(campus_sla_service)
    assert "_SLA_MAX_TARGET_BY_PRIORITY" in src, (
        "_SLA_MAX_TARGET_BY_PRIORITY dict must exist in service"
    )
    assert "exceeds maximum" in src, "Priority tier violation message must be present"
    assert "_ensure_escalation_work_order" in src, (
        "cross-module escalation helper must be present"
    )


# ---------------------------------------------------------------------------
# W16.2 – Critical priority exceeds tier maximum → 422
# ---------------------------------------------------------------------------

def test_w16_critical_priority_above_tier_maximum_returns_422() -> None:
    resp = client.post(
        f"{BASE}/sla-records",
        headers=HEADERS,
        json={
            "service_type": "maintenance",
            "facility_code": _uid("FAC"),
            "target_sla_minutes": 90,  # exceeds critical max of 60
            "priority": "critical",
            "status": "open",
        },
    )
    assert resp.status_code == 422, resp.text
    assert "exceeds maximum" in resp.text


# ---------------------------------------------------------------------------
# W16.3 – Breached SLA auto-creates escalation work order
# ---------------------------------------------------------------------------

def test_w16_breached_sla_auto_creates_escalation_work_order() -> None:
    from app.modules.university_core import shared as university_shared

    _seed_maintenance_request("FAC-001")

    resp = client.post(
        f"{BASE}/sla-records",
        headers=HEADERS,
        json={
            "service_type": "cleaning",
            "facility_code": "FAC-001",
            "target_sla_minutes": 30,
            "actual_minutes": 90,  # actual > target → breach
            "status": "open",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["record"]["breached"] is True

    with university_shared._state_lock:
        work_orders = list(
            university_shared._state.data.get("facilities_work_orders", {}).values()
        )

    sla_id = str(data["record"]["id"])
    escalation_orders = [
        wo for wo in work_orders
        if str(wo.get("integration_source")) == "campus_sla_breach"
        and str(wo.get("source_entity_id")) == sla_id
    ]
    assert len(escalation_orders) == 1, (
        f"Expected exactly 1 escalation work order, got {len(escalation_orders)}"
    )
    wo = escalation_orders[0]
    assert wo["facility_code"] == "FAC-001"
    assert wo["work_type"] == "corrective"


# ---------------------------------------------------------------------------
# W16.4 – Idempotency: same breach does not produce duplicate work orders
# ---------------------------------------------------------------------------

def test_w16_repeated_breach_submissions_do_not_duplicate_work_order() -> None:
    from app.modules.university_core import shared as university_shared

    # Submit the same SLA breach 3 times (each creates a unique SLA record but
    # we test the helper _ensure_escalation_work_order directly for idempotency
    # by calling service twice with the same sla_record_id).
    from app.modules.campus_sla.service import _ensure_escalation_work_order

    sla_record_id = f"TEST-{uuid.uuid4().hex[:8]}"
    sla_record = {
        "facility_code": "FAC-IDEMPOTENT",
        "service_type": "security",
    }

    # Call three times with same ID
    for _ in range(3):
        _ensure_escalation_work_order(1, sla_record_id, sla_record)

    with university_shared._state_lock:
        work_orders = list(
            university_shared._state.data.get("facilities_work_orders", {}).values()
        )

    matching = [
        wo for wo in work_orders
        if str(wo.get("integration_source")) == "campus_sla_breach"
        and str(wo.get("source_entity_id")) == sla_record_id
    ]
    assert len(matching) == 1, (
        f"Idempotency violated: expected 1 work order, got {len(matching)}"
    )
