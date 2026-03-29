"""Developer/Partner Integration API - Separate Trust Zone.

This router handles third-party integrations with app credentials (X-App-Key/X-App-Secret).
NOT part of public API; requires explicit developer registration and scope validation.

Prefix: /api/dev (separate from /api/v1/public)
Auth: X-App-Key + X-App-Secret (developer credentials)
Tenant: Extracted from app_key (NOT from URL, headers, or body)
"""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Request

from app.platform.developer.auth import require_developer_scope
from app.platform.developer import service as developer_service
from app.platform.developer.schemas import PublicEnrollmentReadSchema, PublicGradeReadSchema, PublicStudentReadSchema
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork
from app.modules.students import service as students_service
from app.modules.enrollments import service as enrollments_service


# ============================================================================
# Developer/Partner API Router (Enterprise integrations)
# Requires X-App-Key + X-App-Secret in request headers
# ============================================================================

router = APIRouter(
    prefix="/api/dev",
    tags=["developer-api"],
    responses={
        401: {"description": "Invalid or missing app credentials"},
        403: {"description": "Insufficient scope or unauthorized"},
        429: {"description": "Rate limit exceeded"},
    },
)


def _student_row(item: dict[str, object]) -> dict[str, object]:
    """Transform student record for API response."""
    return {
        "id": int(item.get("id", 0)),
        "tenant_id": item.get("tenant_id"),
        "student_id": item.get("student_id"),
        "first_name": item.get("first_name"),
        "last_name": item.get("last_name"),
        "email": item.get("email"),
        "status": item.get("status"),
        "payload": dict(item),
    }


def _enrollment_row(item: dict[str, object]) -> dict[str, object]:
    """Transform enrollment record for API response."""
    return {
        "id": int(item.get("id", 0)),
        "tenant_id": item.get("tenant_id"),
        "student_id": item.get("student_id"),
        "course_id": item.get("course_id"),
        "semester": item.get("semester"),
        "status": item.get("status"),
        "payload": dict(item),
    }


@router.get(
    "/students",
    response_model=list[PublicStudentReadSchema],
    summary="List students",
    description="List students for authenticated tenant. Developer scope required.",
)
def list_developer_students(
    request: Request,
    auth: dict[str, object] = Depends(require_developer_scope("students.read")),
) -> list[PublicStudentReadSchema]:
    """Get list of students for tenant.

    Security:
    - Requires X-App-Key + X-App-Secret headers
    - Requires 'students.read' scope
    - Tenant determined from app_key (not URL, headers, or body)
    - Rate limited per app_id

    Returns:
    - List of student records (no cross-tenant data)
    - 401 if credentials invalid
    - 403 if scope insufficient
    - 429 if rate limit exceeded
    """
    started = time.monotonic()
    status_code = 200
    try:
        tenant_id = int(auth["tenant_id"])
        app_id = int(auth["app_id"])

        rows = students_service.list_students(tenant_id)
        return [PublicStudentReadSchema.model_validate(_student_row(item)) for item in rows]
    except Exception:
        status_code = 500
        raise
    finally:
        # Log API usage for rate limiting and audit
        developer_service.developer_service.log_api_usage(
            app_id=app_id,
            tenant_id=tenant_id,
            endpoint=str(request.url.path),
            status_code=status_code,
            latency_ms=round((time.monotonic() - started) * 1000, 2),
        )


@router.get(
    "/enrollments",
    response_model=list[PublicEnrollmentReadSchema],
    summary="List enrollments",
    description="List course enrollments for authenticated tenant.",
)
def list_developer_enrollments(
    request: Request,
    auth: dict[str, object] = Depends(require_developer_scope("enrollments.read")),
) -> list[PublicEnrollmentReadSchema]:
    """Get list of enrollments for tenant.

    Security:
    - Requires X-App-Key + X-App-Secret headers
    - Requires 'enrollments.read' scope
    - Tenant determined from app_key (not URL, headers, or body)
    - Rate limited per app_id

    Returns:
    - List of enrollment records (no cross-tenant data)
    """
    started = time.monotonic()
    status_code = 200
    try:
        tenant_id = int(auth["tenant_id"])
        app_id = int(auth["app_id"])

        rows = enrollments_service.list_enrollments(tenant_id)
        return [PublicEnrollmentReadSchema.model_validate(_enrollment_row(item)) for item in rows]
    except Exception:
        status_code = 500
        raise
    finally:
        developer_service.developer_service.log_api_usage(
            app_id=app_id,
            tenant_id=tenant_id,
            endpoint=str(request.url.path),
            status_code=status_code,
            latency_ms=round((time.monotonic() - started) * 1000, 2),
        )


@router.get(
    "/grades",
    response_model=list[PublicGradeReadSchema],
    summary="List grades",
    description="List student grades for authenticated tenant.",
)
def list_developer_grades(
    request: Request,
    auth: dict[str, object] = Depends(require_developer_scope("grades.read")),
) -> list[PublicGradeReadSchema]:
    """Get list of grades for tenant.

    Security:
    - Requires X-App-Key + X-App-Secret headers
    - Requires 'grades.read' scope
    - Tenant determined from app_key
    - Rate limited per app_id
    """
    started = time.monotonic()
    status_code = 200
    try:
        tenant_id = int(auth["tenant_id"])
        app_id = int(auth["app_id"])

        rows = developer_service.developer_service.list_public_grades(
            session_factory=getattr(request.app.state, "admissions_session_factory", None),
            tenant_id=tenant_id,
        )
        return [PublicGradeReadSchema.model_validate(item) for item in rows]
    except Exception:
        status_code = 500
        raise
    finally:
        developer_service.developer_service.log_api_usage(
            app_id=app_id,
            tenant_id=tenant_id,
            endpoint=str(request.url.path),
            status_code=status_code,
            latency_ms=round((time.monotonic() - started) * 1000, 2),
        )


@router.get(
    "/analytics/kpi",
    response_model=dict,
    summary="Get KPI analytics",
    description="Get KPI dashboard data for authenticated tenant.",
)
def get_developer_kpi(
    request: Request,
    auth: dict[str, object] = Depends(require_developer_scope("analytics.read")),
) -> dict[str, object]:
    """Get KPI analytics dashboard for tenant.

    Security:
    - Requires X-App-Key + X-App-Secret headers
    - Requires 'analytics.read' scope
    - Tenant determined from app_key
    - Rate limited per app_id

    Returns:
    - KPI metrics (no cross-tenant data)
    - 401 if credentials invalid
    - 403 if scope insufficient
    """
    started = time.monotonic()
    status_code = 200
    try:
        tenant_id = int(auth["tenant_id"])
        app_id = int(auth["app_id"])

        with UnitOfWork() as uow:
            return kpi_service.get_rector_dashboard(tenant_id=tenant_id, uow=uow)
    except Exception:
        status_code = 500
        raise
    finally:
        developer_service.developer_service.log_api_usage(
            app_id=app_id,
            tenant_id=tenant_id,
            endpoint=str(request.url.path),
            status_code=status_code,
            latency_ms=round((time.monotonic() - started) * 1000, 2),
        )
