"""Student Services / Welfare / Support dependency helpers."""

from __future__ import annotations

import time
from collections.abc import Generator

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.dependency_logging import log_dependency_unavailable
from app.core.module_helpers.service_validation import TenantRequiredError, validate_tenant_id_provided
from app.core.tenant import get_current_tenant
from app.modules.observability.perf_profile import perf_segment
from app.modules.rbac.security import permission_dependency


def get_student_services_support_db(request: Request) -> Generator[Session, None, None]:
    started = time.perf_counter()
    with perf_segment("db.session.open"):
        session_factory = getattr(request.app.state, "student_services_support_session_factory", None)
        if session_factory is None:
            session_factory = getattr(request.app.state, "admissions_session_factory", None)
    if session_factory is None:
        log_dependency_unavailable(
            request,
            dependency="student_services_support_db_session",
            reason="student_services_support session factory is not configured",
            started_at=started,
        )
        raise HTTPException(status_code=503, detail="student_services_support database session is not configured")
    with perf_segment("db.session.create"):
        session = session_factory()
    try:
        yield session
    finally:
        close = getattr(session, "close", None)
        if callable(close):
            with perf_segment("db.session.close"):
                close()


def require_student_services_support_permission(permission: str):
    return Depends(permission_dependency(permission))


def require_student_services_support_tenant(tenant: dict = Depends(get_current_tenant)) -> int:
    try:
        return validate_tenant_id_provided(tenant.get("id"))
    except TenantRequiredError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
