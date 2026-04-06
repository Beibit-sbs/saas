"""Tenant-aware implementation layer for university entity CRUD.

This module hosts the concrete tenant-scoped behavior extracted from
`university_core.service` during C-007 phased decomposition.
"""

from app.modules.university_core import service as university_service


def _list_entities_for_tenant_db_impl(entity_name: str, tenant_id: int) -> list[dict[str, object]]:
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
            query = university_service.psycopg.sql.SQL("SELECT {} FROM {} WHERE tenant_id = %s ORDER BY id ASC").format(
                university_service._sql_identifier_list(selected_columns),
                university_service._sql_identifier(config.table),
            )
            cur.execute(query, (str(tenant_id),))
            rows = cur.fetchall()

    return [university_service._row_to_dict(row, config.fields, include_created_at) for row in rows]


def _update_entity_for_tenant_db_impl(
    entity_name: str, item_id: int, payload: dict[str, object], tenant_id: int
) -> dict[str, object]:
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
            values: list[object] = [payload[column] for column in config.fields]
            values.extend([item_id, str(tenant_id)])
            query = university_service.psycopg.sql.SQL(
                "UPDATE {} SET {} WHERE id = %s AND tenant_id = %s RETURNING {}"
            ).format(
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


def _delete_entity_for_tenant_db_impl(
    entity_name: str, item_id: int, tenant_id: int
) -> dict[str, object]:
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
            query = university_service.psycopg.sql.SQL(
                "DELETE FROM {} WHERE id = %s AND tenant_id = %s RETURNING {}"
            ).format(
                university_service._sql_identifier(config.table),
                university_service._sql_identifier_list(returning_columns),
            )
            cur.execute(query, (item_id, str(tenant_id)))
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise ValueError(f"{entity_name.rstrip('s')} not found")
    return university_service._row_to_dict(row, config.fields, include_created_at)


def _list_entities_for_tenant_memory_impl(entity_name: str, tenant_id: int) -> list[dict[str, object]]:
    tid = str(tenant_id)
    with university_service._state_lock:
        rows = [
            dict(r)
            for r in university_service._state.data[entity_name].values()
            if str(r.get("tenant_id", "")) == tid
        ]
    rows.sort(key=lambda r: int(r["id"]))  # type: ignore[arg-type]
    return rows


def _update_entity_for_tenant_memory_impl(
    entity_name: str, item_id: int, payload: dict[str, object], tenant_id: int
) -> dict[str, object]:
    tid = str(tenant_id)
    with university_service._state_lock:
        university_service._validate_foreign_keys_memory(entity_name, payload)
        current = university_service._state.data[entity_name].get(item_id)
        if current is None or str(current.get("tenant_id", "")) != tid:
            raise ValueError(f"{entity_name.rstrip('s')} not found")
        updated: dict[str, object] = {"id": item_id, **payload}
        if entity_name == "students":
            updated["created_at"] = current.get("created_at") or university_service._now_iso()
        university_service._state.data[entity_name][item_id] = updated
        return dict(updated)


def _delete_entity_for_tenant_memory_impl(
    entity_name: str, item_id: int, tenant_id: int
) -> dict[str, object]:
    tid = str(tenant_id)
    with university_service._state_lock:
        current = university_service._state.data[entity_name].get(item_id)
        if current is None or str(current.get("tenant_id", "")) != tid:
            raise ValueError(f"{entity_name.rstrip('s')} not found")
        del university_service._state.data[entity_name][item_id]
        return dict(current)


def list_entities_for_tenant_impl(entity_name: str, tenant_id: int) -> list[dict[str, object]]:
    """List entities filtered by tenant_id."""
    if entity_name not in university_service.ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    if university_service._use_database():
        try:
            return _list_entities_for_tenant_db_impl(entity_name, tenant_id)
        except Exception as exc:
            if not university_service._should_fallback_to_memory(exc):
                raise

    return _list_entities_for_tenant_memory_impl(entity_name, tenant_id)


def create_entity_for_tenant_impl(
    entity_name: str,
    payload: dict[str, object],
    tenant_id: int,
) -> dict[str, object]:
    """Create entity with tenant_id forced from context (ignores incoming tenant_id)."""
    if entity_name not in university_service.ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    payload_with_tenant: dict[str, object] = {**payload, "tenant_id": str(tenant_id)}
    normalized = university_service._normalize_payload(entity_name, payload_with_tenant)

    if university_service._use_database():
        try:
            return university_service._create_entity_db(entity_name, normalized)
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
        return dict(row)


def update_entity_for_tenant_impl(
    entity_name: str,
    item_id: int,
    payload: dict[str, object],
    tenant_id: int,
) -> dict[str, object]:
    """Update entity, enforcing tenant ownership."""
    if entity_name not in university_service.ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    payload_with_tenant: dict[str, object] = {**payload, "tenant_id": str(tenant_id)}
    normalized = university_service._normalize_payload(entity_name, payload_with_tenant)

    if university_service._use_database():
        try:
            return _update_entity_for_tenant_db_impl(entity_name, item_id, normalized, tenant_id)
        except Exception as exc:
            if not university_service._should_fallback_to_memory(exc):
                raise

    return _update_entity_for_tenant_memory_impl(entity_name, item_id, normalized, tenant_id)


def delete_entity_for_tenant_impl(
    entity_name: str,
    item_id: int,
    tenant_id: int,
) -> dict[str, object]:
    """Delete entity, enforcing tenant ownership."""
    if entity_name not in university_service.ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    if university_service._use_database():
        try:
            return _delete_entity_for_tenant_db_impl(entity_name, item_id, tenant_id)
        except Exception as exc:
            if not university_service._should_fallback_to_memory(exc):
                raise

    return _delete_entity_for_tenant_memory_impl(entity_name, item_id, tenant_id)


__all__ = [
    "_list_entities_for_tenant_db_impl",
    "_update_entity_for_tenant_db_impl",
    "_delete_entity_for_tenant_db_impl",
    "_list_entities_for_tenant_memory_impl",
    "_update_entity_for_tenant_memory_impl",
    "_delete_entity_for_tenant_memory_impl",
    "list_entities_for_tenant_impl",
    "create_entity_for_tenant_impl",
    "update_entity_for_tenant_impl",
    "delete_entity_for_tenant_impl",
]
