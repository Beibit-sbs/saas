from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.main import app
from app.modules.interventions import playbook_router
from app.modules.interventions.dependencies import get_interventions_db
from app.modules.interventions import playbook_service
from app.modules.interventions.playbook_schemas import (
    PlaybookExecutionReadSchema,
    PlaybookReadSchema,
    PlaybookStepExecutionReadSchema,
    PlaybookStepReadSchema,
)
from app.modules.rbac import service as rbac_service
from tests.conftest import _auth_headers, _configure_db_only_role_resolution, client


@pytest.fixture(autouse=True)
def _enable_playbook_permissions_for_admin(monkeypatch: pytest.MonkeyPatch):
    permissions = set(rbac_service.BASELINE_ROLE_PERMISSIONS.get("admin", set()))
    permissions.update(
        {
            "interventions:view",
            "interventions:manage_playbooks",
            "interventions:execute_playbook",
        }
    )
    monkeypatch.setitem(rbac_service.BASELINE_ROLE_PERMISSIONS, "admin", permissions)

    def _resolve_permissions_for_tenant(roles: list[str], tenant_id: int) -> set[str]:
        granted: set[str] = set()
        for role in roles:
            granted.update(rbac_service.BASELINE_ROLE_PERMISSIONS.get(role, set()))
        return granted

    monkeypatch.setattr(
        rbac_service,
        "resolve_permissions_for_tenant",
        _resolve_permissions_for_tenant,
    )

    _configure_db_only_role_resolution(
        monkeypatch,
        {
            "owner@example.com": ["admin"],
            "student.no.jobs@example.com": ["student"],
        },
    )
    monkeypatch.setattr(playbook_router, "is_flag_enabled", lambda *args, **kwargs: True)


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
    return _auth_headers("owner@example.com", ["admin"])


@pytest.fixture
def student_headers() -> dict[str, str]:
    return _auth_headers("student.no.jobs@example.com", ["student"])


def _playbook_schema() -> PlaybookReadSchema:
    now = datetime(2026, 4, 13, 10, 0, 0, tzinfo=UTC)
    return PlaybookReadSchema(
        id=100,
        tenant_id=1,
        name="Academic Recovery Plan",
        description="Default intervention plan",
        trigger_threshold_id=None,
        enabled=True,
        version=1,
        metadata_json={},
        created_by="owner@example.com",
        updated_by="owner@example.com",
        created_at=now,
        updated_at=now,
        steps=[
            PlaybookStepReadSchema(
                id=1,
                playbook_id=100,
                step_order=0,
                title="Schedule consultation",
                action_type="consultation_scheduled",
                rationale="High-risk student",
                is_mandatory=True,
                due_days_offset=2,
                assignee_role="advisor",
                metadata_json={},
            )
        ],
    )


def _execution_schema() -> PlaybookExecutionReadSchema:
    now = datetime(2026, 4, 13, 10, 5, 0, tzinfo=UTC)
    return PlaybookExecutionReadSchema(
        id=501,
        tenant_id=1,
        playbook_id=100,
        case_id=901,
        student_profile_id=101,
        triggered_by="manual",
        status="in_progress",
        started_at=now,
        completed_at=None,
        abandoned_at=None,
        abandon_reason=None,
        outcome_delta_score=None,
        metadata_json={},
        created_by="owner@example.com",
        created_at=now,
        updated_at=now,
        step_executions=[
            PlaybookStepExecutionReadSchema(
                id=7001,
                execution_id=501,
                step_id=1,
                status="pending",
                performed_by=None,
                performed_at=None,
                outcome_note=None,
                metadata_json={},
            )
        ],
    )


def test_create_playbook_success(
    monkeypatch: pytest.MonkeyPatch,
    override_interventions_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    def _tenant_id(value: Any) -> int:
        if isinstance(value, int):
            return value
        if isinstance(value, dict):
            return int(value.get("id"))
        return int(getattr(value, "id"))

    def fake_create_playbook(self, tenant_id: int, actor: str, payload):
        assert _tenant_id(tenant_id) == 1
        assert actor == "owner@example.com"
        assert payload.name == "Academic Recovery Plan"
        return _playbook_schema()

    monkeypatch.setattr(playbook_service.PlaybookService, "create_playbook", fake_create_playbook)

    response = client.post(
        "/api/admin/interventions/playbooks",
        headers=admin_headers,
        json={
            "name": "Academic Recovery Plan",
            "description": "Default intervention plan",
            "steps": [
                {
                    "step_order": 0,
                    "title": "Schedule consultation",
                    "action_type": "consultation_scheduled",
                }
            ],
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["id"] == 100
    assert body["name"] == "Academic Recovery Plan"


def test_start_execution_success(
    monkeypatch: pytest.MonkeyPatch,
    override_interventions_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    def _tenant_id(value: Any) -> int:
        if isinstance(value, int):
            return value
        if isinstance(value, dict):
            return int(value.get("id"))
        return int(getattr(value, "id"))

    def fake_start_execution(self, tenant_id: int, actor: str, payload):
        assert _tenant_id(tenant_id) == 1
        assert actor == "owner@example.com"
        assert payload.playbook_id == 100
        return _execution_schema()

    monkeypatch.setattr(playbook_service.PlaybookService, "start_execution", fake_start_execution)

    response = client.post(
        "/api/admin/interventions/playbooks/executions",
        headers=admin_headers,
        json={"playbook_id": 100, "case_id": 901, "student_profile_id": 101},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["id"] == 501
    assert body["status"] == "in_progress"


def test_playbook_write_requires_permission(student_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/admin/interventions/playbooks",
        headers=student_headers,
        json={"name": "No Access Plan"},
    )

    assert response.status_code == 403, response.text


def test_create_playbook_returns_403_when_feature_disabled(
    monkeypatch: pytest.MonkeyPatch,
    override_interventions_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    monkeypatch.setattr(playbook_router, "is_flag_enabled", lambda *args, **kwargs: False)

    response = client.post(
        "/api/admin/interventions/playbooks",
        headers=admin_headers,
        json={
            "name": "Academic Recovery Plan",
            "description": "Default intervention plan",
            "steps": [
                {
                    "step_order": 0,
                    "title": "Schedule consultation",
                    "action_type": "consultation_scheduled",
                }
            ],
        },
    )

    assert response.status_code == 403, response.text
    assert "feature is disabled" in str(response.json().get("detail", ""))


def test_list_playbooks_allows_read_only_when_feature_disabled(
    monkeypatch: pytest.MonkeyPatch,
    override_interventions_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    monkeypatch.setattr(playbook_router, "is_flag_enabled", lambda *args, **kwargs: False)
    monkeypatch.setattr(playbook_service.PlaybookService, "list_playbooks", lambda *args, **kwargs: ([], 0))

    response = client.get("/api/admin/interventions/playbooks", headers=admin_headers)

    assert response.status_code == 200, response.text
    assert response.json() == {"items": [], "total": 0}
