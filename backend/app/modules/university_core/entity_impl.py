"""Non-tenant implementation layer for shared university entity CRUD.

This module hosts generic (non-tenant-scoped) CRUD behavior extracted
from `university_core.service` as part of C-007 decomposition.
"""

import os
import re
from datetime import datetime, timezone

from app.modules.university_core import shared as university_shared
from app.modules.university_core.business_rules import UniversityCoreRules


_SQL_IDENTIFIER_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


def _is_fail_closed_mode_impl() -> bool:
    """Return True when university_core should not degrade to in-memory fallback.

    Priority:
    1) Explicit UNIVERSITY_CORE_FAIL_CLOSED env override.
    2) Production mode via APP_ENV/ENVIRONMENT.
    """
    raw = os.getenv("UNIVERSITY_CORE_FAIL_CLOSED", "").strip().lower()
    if raw:
        return raw in {"1", "true", "yes", "on"}

    env_raw = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()
    return env_raw in {"prod", "production"}


def _db_url_impl() -> str | None:
    return os.getenv("DATABASE_URL")


def _use_database_impl() -> bool:
    return bool(_db_url_impl()) and university_shared.psycopg is not None


def _should_fallback_to_memory_impl(exc: Exception) -> bool:
    # In fail-closed mode (production by default), never degrade to in-memory
    # for DB/schema class errors because it breaks durable data guarantees.
    if _is_fail_closed_mode_impl() and university_shared.psycopg is not None and isinstance(
        exc,
        (
            university_shared.psycopg.OperationalError,
            university_shared.psycopg.InterfaceError,
            university_shared.psycopg.errors.UndefinedTable,
            university_shared.psycopg.ProgrammingError,
        ),
    ):
        return False

    if isinstance(exc, RuntimeError) and str(exc) == "database unavailable":
        return True
    if isinstance(exc, (ConnectionError, TimeoutError, OSError, ValueError)):
        return True
    if university_shared.psycopg is not None and isinstance(
        exc, (
            university_shared.psycopg.OperationalError,
            university_shared.psycopg.InterfaceError,
            university_shared.psycopg.errors.UndefinedTable,
            university_shared.psycopg.ProgrammingError,
        )
    ):
        return True
    return False


def _now_iso_impl() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_string_impl(name: str, value: object, max_len: int = 255) -> str:
    normalized = ("" if value is None else str(value)).strip()
    if not normalized:
        raise ValueError(f"{name} is required")
    if len(normalized) > max_len:
        raise ValueError(f"{name} must be at most {max_len} characters")
    return normalized


def _normalize_optional_tenant_impl(value: object) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None


def _normalize_payload_impl(entity_name: str, payload: dict[str, object]) -> dict[str, object]:
    config = university_shared.ENTITY_CONFIGS[entity_name]
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

        if field_name not in config.required and (raw_value is None or raw_value == ""):
            normalized[field_name] = None
            continue
        normalized[field_name] = _normalize_string_impl(field_name, raw_value)

    email_value = normalized.get("email")
    if isinstance(email_value, str) and "@" not in email_value:
        raise ValueError("email must contain @")

    if "start_date" in config.fields and "end_date" in config.fields:
        UniversityCoreRules.validate_end_after_start(
            str(normalized.get("start_date") or "") or None,
            str(normalized.get("end_date") or "") or None,
            entity_name=entity_name,
        )

    return normalized


def _memory_fk_exists_impl(entity_name: str, item_id: int) -> bool:
    return item_id in university_shared._state.data[entity_name]


def _validate_foreign_keys_memory_impl(entity_name: str, payload: dict[str, object]) -> None:
    config = university_shared.ENTITY_CONFIGS[entity_name]
    if "program_id" in config.fk_fields and not _memory_fk_exists_impl("programs", int(payload["program_id"])):
        raise ValueError("program_id references unknown program")
    if "student_id" in config.fk_fields and not _memory_fk_exists_impl("students", int(payload["student_id"])):
        raise ValueError("student_id references unknown student")
    if "course_id" in config.fk_fields and not _memory_fk_exists_impl("courses", int(payload["course_id"])):
        raise ValueError("course_id references unknown course")


def _db_fetch_exists_impl(conn, table: str, item_id: int) -> bool:
    with conn.cursor() as cur:
        query = university_shared.psycopg.sql.SQL("SELECT 1 FROM {} WHERE id = %s").format(
            _sql_identifier_impl(table)
        )
        cur.execute(query, (item_id,))
        return cur.fetchone() is not None


def _validate_foreign_keys_db_impl(conn, entity_name: str, payload: dict[str, object]) -> None:
    config = university_shared.ENTITY_CONFIGS[entity_name]

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
        value = row[offset + index]
        # tenant_id is stored as BIGINT in some tables but schemas expect str
        if field_name == "tenant_id" and isinstance(value, int):
            value = str(value)
        result[field_name] = value
    return result


def _sql_identifier_impl(name: str):
    if university_shared.psycopg is None:
        raise RuntimeError("database unavailable")
    normalized = str(name or "").strip()
    if not _SQL_IDENTIFIER_RE.fullmatch(normalized):
        raise ValueError(f"unsafe SQL identifier: {normalized}")
    return university_shared.psycopg.sql.Identifier(normalized)


def _sql_identifier_list_impl(names: list[str] | tuple[str, ...]):
    if university_shared.psycopg is None:
        raise RuntimeError("database unavailable")
    return university_shared.psycopg.sql.SQL(", ").join(_sql_identifier_impl(name) for name in names)


def _list_entities_db_impl(entity_name: str, max_limit: int = 200) -> list[dict[str, object]]:
    if not _db_url_impl() or university_shared.psycopg is None:
        raise RuntimeError("database unavailable")

    config = university_shared.ENTITY_CONFIGS[entity_name]
    include_created_at = entity_name == "students"
    selected_columns = ["id"]
    if include_created_at:
        selected_columns.append("created_at")
    selected_columns.extend(config.fields)

    with university_shared.get_raw_conn() as conn:
        with conn.cursor() as cur:
            query = university_shared.psycopg.sql.SQL("SELECT {} FROM {} ORDER BY id ASC LIMIT %s").format(
                _sql_identifier_list_impl(selected_columns),
                _sql_identifier_impl(config.table),
            )
            cur.execute(query, (max_limit,))
            rows = cur.fetchall()

    return [_row_to_dict_impl(row, config.fields, include_created_at) for row in rows]


def _create_entity_db_impl(entity_name: str, payload: dict[str, object]) -> dict[str, object]:
    if not _db_url_impl() or university_shared.psycopg is None:
        raise RuntimeError("database unavailable")

    config = university_shared.ENTITY_CONFIGS[entity_name]
    include_created_at = entity_name == "students"
    returning_columns = ["id"]
    if include_created_at:
        returning_columns.append("created_at")
    returning_columns.extend(config.fields)

    with university_shared.get_raw_conn() as conn:
        _validate_foreign_keys_db_impl(conn, entity_name, payload)
        with conn.cursor() as cur:
            columns = list(config.fields)
            values = [payload[column] for column in columns]
            query = university_shared.psycopg.sql.SQL(
                "INSERT INTO {} ({}) VALUES ({}) RETURNING {}"
            ).format(
                _sql_identifier_impl(config.table),
                _sql_identifier_list_impl(columns),
                university_shared.psycopg.sql.SQL(", ").join(university_shared.psycopg.sql.Placeholder() for _ in columns),
                _sql_identifier_list_impl(returning_columns),
            )
            cur.execute(query, values)
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise RuntimeError(f"failed to create {entity_name}")
    return _row_to_dict_impl(row, config.fields, include_created_at)


def _update_entity_db_impl(entity_name: str, item_id: int, payload: dict[str, object]) -> dict[str, object]:
    if not _db_url_impl() or university_shared.psycopg is None:
        raise RuntimeError("database unavailable")

    config = university_shared.ENTITY_CONFIGS[entity_name]
    include_created_at = entity_name == "students"
    returning_columns = ["id"]
    if include_created_at:
        returning_columns.append("created_at")
    returning_columns.extend(config.fields)

    with university_shared.get_raw_conn() as conn:
        _validate_foreign_keys_db_impl(conn, entity_name, payload)
        with conn.cursor() as cur:
            assignments = [
                university_shared.psycopg.sql.SQL("{} = %s").format(_sql_identifier_impl(column))
                for column in config.fields
            ]
            values = [payload[column] for column in config.fields]
            values.append(item_id)
            query = university_shared.psycopg.sql.SQL("UPDATE {} SET {} WHERE id = %s RETURNING {}").format(
                _sql_identifier_impl(config.table),
                university_shared.psycopg.sql.SQL(", ").join(assignments),
                _sql_identifier_list_impl(returning_columns),
            )
            cur.execute(query, values)
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise ValueError(f"{entity_name.rstrip('s')} not found")
    return _row_to_dict_impl(row, config.fields, include_created_at)


def _delete_entity_db_impl(entity_name: str, item_id: int) -> dict[str, object]:
    if not _db_url_impl() or university_shared.psycopg is None:
        raise RuntimeError("database unavailable")

    config = university_shared.ENTITY_CONFIGS[entity_name]
    include_created_at = entity_name == "students"
    returning_columns = ["id"]
    if include_created_at:
        returning_columns.append("created_at")
    returning_columns.extend(config.fields)

    with university_shared.get_raw_conn() as conn:
        with conn.cursor() as cur:
            query = university_shared.psycopg.sql.SQL("DELETE FROM {} WHERE id = %s RETURNING {}").format(
                _sql_identifier_impl(config.table),
                _sql_identifier_list_impl(returning_columns),
            )
            cur.execute(query, (item_id,))
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise ValueError(f"{entity_name.rstrip('s')} not found")
    return _row_to_dict_impl(row, config.fields, include_created_at)


def list_entities_impl(entity_name: str, max_limit: int = 200) -> list[dict[str, object]]:
    if entity_name not in university_shared.ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    if _use_database_impl():
        try:
            return _list_entities_db_impl(entity_name, max_limit=max_limit)
        except Exception as exc:
            if not _should_fallback_to_memory_impl(exc):
                raise

    with university_shared._state_lock:
        rows = list(university_shared._state.data[entity_name].values())
    rows.sort(key=lambda row: int(row["id"]))
    return rows[:max_limit]


def create_entity_impl(entity_name: str, payload: dict[str, object]) -> dict[str, object]:
    if entity_name not in university_shared.ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    normalized = _normalize_payload_impl(entity_name, payload)

    if _use_database_impl():
        try:
            return _create_entity_db_impl(entity_name, normalized)
        except Exception as exc:
            if not _should_fallback_to_memory_impl(exc):
                raise

    with university_shared._state_lock:
        _validate_foreign_keys_memory_impl(entity_name, normalized)
        university_shared._state.counters[entity_name] += 1
        item_id = university_shared._state.counters[entity_name]
        row: dict[str, object] = {"id": item_id, **normalized}
        if entity_name == "students":
            row["created_at"] = _now_iso_impl()
        university_shared._state.data[entity_name][item_id] = row
        return row


def update_entity_impl(entity_name: str, item_id: int, payload: dict[str, object]) -> dict[str, object]:
    if entity_name not in university_shared.ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    normalized = _normalize_payload_impl(entity_name, payload)

    if _use_database_impl():
        try:
            return _update_entity_db_impl(entity_name, item_id, normalized)
        except Exception as exc:
            if not _should_fallback_to_memory_impl(exc):
                raise

    with university_shared._state_lock:
        _validate_foreign_keys_memory_impl(entity_name, normalized)
        current = university_shared._state.data[entity_name].get(item_id)
        if current is None:
            raise ValueError(f"{entity_name.rstrip('s')} not found")

        updated = {"id": item_id, **normalized}
        if entity_name == "students":
            updated["created_at"] = current.get("created_at") or _now_iso_impl()
        university_shared._state.data[entity_name][item_id] = updated
        return updated


def delete_entity_impl(entity_name: str, item_id: int) -> dict[str, object]:
    if entity_name not in university_shared.ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    if _use_database_impl():
        try:
            return _delete_entity_db_impl(entity_name, item_id)
        except Exception as exc:
            if not _should_fallback_to_memory_impl(exc):
                raise

    with university_shared._state_lock:
        current = university_shared._state.data[entity_name].pop(item_id, None)
        if current is None:
            raise ValueError(f"{entity_name.rstrip('s')} not found")
        return current


def validate_entity_tables_impl() -> dict[str, list[str]]:
    """Check that every table referenced in ENTITY_CONFIGS exists in the database.

    Returns a dict with two keys:
    - "missing": DB-required table names absent from the DB.
    - "present": DB-required table names found.
    - "missing_fallback": fallback-allowed table names absent from the DB.
    - "present_fallback": fallback-allowed table names found.

    If the database is not configured or psycopg is unavailable the function
    returns immediately with empty lists (no-op; will be logged by the caller).
    """
    import logging as _logging

    _log = _logging.getLogger(__name__)

    missing: list[str] = []
    present: list[str] = []
    missing_fallback: list[str] = []
    present_fallback: list[str] = []

    if not _use_database_impl():
        return {
            "missing": missing,
            "present": present,
            "missing_fallback": missing_fallback,
            "present_fallback": present_fallback,
        }

    db_url = _db_url_impl()
    assert db_url is not None  # narrowing — _use_database_impl already checked

    try:
        with university_shared.psycopg.connect(db_url) as conn:
            conn.autocommit = True
            rows = conn.execute(
                university_shared.psycopg.sql.SQL(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public'"
                )
            ).fetchall()
            db_tables = {r[0] for r in rows}
    except Exception as exc:  # pragma: no cover
        if _is_fail_closed_mode_impl():
            raise RuntimeError(
                "university_core: table-existence validation failed in fail-closed mode"
            ) from exc
        _log.warning("university_core: table-existence validation skipped — DB error: %s", exc)
        return {
            "missing": missing,
            "present": present,
            "missing_fallback": missing_fallback,
            "present_fallback": present_fallback,
        }

    for _entity_name, cfg in university_shared.ENTITY_CONFIGS.items():
        if cfg.table in db_tables:
            if cfg.table in university_shared.REQUIRED_DB_TABLES:
                present.append(cfg.table)
            else:
                present_fallback.append(cfg.table)
        else:
            if cfg.table in university_shared.REQUIRED_DB_TABLES:
                missing.append(cfg.table)
            else:
                missing_fallback.append(cfg.table)

    if missing:
        if _is_fail_closed_mode_impl():
            raise RuntimeError(
                "university_core: missing required entity tables in fail-closed mode: "
                + ", ".join(sorted(missing))
            )
        _log.warning(
            "university_core: %d REQUIRED entity table(s) missing from database: %s",
            len(missing),
            ", ".join(sorted(missing)),
        )
    elif present:
        _log.info(
            "university_core: all %d required entity tables verified in database", len(present)
        )

    if missing_fallback:
        _log.warning(
            "university_core: %d fallback-allowed entity table(s) absent from database — "
            "CRUD calls may use in-memory store: %s",
            len(missing_fallback),
            ", ".join(sorted(missing_fallback)),
        )

    return {
        "missing": missing,
        "present": present,
        "missing_fallback": missing_fallback,
        "present_fallback": present_fallback,
    }


__all__ = [
    "_db_url_impl",
    "_use_database_impl",
    "_is_fail_closed_mode_impl",
    "_should_fallback_to_memory_impl",
    "_now_iso_impl",
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
    "validate_entity_tables_impl",
]
