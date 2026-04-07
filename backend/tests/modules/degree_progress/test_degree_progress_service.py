from __future__ import annotations

import asyncio
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import TenantResourceNotFoundError
from app.modules.degree_progress.models import ProgramRequirementItemModel, ProgramRequirementModel
from app.modules.degree_progress.service import DegreeProgressService
from app.modules.degree_progress.schemas import DegreeProgressSchema
from app.modules.students.models import StudentProgramBindingModel, StudentProgramBindingState
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


@pytest.fixture
def run_async():
    return asyncio.run


@pytest.fixture
def db_session() -> MagicMock:
    return MagicMock(spec=Session)


def _binding() -> StudentProgramBindingModel:
    return StudentProgramBindingModel(
        id=5001,
        tenant_id=1,
        student_profile_id=1001,
        program_id=701,
        is_primary=True,
        binding_state=StudentProgramBindingState.ACTIVE,
        metadata_json={},
        version=1,
        created_by="owner@example.com",
        updated_by="owner@example.com",
    )


def _requirement() -> ProgramRequirementModel:
    return ProgramRequirementModel(
        id=6001,
        tenant_id=1,
        program_id=701,
        name="BSCS Core",
        minimum_credits=120,
        minimum_gpa=Decimal("2.00"),
        is_active=True,
    )


def _req_item(course_id: int, required: bool = True) -> ProgramRequirementItemModel:
    return ProgramRequirementItemModel(
        id=6100 + course_id,
        tenant_id=1,
        requirement_id=6001,
        course_id=course_id,
        required=required,
        credits=3,
    )


def _transcript() -> StudentTranscriptSchema:
    return StudentTranscriptSchema(
        student_profile_id=1001,
        total_credits=120,
        gpa=Decimal("3.20"),
        items=[
            TranscriptItemSchema(
                enrollment_id=4001,
                term_id=1,
                term_code="2026-SPRING",
                term_name="Spring 2026",
                course_id=101,
                course_code="CS101",
                course_title="Intro",
                credits=3,
                grade_code="A",
                grade_points=Decimal("4.00"),
            ),
            TranscriptItemSchema(
                enrollment_id=4002,
                term_id=1,
                term_code="2026-SPRING",
                term_name="Spring 2026",
                course_id=102,
                course_code="CS102",
                course_title="DS",
                credits=3,
                grade_code="B",
                grade_points=Decimal("3.00"),
            ),
        ],
    )


def test_evaluate_degree_progress_success(monkeypatch: pytest.MonkeyPatch, run_async, db_session) -> None:
    async def fake_get_transcript(self, tenant_id: int, *, student_profile_id: int):
        return _transcript()

    monkeypatch.setattr("app.modules.degree_progress.service.TranscriptService.get_student_transcript", fake_get_transcript)

    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=MagicMock(id=1001, tenant_id=1)),
        ExecuteResult(scalar_one_or_none=_binding()),
        ExecuteResult(scalars=[_requirement()]),
        ExecuteResult(scalars=[_req_item(101), _req_item(102), _req_item(103)]),
    ]

    service = DegreeProgressService(db_session)
    result: DegreeProgressSchema = run_async(
        service.evaluate_degree_progress(tenant_id=1, student_profile_id=1001, actor_id="advisor@example.com")
    )

    assert result.student_profile_id == 1001
    assert result.program_id == 701
    assert len(result.completed_requirements) == 2
    assert len(result.remaining_requirements) == 1
    assert result.graduation_eligible is False


def test_is_student_eligible_for_graduation_true(monkeypatch: pytest.MonkeyPatch, run_async, db_session) -> None:
    async def fake_get_transcript(self, tenant_id: int, *, student_profile_id: int):
        transcript = _transcript()
        transcript.items.append(
            TranscriptItemSchema(
                enrollment_id=4003,
                term_id=2,
                term_code="2026-FALL",
                term_name="Fall 2026",
                course_id=103,
                course_code="CS103",
                course_title="Algo",
                credits=3,
                grade_code="A",
                grade_points=Decimal("4.00"),
            )
        )
        transcript.total_credits = 123
        transcript.gpa = Decimal("3.40")
        return transcript

    monkeypatch.setattr("app.modules.degree_progress.service.TranscriptService.get_student_transcript", fake_get_transcript)

    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=MagicMock(id=1001, tenant_id=1)),
        ExecuteResult(scalar_one_or_none=_binding()),
        ExecuteResult(scalars=[_requirement()]),
        ExecuteResult(scalars=[_req_item(101), _req_item(102), _req_item(103)]),
    ]

    service = DegreeProgressService(db_session)
    result = run_async(
        service.is_student_eligible_for_graduation(tenant_id=1, student_profile_id=1001, actor_id="advisor@example.com")
    )

    assert result.eligible is True


def test_evaluate_degree_progress_tenant_not_found(run_async, db_session) -> None:
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=None)
    service = DegreeProgressService(db_session)

    with pytest.raises(TenantResourceNotFoundError):
        run_async(service.evaluate_degree_progress(tenant_id=1, student_profile_id=1001, actor_id="advisor@example.com"))
