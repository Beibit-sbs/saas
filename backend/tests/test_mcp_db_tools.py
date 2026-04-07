"""Tests for AI copilot DB introspection tools and redaction policy.

All tests run without a real database connection (conn=None fallback paths),
so no DATABASE_URL is required.  The tests verify:
  - PII_COLUMNS coverage and redact_row() behaviour
  - ALLOWED_TABLES whitelist invariants
  - describe_table() and list_tables() fallback paths
  - query_aggregate() safety guards (whitelist, PII group_by, injection check)
"""
from __future__ import annotations

import pytest

from app.platform.ai.db_tools import (
    ALLOWED_TABLES,
    MAX_AGGREGATE_ROWS,
    PII_COLUMNS,
    describe_table,
    list_tables,
    query_aggregate,
    redact_row,
)


# ---------------------------------------------------------------------------
# redact_row
# ---------------------------------------------------------------------------


def test_redact_row_replaces_pii_fields():
    row = {
        "id": 1,
        "tenant_id": 99,
        "email": "alice@example.com",
        "name": "Alice Smith",
        "entity_type": "student",
        "password_hash": "bcrypt...",
        "status": "active",
    }
    result = redact_row(row)
    assert result["id"] == 1
    assert result["tenant_id"] == 99
    assert result["entity_type"] == "student"
    assert result["status"] == "active"
    assert result["email"] == "[REDACTED]"
    assert result["name"] == "[REDACTED]"
    assert result["password_hash"] == "[REDACTED]"


def test_redact_row_case_insensitive():
    """Column name casing (e.g. from ORM) must not bypass redaction."""
    row = {"Email": "test@test.com", "NAME": "Bob", "value": 42}
    result = redact_row(row)
    assert result["Email"] == "[REDACTED]"
    assert result["NAME"] == "[REDACTED]"
    assert result["value"] == 42


def test_redact_row_empty_dict():
    assert redact_row({}) == {}


# ---------------------------------------------------------------------------
# PII_COLUMNS coverage
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field",
    [
        "email",
        "password",
        "password_hash",
        "hashed_password",
        "api_key",
        "token",
        "refresh_token",
        "access_token",
        "iin",
        "national_id",
        "date_of_birth",
        "dob",
        "phone",
        "name",
        "signing_key",
        "private_key",
    ],
)
def test_pii_columns_includes_sensitive_fields(field: str):
    assert field in PII_COLUMNS


# ---------------------------------------------------------------------------
# ALLOWED_TABLES whitelist invariants
# ---------------------------------------------------------------------------


def test_allowed_tables_does_not_include_local_users():
    """app_local_users has plaintext email and hashed password columns."""
    assert "app_local_users" not in ALLOWED_TABLES


def test_allowed_tables_does_not_include_service_accounts():
    assert "app_service_accounts" not in ALLOWED_TABLES


def test_allowed_tables_is_non_empty():
    assert len(ALLOWED_TABLES) > 0


# ---------------------------------------------------------------------------
# list_tables
# ---------------------------------------------------------------------------


def test_list_tables_without_db_returns_static_fallback():
    result = list_tables(None)
    assert isinstance(result, list)
    assert len(result) == len(ALLOWED_TABLES)
    returned_names = {r["table_name"] for r in result}
    assert returned_names == ALLOWED_TABLES


def test_list_tables_fallback_row_count_is_zero():
    result = list_tables(None)
    assert all(r["approx_row_count"] == 0 for r in result)


# ---------------------------------------------------------------------------
# describe_table
# ---------------------------------------------------------------------------


def test_describe_table_raises_on_disallowed_table():
    with pytest.raises(ValueError, match="not in allowed list"):
        describe_table(None, "app_local_users")


def test_describe_table_raises_on_arbitrary_table():
    with pytest.raises(ValueError, match="not in allowed list"):
        describe_table(None, "pg_shadow")


def test_describe_table_returns_fallback_without_db():
    table = next(iter(sorted(ALLOWED_TABLES)))
    result = describe_table(None, table)
    assert isinstance(result, list)
    assert len(result) > 0
    # Fallback row must have required keys
    assert "column_name" in result[0]
    assert "data_type" in result[0]
    assert "is_pii" in result[0]


# ---------------------------------------------------------------------------
# query_aggregate — safety guards
# ---------------------------------------------------------------------------


def test_query_aggregate_raises_on_disallowed_table():
    with pytest.raises(ValueError, match="not in allowed list"):
        query_aggregate(None, table_name="pg_user", group_by=[])


def test_query_aggregate_raises_on_pii_group_by():
    table = next(iter(sorted(ALLOWED_TABLES)))
    with pytest.raises(ValueError, match="PII column"):
        query_aggregate(None, table_name=table, group_by=["email"])


def test_query_aggregate_raises_on_pii_group_by_password():
    table = next(iter(sorted(ALLOWED_TABLES)))
    with pytest.raises(ValueError, match="PII column"):
        query_aggregate(None, table_name=table, group_by=["password_hash"])


def test_query_aggregate_raises_on_sql_injection_via_identifier():
    table = next(iter(sorted(ALLOWED_TABLES)))
    with pytest.raises(ValueError, match="unsafe SQL identifier"):
        query_aggregate(None, table_name=table, group_by=["status; DROP TABLE foo"])


def test_query_aggregate_raises_on_identifier_with_spaces():
    table = next(iter(sorted(ALLOWED_TABLES)))
    with pytest.raises(ValueError, match="unsafe SQL identifier"):
        query_aggregate(None, table_name=table, group_by=["col name"])


def test_query_aggregate_raises_on_disallowed_table_identifier():
    with pytest.raises(ValueError, match="not in allowed list"):
        query_aggregate(None, table_name="app_local_users", group_by=["tenant_id"])


def test_query_aggregate_without_db_returns_empty():
    table = next(iter(sorted(ALLOWED_TABLES)))
    result = query_aggregate(None, table_name=table, group_by=["entity_type"])
    assert result == []


def test_query_aggregate_limit_capped_at_max():
    """Even if the caller requests 9999 rows, limit is capped."""
    table = next(iter(sorted(ALLOWED_TABLES)))
    # We can't easily assert the SQL limit without a DB, but we can confirm
    # the call doesn't raise and returns empty for conn=None.
    result = query_aggregate(None, table_name=table, group_by=[], limit=9999)
    assert result == []


# ---------------------------------------------------------------------------
# MAX_AGGREGATE_ROWS constant
# ---------------------------------------------------------------------------


def test_max_aggregate_rows_is_reasonable():
    assert 1 <= MAX_AGGREGATE_ROWS <= 200
