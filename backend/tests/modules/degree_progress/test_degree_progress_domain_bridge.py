"""Test for degree_progress domain bridge - graduation risk signal emission."""
from __future__ import annotations

import asyncio
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.orm import Session

from app.modules.degree_progress.service import DegreeProgressService
from app.modules.transcripts.schemas import StudentTranscriptSchema, TranscriptItemSchema


class ScalarListResult:
    def __init__(self, items: list[object]):
        self._items = items

    def all(self) -> list[object]:
        return list(self._items)

    def first(self) -> object | None:
        return self._items[0] if self._items else None


class ExecuteResult:
    def __init__(self, *, scalar_one_or_none: object | None = None, scalars: list[object] | None = None):
        self._scalar_one_or_none = scalar_one_or_none
        self._scalars = scalars or []

    def scalar_one_or_none(self) -> object | None:
        return self._scalar_one_or_none

    def scalars(self) -> ScalarListResult:
        return ScalarListResult(self._scalars)


def _student() -> SimpleNamespace:
    return SimpleNamespace(id=1001, tenant_id=1)


def _binding() -> SimpleNamespace:
    return SimpleNamespace(id=5001, tenant_id=1, student_profile_id=1001, program_id=701)


def _requirement() -> SimpleNamespace:
    return SimpleNamespace(
        id=2001,
        tenant_id=1,
        program_id=701,
        name="Bachelor of Science",
        minimum_credits=120,
        minimum_gpa=Decimal("2.0"),
    )


def _transcript_at_risk() -> StudentTranscriptSchema:
    """Transcript for student not eligible for graduation (at-risk condition)."""
    return StudentTranscriptSchema(
        student_profile_id=1001,
        total_credits=100,  # Below 120 minimum
        gpa=Decimal("2.5"),
        items=[
            TranscriptItemSchema(
                enrollment_id=50001,
                term_id=202601,
                term_code="2026S",
                term_name="Spring 2026",
                course_id=1001,
                course_code="C-1001",
                course_title="Course 1001",
                grade_code="A",
                grade_points=Decimal("4.0"),
                credits=3,
            ),
            TranscriptItemSchema(
                enrollment_id=50002,
                term_id=202601,
                term_code="2026S",
                term_name="Spring 2026",
                course_id=1002,
                course_code="C-1002",
                course_title="Course 1002",
                grade_code="B",
                grade_points=Decimal("3.0"),
                credits=3,
            ),
        ],
    )


def _requirement_items() -> list[SimpleNamespace]:
    """Requirement items - 3 remaining required courses."""
    items = []
    for i in range(3):
        item = SimpleNamespace(
            id=3001 + i,
            tenant_id=1,
            requirement_id=2001,
            course_id=2001 + i,
            required=True,
            credits=3,
        )
        items.append(item)
    return items


@pytest.mark.asyncio
async def test_is_student_eligible_for_graduation_emits_graduation_risk_signal_when_not_eligible(monkeypatch) -> None:
    """Test: When student is not eligible for graduation, graduation_risk signal is emitted."""
    # Setup mock db_session
    db_session = MagicMock(spec=Session)

    # Mock the _load_student call
    student = _student()
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=student)

    # Create service
    service = DegreeProgressService(db_session)

    # Mock _load_student to avoid the select query
    service._load_student = MagicMock(return_value=student)

    # Mock _load_active_primary_program_binding
    binding = _binding()
    service._load_active_primary_program_binding = MagicMock(return_value=binding)

    # Mock _load_active_requirement
    requirement = _requirement()
    service._load_active_requirement = MagicMock(return_value=requirement)

    # Mock _load_requirement_items to return 3 remaining required items
    requirement_items = _requirement_items()
    service._load_requirement_items = MagicMock(return_value=requirement_items)

    # Mock TranscriptService.get_student_transcript to return at-risk transcript
    transcript_at_risk = _transcript_at_risk()
    mock_transcript_service = AsyncMock()
    mock_transcript_service.get_student_transcript = AsyncMock(return_value=transcript_at_risk)

    monkeypatch.setattr(
        "app.modules.degree_progress.service.TranscriptService",
        MagicMock(return_value=mock_transcript_service),
    )

    # Setup EventPublisher mock
    publisher_instance = MagicMock(name="event_publisher")
    publisher_factory = MagicMock(return_value=publisher_instance)
    monkeypatch.setattr(
        "app.platform.events.publisher.EventPublisher",
        publisher_factory,
    )

    # Call the method that should emit the signal
    result = await service.is_student_eligible_for_graduation(
        tenant_id=1,
        student_profile_id=1001,
        actor_id="test.system",
    )

    # Verify result shows student is not eligible
    assert result.eligible is False
    assert result.credits_earned == 100
    assert result.minimum_credits == 120

    # Verify graduation_risk signal was published
    publisher_instance.publish_event.assert_called_once()
    call_kwargs = publisher_instance.publish_event.call_args.kwargs
    assert call_kwargs["event_type"] == "degree_progress.graduation_risk.detected"
    assert call_kwargs["tenant_id"] == 1
    assert call_kwargs["aggregate_type"] == "student_graduation_progress"
    assert call_kwargs["aggregate_id"] == 1001

    # Verify payload contains expected data
    payload = call_kwargs["payload_json"]
    assert payload["student_profile_id"] == 1001
    assert payload["program_id"] == 701
    assert payload["credits_earned"] == 100
    assert payload["minimum_credits"] == 120
    assert payload["remaining_required_items"] == 3  # 3 required courses not completed
    assert payload["source_module"] == "degree_progress"


@pytest.mark.asyncio
async def test_is_student_eligible_for_graduation_does_not_emit_signal_when_eligible(monkeypatch) -> None:
    """Test: When student IS eligible for graduation, no signal is emitted."""
    # Setup mock db_session
    db_session = MagicMock(spec=Session)

    # Mock the _load_student call
    student = _student()
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=student)

    # Create service
    service = DegreeProgressService(db_session)

    # Mock _load_student to avoid the select query
    service._load_student = MagicMock(return_value=student)

    # Mock _load_active_primary_program_binding
    binding = _binding()
    service._load_active_primary_program_binding = MagicMock(return_value=binding)

    # Mock _load_active_requirement
    requirement = _requirement()
    service._load_active_requirement = MagicMock(return_value=requirement)

    # Mock _load_requirement_items to return 0 remaining required items (all done)
    service._load_requirement_items = MagicMock(return_value=[])

    # Mock TranscriptService.get_student_transcript to return eligible transcript
    transcript_eligible = StudentTranscriptSchema(
        student_profile_id=1001,
        total_credits=125,  # Above 120 minimum
        gpa=Decimal("3.5"),  # Above 2.0 minimum
        items=[
            TranscriptItemSchema(
                enrollment_id=50003,
                term_id=202601,
                term_code="2026S",
                term_name="Spring 2026",
                course_id=1001,
                course_code="C-1001",
                course_title="Course 1001",
                grade_code="A",
                grade_points=Decimal("4.0"),
                credits=3,
            ),
        ],
    )
    mock_transcript_service = AsyncMock()
    mock_transcript_service.get_student_transcript = AsyncMock(return_value=transcript_eligible)

    monkeypatch.setattr(
        "app.modules.degree_progress.service.TranscriptService",
        MagicMock(return_value=mock_transcript_service),
    )

    # Setup EventPublisher mock
    publisher_instance = MagicMock(name="event_publisher")
    publisher_factory = MagicMock(return_value=publisher_instance)
    monkeypatch.setattr(
        "app.platform.events.publisher.EventPublisher",
        publisher_factory,
    )

    # Call the method that should NOT emit the signal
    result = await service.is_student_eligible_for_graduation(
        tenant_id=1,
        student_profile_id=1001,
        actor_id="test.system",
    )

    # Verify result shows student IS eligible
    assert result.eligible is True
    assert result.credits_earned == 125
    assert result.minimum_credits == 120

    # Verify graduation_risk signal was NOT published
    publisher_instance.publish_event.assert_not_called()
