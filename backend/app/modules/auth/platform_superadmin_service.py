from __future__ import annotations

from typing import Any

from app.modules.audit.service import log_admin_action
from app.modules.auth.local_users_service import local_user_store
from app.modules.rbac.service import sync_user_roles_from_trusted_source


PLATFORM_TENANT_ID = 1
PLATFORM_SCOPE = "platform"
PLATFORM_SUPERADMIN_ROLE = "superadmin"


def ensure_platform_superadmin(
    *,
    login: str,
    password: str,
    email: str | None = None,
    update_password: bool = False,
    force_password_change: bool = False,
    actor: str = "system.management",
) -> dict[str, Any]:
    result = local_user_store.upsert_platform_superadmin(
        login=login,
        password=password,
        platform_tenant_id=PLATFORM_TENANT_ID,
        email=email,
        update_password=update_password,
        force_password_change=force_password_change,
    )
    user = result["user"]
    user_id = str(user["user_id"])

    sync_user_roles_from_trusted_source(
        user_id=user_id,
        roles=[PLATFORM_SUPERADMIN_ROLE],
        tenant_id=PLATFORM_TENANT_ID,
    )

    log_admin_action(
        actor=actor,
        action="platform.superadmin.ensure",
        entity="identity",
        path="cli:create_platform_superadmin",
        client_ip="10.0.0.1",
        tenant_id=PLATFORM_TENANT_ID,
        result="success",
        metadata={
            "operation": result["operation"],
            "user_id": user_id,
            "login": str(user.get("login", "")),
            "email": str(user.get("email", "")),
            "account_scope": PLATFORM_SCOPE,
            "is_platform_user": True,
            "role": PLATFORM_SUPERADMIN_ROLE,
            "password_updated": bool(update_password),
            "force_password_change": bool(force_password_change),
        },
    )

    return {
        "operation": result["operation"],
        "tenant_id": PLATFORM_TENANT_ID,
        "role": PLATFORM_SUPERADMIN_ROLE,
        "user": user,
    }
