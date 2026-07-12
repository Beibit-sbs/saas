"""Ready-made demo accounts for every platform role.

This module is the single source of truth for the optional demo accounts that
are seeded at startup and surfaced on the login page. It is intentionally
side-effect free (pure configuration + env parsing) so it can be imported by
both the bootstrap routine and the public login endpoint.

Everything here is gated by ``DEMO_ROLE_ACCOUNTS_ENABLED`` (default: disabled),
so production deployments never seed or expose these accounts unless the flag is
explicitly turned on for a demo/pilot environment.
"""

from __future__ import annotations

import os

DEMO_ACCOUNTS_TENANT_ID_DEFAULT = 1
DEMO_ACCOUNTS_PASSWORD_DEFAULT = "DemoPassword123!"

# Login used for the seeded platform superadmin demo account.
DEMO_SUPERADMIN_LOGIN = "demo_superadmin"

# Tenant-scoped demo accounts: (role, login, display_name).
# The platform ``superadmin`` role is handled separately because it must be
# provisioned as a real platform user, not a tenant-scoped local user.
_DEMO_TENANT_ACCOUNTS: tuple[tuple[str, str, str], ...] = (
    ("admin", "demo_admin", "Demo Tenant Administrator"),
    ("auditor", "demo_auditor", "Demo Auditor"),
    ("dean", "demo_dean", "Demo Dean Office"),
    ("teacher", "demo_teacher", "Demo Teacher"),
    ("student", "demo_student", "Demo Student"),
    ("faculty", "demo_faculty", "Demo Faculty Portal"),
    ("registrar", "demo_registrar", "Demo Registrar Portal"),
)


def demo_accounts_enabled() -> bool:
    """Whether demo role accounts should be seeded and exposed."""
    raw = str(os.getenv("DEMO_ROLE_ACCOUNTS_ENABLED", "")).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def demo_accounts_tenant_id() -> int:
    """Tenant id used for the tenant-scoped demo accounts."""
    raw = str(os.getenv("DEMO_ROLE_ACCOUNTS_TENANT_ID", str(DEMO_ACCOUNTS_TENANT_ID_DEFAULT))).strip()
    try:
        tenant_id = int(raw)
    except ValueError:
        return DEMO_ACCOUNTS_TENANT_ID_DEFAULT
    return tenant_id if tenant_id > 0 else DEMO_ACCOUNTS_TENANT_ID_DEFAULT


def demo_accounts_password() -> str:
    """Shared password for all demo accounts."""
    value = str(os.getenv("DEMO_ROLE_ACCOUNTS_PASSWORD", "")).strip()
    return value or DEMO_ACCOUNTS_PASSWORD_DEFAULT


def get_tenant_demo_accounts() -> list[dict[str, object]]:
    """Tenant-scoped demo accounts to seed as local users."""
    tenant_id = demo_accounts_tenant_id()
    password = demo_accounts_password()
    return [
        {
            "role": role,
            "login": login,
            "display_name": display_name,
            "tenant_id": tenant_id,
            "password": password,
        }
        for (role, login, display_name) in _DEMO_TENANT_ACCOUNTS
    ]


def get_public_demo_accounts() -> list[dict[str, object]]:
    """Demo accounts surfaced on the login page for one-click sign-in.

    The ``login`` field is the value that should be typed into the login form.
    The superadmin entry uses the ``local/`` prefix so the frontend treats it as
    a platform-administrator sign-in (no tenant binding required).
    """
    password = demo_accounts_password()
    tenant_id = demo_accounts_tenant_id()

    accounts: list[dict[str, object]] = [
        {
            "role": "superadmin",
            "label": "Platform Superadmin",
            "login": f"local/{DEMO_SUPERADMIN_LOGIN}",
            "password": password,
            "tenant_id": 1,
            "is_platform_admin": True,
        }
    ]
    for account in get_tenant_demo_accounts():
        accounts.append(
            {
                "role": account["role"],
                "label": str(account["display_name"]),
                "login": account["login"],
                "password": password,
                "tenant_id": account["tenant_id"],
                "is_platform_admin": False,
            }
        )
    return accounts
