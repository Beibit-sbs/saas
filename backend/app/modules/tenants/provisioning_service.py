from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from app.modules.audit.service import log_admin_action
from app.modules.billing.service import ensure_tenant_subscription
from app.modules.backup.service import save_backup_settings
from app.modules.feature_flags.service import list_flags
from app.modules.integrations.service import save_setting
from app.modules.plans.service import get_plan_by_code
from app.modules.rbac.service import BASELINE_ROLE_PERMISSIONS, add_or_update_role_for_tenant
from app.modules.tenants.service import create_tenant, force_delete_tenant, get_tenant_by_slug
from app.core.db import get_raw_conn

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
    def derive_tenant_slug(tenant_name: str) -> str:
        normalized_name = tenant_name.strip()
        if not normalized_name:
            raise ValueError("tenant_name is required")
        return _slugify(normalized_name)

    @staticmethod
    def create_tenant_with_defaults(
        *,
        tenant_name: str,
        admin_email: str,
        plan_code: str,
        actor: str,
        slug: str | None = None,
        allow_existing_slug: bool = False,
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

        normalized_slug = _slugify(str(slug or normalized_name))
        existing_tenant = get_tenant_by_slug(normalized_slug)
        created_new_tenant = False

        if existing_tenant is not None:
            if not allow_existing_slug:
                raise ValueError(f"tenant slug '{normalized_slug}' already exists")
            tenant = existing_tenant
        else:
            tenant = create_tenant(
                {
                    "slug": normalized_slug,
                    "name": normalized_name,
                    "status": "active",
                    "plan_id": int(plan["id"]),
                }
            )
            created_new_tenant = True
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

            ensure_tenant_subscription(
                tenant_id,
                plan_code=str(plan.get("code", "free")),
                status="trial",
            )

            # Bootstrap root OrgUnit for the new tenant (idempotent).
            _bootstrap_org_unit_root(tenant_id, normalized_name)

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
            if created_new_tenant:
                force_delete_tenant(tenant_id)
            raise

        return {
            "tenant": tenant,
            "plan": plan,
        }


def _bootstrap_org_unit_root(tenant_id: int, tenant_name: str) -> None:
    """Insert the root 'university' OrgUnit for a new tenant. Idempotent."""
    with get_raw_conn() as conn:
        if conn is None:
            return
        existing = conn.execute(
            """
            SELECT id FROM app_org_org_units
            WHERE tenant_id = %s AND unit_type = 'university' AND parent_unit_id IS NULL
            LIMIT 1
            """,
            (tenant_id,),
        ).fetchone()
        if existing:
            conn.commit()
            return
        conn.execute(
            """
            INSERT INTO app_org_org_units
                (tenant_id, name, code, unit_type, parent_unit_id, active, created_at, updated_at)
            VALUES
                (%s, %s, 'ROOT', 'university', NULL, true, NOW(), NOW())
            """,
            (tenant_id, tenant_name),
        )
        conn.commit()
