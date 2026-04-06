from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.modules.profiles.models import (
    DepartmentModel,
    FacultyModel,
    PersonModel,
    ProgramModel,
    StudentModel,
)


@pytest.fixture
def db_session() -> MagicMock:
    session = MagicMock(name="profiles_db_session")

    id_counter = {"value": 1000}

    def _refresh(instance) -> None:
        if getattr(instance, "id", None) is None:
            id_counter["value"] += 1
            instance.id = id_counter["value"]
        if getattr(instance, "version", None) is None:
            instance.version = 1
        if getattr(instance, "created_at", None) is None:
            instance.created_at = datetime.now(UTC)
        if getattr(instance, "updated_at", None) is None:
            instance.updated_at = datetime.now(UTC)

    session.refresh.side_effect = _refresh
    return session


@pytest.fixture
def now_utc() -> datetime:
    return datetime.now(UTC)


@pytest.fixture
def person_factory(now_utc: datetime):
    def _factory(**overrides) -> PersonModel:
        model = PersonModel(
            tenant_id=1,
            email="person@example.edu",
            first_name="Alice",
            last_name="Anderson",
            phone=None,
            external_person_key=None,
            status="active",
            metadata_json={},
            version=1,
            created_by="owner@example.com",
            created_at=now_utc,
            updated_at=now_utc,
        )
        model.id = 101
        for key, value in overrides.items():
            setattr(model, key, value)
        return model

    return _factory


@pytest.fixture
def department_factory(now_utc: datetime):
    def _factory(**overrides) -> DepartmentModel:
        model = DepartmentModel(
            tenant_id=1,
            code="CS",
            name="Computer Science",
            unit_type="department",
            parent_department_id=None,
            status="active",
            metadata_json={},
            version=1,
            created_by="owner@example.com",
            created_at=now_utc,
            updated_at=now_utc,
        )
        model.id = 201
        for key, value in overrides.items():
            setattr(model, key, value)
        return model

    return _factory


@pytest.fixture
def program_factory(now_utc: datetime):
    def _factory(**overrides) -> ProgramModel:
        model = ProgramModel(
            tenant_id=1,
            department_id=201,
            code="CS-BSC",
            title="Computer Science BSc",
            degree_type="bachelor",
            status="active",
            metadata_json={},
            version=1,
            created_by="owner@example.com",
            created_at=now_utc,
            updated_at=now_utc,
        )
        model.id = 301
        for key, value in overrides.items():
            setattr(model, key, value)
        return model

    return _factory


@pytest.fixture
def student_factory(now_utc: datetime):
    def _factory(**overrides) -> StudentModel:
        model = StudentModel(
            tenant_id=1,
            person_id=101,
            program_id=301,
            student_number="S-001",
            cohort_year=2026,
            status="active",
            metadata_json={},
            version=1,
            created_by="owner@example.com",
            created_at=now_utc,
            updated_at=now_utc,
        )
        model.id = 401
        for key, value in overrides.items():
            setattr(model, key, value)
        return model

    return _factory


@pytest.fixture
def faculty_factory(now_utc: datetime):
    def _factory(**overrides) -> FacultyModel:
        model = FacultyModel(
            tenant_id=1,
            person_id=101,
            department_id=201,
            faculty_number="F-001",
            academic_title="Professor",
            status="active",
            metadata_json={},
            version=1,
            created_by="owner@example.com",
            created_at=now_utc,
            updated_at=now_utc,
        )
        model.id = 501
        for key, value in overrides.items():
            setattr(model, key, value)
        return model

    return _factory


def make_execute_result(*, scalar_one_or_none=None, scalar_one=None, scalars_all=None):
    result = MagicMock(name="execute_result")
    result.scalar_one_or_none.return_value = scalar_one_or_none
    if scalar_one is not None:
        result.scalar_one.return_value = scalar_one
    if scalars_all is not None:
        scalars = MagicMock(name="scalars_result")
        scalars.all.return_value = scalars_all
        result.scalars.return_value = scalars
    return result
