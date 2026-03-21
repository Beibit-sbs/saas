from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.core.tenant import get_current_tenant
from app.modules.audit.service import log_admin_action
from app.modules.jobs.schemas import JobCreate, JobListResponse, JobResultResponse
from app.modules.jobs.service import (
    cancel_job,
    enqueue_job,
    get_job_for_tenant,
    list_jobs_for_tenant,
    retry_job,
)
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.rbac.service import is_platform_admin
from app.modules.tenants.service import get_tenant

router = APIRouter(prefix="/api/admin/jobs", tags=["jobs"])


def _is_platform_admin_request(request: Request, actor: str) -> bool:
    claims = getattr(request.state, "auth_claims", None)
    claim_roles = {r.strip() for r in getattr(claims, "roles", []) if str(r).strip()}
    return "superadmin" in claim_roles or is_platform_admin(actor)


def _resolve_target_tenant_id(
    request: Request,
    actor: str,
    tenant: dict[str, object],
    tenant_override: int | None,
) -> int:
    current_tenant_id = int(tenant["id"])
    if tenant_override is None:
        return current_tenant_id

    target = get_tenant(int(tenant_override))
    if target is None:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_override} not found")

    if not _is_platform_admin_request(request, actor):
        raise HTTPException(status_code=404, detail="job not found")

    return int(tenant_override)


@router.get("", response_model=JobListResponse)
def get_jobs(
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.jobs.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: str | None = Query(default=None),
    tenant_id: int | None = Query(default=None, gt=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> JobListResponse:
    target_tenant_id = _resolve_target_tenant_id(request, actor, tenant, tenant_id)
    rows = list_jobs_for_tenant(target_tenant_id, status=status, limit=limit)
    return JobListResponse(jobs=rows)


@router.get("/{job_id}", response_model=JobResultResponse)
def get_job(
    job_id: int,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.jobs.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    tenant_id: int | None = Query(default=None, gt=0),
) -> JobResultResponse:
    target_tenant_id = _resolve_target_tenant_id(request, actor, tenant, tenant_id)
    row = get_job_for_tenant(target_tenant_id, job_id)
    if row is None:
        raise HTTPException(status_code=404, detail="job not found")
    return JobResultResponse(job=row)


@router.post("", response_model=JobResultResponse)
def create_job(
    payload: JobCreate,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.jobs.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    tenant_id: int | None = Query(default=None, gt=0),
) -> JobResultResponse:
    target_tenant_id = _resolve_target_tenant_id(request, actor, tenant, tenant_id)
    try:
        row = enqueue_job(
            tenant_id=target_tenant_id,
            job_type=payload.job_type,
            payload=payload.payload,
            created_by=actor,
            max_retries=payload.max_retries,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        tenant_id=target_tenant_id,
        action="jobs.enqueue",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="jobs",
        result="success",
        metadata={"job_id": row["id"], "job_type": row["job_type"]},
    )
    return JobResultResponse(job=row)


@router.post("/{job_id}/retry", response_model=JobResultResponse)
def retry_job_endpoint(
    job_id: int,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.jobs.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    tenant_id: int | None = Query(default=None, gt=0),
) -> JobResultResponse:
    target_tenant_id = _resolve_target_tenant_id(request, actor, tenant, tenant_id)
    visible = get_job_for_tenant(target_tenant_id, job_id)
    if visible is None:
        raise HTTPException(status_code=404, detail="job not found")

    row = retry_job(job_id)
    if row is None:
        raise HTTPException(status_code=400, detail="job cannot be retried")

    log_admin_action(
        actor=actor,
        tenant_id=target_tenant_id,
        action="jobs.retry",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="jobs",
        result="success",
        metadata={"job_id": row["id"], "retry_count": row["retry_count"]},
    )
    return JobResultResponse(job=row)


@router.post("/{job_id}/cancel", response_model=JobResultResponse)
def cancel_job_endpoint(
    job_id: int,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.jobs.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    tenant_id: int | None = Query(default=None, gt=0),
) -> JobResultResponse:
    target_tenant_id = _resolve_target_tenant_id(request, actor, tenant, tenant_id)
    visible = get_job_for_tenant(target_tenant_id, job_id)
    if visible is None:
        raise HTTPException(status_code=404, detail="job not found")

    row = cancel_job(job_id)
    if row is None:
        raise HTTPException(status_code=400, detail="job cannot be cancelled")

    log_admin_action(
        actor=actor,
        tenant_id=target_tenant_id,
        action="jobs.cancel",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="jobs",
        result="success",
        metadata={"job_id": row["id"], "status": row["status"]},
    )
    return JobResultResponse(job=row)
