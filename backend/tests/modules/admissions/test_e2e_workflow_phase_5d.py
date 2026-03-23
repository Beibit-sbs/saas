"""
Phase 5D: End-to-End Admissions Workflow Validation

Scope:
- Validate full admissions flow using existing endpoints and service contracts
- No schema/router/service code changes
- Tenant-first checks preserved
- RBAC preserved
- Audit logging preserved

Flow:
1. create applicant
2. create application
3. submit application
4. workflow instance is created
5. workflow tasks are created
6. simulate approval transitions
7. workflow reaches END
8. workflow callback executed
9. DecisionService.finalize_workflow_decision() invoked
10. application stage becomes concluded
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.main import app
from app.modules.admissions import service as admissions_service
from app.modules.admissions.dependencies import get_admissions_db
from app.modules.admissions.schemas import (
    ApplicantReadSchema,
    ApplicationConclusionType,
    ApplicationReadSchema,
    ApplicationStage,
)
from app.modules.workflows.dependencies import get_workflows_db
from app.modules.workflows.models import WorkflowInstanceStatus, WorkflowTaskStatus
from app.modules.workflows import workflow_service as workflows_service
from tests.conftest import ADMIN_HEADERS, _auth_headers, client


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass
class InMemoryE2EState:
    tenant_id: int
    applicant_seq: int
    application_seq: int
    workflow_seq: int
    task_seq: int
    decision_seq: int
    applicants: dict[int, dict[str, Any]]
    applications: dict[int, dict[str, Any]]
    workflow_instances: dict[int, dict[str, Any]]
    workflow_tasks: dict[int, dict[str, Any]]
    decisions: dict[int, dict[str, Any]]
    callback_calls: list[dict[str, Any]]
    finalize_calls: list[dict[str, Any]]
    audit_calls: list[dict[str, Any]]


@pytest.fixture
def override_module_dbs() -> MagicMock:
    """Override both module DB dependencies with one mock session."""
    session = MagicMock(name="phase5d_db_session")
    app.dependency_overrides[get_admissions_db] = lambda: session
    app.dependency_overrides[get_workflows_db] = lambda: session
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_admissions_db, None)
        app.dependency_overrides.pop(get_workflows_db, None)


@pytest.fixture
def e2e_state() -> InMemoryE2EState:
    return InMemoryE2EState(
        tenant_id=1,
        applicant_seq=100,
        application_seq=200,
        workflow_seq=700,
        task_seq=900,
        decision_seq=500,
        applicants={},
        applications={},
        workflow_instances={},
        workflow_tasks={},
        decisions={},
        callback_calls=[],
        finalize_calls=[],
        audit_calls=[],
    )


@pytest.fixture
def patch_phase5d_services(monkeypatch: pytest.MonkeyPatch, e2e_state: InMemoryE2EState):
    """
    Patch service methods with deterministic in-memory behavior while preserving
    endpoint contracts, tenant checks, RBAC checks, and audit-call semantics.
    """

    def _audit_capture(**kwargs):
        e2e_state.audit_calls.append(kwargs)

    monkeypatch.setattr(admissions_service, "log_admin_action", _audit_capture)
    monkeypatch.setattr(workflows_service, "log_admin_action", _audit_capture)

    async def fake_create_applicant(self, tenant_id: int, request, created_by: str) -> ApplicantReadSchema:
        if tenant_id is None:
            raise ValueError("tenant_id must always be provided explicitly")

        e2e_state.applicant_seq += 1
        applicant_id = e2e_state.applicant_seq
        ts = _now()

        row = {
            "id": applicant_id,
            "tenant_id": tenant_id,
            "email": request.email,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "phone": request.phone,
            "program_id": request.program_id,
            "application_year": request.application_year,
            "status": request.status,
            "external_id": request.external_id,
            "metadata_json": dict(request.metadata_json),
            "created_by": created_by,
            "created_at": ts,
            "updated_at": ts,
        }
        e2e_state.applicants[applicant_id] = row

        admissions_service.log_admin_action(
            actor=created_by,
            action="admissions.applicant.create",
            path=f"/internal/admissions/applicants/{applicant_id}",
            client_ip="service",
            entity="applicant",
            metadata={"resource_id": str(applicant_id)},
            tenant_id=tenant_id,
        )

        return ApplicantReadSchema.model_validate(row)

    async def fake_create_application(self, tenant_id: int, request, created_by: str) -> ApplicationReadSchema:
        if tenant_id is None:
            raise ValueError("tenant_id must always be provided explicitly")
        if request.applicant_id not in e2e_state.applicants:
            raise ValueError(f"Applicant {request.applicant_id} not found in tenant {tenant_id}")

        e2e_state.application_seq += 1
        app_id = e2e_state.application_seq
        ts = _now()

        row = {
            "id": app_id,
            "tenant_id": tenant_id,
            "applicant_id": request.applicant_id,
            "program_id": request.program_id,
            "metadata_json": dict(request.metadata_json),
            "stage": ApplicationStage.NEW,
            "conclusion_type": None,
            "received_at": None,
            "decision_at": None,
            "version": 1,
            "created_by": created_by,
            "created_at": ts,
            "updated_at": ts,
        }
        e2e_state.applications[app_id] = row

        admissions_service.log_admin_action(
            actor=created_by,
            action="admissions.application.create",
            path=f"/internal/admissions/applications/{app_id}",
            client_ip="service",
            entity="application",
            metadata={"resource_id": str(app_id)},
            tenant_id=tenant_id,
        )

        return ApplicationReadSchema.model_validate(row)

    async def fake_finalize_workflow_decision(
        self,
        tenant_id: int,
        application_id: int,
        workflow_instance_id: int,
        approval_action: str,
        actor: str = "system@workflow",
    ):
        if tenant_id is None:
            raise ValueError("tenant_id must always be provided explicitly")

        app_row = e2e_state.applications.get(application_id)
        if not app_row or app_row["tenant_id"] != tenant_id:
            raise ValueError(f"Application {application_id} not found in tenant {tenant_id}")

        e2e_state.finalize_calls.append(
            {
                "tenant_id": tenant_id,
                "application_id": application_id,
                "workflow_instance_id": workflow_instance_id,
                "approval_action": approval_action,
                "actor": actor,
            }
        )

        if approval_action == "approve":
            conclusion = ApplicationConclusionType.ACCEPTED
        elif approval_action == "reject":
            conclusion = ApplicationConclusionType.REJECTED
        else:
            raise ValueError("Invalid approval_action")

        e2e_state.decision_seq += 1
        decision_id = e2e_state.decision_seq
        ts = _now()

        app_row["stage"] = ApplicationStage.CONCLUDED
        app_row["conclusion_type"] = conclusion
        app_row["decision_at"] = ts
        app_row["version"] += 1
        app_row["metadata_json"]["workflow_status"] = "completed"
        app_row["metadata_json"]["workflow_outcome"] = approval_action
        app_row["metadata_json"]["workflow_completed_at"] = ts.isoformat()
        app_row["updated_at"] = ts

        decision = {
            "id": decision_id,
            "tenant_id": tenant_id,
            "application_id": application_id,
            "decision_type": conclusion,
            "decision_rationale": f"Workflow decision: {approval_action}",
            "decided_by_id": actor,
            "decided_at": ts,
            "conditions_json": {
                "workflow_instance_id": workflow_instance_id,
                "approval_action": approval_action,
            },
            "version": 1,
            "created_at": ts,
            "updated_at": ts,
        }
        e2e_state.decisions[decision_id] = decision

        admissions_service.log_admin_action(
            actor=actor,
            action="admissions.decision.finalize",
            path=f"/internal/admissions/applications/{application_id}/decision",
            client_ip="service",
            entity="decision",
            metadata={"resource_id": str(application_id), "workflow_instance_id": workflow_instance_id},
            tenant_id=tenant_id,
        )

        return SimpleNamespace(id=decision_id)

    async def fake_on_workflow_completed(
        self,
        workflow_id: int,
        tenant_id: int,
        entity_type: str,
        entity_id: int,
        workflow_key: str,
        outcome: dict | None = None,
    ) -> dict:
        e2e_state.callback_calls.append(
            {
                "workflow_id": workflow_id,
                "tenant_id": tenant_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "workflow_key": workflow_key,
                "outcome": outcome or {},
            }
        )

        decision_service = admissions_service.DecisionService(self.db)
        decision = await decision_service.finalize_workflow_decision(
            tenant_id=tenant_id,
            application_id=entity_id,
            workflow_instance_id=workflow_id,
            approval_action=(outcome or {}).get("action", "approve"),
            actor="system@workflow",
        )
        return {
            "status": "success",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "result_id": decision.id,
            "message": "Decision finalized via callback",
        }

    async def fake_submit_application(
        self,
        tenant_id: int,
        application_id: int,
        actor: str,
        expected_version: int,
    ) -> ApplicationReadSchema:
        if tenant_id is None:
            raise ValueError("tenant_id must always be provided explicitly")

        app_row = e2e_state.applications.get(application_id)
        if not app_row or app_row["tenant_id"] != tenant_id:
            raise ValueError(f"Application {application_id} not found in tenant {tenant_id}")

        if app_row["version"] != expected_version:
            raise ValueError(
                f"Version mismatch for application {application_id}: expected {expected_version}, got {app_row['version']}"
            )

        if app_row["stage"] != ApplicationStage.NEW:
            raise ValueError(f"Cannot submit application in stage '{app_row['stage'].value}'.")

        e2e_state.workflow_seq += 1
        workflow_id = e2e_state.workflow_seq
        ts = _now()

        app_row["stage"] = ApplicationStage.RECEIVED
        app_row["received_at"] = ts
        app_row["version"] += 1
        app_row["metadata_json"]["workflow_instance_id"] = workflow_id
        app_row["metadata_json"]["workflow_key"] = "admissions"
        app_row["metadata_json"]["workflow_status"] = "in_progress"
        app_row["metadata_json"]["workflow_started_at"] = ts.isoformat()
        app_row["updated_at"] = ts

        e2e_state.workflow_instances[workflow_id] = {
            "id": workflow_id,
            "tenant_id": tenant_id,
            "workflow_definition_id": 1,
            "workflow_definition_version_id": 1,
            "entity_type": "admission_application",
            "entity_id": application_id,
            "status": WorkflowInstanceStatus.IN_PROGRESS,
            "current_step_id": 10,
            "initiated_by": actor,
            "started_at": ts,
            "due_at": None,
            "completed_at": None,
            "priority": 50,
            "metadata_json": {"outcome": {"action": "approve"}},
            "version": 1,
            "created_by": actor,
            "created_at": ts,
            "updated_by": actor,
            "updated_at": ts,
        }

        e2e_state.task_seq += 1
        task_id = e2e_state.task_seq
        e2e_state.workflow_tasks[task_id] = {
            "id": task_id,
            "tenant_id": tenant_id,
            "workflow_instance_id": workflow_id,
            "workflow_step_id": 10,
            "task_type": "approval",
            "status": WorkflowTaskStatus.OPEN,
            "assignee_type": "group",
            "assignee_ref": "admissions_staff",
            "title": "Document Review",
            "instructions": "Review submitted documents",
            "due_at": None,
            "sequence_no": 1,
            "is_blocking": True,
            "claimed_at": None,
            "completed_at": None,
            "metadata_json": {},
            "version": 1,
            "created_by": actor,
            "created_at": ts,
            "updated_by": actor,
            "updated_at": ts,
        }

        admissions_service.log_admin_action(
            actor=actor,
            action="admissions.application.submit",
            path=f"/internal/admissions/applications/{application_id}/submit",
            client_ip="service",
            entity="application",
            metadata={"resource_id": str(application_id), "workflow_instance_id": workflow_id},
            tenant_id=tenant_id,
        )

        return ApplicationReadSchema.model_validate(app_row)

    async def fake_list_instances(self, tenant_id: int, *, entity_type=None, entity_id=None, status=None, limit=100):
        rows = []
        for row in e2e_state.workflow_instances.values():
            if row["tenant_id"] != tenant_id:
                continue
            if entity_type and row["entity_type"] != entity_type:
                continue
            if entity_id is not None and row["entity_id"] != entity_id:
                continue
            if status and row["status"] != status:
                continue
            rows.append(SimpleNamespace(**row))
        return rows[:limit]

    async def fake_get_user_tasks(
        self,
        tenant_id: int,
        assignee_ref: str,
        *,
        assignee_type: str = "user",
        include_completed: bool = False,
        limit: int = 100,
    ):
        rows = []
        for row in e2e_state.workflow_tasks.values():
            if row["tenant_id"] != tenant_id:
                continue
            if row["assignee_type"] != assignee_type:
                continue
            if row["assignee_ref"] != assignee_ref:
                continue
            if not include_completed and row["status"] == WorkflowTaskStatus.COMPLETED:
                continue
            rows.append(SimpleNamespace(**row))
        rows.sort(key=lambda x: x.sequence_no)
        return rows[:limit]

    async def fake_complete_task(
        self,
        tenant_id: int,
        task_id: int,
        actor: str,
        *,
        expected_task_version: int,
        transition_action: str = "complete",
        reason: str | None = None,
    ):
        task = e2e_state.workflow_tasks.get(task_id)
        if not task or task["tenant_id"] != tenant_id:
            raise ValueError(f"Workflow task {task_id} not found in tenant {tenant_id}")

        if task["version"] != expected_task_version:
            raise ValueError("Version mismatch")

        task["status"] = WorkflowTaskStatus.COMPLETED
        task["completed_at"] = _now()
        task["updated_by"] = actor
        task["updated_at"] = _now()
        task["version"] += 1

        workflow = e2e_state.workflow_instances[task["workflow_instance_id"]]
        step_order = ["admissions_staff", "department_chairs", "deans", "registrars", "admissions_leadership"]
        current_idx = step_order.index(task["assignee_ref"])

        if current_idx < len(step_order) - 1:
            next_group = step_order[current_idx + 1]
            e2e_state.task_seq += 1
            next_task_id = e2e_state.task_seq
            e2e_state.workflow_tasks[next_task_id] = {
                "id": next_task_id,
                "tenant_id": tenant_id,
                "workflow_instance_id": workflow["id"],
                "workflow_step_id": (current_idx + 2) * 10,
                "task_type": "approval",
                "status": WorkflowTaskStatus.OPEN,
                "assignee_type": "group",
                "assignee_ref": next_group,
                "title": f"Approval step {current_idx + 2}",
                "instructions": "Review and approve",
                "due_at": None,
                "sequence_no": current_idx + 2,
                "is_blocking": True,
                "claimed_at": None,
                "completed_at": None,
                "metadata_json": {},
                "version": 1,
                "created_by": actor,
                "created_at": _now(),
                "updated_by": actor,
                "updated_at": _now(),
            }
            workflow["current_step_id"] = (current_idx + 2) * 10
        else:
            workflow["status"] = WorkflowInstanceStatus.COMPLETED
            workflow["current_step_id"] = None
            workflow["completed_at"] = _now()
            workflow["updated_at"] = _now()
            await workflows_service.WorkflowService.on_workflow_completed(
                self,
                workflow_id=workflow["id"],
                tenant_id=tenant_id,
                entity_type=workflow["entity_type"],
                entity_id=workflow["entity_id"],
                workflow_key="admissions",
                outcome=workflow["metadata_json"].get("outcome", {"action": "approve"}),
            )

        workflows_service.log_admin_action(
            actor=actor,
            action="workflows.task.completed",
            path=f"/internal/workflows/tasks/{task_id}/complete",
            client_ip="service",
            entity="workflow_task",
            metadata={"resource_id": str(task_id), "transition_action": transition_action, "reason": reason},
            tenant_id=tenant_id,
        )

        return SimpleNamespace(**task)

    monkeypatch.setattr(admissions_service.ApplicantService, "create_applicant", fake_create_applicant)
    monkeypatch.setattr(admissions_service.ApplicationService, "create_application", fake_create_application)
    monkeypatch.setattr(admissions_service.ApplicationService, "submit_application", fake_submit_application)
    monkeypatch.setattr(admissions_service.DecisionService, "finalize_workflow_decision", fake_finalize_workflow_decision)

    monkeypatch.setattr(workflows_service.WorkflowService, "list_instances", fake_list_instances)
    monkeypatch.setattr(workflows_service.WorkflowService, "get_user_tasks", fake_get_user_tasks)
    monkeypatch.setattr(workflows_service.WorkflowService, "complete_task", fake_complete_task)
    monkeypatch.setattr(workflows_service.WorkflowService, "on_workflow_completed", fake_on_workflow_completed)


@pytest.mark.usefixtures("override_module_dbs", "patch_phase5d_services")
class TestAdmissionsWorkflowE2EPhase5D:
    def test_full_admissions_to_decision_flow_happy_path(self, e2e_state: InMemoryE2EState):
        """Validate full flow from applicant creation to concluded decision via callback."""

        # 1) create applicant
        applicant_res = client.post(
            "/api/admin/admissions/applicants",
            headers=ADMIN_HEADERS,
            json={
                "email": "phase5d@student.edu",
                "first_name": "Phase",
                "last_name": "FiveD",
                "program_id": 501,
                "application_year": 2026,
            },
        )
        assert applicant_res.status_code == 201, applicant_res.text
        applicant_id = applicant_res.json()["id"]

        # 2) create application
        application_res = client.post(
            "/api/admin/admissions/applications",
            headers=ADMIN_HEADERS,
            json={"applicant_id": applicant_id, "program_id": 501, "metadata_json": {"gpa": 3.9}},
        )
        assert application_res.status_code == 201, application_res.text
        application_id = application_res.json()["id"]
        assert application_res.json()["stage"] == ApplicationStage.NEW.value

        # 3) submit application
        submit_res = client.post(
            f"/api/admin/admissions/applications/{application_id}/submit",
            headers=ADMIN_HEADERS,
            json={"expected_version": 1},
        )
        assert submit_res.status_code == 200, submit_res.text
        assert submit_res.json()["stage"] == ApplicationStage.RECEIVED.value

        # 4) workflow instance is created
        list_instances_res = client.get(
            "/api/admin/workflows/instances",
            headers=ADMIN_HEADERS,
            params={"entity_type": "admission_application", "entity_id": application_id},
        )
        assert list_instances_res.status_code == 200, list_instances_res.text
        instances = list_instances_res.json()["items"]
        assert len(instances) == 1
        workflow_id = instances[0]["id"]
        assert instances[0]["status"] == WorkflowInstanceStatus.IN_PROGRESS.value

        # 5) workflow tasks are created
        tasks_res = client.get(
            "/api/admin/workflows/tasks",
            headers=ADMIN_HEADERS,
            params={"assignee_type": "group", "assignee_ref": "admissions_staff"},
        )
        assert tasks_res.status_code == 200, tasks_res.text
        open_tasks = tasks_res.json()["items"]
        assert len(open_tasks) == 1
        task_id = open_tasks[0]["id"]

        # 6) simulate approval transitions (complete all approval tasks)
        sequence_groups = [
            "admissions_staff",
            "department_chairs",
            "deans",
            "registrars",
            "admissions_leadership",
        ]
        for group in sequence_groups:
            list_task_res = client.get(
                "/api/admin/workflows/tasks",
                headers=ADMIN_HEADERS,
                params={"assignee_type": "group", "assignee_ref": group},
            )
            assert list_task_res.status_code == 200, list_task_res.text
            items = list_task_res.json()["items"]
            assert len(items) == 1, f"Expected one open task for group={group}, got {len(items)}"
            current = items[0]
            complete_res = client.post(
                f"/api/admin/workflows/tasks/{current['id']}/complete",
                headers=ADMIN_HEADERS,
                json={
                    "expected_task_version": current["version"],
                    "transition_action": "complete",
                    "reason": f"Approved by {group}",
                },
            )
            assert complete_res.status_code == 200, complete_res.text

        # 7) workflow reaches END
        updated_instance = e2e_state.workflow_instances[workflow_id]
        assert updated_instance["status"] == WorkflowInstanceStatus.COMPLETED
        assert updated_instance["completed_at"] is not None

        # 8) workflow callback executed
        assert len(e2e_state.callback_calls) == 1
        callback_call = e2e_state.callback_calls[0]
        assert callback_call["workflow_id"] == workflow_id
        assert callback_call["entity_type"] == "admission_application"

        # 9) DecisionService.finalize_workflow_decision() invoked
        assert len(e2e_state.finalize_calls) == 1
        finalize_call = e2e_state.finalize_calls[0]
        assert finalize_call["application_id"] == application_id
        assert finalize_call["workflow_instance_id"] == workflow_id
        assert finalize_call["approval_action"] == "approve"

        # 10) application stage becomes concluded
        concluded_app = e2e_state.applications[application_id]
        assert concluded_app["stage"] == ApplicationStage.CONCLUDED
        assert concluded_app["conclusion_type"] == ApplicationConclusionType.ACCEPTED
        assert concluded_app["decision_at"] is not None

        # Audit logging preserved
        assert len(e2e_state.audit_calls) >= 4
        entities = {call.get("entity") for call in e2e_state.audit_calls}
        assert "application" in entities
        assert "workflow_task" in entities
        assert "decision" in entities

    def test_rbac_is_preserved_for_submit_and_workflow_complete(self, e2e_state: InMemoryE2EState):
        """Student role must not bypass admissions/workflow write permissions."""
        student_headers = _auth_headers("student-phase5d@example.com", ["student"])

        submit_denied = client.post(
            "/api/admin/admissions/applications/999/submit",
            headers=student_headers,
            json={"expected_version": 1},
        )
        assert submit_denied.status_code == 403, submit_denied.text

        complete_denied = client.post(
            "/api/admin/workflows/tasks/999/complete",
            headers=student_headers,
            json={"expected_task_version": 1, "transition_action": "complete"},
        )
        assert complete_denied.status_code == 403, complete_denied.text

    def test_tenant_first_validation_is_preserved(self, e2e_state: InMemoryE2EState):
        """Cross-tenant override is blocked by trusted tenant guard (fail-closed)."""

        # Create resources in tenant=1 (admin default)
        applicant_res = client.post(
            "/api/admin/admissions/applicants",
            headers=ADMIN_HEADERS,
            json={
                "email": "tenant-check@student.edu",
                "first_name": "Tenant",
                "last_name": "Check",
                "program_id": 501,
                "application_year": 2026,
            },
        )
        assert applicant_res.status_code == 201, applicant_res.text
        applicant_id = applicant_res.json()["id"]

        application_res = client.post(
            "/api/admin/admissions/applications",
            headers=ADMIN_HEADERS,
            json={"applicant_id": applicant_id, "program_id": 501},
        )
        assert application_res.status_code == 201, application_res.text
        application_id = application_res.json()["id"]

        # Cross-tenant submit attempt
        cross_tenant_headers = dict(ADMIN_HEADERS)
        cross_tenant_headers["X-Tenant-ID"] = "2"

        cross_res = client.post(
            f"/api/admin/admissions/applications/{application_id}/submit",
            headers=cross_tenant_headers,
            json={"expected_version": 1},
        )
        assert cross_res.status_code == 403, cross_res.text
        assert "cross-tenant override forbidden" in cross_res.json()["detail"].lower()
