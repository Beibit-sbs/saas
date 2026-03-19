from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.tenant import get_current_tenant
from app.modules.audit.service import log_admin_action
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.students.schemas import (
    StudentCreatePayload,
    StudentDeleteResponse,
    StudentItemResponse,
    StudentListResponse,
    StudentUpdatePayload,
)
from app.modules.students.service import create_student, delete_student, list_students, update_student

router = APIRouter(prefix="/api/admin/university/students", tags=["university-students"])


@router.get("", response_model=StudentListResponse)
def get_students(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.students.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> StudentListResponse:
    return {"students": list_students(int(tenant["id"]))}


@router.post("", response_model=StudentItemResponse)
def create_student_endpoint(
    payload: StudentCreatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.students.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> StudentItemResponse:
    try:
        student = create_student(payload.model_dump(), int(tenant["id"]))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        action="university.students.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_students",
        result="success",
        metadata={"id": student["id"], "student_id": student["student_id"]},
    )
    return {"student": student}


@router.put("/{student_id}", response_model=StudentItemResponse)
def update_student_endpoint(
    student_id: int,
    payload: StudentUpdatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.students.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> StudentItemResponse:
    try:
        student = update_student(student_id, payload.model_dump(), int(tenant["id"]))
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        action="university.students.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_students",
        result="success",
        metadata={"id": student["id"], "student_id": student["student_id"]},
    )
    return {"student": student}


@router.delete("/{student_id}", response_model=StudentDeleteResponse)
def delete_student_endpoint(
    student_id: int,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.students.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> StudentDeleteResponse:
    try:
        student = delete_student(student_id, int(tenant["id"]))
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        action="university.students.delete",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_students",
        result="success",
        metadata={"id": student["id"], "student_id": student["student_id"]},
    )
    return {"deleted": True, "student": student}
