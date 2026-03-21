from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.tenant import get_current_tenant
from app.modules.ai_gateway.schemas import AIModelEnabledPayload, AIModelUpsertPayload
from app.modules.ai_gateway.service import (
    list_models,
    list_provider_status,
    set_model_enabled,
    upsert_model,
    validate_provider_runtime,
)
from app.modules.audit.service import log_admin_action
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/ai", tags=["ai-gateway"])


@router.get("/providers")
def provider_status(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.providers.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, object]:
    return {"providers": list_provider_status(tenant_id=int(tenant["id"]))}


@router.post("/providers/{provider}/validate")
def validate_provider_key(
    provider: str,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.providers.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, object]:
    try:
        claims = getattr(request.state, "auth_claims", None)
        roles = [item.strip() for item in claims.roles if item.strip()] if claims else []
        result = validate_provider_runtime(provider, actor=actor, roles=roles, tenant_id=int(tenant["id"]))
    except ValueError as exc:
        detail = str(exc)
        log_admin_action(
            actor=actor,
            action="ai.providers.validate",
            path=str(request.url.path),
            client_ip=request.client.host if request.client else "unknown",
            correlation_id=getattr(request.state, "request_id", None),
            entity="ai_gateway",
            result="failed",
            metadata={"provider": provider, "reason": detail},
        )
        if "rate limit exceeded" in detail:
            raise HTTPException(status_code=429, detail=detail) from exc
        raise HTTPException(status_code=400, detail=detail) from exc

    log_admin_action(
        actor=actor,
        action="ai.providers.validate",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="ai_gateway",
        result="success",
        metadata={"provider": provider, "http_status": result.get("http_status")},
    )
    return {"result": result}


@router.get("/models")
def model_registry(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
) -> dict[str, object]:
    return {"models": list_models(include_disabled=True)}


@router.put("/models/{model_key}")
def upsert_model_endpoint(
    model_key: str,
    payload: AIModelUpsertPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
) -> dict[str, object]:
    try:
        model = upsert_model(
            model_key=model_key,
            provider=payload.provider,
            provider_model_id=payload.provider_model_id,
            display_name=payload.display_name,
            enabled=payload.enabled,
            priority=payload.priority,
            metadata=payload.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        action="ai.models.upsert",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="ai_gateway",
        result="success",
        metadata={
            "model_key": model.get("model_key"),
            "provider": model.get("provider"),
            "enabled": model.get("enabled"),
            "priority": model.get("priority"),
        },
    )
    return {"model": model}


@router.patch("/models/{model_key}/enabled")
def set_model_enabled_endpoint(
    model_key: str,
    payload: AIModelEnabledPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
) -> dict[str, object]:
    try:
        model = set_model_enabled(model_key, payload.enabled)
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        action="ai.models.set_enabled",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="ai_gateway",
        result="success",
        metadata={
            "model_key": model.get("model_key"),
            "enabled": model.get("enabled"),
        },
    )
    return {"model": model}
