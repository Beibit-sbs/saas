"""Security / Access / Compliance dependency helpers."""

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


def get_security_access_compliance_db(request: Request) -> Generator[Session, None, None]:
    started = time.perf_counter()
    with perf_segment("db.session.open"):
        session_factory = getattr(request.app.state, "admissions_session_factory", None)
    if session_factory is None:
        log_dependency_unavailable(
            request,
            dependency="security_access_compliance_db_session",
            reason="admissions session factory is not configured",
            started_at=started,
        )
        raise HTTPException(status_code=503, detail="security_access_compliance database session is not configured")

    with perf_segment("db.session.create"):
        session = session_factory()
    try:
        yield session
    finally:
        close = getattr(session, "close", None)
        if callable(close):
            with perf_segment("db.session.close"):
                close()


def require_security_access_compliance_permission(permission: str):
    return Depends(permission_dependency(permission))


def require_security_access_compliance_tenant(tenant: dict = Depends(get_current_tenant)) -> int:
    try:
        return validate_tenant_id_provided(tenant.get("id"))
    except TenantRequiredError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
