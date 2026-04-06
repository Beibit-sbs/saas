from __future__ import annotations
import logging
from app.core.db import get_raw_conn

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
import re
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
_SQL_IDENTIFIER_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
logger = logging.getLogger("app.university_core")


def _mark_university_core_usage(function_name: str, entity_name: str, tenant_id: int | None = None) -> None:
    logger.warning(
        "university_core shared service used; function=%s entity=%s tenant_id=%s",
        function_name,
        entity_name,
        tenant_id,
    )


def _parse_tenant_id(value: object) -> int | None:
    normalized = str(value or "").strip()
    if not normalized:
        return None
    try:
        return int(normalized)
    except (TypeError, ValueError):
        return None


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


def _sql_identifier(name: str):
    if psycopg is None:
        raise RuntimeError("database unavailable")
    normalized = str(name or "").strip()
    if not _SQL_IDENTIFIER_RE.fullmatch(normalized):
        raise ValueError(f"unsafe SQL identifier: {normalized}")
    return psycopg.sql.Identifier(normalized)


def _sql_identifier_list(names: list[str] | tuple[str, ...]):
    if psycopg is None:
        raise RuntimeError("database unavailable")
    return psycopg.sql.SQL(", ").join(_sql_identifier(name) for name in names)


def _db_fetch_exists(conn, table: str, item_id: int) -> bool:
    with conn.cursor() as cur:
        query = psycopg.sql.SQL("SELECT 1 FROM {} WHERE id = %s").format(_sql_identifier(table))
        cur.execute(query, (item_id,))
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
    from app.modules.university_core.entity_impl import _list_entities_db_impl

    return _list_entities_db_impl(entity_name)


def _create_entity_db(entity_name: str, payload: dict[str, object]) -> dict[str, object]:
    from app.modules.university_core.entity_impl import _create_entity_db_impl

    return _create_entity_db_impl(entity_name, payload)


def _update_entity_db(entity_name: str, item_id: int, payload: dict[str, object]) -> dict[str, object]:
    from app.modules.university_core.entity_impl import _update_entity_db_impl

    return _update_entity_db_impl(entity_name, item_id, payload)


def _delete_entity_db(entity_name: str, item_id: int) -> dict[str, object]:
    from app.modules.university_core.entity_impl import _delete_entity_db_impl

    return _delete_entity_db_impl(entity_name, item_id)


def _memory_fk_exists(entity_name: str, item_id: int) -> bool:
    from app.modules.university_core.entity_impl import _memory_fk_exists_impl

    return _memory_fk_exists_impl(entity_name, item_id)


def _validate_foreign_keys_memory(entity_name: str, payload: dict[str, object]) -> None:
    from app.modules.university_core.entity_impl import _validate_foreign_keys_memory_impl

    return _validate_foreign_keys_memory_impl(entity_name, payload)


def list_entities(entity_name: str) -> list[dict[str, object]]:
    if entity_name not in ENTITY_CONFIGS:
        raise ValueError("unknown entity")
    _mark_university_core_usage("list_entities", entity_name)
    from app.modules.university_core.entity_impl import list_entities_impl

    return list_entities_impl(entity_name)


def create_entity(entity_name: str, payload: dict[str, object]) -> dict[str, object]:
    if entity_name not in ENTITY_CONFIGS:
        raise ValueError("unknown entity")
    tenant_id_int = _parse_tenant_id(payload.get("tenant_id"))
    _mark_university_core_usage("create_entity", entity_name, tenant_id_int)
    from app.modules.university_core.entity_impl import create_entity_impl

    return create_entity_impl(entity_name, payload)


def update_entity(entity_name: str, item_id: int, payload: dict[str, object]) -> dict[str, object]:
    if entity_name not in ENTITY_CONFIGS:
        raise ValueError("unknown entity")
    tenant_id_int = _parse_tenant_id(payload.get("tenant_id"))
    _mark_university_core_usage("update_entity", entity_name, tenant_id_int)
    from app.modules.university_core.entity_impl import update_entity_impl

    return update_entity_impl(entity_name, item_id, payload)


def delete_entity(entity_name: str, item_id: int) -> dict[str, object]:
    if entity_name not in ENTITY_CONFIGS:
        raise ValueError("unknown entity")
    _mark_university_core_usage("delete_entity", entity_name)
    from app.modules.university_core.entity_impl import delete_entity_impl

    return delete_entity_impl(entity_name, item_id)


# ---------------------------------------------------------------------------
# Tenant-aware DB implementations
# ---------------------------------------------------------------------------

def _list_entities_for_tenant_db(entity_name: str, tenant_id: int) -> list[dict[str, object]]:
    from app.modules.university_core.tenant_entity_impl import _list_entities_for_tenant_db_impl

    return _list_entities_for_tenant_db_impl(entity_name, tenant_id)


def _update_entity_for_tenant_db(
    entity_name: str, item_id: int, payload: dict[str, object], tenant_id: int
) -> dict[str, object]:
    from app.modules.university_core.tenant_entity_impl import _update_entity_for_tenant_db_impl

    return _update_entity_for_tenant_db_impl(entity_name, item_id, payload, tenant_id)


def _delete_entity_for_tenant_db(
    entity_name: str, item_id: int, tenant_id: int
) -> dict[str, object]:
    from app.modules.university_core.tenant_entity_impl import _delete_entity_for_tenant_db_impl

    return _delete_entity_for_tenant_db_impl(entity_name, item_id, tenant_id)


# ---------------------------------------------------------------------------
# Tenant-aware memory implementations
# ---------------------------------------------------------------------------

def _list_entities_for_tenant_memory(entity_name: str, tenant_id: int) -> list[dict[str, object]]:
    from app.modules.university_core.tenant_entity_impl import _list_entities_for_tenant_memory_impl

    return _list_entities_for_tenant_memory_impl(entity_name, tenant_id)


def _update_entity_for_tenant_memory(
    entity_name: str, item_id: int, payload: dict[str, object], tenant_id: int
) -> dict[str, object]:
    from app.modules.university_core.tenant_entity_impl import _update_entity_for_tenant_memory_impl

    return _update_entity_for_tenant_memory_impl(entity_name, item_id, payload, tenant_id)


def _delete_entity_for_tenant_memory(
    entity_name: str, item_id: int, tenant_id: int
) -> dict[str, object]:
    from app.modules.university_core.tenant_entity_impl import _delete_entity_for_tenant_memory_impl

    return _delete_entity_for_tenant_memory_impl(entity_name, item_id, tenant_id)


# ---------------------------------------------------------------------------
# Public tenant-aware API
# ---------------------------------------------------------------------------

def list_entities_for_tenant(entity_name: str, tenant_id: int) -> list[dict[str, object]]:
    """List entities filtered by tenant_id."""
    if entity_name not in ENTITY_CONFIGS:
        raise ValueError("unknown entity")
    _mark_university_core_usage("list_entities_for_tenant", entity_name, tenant_id)
    from app.modules.university_core.tenant_entity_impl import list_entities_for_tenant_impl

    return list_entities_for_tenant_impl(entity_name, tenant_id)


def create_entity_for_tenant(
    entity_name: str, payload: dict[str, object], tenant_id: int
) -> dict[str, object]:
    """Create entity with tenant_id forced from context (ignores any incoming tenant_id)."""
    if entity_name not in ENTITY_CONFIGS:
        raise ValueError("unknown entity")
    _mark_university_core_usage("create_entity_for_tenant", entity_name, tenant_id)
    from app.modules.university_core.tenant_entity_impl import create_entity_for_tenant_impl

    return create_entity_for_tenant_impl(entity_name, payload, tenant_id)


def update_entity_for_tenant(
    entity_name: str, item_id: int, payload: dict[str, object], tenant_id: int
) -> dict[str, object]:
    """Update entity, enforcing tenant ownership. Returns 404 if not found or wrong tenant."""
    if entity_name not in ENTITY_CONFIGS:
        raise ValueError("unknown entity")
    _mark_university_core_usage("update_entity_for_tenant", entity_name, tenant_id)
    from app.modules.university_core.tenant_entity_impl import update_entity_for_tenant_impl

    return update_entity_for_tenant_impl(entity_name, item_id, payload, tenant_id)


def delete_entity_for_tenant(
    entity_name: str, item_id: int, tenant_id: int
) -> dict[str, object]:
    """Delete entity, enforcing tenant ownership. Returns 404 if not found or wrong tenant."""
    if entity_name not in ENTITY_CONFIGS:
        raise ValueError("unknown entity")
    _mark_university_core_usage("delete_entity_for_tenant", entity_name, tenant_id)
    from app.modules.university_core.tenant_entity_impl import delete_entity_for_tenant_impl

    return delete_entity_for_tenant_impl(entity_name, item_id, tenant_id)
