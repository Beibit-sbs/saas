"""Week 21 — Domain Depth: Alumni Engagement Cap + Engagement Event Side Effect.

Tests:
  W21.1 - Source guard: _ENGAGEMENT_TYPE_MAX_ACTIVE and _ensure_engagement_event present
  W21.2 - Exceeding active mentoring records for a student returns 422
  W21.3 - Transitioning alumni record to 'engaged' auto-creates alumni_engagement_events entry
  W21.4 - Multiple _ensure_engagement_event calls for same record_id do not duplicate (idempotent)
"""
from __future__ import annotations

import inspect

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE = "/api/admin/alumni"

HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="week21.alumni@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["alumni.read", "alumni.write"],
        )
    )
}


def _seed_student(student_id: int, tenant_id: int = 1) -> None:
    """Seed a graduated student record for alumni guard."""
    from app.modules.university_core.shared import _state, _state_lock

    with _state_lock:
        _state.data.setdefault("students", {})
        _state.counters.setdefault("students", 0)
        _state.counters["students"] += 1
        sid = _state.counters["students"]
        _state.data["students"][sid] = {
            "id": student_id,
            "student_id": student_id,
            "status": "graduated",
            "tenant_id": str(tenant_id),
        }


def _reset_state() -> None:
    from app.modules.university_core import shared as university_shared

    with university_shared._state_lock:
        for key in ("alumni_records", "alumni_engagement_events", "students"):
            if key in university_shared._state.data:
                university_shared._state.data[key].clear()
                university_shared._state.counters[key] = 0


def setup_module(_: object) -> None:
    _reset_state()


def teardown_function(_: object) -> None:
    _reset_state()


def _create_record(student_id: int, engagement_type: str = "event") -> dict:
    _seed_student(student_id)
    payload = {
        "student_id": student_id,
        "graduation_year": 2020,
        "engagement_type": engagement_type,
    }
    resp = client.post(BASE, headers=HEADERS, json=payload)
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# W21.1 – Source guard
# ---------------------------------------------------------------------------

def test_w21_source_contains_engagement_cap_and_event_helper() -> None:
    from app.modules.alumni import service as alumni_service

    src = inspect.getsource(alumni_service)
    assert "_ENGAGEMENT_TYPE_MAX_ACTIVE" in src, (
        "_ENGAGEMENT_TYPE_MAX_ACTIVE dict must exist in alumni service"
    )
    assert "_ensure_engagement_event" in src, (
        "_ensure_engagement_event helper must exist in alumni service"
    )


# ---------------------------------------------------------------------------
# W21.2 – Cap exceeded for mentoring (max=1) → 422
# ---------------------------------------------------------------------------

def test_w21_mentoring_cap_exceeded_returns_422() -> None:
    student_id = 900001
    # First mentoring record should succeed
    _create_record(student_id, "mentoring")

    # Second mentoring record must be rejected
    resp = client.post(
        BASE,
        headers=HEADERS,
        json={"student_id": student_id, "graduation_year": 2020, "engagement_type": "mentoring"},
    )
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# W21.3 – Transition to 'engaged' auto-creates alumni_engagement_events entry
# ---------------------------------------------------------------------------

def test_w21_transition_to_engaged_creates_engagement_event() -> None:
    from app.modules.university_core import shared as university_shared

    student_id = 900002
    data = _create_record(student_id, "event")
    record_id = data["item"]["id"]

    resp = client.patch(
        f"{BASE}/{record_id}/status",
        headers=HEADERS,
        json={"status": "engaged"},
    )
    assert resp.status_code == 200, resp.text

    with university_shared._state_lock:
        events = list(university_shared._state.data.get("alumni_engagement_events", {}).values())

    matched = [
        e for e in events
        if str(e.get("source_entity_id")) == str(record_id)
        and str(e.get("integration_source")) == "alumni_engagement"
    ]
    assert len(matched) == 1, (
        f"Expected 1 engagement event for record_id={record_id}, found {len(matched)}"
    )
    assert int(matched[0]["student_id"]) == student_id


# ---------------------------------------------------------------------------
# W21.4 – _ensure_engagement_event is idempotent (3 calls → 1 record)
# ---------------------------------------------------------------------------

def test_w21_ensure_engagement_event_is_idempotent() -> None:
    from app.modules.university_core import shared as university_shared
    from app.modules.alumni.service import _ensure_engagement_event

    student_id = 900003
    data = _create_record(student_id, "referral")
    record_id = data["item"]["id"]
    record_data = data["item"]

    # Call helper 3 times with same record_id
    for _ in range(3):
        _ensure_engagement_event(tenant_id=1, record_id=record_id, record_data=record_data)

    with university_shared._state_lock:
        events = list(university_shared._state.data.get("alumni_engagement_events", {}).values())

    matched = [
        e for e in events
        if str(e.get("source_entity_id")) == str(record_id)
        and str(e.get("integration_source")) == "alumni_engagement"
    ]
    assert len(matched) == 1, (
        f"Idempotent helper produced {len(matched)} records, expected exactly 1"
    )
