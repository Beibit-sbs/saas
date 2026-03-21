from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.modules.audit.service import log_admin_action
from app.modules.enrollments.schemas import (
    EnrollmentCreatePayload,
    EnrollmentDeleteResponse,
    EnrollmentItemResponse,
    EnrollmentListResponse,
    EnrollmentUpdatePayload,
)
from app.modules.enrollments.service import create_enrollment, delete_enrollment, list_enrollments, update_enrollment
from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/university/enrollments", tags=["university-enrollments"])


@router.get("", response_model=EnrollmentListResponse)
def get_enrollments(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.enrollments.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> EnrollmentListResponse:
    return {"enrollments": list_enrollments(int(tenant["id"]))}


@router.post("", response_model=EnrollmentItemResponse)
def create_enrollment_endpoint(
    payload: EnrollmentCreatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.enrollments.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> EnrollmentItemResponse:
    try:
        enrollment = create_enrollment(payload.model_dump(), int(tenant["id"]))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="university.enrollments.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_enrollments",
        result="success",
        metadata={"id": enrollment["id"], "student_id": enrollment["student_id"], "course_id": enrollment["course_id"]},
    )
    return {"enrollment": enrollment}


@router.put("/{enrollment_id}", response_model=EnrollmentItemResponse)
def update_enrollment_endpoint(
    enrollment_id: int,
    payload: EnrollmentUpdatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.enrollments.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> EnrollmentItemResponse:
    try:
        enrollment = update_enrollment(enrollment_id, payload.model_dump(), int(tenant["id"]))
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="university.enrollments.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_enrollments",
        result="success",
        metadata={"id": enrollment["id"], "student_id": enrollment["student_id"], "course_id": enrollment["course_id"]},
    )
    return {"enrollment": enrollment}


@router.delete("/{enrollment_id}", response_model=EnrollmentDeleteResponse)
def delete_enrollment_endpoint(
    enrollment_id: int,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.enrollments.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> EnrollmentDeleteResponse:
    try:
        enrollment = delete_enrollment(enrollment_id, int(tenant["id"]))
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="university.enrollments.delete",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_enrollments",
        result="success",
        metadata={"id": enrollment["id"], "student_id": enrollment["student_id"], "course_id": enrollment["course_id"]},
    )
    return {"deleted": True, "enrollment": enrollment}
