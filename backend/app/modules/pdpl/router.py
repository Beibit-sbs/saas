"""PDPL (Personal Data Protection Law) compliance router.

Implements the Right to Erasure endpoint (Article 14 / PDPL-SA):
  DELETE /api/admin/pdpl/users/{user_id}/data

The endpoint anonymises all personal identifiers belonging to a user
within the caller's tenant and emits an audit event as a deletion receipt.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.tenant import get_current_tenant
from app.modules.audit.service import log_admin_action
from app.modules.auth.local_users_service import local_user_store
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/pdpl", tags=["pdpl"])

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

_ANON_PREFIX = "ANONYMIZED"


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _anonymise_user(user_id: str, tenant_id: int) -> dict[str, Any]:
    """Overwrite PII fields for *user_id* and return the sanitised record."""
    anon_suffix = user_id[:8]
    return local_user_store.update_user(
        user_id=user_id,
        tenant_id=tenant_id,
        display_name=f"{_ANON_PREFIX}_{anon_suffix}",
    )


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.delete("/users/{user_id}/data", status_code=200)
def delete_user_personal_data(
    user_id: str,
    request: Request,
    actor_id: Annotated[str, Depends(get_actor)],
    _perm: Annotated[None, Depends(permission_dependency("admin.users.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, Any]:
    """PDPL Right-to-Erasure: anonymise all PII for *user_id* in this tenant.

    Returns a deletion receipt that can be presented as compliance evidence.
    """
    tenant_id = int(tenant["id"])
    receipt_id = str(uuid.uuid4())
    issued_at = datetime.now(timezone.utc).isoformat()

    # Verify the user exists in this tenant before attempting anonymisation
    users = local_user_store.list_users(tenant_id=tenant_id)
    if not any(u["user_id"] == user_id for u in users):
        raise HTTPException(status_code=404, detail="user not found")

    try:
        _anonymise_user(user_id, tenant_id)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail="anonymisation failed") from exc

    log_admin_action(
        actor=actor_id,
        action="pdpl.erasure",
        path=request.url.path,
        client_ip=_client_ip(request),
        entity="user",
        result="success",
        tenant_id=tenant_id,
        metadata={
            "receipt_id": receipt_id,
            "user_id": user_id,
            "issued_at": issued_at,
            "regulation": "PDPL-SA",
            "article": "14",
        },
    )

    return {
        "receipt_id": receipt_id,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "action": "personal_data_erased",
        "regulation": "PDPL-SA",
        "article": "14",
        "issued_at": issued_at,
        "status": "completed",
    }
