"""HTTP-level tests for internal MCP router (app.platform.router_mcp).

Exercises the three endpoints:
  GET  /api/v1/internal/mcp/schema
  GET  /api/v1/internal/mcp/schema/{table_name}
  POST /api/v1/internal/mcp/schema/{table_name}/query

All tests run without a real DB (conn=None fallback in UnitOfWork), so no
DATABASE_URL is required.  The INTERNAL_API_TOKEN env var is already set to
'internal-token-for-tests-only' by tests/conftest.py.
"""
from __future__ import annotations

import os

from tests.conftest import client

# Use the token that conftest.py / docker-compose injected into the process env.
# Conftest sets a default "internal-token-for-tests-only" when no env var exists,
# but in Docker the real value from .env takes precedence.
INTERNAL_TOKEN = os.environ.get("INTERNAL_API_TOKEN", "internal-token-for-tests-only")
AUTH_HEADER = {"Authorization": f"Bearer {INTERNAL_TOKEN}"}


# ---------------------------------------------------------------------------
# _require_mcp_token — authentication guard
# ---------------------------------------------------------------------------

def test_schema_requires_token() -> None:
    """Missing Authorization header → 401."""
    response = client.get("/api/v1/internal/mcp/schema")
    assert response.status_code == 401


def test_schema_rejects_wrong_token() -> None:
    """Wrong token → 403."""
    response = client.get(
        "/api/v1/internal/mcp/schema",
        headers={"Authorization": "Bearer wrong-token-value"},
    )
    assert response.status_code == 403


def test_schema_rejects_bad_bearer_prefix() -> None:
    """No 'Bearer ' prefix → 401."""
    response = client.get(
        "/api/v1/internal/mcp/schema",
        headers={"Authorization": INTERNAL_TOKEN},  # no 'Bearer ' prefix
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /schema — list all introspectable tables
# ---------------------------------------------------------------------------

def test_schema_list_returns_list_with_valid_token() -> None:
    """Valid token → 200 with a list response."""
    response = client.get("/api/v1/internal/mcp/schema", headers=AUTH_HEADER)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_schema_list_entries_have_table_key() -> None:
    """Each entry should have at minimum a 'table_name' key."""
    response = client.get("/api/v1/internal/mcp/schema", headers=AUTH_HEADER)
    assert response.status_code == 200
    for entry in response.json():
        assert "table_name" in entry


# ---------------------------------------------------------------------------
# GET /schema/{table_name} — describe a table
# ---------------------------------------------------------------------------

def test_describe_table_found() -> None:
    """Describe a known whitelisted table → 200."""
    # First get the list to discover a real table name
    tables_resp = client.get("/api/v1/internal/mcp/schema", headers=AUTH_HEADER)
    assert tables_resp.status_code == 200
    tables = tables_resp.json()
    if not tables:
        return  # nothing to describe → skip
    table_name = tables[0]["table_name"]
    resp = client.get(
        f"/api/v1/internal/mcp/schema/{table_name}",
        headers=AUTH_HEADER,
    )
    assert resp.status_code == 200
    columns = resp.json()
    assert isinstance(columns, list)


def test_describe_table_not_whitelisted() -> None:
    """Non-whitelisted table → 404."""
    resp = client.get(
        "/api/v1/internal/mcp/schema/not_a_real_table_xyz",
        headers=AUTH_HEADER,
    )
    assert resp.status_code == 404


def test_describe_table_requires_token() -> None:
    """No token on describe endpoint → 401."""
    resp = client.get("/api/v1/internal/mcp/schema/app_tenants")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /schema/{table_name}/query — aggregate query
# ---------------------------------------------------------------------------

def test_aggregate_query_not_whitelisted_returns_400() -> None:
    """Non-whitelisted table → 400."""
    resp = client.post(
        "/api/v1/internal/mcp/schema/secret_table/query",
        json={"group_by": [], "limit": 10},
        headers=AUTH_HEADER,
    )
    assert resp.status_code == 400


def test_aggregate_query_whitelisted_table() -> None:
    """Whitelisted table with no group_by → 200 or 400 (if group context fails)."""
    tables_resp = client.get("/api/v1/internal/mcp/schema", headers=AUTH_HEADER)
    assert tables_resp.status_code == 200
    tables = tables_resp.json()
    if not tables:
        return
    table_name = tables[0]["table_name"]
    resp = client.post(
        f"/api/v1/internal/mcp/schema/{table_name}/query",
        json={"group_by": [], "limit": 5},
        headers=AUTH_HEADER,
    )
    # Expects either successful aggregate or a validation error — not a 401/403
    assert resp.status_code in (200, 400)


def test_aggregate_query_requires_token() -> None:
    """No token on query endpoint → 401."""
    resp = client.post(
        "/api/v1/internal/mcp/schema/app_tenants/query",
        json={"group_by": [], "limit": 10},
    )
    assert resp.status_code == 401
