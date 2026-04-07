from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.platform.repository.db import db_available, transaction

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


class TenantRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._memory_tenants: dict[int, dict[str, Any]] = {
            1: {"id": 1, "slug": "default", "name": "Default Organization", "status": "active"}
        }
        self._memory_profiles: dict[int, dict[str, Any]] = {}
        self._memory_counter = 1

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _profile_from(self, tenant: dict[str, Any], profile: dict[str, Any] | None) -> dict[str, Any]:
        profile = profile or {}
        suspended = bool(profile.get("suspended", False))
        status = str(profile.get("status") or tenant.get("status") or "active")
        return {
            "tenant_id": int(tenant["id"]),
            "slug": str(tenant["slug"]),
            "name": str(tenant["name"]),
            "status": status,
            "suspended": suspended,
            "settings": dict(profile.get("settings", {})),
            "quotas": {str(k): int(v) for k, v in dict(profile.get("quotas", {})).items()},
            "limits": {str(k): int(v) for k, v in dict(profile.get("limits", {})).items()},
            "updated_at": str(profile.get("updated_at") or self._now_iso()),
        }

    def _ensure_profile_row_db(self, conn: object, tenant_id: int) -> None:
        if psycopg is None:
            return
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_platform_tenant_settings (tenant_id, status, settings_json, quotas_json, limits_json, updated_at)
                VALUES (%s, 'active', '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, NOW())
                ON CONFLICT (tenant_id) DO NOTHING
                """,
                (tenant_id,),
            )

    def _get_profile_db(self, conn: object, tenant_id: int) -> dict[str, Any] | None:
        if psycopg is None:
            return None
        with conn.cursor() as cur:
            self._ensure_profile_row_db(conn, tenant_id)
            cur.execute(
                """
                SELECT t.id, t.slug, t.name, t.status,
                       s.status, s.settings_json, s.quotas_json, s.limits_json, s.updated_at
                FROM app_tenants t
                LEFT JOIN app_platform_tenant_settings s ON s.tenant_id = t.id
                WHERE t.id = %s
                """,
                (tenant_id,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        tenant = {"id": row[0], "slug": row[1], "name": row[2], "status": row[3]}
        profile = {
            "status": row[4] or row[3],
            "settings": row[5] or {},
            "quotas": row[6] or {},
            "limits": row[7] or {},
            "updated_at": row[8].isoformat() if hasattr(row[8], "isoformat") else str(row[8]),
            "suspended": str(row[4] or row[3]).lower() == "suspended",
        }
        return self._profile_from(tenant, profile)

    def create_tenant(self, slug: str, name: str, *, conn: object | None = None) -> dict[str, Any]:
        normalized_slug = str(slug).strip().lower()
        normalized_name = str(name).strip()
        if not normalized_slug or not normalized_name:
            raise ValueError("slug and name are required")

        if conn is None:
            with transaction() as tx:
                return self.create_tenant(normalized_slug, normalized_name, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT setval(pg_get_serial_sequence('app_tenants', 'id'), COALESCE((SELECT MAX(id) FROM app_tenants), 1), true)"
                )
                cur.execute(
                    """
                    INSERT INTO app_tenants (slug, name, status, plan_id, created_at, updated_at)
                    VALUES (%s, %s, 'active', 1, NOW(), NOW())
                    RETURNING id
                    """,
                    (normalized_slug, normalized_name),
                )
                tenant_id = int(cur.fetchone()[0])
            self._ensure_profile_row_db(conn, tenant_id)
            row = self._get_profile_db(conn, tenant_id)
            if row is None:
                raise ValueError("failed to load tenant profile")
            return row

        with self._lock:
            for item in self._memory_tenants.values():
                if str(item["slug"]) == normalized_slug:
                    raise ValueError(f"Tenant with slug '{normalized_slug}' already exists")
            self._memory_counter += 1
            tenant_id = self._memory_counter
            self._memory_tenants[tenant_id] = {
                "id": tenant_id,
                "slug": normalized_slug,
                "name": normalized_name,
                "status": "active",
            }
            self._memory_profiles.setdefault(
                tenant_id,
                {
                    "status": "active",
                    "settings": {},
                    "quotas": {},
                    "limits": {},
                    "updated_at": self._now_iso(),
                    "suspended": False,
                },
            )
            return self._profile_from(self._memory_tenants[tenant_id], self._memory_profiles[tenant_id])

    def get_tenant_profile(self, tenant_id: int, *, conn: object | None = None) -> dict[str, Any]:
        normalized_tenant_id = int(tenant_id)
        if normalized_tenant_id <= 0:
            raise ValueError("tenant_id must be positive")

        if conn is None:
            with transaction() as tx:
                return self.get_tenant_profile(normalized_tenant_id, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            row = self._get_profile_db(conn, normalized_tenant_id)
            if row is None:
                raise ValueError(f"Tenant {normalized_tenant_id} not found")
            return row

        with self._lock:
            tenant = self._memory_tenants.get(normalized_tenant_id)
            if tenant is None:
                raise ValueError(f"Tenant {normalized_tenant_id} not found")
            profile = self._memory_profiles.setdefault(
                normalized_tenant_id,
                {
                    "status": str(tenant.get("status", "active")),
                    "settings": {},
                    "quotas": {},
                    "limits": {},
                    "updated_at": self._now_iso(),
                    "suspended": False,
                },
            )
            return self._profile_from(tenant, profile)

    def list_tenant_profiles(self, *, conn: object | None = None) -> list[dict[str, Any]]:
        if conn is None:
            with transaction() as tx:
                return self.list_tenant_profiles(conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM app_tenants ORDER BY id")
                ids = [int(row[0]) for row in cur.fetchall()]
            return [self.get_tenant_profile(item, conn=conn) for item in ids]

        with self._lock:
            ids = sorted(int(item) for item in self._memory_tenants.keys())
        return [self.get_tenant_profile(item, conn=conn) for item in ids]

    def patch_settings(self, tenant_id: int, settings: dict[str, Any], *, conn: object | None = None) -> dict[str, Any]:
        if conn is None:
            with transaction() as tx:
                return self.patch_settings(tenant_id, settings, conn=tx)

        profile = self.get_tenant_profile(tenant_id, conn=conn)
        merged = dict(profile.get("settings", {}))
        merged.update(dict(settings))

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE app_platform_tenant_settings
                    SET settings_json = %s::jsonb,
                        updated_at = NOW()
                    WHERE tenant_id = %s
                    """,
                    (psycopg.types.json.Jsonb(merged), int(tenant_id)),
                )
            return self.get_tenant_profile(int(tenant_id), conn=conn)

        with self._lock:
            row = self._memory_profiles.setdefault(
                int(tenant_id),
                {"status": "active", "settings": {}, "quotas": {}, "limits": {}, "updated_at": self._now_iso(), "suspended": False},
            )
            row["settings"] = merged
            row["updated_at"] = self._now_iso()
        return self.get_tenant_profile(int(tenant_id), conn=conn)

    def set_quotas(self, tenant_id: int, quotas: dict[str, int], *, conn: object | None = None) -> dict[str, Any]:
        normalized = {str(k): int(v) for k, v in quotas.items()}
        if conn is None:
            with transaction() as tx:
                return self.set_quotas(tenant_id, normalized, conn=tx)

        self.get_tenant_profile(tenant_id, conn=conn)
        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE app_platform_tenant_settings SET quotas_json = %s::jsonb, updated_at = NOW() WHERE tenant_id = %s",
                    (psycopg.types.json.Jsonb(normalized), int(tenant_id)),
                )
            return self.get_tenant_profile(int(tenant_id), conn=conn)

        with self._lock:
            row = self._memory_profiles.setdefault(
                int(tenant_id),
                {"status": "active", "settings": {}, "quotas": {}, "limits": {}, "updated_at": self._now_iso(), "suspended": False},
            )
            row["quotas"] = normalized
            row["updated_at"] = self._now_iso()
        return self.get_tenant_profile(int(tenant_id), conn=conn)

    def set_limits(self, tenant_id: int, limits: dict[str, int], *, conn: object | None = None) -> dict[str, Any]:
        normalized = {str(k): int(v) for k, v in limits.items()}
        if conn is None:
            with transaction() as tx:
                return self.set_limits(tenant_id, normalized, conn=tx)

        self.get_tenant_profile(tenant_id, conn=conn)
        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE app_platform_tenant_settings SET limits_json = %s::jsonb, updated_at = NOW() WHERE tenant_id = %s",
                    (psycopg.types.json.Jsonb(normalized), int(tenant_id)),
                )
            return self.get_tenant_profile(int(tenant_id), conn=conn)

        with self._lock:
            row = self._memory_profiles.setdefault(
                int(tenant_id),
                {"status": "active", "settings": {}, "quotas": {}, "limits": {}, "updated_at": self._now_iso(), "suspended": False},
            )
            row["limits"] = normalized
            row["updated_at"] = self._now_iso()
        return self.get_tenant_profile(int(tenant_id), conn=conn)

    def set_suspended(self, tenant_id: int, suspended: bool, *, conn: object | None = None) -> dict[str, Any]:
        if conn is None:
            with transaction() as tx:
                return self.set_suspended(tenant_id, suspended, conn=tx)

        next_status = "suspended" if bool(suspended) else "active"
        self.get_tenant_profile(tenant_id, conn=conn)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute("UPDATE app_tenants SET status = %s, updated_at = NOW() WHERE id = %s", ("inactive" if suspended else "active", int(tenant_id)))
                cur.execute(
                    "UPDATE app_platform_tenant_settings SET status = %s, updated_at = NOW() WHERE tenant_id = %s",
                    (next_status, int(tenant_id)),
                )
            return self.get_tenant_profile(int(tenant_id), conn=conn)

        with self._lock:
            tenant = self._memory_tenants.get(int(tenant_id))
            if tenant is None:
                raise ValueError(f"Tenant {tenant_id} not found")
            tenant["status"] = "inactive" if suspended else "active"
            row = self._memory_profiles.setdefault(
                int(tenant_id),
                {"status": "active", "settings": {}, "quotas": {}, "limits": {}, "updated_at": self._now_iso(), "suspended": False},
            )
            row["status"] = next_status
            row["suspended"] = bool(suspended)
            row["updated_at"] = self._now_iso()
        return self.get_tenant_profile(int(tenant_id), conn=conn)
