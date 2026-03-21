from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from app.modules.audit.service import log_admin_action
from app.modules.backup.service import save_backup_settings
from app.modules.feature_flags.service import list_flags
from app.modules.integrations.service import save_setting
from app.modules.plans.service import get_plan_by_code
from app.modules.rbac.service import BASELINE_ROLE_PERMISSIONS, add_or_update_role_for_tenant
from app.modules.tenants.service import create_tenant, force_delete_tenant, get_tenant_by_slug

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized[:120] if normalized else "tenant"


def _db_url() -> str | None:
    return os.getenv("DATABASE_URL")


def _use_database() -> bool:
    return bool(_db_url()) and psycopg is not None


@dataclass
class ProvisioningResult:
    tenant: dict[str, object]
    plan: dict[str, object]


class TenantProvisioningService:
    @staticmethod
    def create_tenant_with_defaults(
        *,
        tenant_name: str,
        admin_email: str,
        plan_code: str,
        actor: str,
    ) -> dict[str, object]:
        normalized_name = tenant_name.strip()
        normalized_email = admin_email.strip().lower()
        normalized_plan_code = plan_code.strip().lower()

        if not normalized_name:
            raise ValueError("tenant_name is required")
        if not normalized_email:
            raise ValueError("admin_email is required")

        plan = get_plan_by_code(normalized_plan_code)
        if plan is None:
            raise ValueError("plan not found")

        base_slug = _slugify(normalized_name)
        slug = base_slug
        suffix = 1
        while get_tenant_by_slug(slug) is not None:
            suffix += 1
            slug = f"{base_slug}-{suffix}"

        tenant = create_tenant(
            {
                "slug": slug,
                "name": normalized_name,
                "status": "active",
                "plan_id": int(plan["id"]),
            }
        )
        tenant_id = int(tenant["id"])

        try:
            add_or_update_role_for_tenant(
                tenant_id,
                "admin",
                sorted(BASELINE_ROLE_PERMISSIONS.get("admin", set())),
            )

            # Seed feature flags storage for the tenant.
            list_flags(tenant_id=tenant_id)

            # Seed integration settings.
            save_setting("ldap.enabled", "false", is_secret=False, tenant_id=tenant_id)

            # Seed backup settings with tenant-scoped profile path.
            backup_root = Path(f"/tmp/app-backups/tenant-{tenant_id}").resolve()
            save_backup_settings(
                {
                    "active_profile": "local",
                    "profiles": [
                        {
                            "id": "local",
                            "label": "Local backup volume",
                            "path": str(backup_root),
                        }
                    ],
                    "retention_days": 14,
                    "retention_min_files": 3,
                },
                tenant_id=tenant_id,
            )

            log_admin_action(
                tenant_id=tenant_id,
                actor=actor,
                action="platform.tenants.provision",
                path="/platform/tenants",
                client_ip="platform",
                entity="app_tenants",
                result="success",
                metadata={
                    "tenant_id": tenant_id,
                    "tenant_slug": tenant.get("slug"),
                    "plan_code": plan.get("code"),
                    "admin_email": normalized_email,
                },
            )
        except Exception:
            force_delete_tenant(tenant_id)
            raise

        return {
            "tenant": tenant,
            "plan": plan,
        }
