from datetime import datetime, timezone
from contextlib import asynccontextmanager
import hmac
import logging
import time
import uuid

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.responses import PlainTextResponse

from app.core.config import (
    get_auth_cookie_name,
    get_auth_csrf_cookie_name,
    is_csrf_protection_enabled,
)

from app.modules.admin.router import router as admin_router
from app.modules.admin.local_users_router import router as admin_local_users_router
from app.modules.academic_records.router import router as academic_records_router
from app.modules.ai_gateway.router import router as ai_gateway_router
from app.modules.ai_gateway.public_router import router as ai_gateway_public_router
from app.modules.audit.router import router as audit_router
from app.modules.audit.service import log_admin_action, reset_request_tenant_id, set_request_tenant_id
from app.modules.backup.router import router as backup_router
from app.modules.courses.router import router as courses_router
from app.modules.enrollments.router import router as enrollments_router
from app.modules.example_notes.router import router as example_notes_router
from app.modules.example_slice.router import router as example_slice_router
from app.modules.faculty.router import router as faculty_router
from app.modules.feature_flags.router import router as feature_flags_router
from app.modules.auth.router import router as auth_router
from app.modules.help.router import router as help_router
from app.modules.i18n.router import admin_router as i18n_admin_router
from app.modules.i18n.router import public_router as i18n_public_router
from app.modules.integrations.router import router as integrations_router
from app.modules.ldap.router import router as ldap_router
from app.modules.jobs.router import router as jobs_router
from app.modules.programs.router import router as programs_router
from app.modules.platform.router import router as platform_router
from app.modules.rbac.router import router as rbac_router
from app.modules.rbac.security import get_actor
from app.modules.rbac.security import resolve_current_user_claims
from app.modules.students.router import router as students_router
from app.modules.tenants.router import router as tenants_router
from app.modules.observability.logging import configure_json_logging, request_id_var
from app.modules.observability.metrics import record_request, render_metrics
from app.modules.security.rate_limit import (
    check_request_rate_limit,
    get_rate_limit_audit_metadata,
    should_audit_rate_limit,
)

configure_json_logging()
logger = logging.getLogger("app.audit")
request_logger = logging.getLogger("app.request")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Re-apply on process startup so third-party logger setup doesn't override JSON handlers.
    configure_json_logging()
    yield


app = FastAPI(title="AI Engineering Backend", version="0.1.0", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(admin_local_users_router)
app.include_router(ai_gateway_router)
app.include_router(ai_gateway_public_router)
app.include_router(rbac_router)
app.include_router(audit_router)
app.include_router(help_router)
app.include_router(i18n_public_router)
app.include_router(i18n_admin_router)
app.include_router(integrations_router)
app.include_router(ldap_router)
app.include_router(backup_router)
app.include_router(jobs_router)
app.include_router(feature_flags_router)
app.include_router(example_notes_router)
app.include_router(example_slice_router)
app.include_router(students_router)
app.include_router(faculty_router)
app.include_router(programs_router)
app.include_router(courses_router)
app.include_router(enrollments_router)
app.include_router(academic_records_router)
app.include_router(tenants_router)
app.include_router(platform_router)

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
_DEFAULT_TENANT_ID = 1


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
    raw = request.headers.get("x-tenant-id")
    if raw is None:
        return _DEFAULT_TENANT_ID
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return _DEFAULT_TENANT_ID
    return value if value > 0 else _DEFAULT_TENANT_ID


@app.middleware("http")
async def enforce_rate_limit(request: Request, call_next):
    body = b""
    if request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path.startswith("/api/"):
        body = await request.body()

    actor = None
    if request.url.path.startswith("/api/admin/"):
        actor = _resolve_rate_limit_actor(request)

    decision = check_request_rate_limit(request, actor=actor, body=body)
    if decision is not None:
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

    return await call_next(request)


@app.middleware("http")
async def enforce_csrf(request: Request, call_next):
    if not is_csrf_protection_enabled():
        return await call_next(request)

    if request.method in SAFE_METHODS:
        return await call_next(request)

    if not request.url.path.startswith("/api/"):
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
        return JSONResponse(status_code=403, content={"detail": "csrf token required"})
    if not hmac.compare_digest(csrf_cookie, csrf_header):
        return JSONResponse(status_code=403, content={"detail": "invalid csrf token"})

    return await call_next(request)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = request_id
    # Propagate into logging context
    token = request_id_var.set(request_id)
    tenant_token = set_request_tenant_id(_resolve_request_tenant_id(request))
    start = time.monotonic()
    response = None
    try:
        response = await call_next(request)
    finally:
        duration = time.monotonic() - start
        status = getattr(response, "status_code", 0)
        raw_path = request.url.path
        record_request(request.method, raw_path, status, duration)
        request_logger.info(
            "http_request",
            extra={
                "method": request.method,
                "path": raw_path,
                "status": status,
                "duration_ms": round(duration * 1000, 2),
            },
        )
        reset_request_tenant_id(tenant_token)
        request_id_var.reset(token)
    response.headers["x-request-id"] = request_id
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/health")
def api_health() -> dict[str, str]:
    return health()


@app.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
def metrics() -> str:
    """Prometheus text format metrics endpoint."""
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
