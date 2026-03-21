from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.tenant import get_current_tenant
from app.modules.audit.service import log_admin_action
from app.modules.example_slice.service import list_reference_items
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/example-slice", tags=["example-slice"])

# Example-only reference route.
# This module demonstrates namespacing, RBAC guarding, and audit wiring only.
# It is intentionally removable in derived projects and is not a full domain CRUD reference.


@router.get("/reference-items")
def get_reference_items(
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, object]:
    tenant_id = int(tenant["id"])
    items = list_reference_items()
    log_admin_action(
        actor=actor,
        action="example_slice.read",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="example_slice",
        result="success",
        tenant_id=tenant_id,
        metadata={"items_count": len(items)},
    )
    return {
        "items": items,
        "note": "Template example vertical slice. Keep namespaced as example_* in derived projects.",
    }
