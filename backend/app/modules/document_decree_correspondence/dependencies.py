"""Document / Decree / Correspondence dependency helpers."""

from __future__ import annotations

import time
from collections.abc import Generator

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.dependency_logging import log_dependency_unavailable
from app.core.module_helpers.service_validation import TenantRequiredError
from app.core.tenant import get_current_tenant
from app.modules.observability.perf_profile import perf_segment
from app.modules.rbac.security import permission_dependency


def get_document_decree_correspondence_db(request: Request) -> Generator[Session, None, None]:
    started = time.perf_counter()
    with perf_segment("db.session.open"):
        session_factory = getattr(request.app.state, "document_decree_correspondence_session_factory", None)
        if session_factory is None:
            session_factory = getattr(request.app.state, "finance_procurement_asset_session_factory", None)
        if session_factory is None:
            session_factory = getattr(request.app.state, "hr_staff_governance_session_factory", None)
        if session_factory is None:
            session_factory = getattr(request.app.state, "quality_accreditation_session_factory", None)
        if session_factory is None:
            session_factory = getattr(request.app.state, "research_science_session_factory", None)
        if session_factory is None:
            session_factory = getattr(request.app.state, "academic_operations_session_factory", None)
        if session_factory is None:
            session_factory = getattr(request.app.state, "student_lifecycle_session_factory", None)
        if session_factory is None:
            session_factory = getattr(request.app.state, "admissions_session_factory", None)
    if session_factory is None:
        log_dependency_unavailable(
            request,
            dependency="document_decree_correspondence_db_session",
            reason="document_decree_correspondence session factory is not configured",
            started_at=started,
        )
        raise HTTPException(status_code=503, detail="document_decree_correspondence database session is not configured")
    with perf_segment("db.session.create"):
        session = session_factory()
    try:
        yield session
    finally:
        close = getattr(session, "close", None)
        if callable(close):
            with perf_segment("db.session.close"):
                close()


def require_document_decree_correspondence_permission(permission: str):
    return Depends(permission_dependency(permission))


def validate_tenant_id(tenant_id) -> int:
    if isinstance(tenant_id, bool) or tenant_id is None:
        raise TenantRequiredError("tenant_id must be a positive integer")
    if not isinstance(tenant_id, int):
        raise TenantRequiredError("tenant_id must be a positive integer")
    if tenant_id <= 0:
        raise TenantRequiredError("tenant_id must be a positive integer")
    return tenant_id


def require_document_decree_correspondence_tenant(tenant: dict = Depends(get_current_tenant)) -> int:
    try:
        return validate_tenant_id(tenant.get("id"))
    except TenantRequiredError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
