from __future__ import annotations

import json
import os

from app.demo_accounts import (
    DEMO_SUPERADMIN_LOGIN,
    demo_accounts_enabled,
    demo_accounts_password,
    get_tenant_demo_accounts,
)
from app.modules.auth.local_users_service import local_user_store
from app.modules.auth.platform_superadmin_service import ensure_platform_superadmin


def _read_bool_env(name: str, default: bool) -> bool:
    raw = str(os.getenv(name, "")).strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _read_env(name: str, default: str) -> str:
    value = str(os.getenv(name, default)).strip()
    if not value:
        raise RuntimeError(f"{name} is required for platform admin bootstrap")
    return value


def _is_placeholder_secret(value: str) -> bool:
    lowered = str(value).strip().lower()
    return lowered in {"change_me", "changeme", "replace_me", "example", "test", "secret", "!qaz1qaz"}


def _read_strong_password_env(name: str) -> str:
    value = str(os.getenv(name, "")).strip()
    if not value:
        raise RuntimeError(f"{name} must be explicitly configured")
    if len(value) < 12:
        raise RuntimeError(f"{name} must be at least 12 characters long")
    if _is_placeholder_secret(value):
        raise RuntimeError(f"{name} must not use placeholder/default values")
    return value


def ensure_platform_admin() -> dict[str, object]:
    login = _read_env("PLATFORM_ADMIN_LOGIN", "platform_admin")
    password = _read_strong_password_env("PLATFORM_ADMIN_PASSWORD")
    email = _read_env("PLATFORM_ADMIN_EMAIL", "platform_admin@platform.local")
    update_password = _read_bool_env("PLATFORM_ADMIN_UPDATE_PASSWORD", True)
    force_password_change = _read_bool_env("PLATFORM_ADMIN_FORCE_PASSWORD_CHANGE", False)

    result = ensure_platform_superadmin(
        login=login,
        password=password,
        email=email,
        update_password=update_password,
        force_password_change=force_password_change,
        actor="system.bootstrap",
    )

    user = local_user_store.find_user_by_login(login)
    if user is None:
        raise RuntimeError("platform admin bootstrap failed: user not found after upsert")

    if int(user.get("tenant_id", 0)) != 1:
        raise RuntimeError("platform admin bootstrap failed: tenant_id must be 1")

    roles = {str(role).strip() for role in user.get("roles", []) if str(role).strip()}
    if "superadmin" not in roles:
        raise RuntimeError("platform admin bootstrap failed: superadmin role is missing")

    return {
        "operation": result.get("operation", "unknown"),
        "login": login,
        "tenant_id": 1,
        "roles": sorted(roles),
    }


def _upsert_local_tenant_admin(
    *,
    tenant_id: int,
    login: str,
    password: str,
    display_name: str,
    update_password: bool,
) -> str:
    normalized_login = str(login).strip().lower()
    if not normalized_login:
        raise RuntimeError("LOCAL_TENANT_ADMIN_LOGINS contains an empty login")

    existing = local_user_store.find_user_by_login(normalized_login)
    if existing is None:
        local_user_store.create_user(
            login=normalized_login,
            password=password,
            display_name=display_name,
            roles=["admin"],
            default_language="ru",
            tenant_id=tenant_id,
            email=f"{normalized_login}@tenant.local",
        )
        return "created"

    existing_tenant = int(existing.get("tenant_id", 0))
    if existing_tenant != tenant_id:
        raise RuntimeError(
            f"LOCAL_TENANT_ADMIN_LOGINS login '{normalized_login}' belongs to tenant {existing_tenant}, expected tenant {tenant_id}"
        )

    local_user_store.update_user(
        str(existing.get("user_id", "")),
        tenant_id=tenant_id,
        display_name=display_name,
        roles=["admin"],
    )
    if update_password:
        local_user_store.set_password(str(existing.get("user_id", "")), password, tenant_id=tenant_id)
    return "updated"


def ensure_local_tenant_admins() -> dict[str, object]:
    enabled = _read_bool_env("LOCAL_TENANT_ADMIN_BOOTSTRAP_ENABLED", False)
    if not enabled:
        return {
            "enabled": False,
            "tenant_id": None,
            "logins": [],
            "results": [],
        }

    tenant_id_raw = _read_env("LOCAL_TENANT_ADMIN_TENANT_ID", "1")
    try:
        tenant_id = int(tenant_id_raw)
    except ValueError as exc:
        raise RuntimeError("LOCAL_TENANT_ADMIN_TENANT_ID must be an integer") from exc
    if tenant_id <= 0:
        raise RuntimeError("LOCAL_TENANT_ADMIN_TENANT_ID must be > 0")

    password = str(os.getenv("LOCAL_TENANT_ADMIN_PASSWORD", "")).strip()
    if len(password) < 6:
        raise RuntimeError("LOCAL_TENANT_ADMIN_PASSWORD must be at least 6 characters")

    raw_logins = str(os.getenv("LOCAL_TENANT_ADMIN_LOGINS", "inst_admin,acad_admin"))
    logins = [item.strip().lower() for item in raw_logins.split(",") if item.strip()]
    if not logins:
        raise RuntimeError("LOCAL_TENANT_ADMIN_LOGINS must contain at least one login")

    update_password = _read_bool_env("LOCAL_TENANT_ADMIN_UPDATE_PASSWORD", True)
    results: list[dict[str, str]] = []
    for index, login in enumerate(logins, start=1):
        result = _upsert_local_tenant_admin(
            tenant_id=tenant_id,
            login=login,
            password=password,
            display_name=f"Tenant Administrator {index}",
            update_password=update_password,
        )
        results.append({"login": login, "result": result})

    return {
        "enabled": True,
        "tenant_id": tenant_id,
        "logins": logins,
        "results": results,
    }


def _upsert_demo_tenant_user(
    *,
    tenant_id: int,
    login: str,
    password: str,
    display_name: str,
    role: str,
) -> str:
    normalized_login = str(login).strip().lower()
    if not normalized_login:
        raise RuntimeError("demo account login must not be empty")

    existing = local_user_store.find_user_by_login(normalized_login)
    if existing is None:
        local_user_store.create_user(
            login=normalized_login,
            password=password,
            display_name=display_name,
            roles=[role],
            default_language="ru",
            tenant_id=tenant_id,
            email=f"{normalized_login}@demo.local",
        )
        return "created"

    existing_tenant = int(existing.get("tenant_id", 0))
    if existing_tenant != tenant_id:
        raise RuntimeError(
            f"demo account login '{normalized_login}' belongs to tenant {existing_tenant}, expected tenant {tenant_id}"
        )

    local_user_store.update_user(
        str(existing.get("user_id", "")),
        tenant_id=tenant_id,
        display_name=display_name,
        roles=[role],
    )
    local_user_store.set_password(str(existing.get("user_id", "")), password, tenant_id=tenant_id)
    return "updated"


def ensure_demo_role_accounts() -> dict[str, object]:
    """Seed ready-made demo accounts for every platform role.

    Gated by ``DEMO_ROLE_ACCOUNTS_ENABLED`` (default disabled). Idempotent: safe
    to run on every startup. The platform superadmin demo account is provisioned
    as a real platform user; all other roles are tenant-scoped local users.
    """
    if not demo_accounts_enabled():
        return {"enabled": False, "results": []}

    password = demo_accounts_password()
    results: list[dict[str, str]] = []

    # Platform superadmin demo account (real platform user, tenant 1).
    superadmin_result = ensure_platform_superadmin(
        login=DEMO_SUPERADMIN_LOGIN,
        password=password,
        email=f"{DEMO_SUPERADMIN_LOGIN}@demo.local",
        update_password=True,
        force_password_change=False,
        actor="system.bootstrap.demo",
    )
    results.append({"login": DEMO_SUPERADMIN_LOGIN, "role": "superadmin", "result": str(superadmin_result.get("operation", "unknown"))})

    # Tenant-scoped demo accounts (one per role).
    for account in get_tenant_demo_accounts():
        result = _upsert_demo_tenant_user(
            tenant_id=int(account["tenant_id"]),
            login=str(account["login"]),
            password=str(account["password"]),
            display_name=str(account["display_name"]),
            role=str(account["role"]),
        )
        results.append({"login": str(account["login"]), "role": str(account["role"]), "result": result})

    return {"enabled": True, "results": results}


def main() -> int:
    payload = {
        "platform_admin": ensure_platform_admin(),
        "tenant_admins": ensure_local_tenant_admins(),
        "demo_role_accounts": ensure_demo_role_accounts(),
    }
    print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())