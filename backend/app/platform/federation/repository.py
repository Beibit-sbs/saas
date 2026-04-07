from __future__ import annotations

import json
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.platform.repository.db import db_available, transaction

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


class FederationRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._institutions: dict[int, dict[str, Any]] = {}
        self._members: dict[int, dict[str, Any]] = {}
        self._inst_counter = 0
        self._member_counter = 0

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def clear_state(self, *, conn: object | None = None) -> None:
        if conn is None:
            with transaction() as tx:
                self.clear_state(conn=tx)
                return

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM app_platform_federation_members")
                cur.execute("UPDATE app_tenants SET institution_id = NULL")
                cur.execute("DELETE FROM app_platform_institutions")
            return

        with self._lock:
            self._institutions.clear()
            self._members.clear()
            self._inst_counter = 0
            self._member_counter = 0

    # ------------------------------------------------------------------
    # Institutions
    # ------------------------------------------------------------------

    def create_institution(
        self,
        *,
        name: str,
        code: str,
        country: str,
        inst_type: str,
        metadata_json: dict[str, Any],
        conn: object | None = None,
    ) -> dict[str, Any]:
        if conn is None:
            with transaction() as tx:
                return self.create_institution(
                    name=name,
                    code=code,
                    country=country,
                    inst_type=inst_type,
                    metadata_json=metadata_json,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_institutions (name, code, country, type, status, metadata_json)
                    VALUES (%s, %s, %s, %s, 'active', %s)
                    RETURNING id, name, code, country, type, status, metadata_json, created_at, updated_at
                    """,
                    (name, code, country, inst_type, json.dumps(metadata_json)),
                )
                row = cur.fetchone()
            return self._inst_row_to_api(row)

        with self._lock:
            self._inst_counter += 1
            row_id = self._inst_counter
            now = self._now_iso()
            record = {
                "id": row_id,
                "name": name,
                "code": code,
                "country": country,
                "type": inst_type,
                "status": "active",
                "metadata_json": metadata_json,
                "created_at": now,
                "updated_at": now,
            }
            self._institutions[row_id] = record
        return dict(record)

    def list_institutions(self, *, conn: object | None = None) -> list[dict[str, Any]]:
        if conn is None:
            with transaction() as tx:
                return self.list_institutions(conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, code, country, type, status, metadata_json, created_at, updated_at
                    FROM app_platform_institutions
                    ORDER BY name ASC
                    """
                )
                rows = cur.fetchall()
            return [self._inst_row_to_api(r) for r in rows]

        with self._lock:
            return [dict(r) for r in sorted(self._institutions.values(), key=lambda x: x["name"])]

    def get_institution(self, institution_id: int, *, conn: object | None = None) -> dict[str, Any] | None:
        if conn is None:
            with transaction() as tx:
                return self.get_institution(institution_id, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, code, country, type, status, metadata_json, created_at, updated_at
                    FROM app_platform_institutions
                    WHERE id = %s
                    """,
                    (institution_id,),
                )
                row = cur.fetchone()
            if row is None:
                return None
            return self._inst_row_to_api(row)

        with self._lock:
            record = self._institutions.get(institution_id)
        return dict(record) if record else None

    # ------------------------------------------------------------------
    # Federation members (tenant → institution link)
    # ------------------------------------------------------------------

    def link_tenant_to_institution(
        self,
        *,
        institution_id: int,
        tenant_id: int,
        role: str,
        conn: object | None = None,
    ) -> dict[str, Any]:
        if conn is None:
            with transaction() as tx:
                return self.link_tenant_to_institution(
                    institution_id=institution_id,
                    tenant_id=tenant_id,
                    role=role,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                # Update the tenant's institution_id (denormalized for fast lookup)
                cur.execute(
                    "UPDATE app_tenants SET institution_id = %s WHERE id = %s",
                    (institution_id, tenant_id),
                )
                cur.execute(
                    """
                    INSERT INTO app_platform_federation_members (institution_id, tenant_id, role)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (institution_id, tenant_id) DO UPDATE SET role = EXCLUDED.role
                    RETURNING id, institution_id, tenant_id, role, created_at
                    """,
                    (institution_id, tenant_id, role),
                )
                row = cur.fetchone()
            return self._member_row_to_api(row)

        with self._lock:
            # Update tenant in-memory institution_id (note: TenantRepository has its own store;
            # we track the link separately here for in-memory tests)
            self._member_counter += 1
            now = self._now_iso()
            # Upsert: remove existing link for same (institution_id, tenant_id) pair
            existing_key = next(
                (k for k, v in self._members.items()
                 if v["institution_id"] == institution_id and v["tenant_id"] == tenant_id),
                None,
            )
            if existing_key is not None:
                self._members[existing_key]["role"] = role
                return dict(self._members[existing_key])

            record = {
                "id": self._member_counter,
                "institution_id": institution_id,
                "tenant_id": tenant_id,
                "role": role,
                "created_at": now,
            }
            self._members[self._member_counter] = record
        return dict(record)

    def list_institution_tenants(
        self,
        institution_id: int,
        *,
        conn: object | None = None,
    ) -> list[dict[str, Any]]:
        if conn is None:
            with transaction() as tx:
                return self.list_institution_tenants(institution_id, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT m.id, m.institution_id, m.tenant_id, m.role, m.created_at
                    FROM app_platform_federation_members m
                    WHERE m.institution_id = %s
                    ORDER BY m.created_at ASC
                    """,
                    (institution_id,),
                )
                rows = cur.fetchall()
            return [self._member_row_to_api(r) for r in rows]

        with self._lock:
            rows = [
                dict(m) for m in self._members.values()
                if m["institution_id"] == institution_id
            ]
        return sorted(rows, key=lambda r: r["created_at"])

    def get_tenant_ids_for_institution(
        self,
        institution_id: int,
        *,
        conn: object | None = None,
    ) -> list[int]:
        members = self.list_institution_tenants(institution_id, conn=conn)
        return [int(m["tenant_id"]) for m in members]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _inst_row_to_api(self, row: tuple[Any, ...]) -> dict[str, Any]:
        return {
            "id": int(row[0]),
            "name": str(row[1]),
            "code": str(row[2]),
            "country": str(row[3]),
            "type": str(row[4]),
            "status": str(row[5]),
            "metadata_json": dict(row[6] or {}),
            "created_at": row[7].isoformat() if hasattr(row[7], "isoformat") else str(row[7]),
            "updated_at": row[8].isoformat() if hasattr(row[8], "isoformat") else str(row[8]),
        }

    def _member_row_to_api(self, row: tuple[Any, ...]) -> dict[str, Any]:
        return {
            "id": int(row[0]),
            "institution_id": int(row[1]),
            "tenant_id": int(row[2]),
            "role": str(row[3]),
            "created_at": row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4]),
        }
