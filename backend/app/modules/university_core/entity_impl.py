"""Non-tenant implementation layer for shared university entity CRUD.

This module hosts generic (non-tenant-scoped) CRUD behavior extracted
from `university_core.service` as part of C-007 decomposition.
"""

import re

from app.modules.university_core import service as university_service


_SQL_IDENTIFIER_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


def _normalize_string_impl(name: str, value: object, max_len: int = 255) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{name} is required")
    if len(normalized) > max_len:
        raise ValueError(f"{name} must be at most {max_len} characters")
    return normalized


def _normalize_optional_tenant_impl(value: object) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None


def _normalize_payload_impl(entity_name: str, payload: dict[str, object]) -> dict[str, object]:
    config = university_service.ENTITY_CONFIGS[entity_name]
    normalized: dict[str, object] = {}

    for field_name in config.required:
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")

    for field_name in config.fields:
        raw_value = payload.get(field_name)

        if field_name == "tenant_id":
            normalized[field_name] = _normalize_optional_tenant_impl(raw_value)
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

        normalized[field_name] = _normalize_string_impl(field_name, raw_value)

    email_value = normalized.get("email")
    if isinstance(email_value, str) and "@" not in email_value:
        raise ValueError("email must contain @")

    return normalized


def _memory_fk_exists_impl(entity_name: str, item_id: int) -> bool:
    return item_id in university_service._state.data[entity_name]


def _validate_foreign_keys_memory_impl(entity_name: str, payload: dict[str, object]) -> None:
    config = university_service.ENTITY_CONFIGS[entity_name]
    if "program_id" in config.fk_fields and not _memory_fk_exists_impl("programs", int(payload["program_id"])):
        raise ValueError("program_id references unknown program")
    if "student_id" in config.fk_fields and not _memory_fk_exists_impl("students", int(payload["student_id"])):
        raise ValueError("student_id references unknown student")
    if "course_id" in config.fk_fields and not _memory_fk_exists_impl("courses", int(payload["course_id"])):
        raise ValueError("course_id references unknown course")


def _db_fetch_exists_impl(conn, table: str, item_id: int) -> bool:
    with conn.cursor() as cur:
        query = university_service.psycopg.sql.SQL("SELECT 1 FROM {} WHERE id = %s").format(
            _sql_identifier_impl(table)
        )
        cur.execute(query, (item_id,))
        return cur.fetchone() is not None


def _validate_foreign_keys_db_impl(conn, entity_name: str, payload: dict[str, object]) -> None:
    config = university_service.ENTITY_CONFIGS[entity_name]

    if "program_id" in config.fk_fields:
        program_id = int(payload["program_id"])
        if not _db_fetch_exists_impl(conn, "university_programs", program_id):
            raise ValueError("program_id references unknown program")

    if "student_id" in config.fk_fields:
        student_id = int(payload["student_id"])
        if not _db_fetch_exists_impl(conn, "university_students", student_id):
            raise ValueError("student_id references unknown student")

    if "course_id" in config.fk_fields:
        course_id = int(payload["course_id"])
        if not _db_fetch_exists_impl(conn, "university_courses", course_id):
            raise ValueError("course_id references unknown course")


def _row_to_dict_impl(
    row: tuple[object, ...], fields: tuple[str, ...], include_created_at: bool
) -> dict[str, object]:
    result: dict[str, object] = {"id": int(row[0])}
    offset = 1
    if include_created_at:
        created_at = row[offset]
        result["created_at"] = created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at)
        offset += 1

    for index, field_name in enumerate(fields):
        result[field_name] = row[offset + index]
    return result


def _sql_identifier_impl(name: str):
    if university_service.psycopg is None:
        raise RuntimeError("database unavailable")
    normalized = str(name or "").strip()
    if not _SQL_IDENTIFIER_RE.fullmatch(normalized):
        raise ValueError(f"unsafe SQL identifier: {normalized}")
    return university_service.psycopg.sql.Identifier(normalized)


def _sql_identifier_list_impl(names: list[str] | tuple[str, ...]):
    if university_service.psycopg is None:
        raise RuntimeError("database unavailable")
    return university_service.psycopg.sql.SQL(", ").join(_sql_identifier_impl(name) for name in names)


def _list_entities_db_impl(entity_name: str) -> list[dict[str, object]]:
    if not university_service._db_url() or university_service.psycopg is None:
        raise RuntimeError("database unavailable")

    config = university_service.ENTITY_CONFIGS[entity_name]
    include_created_at = entity_name == "students"
    selected_columns = ["id"]
    if include_created_at:
        selected_columns.append("created_at")
    selected_columns.extend(config.fields)

    with university_service.get_raw_conn() as conn:
        with conn.cursor() as cur:
            query = university_service.psycopg.sql.SQL("SELECT {} FROM {} ORDER BY id ASC").format(
                _sql_identifier_list_impl(selected_columns),
                _sql_identifier_impl(config.table),
            )
            cur.execute(query)
            rows = cur.fetchall()

    return [_row_to_dict_impl(row, config.fields, include_created_at) for row in rows]


def _create_entity_db_impl(entity_name: str, payload: dict[str, object]) -> dict[str, object]:
    if not university_service._db_url() or university_service.psycopg is None:
        raise RuntimeError("database unavailable")

    config = university_service.ENTITY_CONFIGS[entity_name]
    include_created_at = entity_name == "students"
    returning_columns = ["id"]
    if include_created_at:
        returning_columns.append("created_at")
    returning_columns.extend(config.fields)

    with university_service.get_raw_conn() as conn:
        _validate_foreign_keys_db_impl(conn, entity_name, payload)
        with conn.cursor() as cur:
            columns = list(config.fields)
            values = [payload[column] for column in columns]
            query = university_service.psycopg.sql.SQL(
                "INSERT INTO {} ({}) VALUES ({}) RETURNING {}"
            ).format(
                _sql_identifier_impl(config.table),
                _sql_identifier_list_impl(columns),
                university_service.psycopg.sql.SQL(", ").join(university_service.psycopg.sql.Placeholder() for _ in columns),
                _sql_identifier_list_impl(returning_columns),
            )
            cur.execute(query, values)
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise RuntimeError(f"failed to create {entity_name}")
    return _row_to_dict_impl(row, config.fields, include_created_at)


def _update_entity_db_impl(entity_name: str, item_id: int, payload: dict[str, object]) -> dict[str, object]:
    if not university_service._db_url() or university_service.psycopg is None:
        raise RuntimeError("database unavailable")

    config = university_service.ENTITY_CONFIGS[entity_name]
    include_created_at = entity_name == "students"
    returning_columns = ["id"]
    if include_created_at:
        returning_columns.append("created_at")
    returning_columns.extend(config.fields)

    with university_service.get_raw_conn() as conn:
        _validate_foreign_keys_db_impl(conn, entity_name, payload)
        with conn.cursor() as cur:
            assignments = [
                university_service.psycopg.sql.SQL("{} = %s").format(_sql_identifier_impl(column))
                for column in config.fields
            ]
            values = [payload[column] for column in config.fields]
            values.append(item_id)
            query = university_service.psycopg.sql.SQL("UPDATE {} SET {} WHERE id = %s RETURNING {}").format(
                _sql_identifier_impl(config.table),
                university_service.psycopg.sql.SQL(", ").join(assignments),
                _sql_identifier_list_impl(returning_columns),
            )
            cur.execute(query, values)
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise ValueError(f"{entity_name.rstrip('s')} not found")
    return _row_to_dict_impl(row, config.fields, include_created_at)


def _delete_entity_db_impl(entity_name: str, item_id: int) -> dict[str, object]:
    if not university_service._db_url() or university_service.psycopg is None:
        raise RuntimeError("database unavailable")

    config = university_service.ENTITY_CONFIGS[entity_name]
    include_created_at = entity_name == "students"
    returning_columns = ["id"]
    if include_created_at:
        returning_columns.append("created_at")
    returning_columns.extend(config.fields)

    with university_service.get_raw_conn() as conn:
        with conn.cursor() as cur:
            query = university_service.psycopg.sql.SQL("DELETE FROM {} WHERE id = %s RETURNING {}").format(
                _sql_identifier_impl(config.table),
                _sql_identifier_list_impl(returning_columns),
            )
            cur.execute(query, (item_id,))
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise ValueError(f"{entity_name.rstrip('s')} not found")
    return _row_to_dict_impl(row, config.fields, include_created_at)


def list_entities_impl(entity_name: str) -> list[dict[str, object]]:
    if entity_name not in university_service.ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    if university_service._use_database():
        try:
            return _list_entities_db_impl(entity_name)
        except Exception as exc:
            if not university_service._should_fallback_to_memory(exc):
                raise

    with university_service._state_lock:
        rows = list(university_service._state.data[entity_name].values())
    rows.sort(key=lambda row: int(row["id"]))
    return rows


def create_entity_impl(entity_name: str, payload: dict[str, object]) -> dict[str, object]:
    if entity_name not in university_service.ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    normalized = _normalize_payload_impl(entity_name, payload)

    if university_service._use_database():
        try:
            return _create_entity_db_impl(entity_name, normalized)
        except Exception as exc:
            if not university_service._should_fallback_to_memory(exc):
                raise

    with university_service._state_lock:
        _validate_foreign_keys_memory_impl(entity_name, normalized)
        university_service._state.counters[entity_name] += 1
        item_id = university_service._state.counters[entity_name]
        row: dict[str, object] = {"id": item_id, **normalized}
        if entity_name == "students":
            row["created_at"] = university_service._now_iso()
        university_service._state.data[entity_name][item_id] = row
        return row


def update_entity_impl(entity_name: str, item_id: int, payload: dict[str, object]) -> dict[str, object]:
    if entity_name not in university_service.ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    normalized = _normalize_payload_impl(entity_name, payload)

    if university_service._use_database():
        try:
            return _update_entity_db_impl(entity_name, item_id, normalized)
        except Exception as exc:
            if not university_service._should_fallback_to_memory(exc):
                raise

    with university_service._state_lock:
        _validate_foreign_keys_memory_impl(entity_name, normalized)
        current = university_service._state.data[entity_name].get(item_id)
        if current is None:
            raise ValueError(f"{entity_name.rstrip('s')} not found")

        updated = {"id": item_id, **normalized}
        if entity_name == "students":
            updated["created_at"] = current.get("created_at") or university_service._now_iso()
        university_service._state.data[entity_name][item_id] = updated
        return updated


def delete_entity_impl(entity_name: str, item_id: int) -> dict[str, object]:
    if entity_name not in university_service.ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    if university_service._use_database():
        try:
            return _delete_entity_db_impl(entity_name, item_id)
        except Exception as exc:
            if not university_service._should_fallback_to_memory(exc):
                raise

    with university_service._state_lock:
        current = university_service._state.data[entity_name].pop(item_id, None)
        if current is None:
            raise ValueError(f"{entity_name.rstrip('s')} not found")
        return current


__all__ = [
    "_row_to_dict_impl",
    "_sql_identifier_impl",
    "_sql_identifier_list_impl",
    "_normalize_string_impl",
    "_normalize_optional_tenant_impl",
    "_normalize_payload_impl",
    "_memory_fk_exists_impl",
    "_validate_foreign_keys_memory_impl",
    "_db_fetch_exists_impl",
    "_validate_foreign_keys_db_impl",
    "_list_entities_db_impl",
    "_create_entity_db_impl",
    "_update_entity_db_impl",
    "_delete_entity_db_impl",
    "list_entities_impl",
    "create_entity_impl",
    "update_entity_impl",
    "delete_entity_impl",
]
