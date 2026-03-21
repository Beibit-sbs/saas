from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.tenant import get_current_tenant
from app.modules.audit.service import log_admin_action
from app.modules.backup.service import (
    apply_retention_policy,
    get_backup_settings_for_admin,
    list_backup_history,
    list_restore_candidates,
    run_restore_now,
    save_backup_settings,
)
from app.modules.jobs.service import enqueue_job
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/backups", tags=["backups"])


class BackupProfilePayload(BaseModel):
    id: str = Field(min_length=2, max_length=64)
    label: str = Field(min_length=2, max_length=120)
    path: str = Field(min_length=1, max_length=500)


class BackupSettingsPayload(BaseModel):
    active_profile: str = Field(min_length=2, max_length=64)
    profiles: list[BackupProfilePayload]
    retention_days: int | None = Field(default=None, ge=0, le=3650)
    retention_min_files: int | None = Field(default=None, ge=0, le=1000)


class BackupRestorePayload(BaseModel):
    profile_id: str | None = Field(default=None, min_length=2, max_length=64)
    file_name: str | None = Field(default=None, min_length=1, max_length=255)
    dry_run: bool = True
    confirm_text: str | None = Field(default=None, max_length=32)


class BackupRetentionPayload(BaseModel):
    profile_id: str | None = Field(default=None, min_length=2, max_length=64)
    dry_run: bool = True


@router.get("/settings")
def get_backup_settings(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.backup.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, Any]:
    return get_backup_settings_for_admin(tenant_id=int(tenant["id"]))


@router.put("/settings")
def update_backup_settings(
    payload: BackupSettingsPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.backup.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, Any]:
    try:
        result = save_backup_settings(payload.model_dump(), tenant_id=int(tenant["id"]))
        log_admin_action(
            actor=actor,
            tenant_id=int(tenant["id"]),
            action="backup_settings_updated",
            path="/api/admin/backups/settings",
            client_ip=request.client.host if request.client else "unknown",
            correlation_id=getattr(request.state, "request_id", None),
            entity="backup_settings",
            result="success",
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/history")
def get_backup_history(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.backup.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, Any]:
    return {"jobs": list_backup_history(tenant_id=int(tenant["id"]))}


@router.get("/restore-candidates")
def get_restore_candidates(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.backup.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    profile_id: str | None = None,
) -> dict[str, Any]:
    try:
        return list_restore_candidates(profile_id=profile_id, tenant_id=int(tenant["id"]))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/restore")
def run_restore(
    payload: BackupRestorePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.backup.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, Any]:
    try:
        result = run_restore_now(
            actor=actor,
            profile_id=payload.profile_id,
            file_name=payload.file_name,
            dry_run=payload.dry_run,
            confirm_text=payload.confirm_text,
            tenant_id=int(tenant["id"]),
        )
        log_admin_action(
            actor=actor,
            tenant_id=int(tenant["id"]),
            action="backup_restore" if not payload.dry_run else "backup_restore_plan",
            path="/api/admin/backups/restore",
            client_ip=request.client.host if request.client else "unknown",
            correlation_id=getattr(request.state, "request_id", None),
            entity="backup_restore",
            result="success" if not payload.dry_run else "planned",
        )
        return {"job": result}
    except ValueError as exc:
        log_admin_action(
            actor=actor,
            tenant_id=int(tenant["id"]),
            action="backup_restore_failed",
            path="/api/admin/backups/restore",
            client_ip=request.client.host if request.client else "unknown",
            correlation_id=getattr(request.state, "request_id", None),
            entity="backup_restore",
            result="failed",
            metadata={"error": str(exc)},
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/retention/apply")
def apply_retention(
    payload: BackupRetentionPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.backup.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, Any]:
    try:
        result = apply_retention_policy(
            profile_id=payload.profile_id,
            dry_run=payload.dry_run,
            actor=actor,
            tenant_id=int(tenant["id"]),
        )
        log_admin_action(
            actor=actor,
            tenant_id=int(tenant["id"]),
            action="backup_retention_run" if not payload.dry_run else "backup_retention_plan",
            path="/api/admin/backups/retention/apply",
            client_ip=request.client.host if request.client else "unknown",
            correlation_id=getattr(request.state, "request_id", None),
            entity="backup_retention",
            result="success" if not payload.dry_run else "planned",
        )
        return {"job": result}
    except ValueError as exc:
        log_admin_action(
            actor=actor,
            tenant_id=int(tenant["id"]),
            action="backup_retention_failed",
            path="/api/admin/backups/retention/apply",
            client_ip=request.client.host if request.client else "unknown",
            correlation_id=getattr(request.state, "request_id", None),
            entity="backup_retention",
            result="failed",
            metadata={"error": str(exc)},
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/run")
def run_backup(
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.backup.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, Any]:
    try:
        result = enqueue_job(
            tenant_id=int(tenant["id"]),
            job_type="backup.run",
            payload={"source": "admin.backups.run"},
            created_by=actor,
            max_retries=3,
        )
        log_admin_action(
            actor=actor,
            tenant_id=int(tenant["id"]),
            action="backup_run",
            path="/api/admin/backups/run",
            client_ip=request.client.host if request.client else "unknown",
            correlation_id=getattr(request.state, "request_id", None),
            entity="backup_job",
            result="queued",
            metadata={"job_id": result.get("id"), "job_type": result.get("job_type")},
        )
        return {"job": result}
    except ValueError as exc:
        log_admin_action(
            actor=actor,
            tenant_id=int(tenant["id"]),
            action="backup_run_failed",
            path="/api/admin/backups/run",
            client_ip=request.client.host if request.client else "unknown",
            correlation_id=getattr(request.state, "request_id", None),
            entity="backup_job",
            result="failed",
            metadata={"error": str(exc)},
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
