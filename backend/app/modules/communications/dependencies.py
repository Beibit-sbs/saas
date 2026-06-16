"""Dependencies for Communications module."""

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.dependency_logging import log_dependency_unavailable
from app.core.tenant import get_current_tenant


def get_communications_db(request: Request) -> Generator[Session, None, None]:
    """Get communications DB session from configured app session factories."""
    session_factory = getattr(request.app.state, "academic_operations_session_factory", None)
    if session_factory is None:
        session_factory = getattr(request.app.state, "student_lifecycle_session_factory", None)
    if session_factory is None:
        session_factory = getattr(request.app.state, "admissions_session_factory", None)
    if session_factory is None:
        log_dependency_unavailable(
            request,
            dependency="communications_db_session",
            reason="communications session factory is not configured",
        )
        raise HTTPException(status_code=503, detail="communications database session is not configured")

    session = session_factory()
    try:
        yield session
    finally:
        close = getattr(session, "close", None)
        if callable(close):
            close()


async def require_communications_tenant(
    tenant: Annotated[dict, Depends(get_current_tenant)]
) -> int:
    """Require and return tenant ID for communications operations."""
    if not tenant or "id" not in tenant:
        raise HTTPException(status_code=403, detail="Tenant context required")
    try:
        return int(tenant["id"])
    except (TypeError, ValueError):
        raise HTTPException(status_code=403, detail="Invalid tenant context")
