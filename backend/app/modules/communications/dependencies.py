"""Dependencies for Communications module."""

from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.tenant import get_current_tenant


async def get_communications_db() -> Session:
    """Get database session for communications module."""
    db = get_db()
    try:
        yield db
    finally:
        db.close()


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
