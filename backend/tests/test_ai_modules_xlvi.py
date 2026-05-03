"""Phase XLVI — AI Modules tests (30 tests).

XLVI.1 student_ai_tutor    — tests 1-10
XLVI.2 ai_plagiarism       — tests 11-20
XLVI.3 ai_admissions_scoring — tests 21-30
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


def _make_row(id_val: str, **kwargs) -> dict:
    return {"id": id_val, **kwargs}


# ═══════════════════════════════════════════════════════════════
# XLVI.1 — student_ai_tutor (tests 1-10)
# ═══════════════════════════════════════════════════════════════

class TestTutorStates:
    def test_session_states_complete(self):
        from app.modules.student_ai_tutor.service import SESSION_STATES
        assert SESSION_STATES == frozenset({"ACTIVE", "ENDED", "ABANDONED"})

    def test_struggle_threshold_positive(self):
        from app.modules.student_ai_tutor.service import STRUGGLE_THRESHOLD
        assert STRUGGLE_THRESHOLD > 0


class TestStartSession:
    def test_start_session_fires_event(self):
        from app.modules.student_ai_tutor.service import start_session
        mock_pub = MagicMock()
        mock_row = _make_row("s1", student_id="u1", topic="Algebra", status="ACTIVE", struggle_count=0, tenant_id=1)
        with (
            patch("app.modules.student_ai_tutor.service.create_entity_for_tenant", return_value=mock_row),
            patch("app.modules.student_ai_tutor.service.EventPublisher", return_value=mock_pub),
        ):
            result = start_session(1, student_id="u1", topic="Algebra")
        assert result["status"] == "ACTIVE"
        assert result["session_id"] == "s1"
        call_kwargs = mock_pub.publish_event.call_args[1]
        assert call_kwargs["event_type"] == "tutor_session.started"

    def test_start_session_missing_student(self):
        from app.modules.student_ai_tutor.service import start_session
        with pytest.raises(ValueError, match="student_id"):
            start_session(1, student_id="", topic="Algebra")

    def test_start_session_missing_topic(self):
        from app.modules.student_ai_tutor.service import start_session
        with pytest.raises(ValueError, match="topic"):
            start_session(1, student_id="u1", topic="")

    def test_start_session_bad_tenant(self):
        from app.modules.student_ai_tutor.service import start_session
        with pytest.raises(ValueError, match="tenant_id"):
            start_session(0, student_id="u1", topic="Algebra")


class TestSessionOperations:
    def _session_row(self, status="ACTIVE", struggle_count=0) -> dict:
        return _make_row("s1", student_id="u1", topic="Algebra", status=status, struggle_count=struggle_count, tenant_id=1)

    def test_send_message_returns_response(self):
        from app.modules.student_ai_tutor.service import send_message
        with (
            patch("app.modules.student_ai_tutor.service.list_entities_for_tenant", return_value=[self._session_row()]),
            patch("app.modules.student_ai_tutor.service.EventPublisher"),
        ):
            result = send_message(1, session_id="s1", message="What is x?")
        assert "response" in result
        assert "AI" in result["response"]

    def test_send_message_struggle_fires_intervention(self):
        from app.modules.student_ai_tutor.service import send_message, STRUGGLE_THRESHOLD
        mock_pub = MagicMock()
        # struggle_count already at threshold-1, one more triggers
        row = self._session_row(struggle_count=STRUGGLE_THRESHOLD - 1)
        with (
            patch("app.modules.student_ai_tutor.service.list_entities_for_tenant", return_value=[row]),
            patch("app.modules.student_ai_tutor.service.EventPublisher", return_value=mock_pub),
        ):
            send_message(1, session_id="s1", message="I don't understand", is_struggle=True)
        call_kwargs = mock_pub.publish_event.call_args[1]
        assert call_kwargs["event_type"] == "student.needs_intervention"

    def test_detect_breakthrough_fires_event(self):
        from app.modules.student_ai_tutor.service import detect_breakthrough
        mock_pub = MagicMock()
        with (
            patch("app.modules.student_ai_tutor.service.list_entities_for_tenant", return_value=[self._session_row()]),
            patch("app.modules.student_ai_tutor.service.EventPublisher", return_value=mock_pub),
        ):
            result = detect_breakthrough(1, session_id="s1")
        assert result["breakthrough"] is True
        call_kwargs = mock_pub.publish_event.call_args[1]
        assert call_kwargs["event_type"] == "learning.breakthrough_detected"

    def test_end_session_success(self):
        from app.modules.student_ai_tutor.service import end_session
        with (
            patch("app.modules.student_ai_tutor.service.list_entities_for_tenant", return_value=[self._session_row()]),
            patch("app.modules.student_ai_tutor.service.EventPublisher"),
        ):
            result = end_session(1, session_id="s1")
        assert result["status"] == "ENDED"

    def test_list_sessions_by_student(self):
        from app.modules.student_ai_tutor.service import list_sessions
        rows = [
            _make_row("s1", student_id="u1", status="ACTIVE"),
            _make_row("s2", student_id="u2", status="ENDED"),
            _make_row("s3", student_id="u1", status="ENDED"),
        ]
        with patch("app.modules.student_ai_tutor.service.list_entities_for_tenant", return_value=rows):
            result = list_sessions(1, student_id="u1")
        assert len(result) == 2
        assert all(r["student_id"] == "u1" for r in result)


# ═══════════════════════════════════════════════════════════════
# XLVI.2 — ai_plagiarism (tests 11-20)
# ═══════════════════════════════════════════════════════════════

class TestScanStates:
    def test_scan_states_complete(self):
        from app.modules.ai_plagiarism.service import SCAN_STATES
        assert SCAN_STATES == frozenset({"SUBMITTED", "SCANNING", "RESULT_READY"})

    def test_thresholds_ordered(self):
        from app.modules.ai_plagiarism.service import OK_THRESHOLD, WARNING_THRESHOLD
        assert 0 < OK_THRESHOLD < WARNING_THRESHOLD < 1.0


class TestSubmitScan:
    def test_submit_scan_success(self):
        from app.modules.ai_plagiarism.service import submit_scan
        mock_row = _make_row("sc1", document_id="doc1", status="SUBMITTED", tenant_id=1)
        with patch("app.modules.ai_plagiarism.service.create_entity_for_tenant", return_value=mock_row):
            result = submit_scan(1, document_id="doc1", content="This is my essay...")
        assert result["status"] == "SUBMITTED"
        assert result["scan_id"] == "sc1"

    def test_submit_scan_missing_content(self):
        from app.modules.ai_plagiarism.service import submit_scan
        with pytest.raises(ValueError, match="content"):
            submit_scan(1, document_id="doc1", content="")

    def test_submit_scan_missing_document(self):
        from app.modules.ai_plagiarism.service import submit_scan
        with pytest.raises(ValueError, match="document_id"):
            submit_scan(1, document_id="", content="Essay text here")


class TestScanFSM:
    def _scan_row(self, status: str, doc_id: str = "doc1") -> dict:
        return _make_row("sc1", document_id=doc_id, status=status, similarity_score=None, verdict=None, tenant_id=1)

    def test_start_scanning_success(self):
        from app.modules.ai_plagiarism.service import start_scanning
        with (
            patch("app.modules.ai_plagiarism.service.list_entities_for_tenant", return_value=[self._scan_row("SUBMITTED")]),
            patch("app.modules.ai_plagiarism.service.EventPublisher"),
        ):
            result = start_scanning(1, scan_id="sc1")
        assert result["status"] == "SCANNING"

    def test_complete_scan_ok_verdict(self):
        from app.modules.ai_plagiarism.service import complete_scan
        mock_pub = MagicMock()
        with (
            patch("app.modules.ai_plagiarism.service.list_entities_for_tenant", return_value=[self._scan_row("SCANNING")]),
            patch("app.modules.ai_plagiarism.service.EventPublisher", return_value=mock_pub),
        ):
            result = complete_scan(1, scan_id="sc1", similarity_score=0.05)
        assert result["verdict"] == "OK"
        assert mock_pub.publish_event.call_count == 1  # only scan.complete

    def test_complete_scan_warning_verdict(self):
        from app.modules.ai_plagiarism.service import complete_scan
        mock_pub = MagicMock()
        with (
            patch("app.modules.ai_plagiarism.service.list_entities_for_tenant", return_value=[self._scan_row("SCANNING")]),
            patch("app.modules.ai_plagiarism.service.EventPublisher", return_value=mock_pub),
        ):
            result = complete_scan(1, scan_id="sc1", similarity_score=0.20)
        assert result["verdict"] == "WARNING"

    def test_complete_scan_violation_fires_plagiarism_event(self):
        from app.modules.ai_plagiarism.service import complete_scan
        mock_pub = MagicMock()
        with (
            patch("app.modules.ai_plagiarism.service.list_entities_for_tenant", return_value=[self._scan_row("SCANNING")]),
            patch("app.modules.ai_plagiarism.service.EventPublisher", return_value=mock_pub),
        ):
            result = complete_scan(1, scan_id="sc1", similarity_score=0.45)
        assert result["verdict"] == "VIOLATION"
        # scan.complete + plagiarism.detected
        assert mock_pub.publish_event.call_count == 2
        event_types = [c[1]["event_type"] for c in mock_pub.publish_event.call_args_list]
        assert "plagiarism.detected" in event_types

    def test_complete_scan_invalid_score(self):
        from app.modules.ai_plagiarism.service import complete_scan
        with (
            patch("app.modules.ai_plagiarism.service.list_entities_for_tenant", return_value=[self._scan_row("SCANNING")]),
            patch("app.modules.ai_plagiarism.service.EventPublisher"),
        ):
            with pytest.raises(ValueError, match="similarity_score"):
                complete_scan(1, scan_id="sc1", similarity_score=1.5)

    def test_scan_list_filter_by_status(self):
        from app.modules.ai_plagiarism.service import list_scans
        rows = [
            _make_row("s1", status="SUBMITTED"),
            _make_row("s2", status="SCANNING"),
            _make_row("s3", status="SUBMITTED"),
        ]
        with patch("app.modules.ai_plagiarism.service.list_entities_for_tenant", return_value=rows):
            result = list_scans(1, status="SUBMITTED")
        assert len(result) == 2


# ═══════════════════════════════════════════════════════════════
# XLVI.3 — ai_admissions_scoring (tests 21-30)
# ═══════════════════════════════════════════════════════════════

class TestScoringStates:
    def test_score_states_complete(self):
        from app.modules.ai_admissions_scoring.service import SCORE_STATES
        assert SCORE_STATES == frozenset({"PENDING", "SCORED", "FLAGGED", "APPROVED", "REJECTED"})


class TestSubmitForScoring:
    def test_submit_success(self):
        from app.modules.ai_admissions_scoring.service import submit_for_scoring
        mock_row = _make_row("sc1", application_id="app1", status="PENDING", tenant_id=1)
        with patch("app.modules.ai_admissions_scoring.service.create_entity_for_tenant", return_value=mock_row):
            result = submit_for_scoring(1, application_id="app1", gpa=3.5, test_score=85, essay_length=600)
        assert result["status"] == "PENDING"
        assert result["scoring_id"] == "sc1"

    def test_submit_invalid_gpa(self):
        from app.modules.ai_admissions_scoring.service import submit_for_scoring
        with pytest.raises(ValueError, match="gpa"):
            submit_for_scoring(1, application_id="app1", gpa=5.0, test_score=85, essay_length=600)

    def test_submit_invalid_test_score(self):
        from app.modules.ai_admissions_scoring.service import submit_for_scoring
        with pytest.raises(ValueError, match="test_score"):
            submit_for_scoring(1, application_id="app1", gpa=3.5, test_score=150, essay_length=600)

    def test_submit_missing_application(self):
        from app.modules.ai_admissions_scoring.service import submit_for_scoring
        with pytest.raises(ValueError, match="application_id"):
            submit_for_scoring(1, application_id="", gpa=3.5, test_score=85, essay_length=600)


class TestScoringFSM:
    def _scoring_row(self, status: str, score=None) -> dict:
        return _make_row("sc1", application_id="app1", gpa=3.5, test_score=85, essay_length=600, score=score, status=status, tenant_id=1)

    def test_generate_score_fires_event(self):
        from app.modules.ai_admissions_scoring.service import generate_score
        mock_pub = MagicMock()
        with (
            patch("app.modules.ai_admissions_scoring.service.list_entities_for_tenant", return_value=[self._scoring_row("PENDING")]),
            patch("app.modules.ai_admissions_scoring.service.EventPublisher", return_value=mock_pub),
        ):
            result = generate_score(1, scoring_id="sc1")
        assert result["status"] == "SCORED"
        assert 0 <= result["score"] <= 1.0
        call_kwargs = mock_pub.publish_event.call_args[1]
        assert call_kwargs["event_type"] == "admissions.score_generated"

    def test_detect_anomaly_fires_event(self):
        from app.modules.ai_admissions_scoring.service import detect_anomaly
        mock_pub = MagicMock()
        with (
            patch("app.modules.ai_admissions_scoring.service.list_entities_for_tenant", return_value=[self._scoring_row("SCORED", score=0.9)]),
            patch("app.modules.ai_admissions_scoring.service.EventPublisher", return_value=mock_pub),
        ):
            result = detect_anomaly(1, scoring_id="sc1")
        assert result["status"] == "FLAGGED"
        call_kwargs = mock_pub.publish_event.call_args[1]
        assert call_kwargs["event_type"] == "admissions.anomaly_detected"

    def test_approve_scoring_success(self):
        from app.modules.ai_admissions_scoring.service import approve_scoring
        with (
            patch("app.modules.ai_admissions_scoring.service.list_entities_for_tenant", return_value=[self._scoring_row("SCORED")]),
            patch("app.modules.ai_admissions_scoring.service.EventPublisher"),
        ):
            result = approve_scoring(1, scoring_id="sc1")
        assert result["status"] == "APPROVED"

    def test_reject_scoring_success(self):
        from app.modules.ai_admissions_scoring.service import reject_scoring
        with (
            patch("app.modules.ai_admissions_scoring.service.list_entities_for_tenant", return_value=[self._scoring_row("SCORED")]),
            patch("app.modules.ai_admissions_scoring.service.EventPublisher"),
        ):
            result = reject_scoring(1, scoring_id="sc1")
        assert result["status"] == "REJECTED"

    def test_invalid_transition_from_pending(self):
        from app.modules.ai_admissions_scoring.service import detect_anomaly
        with (
            patch("app.modules.ai_admissions_scoring.service.list_entities_for_tenant", return_value=[self._scoring_row("PENDING")]),
            patch("app.modules.ai_admissions_scoring.service.EventPublisher"),
        ):
            with pytest.raises(ValueError, match="Cannot transition"):
                detect_anomaly(1, scoring_id="sc1")
