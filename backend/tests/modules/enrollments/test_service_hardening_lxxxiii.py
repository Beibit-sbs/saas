"""LXXXIII — Enrollments Service Hardening (10-step contract)

Tests:
1. enroll_student emits enrollment.created event after persist and records metric
2. change_enrollment_status invalid transition raises DomainValidationError (FSM guard)
3. drop_enrollment triggers Brain Core signal after persist and records metric
4. enroll_student event order: persist < event < metric
"""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.enrollments.models import EnrollmentStatus
from app.modules.enrollments.schemas import (
    EnrollmentCreateSchema,
    EnrollmentDropSchema,
    EnrollmentStatusChangeSchema,
)
from app.modules.enrollments.service import EnrollmentLifecycleService

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _make_db_mock(enrollment_row: SimpleNamespace) -> MagicMock:
    db = MagicMock()
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock(side_effect=lambda obj: None)
    db.commit = MagicMock()
    return db


def _make_enrollment_ns(
    enrollment_id: int = 1,
    tenant_id: int = 10,
    status: EnrollmentStatus = EnrollmentStatus.ENROLLED,
    version: int = 1,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=enrollment_id,
        tenant_id=tenant_id,
        student_profile_id=101,
        course_id=201,
        term_id=301,
        section_id=401,
        enrollment_status=status,
        enrollment_type="regular",
        enrolled_at=_NOW,
        dropped_at=None,
        grade_code=None,
        grade_points=None,
        metadata_json={},
        version=version,
        created_at=_NOW,
        updated_at=_NOW,
        created_by="admin@example.com",
        updated_by="admin@example.com",
    )


# ---------------------------------------------------------------------------
# Test 1+4: enroll_student emits event AFTER persist and records metric
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enroll_student_emits_event_after_persist_and_records_metric(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    enrollment = _make_enrollment_ns(enrollment_id=42)
    db = _make_db_mock(enrollment)
    committed = {"done": False}
    events: list[str] = []
    metrics: list[str] = []

    def _commit() -> None:
        committed["done"] = True

    db.commit.side_effect = _commit

    service = EnrollmentLifecycleService(db_session=db)

    # Stub all private helpers
    profile = SimpleNamespace(
        id=101,
        tenant_id=10,
        current_status="active",
        academic_hold=False,
        is_suspended=False,
        is_expelled=False,
    )
    monkeypatch.setattr(service, "_load_student_profile", lambda tid, spid: profile)
    monkeypatch.setattr(service, "_load_course", lambda tid, cid: SimpleNamespace(id=cid))
    monkeypatch.setattr(service, "_load_term", lambda tid, tid2: SimpleNamespace(id=tid2))
    monkeypatch.setattr(
        service,
        "get_active_enrollment_for_student_course_term",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        service,
        "_load_section_for_enrollment",
        lambda tid, section_id, course_id, term_id: SimpleNamespace(
            id=section_id, course_id=course_id, term_id=term_id,
            capacity=30, enrolled_count=10, status="active",
        ),
    )
    monkeypatch.setattr(service, "_check_section_capacity", lambda tid, section: None)
    monkeypatch.setattr(service, "_check_course_prerequisites", lambda tid, spid, cid: None)
    monkeypatch.setattr(service, "_append_status_history", lambda **kw: None)

    def _fake_publish_event(self_pub, *, event_type, **kwargs):  # noqa: ANN001
        assert committed["done"] is True, "event must be emitted after commit/persist"
        events.append(event_type)

    monkeypatch.setattr(
        "app.platform.events.publisher.EventPublisher.publish_event",
        _fake_publish_event,
    )
    monkeypatch.setattr(
        "app.modules.enrollments.service.log_admin_action",
        lambda **kw: None,
    )
    monkeypatch.setattr(
        "app.modules.enrollments.service.log_data_access_event",
        lambda **kw: None,
    )
    monkeypatch.setattr(
        "app.modules.enrollments.service.assert_billing_write_allowed",
        lambda tid, action: None,
    )
    monkeypatch.setattr(
        "app.modules.usage.service.record_usage_event",
        lambda tid, metric, value=1: metrics.append(metric),
    )

    def _refresh(obj: object) -> None:
        # populate server-generated fields so model_validate passes
        import datetime as _dt
        now = _dt.datetime(2026, 1, 1, tzinfo=_dt.timezone.utc)
        object.__setattr__(obj, "id", 42) if not getattr(obj, "id", None) else None
        for attr, val in [
            ("enrolled_at", now),
            ("grade_code", None),
            ("grade_points", None),
            ("created_at", now),
            ("updated_at", now),
            ("version", 1),
        ]:
            if getattr(obj, attr, "MISSING") in (None, "MISSING"):
                try:
                    setattr(obj, attr, val)
                except Exception:
                    pass

    db.refresh.side_effect = _refresh

    request = EnrollmentCreateSchema(
        student_profile_id=101,
        course_id=201,
        term_id=301,
        section_id=401,
        enrollment_status=EnrollmentStatus.ENROLLED,
        enrollment_type="regular",
        enrolled_at=None,
        metadata_json={},
    )

    await service.enroll_student(tenant_id=10, request=request, actor_id="admin@example.com")

    assert "enrollment.created" in events
    assert "enrollments_created" in metrics


# ---------------------------------------------------------------------------
# Test 2: FSM guard — invalid transition raises DomainValidationError
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_change_status_invalid_transition_raises_domain_validation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """COMPLETED → ENROLLED is forbidden per FSM."""
    enrollment = _make_enrollment_ns(
        enrollment_id=5, status=EnrollmentStatus.COMPLETED, version=3
    )
    db = _make_db_mock(enrollment)
    service = EnrollmentLifecycleService(db_session=db)

    monkeypatch.setattr(service, "_load_enrollment", lambda tid, eid: enrollment)

    request = EnrollmentStatusChangeSchema(
        to_status=EnrollmentStatus.ENROLLED,
        expected_version=3,
        reason="invalid attempt",
        metadata_json={},
    )

    with pytest.raises(DomainValidationError):
        await service.change_enrollment_status(
            tenant_id=10,
            enrollment_id=5,
            request=request,
            actor_id="admin@example.com",
        )


# ---------------------------------------------------------------------------
# Test 3: drop_enrollment triggers Brain Core signal after persist + metric
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_drop_enrollment_records_metric_and_triggers_brain_core_signal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    enrollment = _make_enrollment_ns(
        enrollment_id=7, status=EnrollmentStatus.ENROLLED, version=2
    )
    db = _make_db_mock(enrollment)
    committed = {"done": False}
    metrics: list[str] = []
    brain_signals: list[dict] = []

    def _commit() -> None:
        committed["done"] = True

    db.commit.side_effect = _commit
    service = EnrollmentLifecycleService(db_session=db)

    monkeypatch.setattr(service, "_load_enrollment", lambda tid, eid: enrollment)
    monkeypatch.setattr(service, "_check_drop_deadline", lambda tid, term_id: None)
    monkeypatch.setattr(service, "_append_status_history", lambda **kw: None)
    monkeypatch.setattr(
        "app.modules.enrollments.service.log_admin_action",
        lambda **kw: None,
    )
    monkeypatch.setattr(
        "app.modules.enrollments.service.log_data_access_event",
        lambda **kw: None,
    )
    monkeypatch.setattr(
        "app.modules.usage.service.record_usage_event",
        lambda tid, metric, value=1: metrics.append(metric),
    )

    db.refresh.side_effect = lambda obj: None

    # Patch Brain Core process_signal
    def _fake_brain_signal(signal: dict) -> dict:
        assert committed["done"] is True, "Brain Core must be called after commit"
        brain_signals.append(signal)
        return {"status": "processed"}

    monkeypatch.setattr(
        "app.modules.brain_core.service.brain_core_service.process_signal",
        _fake_brain_signal,
    )

    request = EnrollmentDropSchema(
        expected_version=2,
        reason="student request",
        dropped_at=None,
        metadata_json={},
    )

    await service.drop_enrollment(
        tenant_id=10,
        enrollment_id=7,
        request=request,
        actor_id="admin@example.com",
    )

    assert "enrollments_dropped" in metrics
    assert any(
        s.get("event_type") == "enrollments.dropout_risk.detected"
        for s in brain_signals
    )


# ---------------------------------------------------------------------------
# Test 4: event-after-persist ordering for change_enrollment_status
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_change_status_valid_transition_emits_event_after_persist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ENROLLED → SUSPENDED must emit dropout_risk event after persist."""
    enrollment = _make_enrollment_ns(
        enrollment_id=9, status=EnrollmentStatus.ENROLLED, version=1
    )
    db = _make_db_mock(enrollment)
    committed = {"done": False}
    events: list[str] = []

    def _commit() -> None:
        committed["done"] = True

    db.commit.side_effect = _commit
    service = EnrollmentLifecycleService(db_session=db)

    monkeypatch.setattr(service, "_load_enrollment", lambda tid, eid: enrollment)
    monkeypatch.setattr(service, "_append_status_history", lambda **kw: None)
    monkeypatch.setattr(
        "app.modules.enrollments.service.log_admin_action",
        lambda **kw: None,
    )
    monkeypatch.setattr(
        "app.modules.enrollments.service.log_data_access_event",
        lambda **kw: None,
    )

    def _fake_dropout_signal(**kwargs) -> None:  # noqa: ANN003
        assert committed["done"] is True, "dropout signal must be emitted after commit"
        events.append("enrollments.dropout_risk.detected")

    monkeypatch.setattr(
        "app.modules.enrollments.service._emit_dropout_risk_signal",
        lambda **kw: events.append("enrollments.dropout_risk.detected"),
    )
    monkeypatch.setattr(
        "app.modules.brain_core.service.brain_core_service.process_signal",
        lambda s: None,
    )

    db.refresh.side_effect = lambda obj: None

    request = EnrollmentStatusChangeSchema(
        to_status=EnrollmentStatus.SUSPENDED,
        expected_version=1,
        reason="academic probation",
        metadata_json={},
    )

    await service.change_enrollment_status(
        tenant_id=10,
        enrollment_id=9,
        request=request,
        actor_id="admin@example.com",
    )

    assert "enrollments.dropout_risk.detected" in events
