"""Dependency helpers for Integration Provider Readiness backend foundation."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.core.module_helpers.service_validation import TenantRequiredError, validate_tenant_id_provided
from app.modules.rbac.security import permission_dependency


def get_integration_provider_readiness_db(request: Request) -> Generator[Session, None, None]:
    session_factory = getattr(request.app.state, "integration_provider_readiness_session_factory", None)
    if session_factory is None:
        raise HTTPException(
            status_code=503,
            detail="integration_provider_readiness database session is not configured",
        )
    session = session_factory()
    try:
        yield session
    finally:
        close = getattr(session, "close", None)
        if callable(close):
            close()


def require_integration_provider_readiness_tenant(tenant: dict = Depends(get_current_tenant)) -> int:
    try:
        return validate_tenant_id_provided(tenant.get("id"))
    except TenantRequiredError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def require_integration_provider_readiness_permission(permission: str):
    return Depends(permission_dependency(permission))
