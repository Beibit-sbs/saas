from __future__ import annotations
import logging

from dataclasses import dataclass, field
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
    from app.modules.university_core.entity_impl import _db_url_impl

    return _db_url_impl()


def _use_database() -> bool:
    from app.modules.university_core.entity_impl import _use_database_impl

    return _use_database_impl()


def _should_fallback_to_memory(exc: Exception) -> bool:
    from app.modules.university_core.entity_impl import _should_fallback_to_memory_impl

    return _should_fallback_to_memory_impl(exc)


def _now_iso() -> str:
    from app.modules.university_core.entity_impl import _now_iso_impl

    return _now_iso_impl()


def _normalize_string(name: str, value: object, max_len: int = 255) -> str:
    from app.modules.university_core.entity_impl import _normalize_string_impl

    return _normalize_string_impl(name, value, max_len)


def _normalize_optional_tenant(value: object) -> str | None:
    from app.modules.university_core.entity_impl import _normalize_optional_tenant_impl

    return _normalize_optional_tenant_impl(value)


def _normalize_payload(entity_name: str, payload: dict[str, object]) -> dict[str, object]:
    from app.modules.university_core.entity_impl import _normalize_payload_impl

    return _normalize_payload_impl(entity_name, payload)


def _row_to_dict(row: tuple[Any, ...], fields: tuple[str, ...], include_created_at: bool) -> dict[str, object]:
    from app.modules.university_core.entity_impl import _row_to_dict_impl

    return _row_to_dict_impl(row, fields, include_created_at)


def _sql_identifier(name: str):
    from app.modules.university_core.entity_impl import _sql_identifier_impl

    return _sql_identifier_impl(name)


def _sql_identifier_list(names: list[str] | tuple[str, ...]):
    from app.modules.university_core.entity_impl import _sql_identifier_list_impl

    return _sql_identifier_list_impl(names)


def _db_fetch_exists(conn, table: str, item_id: int) -> bool:
    from app.modules.university_core.entity_impl import _db_fetch_exists_impl

    return _db_fetch_exists_impl(conn, table, item_id)


def _validate_foreign_keys_db(conn, entity_name: str, payload: dict[str, object]) -> None:
    from app.modules.university_core.entity_impl import _validate_foreign_keys_db_impl

    return _validate_foreign_keys_db_impl(conn, entity_name, payload)


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
