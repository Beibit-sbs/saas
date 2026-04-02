from __future__ import annotations

from app.core.db import get_raw_conn

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from threading import Lock

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


@dataclass
class TenantMemoryState:
    data: dict[int, dict[str, object]] = field(default_factory=dict)
    counter: int = 0


_state_lock = Lock()
_state = TenantMemoryState(
    data={
        1: {
            "id": 1,
            "slug": "default",
            "name": "Default Organization",
            "status": "active",
            "plan_id": 3,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
    },
    counter=1,
)


def clear_tenant_state() -> None:
    """Reset to initial state with default tenant (used in tests)."""
    with _state_lock:
        _state.data.clear()
        _state.data[1] = {
            "id": 1,
            "slug": "default",
            "name": "Default Organization",
            "status": "active",
            "plan_id": 3,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
        _state.counter = 1


def _db_url() -> str | None:
    return os.getenv("DATABASE_URL")


def _use_database() -> bool:
    return bool(_db_url()) and psycopg is not None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _should_fallback_to_memory(exc: Exception) -> bool:
    if isinstance(exc, RuntimeError) and str(exc) == "database unavailable":
        return True
    if isinstance(exc, (ConnectionError, TimeoutError, OSError, ValueError)):
        return True
    if psycopg is not None and isinstance(exc, (psycopg.OperationalError, psycopg.InterfaceError)):
        return True
    return False


def _row_to_dict(row: object) -> dict[str, object]:
    return {
        "id": row[0],
        "slug": row[1],
        "name": row[2],
        "status": row[3],
        "plan_id": int(row[4]) if row[4] is not None else 1,
        "created_at": row[5].isoformat() if hasattr(row[5], "isoformat") else str(row[5]),
        "updated_at": row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6]),
    }


# ---------------------------------------------------------------------------
# DB implementations
# ---------------------------------------------------------------------------

def _list_tenants_db() -> list[dict[str, object]]:
    url = _db_url()
    assert url
    with get_raw_conn() as conn:
        rows = conn.execute(
            "SELECT id, slug, name, status, plan_id, created_at, updated_at FROM app_tenants ORDER BY id"
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def _create_tenant_db(payload: dict[str, object]) -> dict[str, object]:
    url = _db_url()
    assert url
    slug = str(payload.get("slug", "")).strip()
    if not slug:
        raise ValueError("slug is required")

    existing = _get_tenant_by_slug_db(slug)
    if existing is not None:
        raise ValueError(f"Tenant with slug '{slug}' already exists")

    with get_raw_conn() as conn:
        try:
            row = conn.execute(
                """
                INSERT INTO app_tenants (slug, name, status, plan_id, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING id, slug, name, status, plan_id, created_at, updated_at
                """,
                (
                    slug,
                    payload["name"],
                    payload.get("status", "active"),
                    int(payload.get("plan_id") or 1),
                ),
            ).fetchone()
            conn.commit()
        except Exception as exc:
            message = str(exc).lower()
            if "duplicate key" in message and "slug" in message:
                raise ValueError(f"Tenant with slug '{slug}' already exists") from exc
            if "foreign key" in message and "plan_id" in message:
                raise ValueError("plan_id is invalid") from exc
            raise
    return _row_to_dict(row)


def _update_tenant_db(tenant_id: int, payload: dict[str, object]) -> dict[str, object]:
    url = _db_url()
    assert url
    with get_raw_conn() as conn:
        existing = conn.execute(
            "SELECT id, slug, name, status, plan_id, created_at, updated_at FROM app_tenants WHERE id = %s",
            (tenant_id,),
        ).fetchone()
        if not existing:
            raise ValueError(f"Tenant {tenant_id} not found")
        name = payload.get("name") or existing[2]
        status = payload.get("status") or existing[3]
        plan_id = int(payload.get("plan_id") or existing[4] or 1)
        row = conn.execute(
            """
            UPDATE app_tenants SET name = %s, status = %s, plan_id = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING id, slug, name, status, plan_id, created_at, updated_at
            """,
            (name, status, plan_id, tenant_id),
        ).fetchone()
        conn.commit()
    return _row_to_dict(row)


def _delete_tenant_db(tenant_id: int) -> dict[str, object]:
    url = _db_url()
    assert url
    with get_raw_conn() as conn:
        row = conn.execute(
            """
            UPDATE app_tenants SET status = 'inactive', updated_at = NOW()
            WHERE id = %s
            RETURNING id, slug, name, status, plan_id, created_at, updated_at
            """,
            (tenant_id,),
        ).fetchone()
        if not row:
            raise ValueError(f"Tenant {tenant_id} not found")
        conn.commit()
    return _row_to_dict(row)


def _get_tenant_db(tenant_id: int) -> dict[str, object] | None:
    url = _db_url()
    assert url
    with get_raw_conn() as conn:
        row = conn.execute(
            "SELECT id, slug, name, status, plan_id, created_at, updated_at FROM app_tenants WHERE id = %s",
            (tenant_id,),
        ).fetchone()
    return _row_to_dict(row) if row else None


def _get_tenant_by_slug_db(slug: str) -> dict[str, object] | None:
    url = _db_url()
    assert url
    with get_raw_conn() as conn:
        row = conn.execute(
            "SELECT id, slug, name, status, plan_id, created_at, updated_at FROM app_tenants WHERE slug = %s",
            (slug,),
        ).fetchone()
    return _row_to_dict(row) if row else None


# ---------------------------------------------------------------------------
# Memory implementations
# ---------------------------------------------------------------------------

def _list_tenants_memory() -> list[dict[str, object]]:
    with _state_lock:
        return sorted(_state.data.values(), key=lambda t: int(t["id"]))  # type: ignore[arg-type]


def _create_tenant_memory(payload: dict[str, object]) -> dict[str, object]:
    slug = str(payload.get("slug", "")).strip()
    name = str(payload.get("name", "")).strip()
    status = str(payload.get("status", "active")).strip() or "active"
    plan_id = int(payload.get("plan_id") or 1)
    if not slug:
        raise ValueError("slug is required")
    if not name:
        raise ValueError("name is required")
    now = _now_iso()
    with _state_lock:
        for existing in _state.data.values():
            if existing["slug"] == slug:
                raise ValueError(f"Tenant with slug '{slug}' already exists")
        _state.counter += 1
        new_id = _state.counter
        record: dict[str, object] = {
            "id": new_id,
            "slug": slug,
            "name": name,
            "status": status,
            "plan_id": plan_id,
            "created_at": now,
            "updated_at": now,
        }
        _state.data[new_id] = record
    return dict(record)


def _update_tenant_memory(tenant_id: int, payload: dict[str, object]) -> dict[str, object]:
    now = _now_iso()
    with _state_lock:
        existing = _state.data.get(tenant_id)
        if not existing:
            raise ValueError(f"Tenant {tenant_id} not found")
        if "name" in payload and payload["name"]:
            existing["name"] = str(payload["name"]).strip()
        if "status" in payload and payload["status"]:
            existing["status"] = str(payload["status"]).strip()
        if "plan_id" in payload and payload["plan_id"]:
            existing["plan_id"] = int(payload["plan_id"])
        existing["updated_at"] = now
    return dict(existing)


def _delete_tenant_memory(tenant_id: int) -> dict[str, object]:
    now = _now_iso()
    with _state_lock:
        existing = _state.data.get(tenant_id)
        if not existing:
            raise ValueError(f"Tenant {tenant_id} not found")
        existing["status"] = "inactive"
        existing["updated_at"] = now
    return dict(existing)


def _get_tenant_memory(tenant_id: int) -> dict[str, object] | None:
    with _state_lock:
        existing = _state.data.get(tenant_id)
    return dict(existing) if existing else None


def _get_tenant_by_slug_memory(slug: str) -> dict[str, object] | None:
    with _state_lock:
        for existing in _state.data.values():
            if existing["slug"] == slug:
                return dict(existing)
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_tenants() -> list[dict[str, object]]:
    if _use_database():
        try:
            return _list_tenants_db()
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise
    return _list_tenants_memory()


def create_tenant(payload: dict[str, object]) -> dict[str, object]:
    if _use_database():
        try:
            return _create_tenant_db(payload)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise
    return _create_tenant_memory(payload)


def update_tenant(tenant_id: int, payload: dict[str, object]) -> dict[str, object]:
    if _use_database():
        try:
            return _update_tenant_db(tenant_id, payload)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise
    return _update_tenant_memory(tenant_id, payload)


def delete_tenant(tenant_id: int) -> dict[str, object]:
    if _use_database():
        try:
            return _delete_tenant_db(tenant_id)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise
    return _delete_tenant_memory(tenant_id)


def get_tenant(tenant_id: int) -> dict[str, object] | None:
    if _use_database():
        try:
            return _get_tenant_db(tenant_id)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise
    return _get_tenant_memory(tenant_id)


def get_tenant_by_slug(slug: str) -> dict[str, object] | None:
    if _use_database():
        try:
            return _get_tenant_by_slug_db(slug)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise
    return _get_tenant_by_slug_memory(slug)


def force_delete_tenant(tenant_id: int) -> bool:
    """Hard-delete tenant row for failed provisioning rollback paths."""
    normalized_tenant_id = int(tenant_id)
    if normalized_tenant_id <= 0 or normalized_tenant_id == 1:
        return False

    if _use_database():
        try:
            url = _db_url()
            assert url
            with get_raw_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM app_user_roles WHERE tenant_id = %s", (normalized_tenant_id,))
                    cur.execute("DELETE FROM app_role_permissions WHERE tenant_id = %s", (normalized_tenant_id,))
                    cur.execute("DELETE FROM app_roles WHERE tenant_id = %s", (normalized_tenant_id,))
                    cur.execute("DELETE FROM app_usage_events WHERE tenant_id = %s", (normalized_tenant_id,))
                    cur.execute("DELETE FROM app_jobs WHERE tenant_id = %s", (normalized_tenant_id,))
                    cur.execute("DELETE FROM app_audit_events WHERE tenant_id = %s", (normalized_tenant_id,))
                    cur.execute("DELETE FROM app_tenants WHERE id = %s", (normalized_tenant_id,))
                    removed = cur.rowcount > 0
                conn.commit()
            if removed:
                return True
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    with _state_lock:
        existing = _state.data.pop(normalized_tenant_id, None)
    return existing is not None


def list_login_directory_tenants() -> list[dict[str, object]]:
    """
    Public login directory: list of active tenants available for tenant-bound users.
    Returns only essential fields: tenant_id, slug, name.
    Filters out inactive, suspended, or non-login-allowed tenants.
    Safe for unauthenticated access.
    """
    tenants = list_tenants()
    
    result = []
    for tenant in tenants:
        status = str(tenant.get("status", "")).lower()
        # Only include active tenants for login UX
        if status != "active":
            continue
        
        result.append({
            "tenant_id": int(tenant["id"]),
            "slug": str(tenant["slug"]),
            "name": str(tenant["name"]),
        })
    
    # Sort by name for consistent UI ordering
    result.sort(key=lambda t: t["name"])
    return result
