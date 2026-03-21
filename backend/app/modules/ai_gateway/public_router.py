from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.tenant import get_current_tenant
from app.modules.ai_gateway.schemas import AIChatRequestPayload
from app.modules.ai_gateway.service import AIGatewayError, execute_chat
from app.modules.audit.service import log_admin_action
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/ai", tags=["ai-gateway"])


@router.post("/chat")
def chat(
    payload: AIChatRequestPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
    __: Annotated[None, Depends(permission_dependency("ai.chat.execute"))],
) -> dict[str, object]:
    claims = getattr(request.state, "auth_claims", None)
    roles = [item.strip() for item in claims.roles if item.strip()] if claims else []
    tenant_id = int(current_tenant.get("id"))

    try:
        result = execute_chat(
            payload.model_dump(),
            actor=actor,
            roles=roles,
            tenant_id=tenant_id,
            correlation_id=getattr(request.state, "request_id", None),
        )
        log_admin_action(
            actor=actor,
            action="ai.chat.execute",
            path=str(request.url.path),
            client_ip=request.client.host if request.client else "unknown",
            correlation_id=getattr(request.state, "request_id", None),
            entity="ai_gateway",
            result="success",
            tenant_id=tenant_id,
            metadata={
                "model": result.get("model"),
                "provider": result.get("provider"),
            },
        )
        return {"result": result}
    except AIGatewayError as exc:
        log_admin_action(
            actor=actor,
            action="ai.chat.execute",
            path=str(request.url.path),
            client_ip=request.client.host if request.client else "unknown",
            correlation_id=getattr(request.state, "request_id", None),
            entity="ai_gateway",
            result="failed",
            tenant_id=tenant_id,
            metadata={
                "provider": exc.provider,
                "model": exc.model,
                "reason": exc.audit_reason,
                "status_code": exc.status_code,
            },
        )
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
