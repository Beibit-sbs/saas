from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.module_helpers.router_errors import (
    integrity_error_to_http,
    permission_error_to_http,
    tenant_not_found_to_http,
    validation_error_to_http,
)
from app.core.module_helpers.service_validation import (
    OptimisticLockConflictError,
    TenantResourceNotFoundError,
)
from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.observability.metrics import observe_workflow_execution
from app.modules.workflows.dependencies import get_workflows_db
from app.modules.workflows.schemas import (
    WorkflowInstanceListResponseSchema,
    WorkflowInstanceReadSchema,
    WorkflowStartRequestSchema,
    WorkflowTaskAssignRequestSchema,
    WorkflowTaskCommentReadSchema,
    WorkflowTaskCommentRequestSchema,
    WorkflowTaskCompleteRequestSchema,
    WorkflowTaskListResponseSchema,
    WorkflowTaskReadSchema,
)
from app.modules.workflows.workflow_service import WorkflowService
from app.modules.workflows.workflow_task_service import WorkflowTaskService


router = APIRouter(prefix="/api/admin/workflows", tags=["workflows"])


class ErrorDetailResponse(BaseModel):
    detail: Any


def _parse_payload(schema_cls: type[BaseModel], payload: dict[str, Any]) -> BaseModel:
    try:
        return schema_cls.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc


def _raise_workflow_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return permission_error_to_http(exc)
    if isinstance(exc, (IntegrityError, OptimisticLockConflictError)):
        return integrity_error_to_http(exc)
    if isinstance(exc, TenantResourceNotFoundError):
        return tenant_not_found_to_http(exc)
    if isinstance(exc, ValueError):
        return validation_error_to_http(exc)
    raise HTTPException(status_code=400, detail=str(exc))


TrustedTenant = Annotated[dict[str, object], Depends(get_current_tenant)]
Actor = Annotated[str, Depends(get_actor)]
WorkflowsDb = Annotated[Session, Depends(get_workflows_db)]


@router.post(
    "/start",
    response_model=WorkflowInstanceReadSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}, 409: {"model": ErrorDetailResponse}},
    status_code=status.HTTP_201_CREATED,
)
async def start_workflow_endpoint(
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("workflows.write"))] = None,
    tenant: TrustedTenant = None,
    db: WorkflowsDb = None,
) -> WorkflowInstanceReadSchema:
    request_model = _parse_payload(WorkflowStartRequestSchema, payload)
    service = WorkflowService(db)
    try:
        instance = await service.start_workflow(
            tenant_id=int(tenant["id"]),
            workflow_key=request_model.workflow_key,
            entity_type=request_model.entity_type,
            entity_id=request_model.entity_id,
            actor=actor,
            metadata_json=request_model.metadata_json,
            workflow_version_no=request_model.workflow_version_no,
        )
        observe_workflow_execution()
        return WorkflowInstanceReadSchema.model_validate(instance)
    except (PermissionError, ValueError, IntegrityError, TenantResourceNotFoundError) as exc:
        raise _raise_workflow_http_error(exc) from exc


@router.get(
    "/instances",
    response_model=WorkflowInstanceListResponseSchema,
    responses={403: {"model": ErrorDetailResponse}},
)
async def list_workflow_instances_endpoint(
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("workflows.read"))] = None,
    tenant: TrustedTenant = None,
    db: WorkflowsDb = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    status: str | None = None,
    limit: int = 100,
) -> WorkflowInstanceListResponseSchema:
    service = WorkflowService(db)
    rows = await service.list_instances(
        tenant_id=int(tenant["id"]),
        entity_type=entity_type,
        entity_id=entity_id,
        status=status,
        limit=limit,
    )
    items = [WorkflowInstanceReadSchema.model_validate(row) for row in rows]
    return WorkflowInstanceListResponseSchema(total=len(items), items=items)


@router.get(
    "/tasks",
    response_model=WorkflowTaskListResponseSchema,
    responses={403: {"model": ErrorDetailResponse}},
)
async def list_user_tasks_endpoint(
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("workflows.read"))] = None,
    tenant: TrustedTenant = None,
    db: WorkflowsDb = None,
    assignee_type: str = "user",
    assignee_ref: str | None = None,
    include_completed: bool = False,
    limit: int = 100,
) -> WorkflowTaskListResponseSchema:
    service = WorkflowService(db)
    resolved_assignee = assignee_ref if assignee_ref is not None else actor
    rows = await service.get_user_tasks(
        tenant_id=int(tenant["id"]),
        assignee_type=assignee_type,
        assignee_ref=resolved_assignee,
        include_completed=include_completed,
        limit=limit,
    )
    items = [WorkflowTaskReadSchema.model_validate(row) for row in rows]
    return WorkflowTaskListResponseSchema(total=len(items), items=items)


@router.post(
    "/tasks/{task_id}/complete",
    response_model=WorkflowTaskReadSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}, 409: {"model": ErrorDetailResponse}},
)
async def complete_workflow_task_endpoint(
    task_id: int,
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("workflows.write"))] = None,
    tenant: TrustedTenant = None,
    db: WorkflowsDb = None,
) -> WorkflowTaskReadSchema:
    request_model = _parse_payload(WorkflowTaskCompleteRequestSchema, payload)
    service = WorkflowService(db)
    try:
        task = await service.complete_task(
            tenant_id=int(tenant["id"]),
            task_id=task_id,
            actor=actor,
            expected_task_version=request_model.expected_task_version,
            transition_action=request_model.transition_action,
            reason=request_model.reason,
        )
        return WorkflowTaskReadSchema.model_validate(task)
    except (PermissionError, ValueError, IntegrityError, TenantResourceNotFoundError, OptimisticLockConflictError) as exc:
        raise _raise_workflow_http_error(exc) from exc


@router.post(
    "/tasks/{task_id}/assign",
    response_model=WorkflowTaskReadSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}, 409: {"model": ErrorDetailResponse}},
)
async def assign_workflow_task_endpoint(
    task_id: int,
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("workflows.write"))] = None,
    tenant: TrustedTenant = None,
    db: WorkflowsDb = None,
) -> WorkflowTaskReadSchema:
    request_model = _parse_payload(WorkflowTaskAssignRequestSchema, payload)
    service = WorkflowTaskService(db)
    try:
        task = await service.assign_task(
            tenant_id=int(tenant["id"]),
            task_id=task_id,
            assignee_type=request_model.assignee_type,
            assignee_ref=request_model.assignee_ref,
            actor=actor,
            expected_version=request_model.expected_version,
        )
        return WorkflowTaskReadSchema.model_validate(task)
    except (PermissionError, ValueError, IntegrityError, TenantResourceNotFoundError, OptimisticLockConflictError) as exc:
        raise _raise_workflow_http_error(exc) from exc


@router.post(
    "/tasks/{task_id}/comment",
    response_model=WorkflowTaskCommentReadSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}, 409: {"model": ErrorDetailResponse}},
    status_code=status.HTTP_201_CREATED,
)
async def add_workflow_task_comment_endpoint(
    task_id: int,
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("workflows.write"))] = None,
    tenant: TrustedTenant = None,
    db: WorkflowsDb = None,
) -> WorkflowTaskCommentReadSchema:
    request_model = _parse_payload(WorkflowTaskCommentRequestSchema, payload)
    service = WorkflowTaskService(db)
    try:
        comment = await service.add_comment(
            tenant_id=int(tenant["id"]),
            task_id=task_id,
            actor=actor,
            body=request_model.body,
            comment_type=request_model.comment_type,
            visibility=request_model.visibility,
            attachments_json=request_model.attachments_json,
            metadata_json=request_model.metadata_json,
        )
        return WorkflowTaskCommentReadSchema.model_validate(comment)
    except (PermissionError, ValueError, IntegrityError, TenantResourceNotFoundError, OptimisticLockConflictError) as exc:
        raise _raise_workflow_http_error(exc) from exc
