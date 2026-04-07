from __future__ import annotations
from app.core.db import get_raw_conn
from app.core.config import is_runtime_schema_bootstrap_enabled

from dataclasses import dataclass, field
import os
from threading import Lock

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


DEFAULT_PLANS: tuple[dict[str, object], ...] = (
    {
        "code": "free",
        "name": "Free",
        "description": "Starter plan",
        "active": True,
    },
    {
        "code": "basic",
        "name": "Basic",
        "description": "Entry commercial plan",
        "active": True,
    },
    {
        "code": "pro",
        "name": "Pro",
        "description": "Professional plan",
        "active": True,
    },
    {
        "code": "enterprise",
        "name": "Enterprise",
        "description": "Enterprise plan",
        "active": True,
    },
)


@dataclass
class PlansState:
    rows: dict[int, dict[str, object]] = field(default_factory=dict)
    counter: int = 0


_state_lock = Lock()
_state = PlansState()


def _db_url() -> str | None:
    return os.getenv("DATABASE_URL")


def _use_database() -> bool:
    return bool(_db_url()) and psycopg is not None


def _normalize_code(value: str) -> str:
    code = str(value or "").strip().lower()
    if not code:
        raise ValueError("plan code is required")
    if len(code) > 64:
        raise ValueError("plan code is too long")
    return code


def _normalize_name(value: str) -> str:
    name = str(value or "").strip()
    if not name:
        raise ValueError("plan name is required")
    if len(name) > 255:
        raise ValueError("plan name is too long")
    return name


def _normalize_description(value: str | None) -> str:
    description = str(value or "").strip()
    if len(description) > 2000:
        raise ValueError("plan description is too long")
    return description


def _ensure_memory_seeded() -> None:
    with _state_lock:
        if _state.rows:
            return
        for item in DEFAULT_PLANS:
            _state.counter += 1
            plan_id = _state.counter
            _state.rows[plan_id] = {
                "id": plan_id,
                "code": item["code"],
                "name": item["name"],
                "description": item["description"],
                "active": bool(item["active"]),
            }


def _ensure_db(conn) -> None:
    if not is_runtime_schema_bootstrap_enabled():
        return
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_plans (
                id BIGSERIAL PRIMARY KEY,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS ix_app_plans_active ON app_plans (active)")
        cur.executemany(
            """
            INSERT INTO app_plans (code, name, description, active)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (code) DO NOTHING
            """,
            [
                (item["code"], item["name"], item["description"], bool(item["active"]))
                for item in DEFAULT_PLANS
            ],
        )
    conn.commit()


def _list_db(include_inactive: bool) -> list[dict[str, object]]:
    assert _db_url() and psycopg is not None
    with get_raw_conn() as conn:
        _ensure_db(conn)
        where_sql = "" if include_inactive else "WHERE active = TRUE"
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, code, name, description, active
                FROM app_plans
                {where_sql}
                ORDER BY id
                """
            )
            rows = cur.fetchall()
    return [
        {
            "id": int(row[0]),
            "code": str(row[1]),
            "name": str(row[2]),
            "description": str(row[3] or ""),
            "active": bool(row[4]),
        }
        for row in rows
    ]


def _create_db(payload: dict[str, object]) -> dict[str, object]:
    assert _db_url() and psycopg is not None
    with get_raw_conn() as conn:
        _ensure_db(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_plans (code, name, description, active)
                VALUES (%s, %s, %s, %s)
                RETURNING id, code, name, description, active
                """,
                (
                    payload["code"],
                    payload["name"],
                    payload["description"],
                    payload["active"],
                ),
            )
            row = cur.fetchone()
        conn.commit()
    return {
        "id": int(row[0]),
        "code": str(row[1]),
        "name": str(row[2]),
        "description": str(row[3] or ""),
        "active": bool(row[4]),
    }


def _update_db(plan_id: int, payload: dict[str, object]) -> dict[str, object]:
    assert _db_url() and psycopg is not None
    with get_raw_conn() as conn:
        _ensure_db(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, code, name, description, active FROM app_plans WHERE id = %s",
                (plan_id,),
            )
            existing = cur.fetchone()
            if existing is None:
                raise ValueError("plan not found")

            next_name = payload.get("name", existing[2])
            next_description = payload.get("description", existing[3])
            next_active = payload.get("active", existing[4])

            cur.execute(
                """
                UPDATE app_plans
                SET name = %s,
                    description = %s,
                    active = %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING id, code, name, description, active
                """,
                (next_name, next_description, bool(next_active), plan_id),
            )
            row = cur.fetchone()
        conn.commit()

    return {
        "id": int(row[0]),
        "code": str(row[1]),
        "name": str(row[2]),
        "description": str(row[3] or ""),
        "active": bool(row[4]),
    }


def list_plans(include_inactive: bool = True) -> list[dict[str, object]]:
    if _use_database():
        try:
            return _list_db(include_inactive=include_inactive)
        except Exception:
            pass

    _ensure_memory_seeded()
    with _state_lock:
        rows = [dict(item) for item in _state.rows.values()]
    if not include_inactive:
        rows = [item for item in rows if bool(item.get("active"))]
    rows.sort(key=lambda item: int(item["id"]))
    return rows


def get_plan_by_id(plan_id: int) -> dict[str, object] | None:
    normalized_plan_id = int(plan_id)
    if normalized_plan_id <= 0:
        return None

    rows = list_plans(include_inactive=True)
    return next((item for item in rows if int(item["id"]) == normalized_plan_id), None)


def get_plan_by_code(code: str) -> dict[str, object] | None:
    normalized_code = _normalize_code(code)
    rows = list_plans(include_inactive=True)
    return next((item for item in rows if str(item["code"]) == normalized_code), None)


def create_plan(payload: dict[str, object]) -> dict[str, object]:
    normalized_payload = {
        "code": _normalize_code(str(payload.get("code", ""))),
        "name": _normalize_name(str(payload.get("name", ""))),
        "description": _normalize_description(str(payload.get("description", ""))),
        "active": bool(payload.get("active", True)),
    }

    if get_plan_by_code(normalized_payload["code"]):
        raise ValueError("plan code already exists")

    if _use_database():
        try:
            return _create_db(normalized_payload)
        except Exception:
            pass

    _ensure_memory_seeded()
    with _state_lock:
        for item in _state.rows.values():
            if item["code"] == normalized_payload["code"]:
                raise ValueError("plan code already exists")
        _state.counter += 1
        plan_id = _state.counter
        row = {
            "id": plan_id,
            **normalized_payload,
        }
        _state.rows[plan_id] = row
        return dict(row)


def update_plan(plan_id: int, payload: dict[str, object]) -> dict[str, object]:
    normalized_plan_id = int(plan_id)
    if normalized_plan_id <= 0:
        raise ValueError("invalid plan id")

    normalized_payload: dict[str, object] = {}
    if "name" in payload and payload["name"] is not None:
        normalized_payload["name"] = _normalize_name(str(payload["name"]))
    if "description" in payload and payload["description"] is not None:
        normalized_payload["description"] = _normalize_description(str(payload["description"]))
    if "active" in payload and payload["active"] is not None:
        normalized_payload["active"] = bool(payload["active"])

    if _use_database():
        try:
            return _update_db(normalized_plan_id, normalized_payload)
        except Exception:
            pass

    _ensure_memory_seeded()
    with _state_lock:
        existing = _state.rows.get(normalized_plan_id)
        if existing is None:
            raise ValueError("plan not found")
        existing.update(normalized_payload)
        return dict(existing)


def clear_plans_state() -> None:
    with _state_lock:
        _state.rows.clear()
        _state.counter = 0
