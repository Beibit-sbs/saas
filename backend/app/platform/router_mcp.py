"""Internal MCP-style HTTP endpoints for AI copilot DB introspection.

These are internal-only endpoints (prefix /api/v1/internal/mcp) protected by
the same Bearer token used by all internal platform routes.  They enforce:
  - table whitelist (ALLOWED_TABLES)
  - PII column redaction
  - hard row-count cap (MAX_AGGREGATE_ROWS)

The endpoints are intentionally thin wrappers around ``app.platform.ai.db_tools``
and expose only safe, aggregate-level data to the AI layer.
"""
from __future__ import annotations

import hmac
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_internal_api_token
from app.platform.ai import db_tools
from app.platform.uow import UnitOfWork

router = APIRouter(prefix="/api/v1/internal/mcp", tags=["platform-mcp-internal"])


def _require_mcp_token(authorization: str | None) -> None:
    configured = get_internal_api_token()
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="internal token required")
    provided = authorization[len("Bearer "):].strip()
    if not hmac.compare_digest(provided.encode(), configured.encode()):
        raise HTTPException(status_code=403, detail="invalid internal token")


class AggregateRequest(BaseModel):
    group_by: list[str] = Field(default_factory=list)
    tenant_id: int | None = None
    limit: int = Field(default=50, ge=1, le=50)


@router.get("/schema", summary="List introspectable tables")
def get_schema(
    authorization: str | None = Header(default=None),
) -> list[dict[str, Any]]:
    """Return all tables the AI copilot is allowed to introspect."""
    _require_mcp_token(authorization)
    try:
        with UnitOfWork() as uow:
            return db_tools.list_tables(uow.conn)
    except Exception:  # noqa: BLE001
        return db_tools.list_tables(None)


@router.get("/schema/{table_name}", summary="Describe table columns")
def get_table_schema(
    table_name: str,
    authorization: str | None = Header(default=None),
) -> list[dict[str, Any]]:
    """Return column metadata for *table_name*.  PII columns are flagged as ``is_pii=true``."""
    _require_mcp_token(authorization)
    try:
        with UnitOfWork() as uow:
            return db_tools.describe_table(uow.conn, table_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception:  # noqa: BLE001
        try:
            return db_tools.describe_table(None, table_name)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/schema/{table_name}/query", summary="Aggregate query on a table")
def query_table_aggregate(
    table_name: str,
    body: AggregateRequest,
    authorization: str | None = Header(default=None),
) -> list[dict[str, Any]]:
    """Execute a ``COUNT(*) GROUP BY`` query.  No PII columns may appear in *group_by*."""
    _require_mcp_token(authorization)
    try:
        with UnitOfWork() as uow:
            return db_tools.query_aggregate(
                uow.conn,
                table_name=table_name,
                group_by=body.group_by,
                tenant_id=body.tenant_id,
                limit=body.limit,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:  # noqa: BLE001
        try:
            return db_tools.query_aggregate(
                None,
                table_name=table_name,
                group_by=body.group_by,
                tenant_id=body.tenant_id,
                limit=body.limit,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
