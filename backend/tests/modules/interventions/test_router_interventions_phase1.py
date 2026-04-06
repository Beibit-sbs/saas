from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.main import app
from app.modules.interventions import service as interventions_service
from app.modules.interventions.dependencies import get_interventions_db
from app.modules.interventions.models import (
    InterventionActionType,
    InterventionAssigneeType,
    InterventionCaseSeverity,
    InterventionCaseStatus,
    InterventionCaseType,
)
from app.modules.rbac import service as rbac_service
from app.modules.interventions.schemas import InterventionActionReadSchema, InterventionCaseReadSchema
from tests.conftest import ADMIN_HEADERS, _auth_headers, _configure_db_only_role_resolution, client


@pytest.fixture(autouse=True)
def _enable_intervention_permissions_for_admin(monkeypatch: pytest.MonkeyPatch):
    permissions = set(rbac_service.BASELINE_ROLE_PERMISSIONS.get("admin", set()))
    permissions.update({"admin.jobs.read", "admin.jobs.write"})
    monkeypatch.setitem(rbac_service.BASELINE_ROLE_PERMISSIONS, "admin", permissions)
    _configure_db_only_role_resolution(
        monkeypatch,
        {
            "owner@example.com": ["admin"],
            "student.no.jobs@example.com": ["student"],
        },
    )


@pytest.fixture
def override_interventions_db() -> Generator[MagicMock, None, None]:
    session = MagicMock()
    app.dependency_overrides[get_interventions_db] = lambda: session
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_interventions_db, None)


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return dict(ADMIN_HEADERS)


@pytest.fixture
def student_headers() -> dict[str, str]:
    return _auth_headers("student.no.jobs@example.com", ["student"])


def _case_schema(
    *,
    case_id: int,
    status: InterventionCaseStatus = InterventionCaseStatus.OPEN,
    severity: InterventionCaseSeverity = InterventionCaseSeverity.HIGH,
    assignee_type: InterventionAssigneeType = InterventionAssigneeType.GROUP,
    assignee_ref: str = "dean_office",
    version: int = 1,
) -> InterventionCaseReadSchema:
    now = datetime(2026, 4, 5, 10, 0, 0, tzinfo=UTC)
    due = datetime(2026, 4, 8, 10, 0, 0, tzinfo=UTC)
    return InterventionCaseReadSchema(
        id=case_id,
        tenant_id=1,
        case_type=InterventionCaseType.ACADEMIC_RISK,
        student_profile_id=101,
        severity=severity,
        status=status,
        title="Academic risk case",
        description="Student has GPA 1.8 and 3 failed subjects",
        risk_snapshot_json={"gpa": 1.8},
        assignee_type=assignee_type,
        assignee_ref=assignee_ref,
        due_at=due,
        opened_at=now,
        resolved_at=None,
        metadata_json={},
        version=version,
        created_by="owner@example.com",
        updated_by="owner@example.com",
        created_at=now,
        updated_at=now,
    )


def _action_schema(*, action_id: int, case_id: int) -> InterventionActionReadSchema:
    now = datetime(2026, 4, 5, 10, 1, 0, tzinfo=UTC)
    return InterventionActionReadSchema(
        id=action_id,
        tenant_id=1,
        case_id=case_id,
        action_type=InterventionActionType.CONSULTATION_SCHEDULED,
        description="Consultation with advisor was scheduled",
        outcome_note=None,
        performed_by="owner@example.com",
        performed_at=now,
        metadata_json={},
    )


def test_create_case_success(
    monkeypatch: pytest.MonkeyPatch,
    override_interventions_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_create_case(self, tenant_id: int, request, actor: str):
        assert tenant_id == 1
        assert actor == "owner@example.com"
        assert request.severity == InterventionCaseSeverity.HIGH
        return _case_schema(case_id=9001)

    monkeypatch.setattr(interventions_service.InterventionService, "create_case", fake_create_case)

    response = client.post(
        "/api/admin/interventions/cases",
        headers=admin_headers,
        json={
            "student_profile_id": 101,
            "severity": "high",
            "title": "Academic risk case",
            "description": "Student has GPA 1.8 and 3 failed subjects",
            "risk_snapshot_json": {"gpa": 1.8},
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["id"] == 9001
    assert body["assignee_ref"] == "dean_office"


def test_take_case_sets_in_progress(
    monkeypatch: pytest.MonkeyPatch,
    override_interventions_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_take_case(self, tenant_id: int, case_id: int, request, actor: str):
        assert tenant_id == 1
        assert case_id == 9001
        assert request.expected_version == 1
        assert actor == "owner@example.com"
        return _case_schema(
            case_id=case_id,
            status=InterventionCaseStatus.IN_PROGRESS,
            assignee_type=InterventionAssigneeType.USER,
            assignee_ref=actor,
            version=2,
        )

    monkeypatch.setattr(interventions_service.InterventionService, "take_case", fake_take_case)

    response = client.post(
        "/api/admin/interventions/cases/9001/take",
        headers=admin_headers,
        json={"expected_version": 1},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "in_progress"
    assert body["assignee_type"] == "user"
    assert body["assignee_ref"] == "owner@example.com"


def test_add_action_returns_case_and_action(
    monkeypatch: pytest.MonkeyPatch,
    override_interventions_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_add_case_action(self, tenant_id: int, case_id: int, request, actor: str):
        assert tenant_id == 1
        assert case_id == 9001
        assert request.action_type == InterventionActionType.CONSULTATION_SCHEDULED
        return _case_schema(case_id=case_id, status=InterventionCaseStatus.IN_PROGRESS, version=3), _action_schema(
            action_id=1,
            case_id=case_id,
        )

    monkeypatch.setattr(interventions_service.InterventionService, "add_case_action", fake_add_case_action)

    response = client.post(
        "/api/admin/interventions/cases/9001/actions",
        headers=admin_headers,
        json={
            "expected_version": 2,
            "action_type": "consultation_scheduled",
            "description": "Consultation with advisor was scheduled",
            "mark_case_in_progress": True,
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["case"]["status"] == "in_progress"
    assert body["action"]["action_type"] == "consultation_scheduled"


def test_case_write_requires_permission(
    student_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/admin/interventions/cases",
        headers=student_headers,
        json={
            "student_profile_id": 101,
            "severity": "high",
            "title": "Academic risk case",
        },
    )

    assert response.status_code == 403, response.text
