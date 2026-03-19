import os
import shutil
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends

from app.modules.audit.service import list_admin_actions
from app.modules.auth.local_users_service import local_user_store
from app.modules.backup.service import get_backup_settings_for_admin, list_backup_history
from app.modules.i18n.service import list_languages
from app.modules.integrations.service import get_ldap_config_for_admin, list_ai_provider_config_for_admin
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.rbac.service import list_roles, list_user_role_assignments

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/system/health")
def admin_system_health(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))],
) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    languages = list_languages(enabled_only=False)
    local_users = local_user_store.list_users()
    roles = list_roles()
    assignments = list_user_role_assignments()
    backup_jobs = list_backup_history()
    recent_audit_events = list_admin_actions(limit=50)

    total_bytes, used_bytes, free_bytes = shutil.disk_usage("/")
    usage_percent = round((used_bytes / total_bytes) * 100, 2) if total_bytes > 0 else 0.0

    load_1m, load_5m, load_15m = os.getloadavg()
    running_backup_jobs = sum(
        1
        for job in backup_jobs
        if str(job.get("status", "")).lower() in {"running", "in_progress", "planned", "queued"}
    )

    return {
        "status": "ok",
        "services": {
            "backend": "ok",
            "api": "ok",
            "metrics": "available",
        },
        "metrics": {
            "generated_at": now.isoformat(),
            "load_avg_1m": round(load_1m, 2),
            "load_avg_5m": round(load_5m, 2),
            "load_avg_15m": round(load_15m, 2),
            "local_users_count": len(local_users),
            "roles_count": len(roles),
            "assignments_count": len(assignments),
            "languages_count": len(languages),
        },
        "queues": {
            "backup_jobs_total": len(backup_jobs),
            "backup_jobs_running": running_backup_jobs,
            "audit_events_recent": len(recent_audit_events),
        },
        "disk": {
            "path": "/",
            "total_bytes": total_bytes,
            "used_bytes": used_bytes,
            "free_bytes": free_bytes,
            "usage_percent": usage_percent,
        },
    }


@router.get("/dashboard")
def admin_dashboard_meta(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))],
) -> dict[str, object]:
    languages = list_languages(enabled_only=False)
    local_users = local_user_store.list_users()
    roles = list_roles()
    assignments = list_user_role_assignments()
    ldap = get_ldap_config_for_admin()
    ai_providers = list_ai_provider_config_for_admin()
    backup_settings = get_backup_settings_for_admin()
    backup_jobs = list_backup_history()
    audit_events = list_admin_actions(limit=1)
    last_backup_job = backup_jobs[0] if backup_jobs else None
    last_audit_event = audit_events[0] if audit_events else None

    return {
        "dashboard": "university-core",
        "status": "ok",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "system": {
            "backend_health": "ok",
            "api_health": "ok",
            "metrics_available": True,
        },
        "users": {
            "local_users_count": len(local_users),
        },
        "rbac": {
            "roles_count": len(roles),
            "assignments_count": len(assignments),
        },
        "languages": {
            "total_count": len(languages),
            "enabled_count": sum(1 for item in languages if item.get("enabled")),
            "system_count": sum(1 for item in languages if item.get("system")),
        },
        "integrations": {
            "ldap": {
                "enabled": bool(ldap.get("enabled")),
                "configured": bool(ldap.get("has_bind_password")) and bool(ldap.get("server_uri")) and bool(ldap.get("base_dn")),
            },
            "ai_providers": {
                "total_count": len(ai_providers),
                "configured_count": sum(1 for item in ai_providers if item.get("configured")),
            },
        },
        "backups": {
            "active_profile": backup_settings.get("active_profile", ""),
            "profiles_count": len(backup_settings.get("profiles", [])),
            "last_job": last_backup_job,
        },
        "audit": {
            "recent_events_count": len(audit_events),
            "last_event": last_audit_event,
        },
    }
