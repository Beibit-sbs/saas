import os
from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, List, Set

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


BASELINE_ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "superadmin": {
        "admin.dashboard.read",
        "admin.roles.manage",
        "admin.audit.read",
        "admin.integrations.manage",
        "admin.ai.providers.manage",
        "admin.ai.models.manage",
        "ai.chat.execute",
        "admin.i18n.manage",
        "admin.users.manage",
        "admin.backup.manage",
        "example.notes.read",
        "example.notes.manage",
    },
    "admin": {
        "admin.dashboard.read",
        "admin.roles.manage",
        "admin.audit.read",
        "admin.integrations.manage",
        "admin.ai.providers.manage",
        "admin.ai.models.manage",
        "ai.chat.execute",
        "admin.i18n.manage",
        "admin.users.manage",
        "admin.backup.manage",
        "example.notes.read",
        "example.notes.manage",
    },
    "auditor": {
        "admin.audit.read",
        "admin.dashboard.read",
        "example.notes.read",
    },
}

TRUSTED_DEMO_ROLE_MAP: Dict[str, List[str]] = {
    "admin.001": ["admin"],
    "teacher.001": ["auditor"],
    "student.001": [],
}


@dataclass
class RbacState:
    roles: Dict[str, Set[str]] = field(default_factory=dict)
    user_roles: Dict[str, Set[str]] = field(default_factory=dict)


state = RbacState(
    roles={role: set(perms) for role, perms in BASELINE_ROLE_PERMISSIONS.items()},
    user_roles={},
)

_permission_cache: dict[tuple[str, ...], Set[str]] = {}
_cache_lock = Lock()


def _db_url() -> str | None:
    return os.getenv("DATABASE_URL")


def _use_database() -> bool:
    return bool(_db_url()) and psycopg is not None


def _should_fallback_to_memory(exc: Exception) -> bool:
    if isinstance(exc, RuntimeError) and str(exc) == "database unavailable":
        return True
    if isinstance(exc, (ConnectionError, TimeoutError, OSError)):
        return True
    if psycopg is not None and isinstance(exc, (psycopg.OperationalError, psycopg.InterfaceError)):
        return True
    return False


def _clear_permission_cache() -> None:
    with _cache_lock:
        _permission_cache.clear()


def _seed_baseline_data(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO app_roles (name, description)
            VALUES
                ('superadmin', 'Full platform access'),
                ('admin', 'Platform administration access'),
                ('auditor', 'Read-only audit and dashboard access')
            ON CONFLICT (name) DO NOTHING
            """
        )

        permission_values = sorted({perm for perms in BASELINE_ROLE_PERMISSIONS.values() for perm in perms})
        cur.executemany(
            """
            INSERT INTO app_permissions (code, description)
            VALUES (%s, %s)
            ON CONFLICT (code) DO NOTHING
            """,
            [(perm, "") for perm in permission_values],
        )

        for role_name, permission_codes in BASELINE_ROLE_PERMISSIONS.items():
            cur.executemany(
                """
                INSERT INTO app_role_permissions (role_id, permission_id)
                SELECT r.id, p.id
                FROM app_roles r
                JOIN app_permissions p ON p.code = %s
                WHERE r.name = %s
                ON CONFLICT (role_id, permission_id) DO NOTHING
                """,
                [(code, role_name) for code in permission_codes],
            )


def _ensure_schema_and_seed(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_roles (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_permissions (
                id BIGSERIAL PRIMARY KEY,
                code TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_role_permissions (
                role_id BIGINT NOT NULL REFERENCES app_roles(id) ON DELETE CASCADE,
                permission_id BIGINT NOT NULL REFERENCES app_permissions(id) ON DELETE CASCADE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (role_id, permission_id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_user_roles (
                user_id TEXT NOT NULL,
                role_id BIGINT NOT NULL REFERENCES app_roles(id) ON DELETE CASCADE,
                assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (user_id, role_id)
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_app_role_permissions_role_id ON app_role_permissions (role_id)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_app_role_permissions_permission_id ON app_role_permissions (permission_id)"
        )
        cur.execute("CREATE INDEX IF NOT EXISTS ix_app_user_roles_user_id ON app_user_roles (user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_app_user_roles_role_id ON app_user_roles (role_id)")

    _seed_baseline_data(conn)
    conn.commit()


def _list_roles_db() -> Dict[str, List[str]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_schema_and_seed(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.name, p.code
                FROM app_roles r
                LEFT JOIN app_role_permissions rp ON rp.role_id = r.id
                LEFT JOIN app_permissions p ON p.id = rp.permission_id
                ORDER BY r.name, p.code
                """
            )
            rows = cur.fetchall()

    roles: Dict[str, Set[str]] = {}
    for role_name, permission_code in rows:
        roles.setdefault(role_name, set())
        if permission_code:
            roles[role_name].add(permission_code)
    return {name: sorted(perms) for name, perms in roles.items()}


def _add_or_update_role_db(name: str, permissions: Set[str]) -> Dict[str, List[str]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_schema_and_seed(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_roles (name, description)
                VALUES (%s, '')
                ON CONFLICT (name) DO NOTHING
                """,
                (name,),
            )

            if permissions:
                cur.executemany(
                    """
                    INSERT INTO app_permissions (code, description)
                    VALUES (%s, '')
                    ON CONFLICT (code) DO NOTHING
                    """,
                    [(perm,) for perm in sorted(permissions)],
                )

            cur.execute(
                """
                DELETE FROM app_role_permissions
                WHERE role_id = (SELECT id FROM app_roles WHERE name = %s)
                """,
                (name,),
            )

            if permissions:
                cur.executemany(
                    """
                    INSERT INTO app_role_permissions (role_id, permission_id)
                    SELECT r.id, p.id
                    FROM app_roles r
                    JOIN app_permissions p ON p.code = %s
                    WHERE r.name = %s
                    ON CONFLICT (role_id, permission_id) DO NOTHING
                    """,
                    [(perm, name) for perm in sorted(permissions)],
                )

        conn.commit()

    return {name: sorted(permissions)}


def _assign_role_db(user_id: str, role: str) -> Dict[str, List[str]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_schema_and_seed(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM app_roles WHERE name = %s", (role,))
            role_row = cur.fetchone()
            if role_row is None:
                raise ValueError(f"unknown role: {role}")

            cur.execute(
                """
                INSERT INTO app_user_roles (user_id, role_id)
                VALUES (%s, %s)
                ON CONFLICT (user_id, role_id) DO NOTHING
                """,
                (user_id, role_row[0]),
            )

            cur.execute(
                """
                SELECT r.name
                FROM app_user_roles ur
                JOIN app_roles r ON r.id = ur.role_id
                WHERE ur.user_id = %s
                ORDER BY r.name
                """,
                (user_id,),
            )
            roles = [row[0] for row in cur.fetchall()]

        conn.commit()

    return {"user_id": user_id, "roles": roles}


def _sync_user_roles_db(user_id: str, roles: List[str]) -> Dict[str, List[str]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    normalized_roles = sorted({role.strip() for role in roles if role.strip()})

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_schema_and_seed(conn)
        with conn.cursor() as cur:
            cur.execute("DELETE FROM app_user_roles WHERE user_id = %s", (user_id,))

            if normalized_roles:
                cur.executemany(
                    """
                    INSERT INTO app_user_roles (user_id, role_id)
                    SELECT %s, r.id
                    FROM app_roles r
                    WHERE r.name = %s
                    ON CONFLICT (user_id, role_id) DO NOTHING
                    """,
                    [(user_id, role_name) for role_name in normalized_roles],
                )

            cur.execute(
                """
                SELECT r.name
                FROM app_user_roles ur
                JOIN app_roles r ON r.id = ur.role_id
                WHERE ur.user_id = %s
                ORDER BY r.name
                """,
                (user_id,),
            )
            resolved_roles = [row[0] for row in cur.fetchall()]

        conn.commit()

    return {"user_id": user_id, "roles": resolved_roles}


def _get_user_roles_db(user_id: str) -> List[str]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_schema_and_seed(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.name
                FROM app_user_roles ur
                JOIN app_roles r ON r.id = ur.role_id
                WHERE ur.user_id = %s
                ORDER BY r.name
                """,
                (user_id,),
            )
            return [row[0] for row in cur.fetchall()]


def _list_user_role_assignments_db(user_id: str | None = None, role: str | None = None) -> List[Dict[str, object]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    clauses: list[str] = []
    params: list[str] = []
    if user_id:
        clauses.append("ur.user_id = %s")
        params.append(user_id)
    if role:
        clauses.append("r.name = %s")
        params.append(role)

    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_schema_and_seed(conn)
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT ur.user_id, r.name
                FROM app_user_roles ur
                JOIN app_roles r ON r.id = ur.role_id
                {where_clause}
                ORDER BY ur.user_id, r.name
                """,
                params,
            )
            rows = cur.fetchall()

    assignments: Dict[str, List[str]] = {}
    for current_user_id, current_role in rows:
        assignments.setdefault(current_user_id, []).append(current_role)

    return [
        {"user_id": current_user_id, "roles": roles}
        for current_user_id, roles in assignments.items()
    ]


def _revoke_role_db(user_id: str, role: str) -> Dict[str, object]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    removed = False
    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_schema_and_seed(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM app_roles WHERE name = %s",
                (role,),
            )
            role_row = cur.fetchone()
            if role_row is not None:
                cur.execute(
                    "DELETE FROM app_user_roles WHERE user_id = %s AND role_id = %s",
                    (user_id, role_row[0]),
                )
                removed = cur.rowcount > 0

            cur.execute(
                """
                SELECT r.name
                FROM app_user_roles ur
                JOIN app_roles r ON r.id = ur.role_id
                WHERE ur.user_id = %s
                ORDER BY r.name
                """,
                (user_id,),
            )
            roles = [row[0] for row in cur.fetchall()]

        conn.commit()

    return {"user_id": user_id, "role": role, "removed": removed, "roles": roles}


def _resolve_permissions_db(roles: List[str]) -> Set[str]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")
    if not roles:
        return set()

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_schema_and_seed(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT p.code
                FROM app_roles r
                JOIN app_role_permissions rp ON rp.role_id = r.id
                JOIN app_permissions p ON p.id = rp.permission_id
                WHERE r.name = ANY(%s)
                """,
                (roles,),
            )
            return {row[0] for row in cur.fetchall()}


def list_roles() -> Dict[str, List[str]]:
    if _use_database():
        try:
            return _list_roles_db()
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise
    return {name: sorted(perms) for name, perms in state.roles.items()}


def add_or_update_role(name: str, permissions: List[str]) -> Dict[str, List[str]]:
    normalized_name = name.strip()
    if not normalized_name:
        raise ValueError("role name is required")

    normalized = {perm.strip() for perm in permissions if perm.strip()}
    if _use_database():
        try:
            result = _add_or_update_role_db(normalized_name, normalized)
            _clear_permission_cache()
            return result
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    state.roles[normalized_name] = normalized
    _clear_permission_cache()
    return {normalized_name: sorted(normalized)}


def assign_role(user_id: str, role: str) -> Dict[str, List[str]]:
    normalized_user_id = user_id.strip()
    normalized_role = role.strip()
    if not normalized_user_id:
        raise ValueError("user_id is required")

    if _use_database():
        try:
            assigned = _assign_role_db(normalized_user_id, normalized_role)
            _clear_permission_cache()
            return assigned
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    if normalized_role not in state.roles:
        raise ValueError(f"unknown role: {normalized_role}")

    if normalized_user_id not in state.user_roles:
        state.user_roles[normalized_user_id] = set()

    state.user_roles[normalized_user_id].add(normalized_role)
    _clear_permission_cache()
    return {"user_id": normalized_user_id, "roles": sorted(state.user_roles[normalized_user_id])}


def sync_user_roles_from_trusted_source(user_id: str, roles: List[str]) -> Dict[str, List[str]]:
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        raise ValueError("user_id is required")

    normalized_roles = sorted({role.strip() for role in roles if role.strip()})

    if _use_database():
        try:
            synced = _sync_user_roles_db(normalized_user_id, normalized_roles)
            _clear_permission_cache()
            return synced
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    state.user_roles[normalized_user_id] = set(normalized_roles)
    if not normalized_roles:
        state.user_roles.pop(normalized_user_id, None)
    _clear_permission_cache()
    return {"user_id": normalized_user_id, "roles": normalized_roles}


def clear_user_roles_for_user(user_id: str) -> Dict[str, object]:
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        raise ValueError("user_id is required")

    previous_roles = get_user_roles(normalized_user_id)
    sync_user_roles_from_trusted_source(normalized_user_id, [])
    return {
        "user_id": normalized_user_id,
        "removed": bool(previous_roles),
        "roles": [],
    }


def get_trusted_demo_roles(user_id: str) -> List[str]:
    return list(TRUSTED_DEMO_ROLE_MAP.get(user_id, []))


def get_user_roles(user_id: str) -> List[str]:
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        return []

    if _use_database():
        try:
            return _get_user_roles_db(normalized_user_id)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise
    return sorted(state.user_roles.get(normalized_user_id, set()))


def get_user_roles_db_source(user_id: str) -> List[str]:
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        return []
    return _get_user_roles_db(normalized_user_id)


def resolve_permissions(roles: List[str]) -> Set[str]:
    normalized_roles = sorted({role.strip() for role in roles if role.strip()})
    cache_key = tuple(normalized_roles)
    with _cache_lock:
        cached = _permission_cache.get(cache_key)
        if cached is not None:
            return set(cached)

    if _use_database():
        try:
            permissions = _resolve_permissions_db(normalized_roles)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise
            permissions = set()
            for role in normalized_roles:
                permissions.update(state.roles.get(role, set()))
    else:
        permissions: Set[str] = set()
        for role in normalized_roles:
            permissions.update(state.roles.get(role, set()))

    with _cache_lock:
        _permission_cache[cache_key] = set(permissions)
    return permissions


def resolve_permissions_db_source(roles: List[str]) -> Set[str]:
    normalized_roles = sorted({role.strip() for role in roles if role.strip()})
    if not normalized_roles:
        return set()
    return _resolve_permissions_db(normalized_roles)


def list_user_role_assignments(user_id: str | None = None, role: str | None = None) -> List[Dict[str, object]]:
    normalized_user_id = user_id.strip() if user_id else None
    normalized_role = role.strip() if role else None

    if _use_database():
        try:
            return _list_user_role_assignments_db(normalized_user_id, normalized_role)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    assignments: List[Dict[str, object]] = []
    for current_user_id in sorted(state.user_roles):
        if normalized_user_id and current_user_id != normalized_user_id:
            continue
        roles = sorted(state.user_roles.get(current_user_id, set()))
        if normalized_role and normalized_role not in roles:
            continue
        assignments.append({"user_id": current_user_id, "roles": roles})
    return assignments


def revoke_role(user_id: str, role: str) -> Dict[str, object]:
    normalized_user_id = user_id.strip()
    normalized_role = role.strip()
    if not normalized_user_id:
        raise ValueError("user_id is required")
    if not normalized_role:
        raise ValueError("role is required")

    if _use_database():
        try:
            result = _revoke_role_db(normalized_user_id, normalized_role)
            _clear_permission_cache()
            return result
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    assigned_roles = state.user_roles.setdefault(normalized_user_id, set())
    removed = normalized_role in assigned_roles
    assigned_roles.discard(normalized_role)
    if not assigned_roles:
        state.user_roles.pop(normalized_user_id, None)
        remaining_roles: list[str] = []
    else:
        remaining_roles = sorted(assigned_roles)
    _clear_permission_cache()
    return {
        "user_id": normalized_user_id,
        "role": normalized_role,
        "removed": removed,
        "roles": remaining_roles,
    }
