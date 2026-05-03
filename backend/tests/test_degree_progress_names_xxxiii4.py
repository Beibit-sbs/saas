"""XXXIII.4 — degree_progress Names Resolution tests.

Verifies that evaluate_degree_progress() populates course_name and
program_name instead of exposing raw IDs only.
"""
from __future__ import annotations

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.orm import Session

from app.modules.degree_progress.models import ProgramRequirementItemModel, ProgramRequirementModel
from app.modules.degree_progress.service import DegreeProgressService
from app.modules.students.models import StudentProgramBindingModel, StudentProgramBindingState
from app.modules.transcripts.schemas import StudentTranscriptSchema, TranscriptItemSchema


# ── Helpers / fakes ──────────────────────────────────────────────────────────

class _RowLike:
    """Mimics a named-tuple row returned by SQLAlchemy multi-column queries."""
    def __init__(self, **kw: object):
        for k, v in kw.items():
            setattr(self, k, v)


class _ScalarList:
    def __init__(self, items: list[object]):
        self._items = items

    def all(self) -> list[object]:
        return list(self._items)

    def first(self) -> object | None:
        return self._items[0] if self._items else None


class _Execute:
    """Flexible fake for db.execute() return value."""
    def __init__(
        self,
        *,
        scalar_one_or_none: object | None = None,
        scalars: list[object] | None = None,
        all_rows: list[object] | None = None,
    ):
        self._s1n = scalar_one_or_none
        self._scalars = scalars or []
        self._all_rows = all_rows or []

    def scalar_one_or_none(self) -> object | None:
        return self._s1n

    def scalars(self) -> _ScalarList:
        return _ScalarList(self._scalars)

    def all(self) -> list[object]:
        return list(self._all_rows)


def _binding(program_id: int = 701) -> StudentProgramBindingModel:
    return StudentProgramBindingModel(
        id=5001,
        tenant_id=1,
        student_profile_id=1001,
        program_id=program_id,
        is_primary=True,
        binding_state=StudentProgramBindingState.ACTIVE,
        metadata_json={},
        version=1,
        created_by="owner@example.com",
        updated_by="owner@example.com",
    )


def _requirement(program_id: int = 701) -> ProgramRequirementModel:
    return ProgramRequirementModel(
        id=6001,
        tenant_id=1,
        program_id=program_id,
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


def _transcript(completed: list[int] | None = None) -> StudentTranscriptSchema:
    completed = completed or []
    items = [
        TranscriptItemSchema(
            enrollment_id=4000 + cid,
            term_id=1,
            term_code="2026-SPRING",
            term_name="Spring 2026",
            course_id=cid,
            course_code=f"CS{cid}",
            course_title=f"Course {cid}",
            credits=3,
            grade_code="A",
            grade_points=Decimal("4.00"),
        )
        for cid in completed
    ]
    return StudentTranscriptSchema(
        student_profile_id=1001,
        total_credits=120,
        gpa=Decimal("3.20"),
        items=items,
    )


def _side_effects(
    *,
    binding: StudentProgramBindingModel,
    requirement: ProgramRequirementModel,
    req_items: list[ProgramRequirementItemModel],
    course_rows: list[_RowLike],
    program_name: str | None,
) -> list[_Execute]:
    """Returns the ordered execute() side_effects list."""
    return [
        _Execute(scalar_one_or_none=MagicMock(id=1001, tenant_id=1)),  # student
        _Execute(scalar_one_or_none=binding),                           # binding
        _Execute(scalars=[requirement]),                                 # requirement
        _Execute(scalars=req_items),                                     # req_items
        _Execute(all_rows=course_rows),                                  # course names
        _Execute(scalar_one_or_none=program_name),                       # program name
    ]


@pytest.fixture
def run_async():
    return asyncio.run


@pytest.fixture
def db_session() -> MagicMock:
    return MagicMock(spec=Session)


# ── Tests ────────────────────────────────────────────────────────────────────

def test_course_name_populated_in_completed_requirements(
    monkeypatch: pytest.MonkeyPatch, run_async, db_session
) -> None:
    """course_name is resolved and present in completed requirements."""
    monkeypatch.setattr(
        "app.modules.degree_progress.service.TranscriptService.get_student_transcript",
        AsyncMock(return_value=_transcript(completed=[101, 102])),
    )

    db_session.execute.side_effect = _side_effects(
        binding=_binding(),
        requirement=_requirement(),
        req_items=[_req_item(101), _req_item(102), _req_item(103)],
        course_rows=[
            _RowLike(id=101, title="Intro to CS"),
            _RowLike(id=102, title="Data Structures"),
            _RowLike(id=103, title="Algorithms"),
        ],
        program_name="BSc Computer Science",
    )

    service = DegreeProgressService(db_session)
    result = run_async(
        service.evaluate_degree_progress(tenant_id=1, student_profile_id=1001, actor_id="advisor@test.com")
    )

    assert len(result.completed_requirements) == 2
    names = {r.course_name for r in result.completed_requirements}
    assert "Intro to CS" in names
    assert "Data Structures" in names


def test_course_name_populated_in_remaining_requirements(
    monkeypatch: pytest.MonkeyPatch, run_async, db_session
) -> None:
    """course_name is resolved and present in remaining requirements."""
    monkeypatch.setattr(
        "app.modules.degree_progress.service.TranscriptService.get_student_transcript",
        AsyncMock(return_value=_transcript(completed=[]))
    )

    db_session.execute.side_effect = _side_effects(
        binding=_binding(),
        requirement=_requirement(),
        req_items=[_req_item(201), _req_item(202)],
        course_rows=[
            _RowLike(id=201, title="Linear Algebra"),
            _RowLike(id=202, title="Discrete Math"),
        ],
        program_name="BSc Mathematics",
    )

    service = DegreeProgressService(db_session)
    result = run_async(
        service.evaluate_degree_progress(tenant_id=1, student_profile_id=1001, actor_id="advisor@test.com")
    )

    assert len(result.remaining_requirements) == 2
    names = {r.course_name for r in result.remaining_requirements}
    assert "Linear Algebra" in names
    assert "Discrete Math" in names


def test_program_name_populated(
    monkeypatch: pytest.MonkeyPatch, run_async, db_session
) -> None:
    """program_name is resolved and present in the progress response."""
    monkeypatch.setattr(
        "app.modules.degree_progress.service.TranscriptService.get_student_transcript",
        AsyncMock(return_value=_transcript(completed=[]))
    )

    db_session.execute.side_effect = _side_effects(
        binding=_binding(),
        requirement=_requirement(),
        req_items=[_req_item(301)],
        course_rows=[_RowLike(id=301, title="Physics 101")],
        program_name="BSc Physics",
    )

    service = DegreeProgressService(db_session)
    result = run_async(
        service.evaluate_degree_progress(tenant_id=1, student_profile_id=1001, actor_id="advisor@test.com")
    )

    assert result.program_name == "BSc Physics"


def test_course_name_falls_back_to_none_when_not_found(
    monkeypatch: pytest.MonkeyPatch, run_async, db_session
) -> None:
    """If a course is not in the DB, course_name is None (no crash)."""
    monkeypatch.setattr(
        "app.modules.degree_progress.service.TranscriptService.get_student_transcript",
        AsyncMock(return_value=_transcript(completed=[]))
    )

    db_session.execute.side_effect = _side_effects(
        binding=_binding(),
        requirement=_requirement(),
        req_items=[_req_item(401)],
        course_rows=[],  # no course returned
        program_name="BSc Engineering",
    )

    service = DegreeProgressService(db_session)
    result = run_async(
        service.evaluate_degree_progress(tenant_id=1, student_profile_id=1001, actor_id="advisor@test.com")
    )

    remaining = result.remaining_requirements
    assert len(remaining) == 1
    assert remaining[0].course_name is None
    assert remaining[0].course_id == 401


def test_program_name_falls_back_to_none_when_not_found(
    monkeypatch: pytest.MonkeyPatch, run_async, db_session
) -> None:
    """If a program is not in the DB, program_name is None (no crash)."""
    monkeypatch.setattr(
        "app.modules.degree_progress.service.TranscriptService.get_student_transcript",
        AsyncMock(return_value=_transcript(completed=[]))
    )

    db_session.execute.side_effect = _side_effects(
        binding=_binding(),
        requirement=_requirement(),
        req_items=[_req_item(501)],
        course_rows=[_RowLike(id=501, title="Chemistry")],
        program_name=None,  # not found
    )

    service = DegreeProgressService(db_session)
    result = run_async(
        service.evaluate_degree_progress(tenant_id=1, student_profile_id=1001, actor_id="advisor@test.com")
    )

    assert result.program_name is None
    assert result.program_id == 701


def test_both_course_and_program_names_present_together(
    monkeypatch: pytest.MonkeyPatch, run_async, db_session
) -> None:
    """Regression: both names populated simultaneously; course_id and program_id still present."""
    monkeypatch.setattr(
        "app.modules.degree_progress.service.TranscriptService.get_student_transcript",
        AsyncMock(return_value=_transcript(completed=[601])),
    )

    db_session.execute.side_effect = _side_effects(
        binding=_binding(program_id=888),
        requirement=_requirement(program_id=888),
        req_items=[_req_item(601), _req_item(602)],
        course_rows=[
            _RowLike(id=601, title="Operating Systems"),
            _RowLike(id=602, title="Networks"),
        ],
        program_name="MSc Computer Science",
    )

    service = DegreeProgressService(db_session)
    result = run_async(
        service.evaluate_degree_progress(tenant_id=1, student_profile_id=1001, actor_id="advisor@test.com")
    )

    assert result.program_id == 888
    assert result.program_name == "MSc Computer Science"
    completed_names = {r.course_name for r in result.completed_requirements}
    remaining_names = {r.course_name for r in result.remaining_requirements}
    assert "Operating Systems" in completed_names
    assert "Networks" in remaining_names
    # raw IDs still present
    assert result.completed_requirements[0].course_id == 601
