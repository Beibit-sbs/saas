from __future__ import annotations


def _normalize_tenant_id(tenant_id: int | None) -> int:
    if tenant_id is None:
        raise ValueError("tenant_id is required for db tenant context")
    normalized = int(tenant_id)
    if normalized <= 0:
        raise ValueError("tenant_id must be positive for db tenant context")
    return normalized


def set_db_tenant_context(conn, *, tenant_id: int) -> None:
    """Set PostgreSQL transaction-local tenant context for RLS policies.

    Uses set_config(..., is_local=true) so the scope is the current transaction.
    """
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT set_config('app.tenant_id', %s, true)",
            (str(normalized_tenant_id),),
        )
