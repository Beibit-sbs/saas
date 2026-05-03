"""LXXXIV - Grades Service Hardening (10-step contract).

Tests:
1. submit_grade emits events after persist and records metric
2. submit_grade duplicate guard raises DomainValidationError
3. change_grade records metric after persist
4. change_grade invalid version raises DomainValidationError
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.module_helpers.service_validation import (
    DomainValidationError,
    OptimisticLockConflictError,
)
from app.modules.enrollments.models import EnrollmentStatus
from app.modules.grades.schemas import GradeChangeSchema, GradeSubmitSchema
from app.modules.grades.service import GradeLifecycleService


@pytest.mark.asyncio
async def test_submit_grade_emits_events_after_persist_and_records_metric(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = MagicMock()
    db.add = MagicMock()
    db.flush = MagicMock()
    db.rollback = MagicMock()

    committed = {"done": False}
    events: list[str] = []
    metrics: list[str] = []

    def _commit() -> None:
        committed["done"] = True

    def _refresh(submission: object) -> None:
        now = datetime(2026, 1, 1, tzinfo=UTC)
        if getattr(submission, "id", None) is None:
            setattr(submission, "id", 77)
        if getattr(submission, "submitted_at", None) is None:
            setattr(submission, "submitted_at", now)
        if getattr(submission, "version", None) is None:
            setattr(submission, "version", 1)

    db.commit.side_effect = _commit
    db.refresh.side_effect = _refresh

    service = GradeLifecycleService(db_session=db)

    enrollment = SimpleNamespace(
        id=11,
        tenant_id=10,
        student_profile_id=501,
        course_id=301,
        term_id=401,
        enrollment_status=EnrollmentStatus.ENROLLED,
        grade_code=None,
        grade_points=None,
        version=1,
        updated_by="teacher@example.com",
    )

    monkeypatch.setattr(service, "_load_enrollment", lambda tid, eid: enrollment)
    monkeypatch.setattr(service, "_check_term_submission_window_open", lambda tid, term_id: None)
    monkeypatch.setattr(service, "_check_section_not_cancelled", lambda tid, eid: None)
    monkeypatch.setattr(service, "_load_course", lambda tid, cid: SimpleNamespace(id=cid, tenant_id=tid))
    monkeypatch.setattr(
        service,
        "_load_grade_submission",
        lambda tid, enrollment_id: None,
    )
    monkeypatch.setattr(service, "_load_grading_scale", lambda tid, sid: SimpleNamespace(id=sid, is_active=True))
    monkeypatch.setattr(
        service,
        "_load_scale_items",
        lambda tid, sid: [SimpleNamespace(grade_code="C", grade_points=Decimal("1.00"))],
    )
    monkeypatch.setattr(service, "_append_grade_history", lambda **kw: None)

    monkeypatch.setattr("app.modules.grades.service.assert_billing_write_allowed", lambda tid, action: None)
    monkeypatch.setattr("app.modules.grades.service.assert_quota_with_increment", lambda tid, metric, increment=1: None)
    monkeypatch.setattr("app.modules.grades.service.validate_grade_submission", AsyncMock(return_value=None))
    monkeypatch.setattr("app.modules.grades.service.log_admin_action", lambda **kw: None)
    monkeypatch.setattr("app.modules.grades.service.log_data_access_event", lambda **kw: None)

    def _fake_publish_event(self_pub, *, event_type, **kwargs):  # noqa: ANN001
        assert committed["done"] is True, "event must be emitted after commit/persist"
        events.append(str(event_type))

    monkeypatch.setattr("app.platform.events.publisher.EventPublisher.publish_event", _fake_publish_event)

    def _fake_metric(*, tenant_id: int, metric: str, value: int = 1) -> None:
        assert committed["done"] is True, "metric must be recorded after commit/persist"
        metrics.append(metric)

    monkeypatch.setattr("app.modules.grades.service.record_usage_event", _fake_metric)
    monkeypatch.setattr(
        "app.modules.brain_core.service.brain_core_service.process_signal",
        lambda signal: None,
    )

    request = GradeSubmitSchema(
        enrollment_id=11,
        grading_scale_id=5,
        grade_code="C",
        grade_points=Decimal("1.00"),
        metadata_json={},
    )

    result = await service.submit_grade(tenant_id=10, request=request, actor_id="teacher@example.com")

    assert result.entity.id == 77
    assert "grade.submitted" in events
    assert "academic.grade_risk.detected" in events
    assert "grades_submitted" in metrics


@pytest.mark.asyncio
async def test_submit_grade_duplicate_submit_is_idempotent_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = MagicMock()
    service = GradeLifecycleService(db_session=db)

    enrollment = SimpleNamespace(
        id=11,
        tenant_id=10,
        student_profile_id=501,
        course_id=301,
        term_id=401,
        enrollment_status=EnrollmentStatus.ENROLLED,
        version=1,
    )

    monkeypatch.setattr(service, "_load_enrollment", lambda tid, eid: enrollment)
    monkeypatch.setattr(service, "_check_term_submission_window_open", lambda tid, term_id: None)
    monkeypatch.setattr(service, "_check_section_not_cancelled", lambda tid, eid: None)
    monkeypatch.setattr(service, "_load_course", lambda tid, cid: SimpleNamespace(id=cid, tenant_id=tid))
    existing_submission = SimpleNamespace(
        id=999,
        tenant_id=10,
        enrollment_id=11,
        grade_code="B",
        grade_points=Decimal("3.00"),
        grading_scale_id=5,
        submitted_by="teacher@example.com",
        submitted_at=datetime(2026, 1, 1, tzinfo=UTC),
        version=1,
        metadata_json={},
    )
    monkeypatch.setattr(service, "_load_grade_submission", lambda tid, enrollment_id: existing_submission)

    monkeypatch.setattr("app.modules.grades.service.assert_billing_write_allowed", lambda tid, action: None)
    monkeypatch.setattr("app.modules.grades.service.assert_quota_with_increment", lambda tid, metric, increment=1: None)
    monkeypatch.setattr("app.modules.grades.service.validate_grade_submission", AsyncMock(return_value=None))

    request = GradeSubmitSchema(
        enrollment_id=11,
        grading_scale_id=5,
        grade_code="B",
        grade_points=Decimal("3.00"),
        metadata_json={},
    )

    result = await service.submit_grade(tenant_id=10, request=request, actor_id="teacher@example.com")
    assert result.idempotent_replay is True
    assert result.entity.id == 999


@pytest.mark.asyncio
async def test_change_grade_records_metric_after_persist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = MagicMock()
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock(side_effect=lambda obj: None)
    db.rollback = MagicMock()

    committed = {"done": False}
    metrics: list[str] = []

    def _commit() -> None:
        committed["done"] = True

    db.commit.side_effect = _commit

    service = GradeLifecycleService(db_session=db)

    enrollment = SimpleNamespace(
        id=11,
        tenant_id=10,
        student_profile_id=501,
        course_id=301,
        term_id=401,
        enrollment_status=EnrollmentStatus.ENROLLED,
        grade_code="B",
        grade_points=Decimal("3.00"),
        version=3,
        updated_by="teacher@example.com",
    )
    submission = SimpleNamespace(
        id=77,
        tenant_id=10,
        enrollment_id=11,
        grade_code="B",
        grade_points=Decimal("3.00"),
        grading_scale_id=5,
        submitted_by="teacher@example.com",
        submitted_at=datetime(2026, 1, 1, tzinfo=UTC),
        version=1,
        metadata_json={},
    )

    monkeypatch.setattr(service, "_load_enrollment", lambda tid, eid: enrollment)
    monkeypatch.setattr(service, "_load_grade_submission", lambda tid, eid: submission)
    monkeypatch.setattr(service, "_load_grading_scale", lambda tid, sid: SimpleNamespace(id=sid, is_active=True))
    monkeypatch.setattr(
        service,
        "_load_scale_items",
        lambda tid, sid: [SimpleNamespace(grade_code="C", grade_points=Decimal("2.00"))],
    )
    monkeypatch.setattr(service, "_append_grade_history", lambda **kw: None)

    monkeypatch.setattr("app.modules.grades.service.validate_grade_modification", AsyncMock(return_value=None))
    monkeypatch.setattr("app.modules.grades.service.log_admin_action", lambda **kw: None)
    monkeypatch.setattr("app.modules.grades.service.log_data_access_event", lambda **kw: None)

    def _fake_metric(*, tenant_id: int, metric: str, value: int = 1) -> None:
        assert committed["done"] is True, "metric must be recorded after commit/persist"
        metrics.append(metric)

    monkeypatch.setattr("app.modules.grades.service.record_usage_event", _fake_metric)

    request = GradeChangeSchema(
        enrollment_id=11,
        grading_scale_id=5,
        new_grade_code="C",
        new_grade_points=Decimal("2.00"),
        expected_version=1,
        reason="appeal review",
        metadata_json={},
    )

    result = await service.change_grade(tenant_id=10, request=request, actor_id="teacher@example.com")

    assert result.entity.grade_code == "C"
    assert "grades_submitted" in metrics


@pytest.mark.asyncio
async def test_change_grade_invalid_version_raises_optimistic_lock_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = MagicMock()
    service = GradeLifecycleService(db_session=db)

    enrollment = SimpleNamespace(
        id=11,
        tenant_id=10,
        student_profile_id=501,
        course_id=301,
        term_id=401,
        enrollment_status=EnrollmentStatus.ENROLLED,
        version=2,
    )
    submission = SimpleNamespace(
        id=77,
        tenant_id=10,
        enrollment_id=11,
        grade_code="B",
        grade_points=Decimal("3.00"),
        grading_scale_id=5,
        submitted_by="teacher@example.com",
        submitted_at=datetime(2026, 1, 1, tzinfo=UTC),
        version=2,
        metadata_json={},
    )

    monkeypatch.setattr(service, "_load_enrollment", lambda tid, eid: enrollment)
    monkeypatch.setattr(service, "_load_grade_submission", lambda tid, eid: submission)
    monkeypatch.setattr("app.modules.grades.service.validate_grade_modification", AsyncMock(return_value=None))

    request = GradeChangeSchema(
        enrollment_id=11,
        grading_scale_id=5,
        new_grade_code="A",
        new_grade_points=Decimal("4.00"),
        expected_version=1,
        reason="invalid version",
        metadata_json={},
    )

    with pytest.raises(OptimisticLockConflictError):
        await service.change_grade(tenant_id=10, request=request, actor_id="teacher@example.com")
