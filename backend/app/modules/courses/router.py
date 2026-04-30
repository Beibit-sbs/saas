from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.modules.audit.service import log_admin_action
from app.modules.courses.schemas import (
    CourseConsistencyReportSchema,
    CourseCreatePayload,
    CourseDeleteResponse,
    CourseItemResponse,
    CourseListResponse,
    CourseUpdatePayload,
)
from app.modules.courses.service import (
    create_course,
    delete_course,
    get_course_consistency_report,
    get_courses_brain_context,
    list_courses,
    update_course,
)
from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/org/courses", tags=["org-courses"])


@router.get("", response_model=CourseListResponse)
def get_courses(
    request: Request,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.courses.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> CourseListResponse:
    return {"courses": list_courses(int(tenant["id"]))}


@router.get("/consistency", response_model=CourseConsistencyReportSchema)
def get_course_consistency_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.courses.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> CourseConsistencyReportSchema:
    return CourseConsistencyReportSchema.model_validate(
        get_course_consistency_report(int(tenant["id"]))
    )


@router.post("", response_model=CourseItemResponse)
def create_course_endpoint(
    payload: CourseCreatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.courses.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> CourseItemResponse:
    try:
        course = create_course(payload.model_dump(), int(tenant["id"]))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="university.courses.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_courses",
        result="success",
        metadata={"id": course["id"], "course_code": course["course_code"]},
    )
    return {"course": course}


@router.put("/{course_id}", response_model=CourseItemResponse)
def update_course_endpoint(
    course_id: int,
    payload: CourseUpdatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.courses.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> CourseItemResponse:
    try:
        course = update_course(course_id, payload.model_dump(), int(tenant["id"]))
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="university.courses.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_courses",
        result="success",
        metadata={"id": course["id"], "course_code": course["course_code"]},
    )
    return {"course": course}


@router.delete("/{course_id}", response_model=CourseDeleteResponse)
def delete_course_endpoint(
    course_id: int,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.courses.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> CourseDeleteResponse:
    try:
        course = delete_course(course_id, int(tenant["id"]))
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="university.courses.delete",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_courses",
        result="success",
        metadata={"id": course["id"], "course_code": course["course_code"]},
    )
    return {"deleted": True, "course": course}


@router.get("/brain-context", response_model=dict, tags=["org-courses", "brain-core"])
def get_courses_brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.courses.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Return aggregated brain-context snapshot for Brain Core context builder.

    Used by Brain Core to enrich decisions with courses signals:
    total courses, active courses, inconsistency count, risk level.
    """
    return get_courses_brain_context(int(tenant["id"]))
