"""Week 20 — Domain Depth: Housing Room Allocation Cap + Assignment Record Side Effect.

Tests:
  W20.1 - Source guard: _REQUEST_TYPE_MAX_ACTIVE and _ensure_room_assignment_record present
  W20.2 - Exceeding active assignment requests for a student returns 422
  W20.3 - Transitioning housing request to approved auto-creates room_assignment_records entry
  W20.4 - Multiple _ensure_room_assignment_record calls for same request_id do not duplicate (idempotent)
"""
from __future__ import annotations

import inspect
import uuid

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE = "/api/admin/housing"

HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="week20.housing@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["housing.read", "housing.write"],
        )
    )
}


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _reset_state() -> None:
    from app.modules.university_core import shared as university_shared

    with university_shared._state_lock:
        for key in ("housing_requests", "room_assignment_records"):
            if key in university_shared._state.data:
                university_shared._state.data[key].clear()
                university_shared._state.counters[key] = 0


def setup_module(_: object) -> None:
    _reset_state()


def teardown_function(_: object) -> None:
    _reset_state()


def _create_request(student_id: int, request_type: str = "assignment") -> dict:
    payload = {
        "student_id": student_id,
        "request_type": request_type,
        "dormitory": _uid("dormA"),
    }
    resp = client.post(BASE, headers=HEADERS, json=payload)
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# W20.1 – Source guard
# ---------------------------------------------------------------------------

def test_w20_source_contains_room_allocation_cap_and_assignment_helper() -> None:
    from app.modules.housing import service as housing_service

    src = inspect.getsource(housing_service)
    assert "_REQUEST_TYPE_MAX_ACTIVE" in src, (
        "_REQUEST_TYPE_MAX_ACTIVE dict must exist in housing service"
    )
    assert "_ensure_room_assignment_record" in src, (
        "_ensure_room_assignment_record helper must exist in housing service"
    )


# ---------------------------------------------------------------------------
# W20.2 – Cap enforced: assignment max=1 → 2nd active request returns 422
# ---------------------------------------------------------------------------

def test_w20_active_cap_exceeded_returns_422() -> None:
    student_id = 301

    # First assignment request should succeed (cap=1)
    _create_request(student_id, request_type="assignment")

    # Second should be blocked
    payload = {
        "student_id": student_id,
        "request_type": "assignment",
        "dormitory": _uid("dormB"),
    }
    resp = client.post(BASE, headers=HEADERS, json=payload)
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    assert "max" in resp.json().get("detail", "").lower() or "1" in resp.json().get("detail", "")


# ---------------------------------------------------------------------------
# W20.3 – approved transition auto-creates room_assignment_records
# ---------------------------------------------------------------------------

def test_w20_approved_creates_room_assignment_record() -> None:
    from app.modules.university_core import shared as university_shared

    student_id = 302
    resp_data = _create_request(student_id, request_type="assignment")
    req_id = resp_data["item"]["id"]

    # Transition to approved
    patch_resp = client.patch(
        f"{BASE}/{req_id}/status",
        headers=HEADERS,
        json={"status": "approved"},
    )
    assert patch_resp.status_code == 200, patch_resp.text

    # Check room_assignment_records entity was created
    with university_shared._state_lock:
        records = list(
            (university_shared._state.data.get("room_assignment_records") or {}).values()
        )

    matched = [
        r for r in records
        if str(r.get("integration_source")) == "housing_approval"
        and str(r.get("source_entity_id")) == str(req_id)
    ]
    assert len(matched) == 1, f"Expected 1 room_assignment_record, found {len(matched)}"
    assert int(matched[0]["student_id"]) == student_id


# ---------------------------------------------------------------------------
# W20.4 – _ensure_room_assignment_record is idempotent
# ---------------------------------------------------------------------------

def test_w20_ensure_room_assignment_record_is_idempotent() -> None:
    from app.modules.university_core import shared as university_shared
    from app.modules.housing.service import _ensure_room_assignment_record

    tenant_id = 1
    fake_request_id = 99901
    request_data = {
        "student_id": 303,
        "dormitory": "TestDorm",
        "room_preference": "any",
        "request_type": "assignment",
    }

    _ensure_room_assignment_record(tenant_id, fake_request_id, request_data)
    _ensure_room_assignment_record(tenant_id, fake_request_id, request_data)
    _ensure_room_assignment_record(tenant_id, fake_request_id, request_data)

    with university_shared._state_lock:
        records = list(
            (university_shared._state.data.get("room_assignment_records") or {}).values()
        )

    matched = [
        r for r in records
        if str(r.get("integration_source")) == "housing_approval"
        and str(r.get("source_entity_id")) == str(fake_request_id)
    ]
    assert len(matched) == 1, f"Idempotency failed — expected 1 record, found {len(matched)}"
