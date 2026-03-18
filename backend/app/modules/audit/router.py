from __future__ import annotations

import csv
import io
import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.modules.audit.service import list_admin_actions
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/audit", tags=["audit"])


@router.get("/events")
def get_audit_events(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.audit.read"))],
    actor: str | None = Query(default=None),
    action: str | None = Query(default=None),
    entity: str | None = Query(default=None),
    result: str | None = Query(default=None),
    correlation_id: str | None = Query(default=None),
    since: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    events = list_admin_actions(
        actor=actor,
        action=action,
        entity=entity,
        result=result,
        correlation_id=correlation_id,
        since=since,
        limit=limit,
    )
    return {"events": events}


@router.get("/export")
def export_audit_events(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.audit.read"))],
    format: str = Query(default="json"),
    actor: str | None = Query(default=None),
    action: str | None = Query(default=None),
    entity: str | None = Query(default=None),
    result: str | None = Query(default=None),
    correlation_id: str | None = Query(default=None),
    since: str | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=500),
):
    events = list_admin_actions(
        actor=actor,
        action=action,
        entity=entity,
        result=result,
        correlation_id=correlation_id,
        since=since,
        limit=limit,
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
