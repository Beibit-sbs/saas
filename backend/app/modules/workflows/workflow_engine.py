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

    def _mark_instance_failed(
        self,
        *,
        instance: WorkflowInstanceModel,
        tenant_id: int,
        actor: str,
        reason: str,
    ) -> None:
        instance.status = WorkflowInstanceStatus.FAILED
        instance.completed_at = _utc_now()
        instance.current_step_id = None

        _audit(
            actor=actor,
            action=build_audit_action("workflows", "instance", "failed"),
            path=f"/internal/workflows/instances/{instance.id}/failed",
            entity="workflow_instance",
            metadata={
                "resource_id": str(instance.id),
                "reason": reason,
            },
            tenant_id=tenant_id,
        )

        self.db.flush()
        self.db.commit()

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
            reason = f"No valid transition for action '{action_key}' from step {from_step_id}"
            self._mark_instance_failed(
                instance=instance,
                tenant_id=tenant_id,
                actor=actor,
                reason=reason,
            )
            raise ValueError(reason)

        try:
            next_tasks = await self.create_next_tasks(
                tenant_id=tenant_id,
                workflow_instance_id=workflow_instance_id,
                transition_rows=transition_rows,
                actor=actor,
            )
        except Exception as exc:
            self._mark_instance_failed(
                instance=instance,
                tenant_id=tenant_id,
                actor=actor,
                reason=str(exc),
            )
            raise

        # End-state close when transition reaches END and no tasks are generated.
        reached_end = False
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
                reached_end = True

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

        # ═══════════════════════════════════════════════════════
        # PHASE 5B: NEW - Invoke callback on workflow completion
        # ═══════════════════════════════════════════════════════
        if reached_end:
            try:
                # Import here to avoid circular dependency
                from app.modules.workflows.workflow_service import WorkflowService

                # Get workflow service to invoke callback
                workflow_service = WorkflowService(self.db)

                # Extract outcome from instance metadata
                outcome = self._extract_outcome_data(instance)

                # Invoke callback (idempotent, safe to retry)
                callback_result = await workflow_service.on_workflow_completed(
                    workflow_id=instance.id,
                    tenant_id=instance.tenant_id,
                    entity_type=instance.entity_type,
                    entity_id=instance.entity_id,
                    workflow_key="",  # Not directly available; will be inferred by handler
                    outcome=outcome,
                )

                # Log callback execution result
                _audit(
                    actor="engine",
                    action=build_audit_action("workflows", "engine", "callback_result"),
                    path=f"/internal/workflows/{workflow_instance_id}/callback_result",
                    entity="workflow_runtime",
                    metadata={
                        "workflow_id": instance.id,
                        "callback_status": callback_result["status"],
                        "result_id": callback_result.get("result_id"),
                    },
                    tenant_id=instance.tenant_id,
                )

            except Exception as e:
                # Callback failure: log error but don't fail workflow completion
                _audit(
                    actor="engine",
                    action=build_audit_action("workflows", "engine", "callback_error"),
                    path=f"/internal/workflows/{workflow_instance_id}/callback_error",
                    entity="workflow_runtime",
                    metadata={
                        "workflow_id": instance.id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    tenant_id=instance.tenant_id,
                )
                # Re-raise: caller decides retry strategy
                raise

        return next_tasks

    @staticmethod
    def _extract_outcome_data(instance: WorkflowInstanceModel) -> dict:
        """
        Extract workflow decision outcome for callback.

        Looks in metadata_json["outcome"] or returns empty dict.

        Args:
            instance: Workflow instance

        Returns:
            Outcome dict {
                "action": "approve"|"reject"|None,
                "reason": str,
                "metadata": dict,
            } or empty dict
        """
        if not instance.metadata_json:
            return {}

        outcome = instance.metadata_json.get("outcome")
        if isinstance(outcome, dict):
            return outcome

        return {}

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
