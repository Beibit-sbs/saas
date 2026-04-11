from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.tenant import get_current_tenant
from app.modules.audit.service import log_admin_action
from app.modules.faculty.schemas import (
    FacultyConsistencyReportSchema,
    FacultyCreatePayload,
    FacultyDeleteResponse,
    FacultyItemResponse,
    FacultyListResponse,
    FacultyUpdatePayload,
)
from app.modules.faculty.service import (
    create_faculty_member,
    delete_faculty_member,
    get_faculty_consistency_report,
    list_faculty,
    update_faculty_member,
)
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/org/faculty", tags=["org-faculty"])


@router.get("", response_model=FacultyListResponse)
def get_faculty(
    request: Request,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FacultyListResponse:
    return {"faculty": list_faculty(int(tenant["id"]))}


@router.get("/consistency", response_model=FacultyConsistencyReportSchema)
def get_faculty_consistency_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FacultyConsistencyReportSchema:
    return FacultyConsistencyReportSchema.model_validate(
        get_faculty_consistency_report(int(tenant["id"]))
    )


@router.post("", response_model=FacultyItemResponse)
def create_faculty_endpoint(
    payload: FacultyCreatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.faculty.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FacultyItemResponse:
    try:
        faculty_entry = create_faculty_member(payload.model_dump(), int(tenant["id"]))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="university.faculty.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_faculty",
        result="success",
        metadata={"id": faculty_entry["id"], "faculty_id": faculty_entry["faculty_id"]},
    )
    return {"faculty": faculty_entry}


@router.put("/{faculty_row_id}", response_model=FacultyItemResponse)
def update_faculty_endpoint(
    faculty_row_id: int,
    payload: FacultyUpdatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.faculty.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FacultyItemResponse:
    try:
        faculty_entry = update_faculty_member(faculty_row_id, payload.model_dump(), int(tenant["id"]))
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="university.faculty.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_faculty",
        result="success",
        metadata={"id": faculty_entry["id"], "faculty_id": faculty_entry["faculty_id"]},
    )
    return {"faculty": faculty_entry}


@router.delete("/{faculty_row_id}", response_model=FacultyDeleteResponse)
def delete_faculty_endpoint(
    faculty_row_id: int,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.faculty.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FacultyDeleteResponse:
    try:
        faculty_entry = delete_faculty_member(faculty_row_id, int(tenant["id"]))
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="university.faculty.delete",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_faculty",
        result="success",
        metadata={"id": faculty_entry["id"], "faculty_id": faculty_entry["faculty_id"]},
    )
    return {"deleted": True, "faculty": faculty_entry}
