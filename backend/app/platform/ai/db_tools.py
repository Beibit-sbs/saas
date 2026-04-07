"""Read-only DB introspection tools for the AI copilot.

All queries run through the caller-supplied psycopg connection.
Safety invariants:
  - Only tables listed in ALLOWED_TABLES may be accessed.
  - Columns listed in PII_COLUMNS are always redacted in any row-level return.
  - Only COUNT(*) GROUP BY aggregates are generated; no full row-level dumps.
  - SQL identifiers are validated against a strict regex before interpolation.

These tools are intentionally *not* connected to the ORM so they remain
safe and lightweight when used from the internal MCP endpoint.
"""
from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# Policy: which columns are PII and must never be surfaced to the AI layer
# ---------------------------------------------------------------------------
PII_COLUMNS: frozenset[str] = frozenset(
    {
        "email",
        "name",
        "full_name",
        "first_name",
        "last_name",
        "phone",
        "phone_number",
        "address",
        "date_of_birth",
        "dob",
        "iin",
        "national_id",
        "passport_number",
        "password",
        "password_hash",
        "hashed_password",
        "secret",
        "token",
        "refresh_token",
        "access_token",
        "api_key",
        "signing_key",
        "private_key",
    }
)

# ---------------------------------------------------------------------------
# Policy: which tables the AI may introspect / query
# (must not include tables with direct PII top-level columns, e.g. local_users)
# ---------------------------------------------------------------------------
ALLOWED_TABLES: frozenset[str] = frozenset(
    {
        "app_platform_context_entities",
        "app_platform_context_relations",
        "app_platform_kpi_snapshots",
        "app_platform_jobs",
        "app_platform_notifications",
        "app_platform_automation_rules",
        "app_platform_automation_executions",
        "app_platform_audit_events",
        "app_platform_feature_flags",
        "app_platform_tenants",
        "app_platform_analytics_snapshots",
        "app_platform_outbox_events",
        "app_platform_webhook_subscriptions",
    }
)

MAX_AGGREGATE_ROWS: int = 50

# Validates SQL identifiers (table / column names) before interpolation.
_SAFE_IDENTIFIER: re.Pattern[str] = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,63}$")


def _safe_ident(name: str) -> str:
    """Return *name* if it passes the identifier whitelist, else raise ValueError."""
    if not _SAFE_IDENTIFIER.match(name):
        raise ValueError(f"unsafe SQL identifier: {name!r}")
    return name


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def redact_row(row: dict[str, Any]) -> dict[str, Any]:
    """Replace PII column values with ``[REDACTED]`` in a result row dict."""
    return {
        k: "[REDACTED]" if k.lower() in PII_COLUMNS else v
        for k, v in row.items()
    }


def list_tables(conn: Any) -> list[dict[str, Any]]:
    """Return table names visible in the current schema that are in ALLOWED_TABLES.

    When *conn* is ``None`` (e.g. in testing without a DB), returns the static
    whitelist with ``approx_row_count = 0``.
    """
    if conn is None:
        return [
            {"table_name": t, "approx_row_count": 0}
            for t in sorted(ALLOWED_TABLES)
        ]

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT t.table_name
            FROM information_schema.tables t
            WHERE t.table_schema = 'public'
              AND t.table_type = 'BASE TABLE'
              AND t.table_name = ANY(%s)
            ORDER BY t.table_name
            """,
            (list(ALLOWED_TABLES),),
        )
        rows = cur.fetchall()

    return [{"table_name": row[0], "approx_row_count": None} for row in rows]


def describe_table(conn: Any, table_name: str) -> list[dict[str, Any]]:
    """Return column metadata for *table_name*.

    Each returned dict has:
      - ``column_name``: str
      - ``data_type``: postgres data type string
      - ``is_nullable``: bool
      - ``is_pii``: bool — whether this column is subject to redaction

    Raises ``ValueError`` if *table_name* is not in ALLOWED_TABLES.
    When *conn* is ``None``, returns a minimal fallback row.
    """
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"table not in allowed list: {table_name!r}")

    if conn is None:
        return [{"column_name": "n/a", "data_type": "unknown", "is_nullable": True, "is_pii": False}]

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table_name,),
        )
        rows = cur.fetchall()

    return [
        {
            "column_name": row[0],
            "data_type": row[1],
            "is_nullable": row[2] == "YES",
            "is_pii": row[0].lower() in PII_COLUMNS,
        }
        for row in rows
    ]


def query_aggregate(
    conn: Any,
    *,
    table_name: str,
    group_by: list[str],
    tenant_id: int | None = None,
    limit: int = MAX_AGGREGATE_ROWS,
) -> list[dict[str, Any]]:
    """Execute a safe ``COUNT(*) GROUP BY`` query on an allowed table.

    Safety rules enforced:
      - *table_name* must be in ALLOWED_TABLES.
      - Every column in *group_by* must pass ``_safe_ident`` validation.
      - No *group_by* column may be a PII column.
      - *limit* is capped at MAX_AGGREGATE_ROWS.

    Returns an empty list when *conn* is ``None``.
    """
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"table not in allowed list: {table_name!r}")

    validated_cols: list[str] = []
    for col in group_by:
        safe_col = _safe_ident(col)
        if safe_col.lower() in PII_COLUMNS:
            raise ValueError(f"cannot group by PII column: {safe_col!r}")
        validated_cols.append(safe_col)

    limit = min(int(limit), MAX_AGGREGATE_ROWS)

    if conn is None:
        return []

    safe_table = _safe_ident(table_name)
    params: list[Any] = []

    if validated_cols:
        col_list = ", ".join(validated_cols)
        sql = f"SELECT {col_list}, COUNT(*) AS count FROM {safe_table}"  # noqa: S608
    else:
        col_list = ""
        sql = f"SELECT COUNT(*) AS count FROM {safe_table}"  # noqa: S608

    if tenant_id is not None:
        sql += " WHERE tenant_id = %s"
        params.append(int(tenant_id))

    if validated_cols:
        sql += f" GROUP BY {col_list}"

    sql += f" ORDER BY count DESC LIMIT {limit}"

    with conn.cursor() as cur:
        cur.execute(sql, params)
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

    return [dict(zip(cols, row, strict=False)) for row in rows]
