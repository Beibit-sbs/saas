"""Tests for Phase XLI — Internship Module."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.modules.internship.service import (
    APPLICATION_STATES,
    CONTRACT_STATES,
    accept_offer,
    activate_contract,
    apply,
    complete_contract,
    create_contract,
    create_posting,
    list_applications,
    list_postings,
    make_offer,
    reject_application,
    schedule_interview,
    shortlist,
    sign_contract,
)

TENANT = 1


# ─── helpers ──────────────────────────────────────────────────────────────────

def _app(id_="a1", posting_id="p1", student_id="st1", status="APPLIED"):
    return {"id": id_, "posting_id": posting_id, "student_id": student_id,
            "status": status, "tenant_id": TENANT}


def _contract(id_="c1", student_id="st1", company_id="co1", status="DRAFT"):
    return {"id": id_, "student_id": student_id, "company_id": company_id,
            "status": status, "tenant_id": TENANT}


# ─── constants ────────────────────────────────────────────────────────────────

def test_application_states():
    assert APPLICATION_STATES == {"APPLIED", "SHORTLISTED", "INTERVIEW", "OFFERED", "ACCEPTED", "REJECTED"}


def test_contract_states():
    assert CONTRACT_STATES == {"DRAFT", "SIGNED", "ACTIVE", "COMPLETED"}


# ─── create_posting ───────────────────────────────────────────────────────────

def test_create_posting_success():
    with patch("app.modules.internship.service.create_entity_for_tenant",
               return_value={"id": "p1"}):
        result = create_posting(TENANT, company_id="co1", title="Backend Intern", slots=2)
    assert result["posting_id"] == "p1"
    assert result["status"] == "OPEN"
    assert result["slots"] == 2


def test_create_posting_missing_company():
    with pytest.raises(ValueError, match="company_id"):
        create_posting(TENANT, company_id="", title="Intern")


def test_create_posting_missing_title():
    with pytest.raises(ValueError, match="title"):
        create_posting(TENANT, company_id="co1", title="")


def test_create_posting_zero_slots():
    with pytest.raises(ValueError, match="slots"):
        create_posting(TENANT, company_id="co1", title="Intern", slots=0)


def test_create_posting_invalid_tenant():
    with pytest.raises(ValueError, match="tenant_id"):
        create_posting(0, company_id="co1", title="Intern")


# ─── apply ────────────────────────────────────────────────────────────────────

def test_apply_success_fires_event():
    with (
        patch("app.modules.internship.service.create_entity_for_tenant",
              return_value={"id": "a1"}),
        patch("app.modules.internship.service.EventPublisher") as mock_pub,
    ):
        result = apply(TENANT, posting_id="p1", student_id="st1", cover_letter="Hi!")
    assert result["application_id"] == "a1"
    assert result["status"] == "APPLIED"
    call_kwargs = mock_pub.return_value.publish_event.call_args[1]
    assert call_kwargs["event_type"] == "internship.application_submitted"


def test_apply_missing_student():
    with pytest.raises(ValueError, match="student_id"):
        apply(TENANT, posting_id="p1", student_id="")


def test_apply_missing_posting():
    with pytest.raises(ValueError, match="posting_id"):
        apply(TENANT, posting_id="", student_id="st1")


# ─── application FSM ──────────────────────────────────────────────────────────

def test_shortlist_success():
    app = _app(status="APPLIED")
    with patch("app.modules.internship.service.list_entities_for_tenant", return_value=[app]):
        result = shortlist(TENANT, application_id="a1")
    assert result["status"] == "SHORTLISTED"


def test_shortlist_wrong_status():
    app = _app(status="OFFERED")
    with patch("app.modules.internship.service.list_entities_for_tenant", return_value=[app]):
        with pytest.raises(ValueError, match="Cannot transition"):
            shortlist(TENANT, application_id="a1")


def test_schedule_interview_success():
    app = _app(status="SHORTLISTED")
    with (
        patch("app.modules.internship.service.list_entities_for_tenant", return_value=[app]),
        patch("app.modules.internship.service.create_entity_for_tenant", return_value={"id": "i1"}),
    ):
        result = schedule_interview(TENANT, application_id="a1", interview_date="2026-06-01")
    assert result["status"] == "INTERVIEW"


def test_make_offer_fires_event():
    app = _app(status="INTERVIEW")
    with (
        patch("app.modules.internship.service.list_entities_for_tenant", return_value=[app]),
        patch("app.modules.internship.service.EventPublisher") as mock_pub,
    ):
        result = make_offer(TENANT, application_id="a1")
    assert result["status"] == "OFFERED"
    call_kwargs = mock_pub.return_value.publish_event.call_args[1]
    assert call_kwargs["event_type"] == "internship.offer_received"


def test_accept_offer_success():
    app = _app(status="OFFERED")
    with patch("app.modules.internship.service.list_entities_for_tenant", return_value=[app]):
        result = accept_offer(TENANT, application_id="a1")
    assert result["status"] == "ACCEPTED"


def test_reject_from_applied():
    app = _app(status="APPLIED")
    with patch("app.modules.internship.service.list_entities_for_tenant", return_value=[app]):
        result = reject_application(TENANT, application_id="a1", reason="Not qualified")
    assert result["status"] == "REJECTED"


def test_reject_wrong_status():
    app = _app(status="ACCEPTED")
    with patch("app.modules.internship.service.list_entities_for_tenant", return_value=[app]):
        with pytest.raises(ValueError, match="Cannot transition"):
            reject_application(TENANT, application_id="a1")


# ─── contracts ────────────────────────────────────────────────────────────────

def test_create_contract_success():
    with patch("app.modules.internship.service.create_entity_for_tenant",
               return_value={"id": "c1"}):
        result = create_contract(TENANT, application_id="a1", student_id="st1",
                                 company_id="co1", start_date="2026-07-01", end_date="2026-09-30")
    assert result["contract_id"] == "c1"
    assert result["status"] == "DRAFT"


def test_create_contract_missing_dates():
    with pytest.raises(ValueError, match="start_date"):
        create_contract(TENANT, application_id="a1", student_id="st1",
                        company_id="co1", start_date="", end_date="2026-09-30")


def test_sign_contract_fires_event():
    contract = _contract(status="DRAFT")
    with (
        patch("app.modules.internship.service.list_entities_for_tenant", return_value=[contract]),
        patch("app.modules.internship.service.EventPublisher") as mock_pub,
    ):
        result = sign_contract(TENANT, contract_id="c1")
    assert result["status"] == "SIGNED"
    call_kwargs = mock_pub.return_value.publish_event.call_args[1]
    assert call_kwargs["event_type"] == "internship.contract_signed"


def test_activate_contract_success():
    contract = _contract(status="SIGNED")
    with patch("app.modules.internship.service.list_entities_for_tenant", return_value=[contract]):
        result = activate_contract(TENANT, contract_id="c1")
    assert result["status"] == "ACTIVE"


def test_complete_contract_with_grade():
    contract = _contract(status="ACTIVE")
    with (
        patch("app.modules.internship.service.list_entities_for_tenant", return_value=[contract]),
        patch("app.modules.internship.service.EventPublisher") as mock_pub,
    ):
        result = complete_contract(TENANT, contract_id="c1", grade=85.0)
    assert result["status"] == "COMPLETED"
    assert result["grade"] == 85.0
    assert result["completion_risk"] is False
    event_types = [c[1]["event_type"] for c in mock_pub.return_value.publish_event.call_args_list]
    assert "internship.completed" in event_types
    assert "internship.completion_risk" not in event_types


def test_complete_contract_without_grade_fires_risk():
    contract = _contract(status="ACTIVE")
    with (
        patch("app.modules.internship.service.list_entities_for_tenant", return_value=[contract]),
        patch("app.modules.internship.service.EventPublisher") as mock_pub,
    ):
        result = complete_contract(TENANT, contract_id="c1", grade=None)
    assert result["completion_risk"] is True
    event_types = [c[1]["event_type"] for c in mock_pub.return_value.publish_event.call_args_list]
    assert "internship.completion_risk" in event_types


# ─── list helpers ─────────────────────────────────────────────────────────────

def test_list_postings_unfiltered():
    postings = [{"id": "p1", "company_id": "co1"}, {"id": "p2", "company_id": "co2"}]
    with patch("app.modules.internship.service.list_entities_for_tenant", return_value=postings):
        result = list_postings(TENANT)
    assert len(result) == 2


def test_list_applications_by_student():
    apps = [_app(id_="a1", student_id="st1"), _app(id_="a2", student_id="st2")]
    with patch("app.modules.internship.service.list_entities_for_tenant", return_value=apps):
        result = list_applications(TENANT, student_id="st1")
    assert len(result) == 1
    assert result[0]["id"] == "a1"
