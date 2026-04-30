"""Week 18 — Domain Depth: Student Services SLA Tier Enforcement + SLA Alert Side Effect.

Tests:
  W18.1 - Source guard: _TICKET_PRIORITY_MAX_RESOLUTION_HOURS and _ensure_sla_alert present
  W18.2 - Urgent ticket with target_resolution_hours exceeding cap returns 422
  W18.3 - Urgent ticket auto-creates student_service_sla_alerts cross-module record
  W18.4 - Multiple _ensure_sla_alert calls for same ticket_id do not duplicate (idempotent)
"""
from __future__ import annotations

import inspect
import uuid

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE = "/api/admin/student-services/tickets"

HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="week18.studentservices@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["student_services.read", "student_services.write"],
        )
    )
}


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _seed_enrollment(student_id: int, tenant_id: int = 1) -> None:
    """Seed an active enrollment to satisfy enrollment guard."""
    from app.modules.university_core.shared import _state, _state_lock

    with _state_lock:
        _state.data.setdefault("enrollments", {})
        _state.counters.setdefault("enrollments", 0)
        _state.counters["enrollments"] += 1
        eid = _state.counters["enrollments"]
        _state.data["enrollments"][eid] = {
            "id": eid,
            "student_id": student_id,
            "course_id": 1,
            "semester": "Spring 2026",
            "status": "active",
            "tenant_id": str(tenant_id),
        }


def _reset_state() -> None:
    from app.modules.university_core import shared as university_shared

    with university_shared._state_lock:
        for key in ("student_service_tickets", "student_service_sla_alerts", "enrollments"):
            if key in university_shared._state.data:
                university_shared._state.data[key].clear()
                university_shared._state.counters[key] = 0


def setup_module(_: object) -> None:
    _reset_state()


def teardown_function(_: object) -> None:
    _reset_state()


def _create_ticket(priority: str, target_resolution_hours: int | None = None) -> dict:
    _seed_enrollment(99)
    payload: dict = {
        "student_id": 99,
        "category": _uid("cat"),
        "subject": _uid("subj"),
        "description": "Test ticket for Week 18 domain depth.",
        "priority": priority,
    }
    if target_resolution_hours is not None:
        payload["target_resolution_hours"] = target_resolution_hours
    resp = client.post(BASE, headers=HEADERS, json=payload)
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# W18.1 – Source guard
# ---------------------------------------------------------------------------

def test_w18_source_contains_sla_tier_guard_and_alert_helper() -> None:
    from app.modules.student_services import service as ss_service

    src = inspect.getsource(ss_service)
    assert "_TICKET_PRIORITY_MAX_RESOLUTION_HOURS" in src, (
        "_TICKET_PRIORITY_MAX_RESOLUTION_HOURS dict must exist in student_services service"
    )
    assert "exceeds maximum target_resolution_hours" in src, (
        "SLA cap violation message must be present in service"
    )
    assert "_ensure_sla_alert" in src, (
        "_ensure_sla_alert cross-module helper must be present in service"
    )


# ---------------------------------------------------------------------------
# W18.2 – Urgent ticket with target_resolution_hours above cap → 422
# ---------------------------------------------------------------------------

def test_w18_urgent_ticket_above_sla_cap_returns_422() -> None:
    _seed_enrollment(99)
    # urgent cap is 4 hours; 6 > 4 → must be rejected
    resp = client.post(
        BASE,
        headers=HEADERS,
        json={
            "student_id": 99,
            "category": "academic_advising",
            "subject": "Urgent counselling needed",
            "description": "Student in distress.",
            "priority": "urgent",
            "target_resolution_hours": 6,
        },
    )
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    assert "exceeds maximum" in resp.json().get("detail", ""), resp.text


# ---------------------------------------------------------------------------
# W18.3 – Urgent ticket auto-creates student_service_sla_alerts record
# ---------------------------------------------------------------------------

def test_w18_urgent_ticket_creates_sla_alert_cross_module() -> None:
    from app.modules.university_core import shared as university_shared

    # within-cap urgent ticket (target_resolution_hours=2 ≤ 4 max)
    resp_data = _create_ticket(priority="urgent", target_resolution_hours=2)
    ticket = resp_data.get("item") or resp_data

    # SLA alert should have been created in university_core entity store
    with university_shared._state_lock:
        alerts = list(university_shared._state.data.get("student_service_sla_alerts", {}).values())

    assert len(alerts) == 1, f"Expected 1 sla_alert, got {len(alerts)}: {alerts}"
    alert = alerts[0]
    assert alert["integration_source"] == "student_service_sla"
    assert str(alert["source_entity_id"]) == str(ticket["id"])
    assert alert["priority"] == "urgent"
    assert alert["alert_level"] == "critical"


# ---------------------------------------------------------------------------
# W18.4 – _ensure_sla_alert is idempotent: same ticket_id → single record
# ---------------------------------------------------------------------------

def test_w18_ensure_sla_alert_is_idempotent() -> None:
    from app.modules.university_core import shared as university_shared
    from app.modules.student_services.service import _ensure_sla_alert

    ticket_id = 9001
    ticket_data = {"student_id": 99, "priority": "urgent", "category": "housing"}

    _ensure_sla_alert(1, ticket_id, ticket_data)
    _ensure_sla_alert(1, ticket_id, ticket_data)  # second call — must be a no-op

    with university_shared._state_lock:
        alerts = [
            r for r in university_shared._state.data.get("student_service_sla_alerts", {}).values()
            if str(r.get("source_entity_id")) == str(ticket_id)
        ]

    assert len(alerts) == 1, (
        f"_ensure_sla_alert must be idempotent: expected 1 record, got {len(alerts)}"
    )
