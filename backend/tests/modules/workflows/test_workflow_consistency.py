from __future__ import annotations

import asyncio
from typing import Iterator
from unittest.mock import MagicMock

import pytest

from app.main import app
from app.modules.workflows import workflow_service as workflows_service
from app.modules.workflows.dependencies import get_workflows_db
from app.modules.workflows.schemas import WorkflowConsistencyReportSchema
from app.modules.workflows.workflow_service import WorkflowService
from tests.conftest import ADMIN_HEADERS, client


class ExecuteResult:
    def __init__(self, *, scalars: list[object]) -> None:
        self._scalars = list(scalars)

    def scalars(self) -> "ExecuteResult":
        return self

    def all(self) -> list[object]:
        return list(self._scalars)


def _instance(**overrides: object) -> MagicMock:
    item = MagicMock()
    item.id = overrides.get("id", 101)
    item.workflow_definition_id = overrides.get("workflow_definition_id", 201)
    item.workflow_definition_version_id = overrides.get("workflow_definition_version_id", 301)
    item.current_step_id = overrides.get("current_step_id", 401)
    return item


def _task(**overrides: object) -> MagicMock:
    item = MagicMock()
    item.id = overrides.get("id", 501)
    item.workflow_instance_id = overrides.get("workflow_instance_id", 101)
    item.workflow_step_id = overrides.get("workflow_step_id", 401)
    return item


def _comment(**overrides: object) -> MagicMock:
    item = MagicMock()
    item.id = overrides.get("id", 601)
    item.workflow_task_id = overrides.get("workflow_task_id", 501)
    return item


def test_get_tenant_consistency_report_detects_missing_links() -> None:
    db_session = MagicMock()
    db_session.execute.side_effect = [
        ExecuteResult(scalars=[201]),
        ExecuteResult(scalars=[301]),
        ExecuteResult(scalars=[401]),
        ExecuteResult(
            scalars=[
                _instance(id=101, workflow_definition_id=999, workflow_definition_version_id=301, current_step_id=401),
                _instance(id=102, workflow_definition_id=201, workflow_definition_version_id=998, current_step_id=997),
            ]
        ),
        ExecuteResult(
            scalars=[
                _task(id=501, workflow_instance_id=101, workflow_step_id=401),
                _task(id=502, workflow_instance_id=9999, workflow_step_id=9988),
            ]
        ),
        ExecuteResult(
            scalars=[
                _comment(id=601, workflow_task_id=501),
                _comment(id=602, workflow_task_id=9999),
            ]
        ),
    ]

    service = WorkflowService(db_session)
    report = asyncio.run(service.get_tenant_consistency_report(tenant_id=1))

    assert report.definition_count == 1
    assert report.definition_version_count == 1
    assert report.step_count == 1
    assert report.instance_count == 2
    assert report.task_count == 2
    assert report.comment_count == 2
    issue_types = [issue.issue_type for issue in report.issues]
    assert "instance_missing_definition" in issue_types
    assert "instance_missing_definition_version" in issue_types
    assert "instance_missing_current_step" in issue_types
    assert "task_missing_instance" in issue_types
    assert "task_missing_step" in issue_types
    assert "comment_missing_task" in issue_types


@pytest.fixture
def override_workflows_db() -> Iterator[MagicMock]:
    session = MagicMock()
    app.dependency_overrides[get_workflows_db] = lambda: session
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_workflows_db, None)


def test_get_workflow_consistency_endpoint_success(
    monkeypatch: pytest.MonkeyPatch,
    override_workflows_db: MagicMock,
) -> None:
    async def fake_get_tenant_consistency_report(self, tenant_id: int) -> WorkflowConsistencyReportSchema:
        assert tenant_id == 1
        return WorkflowConsistencyReportSchema(
            definition_count=1,
            definition_version_count=1,
            step_count=2,
            instance_count=1,
            task_count=1,
            comment_count=1,
            issue_count=1,
            issues=[
                {
                    "issue_type": "task_missing_step",
                    "workflow_task_id": 501,
                    "reference_id": 999,
                    "detail": "Workflow task references a missing workflow step.",
                }
            ],
        )

    monkeypatch.setattr(
        workflows_service.WorkflowService,
        "get_tenant_consistency_report",
        fake_get_tenant_consistency_report,
    )

    response = client.get("/api/admin/workflows/consistency", headers=ADMIN_HEADERS)

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["issue_count"] == 1
    assert payload["issues"][0]["issue_type"] == "task_missing_step"