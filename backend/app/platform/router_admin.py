from __future__ import annotations

from typing import Annotated
import dataclasses as _dc

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.modules.audit.service import log_admin_action
from app.modules.rbac.service import is_platform_admin
from app.modules.rbac.security import get_actor, permission_dependency, resolve_current_user_claims
from app.modules.tenants.service import get_tenant
from app.platform.analytics import service as analytics_service
from app.platform.analytics.entitlements import (
    build_analytics_read_policy_state_read,
    list_analytics_read_policy_state_reads,
)
from app.platform.analytics.schemas import AnalyticsEventProjectionListSchema, AnalyticsEventProjectionRead, TenantKpiSnapshotRead
from app.platform.ai import service as ai_service
from app.platform.ai.schemas import CopilotAnswerReadSchema, CopilotQuestionRequestSchema, CopilotQueryLogReadSchema
from app.platform.developer import service as developer_service
from app.platform.education_graph import service as education_graph_service
from app.platform.developer.schemas import (
    DeveloperApiLogReadSchema,
    DeveloperAppCreateSchema,
    DeveloperAppEventSubscriptionCreateSchema,
    DeveloperAppEventSubscriptionReadSchema,
    DeveloperAppInstallSchema,
    DeveloperAppInstallationReadSchema,
    DeveloperAppReadSchema,
    DeveloperAppSecretReadSchema,
)
from app.platform.education_graph.schemas import (
    CourseSkillCreateSchema,
    CourseSkillReadSchema,
    SkillCreateSchema,
    SkillReadSchema,
    StudentSkillReadSchema,
)
from app.platform.federation import service as federation_service
from app.platform.federation.schemas import (
    InstitutionCreateSchema,
    InstitutionOverviewSchema,
    InstitutionReadSchema,
    LinkTenantSchema,
    FederationMemberReadSchema,
)
from app.platform.kpi import service as kpi_service
from app.platform.kpi.schemas import RectorDashboardReadSchema, TenantMetricSnapshotReadSchema
from app.platform.automation import service as automation_service
from app.platform.automation.schemas import (
    AutomationExecutionReadSchema,
    AutomationRuleCreateSchema,
    AutomationRuleReadSchema,
)
from app.platform.automation.templates import service as automation_template_service
from app.platform.automation.templates.schemas import (
    AutomationTemplateReadSchema,
    InstantiateTemplateSchema,
)
from app.platform.context import service as context_service
from app.platform.context.schemas import StudentProfileRead
from app.platform.billing import service as billing_service
from app.platform.feature_flags import service as flags_service
from app.platform.jobs import service as jobs_service
from app.platform.notifications import service as notifications_service
from app.platform.webhooks import service as webhooks_service
from app.platform.uow import UnitOfWork
from app.platform.schemas import (
    AnalyticsEntitlementRolloutSummaryListRead,
    AnalyticsEntitlementRolloutStateRead,
    FeatureFlagRead,
    FeatureFlagSetRequest,
    JobEnqueueRequest,
    JobRead,
    NotificationRead,
    NotificationRequest,
    PlanCreateRequest,
    PlanRead,
    SubscriptionAssignRequest,
    SubscriptionRead,
    TenantCreateRequest,
    TenantMapRequest,
    TenantPlatformRead,
    TenantSettingsPatchRequest,
    TenantSuspendRequest,
    UsageCounterIncrementRequest,
    UsageCounterRead,
)
from app.platform.tenant import service as tenant_service
from app.platform.webhooks.schemas import (
    WebhookDeliveryListSchema,
    WebhookDeliveryReadSchema,
    WebhookSubscriptionCreateSchema,
    WebhookSubscriptionReadSchema,
)

router = APIRouter(prefix="/api/v1/admin", tags=["platform-core-admin"])


Actor = Annotated[str, Depends(get_actor)]
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
PLATFORM_TENANT_ID = 1

_platform_admin_read_dependency = permission_dependency("platform.admin.read")
_platform_admin_write_dependency = permission_dependency("platform.admin.write")


async def _require_platform_admin_permissions(
    request: Request,
    _: Annotated[None, Depends(_platform_admin_read_dependency)],
) -> None:
    if request.method.upper() in SAFE_METHODS:
        return
    await _platform_admin_write_dependency(request)


def _require_request_tenant_id(request: Request) -> int:
    claims = resolve_current_user_claims(request, request.headers.get("authorization"))
    token_tenant_id = int(claims.tenant_id)
    if token_tenant_id <= 0:
        raise HTTPException(status_code=403, detail="invalid tenant context")

    header_tenant_id = request.headers.get("x-tenant-id")
    if header_tenant_id is not None:
        try:
            tenant_id = int(str(header_tenant_id).strip())
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail="invalid tenant header") from exc
        if tenant_id <= 0:
            raise HTTPException(status_code=400, detail="invalid tenant header")
        if tenant_id != token_tenant_id:
            claim_roles = {str(role).strip() for role in claims.roles if str(role).strip()}
            platform_admin = "superadmin" in claim_roles or is_platform_admin(claims.user_id)
            if not platform_admin:
                raise HTTPException(status_code=403, detail="cross-tenant override forbidden")
            token_tenant_id = tenant_id

    tenant = get_tenant(token_tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail=f"Tenant {token_tenant_id} not found")
    if tenant.get("status") != "active":
        raise HTTPException(status_code=403, detail=f"Tenant {token_tenant_id} is not active")
    return token_tenant_id


router.dependencies.append(Depends(_require_platform_admin_permissions))
router.dependencies.append(Depends(_require_request_tenant_id))


def _enforce_target_tenant_match(request: Request, target_tenant_id: int) -> None:
    request_tenant_id = _require_request_tenant_id(request)
    if int(target_tenant_id) != int(request_tenant_id):
        raise HTTPException(status_code=403, detail="cross-tenant access denied")


def _require_platform_tenant_context(request: Request) -> None:
    request_tenant_id = _require_request_tenant_id(request)
    if int(request_tenant_id) != PLATFORM_TENANT_ID:
        raise HTTPException(status_code=403, detail="cross-tenant access denied")


def _audit(request: Request, actor: str, action: str, tenant_id: int, metadata: dict[str, object] | None = None) -> None:
    log_admin_action(
        actor=actor,
        tenant_id=int(tenant_id),
        action=action,
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="platform-core",
        result="success",
        metadata=metadata or {},
    )


def _legacy_job_read(row: dict[str, object]) -> JobRead:
    return JobRead.model_validate(
        {
            "id": int(row.get("id") or 0),
            "tenant_id": int(row.get("tenant_id") or 0),
            "job_type": str(row.get("job_type") or ""),
            "status": str(row.get("status") or ""),
            "retry_count": int(row.get("retry_count") or 0),
            "max_retries": int(row.get("max_retries") or 0),
            "payload": dict(row.get("payload_json") or {}),
            "result": row.get("result_json"),
            "error": row.get("error_message"),
            "created_at": str(row.get("created_at") or ""),
            "updated_at": str(row.get("finished_at") or row.get("started_at") or row.get("created_at") or ""),
        }
    )


@router.post("/tenants", response_model=TenantPlatformRead, status_code=201)
def create_tenant(request: Request, payload: TenantCreateRequest, actor: Actor) -> TenantPlatformRead:
    try:
        row = tenant_service.create_tenant(
            payload.slug,
            payload.name,
            actor=actor,
            correlation_id=getattr(request.state, "request_id", None),
            causation_id="platform.admin.create_tenant",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit(request, actor, "platform_core.tenant.create", int(row["tenant_id"]), {"slug": payload.slug})
    return TenantPlatformRead.model_validate(row)


@router.get(
    "/tenants/analytics/entitlement-rollout-summary",
    response_model=AnalyticsEntitlementRolloutSummaryListRead,
)
def list_tenant_analytics_entitlement_rollout_summary(
    request: Request,
    _actor: Actor,
    limit: int = Query(default=100, ge=1, le=200),
) -> AnalyticsEntitlementRolloutSummaryListRead:
    _require_platform_tenant_context(request)
    items = list_analytics_read_policy_state_reads(limit=limit)
    return AnalyticsEntitlementRolloutSummaryListRead.model_validate(
        {
            "limit": int(limit),
            "count": len(items),
            "items": items,
        }
    )


@router.get("/tenants/{tenant_id}", response_model=TenantPlatformRead)
def get_tenant_profile(tenant_id: int, _actor: Actor) -> TenantPlatformRead:
    try:
        row = tenant_service.get_tenant_profile(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TenantPlatformRead.model_validate(row)


@router.patch("/tenants/{tenant_id}/settings", response_model=TenantPlatformRead)
def patch_tenant_settings(
    tenant_id: int,
    payload: TenantSettingsPatchRequest,
    request: Request,
    actor: Actor,
) -> TenantPlatformRead:
    try:
        row = tenant_service.patch_settings(tenant_id, payload.settings)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _audit(request, actor, "platform_core.tenant.settings.patch", tenant_id)
    return TenantPlatformRead.model_validate(row)


@router.put("/tenants/{tenant_id}/quotas", response_model=TenantPlatformRead)
def set_tenant_quotas(tenant_id: int, payload: TenantMapRequest, request: Request, actor: Actor) -> TenantPlatformRead:
    try:
        row = tenant_service.set_quotas(tenant_id, payload.values)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _audit(request, actor, "platform_core.tenant.quotas.put", tenant_id)
    return TenantPlatformRead.model_validate(row)


@router.put("/tenants/{tenant_id}/limits", response_model=TenantPlatformRead)
def set_tenant_limits(tenant_id: int, payload: TenantMapRequest, request: Request, actor: Actor) -> TenantPlatformRead:
    try:
        row = tenant_service.set_limits(tenant_id, payload.values)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _audit(request, actor, "platform_core.tenant.limits.put", tenant_id)
    return TenantPlatformRead.model_validate(row)


@router.post("/tenants/{tenant_id}/suspension", response_model=TenantPlatformRead)
def set_tenant_suspension(
    tenant_id: int,
    payload: TenantSuspendRequest,
    request: Request,
    actor: Actor,
) -> TenantPlatformRead:
    try:
        row = tenant_service.set_suspended(tenant_id, payload.suspended)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _audit(request, actor, "platform_core.tenant.suspension.set", tenant_id, {"suspended": payload.suspended})
    return TenantPlatformRead.model_validate(row)


@router.put("/features/{module}/{key}", response_model=FeatureFlagRead)
def set_platform_feature(module: str, key: str, payload: FeatureFlagSetRequest, request: Request, actor: Actor) -> FeatureFlagRead:
    row = flags_service.set_platform_feature(module, key, payload.enabled)
    _audit(request, actor, "platform_core.feature.platform.set", 1, {"module": module, "key": key})
    return FeatureFlagRead.model_validate(row)


@router.put("/tenants/{tenant_id}/features/{module}/{key}", response_model=FeatureFlagRead)
def set_tenant_feature(
    tenant_id: int,
    module: str,
    key: str,
    payload: FeatureFlagSetRequest,
    request: Request,
    actor: Actor,
) -> FeatureFlagRead:
    _enforce_target_tenant_match(request, tenant_id)
    row = flags_service.set_tenant_feature(tenant_id, module, key, payload.enabled)
    _audit(request, actor, "platform_core.feature.tenant.set", tenant_id, {"module": module, "key": key})
    return FeatureFlagRead.model_validate(row)


@router.get(
    "/tenants/{tenant_id}/analytics/entitlement-rollout-state",
    response_model=AnalyticsEntitlementRolloutStateRead,
)
def get_tenant_analytics_entitlement_rollout_state(
    tenant_id: int,
    request: Request,
    _actor: Actor,
) -> AnalyticsEntitlementRolloutStateRead:
    _enforce_target_tenant_match(request, tenant_id)
    try:
        payload = build_analytics_read_policy_state_read(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return AnalyticsEntitlementRolloutStateRead.model_validate(payload)


@router.post("/billing/plans", response_model=PlanRead, status_code=201)
def create_plan(payload: PlanCreateRequest, request: Request, actor: Actor) -> PlanRead:
    try:
        row = billing_service.create_plan(payload.code, payload.name, payload.price_cents, payload.features, payload.limits)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit(request, actor, "platform_core.billing.plan.create", 1, {"code": payload.code})
    return PlanRead.model_validate(row)


@router.get("/billing/plans", response_model=list[PlanRead])
def list_plans(_actor: Actor) -> list[PlanRead]:
    return [PlanRead.model_validate(item) for item in billing_service.list_plans()]


@router.put("/tenants/{tenant_id}/billing/subscription", response_model=SubscriptionRead)
def assign_subscription(
    tenant_id: int,
    payload: SubscriptionAssignRequest,
    request: Request,
    actor: Actor,
) -> SubscriptionRead:
    try:
        row = billing_service.assign_plan(tenant_id, payload.plan_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit(request, actor, "platform_core.billing.subscription.assign", tenant_id, {"plan_code": payload.plan_code})
    return SubscriptionRead.model_validate(row)


@router.post("/tenants/{tenant_id}/billing/usage/{metric}", response_model=UsageCounterRead)
def increment_usage(
    tenant_id: int,
    metric: str,
    payload: UsageCounterIncrementRequest,
    request: Request,
    actor: Actor,
) -> UsageCounterRead:
    row = billing_service.increment_usage(tenant_id, metric, payload.value)
    _audit(request, actor, "platform_core.billing.usage.increment", tenant_id, {"metric": metric, "value": payload.value})
    return UsageCounterRead.model_validate(row)


@router.post("/jobs", response_model=JobRead, status_code=201)
def enqueue_job(payload: JobEnqueueRequest, request: Request, actor: Actor) -> JobRead:
    row = jobs_service.enqueue_job(payload.tenant_id, payload.job_type, payload.payload, max_retries=payload.max_retries)
    _audit(request, actor, "platform_core.jobs.enqueue", payload.tenant_id, {"job_type": payload.job_type})
    return JobRead.model_validate(row)


@router.post("/notifications", response_model=NotificationRead, status_code=201)
def dispatch_notification(payload: NotificationRequest, request: Request, actor: Actor) -> NotificationRead:
    try:
        row = notifications_service.dispatch_notification(
            tenant_id=payload.tenant_id,
            channel=payload.channel,
            target=payload.target,
            payload=payload.payload,
            subject=payload.subject,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit(request, actor, "platform_core.notification.dispatch", payload.tenant_id, {"channel": payload.channel})
    return NotificationRead.model_validate(row)


@router.post("/webhooks/subscriptions", response_model=WebhookSubscriptionReadSchema, status_code=201)
def create_webhook_subscription(payload: WebhookSubscriptionCreateSchema, request: Request, actor: Actor) -> WebhookSubscriptionReadSchema:
    try:
        row = webhooks_service.webhook_service.create_subscription(
            tenant_id=payload.tenant_id,
            event_type=payload.event_type,
            target_url=payload.target_url,
            signing_secret=payload.signing_secret,
            actor=actor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit(
        request,
        actor,
        "platform_core.webhook.subscription.create",
        payload.tenant_id,
        {"event_type": payload.event_type},
    )
    return WebhookSubscriptionReadSchema.model_validate(row)


@router.get("/tenants/{tenant_id}/webhooks/subscriptions", response_model=list[WebhookSubscriptionReadSchema])
def list_webhook_subscriptions(tenant_id: int, request: Request, _actor: Actor) -> list[WebhookSubscriptionReadSchema]:
    _enforce_target_tenant_match(request, tenant_id)
    rows = webhooks_service.webhook_service.list_subscriptions(tenant_id=tenant_id, limit=200)
    return [WebhookSubscriptionReadSchema.model_validate(item) for item in rows]


@router.post("/webhooks/subscriptions/{subscription_id}/deactivate", response_model=WebhookSubscriptionReadSchema)
def deactivate_webhook_subscription(subscription_id: int, request: Request, actor: Actor) -> WebhookSubscriptionReadSchema:
    try:
        row = webhooks_service.webhook_service.deactivate_subscription(subscription_id=subscription_id, actor=actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _audit(
        request,
        actor,
        "platform_core.webhook.subscription.deactivate",
        int(row["tenant_id"]),
        {"subscription_id": subscription_id},
    )
    return WebhookSubscriptionReadSchema.model_validate(row)


@router.get("/tenants/{tenant_id}/webhooks/deliveries", response_model=WebhookDeliveryListSchema)
def list_webhook_deliveries(tenant_id: int, _actor: Actor) -> WebhookDeliveryListSchema:
    rows = webhooks_service.webhook_service.list_deliveries(tenant_id=tenant_id, limit=200)
    return WebhookDeliveryListSchema(
        tenant_id=tenant_id,
        total=len(rows),
        items=[WebhookDeliveryReadSchema.model_validate(item) for item in rows],
    )


@router.get("/tenants/{tenant_id}/analytics/events", response_model=AnalyticsEventProjectionListSchema)
def list_analytics_events(
    _actor: Actor,
    request: Request,
    tenant_id: int,
    event_type: str | None = None,
    limit: int = 100,
) -> AnalyticsEventProjectionListSchema:
    _enforce_target_tenant_match(request, tenant_id)

    with UnitOfWork() as uow:
        items = analytics_service.list_event_projections(
            tenant_id=tenant_id,
            event_type=event_type or None,
            limit=max(1, min(limit, 500)),
            uow=uow,
        )
    return AnalyticsEventProjectionListSchema(
        tenant_id=tenant_id,
        total=len(items),
        items=[AnalyticsEventProjectionRead.model_validate(item) for item in items],
    )


@router.get("/tenants/{tenant_id}/analytics/kpis/latest", response_model=TenantKpiSnapshotRead)
def get_latest_analytics_kpis(
    tenant_id: int,
    _actor: Actor,
) -> TenantKpiSnapshotRead:
    with UnitOfWork() as uow:
        snap = analytics_service.get_latest_tenant_kpis(tenant_id=tenant_id, uow=uow)
    if snap is None:
        raise HTTPException(status_code=404, detail="No KPI snapshot found for this tenant")
    return TenantKpiSnapshotRead.model_validate(snap)


@router.get("/skills", response_model=list[SkillReadSchema])
def list_skills(tenant_id: int, request: Request, _actor: Actor) -> list[SkillReadSchema]:
    _enforce_target_tenant_match(request, tenant_id)
    with UnitOfWork() as uow:
        rows = education_graph_service.list_skills(tenant_id=tenant_id, uow=uow)
    return [SkillReadSchema.model_validate(item) for item in rows]


@router.post("/skills", response_model=SkillReadSchema, status_code=201)
def create_skill(body: SkillCreateSchema, actor: Actor, request: Request) -> SkillReadSchema:
    _enforce_target_tenant_match(request, int(body.tenant_id))
    with UnitOfWork() as uow:
        row = education_graph_service.create_skill(
            tenant_id=body.tenant_id,
            skill_key=body.skill_key,
            name=body.name,
            description=body.description,
            category=body.category,
            level=body.level,
            uow=uow,
        )
    _audit(
        request,
        actor,
        "platform_core.education_graph.skill.create",
        int(body.tenant_id),
        {"skill_key": body.skill_key, "category": body.category},
    )
    return SkillReadSchema.model_validate(row)


@router.get("/course-skills", response_model=list[CourseSkillReadSchema])
def list_course_skills(
    tenant_id: int,
    request: Request,
    _actor: Actor,
    course_id: str | None = None,
) -> list[CourseSkillReadSchema]:
    _enforce_target_tenant_match(request, tenant_id)
    with UnitOfWork() as uow:
        rows = education_graph_service.list_course_skills(
            tenant_id=tenant_id,
            course_id=course_id,
            uow=uow,
        )
    return [CourseSkillReadSchema.model_validate(item) for item in rows]


@router.post("/course-skills", response_model=CourseSkillReadSchema, status_code=201)
def create_course_skill(body: CourseSkillCreateSchema, actor: Actor, request: Request) -> CourseSkillReadSchema:
    _enforce_target_tenant_match(request, int(body.tenant_id))
    try:
        with UnitOfWork() as uow:
            row = education_graph_service.map_course_skill(
                tenant_id=body.tenant_id,
                course_id=body.course_id,
                skill_id=body.skill_id,
                weight=body.weight,
                uow=uow,
            )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    _audit(
        request,
        actor,
        "platform_core.education_graph.course_skill.create",
        int(body.tenant_id),
        {"course_id": body.course_id, "skill_id": body.skill_id, "weight": body.weight},
    )
    return CourseSkillReadSchema.model_validate(row)


@router.get("/student-skills", response_model=list[StudentSkillReadSchema])
def list_student_skills(
    tenant_id: int,
    request: Request,
    _actor: Actor,
    student_id: str | None = None,
) -> list[StudentSkillReadSchema]:
    _enforce_target_tenant_match(request, tenant_id)
    with UnitOfWork() as uow:
        rows = education_graph_service.list_student_skills(
            tenant_id=tenant_id,
            student_id=student_id,
            uow=uow,
        )
    return [StudentSkillReadSchema.model_validate(item) for item in rows]


@router.get("/platform/kpi/metrics", response_model=list[TenantMetricSnapshotReadSchema])
def get_platform_kpi_metrics(tenant_id: int, _actor: Actor) -> list[TenantMetricSnapshotReadSchema]:
    with UnitOfWork() as uow:
        rows = kpi_service.get_latest_tenant_metrics(tenant_id=tenant_id, uow=uow)
        if not rows:
            rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)
    return [TenantMetricSnapshotReadSchema.model_validate(item) for item in rows]


@router.get("/platform/kpi/dashboard", response_model=RectorDashboardReadSchema)
def get_platform_rector_dashboard(tenant_id: int, _actor: Actor) -> RectorDashboardReadSchema:
    with UnitOfWork() as uow:
        payload = kpi_service.get_rector_dashboard(tenant_id=tenant_id, uow=uow)
    return RectorDashboardReadSchema.model_validate(payload)


# ------------------------------------------------------------------ #
#  Automation / Workflow Engine v1                                     #
# ------------------------------------------------------------------ #


@router.post("/platform/automation/rules", response_model=AutomationRuleReadSchema, status_code=201)
def create_automation_rule(body: AutomationRuleCreateSchema, actor: Actor, request: Request) -> AutomationRuleReadSchema:
    with UnitOfWork() as uow:
        rule = automation_service.create_rule(
            tenant_id=body.tenant_id,
            name=body.name,
            description=body.description,
            event_type=body.event_type,
            condition_json=body.condition_json,
            actions_json=body.actions_json,
            is_active=body.is_active,
            uow=uow,
        )
    _audit(request, actor, "platform_core.automation.rule_created", body.tenant_id, {"rule_name": body.name})
    return AutomationRuleReadSchema.model_validate(_dc.asdict(rule))


@router.get("/platform/automation/rules", response_model=list[AutomationRuleReadSchema])
def list_automation_rules(tenant_id: int, _actor: Actor) -> list[AutomationRuleReadSchema]:
    with UnitOfWork() as uow:
        rules = automation_service.list_rules(tenant_id=tenant_id, uow=uow)
    return [AutomationRuleReadSchema.model_validate(_dc.asdict(r)) for r in rules]


@router.get("/platform/automation/executions", response_model=list[AutomationExecutionReadSchema])
def list_automation_executions(tenant_id: int, _actor: Actor) -> list[AutomationExecutionReadSchema]:
    with UnitOfWork() as uow:
        executions = automation_service.list_executions(tenant_id=tenant_id, uow=uow)
    return [AutomationExecutionReadSchema.model_validate(_dc.asdict(e)) for e in executions]


@router.get("/platform/automation/templates", response_model=list[AutomationTemplateReadSchema])
def list_automation_templates(_actor: Actor) -> list[AutomationTemplateReadSchema]:
    """List all automation templates (system and user-created)."""
    with UnitOfWork() as uow:
        templates = automation_template_service.list_templates(uow=uow)
    return [AutomationTemplateReadSchema.model_validate(_dc.asdict(t)) for t in templates]


@router.post(
    "/platform/automation/templates/{template_key}/instantiate",
    response_model=AutomationRuleReadSchema,
    status_code=201,
)
def instantiate_automation_template(
    template_key: str,
    body: InstantiateTemplateSchema,
    actor: Actor,
    request: Request,
) -> AutomationRuleReadSchema:
    """Instantiate an automation template into a new rule for the tenant."""
    tenant_id = _require_request_tenant_id(request)

    with UnitOfWork() as uow:
        rule = automation_template_service.instantiate_template(
            template_key=template_key,
            tenant_id=tenant_id,
            rule_name=body.rule_name,
            rule_description=body.rule_description,
            uow=uow,
        )

    _audit(
        request,
        actor,
        "platform_core.automation.template_instantiated",
        tenant_id,
        {"template_key": template_key, "rule_name": rule.name},
    )
    return AutomationRuleReadSchema.model_validate(_dc.asdict(rule))


# ------------------------------------------------------------------ #
#  Context Layer                                                        #
# ------------------------------------------------------------------ #

@router.get("/platform/context/student/{student_id}", response_model=StudentProfileRead)
def get_student_context_profile(
    student_id: str,
    tenant_id: int,
    _actor: Actor,
) -> StudentProfileRead:
    """Return the full semantic profile for a student (admin-scoped)."""
    with UnitOfWork() as uow:
        profile = context_service.build_student_profile(
            student_id=student_id,
            tenant_id=tenant_id,
            conn=uow.conn,
        )
    return StudentProfileRead.model_validate(profile)


# ------------------------------------------------------------------ #
#  AI Copilot Foundation v1 (read-only)                               #
# ------------------------------------------------------------------ #


@router.post("/platform/ai/copilot/ask", response_model=CopilotAnswerReadSchema)
def ask_copilot(
    body: CopilotQuestionRequestSchema,
    actor: Actor,
    request: Request,
) -> CopilotAnswerReadSchema:
    answer = ai_service.answer_question(
        tenant_id=body.tenant_id,
        actor_id=actor,
        question=body.question,
        context=body.context,
    )
    _audit(
        request,
        actor,
        "platform_core.ai.copilot.ask",
        int(body.tenant_id),
        {"query_length": len(body.question)},
    )
    return CopilotAnswerReadSchema.model_validate(answer)


@router.get("/platform/ai/copilot/logs", response_model=list[CopilotQueryLogReadSchema])
def list_copilot_logs(
    tenant_id: int,
    _actor: Actor,
    limit: int = 100,
) -> list[CopilotQueryLogReadSchema]:
    items = ai_service.list_logs(tenant_id=tenant_id, limit=max(1, min(limit, 500)))
    return [CopilotQueryLogReadSchema.model_validate(item) for item in items]


# ------------------------------------------------------------------ #
#  Federation Layer v1                                                #
# ------------------------------------------------------------------ #


@router.post("/platform/federation/institutions", response_model=InstitutionReadSchema, status_code=201)
def create_institution(
    body: InstitutionCreateSchema,
    actor: Actor,
    request: Request,
) -> InstitutionReadSchema:
    try:
        institution = federation_service.create_institution(
            name=body.name,
            code=body.code,
            country=body.country,
            inst_type=body.type,
            metadata=body.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit(request, actor, "platform_core.federation.institution.create", 1, {"code": body.code})
    return InstitutionReadSchema.model_validate(institution)


@router.get("/platform/federation/institutions", response_model=list[InstitutionReadSchema])
def list_institutions(_actor: Actor) -> list[InstitutionReadSchema]:
    institutions = federation_service.list_institutions()
    return [InstitutionReadSchema.model_validate(i) for i in institutions]


@router.get("/platform/federation/institutions/{institution_id}", response_model=InstitutionReadSchema)
def get_institution(institution_id: int, _actor: Actor) -> InstitutionReadSchema:
    institution = federation_service.get_institution(institution_id)
    if institution is None:
        raise HTTPException(status_code=404, detail=f"Institution {institution_id} not found")
    return InstitutionReadSchema.model_validate(institution)


@router.post(
    "/platform/federation/institutions/{institution_id}/tenants",
    response_model=FederationMemberReadSchema,
    status_code=201,
)
def link_tenant_to_institution(
    institution_id: int,
    body: LinkTenantSchema,
    actor: Actor,
    request: Request,
) -> FederationMemberReadSchema:
    try:
        member = federation_service.register_tenant_under_institution(
            institution_id=institution_id,
            tenant_id=body.tenant_id,
            role=body.role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit(
        request, actor,
        "platform_core.federation.tenant.link",
        int(body.tenant_id),
        {"institution_id": institution_id, "role": body.role},
    )
    return FederationMemberReadSchema.model_validate(member)


@router.get(
    "/platform/federation/institutions/{institution_id}/overview",
    response_model=InstitutionOverviewSchema,
)
def get_institution_overview(institution_id: int, _actor: Actor) -> InstitutionOverviewSchema:
    try:
        overview = federation_service.list_institution_overview(institution_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return InstitutionOverviewSchema.model_validate(overview)


@router.post("/platform/developer/apps", response_model=DeveloperAppSecretReadSchema, status_code=201)
def create_developer_app(
    body: DeveloperAppCreateSchema,
    actor: Actor,
    request: Request,
) -> DeveloperAppSecretReadSchema:
    tenant_id = _require_request_tenant_id(request)

    try:
        app = developer_service.developer_service.create_app(
            tenant_id=tenant_id,
            name=body.name,
            description=body.description,
            owner_email=body.owner_email,
            scopes=body.scopes,
            webhook_url=body.webhook_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit(request, actor, "platform_core.developer_app.create", tenant_id, {"app_key": app["app_key"]})
    return DeveloperAppSecretReadSchema.model_validate(app)


@router.get("/platform/developer/apps", response_model=list[DeveloperAppReadSchema])
def list_developer_apps(request: Request, _actor: Actor) -> list[DeveloperAppReadSchema]:
    tenant_id = _require_request_tenant_id(request)
    return [DeveloperAppReadSchema.model_validate(item) for item in developer_service.developer_service.list_apps(tenant_id=tenant_id)]


@router.get("/platform/developer/apps/{app_id}", response_model=DeveloperAppReadSchema)
def get_developer_app(app_id: int, request: Request, _actor: Actor) -> DeveloperAppReadSchema:
    tenant_id = _require_request_tenant_id(request)
    row = developer_service.developer_service.get_app(app_id, tenant_id=tenant_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"developer app {app_id} not found")
    return DeveloperAppReadSchema.model_validate(row)


@router.post("/platform/developer/apps/{app_id}/rotate-secret", response_model=DeveloperAppSecretReadSchema)
def rotate_developer_app_secret(app_id: int, actor: Actor, request: Request) -> DeveloperAppSecretReadSchema:
    tenant_id = _require_request_tenant_id(request)
    try:
        row = developer_service.developer_service.rotate_secret(app_id, tenant_id=tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _audit(request, actor, "platform_core.developer_app.rotate_secret", tenant_id, {"app_id": app_id})
    return DeveloperAppSecretReadSchema.model_validate(row)


@router.post(
    "/platform/developer/apps/{app_id}/installations",
    response_model=DeveloperAppInstallationReadSchema,
    status_code=201,
)
def install_developer_app(
    app_id: int,
    body: DeveloperAppInstallSchema,
    actor: Actor,
    request: Request,
) -> DeveloperAppInstallationReadSchema:
    request_tenant_id = _require_request_tenant_id(request)
    if request_tenant_id != int(body.tenant_id):
        raise HTTPException(status_code=403, detail="cross-tenant installation denied")

    try:
        row = developer_service.developer_service.install_app(app_id=app_id, tenant_id=body.tenant_id, installed_by=actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _audit(request, actor, "platform_core.developer_app.install", body.tenant_id, {"app_id": app_id})
    return DeveloperAppInstallationReadSchema.model_validate(row)


@router.get(
    "/platform/developer/apps/{app_id}/installations",
    response_model=list[DeveloperAppInstallationReadSchema],
)
def list_developer_app_installations(app_id: int, request: Request, _actor: Actor) -> list[DeveloperAppInstallationReadSchema]:
    tenant_id = _require_request_tenant_id(request)
    items = developer_service.developer_service.list_installations(app_id, tenant_id=tenant_id)
    if not items and developer_service.developer_service.get_app(app_id, tenant_id=tenant_id) is None:
        raise HTTPException(status_code=404, detail=f"developer app {app_id} not found")
    return [
        DeveloperAppInstallationReadSchema.model_validate(item)
        for item in items
    ]


@router.get("/platform/developer/apps/{app_id}/logs", response_model=list[DeveloperApiLogReadSchema])
def list_developer_app_logs(app_id: int, request: Request, _actor: Actor, limit: int = 100) -> list[DeveloperApiLogReadSchema]:
    tenant_id = _require_request_tenant_id(request)
    items = developer_service.developer_service.list_api_logs(app_id, tenant_id=tenant_id, limit=limit)
    if not items and developer_service.developer_service.get_app(app_id, tenant_id=tenant_id) is None:
        raise HTTPException(status_code=404, detail=f"developer app {app_id} not found")
    return [
        DeveloperApiLogReadSchema.model_validate(item)
        for item in items
    ]


@router.post(
    "/platform/developer/apps/{app_id}/subscriptions",
    response_model=DeveloperAppEventSubscriptionReadSchema,
    status_code=201,
)
def subscribe_developer_app_to_event(
    app_id: int,
    body: DeveloperAppEventSubscriptionCreateSchema,
    actor: Actor,
    request: Request,
) -> DeveloperAppEventSubscriptionReadSchema:
    tenant_id = _require_request_tenant_id(request)
    try:
        row = developer_service.developer_service.subscribe_to_event(
            app_id=app_id,
            event_type=body.event_type,
            tenant_id=tenant_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _audit(request, actor, "platform_core.developer_app.subscribe", tenant_id, {"app_id": app_id, "event_type": body.event_type})
    return DeveloperAppEventSubscriptionReadSchema.model_validate(row)
