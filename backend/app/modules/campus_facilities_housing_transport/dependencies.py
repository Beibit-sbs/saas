"""Dependencies for Campus / Facilities / Housing / Transport runtime."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import TenantRequiredError, validate_tenant_id_provided
from app.core.tenant import get_current_tenant


def require_campus_facilities_tenant(tenant: dict = Depends(get_current_tenant)) -> int:
    try:
        return validate_tenant_id_provided(tenant.get("id"))
    except TenantRequiredError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def get_campus_facilities_db(request: Request) -> Generator[Session, None, None]:
    session_factory = getattr(request.app.state, "admissions_session_factory", None)
    if session_factory is None:
        raise RuntimeError("Database session factory is not configured")
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
