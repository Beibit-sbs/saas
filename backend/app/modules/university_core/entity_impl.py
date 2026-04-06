"""Non-tenant implementation layer for shared university entity CRUD.

This module hosts generic (non-tenant-scoped) CRUD behavior extracted
from `university_core.service` as part of C-007 decomposition.
"""

from app.modules.university_core import service as university_service


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
                university_service._sql_identifier_list(selected_columns),
                university_service._sql_identifier(config.table),
            )
            cur.execute(query)
            rows = cur.fetchall()

    return [university_service._row_to_dict(row, config.fields, include_created_at) for row in rows]


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
        university_service._validate_foreign_keys_db(conn, entity_name, payload)
        with conn.cursor() as cur:
            columns = list(config.fields)
            values = [payload[column] for column in columns]
            query = university_service.psycopg.sql.SQL(
                "INSERT INTO {} ({}) VALUES ({}) RETURNING {}"
            ).format(
                university_service._sql_identifier(config.table),
                university_service._sql_identifier_list(columns),
                university_service.psycopg.sql.SQL(", ").join(university_service.psycopg.sql.Placeholder() for _ in columns),
                university_service._sql_identifier_list(returning_columns),
            )
            cur.execute(query, values)
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise RuntimeError(f"failed to create {entity_name}")
    return university_service._row_to_dict(row, config.fields, include_created_at)


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
        university_service._validate_foreign_keys_db(conn, entity_name, payload)
        with conn.cursor() as cur:
            assignments = [
                university_service.psycopg.sql.SQL("{} = %s").format(university_service._sql_identifier(column))
                for column in config.fields
            ]
            values = [payload[column] for column in config.fields]
            values.append(item_id)
            query = university_service.psycopg.sql.SQL("UPDATE {} SET {} WHERE id = %s RETURNING {}").format(
                university_service._sql_identifier(config.table),
                university_service.psycopg.sql.SQL(", ").join(assignments),
                university_service._sql_identifier_list(returning_columns),
            )
            cur.execute(query, values)
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise ValueError(f"{entity_name.rstrip('s')} not found")
    return university_service._row_to_dict(row, config.fields, include_created_at)


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
                university_service._sql_identifier(config.table),
                university_service._sql_identifier_list(returning_columns),
            )
            cur.execute(query, (item_id,))
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise ValueError(f"{entity_name.rstrip('s')} not found")
    return university_service._row_to_dict(row, config.fields, include_created_at)


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

    normalized = university_service._normalize_payload(entity_name, payload)

    if university_service._use_database():
        try:
            return _create_entity_db_impl(entity_name, normalized)
        except Exception as exc:
            if not university_service._should_fallback_to_memory(exc):
                raise

    with university_service._state_lock:
        university_service._validate_foreign_keys_memory(entity_name, normalized)
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

    normalized = university_service._normalize_payload(entity_name, payload)

    if university_service._use_database():
        try:
            return _update_entity_db_impl(entity_name, item_id, normalized)
        except Exception as exc:
            if not university_service._should_fallback_to_memory(exc):
                raise

    with university_service._state_lock:
        university_service._validate_foreign_keys_memory(entity_name, normalized)
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
    "_list_entities_db_impl",
    "_create_entity_db_impl",
    "_update_entity_db_impl",
    "_delete_entity_db_impl",
    "list_entities_impl",
    "create_entity_impl",
    "update_entity_impl",
    "delete_entity_impl",
]
