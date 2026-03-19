from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from threading import Lock
from typing import Any

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


@dataclass(frozen=True)
class EntityConfig:
    table: str
    fields: tuple[str, ...]
    required: tuple[str, ...]
    fk_fields: tuple[str, ...] = ()


ENTITY_CONFIGS: dict[str, EntityConfig] = {
    "students": EntityConfig(
        table="university_students",
        fields=("student_id", "first_name", "last_name", "email", "status", "tenant_id"),
        required=("student_id", "first_name", "last_name", "email", "status"),
    ),
    "faculty": EntityConfig(
        table="university_faculty",
        fields=("faculty_id", "first_name", "last_name", "department", "email", "status", "tenant_id"),
        required=("faculty_id", "first_name", "last_name", "department", "email", "status"),
    ),
    "programs": EntityConfig(
        table="university_programs",
        fields=("program_code", "title", "degree_type", "faculty", "status", "tenant_id"),
        required=("program_code", "title", "degree_type", "faculty", "status"),
    ),
    "courses": EntityConfig(
        table="university_courses",
        fields=("course_code", "title", "credits", "program_id", "status", "tenant_id"),
        required=("course_code", "title", "credits", "program_id", "status"),
        fk_fields=("program_id",),
    ),
    "enrollments": EntityConfig(
        table="university_enrollments",
        fields=("student_id", "course_id", "semester", "status", "tenant_id"),
        required=("student_id", "course_id", "semester", "status"),
        fk_fields=("student_id", "course_id"),
    ),
    "academic_records": EntityConfig(
        table="university_academic_records",
        fields=("student_id", "course_id", "grade", "semester", "status", "tenant_id"),
        required=("student_id", "course_id", "grade", "semester", "status"),
        fk_fields=("student_id", "course_id"),
    ),
}


@dataclass
class UniversityMemoryState:
    data: dict[str, dict[int, dict[str, object]]] = field(default_factory=dict)
    counters: dict[str, int] = field(default_factory=dict)


_state_lock = Lock()
_state = UniversityMemoryState(
    data={name: {} for name in ENTITY_CONFIGS},
    counters={name: 0 for name in ENTITY_CONFIGS},
)


def clear_university_state() -> None:
    with _state_lock:
        for name in ENTITY_CONFIGS:
            _state.data[name].clear()
            _state.counters[name] = 0


def _db_url() -> str | None:
    return os.getenv("DATABASE_URL")


def _use_database() -> bool:
    return bool(_db_url()) and psycopg is not None


def _should_fallback_to_memory(exc: Exception) -> bool:
    if isinstance(exc, RuntimeError) and str(exc) == "database unavailable":
        return True
    if isinstance(exc, (ConnectionError, TimeoutError, OSError, ValueError)):
        return True
    if psycopg is not None and isinstance(exc, (psycopg.OperationalError, psycopg.InterfaceError)):
        return True
    return False


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_string(name: str, value: object, max_len: int = 255) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{name} is required")
    if len(normalized) > max_len:
        raise ValueError(f"{name} must be at most {max_len} characters")
    return normalized


def _normalize_optional_tenant(value: object) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None


def _normalize_payload(entity_name: str, payload: dict[str, object]) -> dict[str, object]:
    config = ENTITY_CONFIGS[entity_name]
    normalized: dict[str, object] = {}

    for field_name in config.required:
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")

    for field_name in config.fields:
        raw_value = payload.get(field_name)

        if field_name == "tenant_id":
            normalized[field_name] = _normalize_optional_tenant(raw_value)
            continue

        if field_name == "credits":
            try:
                credits = int(raw_value)
            except (TypeError, ValueError) as exc:
                raise ValueError("credits must be an integer") from exc
            if credits < 0:
                raise ValueError("credits must be non-negative")
            normalized[field_name] = credits
            continue

        if field_name in {"program_id", "student_id", "course_id"} and field_name in config.fk_fields:
            try:
                fk_id = int(raw_value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{field_name} must be an integer") from exc
            if fk_id <= 0:
                raise ValueError(f"{field_name} must be positive")
            normalized[field_name] = fk_id
            continue

        normalized[field_name] = _normalize_string(field_name, raw_value)

    email_value = normalized.get("email")
    if isinstance(email_value, str) and "@" not in email_value:
        raise ValueError("email must contain @")

    return normalized


def _row_to_dict(row: tuple[Any, ...], fields: tuple[str, ...], include_created_at: bool) -> dict[str, object]:
    result: dict[str, object] = {"id": int(row[0])}
    offset = 1
    if include_created_at:
        created_at = row[offset]
        result["created_at"] = created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at)
        offset += 1

    for index, field_name in enumerate(fields):
        result[field_name] = row[offset + index]
    return result


def _db_fetch_exists(conn, table: str, item_id: int) -> bool:
    with conn.cursor() as cur:
        cur.execute(f"SELECT 1 FROM {table} WHERE id = %s", (item_id,))
        return cur.fetchone() is not None


def _validate_foreign_keys_db(conn, entity_name: str, payload: dict[str, object]) -> None:
    config = ENTITY_CONFIGS[entity_name]

    if "program_id" in config.fk_fields:
        program_id = int(payload["program_id"])
        if not _db_fetch_exists(conn, "university_programs", program_id):
            raise ValueError("program_id references unknown program")

    if "student_id" in config.fk_fields:
        student_id = int(payload["student_id"])
        if not _db_fetch_exists(conn, "university_students", student_id):
            raise ValueError("student_id references unknown student")

    if "course_id" in config.fk_fields:
        course_id = int(payload["course_id"])
        if not _db_fetch_exists(conn, "university_courses", course_id):
            raise ValueError("course_id references unknown course")


def _list_entities_db(entity_name: str) -> list[dict[str, object]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    config = ENTITY_CONFIGS[entity_name]
    include_created_at = entity_name == "students"
    selected_columns = ["id"]
    if include_created_at:
        selected_columns.append("created_at")
    selected_columns.extend(config.fields)

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {', '.join(selected_columns)} FROM {config.table} ORDER BY id ASC"
            )
            rows = cur.fetchall()

    return [_row_to_dict(row, config.fields, include_created_at) for row in rows]


def _create_entity_db(entity_name: str, payload: dict[str, object]) -> dict[str, object]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    config = ENTITY_CONFIGS[entity_name]
    include_created_at = entity_name == "students"
    returning_columns = ["id"]
    if include_created_at:
        returning_columns.append("created_at")
    returning_columns.extend(config.fields)

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _validate_foreign_keys_db(conn, entity_name, payload)
        with conn.cursor() as cur:
            columns = list(config.fields)
            placeholders = ["%s" for _ in columns]
            values = [payload[column] for column in columns]
            cur.execute(
                f"INSERT INTO {config.table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING {', '.join(returning_columns)}",
                values,
            )
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise RuntimeError(f"failed to create {entity_name}")
    return _row_to_dict(row, config.fields, include_created_at)


def _update_entity_db(entity_name: str, item_id: int, payload: dict[str, object]) -> dict[str, object]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    config = ENTITY_CONFIGS[entity_name]
    include_created_at = entity_name == "students"
    returning_columns = ["id"]
    if include_created_at:
        returning_columns.append("created_at")
    returning_columns.extend(config.fields)

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _validate_foreign_keys_db(conn, entity_name, payload)
        with conn.cursor() as cur:
            assignments = [f"{column} = %s" for column in config.fields]
            values = [payload[column] for column in config.fields]
            values.append(item_id)
            cur.execute(
                f"UPDATE {config.table} SET {', '.join(assignments)} WHERE id = %s RETURNING {', '.join(returning_columns)}",
                values,
            )
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise ValueError(f"{entity_name.rstrip('s')} not found")
    return _row_to_dict(row, config.fields, include_created_at)


def _delete_entity_db(entity_name: str, item_id: int) -> dict[str, object]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    config = ENTITY_CONFIGS[entity_name]
    include_created_at = entity_name == "students"
    returning_columns = ["id"]
    if include_created_at:
        returning_columns.append("created_at")
    returning_columns.extend(config.fields)

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {config.table} WHERE id = %s RETURNING {', '.join(returning_columns)}",
                (item_id,),
            )
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise ValueError(f"{entity_name.rstrip('s')} not found")
    return _row_to_dict(row, config.fields, include_created_at)


def _memory_fk_exists(entity_name: str, item_id: int) -> bool:
    return item_id in _state.data[entity_name]


def _validate_foreign_keys_memory(entity_name: str, payload: dict[str, object]) -> None:
    config = ENTITY_CONFIGS[entity_name]
    if "program_id" in config.fk_fields and not _memory_fk_exists("programs", int(payload["program_id"])):
        raise ValueError("program_id references unknown program")
    if "student_id" in config.fk_fields and not _memory_fk_exists("students", int(payload["student_id"])):
        raise ValueError("student_id references unknown student")
    if "course_id" in config.fk_fields and not _memory_fk_exists("courses", int(payload["course_id"])):
        raise ValueError("course_id references unknown course")


def list_entities(entity_name: str) -> list[dict[str, object]]:
    if entity_name not in ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    if _use_database():
        try:
            return _list_entities_db(entity_name)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    with _state_lock:
        rows = list(_state.data[entity_name].values())
    rows.sort(key=lambda row: int(row["id"]))
    return rows


def create_entity(entity_name: str, payload: dict[str, object]) -> dict[str, object]:
    if entity_name not in ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    normalized = _normalize_payload(entity_name, payload)

    if _use_database():
        try:
            return _create_entity_db(entity_name, normalized)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    with _state_lock:
        _validate_foreign_keys_memory(entity_name, normalized)
        _state.counters[entity_name] += 1
        item_id = _state.counters[entity_name]
        row: dict[str, object] = {"id": item_id, **normalized}
        if entity_name == "students":
            row["created_at"] = _now_iso()
        _state.data[entity_name][item_id] = row
        return row


def update_entity(entity_name: str, item_id: int, payload: dict[str, object]) -> dict[str, object]:
    if entity_name not in ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    normalized = _normalize_payload(entity_name, payload)

    if _use_database():
        try:
            return _update_entity_db(entity_name, item_id, normalized)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    with _state_lock:
        _validate_foreign_keys_memory(entity_name, normalized)
        current = _state.data[entity_name].get(item_id)
        if current is None:
            raise ValueError(f"{entity_name.rstrip('s')} not found")

        updated = {"id": item_id, **normalized}
        if entity_name == "students":
            updated["created_at"] = current.get("created_at") or _now_iso()
        _state.data[entity_name][item_id] = updated
        return updated


def delete_entity(entity_name: str, item_id: int) -> dict[str, object]:
    if entity_name not in ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    if _use_database():
        try:
            return _delete_entity_db(entity_name, item_id)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    with _state_lock:
        current = _state.data[entity_name].pop(item_id, None)
        if current is None:
            raise ValueError(f"{entity_name.rstrip('s')} not found")
        return current


# ---------------------------------------------------------------------------
# Tenant-aware DB implementations
# ---------------------------------------------------------------------------

def _list_entities_for_tenant_db(entity_name: str, tenant_id: int) -> list[dict[str, object]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    config = ENTITY_CONFIGS[entity_name]
    include_created_at = entity_name == "students"
    selected_columns = ["id"]
    if include_created_at:
        selected_columns.append("created_at")
    selected_columns.extend(config.fields)

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {', '.join(selected_columns)} FROM {config.table}"
                f" WHERE tenant_id = %s ORDER BY id ASC",
                (str(tenant_id),),
            )
            rows = cur.fetchall()

    return [_row_to_dict(row, config.fields, include_created_at) for row in rows]


def _update_entity_for_tenant_db(
    entity_name: str, item_id: int, payload: dict[str, object], tenant_id: int
) -> dict[str, object]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    config = ENTITY_CONFIGS[entity_name]
    include_created_at = entity_name == "students"
    returning_columns = ["id"]
    if include_created_at:
        returning_columns.append("created_at")
    returning_columns.extend(config.fields)

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _validate_foreign_keys_db(conn, entity_name, payload)
        with conn.cursor() as cur:
            assignments = [f"{column} = %s" for column in config.fields]
            values: list[Any] = [payload[column] for column in config.fields]
            values.extend([item_id, str(tenant_id)])
            cur.execute(
                f"UPDATE {config.table} SET {', '.join(assignments)}"
                f" WHERE id = %s AND tenant_id = %s"
                f" RETURNING {', '.join(returning_columns)}",
                values,
            )
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise ValueError(f"{entity_name.rstrip('s')} not found")
    return _row_to_dict(row, config.fields, include_created_at)


def _delete_entity_for_tenant_db(
    entity_name: str, item_id: int, tenant_id: int
) -> dict[str, object]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    config = ENTITY_CONFIGS[entity_name]
    include_created_at = entity_name == "students"
    returning_columns = ["id"]
    if include_created_at:
        returning_columns.append("created_at")
    returning_columns.extend(config.fields)

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {config.table} WHERE id = %s AND tenant_id = %s"
                f" RETURNING {', '.join(returning_columns)}",
                (item_id, str(tenant_id)),
            )
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise ValueError(f"{entity_name.rstrip('s')} not found")
    return _row_to_dict(row, config.fields, include_created_at)


# ---------------------------------------------------------------------------
# Tenant-aware memory implementations
# ---------------------------------------------------------------------------

def _list_entities_for_tenant_memory(entity_name: str, tenant_id: int) -> list[dict[str, object]]:
    tid = str(tenant_id)
    with _state_lock:
        rows = [dict(r) for r in _state.data[entity_name].values() if str(r.get("tenant_id", "")) == tid]
    rows.sort(key=lambda r: int(r["id"]))  # type: ignore[arg-type]
    return rows


def _update_entity_for_tenant_memory(
    entity_name: str, item_id: int, payload: dict[str, object], tenant_id: int
) -> dict[str, object]:
    tid = str(tenant_id)
    with _state_lock:
        _validate_foreign_keys_memory(entity_name, payload)
        current = _state.data[entity_name].get(item_id)
        if current is None or str(current.get("tenant_id", "")) != tid:
            raise ValueError(f"{entity_name.rstrip('s')} not found")
        updated: dict[str, object] = {"id": item_id, **payload}
        if entity_name == "students":
            updated["created_at"] = current.get("created_at") or _now_iso()
        _state.data[entity_name][item_id] = updated
        return dict(updated)


def _delete_entity_for_tenant_memory(
    entity_name: str, item_id: int, tenant_id: int
) -> dict[str, object]:
    tid = str(tenant_id)
    with _state_lock:
        current = _state.data[entity_name].get(item_id)
        if current is None or str(current.get("tenant_id", "")) != tid:
            raise ValueError(f"{entity_name.rstrip('s')} not found")
        del _state.data[entity_name][item_id]
        return dict(current)


# ---------------------------------------------------------------------------
# Public tenant-aware API
# ---------------------------------------------------------------------------

def list_entities_for_tenant(entity_name: str, tenant_id: int) -> list[dict[str, object]]:
    """List entities filtered by tenant_id."""
    if entity_name not in ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    if _use_database():
        try:
            return _list_entities_for_tenant_db(entity_name, tenant_id)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    return _list_entities_for_tenant_memory(entity_name, tenant_id)


def create_entity_for_tenant(
    entity_name: str, payload: dict[str, object], tenant_id: int
) -> dict[str, object]:
    """Create entity with tenant_id forced from context (ignores any incoming tenant_id)."""
    if entity_name not in ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    payload_with_tenant: dict[str, object] = {**payload, "tenant_id": str(tenant_id)}
    normalized = _normalize_payload(entity_name, payload_with_tenant)

    if _use_database():
        try:
            return _create_entity_db(entity_name, normalized)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    with _state_lock:
        _validate_foreign_keys_memory(entity_name, normalized)
        _state.counters[entity_name] += 1
        item_id = _state.counters[entity_name]
        row: dict[str, object] = {"id": item_id, **normalized}
        if entity_name == "students":
            row["created_at"] = _now_iso()
        _state.data[entity_name][item_id] = row
        return dict(row)


def update_entity_for_tenant(
    entity_name: str, item_id: int, payload: dict[str, object], tenant_id: int
) -> dict[str, object]:
    """Update entity, enforcing tenant ownership. Returns 404 if not found or wrong tenant."""
    if entity_name not in ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    payload_with_tenant: dict[str, object] = {**payload, "tenant_id": str(tenant_id)}
    normalized = _normalize_payload(entity_name, payload_with_tenant)

    if _use_database():
        try:
            return _update_entity_for_tenant_db(entity_name, item_id, normalized, tenant_id)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    return _update_entity_for_tenant_memory(entity_name, item_id, normalized, tenant_id)


def delete_entity_for_tenant(
    entity_name: str, item_id: int, tenant_id: int
) -> dict[str, object]:
    """Delete entity, enforcing tenant ownership. Returns 404 if not found or wrong tenant."""
    if entity_name not in ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    if _use_database():
        try:
            return _delete_entity_for_tenant_db(entity_name, item_id, tenant_id)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    return _delete_entity_for_tenant_memory(entity_name, item_id, tenant_id)
