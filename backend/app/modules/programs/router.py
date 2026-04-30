from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.modules.audit.service import log_admin_action
from app.modules.programs.schemas import (
    ProgramConsistencyReportSchema,
    ProgramCreatePayload,
    ProgramDeleteResponse,
    ProgramItemResponse,
    ProgramListResponse,
    ProgramUpdatePayload,
)
from app.modules.programs.service import (
    create_program,
    delete_program,
    get_program_consistency_report,
    get_programs_brain_context,
    list_programs,
    update_program,
)
from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/org/programs", tags=["org-programs"])


@router.get("", response_model=ProgramListResponse)
def get_programs(
    request: Request,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.programs.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ProgramListResponse:
    return {"programs": list_programs(int(tenant["id"]))}


@router.get("/consistency", response_model=ProgramConsistencyReportSchema)
def get_program_consistency_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.programs.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ProgramConsistencyReportSchema:
    return ProgramConsistencyReportSchema.model_validate(
        get_program_consistency_report(int(tenant["id"]))
    )


@router.post("", response_model=ProgramItemResponse)
def create_program_endpoint(
    payload: ProgramCreatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.programs.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ProgramItemResponse:
    try:
        program = create_program(payload.model_dump(), int(tenant["id"]))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="university.programs.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_programs",
        result="success",
        metadata={"id": program["id"], "program_code": program["program_code"]},
    )
    return {"program": program}


@router.put("/{program_id}", response_model=ProgramItemResponse)
def update_program_endpoint(
    program_id: int,
    payload: ProgramUpdatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.programs.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ProgramItemResponse:
    try:
        program = update_program(program_id, payload.model_dump(), int(tenant["id"]))
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="university.programs.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_programs",
        result="success",
        metadata={"id": program["id"], "program_code": program["program_code"]},
    )
    return {"program": program}


@router.delete("/{program_id}", response_model=ProgramDeleteResponse)
def delete_program_endpoint(
    program_id: int,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.programs.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ProgramDeleteResponse:
    try:
        program = delete_program(program_id, int(tenant["id"]))
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="university.programs.delete",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_programs",
        result="success",
        metadata={"id": program["id"], "program_code": program["program_code"]},
    )
    return {"deleted": True, "program": program}


@router.get("/brain-context", response_model=dict, tags=["org-programs", "brain-core"])
def get_programs_brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.programs.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Return aggregated brain-context snapshot for Brain Core context builder.

    Used by Brain Core to enrich decisions with programs signals:
    total programs, active programs, inconsistency count, risk level.
    """
    return get_programs_brain_context(int(tenant["id"]))
