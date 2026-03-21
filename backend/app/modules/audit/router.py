from __future__ import annotations

import csv
import io
import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.core.tenant import get_current_tenant
from app.modules.audit.service import list_admin_actions
from app.modules.rbac.service import is_platform_admin
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.tenants.service import get_tenant

router = APIRouter(prefix="/api/admin/audit", tags=["audit"])


@router.get("/events")
def get_audit_events(
    request: Request,
    actor_id: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.audit.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    actor: str | None = Query(default=None),
    action: str | None = Query(default=None),
    entity: str | None = Query(default=None),
    result: str | None = Query(default=None),
    correlation_id: str | None = Query(default=None),
    since: str | None = Query(default=None),
    tenant_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    claims = getattr(request.state, "auth_claims", None)
    claim_roles = {r.strip() for r in getattr(claims, "roles", []) if str(r).strip()}
    platform_admin = "superadmin" in claim_roles or is_platform_admin(actor_id)

    effective_tenant_id = int(tenant["id"])
    if tenant_id is not None:
        requested_tenant = get_tenant(tenant_id)
        if requested_tenant is None:
            raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
        if not platform_admin and int(tenant_id) != effective_tenant_id:
            raise HTTPException(status_code=404, detail="audit event not found")
        effective_tenant_id = int(tenant_id)

    events = list_admin_actions(
        actor=actor,
        action=action,
        entity=entity,
        result=result,
        correlation_id=correlation_id,
        since=since,
        limit=limit,
        tenant_id=effective_tenant_id,
    )
    return {"events": events}


@router.get("/export")
def export_audit_events(
    request: Request,
    actor_id: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.audit.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    format: str = Query(default="json"),
    actor: str | None = Query(default=None),
    action: str | None = Query(default=None),
    entity: str | None = Query(default=None),
    result: str | None = Query(default=None),
    correlation_id: str | None = Query(default=None),
    since: str | None = Query(default=None),
    tenant_id: int | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=500),
):
    claims = getattr(request.state, "auth_claims", None)
    claim_roles = {r.strip() for r in getattr(claims, "roles", []) if str(r).strip()}
    platform_admin = "superadmin" in claim_roles or is_platform_admin(actor_id)

    effective_tenant_id = int(tenant["id"])
    if tenant_id is not None:
        requested_tenant = get_tenant(tenant_id)
        if requested_tenant is None:
            raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
        if not platform_admin and int(tenant_id) != effective_tenant_id:
            raise HTTPException(status_code=404, detail="audit event not found")
        effective_tenant_id = int(tenant_id)

    events = list_admin_actions(
        actor=actor,
        action=action,
        entity=entity,
        result=result,
        correlation_id=correlation_id,
        since=since,
        limit=limit,
        tenant_id=effective_tenant_id,
    )
    normalized_format = format.strip().lower()

    if normalized_format == "json":
        payload = json.dumps({"events": events}, ensure_ascii=False, indent=2)
        return PlainTextResponse(
            content=payload,
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="audit-events.json"'},
        )

    if normalized_format == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["timestamp", "actor", "action", "entity", "path", "ip", "result", "correlation_id", "metadata"])
        for item in events:
            writer.writerow(
                [
                    item.get("timestamp", ""),
                    item.get("actor", ""),
                    item.get("action", ""),
                    item.get("entity", ""),
                    item.get("path", ""),
                    item.get("ip", item.get("client_ip", "")),
                    item.get("result", ""),
                    item.get("correlation_id", ""),
                    json.dumps(item.get("metadata", {}), ensure_ascii=False),
                ]
            )

        return PlainTextResponse(
            content=buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="audit-events.csv"'},
        )

    raise HTTPException(status_code=400, detail="format must be json or csv")
