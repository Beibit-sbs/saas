from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from app.platform.repository.db import db_available, db_url

try:
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None


TABLES = [
    "app_audit_events",
    "app_ai_models",
    "app_ai_usage_logs",
    "app_roles",
    "app_role_permissions",
    "app_user_roles",
    "app_platform_developer_apps",
    "app_platform_feature_flags",
    "university_courses",
    "university_programs",
    "university_faculty",
    "university_academic_records",
]


@dataclass
class Issue:
    table: str
    problem: str
    count: int


def _count(cur, sql: str, params: tuple | None = None) -> int:
    cur.execute(sql, params or ())
    row = cur.fetchone()
    return int(row[0]) if row else 0


def run_audit() -> dict[str, object]:
    if not db_available() or psycopg is None:
        return {
            "status": "db-unavailable",
            "database_url_set": bool(db_url()),
            "issues": [],
        }

    issues: list[Issue] = []
    with psycopg.connect(db_url(), connect_timeout=5) as conn:  # type: ignore[arg-type]
        with conn.cursor() as cur:
            for table in TABLES:
                null_count = _count(cur, f"SELECT COUNT(*) FROM {table} WHERE tenant_id IS NULL")
                if null_count > 0:
                    issues.append(Issue(table=table, problem="tenant_id_is_null", count=null_count))

                orphan_count = _count(
                    cur,
                    (
                        f"SELECT COUNT(*) FROM {table} t "
                        "LEFT JOIN app_tenants ten ON ten.id = t.tenant_id "
                        "WHERE ten.id IS NULL"
                    ),
                )
                if orphan_count > 0:
                    issues.append(Issue(table=table, problem="tenant_id_orphan", count=orphan_count))

            legacy_default_1 = _count(
                cur,
                """
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE column_name = 'tenant_id'
                  AND table_schema = 'public'
                  AND column_default ILIKE '%1%'
                """,
            )
            if legacy_default_1 > 0:
                issues.append(
                    Issue(
                        table="information_schema.columns",
                        problem="tenant_id_default_contains_1",
                        count=legacy_default_1,
                    )
                )

    return {
        "status": "ok" if not issues else "remediation-required",
        "database_url_set": True,
        "issues": [asdict(item) for item in issues],
    }


if __name__ == "__main__":
    print(json.dumps(run_audit(), indent=2, ensure_ascii=False))
