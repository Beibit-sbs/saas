from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Request

from app.platform.billing import service as billing_service
from app.platform.developer.auth import require_developer_scope
from app.platform.developer import service as developer_service
from app.platform.developer.schemas import PublicEnrollmentReadSchema, PublicGradeReadSchema, PublicStudentReadSchema
from app.platform.feature_flags import service as flags_service
from app.platform.schemas import FeatureFlagRead, SubscriptionRead, TenantPlatformRead
from app.platform.tenant import service as tenant_service
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork
from app.modules.students import service as students_service
from app.modules.enrollments import service as enrollments_service

router = APIRouter(prefix="/api/v1/public", tags=["platform-core-public"])


@router.get("/tenants/{tenant_id}", response_model=TenantPlatformRead)
def get_tenant_public(tenant_id: int) -> TenantPlatformRead:
    row = tenant_service.get_tenant_profile(tenant_id)
    return TenantPlatformRead.model_validate(row)


@router.get("/tenants/{tenant_id}/features", response_model=list[FeatureFlagRead])
def get_tenant_features(tenant_id: int) -> list[FeatureFlagRead]:
    return [FeatureFlagRead.model_validate(item) for item in flags_service.list_tenant_features(tenant_id)]


@router.get("/tenants/{tenant_id}/subscription", response_model=SubscriptionRead | None)
def get_subscription(tenant_id: int) -> SubscriptionRead | None:
    row = billing_service.get_subscription(tenant_id)
    if row is None:
        return None
    return SubscriptionRead.model_validate(row)


def _public_student_row(item: dict[str, object]) -> dict[str, object]:
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


def _public_enrollment_row(item: dict[str, object]) -> dict[str, object]:
    return {
        "id": int(item.get("id", 0)),
        "tenant_id": item.get("tenant_id"),
        "student_id": item.get("student_id"),
        "course_id": item.get("course_id"),
        "semester": item.get("semester"),
        "status": item.get("status"),
        "payload": dict(item),
    }


@router.get("/students", response_model=list[PublicStudentReadSchema])
def list_public_students(
    request: Request,
    auth: dict[str, object] = Depends(require_developer_scope("students.read")),
) -> list[PublicStudentReadSchema]:
    started = time.monotonic()
    status_code = 200
    try:
        rows = students_service.list_students(int(auth["tenant_id"]))
        return [PublicStudentReadSchema.model_validate(_public_student_row(item)) for item in rows]
    except Exception:
        status_code = 500
        raise
    finally:
        developer_service.developer_service.log_api_usage(
            app_id=int(auth["app_id"]),
            tenant_id=int(auth["tenant_id"]),
            endpoint=str(request.url.path),
            status_code=status_code,
            latency_ms=round((time.monotonic() - started) * 1000, 2),
        )


@router.get("/enrollments", response_model=list[PublicEnrollmentReadSchema])
def list_public_enrollments(
    request: Request,
    auth: dict[str, object] = Depends(require_developer_scope("enrollments.read")),
) -> list[PublicEnrollmentReadSchema]:
    started = time.monotonic()
    status_code = 200
    try:
        rows = enrollments_service.list_enrollments(int(auth["tenant_id"]))
        return [PublicEnrollmentReadSchema.model_validate(_public_enrollment_row(item)) for item in rows]
    except Exception:
        status_code = 500
        raise
    finally:
        developer_service.developer_service.log_api_usage(
            app_id=int(auth["app_id"]),
            tenant_id=int(auth["tenant_id"]),
            endpoint=str(request.url.path),
            status_code=status_code,
            latency_ms=round((time.monotonic() - started) * 1000, 2),
        )


@router.get("/grades", response_model=list[PublicGradeReadSchema])
def list_public_grades(
    request: Request,
    auth: dict[str, object] = Depends(require_developer_scope("grades.read")),
) -> list[PublicGradeReadSchema]:
    started = time.monotonic()
    status_code = 200
    try:
        rows = developer_service.developer_service.list_public_grades(
            session_factory=getattr(request.app.state, "admissions_session_factory", None),
            tenant_id=int(auth["tenant_id"]),
        )
        return [PublicGradeReadSchema.model_validate(item) for item in rows]
    except Exception:
        status_code = 500
        raise
    finally:
        developer_service.developer_service.log_api_usage(
            app_id=int(auth["app_id"]),
            tenant_id=int(auth["tenant_id"]),
            endpoint=str(request.url.path),
            status_code=status_code,
            latency_ms=round((time.monotonic() - started) * 1000, 2),
        )


@router.get("/analytics/kpi")
def get_public_kpi(
    request: Request,
    auth: dict[str, object] = Depends(require_developer_scope("analytics.read")),
) -> dict[str, object]:
    started = time.monotonic()
    status_code = 200
    try:
        with UnitOfWork() as uow:
            return kpi_service.get_rector_dashboard(tenant_id=int(auth["tenant_id"]), uow=uow)
    except Exception:
        status_code = 500
        raise
    finally:
        developer_service.developer_service.log_api_usage(
            app_id=int(auth["app_id"]),
            tenant_id=int(auth["tenant_id"]),
            endpoint=str(request.url.path),
            status_code=status_code,
            latency_ms=round((time.monotonic() - started) * 1000, 2),
        )
