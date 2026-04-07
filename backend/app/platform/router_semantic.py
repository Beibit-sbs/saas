from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request

from app.modules.audit.service import log_admin_action
from app.modules.rbac.security import resolve_current_user_claims
from app.modules.rbac.service import get_user_roles_for_tenant
from app.modules.tenants.service import get_tenant
from app.platform.billing import service as billing_service
from app.platform.semantic.schemas import (
    SemanticDimensionSchema,
    SemanticEntitySchema,
    SemanticInsightReadSchema,
    SemanticMetricSchema,
    SemanticQueryRequestSchema,
    SemanticQueryResponseSchema,
)
from app.platform.semantic import service as semantic_service
from app.platform.uow import UnitOfWork


router = APIRouter(prefix="/api/v2/semantic", tags=["semantic-layer"])


def _audit(request: Request, actor: str, action: str, tenant_id: int, metadata: dict[str, object] | None = None) -> None:
    log_admin_action(
        actor=actor,
        tenant_id=int(tenant_id),
        action=action,
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="semantic",
        result="success",
        metadata=metadata or {},
    )


def _resolve_semantic_access(
    request: Request,
    authorization: str | None,
    x_tenant_id: int | None,
) -> tuple[int, str, list[str]]:
    claims = resolve_current_user_claims(request, authorization)
    token_tenant_id = int(claims.tenant_id)
    if token_tenant_id <= 0:
        raise HTTPException(status_code=403, detail="invalid tenant context")

    if x_tenant_id is not None:
        if int(x_tenant_id) <= 0:
            raise HTTPException(status_code=400, detail="invalid tenant header")
        if int(x_tenant_id) != token_tenant_id:
            raise HTTPException(status_code=403, detail="cross-tenant override forbidden")

    tenant = get_tenant(token_tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail=f"Tenant {token_tenant_id} not found")
    if tenant.get("status") != "active":
        raise HTTPException(status_code=403, detail=f"Tenant {token_tenant_id} is not active")

    actor = str(claims.user_id)
    roles = list(get_user_roles_for_tenant(actor, token_tenant_id))
    if not roles:
        roles = [str(role).strip() for role in claims.roles if str(role).strip()]

    return token_tenant_id, actor, roles


@router.get("/entities", response_model=list[SemanticEntitySchema])
def get_semantic_entities(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_tenant_id: Annotated[int | None, Header(alias="X-Tenant-ID")] = None,
) -> list[SemanticEntitySchema]:
    tenant_id, actor, roles = _resolve_semantic_access(request, authorization, x_tenant_id)
    _ = semantic_service.build_semantic_scope(actor_id=actor, roles=roles)
    _audit(request, actor, "semantic.entities.list", tenant_id)
    return semantic_service.list_semantic_entities()


@router.get("/metrics", response_model=list[SemanticMetricSchema])
def get_semantic_metrics(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_tenant_id: Annotated[int | None, Header(alias="X-Tenant-ID")] = None,
) -> list[SemanticMetricSchema]:
    tenant_id, actor, roles = _resolve_semantic_access(request, authorization, x_tenant_id)
    _ = semantic_service.build_semantic_scope(actor_id=actor, roles=roles)
    _audit(request, actor, "semantic.metrics.list", tenant_id)
    return semantic_service.list_semantic_metrics()


@router.get("/dimensions", response_model=list[SemanticDimensionSchema])
def get_semantic_dimensions(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_tenant_id: Annotated[int | None, Header(alias="X-Tenant-ID")] = None,
) -> list[SemanticDimensionSchema]:
    tenant_id, actor, roles = _resolve_semantic_access(request, authorization, x_tenant_id)
    _ = semantic_service.build_semantic_scope(actor_id=actor, roles=roles)
    _audit(request, actor, "semantic.dimensions.list", tenant_id)
    return semantic_service.list_semantic_dimensions()


@router.post("/query", response_model=SemanticQueryResponseSchema)
def post_semantic_query(
    payload: SemanticQueryRequestSchema,
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_tenant_id: Annotated[int | None, Header(alias="X-Tenant-ID")] = None,
) -> SemanticQueryResponseSchema:
    tenant_id, actor, roles = _resolve_semantic_access(request, authorization, x_tenant_id)
    scope = semantic_service.build_semantic_scope(actor_id=actor, roles=roles)

    billing_service.assert_quota_with_increment(tenant_id, "analytics_queries", increment=1)

    with UnitOfWork() as uow:
        response = semantic_service.run_semantic_query(
            tenant_id=tenant_id,
            request=payload,
            scope=scope,
            uow=uow,
        )

    billing_service.increment_usage(tenant_id=tenant_id, metric="analytics_queries", value=1)
    _audit(
        request,
        actor,
        "semantic.query.run",
        tenant_id,
        {
            "entity": payload.entity,
            "metrics": payload.metrics,
            "dimensions": payload.dimensions,
        },
    )
    return response


@router.get("/scorecards", response_model=SemanticQueryResponseSchema)
def get_semantic_scorecards(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_tenant_id: Annotated[int | None, Header(alias="X-Tenant-ID")] = None,
) -> SemanticQueryResponseSchema:
    tenant_id, actor, roles = _resolve_semantic_access(request, authorization, x_tenant_id)
    scope = semantic_service.build_semantic_scope(actor_id=actor, roles=roles)

    with UnitOfWork() as uow:
        result = semantic_service.build_scorecard(tenant_id=tenant_id, uow=uow, scope=scope)

    _audit(request, actor, "semantic.scorecards.read", tenant_id)
    return result


@router.get("/insights", response_model=SemanticInsightReadSchema)
def get_semantic_insight(
    request: Request,
    entity: str,
    metric: str,
    authorization: Annotated[str | None, Header()] = None,
    x_tenant_id: Annotated[int | None, Header(alias="X-Tenant-ID")] = None,
) -> SemanticInsightReadSchema:
    tenant_id, actor, roles = _resolve_semantic_access(request, authorization, x_tenant_id)
    scope = semantic_service.build_semantic_scope(actor_id=actor, roles=roles)

    with UnitOfWork() as uow:
        insight = semantic_service.build_insight(
            tenant_id=tenant_id,
            entity=entity.strip().lower(),
            metric=metric.strip().lower(),
            scope=scope,
            uow=uow,
        )

    _audit(request, actor, "semantic.insight.read", tenant_id, {"entity": entity, "metric": metric})
    return insight
