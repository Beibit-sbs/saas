"""Week 15 - Domain Depth: Scholarship Eligibility Engine.

Tests:
  W15.1 - Source guard: GPA minimums and eligibility logic present in service
  W15.2 - Merit scholarship with GPA below threshold returns 422
  W15.3 - Approved application auto-creates scholarship award (cross-module)
  W15.4 - Repeated approved applications do not duplicate active award (idempotent)
"""
from __future__ import annotations

import inspect
import uuid

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE = "/api/admin/scholarship"

HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="week15.scholarship@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["operations.read", "operations.write"],
        )
    )
}


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _seed_active_enrollment(student_id: str) -> None:
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
            "semester": "Fall 2025",
            "status": "active",
            "tenant_id": "1",
        }


def _reset_state() -> None:
    from app.modules.university_core import shared as university_shared
    with university_shared._state_lock:
        for key in ("scholarship_applications", "scholarship_awards"):
            if key in university_shared._state.data:
                university_shared._state.data[key].clear()
                university_shared._state.counters[key] = 0


def setup_module(_: object) -> None:
    _reset_state()


def teardown_function(_: object) -> None:
    _reset_state()


# ---------------------------------------------------------------------------
# W15.1 – Source guard
# ---------------------------------------------------------------------------

def test_w15_source_contains_eligibility_guard_and_auto_award() -> None:
    from app.modules.scholarship import service as scholarship_service

    src = inspect.getsource(scholarship_service)
    assert "_GPA_MINIMUMS" in src, "_GPA_MINIMUMS dict must exist in service"
    assert "requires gpa >=" in src, "GPA eligibility guard message must be present"
    assert "_ensure_award_for_approved_application" in src, (
        "cross-module auto-award helper must be present"
    )


# ---------------------------------------------------------------------------
# W15.2 – Merit GPA too low → 422
# ---------------------------------------------------------------------------

def test_w15_merit_below_gpa_threshold_returns_422() -> None:
    student_id = _uid("STU")
    _seed_active_enrollment(student_id)

    resp = client.post(
        f"{BASE}/applications",
        headers=HEADERS,
        json={
            "application_code": _uid("APP-MERIT-LOW"),
            "student_id": student_id,
            "scholarship_type": "merit",
            "gpa": 2.7,
            "requested_amount": 5000.0,
        },
    )
    assert resp.status_code == 422, resp.text
    assert "requires gpa >=" in resp.text


# ---------------------------------------------------------------------------
# W15.3 – Approved application auto-creates award
# ---------------------------------------------------------------------------

def test_w15_approved_application_auto_creates_award() -> None:
    student_id = _uid("STU-W15")
    _seed_active_enrollment(student_id)

    resp = client.post(
        f"{BASE}/applications",
        headers=HEADERS,
        json={
            "application_code": _uid("APP-APPROVED"),
            "student_id": student_id,
            "scholarship_type": "merit",
            "status": "approved",
            "gpa": 3.6,
            "requested_amount": 4000.0,
        },
    )
    assert resp.status_code == 201, resp.text

    awards_resp = client.get(f"{BASE}/awards", headers=HEADERS)
    assert awards_resp.status_code == 200, awards_resp.text
    records = awards_resp.json().get("records", [])

    matched = [
        r for r in records
        if r.get("student_id") == student_id
        and r.get("scholarship_type") == "merit"
        and r.get("integration_source") == "scholarship_application_approval"
    ]
    assert len(matched) == 1, f"Expected 1 auto-created award, got {len(matched)}"
    assert matched[0].get("status") == "active"


# ---------------------------------------------------------------------------
# W15.4 – Idempotent: repeated approved applications do not duplicate award
# ---------------------------------------------------------------------------

def test_w15_repeated_approved_applications_do_not_duplicate_award() -> None:
    student_id = _uid("STU-W15-IDEM")
    _seed_active_enrollment(student_id)

    for i in range(3):
        resp = client.post(
            f"{BASE}/applications",
            headers=HEADERS,
            json={
                "application_code": _uid(f"APP-DUP-{i}"),
                "student_id": student_id,
                "scholarship_type": "merit",
                "status": "approved",
                "gpa": 3.8,
                "requested_amount": 3000.0,
            },
        )
        assert resp.status_code == 201, resp.text

    awards_resp = client.get(f"{BASE}/awards", headers=HEADERS)
    assert awards_resp.status_code == 200, awards_resp.text
    records = awards_resp.json().get("records", [])

    matched = [
        r for r in records
        if r.get("student_id") == student_id
        and r.get("scholarship_type") == "merit"
        and str(r.get("status") or "").lower() in {"active", "pending"}
    ]
    assert len(matched) == 1, (
        f"Expected exactly 1 active award, got {len(matched)} — idempotency broken"
    )
