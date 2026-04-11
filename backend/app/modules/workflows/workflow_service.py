from __future__ import annotations

from sqlalchemy import and_, desc, select
from sqlalchemy.orm import Session

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import (
    assert_resource_belongs_to_tenant,
    validate_tenant_id_provided,
    validate_version_match,
)
from app.modules.audit.service import log_admin_action
from app.modules.workflows.models import (
    WorkflowDefinitionModel,
    WorkflowDefinitionStatus,
    WorkflowDefinitionVersionModel,
    WorkflowInstanceModel,
    WorkflowInstanceStatus,
    WorkflowStepModel,
    WorkflowStepType,
    WorkflowTaskModel,
    WorkflowTaskStatus,
    WorkflowTaskCommentModel,
)
from app.modules.workflows.workflow_engine import WorkflowRuntimeEngine
from app.modules.workflows.schemas import (
    WorkflowConsistencyIssueSchema,
    WorkflowConsistencyReportSchema,
)
from app.modules.workflows.workflow_task_service import WorkflowTaskService


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


class WorkflowService:
    """Workflow runtime facade used by future API layer."""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.runtime = WorkflowRuntimeEngine(db_session)
        self.task_service = WorkflowTaskService(db_session)

    async def start_workflow(
        self,
        tenant_id: int,
        workflow_key: str,
        entity_type: str,
        entity_id: int,
        actor: str,
        *,
        metadata_json: dict | None = None,
        workflow_version_no: int | None = None,
    ) -> WorkflowInstanceModel:
        tenant_id = validate_tenant_id_provided(tenant_id)
        if not workflow_key or not workflow_key.strip():
            raise ValueError("workflow_key is required")
        if not entity_type or not entity_type.strip() or int(entity_id) <= 0:
            raise ValueError("entity_type and positive entity_id are required")

        definition = self.db.execute(
            select(WorkflowDefinitionModel).where(
                and_(
                    WorkflowDefinitionModel.tenant_id == tenant_id,
                    WorkflowDefinitionModel.key == workflow_key.strip(),
                    WorkflowDefinitionModel.status.in_(
                        [
                            WorkflowDefinitionStatus.ACTIVE,
                            WorkflowDefinitionStatus.DRAFT,
                        ]
                    ),
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            definition,
            tenant_id,
            resource_name="Workflow definition",
        )

        version_query = select(WorkflowDefinitionVersionModel).where(
            and_(
                WorkflowDefinitionVersionModel.tenant_id == tenant_id,
                WorkflowDefinitionVersionModel.workflow_definition_id == definition.id,
            )
        )
        if workflow_version_no is not None:
            version_query = version_query.where(WorkflowDefinitionVersionModel.version_no == workflow_version_no)
        else:
            version_query = version_query.where(WorkflowDefinitionVersionModel.is_active.is_(True))

        definition_version = self.db.execute(
            version_query.order_by(desc(WorkflowDefinitionVersionModel.version_no))
        ).scalars().first()
        assert_resource_belongs_to_tenant(
            definition_version,
            tenant_id,
            resource_name="Workflow definition version",
        )

        start_step = self.db.execute(
            select(WorkflowStepModel).where(
                and_(
                    WorkflowStepModel.tenant_id == tenant_id,
                    WorkflowStepModel.workflow_definition_version_id == definition_version.id,
                    WorkflowStepModel.step_type == WorkflowStepType.START,
                )
            )
        ).scalars().first()
        assert_resource_belongs_to_tenant(start_step, tenant_id, resource_name="Workflow start step")

        instance = WorkflowInstanceModel(
            tenant_id=tenant_id,
            workflow_definition_id=definition.id,
            workflow_definition_version_id=definition_version.id,
            entity_type=entity_type.strip(),
            entity_id=int(entity_id),
            status=WorkflowInstanceStatus.PENDING,
            current_step_id=start_step.id,
            initiated_by=actor,
            metadata_json=metadata_json or {},
            created_by=actor,
            updated_by=actor,
        )
        self.db.add(instance)
        self.db.flush()
        self.db.refresh(instance)

        # Kickoff transition from START; default transition is used when key is absent.
        await self.runtime.execute_transition(
            tenant_id=tenant_id,
            workflow_instance_id=instance.id,
            from_step_id=start_step.id,
            action_key="start",
            actor=actor,
        )

        refreshed = self.db.execute(
            select(WorkflowInstanceModel).where(
                and_(WorkflowInstanceModel.id == instance.id, WorkflowInstanceModel.tenant_id == tenant_id)
            )
        ).scalar_one()

        _audit(
            actor=actor,
            action=build_audit_action("workflows", "instance", "started"),
            path=f"/internal/workflows/instances/{instance.id}",
            entity="workflow_instance",
            metadata={
                "resource_id": str(instance.id),
                "workflow_key": workflow_key,
                "workflow_version_no": definition_version.version_no,
                "entity_type": entity_type,
                "entity_id": entity_id,
            },
            tenant_id=tenant_id,
        )

        self.db.commit()
        return refreshed

    async def complete_task(
        self,
        tenant_id: int,
        task_id: int,
        actor: str,
        *,
        expected_task_version: int,
        transition_action: str = "complete",
        reason: str | None = None,
    ) -> WorkflowTaskModel:
        tenant_id = validate_tenant_id_provided(tenant_id)

        task = self.db.execute(
            select(WorkflowTaskModel).where(
                and_(WorkflowTaskModel.id == task_id, WorkflowTaskModel.tenant_id == tenant_id)
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(task, tenant_id, resource_name="Workflow task", resource_id=task_id)
        validate_version_match(task.version, expected_task_version)

        completed_task = await self.task_service.complete_task(
            tenant_id=tenant_id,
            task_id=task_id,
            actor=actor,
            expected_version=expected_task_version,
            reason=reason,
        )

        instance = self.db.execute(
            select(WorkflowInstanceModel).where(
                and_(
                    WorkflowInstanceModel.id == completed_task.workflow_instance_id,
                    WorkflowInstanceModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            instance,
            tenant_id,
            resource_name="Workflow instance",
            resource_id=completed_task.workflow_instance_id,
        )

        if completed_task.workflow_step_id is not None:
            await self.runtime.execute_transition(
                tenant_id=tenant_id,
                workflow_instance_id=instance.id,
                from_step_id=completed_task.workflow_step_id,
                action_key=transition_action,
                actor=actor,
            )
        else:
            open_tasks = self.db.execute(
                select(WorkflowTaskModel.id).where(
                    and_(
                        WorkflowTaskModel.tenant_id == tenant_id,
                        WorkflowTaskModel.workflow_instance_id == instance.id,
                        WorkflowTaskModel.status.in_(
                            [
                                WorkflowTaskStatus.OPEN,
                                WorkflowTaskStatus.ASSIGNED,
                                WorkflowTaskStatus.IN_PROGRESS,
                            ]
                        ),
                    )
                )
            ).all()
            if not open_tasks:
                instance.status = WorkflowInstanceStatus.COMPLETED

        self.db.flush()

        _audit(
            actor=actor,
            action=build_audit_action("workflows", "task", "completed"),
            path=f"/internal/workflows/tasks/{task_id}",
            entity="workflow_task",
            metadata={
                "resource_id": str(task_id),
                "workflow_instance_id": completed_task.workflow_instance_id,
                "transition_action": transition_action,
            },
            tenant_id=tenant_id,
        )

        self.db.commit()
        return completed_task

    async def get_user_tasks(
        self,
        tenant_id: int,
        assignee_ref: str,
        *,
        assignee_type: str = "user",
        include_completed: bool = False,
        limit: int = 100,
    ) -> list[WorkflowTaskModel]:
        tenant_id = validate_tenant_id_provided(tenant_id)
        if not assignee_ref or not assignee_ref.strip():
            raise ValueError("assignee_ref is required")

        query = select(WorkflowTaskModel).where(
            and_(
                WorkflowTaskModel.tenant_id == tenant_id,
                WorkflowTaskModel.assignee_type == assignee_type,
                WorkflowTaskModel.assignee_ref == assignee_ref.strip(),
            )
        )

        if not include_completed:
            query = query.where(
                WorkflowTaskModel.status.in_(
                    [
                        WorkflowTaskStatus.OPEN,
                        WorkflowTaskStatus.ASSIGNED,
                        WorkflowTaskStatus.IN_PROGRESS,
                    ]
                )
            )

        rows = self.db.execute(
            query.order_by(
                WorkflowTaskModel.due_at.asc().nulls_last(),
                WorkflowTaskModel.created_at.desc(),
            ).limit(max(1, min(limit, 500)))
        ).scalars().all()

        return list(rows)

    async def list_instances(
        self,
        tenant_id: int,
        *,
        entity_type: str | None = None,
        entity_id: int | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[WorkflowInstanceModel]:
        tenant_id = validate_tenant_id_provided(tenant_id)

        query = select(WorkflowInstanceModel).where(WorkflowInstanceModel.tenant_id == tenant_id)

        if entity_type is not None and entity_type.strip():
            query = query.where(WorkflowInstanceModel.entity_type == entity_type.strip())
        if entity_id is not None:
            query = query.where(WorkflowInstanceModel.entity_id == int(entity_id))
        if status is not None and status.strip():
            query = query.where(WorkflowInstanceModel.status == status.strip())

        rows = self.db.execute(
            query.order_by(WorkflowInstanceModel.created_at.desc()).limit(max(1, min(limit, 500)))
        ).scalars().all()

        return list(rows)

    async def get_tenant_consistency_report(
        self,
        tenant_id: int,
    ) -> WorkflowConsistencyReportSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)

        definitions = self.db.execute(
            select(WorkflowDefinitionModel.id).where(WorkflowDefinitionModel.tenant_id == tenant_id)
        ).scalars().all()
        definition_versions = self.db.execute(
            select(WorkflowDefinitionVersionModel.id).where(
                WorkflowDefinitionVersionModel.tenant_id == tenant_id
            )
        ).scalars().all()
        steps = self.db.execute(
            select(WorkflowStepModel.id).where(WorkflowStepModel.tenant_id == tenant_id)
        ).scalars().all()
        instances = self.db.execute(
            select(WorkflowInstanceModel)
            .where(WorkflowInstanceModel.tenant_id == tenant_id)
            .order_by(WorkflowInstanceModel.id)
        ).scalars().all()
        tasks = self.db.execute(
            select(WorkflowTaskModel)
            .where(WorkflowTaskModel.tenant_id == tenant_id)
            .order_by(WorkflowTaskModel.id)
        ).scalars().all()
        comments = self.db.execute(
            select(WorkflowTaskCommentModel)
            .where(WorkflowTaskCommentModel.tenant_id == tenant_id)
            .order_by(WorkflowTaskCommentModel.id)
        ).scalars().all()

        definition_ids = {int(item) for item in definitions}
        definition_version_ids = {int(item) for item in definition_versions}
        step_ids = {int(item) for item in steps}
        instance_ids = {int(instance.id) for instance in instances}
        task_ids = {int(task.id) for task in tasks}

        issues: list[WorkflowConsistencyIssueSchema] = []

        for instance in instances:
            instance_id = int(instance.id)
            if int(instance.workflow_definition_id) not in definition_ids:
                issues.append(
                    WorkflowConsistencyIssueSchema(
                        issue_type="instance_missing_definition",
                        workflow_instance_id=instance_id,
                        reference_id=int(instance.workflow_definition_id),
                        detail="Workflow instance references a missing definition.",
                    )
                )
            if int(instance.workflow_definition_version_id) not in definition_version_ids:
                issues.append(
                    WorkflowConsistencyIssueSchema(
                        issue_type="instance_missing_definition_version",
                        workflow_instance_id=instance_id,
                        reference_id=int(instance.workflow_definition_version_id),
                        detail="Workflow instance references a missing definition version.",
                    )
                )
            if instance.current_step_id is not None and int(instance.current_step_id) not in step_ids:
                issues.append(
                    WorkflowConsistencyIssueSchema(
                        issue_type="instance_missing_current_step",
                        workflow_instance_id=instance_id,
                        reference_id=int(instance.current_step_id),
                        detail="Workflow instance points to a missing current step.",
                    )
                )

        for task in tasks:
            task_id = int(task.id)
            if int(task.workflow_instance_id) not in instance_ids:
                issues.append(
                    WorkflowConsistencyIssueSchema(
                        issue_type="task_missing_instance",
                        workflow_task_id=task_id,
                        reference_id=int(task.workflow_instance_id),
                        detail="Workflow task references a missing instance.",
                    )
                )
            if task.workflow_step_id is not None and int(task.workflow_step_id) not in step_ids:
                issues.append(
                    WorkflowConsistencyIssueSchema(
                        issue_type="task_missing_step",
                        workflow_task_id=task_id,
                        reference_id=int(task.workflow_step_id),
                        detail="Workflow task references a missing workflow step.",
                    )
                )

        for comment in comments:
            comment_id = int(comment.id)
            if int(comment.workflow_task_id) not in task_ids:
                issues.append(
                    WorkflowConsistencyIssueSchema(
                        issue_type="comment_missing_task",
                        comment_id=comment_id,
                        reference_id=int(comment.workflow_task_id),
                        detail="Workflow comment references a missing task.",
                    )
                )

        return WorkflowConsistencyReportSchema(
            definition_count=len(definition_ids),
            definition_version_count=len(definition_version_ids),
            step_count=len(step_ids),
            instance_count=len(instances),
            task_count=len(tasks),
            comment_count=len(comments),
            issue_count=len(issues),
            issues=issues,
        )

    async def on_workflow_completed(
        self,
        workflow_id: int,
        tenant_id: int,
        entity_type: str,
        entity_id: int,
        workflow_key: str,
        outcome: dict | None = None,
    ) -> dict:
        """
        Handle workflow completion callback (dispatcher).
        
        Invoked by WorkflowRuntimeEngine when workflow reaches END state.
        Dispatches to appropriate handler based on entity_type.
        
        Idempotent: safe to call multiple times.
        
        Args:
            workflow_id: Workflow instance ID
            tenant_id: Tenant (mandatory, fail-closed)
            entity_type: "admission_application" | other_type
            entity_id: Application ID (for admission_application)
            workflow_key: "admissions" | other_key
            outcome: Workflow outcome {
                "action": "approve"|"reject"|None,
                "reason": str,
                "metadata": dict,
            }
        
        Returns:
            {
                "status": "success" | "no_action" | "skipped",
                "entity_type": str,
                "entity_id": int,
                "result_id": int | None,
                "message": str,
            }
        
        Raises:
            ValueError: Invalid input, validation failure
            PermissionError: Tenant mismatch
        """
        # Fail-closed: validate tenant
        tenant_id = validate_tenant_id_provided(tenant_id)
        
        # Get callback registry
        from app.modules.workflows.callback_handler import get_callback_registry
        
        registry = get_callback_registry()
        
        # Dispatch to handler (safe unknown entity → no_action)
        try:
            result = await registry.dispatch(
                workflow_id=workflow_id,
                tenant_id=tenant_id,
                entity_type=entity_type,
                entity_id=entity_id,
                workflow_key=workflow_key,
                outcome=outcome,
            )
            
            # Audit callback execution
            _audit(
                actor="system@workflow",
                action=build_audit_action("workflows", "callback", "executed"),
                path=f"/internal/workflows/{workflow_id}/callback",
                entity="workflow_callback",
                metadata={
                    "workflow_id": workflow_id,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "callback_status": result["status"],
                    "result_id": result.get("result_id"),
                },
                tenant_id=tenant_id,
            )
            
            return result
        
        except Exception as e:
            # Callback failure: log and propagate
            _audit(
                actor="system@workflow",
                action=build_audit_action("workflows", "callback", "failed"),
                path=f"/internal/workflows/{workflow_id}/callback_error",
                entity="workflow_callback",
                metadata={
                    "workflow_id": workflow_id,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                tenant_id=tenant_id,
            )
            # Propagate: caller decides retry strategy
            raise
