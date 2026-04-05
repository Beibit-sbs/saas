from __future__ import annotations

import json
import os

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


def main() -> int:
    payload = ensure_platform_admin()
    print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())