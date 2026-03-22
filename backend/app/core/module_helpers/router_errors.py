from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.core.module_helpers.service_validation import (
    OptimisticLockConflictError,
    TenantResourceNotFoundError,
)


def permission_error_to_http(exc: PermissionError) -> HTTPException:
    """Map permission failures to HTTP 403."""
    detail = str(exc).strip() or "forbidden"
    return HTTPException(status_code=403, detail=detail)


def tenant_not_found_to_http(exc: TenantResourceNotFoundError | ValueError) -> HTTPException:
    """Map tenant-scoped missing resources to HTTP 404."""
    detail = str(exc).strip() or "resource not found"
    return HTTPException(status_code=404, detail=detail)


def validation_error_to_http(exc: ValueError) -> HTTPException:
    """Map generic domain validation errors to HTTP 400."""
    detail = str(exc).strip() or "invalid request"
    return HTTPException(status_code=400, detail=detail)


def integrity_error_to_http(exc: IntegrityError | OptimisticLockConflictError) -> HTTPException:
    """Map DB/integrity and optimistic lock conflicts to HTTP 409."""
    if isinstance(exc, IntegrityError):
        return HTTPException(status_code=409, detail="resource conflict")
    detail = str(exc).strip() or "resource conflict"
    return HTTPException(status_code=409, detail=detail)
