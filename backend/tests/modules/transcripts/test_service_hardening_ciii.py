"""Phase CIII — Transcripts Service Hardening (canonical fail-safe hooks).

Verifies:
1. generate_transcript records outcome + metric after successful persistence.
2. create_transcript_snapshot records outcome + metric after successful persistence.
3. generate_transcript survives outcome dependency failure and still records metric.
4. Locked-transcript guard (graduated student) is fail-closed.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.transcripts.schemas import StudentTranscriptSchema
from app.modules.transcripts.service import TranscriptService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def run_async():
    return asyncio.run


@pytest.fixture
def db_session() -> MagicMock:
    session = MagicMock(spec=Session)

    def fake_refresh(instance: object) -> None:
        now = datetime(2026, 3, 23, 10, 0, 0, tzinfo=UTC)
        if getattr(instance, "id", None) is None:
            instance.id = 9001
        if hasattr(instance, "generated_at") and getattr(instance, "generated_at", None) is None:
            instance.generated_at = now
        if hasattr(instance, "tenant_id") and getattr(instance, "tenant_id", None) is None:
            instance.tenant_id = 1
        if hasattr(instance, "student_profile_id") and getattr(instance, "student_profile_id", None) is None:
            instance.student_profile_id = 501
        if hasattr(instance, "snapshot_json") and getattr(instance, "snapshot_json", None) is None:
            instance.snapshot_json = {}
        if hasattr(instance, "generated_by") and getattr(instance, "generated_by", None) is None:
            instance.generated_by = "actor@test"

    session.refresh.side_effect = fake_refresh
    return session


def _mock_student(*, tenant_id: int = 1, profile_id: int = 501, status: str = "admitted") -> MagicMock:
    student = MagicMock()
    student.id = profile_id
    student.tenant_id = tenant_id
    student.current_status = status
    return student


def _base_generate_patches(db_session: MagicMock, student_status: str = "admitted"):
    """Return a context-manager stack for generate_transcript happy-path."""
    student = _mock_student(status=student_status)
    patches = [
        patch("app.modules.transcripts.service.assert_billing_write_allowed"),
        patch("app.modules.transcripts.service.assert_quota_with_increment"),
        patch.object(TranscriptService, "_load_student", return_value=student),
        patch.object(TranscriptService, "_load_enrollments", return_value=[]),
        patch(
            "app.modules.transcripts.service.GradeLifecycleService.calculate_student_gpa",
            new_callable=AsyncMock,
            return_value=Decimal("3.50"),
        ),
    ]
    return patches


# ---------------------------------------------------------------------------
# Test 1 — generate_transcript records outcome + metric
# ---------------------------------------------------------------------------


def test_generate_transcript_records_outcome_and_metric(db_session, run_async):
    svc = TranscriptService(db_session)

    with (
        patch("app.modules.transcripts.service.assert_billing_write_allowed"),
        patch("app.modules.transcripts.service.assert_quota_with_increment"),
        patch.object(TranscriptService, "_load_student", return_value=_mock_student()),
        patch.object(TranscriptService, "_load_enrollments", return_value=[]),
        patch(
            "app.modules.transcripts.service.GradeLifecycleService.calculate_student_gpa",
            new_callable=AsyncMock,
            return_value=Decimal("3.50"),
        ),
        patch("app.modules.transcripts.service._record_outcome") as mock_outcome,
        patch("app.modules.transcripts.service._metric") as mock_metric,
        patch("app.modules.transcripts.service._audit"),
    ):
        result = run_async(
            svc.generate_transcript(1, student_profile_id=501, actor_id="actor@test")
        )

    assert result.student_profile_id == 501
    mock_outcome.assert_called_once_with(501, "transcript_generated", "actor@test")
    mock_metric.assert_called_once_with(1, "transcripts_generated", 1)


# ---------------------------------------------------------------------------
# Test 2 — create_transcript_snapshot records outcome + metric
# ---------------------------------------------------------------------------


def test_create_transcript_snapshot_records_outcome_and_metric(db_session, run_async):
    svc = TranscriptService(db_session)

    mock_transcript = StudentTranscriptSchema(
        student_profile_id=501,
        total_credits=90,
        gpa=Decimal("3.50"),
        items=[],
    )

    with (
        patch.object(
            TranscriptService,
            "generate_transcript",
            new_callable=AsyncMock,
            return_value=mock_transcript,
        ),
        patch("app.modules.transcripts.service._record_outcome") as mock_outcome,
        patch("app.modules.transcripts.service._metric") as mock_metric,
        patch("app.modules.transcripts.service._audit"),
    ):
        result = run_async(
            svc.create_transcript_snapshot(1, student_profile_id=501, actor_id="actor@test")
        )

    assert result.entity.student_profile_id == 501
    mock_outcome.assert_called_once_with(9001, "transcript_snapshot_created", "actor@test")
    mock_metric.assert_called_once_with(1, "transcript_snapshots_created", 1)


# ---------------------------------------------------------------------------
# Test 3 — generate_transcript survives brain_core failure; metric still fires
# ---------------------------------------------------------------------------


def test_generate_transcript_outcome_fail_safe(db_session, run_async):
    """brain_core down → outcome silently fails but metric still fires."""
    svc = TranscriptService(db_session)

    brain_core_mock = MagicMock()
    brain_core_mock.record_dispatch_outcome.side_effect = RuntimeError("brain_core down")

    with (
        patch("app.modules.transcripts.service.assert_billing_write_allowed"),
        patch("app.modules.transcripts.service.assert_quota_with_increment"),
        patch.object(TranscriptService, "_load_student", return_value=_mock_student()),
        patch.object(TranscriptService, "_load_enrollments", return_value=[]),
        patch(
            "app.modules.transcripts.service.GradeLifecycleService.calculate_student_gpa",
            new_callable=AsyncMock,
            return_value=Decimal("3.50"),
        ),
        patch("app.modules.transcripts.service._metric") as mock_metric,
        patch("app.modules.transcripts.service._audit"),
        patch("app.modules.brain_core.service.brain_core_service", brain_core_mock),
    ):
        result = run_async(
            svc.generate_transcript(1, student_profile_id=501, actor_id="actor@test")
        )

    assert result.student_profile_id == 501
    mock_metric.assert_called_once_with(1, "transcripts_generated", 1)


# ---------------------------------------------------------------------------
# Test 4 — graduated student lock guard is fail-closed
# ---------------------------------------------------------------------------


def test_generate_transcript_locked_for_graduated_student(db_session, run_async):
    """generate_transcript MUST raise DomainValidationError for graduated students."""
    svc = TranscriptService(db_session)

    with (
        patch("app.modules.transcripts.service.assert_billing_write_allowed"),
        patch("app.modules.transcripts.service.assert_quota_with_increment"),
        patch.object(TranscriptService, "_load_student", return_value=_mock_student(status="graduated")),
    ):
        with pytest.raises(DomainValidationError, match="locked"):
            run_async(
                svc.generate_transcript(1, student_profile_id=501, actor_id="actor@test")
            )
