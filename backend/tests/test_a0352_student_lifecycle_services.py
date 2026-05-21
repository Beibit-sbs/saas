from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, TenantRequiredError
from app.modules.student_lifecycle import service


def _db() -> MagicMock:
    db = MagicMock(spec=Session)
    db.commit.return_value = None
    db.rollback.return_value = None
    return db


def test_create_applicant_enforces_flags() -> None:
    db = _db()
    request = SimpleNamespace(applicant_code="APP-1", program_interest="CS", entry_term="2026-FALL", notes=None, source_available=False, limitations=[])
    created = SimpleNamespace(id=1, status="DRAFT", human_review_required=True, automated_decision=False, provider_integration_enabled=False)
    with (
        patch("app.modules.student_lifecycle.service.repository.create_applicant", return_value=created) as mock_create,
        patch("app.modules.student_lifecycle.service.repository.record_applicant_status"),
        patch("app.modules.student_lifecycle.service.repository.create_audit_event"),
    ):
        result = service.create_applicant_service(db, 1, "actor-1", request)
    assert result is created
    kwargs = mock_create.call_args.kwargs
    assert kwargs["human_review_required"] is True
    assert kwargs["automated_decision"] is False
    assert kwargs["provider_integration_enabled"] is False


def test_invalid_applicant_transition_fails_closed() -> None:
    db = _db()
    current = SimpleNamespace(id=1, status="DRAFT", archived_at=None)
    with patch("app.modules.student_lifecycle.service.get_applicant_service", return_value=current):
        with pytest.raises(DomainValidationError):
            service.update_applicant_status_service(db, 1, "actor-1", 1, "ACCEPTED", "bad jump")


@pytest.mark.parametrize("tenant_id", [None, 0, -1, "bad"])
def test_invalid_tenant_fail_closed(tenant_id) -> None:
    db = _db()
    request = SimpleNamespace(applicant_code="APP-1", program_interest=None, entry_term=None, notes=None, source_available=False, limitations=[])
    with pytest.raises(TenantRequiredError):
        service.create_applicant_service(db, tenant_id, "actor-1", request)  # type: ignore[arg-type]


def test_generate_transcript_preview_hardcodes_unofficial_flags() -> None:
    db = _db()
    request = SimpleNamespace(student_id=11, academic_record_id=12, preview_payload={"preview": True}, limitations=[])
    created = SimpleNamespace(id=5, status="GENERATED_UNOFFICIAL_PREVIEW", official_document=False, human_review_required=True, automated_decision=False, provider_integration_enabled=False)
    with (
        patch("app.modules.student_lifecycle.service.repository.create_transcript_preview", return_value=created) as mock_create,
        patch("app.modules.student_lifecycle.service.repository.create_audit_event"),
    ):
        result = service.generate_transcript_preview_service(db, 1, "actor-2", request)
    assert result.official_document is False
    kwargs = mock_create.call_args.kwargs
    assert kwargs["official_document"] is False
    assert kwargs["automated_decision"] is False
    assert kwargs["provider_integration_enabled"] is False


def test_degree_progress_snapshot_never_sets_hidden_score() -> None:
    db = _db()
    request = SimpleNamespace(student_id=99, incomplete_data=True, completion_summary={}, limitations=[])
    created = SimpleNamespace(id=9, status="INCOMPLETE_DATA", hidden_score_present=False, human_review_required=True, automated_decision=False, provider_integration_enabled=False)
    with (
        patch("app.modules.student_lifecycle.service.repository.create_degree_progress_snapshot", return_value=created) as mock_create,
        patch("app.modules.student_lifecycle.service.repository.create_audit_event"),
    ):
        result = service.compute_degree_progress_snapshot_service(db, 1, "actor-3", request)
    assert result.hidden_score_present is False
    kwargs = mock_create.call_args.kwargs
    assert kwargs["hidden_score_present"] is False
    assert kwargs["human_review_required"] is True


def test_graduation_readiness_review_stays_human_review_required() -> None:
    db = _db()
    current = SimpleNamespace(id=8, status="INCOMPLETE_DATA", limitations_json=[])
    updated = SimpleNamespace(id=8, status="HUMAN_REVIEW_REQUIRED", human_review_required=True)
    request = SimpleNamespace(new_status="HUMAN_REVIEW_REQUIRED", note="manual review")
    with (
        patch("app.modules.student_lifecycle.service.get_degree_progress_snapshot_service", return_value=current),
        patch("app.modules.student_lifecycle.service.repository.update_degree_progress_snapshot", return_value=updated) as mock_update,
        patch("app.modules.student_lifecycle.service.repository.create_audit_event"),
    ):
        result = service.review_graduation_readiness_service(db, 1, "actor-4", 42, request)
    assert result.human_review_required is True
    assert mock_update.call_args.kwargs["human_review_required"] is True


def test_request_review_no_autonomous_decision() -> None:
    db = _db()
    current = SimpleNamespace(id=12, status="UNDER_REVIEW")
    updated = SimpleNamespace(id=12, status="DECISION_METADATA_RECORDED", automated_decision=False, provider_integration_enabled=False)
    request = SimpleNamespace(new_status="DECISION_METADATA_RECORDED", decision_note="manual")
    with (
        patch("app.modules.student_lifecycle.service.get_student_request_service", return_value=current),
        patch("app.modules.student_lifecycle.service.repository.update_student_request", return_value=updated) as mock_update,
        patch("app.modules.student_lifecycle.service.repository.create_audit_event"),
    ):
        result = service.review_student_request_service(db, 1, "actor-5", 12, request)
    assert result.automated_decision is False
    kwargs = mock_update.call_args.kwargs
    assert kwargs["automated_decision"] is False
    assert kwargs["provider_integration_enabled"] is False


def test_appeal_review_no_autonomous_decision() -> None:
    db = _db()
    current = SimpleNamespace(id=13, status="REVIEWER_REVIEW")
    updated = SimpleNamespace(id=13, status="DECISION_METADATA_RECORDED", automated_decision=False, provider_integration_enabled=False)
    request = SimpleNamespace(new_status="DECISION_METADATA_RECORDED", decision_note="committee")
    with (
        patch("app.modules.student_lifecycle.service.get_student_appeal_service", return_value=current),
        patch("app.modules.student_lifecycle.service.repository.update_student_appeal", return_value=updated) as mock_update,
        patch("app.modules.student_lifecycle.service.repository.create_audit_event"),
    ):
        result = service.review_student_appeal_service(db, 1, "actor-6", 13, request)
    assert result.automated_decision is False
    kwargs = mock_update.call_args.kwargs
    assert kwargs["automated_decision"] is False
    assert kwargs["provider_integration_enabled"] is False


def test_intervention_followup_never_exposes_hidden_score() -> None:
    db = _db()
    current = SimpleNamespace(id=44, status="OUTCOME_METADATA_RECORDED")
    updated = SimpleNamespace(id=44, status="CONTINUED", hidden_score_present=False)
    request = SimpleNamespace(outcome_note="continue support", continued=True)
    with (
        patch("app.modules.student_lifecycle.service.get_intervention_plan_service", return_value=current),
        patch("app.modules.student_lifecycle.service.repository.record_intervention_followup", return_value=updated),
        patch("app.modules.student_lifecycle.service.repository.create_audit_event"),
    ):
        result = service.record_intervention_followup_service(db, 1, "actor-7", 44, request)
    assert result.hidden_score_present is False


def test_dashboard_response_zeroes_automated_decisions() -> None:
    db = _db()
    with (
        patch("app.modules.student_lifecycle.service.repository.compute_student_lifecycle_dashboard_summary", return_value={
            "applicant_counts_by_status": {"DRAFT": 1},
            "student_counts_by_status": {"ACTIVE": 2},
            "enrollment_counts_by_status": {"ENROLLED": 3},
            "transcript_preview_counts": {"GENERATED_UNOFFICIAL_PREVIEW": 1},
            "degree_progress_counts": {"INCOMPLETE_DATA": 1},
            "request_counts_by_status": {"SUBMITTED": 1},
            "appeal_counts_by_status": {"REVIEWER_REVIEW": 1},
            "intervention_counts_by_status": {"CONTINUED": 1},
            "human_review_required_count": 5,
            "incomplete_data": False,
            "limitations": [],
        }),
        patch("app.modules.student_lifecycle.service.repository.create_audit_event"),
    ):
        result = service.get_student_lifecycle_dashboard_service(db, 1, "actor-8")
    assert result.fake_metrics is False
    assert result.provider_integration_enabled is False
    assert result.automated_decision_count == 0
    assert result.hidden_score_present is False
