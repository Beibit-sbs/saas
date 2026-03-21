from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from threading import Lock

from app.modules.plans.service import get_plan_by_code, get_plan_by_id, list_plans
from app.modules.tenants.service import get_tenant

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


DEFAULT_QUOTAS_BY_PLAN: dict[str, dict[str, int]] = {
    "free": {
        "users": 10,
        "jobs_per_day": 100,
        "backup_storage_mb": 1024,
        "ai_requests_per_day": 200,
        "feature_flags": 20,
        "integrations": 3,
    },
    "pro": {
        "users": 100,
        "jobs_per_day": 1000,
        "backup_storage_mb": 10240,
        "ai_requests_per_day": 5000,
        "feature_flags": 200,
        "integrations": 20,
    },
    "enterprise": {
        "users": 100000,
        "jobs_per_day": 100000,
        "backup_storage_mb": 1048576,
        "ai_requests_per_day": 1000000,
        "feature_flags": 10000,
        "integrations": 1000,
    },
}


@dataclass
class QuotasState:
    rows_by_plan: dict[int, dict[str, int]] = field(default_factory=dict)
    counter: int = 0


_state_lock = Lock()
_state = QuotasState()


def _db_url() -> str | None:
    return os.getenv("DATABASE_URL")


def _use_database() -> bool:
    return bool(_db_url()) and psycopg is not None


def _ensure_db(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_plan_quotas (
                id BIGSERIAL PRIMARY KEY,
                plan_id BIGINT NOT NULL REFERENCES app_plans(id) ON DELETE CASCADE,
                key TEXT NOT NULL,
                limit_value BIGINT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (plan_id, key)
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_app_plan_quotas_plan_id ON app_plan_quotas (plan_id)"
        )
    conn.commit()


def _ensure_seeded() -> None:
    plans = list_plans(include_inactive=True)
    with _state_lock:
        for plan in plans:
            plan_id = int(plan["id"])
            if plan_id in _state.rows_by_plan:
                continue
            code = str(plan["code"])
            defaults = DEFAULT_QUOTAS_BY_PLAN.get(code, DEFAULT_QUOTAS_BY_PLAN["enterprise"])
            _state.rows_by_plan[plan_id] = {k: int(v) for k, v in defaults.items()}
            _state.counter += len(defaults)


def _ensure_seeded_db(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT id, code FROM app_plans")
        plans = cur.fetchall()
        for plan_id, plan_code in plans:
            defaults = DEFAULT_QUOTAS_BY_PLAN.get(str(plan_code), DEFAULT_QUOTAS_BY_PLAN["enterprise"])
            for key, value in defaults.items():
                cur.execute(
                    """
                    INSERT INTO app_plan_quotas (plan_id, key, limit_value)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (plan_id, key) DO NOTHING
                    """,
                    (int(plan_id), str(key), int(value)),
                )
    conn.commit()


def list_quotas(plan_id: int | None = None) -> list[dict[str, object]]:
    if _use_database():
        try:
            assert _db_url() and psycopg is not None
            with psycopg.connect(_db_url(), connect_timeout=5) as conn:
                _ensure_db(conn)
                _ensure_seeded_db(conn)
                with conn.cursor() as cur:
                    if plan_id is None:
                        cur.execute(
                            """
                            SELECT id, plan_id, key, limit_value
                            FROM app_plan_quotas
                            ORDER BY plan_id, key
                            """
                        )
                    else:
                        cur.execute(
                            """
                            SELECT id, plan_id, key, limit_value
                            FROM app_plan_quotas
                            WHERE plan_id = %s
                            ORDER BY key
                            """,
                            (int(plan_id),),
                        )
                    rows = cur.fetchall()
            return [
                {
                    "id": int(row[0]),
                    "plan_id": int(row[1]),
                    "key": str(row[2]),
                    "limit_value": int(row[3]),
                }
                for row in rows
            ]
        except Exception:
            pass

    _ensure_seeded()
    result: list[dict[str, object]] = []
    with _state_lock:
        for current_plan_id, quotas in _state.rows_by_plan.items():
            if plan_id is not None and int(plan_id) != int(current_plan_id):
                continue
            for key in sorted(quotas.keys()):
                result.append(
                    {
                        "id": 0,
                        "plan_id": int(current_plan_id),
                        "key": key,
                        "limit_value": int(quotas[key]),
                    }
                )
    return result


def get_plan_quotas(plan_id: int) -> dict[str, int]:
    rows = list_quotas(plan_id=plan_id)
    if not rows:
        return {}
    return {str(item["key"]): int(item["limit_value"]) for item in rows}


def update_plan_quotas(plan_id: int, quotas: dict[str, int]) -> list[dict[str, object]]:
    normalized_plan_id = int(plan_id)
    if normalized_plan_id <= 0:
        raise ValueError("invalid plan_id")
    if get_plan_by_id(normalized_plan_id) is None:
        raise ValueError("plan not found")

    normalized_quotas: dict[str, int] = {}
    for key, value in quotas.items():
        normalized_key = str(key or "").strip().lower()
        if not normalized_key:
            continue
        normalized_quotas[normalized_key] = max(0, int(value))

    if _use_database():
        try:
            assert _db_url() and psycopg is not None
            with psycopg.connect(_db_url(), connect_timeout=5) as conn:
                _ensure_db(conn)
                _ensure_seeded_db(conn)
                with conn.cursor() as cur:
                    for key, limit_value in normalized_quotas.items():
                        cur.execute(
                            """
                            INSERT INTO app_plan_quotas (plan_id, key, limit_value)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (plan_id, key)
                            DO UPDATE SET limit_value = EXCLUDED.limit_value, updated_at = NOW()
                            """,
                            (normalized_plan_id, key, limit_value),
                        )
                conn.commit()
            return list_quotas(plan_id=normalized_plan_id)
        except Exception:
            pass

    _ensure_seeded()
    with _state_lock:
        row = _state.rows_by_plan.setdefault(normalized_plan_id, {})
        row.update(normalized_quotas)
    return list_quotas(plan_id=normalized_plan_id)


def _day_start_iso() -> str:
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.isoformat()


def _current_value(tenant_id: int, quota_key: str) -> int:
    key = str(quota_key)

    if key == "users":
        from app.modules.auth.local_users_service import local_user_store

        return len(local_user_store.list_users(tenant_id=tenant_id))

    if key == "jobs_per_day":
        from app.modules.jobs.service import list_jobs_for_tenant

        rows = list_jobs_for_tenant(tenant_id=tenant_id, limit=5000)
        day_start = _day_start_iso()
        return sum(1 for item in rows if str(item.get("created_at", "")) >= day_start)

    if key == "backup_storage_mb":
        from app.modules.backup.service import list_backup_history

        rows = list_backup_history(tenant_id=tenant_id)
        total_bytes = sum(max(0, int(item.get("size_bytes") or 0)) for item in rows)
        return int(total_bytes / (1024 * 1024))

    if key == "ai_requests_per_day":
        from app.modules.usage.service import get_usage_sum

        return get_usage_sum(tenant_id=tenant_id, metric="ai_requests", since_iso=_day_start_iso())

    if key == "feature_flags":
        from app.modules.feature_flags.service import list_flags

        return len(list_flags(tenant_id=tenant_id))

    if key == "integrations":
        from app.modules.integrations.service import get_ldap_config_for_admin, list_ai_provider_config_for_admin

        ldap = get_ldap_config_for_admin(tenant_id=tenant_id)
        ai = list_ai_provider_config_for_admin(tenant_id=tenant_id)
        ldap_count = 1 if bool(ldap.get("enabled")) else 0
        ai_count = sum(1 for item in ai if item.get("configured"))
        return ldap_count + ai_count

    return 0


def resolve_tenant_quotas(tenant_id: int) -> dict[str, int]:
    tenant = get_tenant(int(tenant_id))
    if tenant is None:
        raise ValueError("tenant not found")

    plan_id = int(tenant.get("plan_id") or 0)
    if plan_id <= 0:
        enterprise = get_plan_by_code("enterprise")
        if enterprise is None:
            raise ValueError("enterprise plan is not configured")
        plan_id = int(enterprise["id"])

    quotas = get_plan_quotas(plan_id)
    if quotas:
        return quotas

    plan = get_plan_by_id(plan_id)
    code = str(plan.get("code") if plan else "enterprise")
    return dict(DEFAULT_QUOTAS_BY_PLAN.get(code, DEFAULT_QUOTAS_BY_PLAN["enterprise"]))


def check_quota(tenant_id: int, quota_key: str) -> dict[str, object]:
    normalized_tenant_id = int(tenant_id)
    if normalized_tenant_id <= 0:
        raise ValueError("tenant_id must be positive")

    normalized_key = str(quota_key or "").strip().lower()
    if not normalized_key:
        raise ValueError("quota_key is required")

    quotas = resolve_tenant_quotas(normalized_tenant_id)
    limit_value = int(quotas.get(normalized_key, 0))
    current_value = _current_value(normalized_tenant_id, normalized_key)
    within_limit = current_value <= limit_value if limit_value > 0 else True

    if within_limit:
        message = "within quota"
    else:
        message = "quota exceeded (soft enforcement)"

    return {
        "tenant_id": normalized_tenant_id,
        "quota_key": normalized_key,
        "limit_value": limit_value,
        "current_value": current_value,
        "within_limit": within_limit,
        "soft_warning": not within_limit,
        "message": message,
    }


def clear_quotas_state() -> None:
    with _state_lock:
        _state.rows_by_plan.clear()
        _state.counter = 0
