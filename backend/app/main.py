import asyncio
from datetime import datetime, timezone
from contextlib import asynccontextmanager
import hmac
import logging
import os
import time
import uuid
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.responses import PlainTextResponse
from sqlalchemy import text

from app.core.config import (
    get_auth_cookie_name,
    get_auth_csrf_cookie_name,
    is_billing_module_router_enabled,
    is_csrf_protection_enabled,
    get_metrics_allowed_ips,
    get_metrics_token,
    is_production_mode,
    is_worker_health_required,
    validate_required_environment,
)
from app.core.runtime_schema import bootstrap_runtime_schema
from app.modules.university_core.entity_impl import validate_entity_tables_impl

from app.modules.admin.router import router as admin_router
from app.modules.admin.local_users_router import router as admin_local_users_router
from app.modules.academic_records.router import router as academic_records_router
from app.modules.admissions.router import router as admissions_router
from app.modules.ai_gateway.router import router as ai_gateway_router
from app.modules.ai_gateway.public_router import router as ai_gateway_public_router
from app.modules.audit.router import router as audit_router
from app.modules.audit.service import log_admin_action, reset_request_tenant_id, set_request_tenant_id
from app.modules.analytics.router import router as analytics_router
from app.modules.backup.router import router as backup_router
from app.modules.brain_core.router import router as brain_core_router
from app.modules.brain_core.service import brain_core_service
from app.modules.billing.router import router as billing_router
from app.modules.courses.router import router as courses_router
from app.modules.enrollments.router import router as enrollments_router
from app.modules.faculty.router import router as faculty_router
from app.modules.feature_flags.router import router as feature_flags_router
from app.modules.grades.router import router as grades_router
from app.modules.scheduling.router import router as scheduling_router
from app.modules.thesis.router import router as thesis_router
from app.modules.advising.router import router as advising_router
from app.modules.student_services.router import router as student_services_router
from app.modules.career_services.router import router as career_services_router
from app.modules.financial_aid.router import router as financial_aid_router
from app.modules.budget_planning.router import router as budget_planning_router
from app.modules.expense_controls.router import router as expense_controls_router
from app.modules.security_operations.router import router as security_operations_router
from app.modules.transport.router import router as transport_router
from app.modules.dining.router import router as dining_router
from app.modules.campus_sla.router import router as campus_sla_router
from app.modules.research_ethics.router import router as research_ethics_router
from app.modules.ip_management.router import router as ip_management_router
from app.modules.equipment_booking.router import router as equipment_booking_router
from app.modules.room_booking.router import router as room_booking_router
from app.modules.access_control.router import router as access_control_router
from app.modules.scholarship.router import router as scholarship_router
from app.modules.communications.router import router as communications_router
from app.modules.housing.router import router as housing_router
from app.modules.alumni.router import router as alumni_router
from app.modules.research.router import router as research_router
from app.modules.faculty_performance_kpis.router import router as faculty_performance_kpis_router
from app.modules.hr_payroll.router import router as hr_payroll_router
from app.modules.delinquency_collections.router import router as delinquency_collections_router
from app.modules.facilities_work_orders.router import router as facilities_work_orders_router
from app.modules.asset_inventory.router import router as asset_inventory_router
from app.modules.faculty_copilot.router import router as faculty_copilot_router
from app.modules.knowledge_retrieval.router import router as knowledge_retrieval_router
from app.modules.prompt_management.router import router as prompt_management_router
from app.modules.model_evaluation.router import router as model_evaluation_router
from app.modules.currency_localization.router import router as currency_localization_router
from app.modules.operations.router import router as operations_router
from app.modules.student_life.router import router as student_life_router
from app.modules.procurement.router import router as procurement_router
from app.modules.syllabus_governance.router import router as syllabus_governance_router
from app.modules.pdpl.router import router as pdpl_router
from app.modules.exam_governance.router import router as exam_governance_router
from app.modules.teaching_quality.router import router as teaching_quality_router
from app.modules.academic_integrity.router import router as academic_integrity_router
from app.modules.accreditation.router import router as accreditation_router
from app.modules.transcripts.router import router as transcripts_router
from app.modules.degree_progress.router import router as degree_progress_router
from app.modules.auth.router import router as auth_router
from app.modules.auth.token_service import (
    TokenValidationError,
    parse_access_token_from_request,
    validate_token_signing_config,
)
from app.modules.help.router import router as help_router
from app.modules.i18n.router import admin_router as i18n_admin_router
from app.modules.i18n.router import public_router as i18n_public_router
from app.modules.integrations.router import router as integrations_router
from app.modules.identity.router import router as identity_router
from app.modules.identity.phase1_router import router as identity_phase1_router
from app.modules.ldap.router import router as ldap_router
from app.modules.jobs.router import router as jobs_router
from app.modules.programs.router import router as programs_router
from app.modules.platform.router import router as platform_router
from app.modules.platform.self_service_router import router as platform_self_service_router
from app.platform.router_admin import router as platform_v1_admin_router
from app.platform.router_public import router as platform_v1_public_router
from app.platform.router_developer_api import router as platform_developer_api_router
from app.platform.router_internal import router as platform_v1_internal_router
from app.platform.router_mcp import router as platform_v1_mcp_router
from app.platform.router_semantic import router as platform_v2_semantic_router
from app.modules.profiles.router import router as profiles_router
from app.modules.interventions.router import router as interventions_router
from app.modules.interventions.playbook_router import router as interventions_playbook_router
from app.modules.interventions.risk_router import router as interventions_risk_router
from app.modules.interventions.effectiveness_router import router as interventions_effectiveness_router
from app.modules.org_structure.router import router as org_structure_router
from app.modules.plans.router import router as plans_router
from app.modules.subscriptions.router import router as subscriptions_router
from app.modules.workflows.router import router as workflows_router
from app.modules.rbac.router import router as rbac_router
from app.modules.rbac.security import get_actor
from app.modules.rbac.security import permission_dependency
from app.modules.rbac.security import resolve_current_user_claims
from app.modules.rbac.service import resolve_permissions_for_tenant
from app.modules.students.router import router as students_router
from app.modules.service_accounts.router import router as service_accounts_router
from app.modules.tenants.router import router as tenants_router
from app.modules.tenants.public_router import router as tenants_public_router
from app.core.db import build_engine, make_session_factory
from app.modules.observability.logging import (
    actor_id_var,
    configure_json_logging,
    institution_id_var,
    request_id_var,
    tenant_id_var,
    trace_id_var,
)
from app.modules.observability.health import comprehensive_payload, deep_payload, live_payload, readiness_payload
from app.modules.observability.perf_profile import (
    begin_request_profile,
    finish_request_profile,
    get_perf_profile_summary,
    install_redis_profiler,
    install_sqlalchemy_profiler,
    is_perf_profile_enabled,
    perf_segment,
    reset_perf_profile,
)
from app.modules.observability.trace import generate_trace_id
from app.modules.observability.metrics import record_request, render_metrics, snapshot_latency_metrics
from app.modules.observability.security_signals import record_security_signal
from app.modules.observability.otel import setup_otel, teardown_otel
from app.platform.runtime_state import get_scheduler_last_run, get_worker_heartbeat
from app.platform.uow import UnitOfWork
from app.modules.security.rate_limit import (
    check_request_rate_limit,
    get_rate_limit_audit_metadata,
    should_audit_rate_limit,
)

configure_json_logging()
logger = logging.getLogger("app.audit")
request_logger = logging.getLogger("app.request")


def _schedule_usage_event(tenant_id: int) -> None:
    async def _record() -> None:
        try:
            from app.modules.usage.service import record_usage_event

            await asyncio.to_thread(record_usage_event, int(tenant_id), "api_calls", 1)
        except Exception:
            pass

    try:
        asyncio.get_running_loop().create_task(_record())
    except RuntimeError:
        pass


def _extract_admin_module_from_path(path: str) -> str | None:
    if not path.startswith("/api/admin/"):
        return None
    suffix = path[len("/api/admin/"):]
    parts = [part for part in suffix.split("/") if part]
    if not parts:
        return None

    # Keep historical aliases stable where route prefix differs from module name.
    if parts[0] == "org":
        return "faculty"
    if parts[0] == "org-units":
        return "org_structure"
    if parts[0] == "research-grants":
        return "research"
    if parts[0] == "accreditation-compliance":
        return "accreditation"
    if parts[0] == "ops":
        return "operations"
    if parts[0] == "university" and len(parts) > 1 and parts[1] == "records":
        return "academic_records"

    return parts[0].replace("-", "_")


def _emit_brain_module_activity_signal(
    *,
    request: Request,
    status_code: int,
    tenant_id: int,
    correlation_id: str,
) -> None:
    path = request.url.path
    if not path.startswith("/api/admin/"):
        return
    if path.startswith("/api/admin/brain"):
        return
    if status_code >= 500:
        return

    module_name = _extract_admin_module_from_path(path)
    if not module_name:
        return

    brain_core_service.process_signal(
        {
            "signal_id": str(uuid.uuid4()),
            "tenant_id": int(tenant_id),
            "correlation_id": correlation_id,
            "event_type": "platform.module.activity.logged",
            "source_module": module_name,
            "source_entity_type": "http_request",
            "source_entity_id": correlation_id,
            "payload": {
                "path": path,
                "method": request.method,
                "status_code": int(status_code),
                "module": module_name,
            },
            "subject": {},
        }
    )


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    # Re-apply on process startup so third-party logger setup doesn't override JSON handlers.
    configure_json_logging()
    setup_otel(fastapi_app)
    validate_token_signing_config()
    # Skip in pytest runs (PYTEST_CURRENT_TEST is set by pytest automatically).
    # Tests use in-memory stores; env validation is verified by a dedicated test.
    in_pytest = bool(os.getenv("PYTEST_CURRENT_TEST"))
    if not in_pytest:
        validate_required_environment()

    # Runtime schema bootstrap may open a live DB connection. Keep startup tests
    # isolated from infrastructure by skipping this path under pytest.
    if not in_pytest:
        bootstrap_runtime_schema()
        validate_entity_tables_impl()

    # Wire the admissions SQLAlchemy session factory.
    # build_engine() raises RuntimeError when DATABASE_URL is absent; we catch it
    # and log a warning so that the server still starts (endpoints return 503).
    # In production DATABASE_URL must always be set.
    _admissions_engine = None
    try:
        _admissions_engine = build_engine()
        if is_perf_profile_enabled():
            install_sqlalchemy_profiler(_admissions_engine)
            install_redis_profiler()
        fastapi_app.state.admissions_engine = _admissions_engine
        fastapi_app.state.admissions_session_factory = make_session_factory(_admissions_engine)
        fastapi_app.state.profiles_session_factory = make_session_factory(_admissions_engine)
        fastapi_app.state.students_session_factory = make_session_factory(_admissions_engine)
        fastapi_app.state.grades_session_factory = make_session_factory(_admissions_engine)
        fastapi_app.state.workflows_session_factory = make_session_factory(_admissions_engine)
        logger.info("admissions database engine initialised (pool_size=5, max_overflow=10)")
    except RuntimeError as exc:
        fastapi_app.state.admissions_engine = None
        fastapi_app.state.profiles_session_factory = None
        fastapi_app.state.students_session_factory = None
        fastapi_app.state.grades_session_factory = None
        fastapi_app.state.workflows_session_factory = None
        logger.warning(
            "admissions database not configured — admissions endpoints will return HTTP 503. "
            "Reason: %s",
            exc,
        )
        logger.warning(
            "profiles database not configured — profiles endpoints will return HTTP 503. "
            "Reason: %s",
            exc,
        )
        logger.warning(
            "workflows database not configured — workflows endpoints will return HTTP 503. "
            "Reason: %s",
            exc,
        )

    # Seed sensible default Brain Core policy profiles so the engine starts with
    # a well-configured baseline instead of the bare minimum defaults.
    brain_core_service.seed_default_policies([1, 2])
    logger.info("brain_core default policies seeded for tenants [1, 2]")

    # Wire real DB-backed action handlers so Brain Core decisions produce tangible
    # side-effects (e.g. real intervention cases) instead of in-memory stubs.
    try:
        from app.modules.brain_core.action_bridge import wire_action_handlers

        wire_action_handlers(
            dispatcher=brain_core_service._dispatcher,
            session_factory=getattr(fastapi_app.state, "admissions_session_factory", None),
        )
    except Exception as _bridge_err:
        logger.warning("brain_core_action_bridge wiring failed: %s", _bridge_err)

    yield

    teardown_otel()
    # Release all pooled connections on shutdown.
    if _admissions_engine is not None:
        _admissions_engine.dispose()
        logger.info("admissions database engine disposed")


app = FastAPI(title="AI Engineering Backend", version="0.1.0", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(admin_local_users_router)
app.include_router(admissions_router)
app.include_router(ai_gateway_router)
app.include_router(ai_gateway_public_router)
app.include_router(brain_core_router)
app.include_router(profiles_router)
app.include_router(workflows_router)
app.include_router(rbac_router)
app.include_router(audit_router)
app.include_router(help_router)
app.include_router(i18n_public_router)
app.include_router(i18n_admin_router)
app.include_router(integrations_router)
app.include_router(identity_router)
app.include_router(identity_phase1_router)
app.include_router(ldap_router)
app.include_router(backup_router)
app.include_router(jobs_router)
app.include_router(feature_flags_router)
app.include_router(students_router)
app.include_router(service_accounts_router)
app.include_router(faculty_router)
app.include_router(programs_router)
app.include_router(courses_router)
app.include_router(enrollments_router)
app.include_router(grades_router)
app.include_router(scheduling_router)
app.include_router(thesis_router)
app.include_router(advising_router)
app.include_router(student_services_router)
app.include_router(career_services_router)
app.include_router(financial_aid_router)
app.include_router(budget_planning_router)
app.include_router(expense_controls_router)
app.include_router(security_operations_router)
app.include_router(transport_router)
app.include_router(dining_router)
app.include_router(campus_sla_router)
app.include_router(research_ethics_router)
app.include_router(ip_management_router)
app.include_router(equipment_booking_router)
app.include_router(room_booking_router)
app.include_router(access_control_router)
app.include_router(scholarship_router)
app.include_router(communications_router)
app.include_router(housing_router)
app.include_router(alumni_router)
app.include_router(research_router)
app.include_router(faculty_performance_kpis_router)
app.include_router(hr_payroll_router)
app.include_router(delinquency_collections_router)
app.include_router(facilities_work_orders_router)
app.include_router(asset_inventory_router)
app.include_router(faculty_copilot_router)
app.include_router(knowledge_retrieval_router)
app.include_router(prompt_management_router)
app.include_router(model_evaluation_router)
app.include_router(currency_localization_router)
app.include_router(operations_router)
app.include_router(student_life_router)
app.include_router(procurement_router)
app.include_router(syllabus_governance_router)
app.include_router(exam_governance_router)
app.include_router(teaching_quality_router)
app.include_router(academic_integrity_router)
app.include_router(accreditation_router)
app.include_router(pdpl_router)
app.include_router(interventions_router)
app.include_router(interventions_playbook_router)
app.include_router(interventions_risk_router)
app.include_router(interventions_effectiveness_router)
app.include_router(org_structure_router)
app.include_router(plans_router)
app.include_router(subscriptions_router)
app.include_router(analytics_router)
app.include_router(transcripts_router)
app.include_router(degree_progress_router)
app.include_router(academic_records_router)
app.include_router(tenants_router)
app.include_router(tenants_public_router)
app.include_router(platform_router)
app.include_router(platform_self_service_router)
app.include_router(platform_v1_admin_router)
app.include_router(platform_v1_public_router)
app.include_router(platform_developer_api_router)
app.include_router(platform_v1_internal_router)
app.include_router(platform_v1_mcp_router)
app.include_router(platform_v2_semantic_router)


def _register_optional_routers(fastapi_app: FastAPI) -> None:
    if is_billing_module_router_enabled():
        fastapi_app.include_router(billing_router)


_register_optional_routers(app)

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def _basic_database_reachable(app: FastAPI) -> bool:
    session_factory = getattr(app.state, "admissions_session_factory", None)
    if session_factory is None:
        return False
    try:
        with session_factory() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
_DEFAULT_TENANT_ID = 1


def _safe_metric_int(loader) -> int | None:
    try:
        value = loader()
    except Exception:
        return None
    return int(value)


def _collect_ops_metrics() -> dict[str, int | str | None]:
    with UnitOfWork() as uow:
        return {
            "event_queue_size": _safe_metric_int(lambda: uow.outbox_event_repository.count_backlog(conn=uow.conn)),
            "failed_webhooks": _safe_metric_int(lambda: uow.webhook_repository.count_failed_deliveries(conn=uow.conn)),
            "dead_webhooks": _safe_metric_int(lambda: uow.webhook_repository.count_dead_deliveries(conn=uow.conn)),
            "failed_automation_executions": _safe_metric_int(
                lambda: uow.automation_repository.count_failed_executions(conn=uow.conn)
            ),
            "dead_automation_executions": _safe_metric_int(
                lambda: uow.automation_repository.count_failed_executions(conn=uow.conn)
            ),
            "failed_jobs": _safe_metric_int(lambda: uow.job_repository.count_by_status("failed", conn=uow.conn)),
            "dead_jobs": _safe_metric_int(lambda: uow.job_repository.count_dead_jobs(conn=uow.conn)),
            "worker_last_heartbeat": get_worker_heartbeat(),
            "scheduler_last_run": get_scheduler_last_run(),
            "retry_backlog": _safe_metric_int(lambda: uow.webhook_repository.count_retry_backlog(conn=uow.conn)),
            "skills_total": _safe_metric_int(lambda: uow.education_graph_repository.count_skills(conn=uow.conn)),
            "course_skill_edges": _safe_metric_int(
                lambda: uow.education_graph_repository.count_course_skill_edges(conn=uow.conn)
            ),
            "student_skill_edges": _safe_metric_int(
                lambda: uow.education_graph_repository.count_student_skill_edges(conn=uow.conn)
            ),
        }


def _collect_latency_metrics() -> dict[str, float | int | None]:
    metrics: dict[str, float | int | None] = dict(snapshot_latency_metrics())
    try:
        with UnitOfWork() as uow:
            metrics["developer_api_error_count"] = int(uow.developer_repository.count_error_logs(conn=uow.conn))
    except Exception:
        metrics["developer_api_error_count"] = None
    return metrics


def _has_bearer_auth(request: Request) -> bool:
    authorization = request.headers.get("authorization", "")
    return authorization.startswith("Bearer ")


def _resolve_rate_limit_actor(request: Request) -> str | None:
    authorization = request.headers.get("authorization")
    try:
        claims = resolve_current_user_claims(request, authorization)
    except Exception:
        return None
    return claims.user_id


def _resolve_request_tenant_id(request: Request) -> int:
    """Resolve tenant_id for audit context. Trusts JWT; superadmin may override via X-Tenant-ID."""
    try:
        claims = parse_access_token_from_request(request, request.headers.get("authorization"))
    except TokenValidationError:
        claims = None
    if claims is not None and int(claims.tenant_id) > 0:
        token_tenant_id = int(claims.tenant_id)
        raw_header = request.headers.get("x-tenant-id", "").strip()
        if raw_header:
            try:
                header_tenant_id = int(raw_header)
                if header_tenant_id > 0 and header_tenant_id != token_tenant_id:
                    roles = {str(r).strip() for r in claims.roles if str(r).strip()}
                    if "superadmin" in roles:
                        return header_tenant_id
            except (TypeError, ValueError):
                pass
        return token_tenant_id
    return _DEFAULT_TENANT_ID


def _resolve_metrics_tenant_id(request: Request) -> int:
    """Resolve tenant_id for metrics labels. Trusts X-Tenant-ID header directly (observability only)."""
    raw_header = request.headers.get("x-tenant-id", "").strip()
    if raw_header:
        try:
            val = int(raw_header)
            if val > 0:
                return val
        except (TypeError, ValueError):
            pass
    return _resolve_request_tenant_id(request)
def _resolve_request_actor_id(request: Request) -> str | None:
    try:
        claims = parse_access_token_from_request(request, request.headers.get("authorization"))
    except TokenValidationError:
        claims = None
    if claims is not None and claims.user_id:
        return claims.user_id

    fallback_actor = request.headers.get("x-actor-id", "").strip()
    return fallback_actor or None


def _resolve_request_institution_id(request: Request) -> str | None:
    raw = request.headers.get("x-institution-id", "").strip()
    return raw or None


def _resolve_client_ip(request: Request) -> str:
    ip = request.headers.get("x-real-ip", "").strip()
    if ip:
        return ip
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for.strip():
        ips = [item.strip() for item in forwarded_for.split(",") if item.strip()]
        if ips:
            return ips[-1]
    return request.client.host if request.client else "unknown"


def _authorize_observability_permission(request: Request, permission: str) -> None:
    claims = resolve_current_user_claims(request, request.headers.get("authorization"))
    granted_scopes = {str(item).strip() for item in getattr(claims, "permissions", []) if str(item).strip()}
    if granted_scopes:
        if permission not in granted_scopes:
            raise HTTPException(status_code=403, detail=f"missing permission: {permission}")
        return

    if "superadmin" in {str(role).strip() for role in claims.roles if str(role).strip()}:
        return

    tenant_id = int(claims.tenant_id) if int(claims.tenant_id) > 0 else _DEFAULT_TENANT_ID
    granted = resolve_permissions_for_tenant(list(claims.roles), tenant_id)
    if permission not in granted:
        raise HTTPException(status_code=403, detail=f"missing permission: {permission}")


def _is_security_scoped_path(path: str) -> bool:
    return path.startswith("/api/") or path == "/platform" or path.startswith("/platform/")


def _is_admin_scoped_path(path: str) -> bool:
    return path.startswith("/api/admin/") or path == "/platform" or path.startswith("/platform/")


def _extract_error_code_from_response(response) -> str | None:
    body = getattr(response, "body", None)
    if not body:
        return None
    try:
        import json

        parsed = json.loads(body.decode("utf-8"))
    except Exception:
        return None
    if isinstance(parsed, dict):
        detail = parsed.get("detail")
        if isinstance(detail, dict) and isinstance(detail.get("code"), str):
            return str(detail.get("code"))
        if isinstance(parsed.get("code"), str):
            return str(parsed.get("code"))
    return None


@app.middleware("http")
async def enforce_rate_limit(request: Request, call_next):
    body = b""
    if request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"} and _is_security_scoped_path(request.url.path):
        body = await request.body()

    actor = None
    if _is_admin_scoped_path(request.url.path):
        actor = _resolve_rate_limit_actor(request)

    with perf_segment("middleware.rate_limit"):
        decision = check_request_rate_limit(request, actor=actor, body=body)
    if decision is not None:
        record_security_signal(
            signal="rate_limit.blocked",
            outcome="blocked",
            actor=actor,
            client_ip=_resolve_client_ip(request),
            path=request.url.path,
            tenant_id=_resolve_request_tenant_id(request),
        )
        if should_audit_rate_limit(request.url.path):
            log_admin_action(
                tenant_id=_resolve_request_tenant_id(request),
                actor=actor or "anonymous",
                action="rate_limit_exceeded",
                path=str(request.url.path),
                client_ip=request.client.host if request.client else "unknown",
                correlation_id=getattr(request.state, "request_id", None),
                entity="security_abuse",
                result="blocked",
                metadata=get_rate_limit_audit_metadata(request, decision, actor=actor),
            )
        return JSONResponse(
            status_code=429,
            content={"detail": f"rate limit exceeded; retry in {decision.retry_after}s"},
            headers={"Retry-After": str(decision.retry_after)},
        )

    with perf_segment("middleware.rate_limit.call_next"):
        return await call_next(request)


@app.middleware("http")
async def enforce_csrf(request: Request, call_next):
    with perf_segment("middleware.csrf"):
        if not is_csrf_protection_enabled():
            return await call_next(request)

        if request.method in SAFE_METHODS:
            return await call_next(request)

        if not _is_security_scoped_path(request.url.path):
            return await call_next(request)

        auth_cookie = request.cookies.get(get_auth_cookie_name())
        if not auth_cookie:
            return await call_next(request)

        # CSRF protection is scoped to cookie-authenticated requests only.
        if _has_bearer_auth(request):
            return await call_next(request)

        csrf_cookie = request.cookies.get(get_auth_csrf_cookie_name(), "")
        csrf_header = request.headers.get("x-csrf-token", "")
        if not csrf_cookie or not csrf_header:
            record_security_signal(
                signal="auth.csrf.failed",
                outcome="denied",
                actor=_resolve_rate_limit_actor(request),
                client_ip=_resolve_client_ip(request),
                path=request.url.path,
                tenant_id=_resolve_request_tenant_id(request),
            )
            return JSONResponse(status_code=403, content={"detail": "csrf token required"})
        if not hmac.compare_digest(csrf_cookie, csrf_header):
            record_security_signal(
                signal="auth.csrf.failed",
                outcome="denied",
                actor=_resolve_rate_limit_actor(request),
                client_ip=_resolve_client_ip(request),
                path=request.url.path,
                tenant_id=_resolve_request_tenant_id(request),
            )
            return JSONResponse(status_code=403, content={"detail": "invalid csrf token"})

        return await call_next(request)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    trace_id = request.headers.get("x-trace-id", generate_trace_id())
    tenant_id = _resolve_request_tenant_id(request)
    metrics_tenant_id = _resolve_metrics_tenant_id(request)
    actor_id = _resolve_request_actor_id(request)
    institution_id = _resolve_request_institution_id(request)
    request.state.request_id = request_id
    request.state.trace_id = trace_id
    request.state.correlation_id = request_id
    request.state.error_code = None
    # Propagate into logging context
    request_token = request_id_var.set(request_id)
    trace_log_token = trace_id_var.set(trace_id)
    tenant_log_token = tenant_id_var.set(str(tenant_id))
    actor_log_token = actor_id_var.set(actor_id or "-")
    institution_log_token = institution_id_var.set(institution_id or "-")
    tenant_token = set_request_tenant_id(tenant_id)
    start = time.monotonic()
    begin_request_profile(request.method, request.url.path)
    response = None
    status_code = 500
    try:
        with perf_segment("middleware.call_next"):
            response = await call_next(request)
        status_code = int(getattr(response, "status_code", 500))
        response.headers["x-request-id"] = request_id
        response.headers["x-trace-id"] = trace_id
        response.headers["x-correlation-id"] = request_id
        response.headers.setdefault("x-content-type-options", "nosniff")
        response.headers.setdefault("x-frame-options", "DENY")
        response.headers.setdefault("referrer-policy", "strict-origin-when-cross-origin")
        return response
    except Exception:
        duration = time.monotonic() - start
        with perf_segment("metrics.record_request"):
            record_request(request.method, request.url.path, status_code, duration, metrics_tenant_id)
        request_logger.exception(
            "http_request_error",
            extra={
                "method": request.method,
                "path": request.url.path,
                "endpoint": request.url.path,
                "status_code": status_code,
                "duration_ms": round(duration * 1000, 2),
                "tenant_id": str(tenant_id),
                "actor_id": actor_id or "-",
                "institution_id": institution_id or "-",
                "request_id": request_id,
                "trace_id": trace_id,
                "error_code": getattr(request.state, "error_code", None) or "internal_error",
            },
        )
        finish_request_profile(status_code, duration * 1000.0)
        raise
    finally:
        if response is not None:
            duration = time.monotonic() - start
            raw_path = request.url.path
            with perf_segment("metrics.record_request"):
                record_request(request.method, raw_path, status_code, duration, metrics_tenant_id)
            if raw_path.startswith("/api/") and int(tenant_id) > 0:
                _schedule_usage_event(int(tenant_id))
                try:
                    _emit_brain_module_activity_signal(
                        request=request,
                        status_code=status_code,
                        tenant_id=int(tenant_id),
                        correlation_id=request_id,
                    )
                except Exception:
                    # Brain signal wiring must never block request completion.
                    pass
            error_code = _extract_error_code_from_response(response)
            request.state.error_code = error_code
            with perf_segment("logging.request_log"):
                request_logger.info(
                    "http_request",
                    extra={
                        "method": request.method,
                        "path": raw_path,
                        "endpoint": raw_path,
                        "status_code": status_code,
                        "duration_ms": round(duration * 1000, 2),
                        "tenant_id": str(tenant_id),
                        "actor_id": actor_id or "-",
                        "user_id": actor_id or "-",
                        "institution_id": institution_id or "-",
                        "request_id": request_id,
                        "trace_id": trace_id,
                        "error_code": error_code,
                    },
                )
            finish_request_profile(status_code, duration * 1000.0)
        reset_request_tenant_id(tenant_token)
        institution_id_var.reset(institution_log_token)
        actor_id_var.reset(actor_log_token)
        tenant_id_var.reset(tenant_log_token)
        trace_id_var.reset(trace_log_token)
        request_id_var.reset(request_token)


@app.get("/health")
def health_root() -> dict[str, Any]:
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "service": "api"},
        headers={"X-Deprecated": "true"},
    )


@app.get("/health/live")
def health_live() -> dict[str, Any]:
    return live_payload()


@app.get("/api/health")
def api_health() -> dict[str, Any]:
    return live_payload()


@app.get("/health/db")
def health_db(
    request: Request,
    __: None = Depends(permission_dependency("health.read")),
):
    request_logger.warning(
        "deprecated_endpoint_used use /health/live,/health/ready,/health/deep",
        extra={
            "path": "/health/db",
            "method": "GET",
            "status_code": 200,
            "error_code": "deprecated_endpoint",
        },
    )
    if not _basic_database_reachable(request.app):
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "unreachable"},
            headers={"X-Deprecated": "true"},
        )
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "database": "reachable"},
        headers={"X-Deprecated": "true"},
    )


@app.get("/health/ready")
def health_ready(request: Request):
    payload = readiness_payload(request.app)
    lean_payload = {k: v for k, v in payload.items() if k != "dependencies"}
    if not payload["ready"]:
        return JSONResponse(status_code=503, content=lean_payload)
    return lean_payload


@app.get("/health/worker", response_model=None)
def health_worker(
    __: None = Depends(permission_dependency("health.read")),
) -> JSONResponse | dict[str, Any]:
    payload = deep_payload(app)
    worker = payload["dependencies"]["worker"]
    if not worker["healthy"]:
        if not is_worker_health_required():
            return {
                "status": "skipped",
                "worker": "out_of_scope",
                "required": "false",
                **worker["details"],
            }
        return JSONResponse(status_code=503, content={"status": "error", "worker": "unreachable", "details": worker["details"]})
    return {"status": "ok", "worker": "reachable", **worker["details"]}


@app.get("/metrics/ops")
def metrics_ops(
    __: None = Depends(permission_dependency("metrics.read")),
) -> dict[str, object]:
    return _collect_ops_metrics()


@app.get("/metrics/perf-profile")
def metrics_perf_profile(
    reset: bool = False,
    top_n: int = 5,
    __: None = Depends(permission_dependency("metrics.read")),
) -> dict[str, object]:
    summary = get_perf_profile_summary(top_n=max(1, min(int(top_n), 20)))
    if reset:
        reset_perf_profile()
    return summary


@app.get("/metrics/latency")
def metrics_latency(
    __: None = Depends(permission_dependency("metrics.read")),
) -> dict[str, float | int]:
    return _collect_latency_metrics()


@app.get("/health/deep")
def health_deep(
    request: Request,
    __: None = Depends(permission_dependency("health.read")),
):
    payload = deep_payload(request.app)
    if not payload["deep"]:
        return JSONResponse(status_code=503, content=payload)
    return payload


@app.get("/health/comprehensive")
def health_comprehensive(
    request: Request,
    __: None = Depends(permission_dependency("health.read")),
):
    return JSONResponse(
        status_code=200,
        content=comprehensive_payload(request.app),
        headers={"X-Deprecated": "true"},
    )


@app.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
def metrics(request: Request) -> str:
    """Prometheus text format metrics endpoint.

    Protected by METRICS_TOKEN bearer auth when the environment variable is set.
    In production, additionally restrict access at the reverse-proxy layer so
    this endpoint is only reachable from internal/monitoring network segments.
    """
    if is_production_mode():
        allowed_ips = get_metrics_allowed_ips()
        if allowed_ips:
            client_ip = request.headers.get("x-real-ip", "").strip()
            if not client_ip:
                client_ip = request.client.host if request.client else ""
            if client_ip not in allowed_ips:
                record_security_signal(
                    signal="metrics.access.denied",
                    outcome="denied",
                    client_ip=_resolve_client_ip(request),
                    path=request.url.path,
                    tenant_id=_resolve_request_tenant_id(request),
                )
                raise HTTPException(status_code=403, detail="metrics access forbidden from this IP")

    token = get_metrics_token()
    if token is not None:
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            record_security_signal(
                signal="metrics.access.denied",
                outcome="denied",
                client_ip=_resolve_client_ip(request),
                path=request.url.path,
                tenant_id=_resolve_request_tenant_id(request),
            )
            raise HTTPException(status_code=401, detail="metrics authentication required")
        provided = auth_header[len("Bearer "):]
        if not hmac.compare_digest(provided.encode(), token.encode()):
            try:
                _authorize_observability_permission(request, "metrics.read")
            except HTTPException:
                record_security_signal(
                    signal="metrics.access.denied",
                    outcome="denied",
                    client_ip=_resolve_client_ip(request),
                    path=request.url.path,
                    tenant_id=_resolve_request_tenant_id(request),
                )
                raise HTTPException(status_code=403, detail="invalid metrics token")
    else:
        _authorize_observability_permission(request, "metrics.read")
    return render_metrics()


@app.get("/api/meta")
def meta() -> dict[str, str]:
    return {
        "service": "backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "Use this as a starter API and extend domain modules.",
    }


@app.post("/api/admin/audit-test")
def admin_audit_test(
    request: Request,
    actor: str = Depends(get_actor),
) -> dict[str, str]:
    log_admin_action(
        actor=actor,
        action="audit_test",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="audit",
        result="success",
        metadata={"method": request.method},
    )

    return {"status": "logged", "actor": actor}
