"""Phase XXXIV.1 — exam_governance publish_event tests.

Tests verify that exam lifecycle events are published via EventPublisher
for: EXAM_CREATED, EXAM_STARTED, EXAM_SUBMITTED, EXAM_GRADED, VIOLATION_DETECTED.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from tests.conftest import ADMIN_HEADERS, client

BASE = "/api/admin/exam-governance"

_EXAM_PAYLOAD = {
    "course_code": "CS-101",
    "course_title": "Intro to CS",
    "faculty_id": "faculty-1",
    "exam_type": "midterm",
    "term_id": "TERM-2026-1",
    "status": "scheduled",
    "duration_minutes": 90,
    "is_proctored": True,
    "proctoring_mode": "in_person",
}

_REMOTE_EXAM_PAYLOAD = {
    **_EXAM_PAYLOAD,
    "course_code": "CS-200",
    "proctoring_mode": "remote",
}


# ---------------------------------------------------------------------------
# Test 1: create_exam publishes exam.created
# ---------------------------------------------------------------------------
def test_create_exam_publishes_exam_created_event() -> None:
    with patch("app.modules.exam_governance.service.EventPublisher") as mock_cls:
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        resp = client.post(BASE, headers=ADMIN_HEADERS, json=_EXAM_PAYLOAD)
        assert resp.status_code == 200, resp.text

        mock_pub.publish_event.assert_called()
        calls = mock_pub.publish_event.call_args_list
        event_types = [c.kwargs["event_type"] for c in calls]
        assert "exam.created" in event_types


# ---------------------------------------------------------------------------
# Test 2: create_exam does NOT publish exam.created when EventPublisher fails
# ---------------------------------------------------------------------------
def test_create_exam_succeeds_even_if_event_publisher_raises() -> None:
    with patch("app.modules.exam_governance.service.EventPublisher") as mock_cls:
        mock_pub = MagicMock()
        mock_pub.publish_event.side_effect = RuntimeError("broker down")
        mock_cls.return_value = mock_pub

        resp = client.post(BASE, headers=ADMIN_HEADERS, json={**_EXAM_PAYLOAD, "course_code": "CS-999"})
        assert resp.status_code == 200, resp.text


# ---------------------------------------------------------------------------
# Test 3: update to in_progress publishes exam.started
# ---------------------------------------------------------------------------
def test_update_exam_to_in_progress_publishes_exam_started() -> None:
    create_resp = client.post(BASE, headers=ADMIN_HEADERS, json={**_EXAM_PAYLOAD, "course_code": "CS-102"})
    assert create_resp.status_code == 200, create_resp.text
    exam_id = create_resp.json()["item"]["id"]

    with patch("app.modules.exam_governance.service.EventPublisher") as mock_cls:
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        resp = client.put(
            f"{BASE}/{exam_id}",
            headers=ADMIN_HEADERS,
            json={"status": "in_progress"},
        )
        assert resp.status_code == 200, resp.text

        calls = mock_pub.publish_event.call_args_list
        event_types = [c.kwargs["event_type"] for c in calls]
        assert "exam.started" in event_types


# ---------------------------------------------------------------------------
# Test 4: update to completed publishes exam.submitted
# ---------------------------------------------------------------------------
def test_update_exam_to_completed_publishes_exam_submitted() -> None:
    create_resp = client.post(BASE, headers=ADMIN_HEADERS, json={**_EXAM_PAYLOAD, "course_code": "CS-103"})
    assert create_resp.status_code == 200, create_resp.text
    exam_id = create_resp.json()["item"]["id"]

    # Move to in_progress first (FSM)
    client.put(f"{BASE}/{exam_id}", headers=ADMIN_HEADERS, json={"status": "in_progress"})

    with patch("app.modules.exam_governance.service.EventPublisher") as mock_cls:
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        resp = client.put(
            f"{BASE}/{exam_id}",
            headers=ADMIN_HEADERS,
            json={"status": "completed"},
        )
        assert resp.status_code == 200, resp.text

        calls = mock_pub.publish_event.call_args_list
        event_types = [c.kwargs["event_type"] for c in calls]
        assert "exam.submitted" in event_types


# ---------------------------------------------------------------------------
# Test 5: creating remote exam publishes exam.violation_detected
# ---------------------------------------------------------------------------
def test_create_remote_exam_publishes_violation_detected_event() -> None:
    with patch("app.modules.exam_governance.service.EventPublisher") as mock_cls:
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        resp = client.post(BASE, headers=ADMIN_HEADERS, json=_REMOTE_EXAM_PAYLOAD)
        assert resp.status_code == 200, resp.text

        calls = mock_pub.publish_event.call_args_list
        event_types = [c.kwargs["event_type"] for c in calls]
        assert "exam.violation_detected" in event_types


# ---------------------------------------------------------------------------
# Test 6: grade_exam endpoint publishes exam.graded
# ---------------------------------------------------------------------------
def test_grade_exam_publishes_exam_graded_event() -> None:
    create_resp = client.post(BASE, headers=ADMIN_HEADERS, json={**_EXAM_PAYLOAD, "course_code": "CS-104"})
    assert create_resp.status_code == 200, create_resp.text
    exam_id = create_resp.json()["item"]["id"]

    # Lifecycle: scheduled → in_progress → completed
    client.put(f"{BASE}/{exam_id}", headers=ADMIN_HEADERS, json={"status": "in_progress"})
    client.put(f"{BASE}/{exam_id}", headers=ADMIN_HEADERS, json={"status": "completed"})

    with patch("app.modules.exam_governance.service.EventPublisher") as mock_cls:
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        resp = client.post(
            f"{BASE}/{exam_id}/grade",
            headers=ADMIN_HEADERS,
            json={"average_score": 72.5, "pass_rate": 0.85},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["exam_id"] == exam_id
        assert data["average_score"] == 72.5
        assert data["pass_rate"] == 0.85
        assert data["status"] == "graded"

        calls = mock_pub.publish_event.call_args_list
        event_types = [c.kwargs["event_type"] for c in calls]
        assert "exam.graded" in event_types


# ---------------------------------------------------------------------------
# Test 7: grade_exam on non-completed exam returns 422
# ---------------------------------------------------------------------------
def test_grade_exam_on_non_completed_returns_422() -> None:
    create_resp = client.post(BASE, headers=ADMIN_HEADERS, json={**_EXAM_PAYLOAD, "course_code": "CS-105"})
    assert create_resp.status_code == 200, create_resp.text
    exam_id = create_resp.json()["item"]["id"]

    resp = client.post(
        f"{BASE}/{exam_id}/grade",
        headers=ADMIN_HEADERS,
        json={"average_score": 65.0, "pass_rate": 0.75},
    )
    assert resp.status_code == 422, resp.text


# ---------------------------------------------------------------------------
# Test 8: grade_exam on unknown exam returns 404
# ---------------------------------------------------------------------------
def test_grade_exam_unknown_exam_returns_404() -> None:
    resp = client.post(
        f"{BASE}/999999/grade",
        headers=ADMIN_HEADERS,
        json={"average_score": 50.0, "pass_rate": 0.60},
    )
    assert resp.status_code == 404, resp.text


# ---------------------------------------------------------------------------
# Test 9: exam.created event carries correct payload fields
# ---------------------------------------------------------------------------
def test_exam_created_event_payload_contains_course_code_and_exam_type() -> None:
    with patch("app.modules.exam_governance.service.EventPublisher") as mock_cls:
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        resp = client.post(BASE, headers=ADMIN_HEADERS, json={**_EXAM_PAYLOAD, "course_code": "CS-106"})
        assert resp.status_code == 200, resp.text

        calls = mock_pub.publish_event.call_args_list
        created_call = next(
            (c for c in calls if c.kwargs.get("event_type") == "exam.created"), None
        )
        assert created_call is not None
        payload = created_call.kwargs["payload_json"]
        assert payload["course_code"] == "CS-106"
        assert payload["exam_type"] == "midterm"


# ---------------------------------------------------------------------------
# Test 10: update to cancelled does NOT publish exam.started or exam.submitted
# ---------------------------------------------------------------------------
def test_update_exam_to_cancelled_does_not_publish_lifecycle_events() -> None:
    create_resp = client.post(BASE, headers=ADMIN_HEADERS, json={**_EXAM_PAYLOAD, "course_code": "CS-107"})
    assert create_resp.status_code == 200, create_resp.text
    exam_id = create_resp.json()["item"]["id"]

    with patch("app.modules.exam_governance.service.EventPublisher") as mock_cls:
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        resp = client.put(
            f"{BASE}/{exam_id}",
            headers=ADMIN_HEADERS,
            json={"status": "cancelled"},
        )
        assert resp.status_code == 200, resp.text

        calls = mock_pub.publish_event.call_args_list
        event_types = [c.kwargs.get("event_type") for c in calls]
        assert "exam.started" not in event_types
        assert "exam.submitted" not in event_types
