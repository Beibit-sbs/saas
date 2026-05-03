"""Tests for Phase XL — Student Feedback Module."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.modules.student_feedback.service import (
    FEEDBACK_STATES,
    LOW_SATISFACTION_THRESHOLD,
    SATISFACTION_MAX,
    _anonymize,
    analyze_form,
    close_form,
    create_feedback_form,
    get_form_analytics,
    list_forms,
    open_collecting,
    submit_feedback,
)

TENANT = 1


# ─── helpers ──────────────────────────────────────────────────────────────────

def _form(id_="f1", course_id="c1", status="OPEN", anonymous=True):
    return {"id": id_, "course_id": course_id, "title": "Test Form",
            "status": status, "anonymous": anonymous, "tenant_id": TENANT}


def _response(form_id="f1", rating=4.0, student_hash="abc"):
    return {"id": "r1", "form_id": form_id, "student_hash": student_hash,
            "rating": rating, "comment": "", "tenant_id": TENANT}


# ─── constants ────────────────────────────────────────────────────────────────

def test_feedback_states():
    assert FEEDBACK_STATES == {"OPEN", "COLLECTING", "CLOSED", "ANALYZED"}


def test_low_satisfaction_threshold():
    assert LOW_SATISFACTION_THRESHOLD == 3.0


def test_satisfaction_max():
    assert SATISFACTION_MAX == 5.0


# ─── anonymize ────────────────────────────────────────────────────────────────

def test_anonymize_is_deterministic():
    h1 = _anonymize("student1", 1)
    h2 = _anonymize("student1", 1)
    assert h1 == h2


def test_anonymize_differs_by_tenant():
    h1 = _anonymize("student1", 1)
    h2 = _anonymize("student1", 2)
    assert h1 != h2


def test_anonymize_no_pii_in_output():
    result = _anonymize("real_student_name_or_email@example.com", 1)
    assert "real_student_name" not in result
    assert "@" not in result


# ─── create_feedback_form ─────────────────────────────────────────────────────

def test_create_feedback_form_success():
    with patch("app.modules.student_feedback.service.create_entity_for_tenant",
               return_value={"id": "f1"}):
        result = create_feedback_form(TENANT, course_id="c1", title="Course Survey")
    assert result["form_id"] == "f1"
    assert result["status"] == "OPEN"
    assert result["anonymous"] is True


def test_create_feedback_form_missing_course():
    with pytest.raises(ValueError, match="course_id"):
        create_feedback_form(TENANT, course_id="", title="Survey")


def test_create_feedback_form_missing_title():
    with pytest.raises(ValueError, match="title"):
        create_feedback_form(TENANT, course_id="c1", title="")


def test_create_feedback_form_invalid_tenant():
    with pytest.raises(ValueError, match="tenant_id"):
        create_feedback_form(0, course_id="c1", title="Survey")


# ─── open_collecting ──────────────────────────────────────────────────────────

def test_open_collecting_success():
    form = _form(status="OPEN")
    with patch("app.modules.student_feedback.service.list_entities_for_tenant", return_value=[form]):
        result = open_collecting(TENANT, form_id="f1")
    assert result["status"] == "COLLECTING"


def test_open_collecting_wrong_status():
    form = _form(status="CLOSED")
    with patch("app.modules.student_feedback.service.list_entities_for_tenant", return_value=[form]):
        with pytest.raises(ValueError, match="Cannot transition"):
            open_collecting(TENANT, form_id="f1")


# ─── submit_feedback ──────────────────────────────────────────────────────────

def test_submit_feedback_anonymous_fires_event():
    form = _form(status="COLLECTING")
    with (
        patch("app.modules.student_feedback.service.list_entities_for_tenant", return_value=[form]),
        patch("app.modules.student_feedback.service.create_entity_for_tenant",
              return_value={"id": "r1"}),
        patch("app.modules.student_feedback.service.EventPublisher") as mock_pub,
    ):
        result = submit_feedback(TENANT, form_id="f1", student_id="st1", rating=4.0)
    assert result["response_id"] == "r1"
    assert result["rating"] == 4.0
    call_kwargs = mock_pub.return_value.publish_event.call_args[1]
    assert call_kwargs["event_type"] == "feedback.submitted"


def test_submit_feedback_invalid_rating_high():
    form = _form(status="COLLECTING")
    with patch("app.modules.student_feedback.service.list_entities_for_tenant", return_value=[form]):
        with pytest.raises(ValueError, match="rating must be between"):
            submit_feedback(TENANT, form_id="f1", student_id="st1", rating=6.0)


def test_submit_feedback_invalid_rating_low():
    form = _form(status="COLLECTING")
    with patch("app.modules.student_feedback.service.list_entities_for_tenant", return_value=[form]):
        with pytest.raises(ValueError, match="rating must be between"):
            submit_feedback(TENANT, form_id="f1", student_id="st1", rating=0.0)


def test_submit_feedback_form_not_collecting():
    form = _form(status="OPEN")
    with patch("app.modules.student_feedback.service.list_entities_for_tenant", return_value=[form]):
        with pytest.raises(ValueError, match="COLLECTING"):
            submit_feedback(TENANT, form_id="f1", student_id="st1", rating=3.5)


# ─── close_form ───────────────────────────────────────────────────────────────

def test_close_form_success():
    form = _form(status="COLLECTING")
    with patch("app.modules.student_feedback.service.list_entities_for_tenant", return_value=[form]):
        result = close_form(TENANT, form_id="f1")
    assert result["status"] == "CLOSED"


def test_close_form_wrong_status():
    form = _form(status="OPEN")
    with patch("app.modules.student_feedback.service.list_entities_for_tenant", return_value=[form]):
        with pytest.raises(ValueError, match="Cannot transition"):
            close_form(TENANT, form_id="f1")


# ─── analyze_form ─────────────────────────────────────────────────────────────

def test_analyze_form_fires_analysis_complete():
    form = _form(status="CLOSED")
    responses = [_response(rating=4.0), _response(rating=5.0)]
    with (
        patch("app.modules.student_feedback.service.list_entities_for_tenant",
              side_effect=[form, responses] if False else lambda *a, **kw: (
                  [form] if kw.get("entity_type") == "feedback_forms" else responses
              )),
        patch("app.modules.student_feedback.service.create_entity_for_tenant",
              return_value={"id": "an1"}),
        patch("app.modules.student_feedback.service.EventPublisher") as mock_pub,
    ):
        # Use direct mock sequencing
        with patch("app.modules.student_feedback.service.list_entities_for_tenant",
                   side_effect=[[form], responses]):
            result = analyze_form(TENANT, form_id="f1")
    assert result["status"] == "ANALYZED"
    assert result["response_count"] == 2
    assert result["avg_rating"] == pytest.approx(4.5)
    assert result["low_satisfaction_alert"] is False


def test_analyze_form_fires_low_satisfaction_event():
    form = _form(status="CLOSED")
    responses = [_response(rating=2.0), _response(rating=2.5)]
    with (
        patch("app.modules.student_feedback.service.list_entities_for_tenant",
              side_effect=[[form], responses]),
        patch("app.modules.student_feedback.service.create_entity_for_tenant",
              return_value={"id": "an1"}),
        patch("app.modules.student_feedback.service.EventPublisher") as mock_pub,
    ):
        result = analyze_form(TENANT, form_id="f1")
    assert result["low_satisfaction_alert"] is True
    event_calls = [c[1]["event_type"] for c in mock_pub.return_value.publish_event.call_args_list]
    assert "feedback.analysis_complete" in event_calls
    assert "feedback.low_satisfaction" in event_calls


# ─── list_forms ───────────────────────────────────────────────────────────────

def test_list_forms_unfiltered():
    forms = [_form(id_="f1"), _form(id_="f2", course_id="c2")]
    with patch("app.modules.student_feedback.service.list_entities_for_tenant", return_value=forms):
        result = list_forms(TENANT)
    assert len(result) == 2


def test_list_forms_by_course():
    forms = [_form(id_="f1", course_id="c1"), _form(id_="f2", course_id="c2")]
    with patch("app.modules.student_feedback.service.list_entities_for_tenant", return_value=forms):
        result = list_forms(TENANT, course_id="c1")
    assert len(result) == 1
    assert result[0]["id"] == "f1"


def test_list_forms_by_status():
    forms = [_form(id_="f1", status="OPEN"), _form(id_="f2", status="CLOSED")]
    with patch("app.modules.student_feedback.service.list_entities_for_tenant", return_value=forms):
        result = list_forms(TENANT, status="OPEN")
    assert len(result) == 1
    assert result[0]["id"] == "f1"
