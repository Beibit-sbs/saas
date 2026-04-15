from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status
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
    DomainValidationError,
    TenantResourceNotFoundError,
)
from app.core.tenant import get_current_tenant
from app.modules.feature_flags.service import is_flag_enabled
from app.modules.interventions.dependencies import get_interventions_db
from app.modules.interventions.playbook_models import PlaybookExecutionStatus
from app.modules.interventions.playbook_schemas import (
    PlaybookCreateSchema,
    PlaybookExecutionAbandonSchema,
    PlaybookExecutionListResponseSchema,
    PlaybookExecutionReadSchema,
    PlaybookExecutionStartSchema,
    PlaybookListResponseSchema,
    PlaybookReadSchema,
    PlaybookStepCompleteSchema,
    PlaybookStepExecutionReadSchema,
    PlaybookStepSkipSchema,
    PlaybookUpdateSchema,
)
from app.modules.interventions.playbook_service import PlaybookService
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/interventions/playbooks", tags=["interventions-playbooks"])
_PLAYBOOKS_FLAG_KEY = "interventions.auto_playbooks"


class ErrorDetailResponse(BaseModel):
    detail: Any


def _parse(schema_cls: type, payload: dict[str, Any]) -> Any:
    try:
        return schema_cls.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc


def _raise(exc: Exception) -> HTTPException:
    if isinstance(exc, HTTPException):
        return exc
    if isinstance(exc, PermissionError):
        return permission_error_to_http(exc)
    if isinstance(exc, TenantResourceNotFoundError):
        return tenant_not_found_to_http(exc)
    if isinstance(exc, DomainValidationError):
        return validation_error_to_http(exc)
    if isinstance(exc, IntegrityError):
        return integrity_error_to_http(exc)
    if isinstance(exc, ValueError):
        return validation_error_to_http(exc)
    raise HTTPException(status_code=400, detail=str(exc))


def _ensure_playbooks_enabled(tenant_id: int) -> None:
    if not is_flag_enabled(_PLAYBOOKS_FLAG_KEY, tenant_id=tenant_id, default=False):
        raise HTTPException(status_code=403, detail="intervention playbooks feature is disabled")


_common_errors = {
    400: {"model": ErrorDetailResponse},
    403: {"model": ErrorDetailResponse},
    404: {"model": ErrorDetailResponse},
    409: {"model": ErrorDetailResponse},
}

# ---------------------------------------------------------------------------
# Playbook template CRUD
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=PlaybookReadSchema,
    status_code=status.HTTP_201_CREATED,
    responses=_common_errors,
    dependencies=[Depends(permission_dependency("interventions:manage_playbooks"))],
)
def create_playbook(
    payload: Annotated[dict[str, Any], Body()],
    tenant_id: Annotated[int, Depends(get_current_tenant)],
    actor: Annotated[str, Depends(get_actor)],
    db: Annotated[Session, Depends(get_interventions_db)],
) -> PlaybookReadSchema:
    try:
        _ensure_playbooks_enabled(tenant_id)
        data = _parse(PlaybookCreateSchema, payload)
        playbook = PlaybookService(db).create_playbook(
            tenant_id=tenant_id, actor=actor, payload=data
        )
        db.commit()
        db.refresh(playbook)
    except Exception as exc:
        db.rollback()
        raise _raise(exc) from exc
    return PlaybookReadSchema.model_validate(playbook)


@router.get(
    "",
    response_model=PlaybookListResponseSchema,
    dependencies=[Depends(permission_dependency("interventions:view"))],
)
def list_playbooks(
    tenant_id: Annotated[int, Depends(get_current_tenant)],
    db: Annotated[Session, Depends(get_interventions_db)],
    enabled_only: bool = Query(default=False),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> PlaybookListResponseSchema:
    items, total = PlaybookService(db).list_playbooks(
        tenant_id=tenant_id,
        enabled_only=enabled_only,
        offset=offset,
        limit=limit,
    )
    return PlaybookListResponseSchema(
        items=[PlaybookReadSchema.model_validate(p) for p in items],
        total=total,
    )


@router.get(
    "/{playbook_id}",
    response_model=PlaybookReadSchema,
    responses={404: {"model": ErrorDetailResponse}},
    dependencies=[Depends(permission_dependency("interventions:view"))],
)
def get_playbook(
    playbook_id: int,
    tenant_id: Annotated[int, Depends(get_current_tenant)],
    db: Annotated[Session, Depends(get_interventions_db)],
) -> PlaybookReadSchema:
    try:
        playbook = PlaybookService(db).get_playbook(
            tenant_id=tenant_id, playbook_id=playbook_id
        )
    except Exception as exc:
        raise _raise(exc) from exc
    return PlaybookReadSchema.model_validate(playbook)


@router.patch(
    "/{playbook_id}",
    response_model=PlaybookReadSchema,
    responses=_common_errors,
    dependencies=[Depends(permission_dependency("interventions:manage_playbooks"))],
)
def update_playbook(
    playbook_id: int,
    payload: Annotated[dict[str, Any], Body()],
    tenant_id: Annotated[int, Depends(get_current_tenant)],
    actor: Annotated[str, Depends(get_actor)],
    db: Annotated[Session, Depends(get_interventions_db)],
) -> PlaybookReadSchema:
    try:
        _ensure_playbooks_enabled(tenant_id)
        data = _parse(PlaybookUpdateSchema, payload)
        playbook = PlaybookService(db).update_playbook(
            tenant_id=tenant_id,
            playbook_id=playbook_id,
            actor=actor,
            payload=data,
        )
        db.commit()
        db.refresh(playbook)
    except Exception as exc:
        db.rollback()
        raise _raise(exc) from exc
    return PlaybookReadSchema.model_validate(playbook)


@router.delete(
    "/{playbook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=_common_errors,
    dependencies=[Depends(permission_dependency("interventions:manage_playbooks"))],
)
def delete_playbook(
    playbook_id: int,
    tenant_id: Annotated[int, Depends(get_current_tenant)],
    actor: Annotated[str, Depends(get_actor)],
    db: Annotated[Session, Depends(get_interventions_db)],
) -> Response:
    try:
        _ensure_playbooks_enabled(tenant_id)
        PlaybookService(db).delete_playbook(
            tenant_id=tenant_id, playbook_id=playbook_id, actor=actor
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        raise _raise(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Playbook executions
# ---------------------------------------------------------------------------


@router.post(
    "/executions",
    response_model=PlaybookExecutionReadSchema,
    status_code=status.HTTP_201_CREATED,
    responses=_common_errors,
    dependencies=[Depends(permission_dependency("interventions:execute_playbook"))],
)
def start_execution(
    payload: Annotated[dict[str, Any], Body()],
    tenant_id: Annotated[int, Depends(get_current_tenant)],
    actor: Annotated[str, Depends(get_actor)],
    db: Annotated[Session, Depends(get_interventions_db)],
) -> PlaybookExecutionReadSchema:
    try:
        _ensure_playbooks_enabled(tenant_id)
        data = _parse(PlaybookExecutionStartSchema, payload)
        execution = PlaybookService(db).start_execution(
            tenant_id=tenant_id, actor=actor, payload=data
        )
        db.commit()
        db.refresh(execution)
    except Exception as exc:
        db.rollback()
        raise _raise(exc) from exc
    return PlaybookExecutionReadSchema.model_validate(execution)


@router.get(
    "/executions",
    response_model=PlaybookExecutionListResponseSchema,
    dependencies=[Depends(permission_dependency("interventions:view"))],
)
def list_executions(
    tenant_id: Annotated[int, Depends(get_current_tenant)],
    db: Annotated[Session, Depends(get_interventions_db)],
    playbook_id: int | None = Query(default=None),
    case_id: int | None = Query(default=None),
    exec_status: PlaybookExecutionStatus | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> PlaybookExecutionListResponseSchema:
    items, total = PlaybookService(db).list_executions(
        tenant_id=tenant_id,
        playbook_id=playbook_id,
        case_id=case_id,
        status=exec_status,
        offset=offset,
        limit=limit,
    )
    return PlaybookExecutionListResponseSchema(
        items=[PlaybookExecutionReadSchema.model_validate(e) for e in items],
        total=total,
    )


@router.get(
    "/executions/{execution_id}",
    response_model=PlaybookExecutionReadSchema,
    responses={404: {"model": ErrorDetailResponse}},
    dependencies=[Depends(permission_dependency("interventions:view"))],
)
def get_execution(
    execution_id: int,
    tenant_id: Annotated[int, Depends(get_current_tenant)],
    db: Annotated[Session, Depends(get_interventions_db)],
) -> PlaybookExecutionReadSchema:
    try:
        execution = PlaybookService(db).get_execution(
            tenant_id=tenant_id, execution_id=execution_id
        )
    except Exception as exc:
        raise _raise(exc) from exc
    return PlaybookExecutionReadSchema.model_validate(execution)


@router.post(
    "/executions/{execution_id}/abandon",
    response_model=PlaybookExecutionReadSchema,
    responses=_common_errors,
    dependencies=[Depends(permission_dependency("interventions:execute_playbook"))],
)
def abandon_execution(
    execution_id: int,
    payload: Annotated[dict[str, Any], Body()],
    tenant_id: Annotated[int, Depends(get_current_tenant)],
    actor: Annotated[str, Depends(get_actor)],
    db: Annotated[Session, Depends(get_interventions_db)],
) -> PlaybookExecutionReadSchema:
    try:
        _ensure_playbooks_enabled(tenant_id)
        data = _parse(PlaybookExecutionAbandonSchema, payload)
        execution = PlaybookService(db).abandon_execution(
            tenant_id=tenant_id,
            execution_id=execution_id,
            actor=actor,
            reason=data.abandon_reason,
        )
        db.commit()
        db.refresh(execution)
    except Exception as exc:
        db.rollback()
        raise _raise(exc) from exc
    return PlaybookExecutionReadSchema.model_validate(execution)


# ---------------------------------------------------------------------------
# Step execution actions
# ---------------------------------------------------------------------------


@router.post(
    "/executions/{execution_id}/steps/{step_execution_id}/complete",
    response_model=PlaybookStepExecutionReadSchema,
    responses=_common_errors,
    dependencies=[Depends(permission_dependency("interventions:execute_playbook"))],
)
def complete_step(
    execution_id: int,
    step_execution_id: int,
    payload: Annotated[dict[str, Any], Body()],
    tenant_id: Annotated[int, Depends(get_current_tenant)],
    actor: Annotated[str, Depends(get_actor)],
    db: Annotated[Session, Depends(get_interventions_db)],
) -> PlaybookStepExecutionReadSchema:
    try:
        _ensure_playbooks_enabled(tenant_id)
        data = _parse(PlaybookStepCompleteSchema, payload)
        step_exec = PlaybookService(db).complete_step(
            tenant_id=tenant_id,
            execution_id=execution_id,
            step_execution_id=step_execution_id,
            actor=actor,
            payload=data,
        )
        db.commit()
        db.refresh(step_exec)
    except Exception as exc:
        db.rollback()
        raise _raise(exc) from exc
    return PlaybookStepExecutionReadSchema.model_validate(step_exec)


@router.post(
    "/executions/{execution_id}/steps/{step_execution_id}/skip",
    response_model=PlaybookStepExecutionReadSchema,
    responses=_common_errors,
    dependencies=[Depends(permission_dependency("interventions:execute_playbook"))],
)
def skip_step(
    execution_id: int,
    step_execution_id: int,
    payload: Annotated[dict[str, Any], Body()],
    tenant_id: Annotated[int, Depends(get_current_tenant)],
    actor: Annotated[str, Depends(get_actor)],
    db: Annotated[Session, Depends(get_interventions_db)],
) -> PlaybookStepExecutionReadSchema:
    try:
        _ensure_playbooks_enabled(tenant_id)
        data = _parse(PlaybookStepSkipSchema, payload)
        step_exec = PlaybookService(db).skip_step(
            tenant_id=tenant_id,
            execution_id=execution_id,
            step_execution_id=step_execution_id,
            actor=actor,
            payload=data,
        )
        db.commit()
        db.refresh(step_exec)
    except Exception as exc:
        db.rollback()
        raise _raise(exc) from exc
    return PlaybookStepExecutionReadSchema.model_validate(step_exec)
