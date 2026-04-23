"""Phase XII-XII3: Prompt Management router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.tenant import get_current_tenant
from app.modules.prompt_management.schemas import (
    ABTestResultSchema,
    ABTestRouteSchema,
    PromptTemplateCreateSchema,
    PromptTemplateReadSchema,
    PromptTemplateUpdateSchema,
)
from app.modules.prompt_management.service import (
    create_template,
    list_templates,
    route_ab_test,
    update_template,
)
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/prompt-management", tags=["prompt-management"])


@router.get("/health")
def health_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("prompt_management.read"))],
) -> dict[str, str]:
    return {"status": "ok", "module": "prompt_management", "phase": "xii3"}


@router.post("/templates", response_model=PromptTemplateReadSchema, status_code=201)
def create_template_endpoint(
    payload: PromptTemplateCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("prompt_management.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> PromptTemplateReadSchema:
    return create_template(
        tenant_id=int(tenant["id"]),
        actor_id=actor,
        payload=payload,
    )


@router.get("/templates", response_model=list[PromptTemplateReadSchema])
def list_templates_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("prompt_management.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    category: str | None = None,
    active_only: bool = False,
) -> list[PromptTemplateReadSchema]:
    return list_templates(
        tenant_id=int(tenant["id"]),
        category=category,
        active_only=active_only,
    )


@router.patch("/templates/{template_id}", response_model=PromptTemplateReadSchema)
def update_template_endpoint(
    template_id: str,
    payload: PromptTemplateUpdateSchema,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("prompt_management.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> PromptTemplateReadSchema:
    result = update_template(
        tenant_id=int(tenant["id"]),
        template_id=template_id,
        payload=payload,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return result


@router.post("/ab-test/route", response_model=ABTestResultSchema)
def ab_route_endpoint(
    payload: ABTestRouteSchema,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("prompt_management.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ABTestResultSchema:
    return route_ab_test(
        tenant_id=int(tenant["id"]),
        payload=payload,
    )
