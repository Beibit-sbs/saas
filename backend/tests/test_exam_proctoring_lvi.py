"""Phase LVI — Exam Proctoring (AI camera) tests (22 tests)."""
from __future__ import annotations

from unittest.mock import patch

import pytest

MODULE = "app.modules.exam_proctoring.service"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_session(id_=1, exam_id=10, student_id=5, status="active"):
    return {"id": id_, "exam_id": exam_id, "student_id": student_id, "status": status}


def _make_violation(id_=100, session_id=1, violation_type="gaze_away",
                    confidence=0.9, reviewed=False):
    return {
        "id": id_,
        "session_id": session_id,
        "violation_type": violation_type,
        "confidence": confidence,
        "snapshot_ref": "",
        "reviewed": reviewed,
        "resolution": "",
    }


# ---------------------------------------------------------------------------
# 1. start_session — happy path
# ---------------------------------------------------------------------------


def test_start_session_creates_record():
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[]),
        patch(f"{MODULE}.create_entity_for_tenant") as mock_create,
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        mock_create.return_value = {"id": 1}
        from app.modules.exam_proctoring.service import start_session

        result = start_session(exam_id=10, student_id=5, tenant_id=42)

        assert result.session_id == 1
        assert result.status == "active"
        payload = mock_create.call_args[0][1]
        assert payload["status"] == "active"
        mock_pub.publish.assert_called_once()
        assert mock_pub.publish.call_args[1]["event_type"] == "proctoring.session_started"


# ---------------------------------------------------------------------------
# 2. start_session — duplicate active session
# ---------------------------------------------------------------------------


def test_start_session_duplicate_raises():
    existing = [_make_session(status="active")]
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=existing):
        from app.modules.exam_proctoring.service import ProctoringError, start_session

        with pytest.raises(ProctoringError, match="already has an active proctoring session"):
            start_session(exam_id=10, student_id=5, tenant_id=42)


# ---------------------------------------------------------------------------
# 3. start_session — invalid exam_id
# ---------------------------------------------------------------------------


def test_start_session_invalid_exam_id():
    from app.modules.exam_proctoring.service import ProctoringError, start_session

    with pytest.raises(ProctoringError, match="exam_id"):
        start_session(exam_id=0, student_id=5, tenant_id=1)


# ---------------------------------------------------------------------------
# 4. start_session — invalid student_id
# ---------------------------------------------------------------------------


def test_start_session_invalid_student_id():
    from app.modules.exam_proctoring.service import ProctoringError, start_session

    with pytest.raises(ProctoringError, match="student_id"):
        start_session(exam_id=10, student_id=0, tenant_id=1)


# ---------------------------------------------------------------------------
# 5. pause_session — happy path
# ---------------------------------------------------------------------------


def test_pause_session():
    session = _make_session(status="active")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[session]),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
    ):
        from app.modules.exam_proctoring.service import pause_session

        result = pause_session(session_id=1, tenant_id=42)

        assert result.status == "paused"
        assert mock_update.call_args[0][2]["status"] == "paused"


# ---------------------------------------------------------------------------
# 6. pause_session — not active
# ---------------------------------------------------------------------------


def test_pause_already_paused_raises():
    session = _make_session(status="paused")
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[session]):
        from app.modules.exam_proctoring.service import ProctoringError, pause_session

        with pytest.raises(ProctoringError, match="only active sessions"):
            pause_session(session_id=1, tenant_id=42)


# ---------------------------------------------------------------------------
# 7. resume_session — happy path
# ---------------------------------------------------------------------------


def test_resume_session():
    session = _make_session(status="paused")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[session]),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
    ):
        from app.modules.exam_proctoring.service import resume_session

        result = resume_session(session_id=1, tenant_id=42)

        assert result.status == "active"
        assert mock_update.call_args[0][2]["status"] == "active"


# ---------------------------------------------------------------------------
# 8. resume_session — not paused
# ---------------------------------------------------------------------------


def test_resume_non_paused_raises():
    session = _make_session(status="active")
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[session]):
        from app.modules.exam_proctoring.service import ProctoringError, resume_session

        with pytest.raises(ProctoringError, match="only paused sessions"):
            resume_session(session_id=1, tenant_id=42)


# ---------------------------------------------------------------------------
# 9. end_session — happy path
# ---------------------------------------------------------------------------


def test_end_session():
    session = _make_session(status="active")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[session]),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        from app.modules.exam_proctoring.service import end_session

        result = end_session(session_id=1, tenant_id=42)

        assert result.status == "ended"
        assert mock_update.call_args[0][2]["status"] == "ended"
        mock_pub.publish.assert_called_once()
        assert mock_pub.publish.call_args[1]["event_type"] == "proctoring.session_ended"


# ---------------------------------------------------------------------------
# 10. end_session — already ended
# ---------------------------------------------------------------------------


def test_end_already_ended_raises():
    session = _make_session(status="ended")
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[session]):
        from app.modules.exam_proctoring.service import ProctoringError, end_session

        with pytest.raises(ProctoringError, match="already"):
            end_session(session_id=1, tenant_id=42)


# ---------------------------------------------------------------------------
# 11. abort_session — happy path
# ---------------------------------------------------------------------------


def test_abort_session():
    session = _make_session(status="active")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[session]),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
    ):
        from app.modules.exam_proctoring.service import abort_session

        result = abort_session(session_id=1, reason="Exam cancelled", tenant_id=42)

        assert result.status == "aborted"
        payload = mock_update.call_args[0][2]
        assert payload["status"] == "aborted"
        assert payload["abort_reason"] == "Exam cancelled"


# ---------------------------------------------------------------------------
# 12. list_sessions — filters by exam_id
# ---------------------------------------------------------------------------


def test_list_sessions_filters():
    sessions = [
        _make_session(id_=1, exam_id=10),
        _make_session(id_=2, exam_id=20),
        _make_session(id_=3, exam_id=10, student_id=7),
    ]
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=sessions):
        from app.modules.exam_proctoring.service import list_sessions

        result = list_sessions(exam_id=10, tenant_id=42)
        assert len(result) == 2
        assert all(r.exam_id == 10 for r in result)


# ---------------------------------------------------------------------------
# 13. report_violation — happy path
# ---------------------------------------------------------------------------


def test_report_violation_creates_record():
    session = _make_session(status="active")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[session]),
        patch(f"{MODULE}.create_entity_for_tenant") as mock_create,
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        mock_create.return_value = {"id": 100}
        from app.modules.exam_proctoring.service import report_violation

        result = report_violation(
            session_id=1,
            violation_type="gaze_away",
            confidence=0.87,
            snapshot_ref="s3://snap/001.jpg",
            tenant_id=42,
        )

        assert result.violation_id == 100
        assert result.violation_type == "gaze_away"
        assert result.reviewed is False
        payload = mock_create.call_args[0][1]
        assert payload["confidence"] == 0.87
        mock_pub.publish.assert_called_once()
        assert mock_pub.publish.call_args[1]["event_type"] == "proctoring.violation_detected"


# ---------------------------------------------------------------------------
# 14. report_violation — unknown type
# ---------------------------------------------------------------------------


def test_report_violation_unknown_type():
    from app.modules.exam_proctoring.service import ProctoringError, report_violation

    with pytest.raises(ProctoringError, match="unknown violation_type"):
        report_violation(session_id=1, violation_type="cheat_sheet",
                         confidence=0.5, snapshot_ref="", tenant_id=1)


# ---------------------------------------------------------------------------
# 15. report_violation — confidence out of range
# ---------------------------------------------------------------------------


def test_report_violation_bad_confidence():
    from app.modules.exam_proctoring.service import ProctoringError, report_violation

    with pytest.raises(ProctoringError, match="confidence must be between"):
        report_violation(session_id=1, violation_type="gaze_away",
                         confidence=1.5, snapshot_ref="", tenant_id=1)


# ---------------------------------------------------------------------------
# 16. report_violation — session not active
# ---------------------------------------------------------------------------


def test_report_violation_ended_session_raises():
    session = _make_session(status="ended")
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[session]):
        from app.modules.exam_proctoring.service import ProctoringError, report_violation

        with pytest.raises(ProctoringError, match="cannot report violation"):
            report_violation(session_id=1, violation_type="tab_switch",
                             confidence=0.9, snapshot_ref="", tenant_id=42)


# ---------------------------------------------------------------------------
# 17. review_violation — happy path
# ---------------------------------------------------------------------------


def test_review_violation():
    violation = _make_violation(reviewed=False)
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[violation]),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
    ):
        from app.modules.exam_proctoring.service import review_violation

        result = review_violation(
            violation_id=100, resolution="False positive", tenant_id=42
        )

        assert result.reviewed is True
        update_payload = mock_update.call_args[0][2]
        assert update_payload["reviewed"] is True
        assert update_payload["resolution"] == "False positive"


# ---------------------------------------------------------------------------
# 18. review_violation — already reviewed
# ---------------------------------------------------------------------------


def test_review_already_reviewed_raises():
    violation = _make_violation(reviewed=True)
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[violation]):
        from app.modules.exam_proctoring.service import ProctoringError, review_violation

        with pytest.raises(ProctoringError, match="already reviewed"):
            review_violation(violation_id=100, resolution="ok", tenant_id=42)


# ---------------------------------------------------------------------------
# 19. review_violation — missing resolution
# ---------------------------------------------------------------------------


def test_review_violation_missing_resolution():
    from app.modules.exam_proctoring.service import ProctoringError, review_violation

    with pytest.raises(ProctoringError, match="resolution"):
        review_violation(violation_id=100, resolution="", tenant_id=42)


# ---------------------------------------------------------------------------
# 20. list_violations — filters by session_id
# ---------------------------------------------------------------------------


def test_list_violations_filters():
    rows = [
        _make_violation(id_=1, session_id=1),
        _make_violation(id_=2, session_id=2),
        _make_violation(id_=3, session_id=1, violation_type="multiple_faces"),
    ]
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=rows):
        from app.modules.exam_proctoring.service import list_violations

        result = list_violations(session_id=1, tenant_id=42)
        assert len(result) == 2
        assert all(r.session_id == 1 for r in result)


# ---------------------------------------------------------------------------
# 21. create_proctoring_config — happy path
# ---------------------------------------------------------------------------


def test_create_proctoring_config():
    with patch(f"{MODULE}.create_entity_for_tenant") as mock_create:
        mock_create.return_value = {"id": 50}
        from app.modules.exam_proctoring.service import create_proctoring_config

        rules = {"max_gaze_away_sec": 5, "allow_bathroom_break": True}
        result = create_proctoring_config(exam_id=10, rules=rules, tenant_id=42)

        assert result.config_id == 50
        assert result.rules == rules
        payload = mock_create.call_args[0][1]
        assert payload["rules"] == rules


# ---------------------------------------------------------------------------
# 22. get_proctoring_config — returns config or None
# ---------------------------------------------------------------------------


def test_get_proctoring_config_found():
    rows = [{"id": 50, "exam_id": 10, "rules": {"max_gaze_away_sec": 5}}]
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=rows):
        from app.modules.exam_proctoring.service import get_proctoring_config

        result = get_proctoring_config(exam_id=10, tenant_id=42)

        assert result is not None
        assert result.config_id == 50
        assert result.rules["max_gaze_away_sec"] == 5


def test_get_proctoring_config_not_found():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[]):
        from app.modules.exam_proctoring.service import get_proctoring_config

        result = get_proctoring_config(exam_id=99, tenant_id=42)
        assert result is None
