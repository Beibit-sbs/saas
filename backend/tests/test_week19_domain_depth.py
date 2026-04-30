"""Week 19 — Domain Depth: Career Services Matching Engine Cap + Placement Record Side Effect.

Tests:
  W19.1 - Source guard: _OPPORTUNITY_TYPE_MAX_OPEN and _ensure_placement_record present
  W19.2 - Exceeding open opportunity cap for a student+type returns 422
  W19.3 - Transitioning opportunity to in_review auto-creates career_placement_records entry
  W19.4 - Multiple _ensure_placement_record calls for same opportunity_id do not duplicate (idempotent)
"""
from __future__ import annotations

import inspect
import uuid

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE = "/api/admin/career-services"

HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="week19.careerservices@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["career_services.read", "career_services.write"],
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
        for key in ("career_opportunities", "career_placement_records", "enrollments"):
            if key in university_shared._state.data:
                university_shared._state.data[key].clear()
                university_shared._state.counters[key] = 0


def setup_module(_: object) -> None:
    _reset_state()


def teardown_function(_: object) -> None:
    _reset_state()


def _create_opportunity(student_id: int, opportunity_type: str = "work_study") -> dict:
    _seed_enrollment(student_id)
    payload = {
        "student_id": student_id,
        "title": _uid("title"),
        "company": _uid("co"),
        "opportunity_type": opportunity_type,
    }
    resp = client.post(BASE, headers=HEADERS, json=payload)
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# W19.1 – Source guard
# ---------------------------------------------------------------------------

def test_w19_source_contains_matching_engine_cap_and_placement_helper() -> None:
    from app.modules.career_services import service as cs_service

    src = inspect.getsource(cs_service)
    assert "_OPPORTUNITY_TYPE_MAX_OPEN" in src, (
        "_OPPORTUNITY_TYPE_MAX_OPEN dict must exist in career_services service"
    )
    assert "_ensure_placement_record" in src, (
        "_ensure_placement_record helper must exist in career_services service"
    )


# ---------------------------------------------------------------------------
# W19.2 – Matching engine cap enforced: work_study max=1 → 2nd returns 422
# ---------------------------------------------------------------------------

def test_w19_open_cap_exceeded_returns_422() -> None:
    student_id = 201

    # First work_study opportunity should succeed (cap=1)
    _create_opportunity(student_id, opportunity_type="work_study")

    # Second should be blocked
    payload = {
        "student_id": student_id,
        "title": _uid("title"),
        "company": _uid("co"),
        "opportunity_type": "work_study",
    }
    resp = client.post(BASE, headers=HEADERS, json=payload)
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    assert "max" in resp.json().get("detail", "").lower() or "1" in resp.json().get("detail", "")


# ---------------------------------------------------------------------------
# W19.3 – in_review transition auto-creates career_placement_records
# ---------------------------------------------------------------------------

def test_w19_in_review_creates_placement_record() -> None:
    from app.modules.university_core import shared as university_shared

    student_id = 202
    resp_data = _create_opportunity(student_id, opportunity_type="internship")
    opp_id = resp_data["item"]["id"]

    # Transition to in_review
    patch_resp = client.patch(
        f"{BASE}/{opp_id}/status",
        headers=HEADERS,
        json={"status": "in_review"},
    )
    assert patch_resp.status_code == 200, patch_resp.text

    # Verify placement record created
    with university_shared._state_lock:
        records = list(university_shared._state.data.get("career_placement_records", {}).values())

    matched = [
        r for r in records
        if int(r.get("source_entity_id") or 0) == opp_id
        and r.get("integration_source") == "career_matching"
    ]
    assert len(matched) == 1, f"Expected 1 placement record, found {len(matched)}"
    assert int(matched[0]["student_id"]) == student_id


# ---------------------------------------------------------------------------
# W19.4 – _ensure_placement_record is idempotent
# ---------------------------------------------------------------------------

def test_w19_ensure_placement_record_is_idempotent() -> None:
    from app.modules.university_core import shared as university_shared
    from app.modules.career_services.service import _ensure_placement_record

    student_id = 203
    opportunity_id = 9991
    opportunity_data = {
        "student_id": student_id,
        "company": "Acme Corp",
        "opportunity_type": "internship",
    }

    _ensure_placement_record(1, opportunity_id, opportunity_data)
    _ensure_placement_record(1, opportunity_id, opportunity_data)
    _ensure_placement_record(1, opportunity_id, opportunity_data)

    with university_shared._state_lock:
        records = list(university_shared._state.data.get("career_placement_records", {}).values())

    matched = [
        r for r in records
        if int(r.get("source_entity_id") or 0) == opportunity_id
        and r.get("integration_source") == "career_matching"
    ]
    assert len(matched) == 1, f"Expected 1 (idempotent), found {len(matched)}"
