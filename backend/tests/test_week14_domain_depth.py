"""Week 14 - Domain Depth: student_life wellbeing risk routing.

Tests:
  W14.1 - wellbeing guard: low score requires at_risk status
  W14.2 - at-risk wellbeing auto-creates counseling case
  W14.3 - repeated at-risk check-ins do not duplicate open counseling cases
"""
from __future__ import annotations

import inspect
import uuid

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE = "/api/admin/student-life"

HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="week14.studentlife@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["student_life.read", "student_life.write"],
        )
    )
}


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def test_w14_source_contains_wellbeing_risk_guard_and_routing() -> None:
    from app.modules.student_life import service as student_life_service

    src = inspect.getsource(student_life_service.create_wellbeing_checkin)
    assert "wellbeing_score <= 40 requires status='at_risk'" in src
    assert "_ensure_counseling_case_for_wellbeing_risk" in src


def test_w14_low_score_with_stable_status_returns_422() -> None:
    student_id = _uid("STU-W14")
    resp = client.post(
        f"{BASE}/wellbeing-checkins",
        headers=HEADERS,
        json={
            "student_id": student_id,
            "wellbeing_score": 25,
            "status": "stable",
        },
    )
    assert resp.status_code == 422
    assert "requires status='at_risk'" in resp.text


def test_w14_at_risk_checkin_auto_creates_counseling_case() -> None:
    student_id = _uid("STU-W14")
    create_checkin = client.post(
        f"{BASE}/wellbeing-checkins",
        headers=HEADERS,
        json={
            "student_id": student_id,
            "wellbeing_score": 28,
            "status": "at_risk",
        },
    )
    assert create_checkin.status_code == 200, create_checkin.text

    counseling = client.get(f"{BASE}/counseling-cases", headers=HEADERS)
    assert counseling.status_code == 200, counseling.text
    items = counseling.json().get("items", [])

    matched = [
        item
        for item in items
        if item.get("student_id") == student_id and item.get("concern_type") == "wellbeing_risk"
    ]
    assert len(matched) == 1
    assert matched[0].get("status") == "open"


def test_w14_repeated_at_risk_checkins_do_not_duplicate_open_case() -> None:
    student_id = _uid("STU-W14")

    first = client.post(
        f"{BASE}/wellbeing-checkins",
        headers=HEADERS,
        json={
            "student_id": student_id,
            "wellbeing_score": 31,
            "status": "at_risk",
        },
    )
    assert first.status_code == 200, first.text

    second = client.post(
        f"{BASE}/wellbeing-checkins",
        headers=HEADERS,
        json={
            "student_id": student_id,
            "wellbeing_score": 24,
            "status": "at_risk",
        },
    )
    assert second.status_code == 200, second.text

    counseling = client.get(f"{BASE}/counseling-cases", headers=HEADERS)
    assert counseling.status_code == 200, counseling.text
    items = counseling.json().get("items", [])
    matched = [
        item
        for item in items
        if item.get("student_id") == student_id and item.get("concern_type") == "wellbeing_risk"
    ]
    open_cases = [item for item in matched if item.get("status") in {"open", "in_progress"}]
    assert len(open_cases) == 1
