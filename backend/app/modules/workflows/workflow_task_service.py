from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import (
    assert_resource_belongs_to_tenant,
    validate_tenant_id_provided,
    validate_version_match,
)
from app.modules.audit.service import log_admin_action
from app.modules.workflows.models import (
    WorkflowApprovalAction,
    WorkflowApprovalModel,
    WorkflowAssigneeType,
    WorkflowCommentType,
    WorkflowCommentVisibility,
    WorkflowTaskCommentModel,
    WorkflowTaskModel,
    WorkflowTaskStatus,
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


class WorkflowTaskService:
    """Task-level operations used by runtime/service layer (no router concerns)."""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def assign_task(
        self,
        tenant_id: int,
        task_id: int,
        assignee_type: str,
        assignee_ref: str,
        actor: str,
        expected_version: int,
    ) -> WorkflowTaskModel:
        tenant_id = validate_tenant_id_provided(tenant_id)

        task = self.db.execute(
            select(WorkflowTaskModel).where(
                and_(
                    WorkflowTaskModel.id == task_id,
                    WorkflowTaskModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(task, tenant_id, resource_name="Workflow task", resource_id=task_id)
        validate_version_match(task.version, expected_version)

        try:
            task.assignee_type = WorkflowAssigneeType(assignee_type)
        except ValueError as exc:
            raise ValueError(f"Unsupported assignee_type: {assignee_type}") from exc
        task.assignee_ref = assignee_ref
        if task.status == WorkflowTaskStatus.OPEN:
            task.status = WorkflowTaskStatus.ASSIGNED
        task.version += 1

        self.db.flush()
        self.db.refresh(task)

        _audit(
            actor=actor,
            action=build_audit_action("workflows", "task", "assigned"),
            path=f"/internal/workflows/tasks/{task.id}/assign",
            entity="workflow_task",
            metadata={
                "resource_id": str(task.id),
                "assignee_type": assignee_type,
                "assignee_ref": assignee_ref,
            },
            tenant_id=tenant_id,
        )

        self.db.commit()
        return task

    async def complete_task(
        self,
        tenant_id: int,
        task_id: int,
        actor: str,
        expected_version: int,
        *,
        approval_action: WorkflowApprovalAction | None = None,
        reason: str | None = None,
        step_key: str | None = None,
    ) -> WorkflowTaskModel:
        tenant_id = validate_tenant_id_provided(tenant_id)

        task = self.db.execute(
            select(WorkflowTaskModel).where(
                and_(
                    WorkflowTaskModel.id == task_id,
                    WorkflowTaskModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(task, tenant_id, resource_name="Workflow task", resource_id=task_id)
        validate_version_match(task.version, expected_version)

        task.status = WorkflowTaskStatus.COMPLETED
        task.completed_at = _utc_now()
        task.version += 1

        if approval_action is not None:
            existing_count = self.db.execute(
                select(WorkflowApprovalModel.id).where(
                    and_(
                        WorkflowApprovalModel.tenant_id == tenant_id,
                        WorkflowApprovalModel.workflow_task_id == task.id,
                    )
                )
            ).all()
            approval = WorkflowApprovalModel(
                tenant_id=tenant_id,
                workflow_instance_id=task.workflow_instance_id,
                workflow_task_id=task.id,
                action=approval_action,
                actor=actor,
                reason=reason,
                acted_at=_utc_now(),
                step_key=step_key,
                sequence_no=len(existing_count) + 1,
                decision_payload_json={},
                metadata_json={},
                created_by=actor,
            )
            self.db.add(approval)

        self.db.flush()
        self.db.refresh(task)

        _audit(
            actor=actor,
            action=build_audit_action("workflows", "task", "completed"),
            path=f"/internal/workflows/tasks/{task.id}/complete",
            entity="workflow_task",
            metadata={
                "resource_id": str(task.id),
                "workflow_instance_id": task.workflow_instance_id,
            },
            tenant_id=tenant_id,
        )

        self.db.commit()
        return task

    async def add_comment(
        self,
        tenant_id: int,
        task_id: int,
        actor: str,
        body: str,
        *,
        comment_type: str = "note",
        visibility: str = "internal",
        attachments_json: list | None = None,
        metadata_json: dict | None = None,
    ) -> WorkflowTaskCommentModel:
        tenant_id = validate_tenant_id_provided(tenant_id)
        if not body or not body.strip():
            raise ValueError("comment body is required")

        task = self.db.execute(
            select(WorkflowTaskModel).where(
                and_(
                    WorkflowTaskModel.id == task_id,
                    WorkflowTaskModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(task, tenant_id, resource_name="Workflow task", resource_id=task_id)

        comment = WorkflowTaskCommentModel(
            tenant_id=tenant_id,
            workflow_task_id=task_id,
            comment_type=WorkflowCommentType(comment_type),
            visibility=WorkflowCommentVisibility(visibility),
            body=body.strip(),
            attachments_json=attachments_json or [],
            metadata_json=metadata_json or {},
            created_by=actor,
        )
        self.db.add(comment)
        self.db.flush()
        self.db.refresh(comment)

        _audit(
            actor=actor,
            action=build_audit_action("workflows", "task_comment", "added"),
            path=f"/internal/workflows/tasks/{task_id}/comments/{comment.id}",
            entity="workflow_task_comment",
            metadata={
                "resource_id": str(comment.id),
                "workflow_task_id": task_id,
                "comment_type": comment_type,
            },
            tenant_id=tenant_id,
        )

        # Append-only by design: only INSERT happens here.
        self.db.commit()
        return comment
