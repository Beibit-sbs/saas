from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import (
    assert_resource_belongs_to_tenant,
    validate_tenant_id_provided,
)
from app.modules.audit.service import log_admin_action
from app.modules.workflows.models import (
    WorkflowAssigneeType,
    WorkflowInstanceModel,
    WorkflowInstanceStatus,
    WorkflowStepModel,
    WorkflowStepType,
    WorkflowTaskModel,
    WorkflowTaskStatus,
    WorkflowTransitionModel,
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _audit(*, actor: str, action: str, path: str, entity: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity=entity,
        metadata=metadata,
        tenant_id=tenant_id,
    )


class WorkflowRuntimeEngine:
    """Runtime transition executor decoupled from API layer."""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def execute_transition(
        self,
        tenant_id: int,
        workflow_instance_id: int,
        from_step_id: int,
        action_key: str,
        actor: str,
    ) -> list[WorkflowTaskModel]:
        tenant_id = validate_tenant_id_provided(tenant_id)
        if not action_key or not action_key.strip():
            raise ValueError("action_key is required")

        instance = self.db.execute(
            select(WorkflowInstanceModel).where(
                and_(
                    WorkflowInstanceModel.id == workflow_instance_id,
                    WorkflowInstanceModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            instance,
            tenant_id,
            resource_name="Workflow instance",
            resource_id=workflow_instance_id,
        )

        transition_rows = self.db.execute(
            select(WorkflowTransitionModel).where(
                and_(
                    WorkflowTransitionModel.tenant_id == tenant_id,
                    WorkflowTransitionModel.workflow_definition_version_id
                    == instance.workflow_definition_version_id,
                    WorkflowTransitionModel.from_step_id == from_step_id,
                    WorkflowTransitionModel.action_key == action_key,
                )
            )
        ).scalars().all()

        if not transition_rows:
            transition_rows = self.db.execute(
                select(WorkflowTransitionModel).where(
                    and_(
                        WorkflowTransitionModel.tenant_id == tenant_id,
                        WorkflowTransitionModel.workflow_definition_version_id
                        == instance.workflow_definition_version_id,
                        WorkflowTransitionModel.from_step_id == from_step_id,
                        WorkflowTransitionModel.is_default.is_(True),
                    )
                )
            ).scalars().all()

        if not transition_rows:
            raise ValueError(
                f"No valid transition for action '{action_key}' from step {from_step_id}"
            )

        next_tasks = await self.create_next_tasks(
            tenant_id=tenant_id,
            workflow_instance_id=workflow_instance_id,
            transition_rows=transition_rows,
            actor=actor,
        )

        # End-state close when transition reaches END and no tasks are generated.
        if not next_tasks:
            target_steps = self.db.execute(
                select(WorkflowStepModel).where(
                    and_(
                        WorkflowStepModel.tenant_id == tenant_id,
                        WorkflowStepModel.id.in_([row.to_step_id for row in transition_rows]),
                    )
                )
            ).scalars().all()
            if any(step.step_type == WorkflowStepType.END for step in target_steps):
                instance.status = WorkflowInstanceStatus.COMPLETED
                instance.completed_at = _utc_now()
                instance.current_step_id = None

        self.db.flush()
        self.db.refresh(instance)

        _audit(
            actor=actor,
            action=build_audit_action("workflows", "instance", "transitioned"),
            path=f"/internal/workflows/instances/{workflow_instance_id}/transition",
            entity="workflow_instance",
            metadata={
                "resource_id": str(workflow_instance_id),
                "from_step_id": from_step_id,
                "action_key": action_key,
                "created_task_ids": [task.id for task in next_tasks],
            },
            tenant_id=tenant_id,
        )

        self.db.commit()
        return next_tasks

    async def create_next_tasks(
        self,
        tenant_id: int,
        workflow_instance_id: int,
        transition_rows: list[WorkflowTransitionModel],
        actor: str,
    ) -> list[WorkflowTaskModel]:
        tenant_id = validate_tenant_id_provided(tenant_id)
        if not transition_rows:
            return []

        instance = self.db.execute(
            select(WorkflowInstanceModel).where(
                and_(
                    WorkflowInstanceModel.id == workflow_instance_id,
                    WorkflowInstanceModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            instance,
            tenant_id,
            resource_name="Workflow instance",
            resource_id=workflow_instance_id,
        )

        to_step_ids = [row.to_step_id for row in transition_rows]
        next_steps = self.db.execute(
            select(WorkflowStepModel).where(
                and_(
                    WorkflowStepModel.tenant_id == tenant_id,
                    WorkflowStepModel.id.in_(to_step_ids),
                )
            )
        ).scalars().all()

        if not next_steps:
            return []

        return await self.resolve_parallel_steps(
            tenant_id=tenant_id,
            workflow_instance=instance,
            steps=next_steps,
            actor=actor,
        )

    async def resolve_parallel_steps(
        self,
        tenant_id: int,
        workflow_instance: WorkflowInstanceModel,
        steps: list[WorkflowStepModel],
        actor: str,
    ) -> list[WorkflowTaskModel]:
        tenant_id = validate_tenant_id_provided(tenant_id)

        created_tasks: list[WorkflowTaskModel] = []
        sequence_no = len(
            self.db.execute(
                select(WorkflowTaskModel.id).where(
                    and_(
                        WorkflowTaskModel.tenant_id == tenant_id,
                        WorkflowTaskModel.workflow_instance_id == workflow_instance.id,
                    )
                )
            ).all()
        )

        for step in sorted(steps, key=lambda item: (item.sequence_hint or 0, item.id)):
            workflow_instance.current_step_id = step.id

            if step.step_type in (WorkflowStepType.TASK, WorkflowStepType.APPROVAL):
                sequence_no += 1
                task = WorkflowTaskModel(
                    tenant_id=tenant_id,
                    workflow_instance_id=workflow_instance.id,
                    workflow_step_id=step.id,
                    task_type=step.task_type or "generic",
                    status=WorkflowTaskStatus.OPEN,
                    assignee_type=(step.assignee_type or WorkflowAssigneeType.ROLE),
                    assignee_ref=(step.assignee_ref or "admin"),
                    title=step.name,
                    instructions=None,
                    due_at=None,
                    sequence_no=sequence_no,
                    is_blocking=bool(step.is_blocking),
                    metadata_json={},
                    created_by=actor,
                    updated_by=actor,
                )
                self.db.add(task)
                created_tasks.append(task)

            if step.step_type == WorkflowStepType.END:
                workflow_instance.status = WorkflowInstanceStatus.COMPLETED
                workflow_instance.completed_at = _utc_now()
                workflow_instance.current_step_id = None

        if created_tasks and workflow_instance.status != WorkflowInstanceStatus.COMPLETED:
            workflow_instance.status = WorkflowInstanceStatus.IN_PROGRESS

        self.db.flush()
        for task in created_tasks:
            self.db.refresh(task)

        _audit(
            actor=actor,
            action=build_audit_action("workflows", "task", "created"),
            path=f"/internal/workflows/instances/{workflow_instance.id}/tasks",
            entity="workflow_task",
            metadata={
                "workflow_instance_id": workflow_instance.id,
                "task_ids": [task.id for task in created_tasks],
            },
            tenant_id=tenant_id,
        )

        return created_tasks
