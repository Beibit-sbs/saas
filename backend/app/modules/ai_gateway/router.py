from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.core.tenant import get_current_tenant
from app.modules.ai_gateway.schemas import AIModelEnabledPayload, AIModelUpsertPayload
from app.modules.ai_gateway.service import (
    create_routing_policy,
    delete_routing_policy,
    list_routing_selection_log,
    list_slo_compliance,
    list_slo_violations,
    list_slo_policies,
    list_usage_cost_anomalies,
    list_usage_cost_daily_aggregation,
    list_usage_token_prices,
    list_models,
    list_provider_status,
    list_routing_policies,
    summarize_usage_cost_projection,
    summarize_usage_cost_trend,
    refresh_usage_cost_daily_aggregation,
    summarize_usage_cost_by_department,
    summarize_usage_cost_by_user,
    summarize_usage_cost,
    get_usage_budget,
    list_usage_budgets,
    list_usage_budget_status,
    set_model_enabled,
    delete_usage_budget_scoped,
    upsert_usage_budget_scoped,
    upsert_usage_token_price,
    upsert_slo_policy,
    update_usage_budget,
    update_routing_policy,
    upsert_model,
    validate_provider_runtime,
    upsert_ai_safety_policy,
    list_ai_safety_policies,
)
from app.modules.ai_gateway.schemas import (
    AISLOComplianceSchema,
    AISLOPolicyPayload,
    AISLOPolicySchema,
    AISLOViolationSchema,
    AIUsageTokenPricePayload,
    AIUsageTokenPriceSchema,
    AIUsageCostAnomalySchema,
    AIUsageCostDailyAggregateSchema,
    AIUsageCostProjectionSchema,
    AIUsageCostTrendPointSchema,
    AIUsageCostByDepartmentSchema,
    AIUsageCostByUserSchema,
    AIUsageBudgetScopedPayload,
    AIUsageBudgetScopedReadSchema,
    AIUsageBudgetStatusSchema,
    AIUsageBudgetPayload,
    AIUsageBudgetReadSchema,
    AIUsageCostSummarySchema,
    AIRoutingPolicyPayload,
    AIRoutingPolicyReadSchema,
    AISafetyPolicyPayload,
    AISafetyPolicySchema,
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
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, object]:
    return {"models": list_models(include_disabled=True, tenant_id=int(tenant["id"]))}


@router.put("/models/{model_key}")
def upsert_model_endpoint(
    model_key: str,
    payload: AIModelUpsertPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
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
            tenant_id=int(tenant["id"]),
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
        tenant_id=int(tenant["id"]),
    )
    return {"model": model}


@router.patch("/models/{model_key}/enabled")
def set_model_enabled_endpoint(
    model_key: str,
    payload: AIModelEnabledPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, object]:
    try:
        model = set_model_enabled(model_key, payload.enabled, tenant_id=int(tenant["id"]))
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
        tenant_id=int(tenant["id"]),
    )
    return {"model": model}


@router.get("/usage/summary", response_model=AIUsageCostSummarySchema)
def usage_cost_summary_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    limit: Annotated[int, Query(ge=1, le=5000)] = 500,
) -> AIUsageCostSummarySchema:
    summary = summarize_usage_cost(tenant_id=int(tenant["id"]), limit=int(limit))
    return AIUsageCostSummarySchema.model_validate(summary)


@router.get("/usage/by-user", response_model=list[AIUsageCostByUserSchema])
def usage_cost_by_user_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    limit: Annotated[int, Query(ge=1, le=5000)] = 500,
) -> list[AIUsageCostByUserSchema]:
    rows = summarize_usage_cost_by_user(tenant_id=int(tenant["id"]), limit=int(limit))
    return [AIUsageCostByUserSchema.model_validate(item) for item in rows]


@router.get("/usage/by-department", response_model=list[AIUsageCostByDepartmentSchema])
def usage_cost_by_department_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    limit: Annotated[int, Query(ge=1, le=5000)] = 500,
) -> list[AIUsageCostByDepartmentSchema]:
    rows = summarize_usage_cost_by_department(tenant_id=int(tenant["id"]), limit=int(limit))
    return [AIUsageCostByDepartmentSchema.model_validate(item) for item in rows]


@router.get("/usage/trend", response_model=list[AIUsageCostTrendPointSchema])
def usage_cost_trend_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> list[AIUsageCostTrendPointSchema]:
    rows = summarize_usage_cost_trend(tenant_id=int(tenant["id"]), days=int(days))
    return [AIUsageCostTrendPointSchema.model_validate(item) for item in rows]


@router.post("/usage/daily-aggregation/refresh", response_model=list[AIUsageCostDailyAggregateSchema])
def refresh_usage_cost_daily_aggregation_endpoint(
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    days: Annotated[int, Query(ge=1, le=365)] = 30,
    limit: Annotated[int, Query(ge=1, le=5000)] = 5000,
) -> list[AIUsageCostDailyAggregateSchema]:
    rows = refresh_usage_cost_daily_aggregation(
        tenant_id=int(tenant["id"]),
        days=int(days),
        limit=int(limit),
    )

    log_admin_action(
        actor=actor,
        action="ai.usage.daily_aggregation.refresh",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="ai_gateway",
        result="success",
        metadata={"days": int(days), "rows": len(rows)},
        tenant_id=int(tenant["id"]),
    )
    return [AIUsageCostDailyAggregateSchema.model_validate(item) for item in rows]


@router.get("/usage/daily-aggregation", response_model=list[AIUsageCostDailyAggregateSchema])
def list_usage_cost_daily_aggregation_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> list[AIUsageCostDailyAggregateSchema]:
    rows = list_usage_cost_daily_aggregation(tenant_id=int(tenant["id"]), days=int(days))
    return [AIUsageCostDailyAggregateSchema.model_validate(item) for item in rows]


@router.get("/usage/projection", response_model=AIUsageCostProjectionSchema)
def usage_cost_projection_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AIUsageCostProjectionSchema:
    projection = summarize_usage_cost_projection(tenant_id=int(tenant["id"]))
    return AIUsageCostProjectionSchema.model_validate(projection)


@router.get("/usage/anomalies", response_model=list[AIUsageCostAnomalySchema])
def usage_cost_anomalies_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    limit: Annotated[int, Query(ge=1, le=200)] = 20,
) -> list[AIUsageCostAnomalySchema]:
    rows = list_usage_cost_anomalies(tenant_id=int(tenant["id"]), limit=int(limit))
    return [AIUsageCostAnomalySchema.model_validate(item) for item in rows]


@router.get("/prices", response_model=list[AIUsageTokenPriceSchema])
def usage_token_prices_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> list[AIUsageTokenPriceSchema]:
    rows = list_usage_token_prices(tenant_id=int(tenant["id"]))
    return [AIUsageTokenPriceSchema.model_validate(item) for item in rows]


@router.put("/prices/{provider}/{model_key}", response_model=AIUsageTokenPriceSchema)
def put_usage_token_price_endpoint(
    provider: str,
    model_key: str,
    payload: AIUsageTokenPricePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AIUsageTokenPriceSchema:
    try:
        row = upsert_usage_token_price(
            provider,
            model_key,
            payload.model_dump(),
            tenant_id=int(tenant["id"]),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        action="ai.usage.price.upsert",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="ai_gateway",
        result="success",
        metadata={
            "provider": row.get("provider"),
            "model_key": row.get("model_key"),
            "input_price_per_1k": row.get("input_price_per_1k"),
            "output_price_per_1k": row.get("output_price_per_1k"),
        },
        tenant_id=int(tenant["id"]),
    )
    return AIUsageTokenPriceSchema.model_validate(row)


@router.get("/slo", response_model=list[AISLOPolicySchema])
def get_slo_policies_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> list[AISLOPolicySchema]:
    rows = list_slo_policies(tenant_id=int(tenant["id"]))
    return [AISLOPolicySchema.model_validate(item) for item in rows]


@router.put("/slo/{model_key}", response_model=AISLOPolicySchema)
def put_slo_policy_endpoint(
    model_key: str,
    payload: AISLOPolicyPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AISLOPolicySchema:
    try:
        row = upsert_slo_policy(model_key, payload.model_dump(), tenant_id=int(tenant["id"]))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        action="ai.slo.policy.upsert",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="ai_gateway",
        result="success",
        metadata={
            "model_key": row.get("model_key"),
            "p95_latency_ms": row.get("p95_latency_ms"),
            "max_error_rate_pct": row.get("max_error_rate_pct"),
        },
        tenant_id=int(tenant["id"]),
    )
    return AISLOPolicySchema.model_validate(row)


@router.get("/slo/compliance", response_model=list[AISLOComplianceSchema])
def get_slo_compliance_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    limit: Annotated[int, Query(ge=1, le=5000)] = 500,
) -> list[AISLOComplianceSchema]:
    rows = list_slo_compliance(tenant_id=int(tenant["id"]), limit=int(limit))
    return [AISLOComplianceSchema.model_validate(item) for item in rows]


@router.get("/slo/violations", response_model=list[AISLOViolationSchema])
def get_slo_violations_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    limit: Annotated[int, Query(ge=1, le=5000)] = 500,
) -> list[AISLOViolationSchema]:
    rows = list_slo_violations(tenant_id=int(tenant["id"]), limit=int(limit))
    return [AISLOViolationSchema.model_validate(item) for item in rows]


@router.get("/safety-policies", response_model=list[AISafetyPolicySchema])
def list_safety_policies_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
) -> list[AISafetyPolicySchema]:
    rows = list_ai_safety_policies()
    return [AISafetyPolicySchema.model_validate(item) for item in rows]


@router.put("/safety-policies/{tenant_id}", response_model=AISafetyPolicySchema)
def put_safety_policy_endpoint(
    tenant_id: int,
    payload: AISafetyPolicyPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
) -> AISafetyPolicySchema:
    try:
        row = upsert_ai_safety_policy(payload.model_dump(), tenant_id=tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    log_admin_action(
        actor=actor,
        action="ai.safety.policy.upsert",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="ai_safety_policy",
        result="success",
        metadata={"tenant_id": tenant_id, "audit_only": row.get("audit_only")},
        tenant_id=tenant_id,
    )
    return AISafetyPolicySchema.model_validate(row)


@router.get("/usage/budget", response_model=AIUsageBudgetReadSchema)
def get_usage_budget_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AIUsageBudgetReadSchema:
    row = get_usage_budget(tenant_id=int(tenant["id"]))
    return AIUsageBudgetReadSchema.model_validate(row)


@router.put("/usage/budget", response_model=AIUsageBudgetReadSchema)
def put_usage_budget_endpoint(
    payload: AIUsageBudgetPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AIUsageBudgetReadSchema:
    try:
        row = update_usage_budget(payload.model_dump(), tenant_id=int(tenant["id"]))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        action="ai.usage.budget.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="ai_gateway",
        result="success",
        metadata={
            "budget_limit_usd": row.get("budget_limit_usd"),
            "alert_threshold_pct": row.get("alert_threshold_pct"),
            "hard_cap": row.get("hard_cap"),
        },
        tenant_id=int(tenant["id"]),
    )
    return AIUsageBudgetReadSchema.model_validate(row)


@router.put("/usage/budgets", response_model=AIUsageBudgetScopedReadSchema)
def put_usage_budget_scoped_endpoint(
    payload: AIUsageBudgetScopedPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AIUsageBudgetScopedReadSchema:
    try:
        row = upsert_usage_budget_scoped(payload.model_dump(), tenant_id=int(tenant["id"]))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        action="ai.usage.budget.upsert_scoped",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="ai_gateway",
        result="success",
        metadata={
            "scope": row.get("scope"),
            "scope_id": row.get("scope_id"),
            "budget_limit_usd": row.get("budget_limit_usd"),
            "alert_threshold_pct": row.get("alert_threshold_pct"),
            "hard_cap": row.get("hard_cap"),
        },
        tenant_id=int(tenant["id"]),
    )
    return AIUsageBudgetScopedReadSchema.model_validate(row)


@router.get("/usage/budgets", response_model=list[AIUsageBudgetScopedReadSchema])
def list_usage_budgets_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> list[AIUsageBudgetScopedReadSchema]:
    rows = list_usage_budgets(tenant_id=int(tenant["id"]))
    return [AIUsageBudgetScopedReadSchema.model_validate(item) for item in rows]


@router.delete("/usage/budgets", response_model=AIUsageBudgetScopedReadSchema)
def delete_usage_budget_scoped_endpoint(
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    scope: Annotated[str, Query(min_length=1, max_length=32)] = "tenant",
    scope_id: Annotated[str | None, Query(max_length=200)] = None,
) -> AIUsageBudgetScopedReadSchema:
    try:
        row = delete_usage_budget_scoped(
            tenant_id=int(tenant["id"]),
            scope=scope,
            scope_id=scope_id,
        )
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        action="ai.usage.budget.delete_scoped",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="ai_gateway",
        result="success",
        metadata={
            "scope": row.get("scope"),
            "scope_id": row.get("scope_id"),
        },
        tenant_id=int(tenant["id"]),
    )
    return AIUsageBudgetScopedReadSchema.model_validate(row)


@router.get("/usage/budgets/status", response_model=list[AIUsageBudgetStatusSchema])
def get_usage_budget_status_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> list[AIUsageBudgetStatusSchema]:
    rows = list_usage_budget_status(tenant_id=int(tenant["id"]))
    return [AIUsageBudgetStatusSchema.model_validate(item) for item in rows]


@router.get("/routing/policies", response_model=list[AIRoutingPolicyReadSchema])
def list_routing_policies_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> list[AIRoutingPolicyReadSchema]:
    return [
        AIRoutingPolicyReadSchema.model_validate(item)
        for item in list_routing_policies(tenant_id=int(tenant["id"]))
    ]


@router.post("/routing/policies", response_model=AIRoutingPolicyReadSchema, status_code=201)
def create_routing_policy_endpoint(
    payload: AIRoutingPolicyPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AIRoutingPolicyReadSchema:
    try:
        policy = create_routing_policy(payload.model_dump(), tenant_id=int(tenant["id"]))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        action="ai.routing.policy.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="ai_gateway",
        result="success",
        metadata={"policy_id": policy.get("id"), "name": policy.get("name")},
        tenant_id=int(tenant["id"]),
    )
    return AIRoutingPolicyReadSchema.model_validate(policy)


@router.put("/routing/policies/{policy_id}", response_model=AIRoutingPolicyReadSchema)
def update_routing_policy_endpoint(
    policy_id: int,
    payload: AIRoutingPolicyPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AIRoutingPolicyReadSchema:
    try:
        policy = update_routing_policy(policy_id, payload.model_dump(), tenant_id=int(tenant["id"]))
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        action="ai.routing.policy.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="ai_gateway",
        result="success",
        metadata={"policy_id": int(policy_id)},
        tenant_id=int(tenant["id"]),
    )
    return AIRoutingPolicyReadSchema.model_validate(policy)


@router.delete("/routing/policies/{policy_id}", status_code=204)
def delete_routing_policy_endpoint(
    policy_id: int,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> None:
    try:
        delete_routing_policy(policy_id, tenant_id=int(tenant["id"]))
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        action="ai.routing.policy.delete",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="ai_gateway",
        result="success",
        metadata={"policy_id": int(policy_id)},
        tenant_id=int(tenant["id"]),
    )


@router.get("/routing/selection-log")
def get_routing_selection_log_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.ai.models.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, object]]:
    return list_routing_selection_log(tenant_id=int(tenant["id"]), limit=limit)
