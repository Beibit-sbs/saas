"""Local user store — PostgreSQL-backed when DATABASE_URL is set, in-memory fallback for tests."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from collections.abc import Iterable
from typing import Dict, List

from fastapi import HTTPException

from app.core.db import get_raw_conn

_PBKDF2_ITERATIONS = 200_000
_PLATFORM_SUPERADMIN_ROLE = "superadmin"


def _require_tenant_id(value: int | str | None, *, operation: str) -> int:
    if value is None:
        raise HTTPException(status_code=400, detail=f"tenant_id is required for {operation}")
    try:
        tenant_id = int(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"tenant_id is required for {operation}") from exc
    if tenant_id <= 0:
        raise HTTPException(status_code=400, detail=f"tenant_id is required for {operation}")
    return tenant_id


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("ascii"),
        _PBKDF2_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt}${digest}"


def _verify_password(password: str, encoded: str) -> bool:
    parts = encoded.split("$", 3)
    if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
        return False
    try:
        iterations = int(parts[1])
    except ValueError:
        return False
    salt = parts[2]
    expected = parts[3]
    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("ascii"),
        iterations,
    ).hex()
    return hmac.compare_digest(actual, expected)


_SELECT_COLS = (
    "user_id, tenant_id, login, password_hash, display_name, roles, "
    "default_language, email, account_scope, is_platform_user, "
    "force_password_change, auth_source, status"
)


def _row_to_dict(row) -> dict:
    """Convert a psycopg Row (by index position matching _SELECT_COLS) to a dict."""
    roles_raw = row[5]
    if isinstance(roles_raw, list):
        roles = roles_raw
    elif isinstance(roles_raw, str):
        try:
            roles = json.loads(roles_raw)
        except Exception:
            roles = ["student"]
    else:
        roles = ["student"]
    return {
        "user_id": row[0],
        "tenant_id": row[1],
        "login": row[2],
        "password_hash": row[3] or "",
        "display_name": row[4] or "",
        "roles": roles,
        "default_language": row[6] or "ru",
        "email": row[7],
        "account_scope": row[8],
        "is_platform_user": bool(row[9]),
        "force_password_change": bool(row[10]),
        "auth_source": row[11] or "local",
        "status": row[12] or "active",
    }


class LocalUserStore:
    """Persists local users to PostgreSQL (app_local_users table).

    Falls back to an in-memory dict when DATABASE_URL is absent so that unit
    tests continue to work without a database.  Tests reset the in-memory state
    between runs via conftest._reset_local_user_store().
    """

    def __init__(self) -> None:
        # In-memory fallback state (tests only)
        self._users_by_id: Dict[str, dict] = {}
        self._users_by_login: Dict[str, str] = {}
        self._counter: int = 0
        self._loaded: bool = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _use_db(self) -> bool:
        # Mirror the same guard used by the shared engine initialiser:
        # return True only when DATABASE_URL is present in the current env.
        # This ensures test fixtures that pop DATABASE_URL get the in-memory
        # fallback even if a shared engine was initialised at container startup.
        return bool(os.environ.get("DATABASE_URL", "").strip())

    def _public_user(self, item: dict) -> dict:
        tenant_id = _require_tenant_id(item.get("tenant_id"), operation="local_user_public_projection")
        projection: dict = {
            "user_id": item["user_id"],
            "login": item["login"],
            "display_name": item["display_name"],
            "roles": item["roles"],
            "default_language": item["default_language"],
            "tenant_id": tenant_id,
            "auth_source": item.get("auth_source", "local"),
            "sync_with_ad": False,
        }
        if item.get("account_scope"):
            projection["account_scope"] = item["account_scope"]
        if item.get("is_platform_user"):
            projection["is_platform_user"] = bool(item.get("is_platform_user"))
        email = str(item.get("email") or "").strip().lower()
        if email:
            projection["email"] = email
        if bool(item.get("force_password_change", False)):
            projection["force_password_change"] = True
        return projection

    def _normalize_roles(self, roles: Iterable[str]) -> List[str]:
        normalized = [str(role).strip() for role in roles if str(role).strip()]
        return normalized or ["student"]

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    def _db_list_users(self, search, role, language, tenant_id) -> List[dict]:
        with get_raw_conn() as conn:
            with conn.cursor() as cur:
                params: list = []
                where: list[str] = []
                if tenant_id is not None:
                    where.append("tenant_id = %s")
                    params.append(int(tenant_id))
                if language:
                    where.append("lower(default_language) = %s")
                    params.append(language.strip().lower())
                clause = ("WHERE " + " AND ".join(where)) if where else ""
                cur.execute(
                    f"SELECT {_SELECT_COLS} FROM app_local_users {clause} ORDER BY user_id",
                    params,
                )
                rows = cur.fetchall()
        results = []
        for row in rows:
            item = _row_to_dict(row)
            if search:
                haystack = " ".join([
                    str(item.get("user_id", "")),
                    str(item.get("login", "")),
                    str(item.get("display_name", "")),
                ]).lower()
                if search.strip().lower() not in haystack:
                    continue
            if role:
                item_roles = [str(r).strip().lower() for r in item.get("roles", [])]
                if role.strip().lower() not in item_roles:
                    continue
            results.append(self._public_user(item))
        return results

    def _db_create_user(self, login, password, display_name, roles, default_language, tenant_id, email, extra=None) -> dict:
        normalized_email = str(email or "").strip().lower() or None
        normalized_roles = [r.strip() for r in roles if r.strip()] or ["student"]
        ph = _hash_password(str(password).strip())
        extra = extra or {}
        with get_raw_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM app_local_users WHERE login = %s LIMIT 1", (login,))
                if cur.fetchone():
                    raise HTTPException(status_code=409, detail="login already exists")
                if normalized_email:
                    cur.execute("SELECT 1 FROM app_local_users WHERE email = %s LIMIT 1", (normalized_email,))
                    if cur.fetchone():
                        raise HTTPException(status_code=409, detail="email already exists")
                cur.execute(
                    f"""
                    INSERT INTO app_local_users
                        (tenant_id, login, password_hash, display_name, roles,
                         default_language, email, account_scope, is_platform_user,
                         force_password_change, auth_source, status)
                    VALUES (%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,'active')
                    RETURNING {_SELECT_COLS}
                    """,
                    (
                        tenant_id, login, ph, display_name.strip(),
                        json.dumps(normalized_roles), default_language,
                        normalized_email,
                        extra.get("account_scope"),
                        bool(extra.get("is_platform_user", False)),
                        bool(extra.get("force_password_change", False)),
                        extra.get("auth_source", "local"),
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return _row_to_dict(row)

    def _db_get_by_id(self, user_id: str) -> dict | None:
        with get_raw_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT {_SELECT_COLS} FROM app_local_users WHERE user_id = %s", (user_id,))
                row = cur.fetchone()
        return _row_to_dict(row) if row else None

    def _db_get_by_login(self, login: str) -> dict | None:
        with get_raw_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT {_SELECT_COLS} FROM app_local_users WHERE login = %s", (login,))
                row = cur.fetchone()
        return _row_to_dict(row) if row else None

    def _db_get_by_email(self, email: str) -> dict | None:
        with get_raw_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT {_SELECT_COLS} FROM app_local_users WHERE email = %s", (email,))
                row = cur.fetchone()
        return _row_to_dict(row) if row else None

    def _db_update(self, user_id: str, tenant_id: int, **fields) -> dict:
        if not fields:
            result = self._db_get_by_id(user_id)
            return result or {}
        set_parts: list[str] = []
        params: list = []
        for col, val in fields.items():
            if col == "roles":
                set_parts.append(f"{col} = %s::jsonb")
                params.append(json.dumps(val))
            else:
                set_parts.append(f"{col} = %s")
                params.append(val)
        set_parts.append("updated_at = NOW()")
        params += [user_id, int(tenant_id)]
        with get_raw_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE app_local_users SET {chr(44).join(set_parts)} WHERE user_id = %s AND tenant_id = %s RETURNING {_SELECT_COLS}",
                    params,
                )
                row = cur.fetchone()
            conn.commit()
        if row is None:
            raise HTTPException(status_code=404, detail="local user not found")
        return _row_to_dict(row)

    def _db_delete(self, user_id: str, tenant_id: int) -> bool:
        with get_raw_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM app_local_users WHERE user_id = %s AND tenant_id = %s RETURNING user_id",
                    (user_id, int(tenant_id)),
                )
                deleted = cur.fetchone()
            conn.commit()
        if not deleted:
            raise HTTPException(status_code=404, detail="local user not found")
        return True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_users(self, search=None, role=None, language=None, tenant_id=None) -> List[dict]:
        if self._use_db():
            return self._db_list_users(search, role, language, tenant_id)
        self._loaded = True
        normalized_search = (search or "").strip().lower()
        normalized_role = (role or "").strip().lower()
        normalized_language = (language or "").strip().lower()
        result: List[dict] = []
        for item in self._users_by_id.values():
            item_tenant_id = _require_tenant_id(item.get("tenant_id"), operation="local_user_list")
            if tenant_id is not None and item_tenant_id != int(tenant_id):
                continue
            if normalized_search:
                haystack = " ".join([str(item.get("user_id", "")), str(item.get("login", "")), str(item.get("display_name", ""))]).lower()
                if normalized_search not in haystack:
                    continue
            item_roles = [str(v).strip().lower() for v in item.get("roles", []) if str(v).strip()]
            if normalized_role and normalized_role not in item_roles:
                continue
            item_language = str(item.get("default_language", "")).strip().lower()
            if normalized_language and normalized_language != item_language:
                continue
            result.append(self._public_user(item))
        return result

    def create_user(self, login, password, display_name, roles, default_language, tenant_id, email=None) -> dict:
        normalized_tenant_id = _require_tenant_id(tenant_id, operation="local_user_create")
        normalized_login = login.strip().lower()
        if not normalized_login:
            raise HTTPException(status_code=400, detail="login is required")
        normalized_email = str(email or "").strip().lower()
        if normalized_email and "@" not in normalized_email:
            raise HTTPException(status_code=400, detail="email is invalid")

        from app.modules.billing.service import assert_billing_write_allowed, assert_quota_with_increment
        assert_billing_write_allowed(normalized_tenant_id, action="local_users.create")
        assert_quota_with_increment(normalized_tenant_id, "users", increment=1)

        if self._use_db():
            raw = self._db_create_user(normalized_login, password, display_name, roles, default_language, normalized_tenant_id, normalized_email or None)
            try:
                from app.modules.usage.service import record_usage_event
                record_usage_event(normalized_tenant_id, "users_created", 1)
            except Exception:
                pass
            return self._public_user(raw)

        self._loaded = True
        if normalized_login in self._users_by_login:
            raise HTTPException(status_code=409, detail="login already exists")
        if normalized_email and self.find_user_by_email(normalized_email) is not None:
            raise HTTPException(status_code=409, detail="email already exists")
        self._counter += 1
        user_id = f"local.{self._counter:03d}"
        payload: dict = {
            "user_id": user_id, "login": normalized_login,
            "password_hash": _hash_password(password), "display_name": display_name.strip(),
            "roles": [r.strip() for r in roles if r.strip()] or ["student"],
            "default_language": default_language, "tenant_id": normalized_tenant_id,
            "auth_source": "local", "sync_with_ad": False,
        }
        if normalized_email:
            payload["email"] = normalized_email
        self._users_by_id[user_id] = payload
        self._users_by_login[normalized_login] = user_id
        try:
            from app.modules.usage.service import record_usage_event
            record_usage_event(normalized_tenant_id, "users_created", 1)
        except Exception:
            pass
        return self._public_user(payload)

    def update_user(self, user_id, tenant_id, display_name=None, language=None, roles=None) -> dict:
        from app.modules.billing.service import assert_billing_write_allowed
        normalized_user_id = user_id.strip()
        normalized_tenant_id = int(tenant_id)
        assert_billing_write_allowed(normalized_tenant_id, action="local_users.update")
        if not any([display_name is not None, language is not None, roles is not None]):
            raise HTTPException(status_code=400, detail="no fields to update")
        if self._use_db():
            fields: dict = {}
            if display_name is not None:
                v = display_name.strip()
                if not v:
                    raise HTTPException(status_code=400, detail="display_name is required")
                fields["display_name"] = v
            if language is not None:
                v = language.strip().lower()
                if not v:
                    raise HTTPException(status_code=400, detail="language is required")
                fields["default_language"] = v
            if roles is not None:
                fields["roles"] = self._normalize_roles(roles)
            return self._public_user(self._db_update(normalized_user_id, normalized_tenant_id, **fields))
        self._loaded = True
        user = self._users_by_id.get(normalized_user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="local user not found")
        if _require_tenant_id(user.get("tenant_id"), operation="local_user_update") != normalized_tenant_id:
            raise HTTPException(status_code=404, detail="local user not found")
        if display_name is not None:
            v = display_name.strip()
            if not v:
                raise HTTPException(status_code=400, detail="display_name is required")
            user["display_name"] = v
        if language is not None:
            v = language.strip().lower()
            if not v:
                raise HTTPException(status_code=400, detail="language is required")
            user["default_language"] = v
        if roles is not None:
            user["roles"] = self._normalize_roles(roles)
        return self._public_user(user)

    def delete_user(self, user_id, tenant_id) -> bool:
        from app.modules.billing.service import assert_billing_write_allowed
        normalized_user_id = user_id.strip()
        normalized_tenant_id = int(tenant_id)
        assert_billing_write_allowed(normalized_tenant_id, action="local_users.delete")
        if self._use_db():
            return self._db_delete(normalized_user_id, normalized_tenant_id)
        self._loaded = True
        user = self._users_by_id.get(normalized_user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="local user not found")
        if _require_tenant_id(user.get("tenant_id"), operation="local_user_delete") != normalized_tenant_id:
            raise HTTPException(status_code=404, detail="local user not found")
        self._users_by_id.pop(normalized_user_id, None)
        login = str(user.get("login", "")).strip().lower()
        if login:
            self._users_by_login.pop(login, None)
        return True

    def set_password(self, user_id, password, tenant_id) -> None:
        from app.modules.billing.service import assert_billing_write_allowed
        normalized_user_id = user_id.strip()
        normalized_tenant_id = int(tenant_id)
        assert_billing_write_allowed(normalized_tenant_id, action="local_users.set_password")
        normalized_password = password.strip()
        if len(normalized_password) < 6:
            raise HTTPException(status_code=400, detail="password must be at least 6 characters")
        if self._use_db():
            self._db_update(normalized_user_id, normalized_tenant_id, password_hash=_hash_password(normalized_password))
            return
        self._loaded = True
        user = self._users_by_id.get(normalized_user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="local user not found")
        if _require_tenant_id(user.get("tenant_id"), operation="local_user_password_set") != normalized_tenant_id:
            raise HTTPException(status_code=404, detail="local user not found")
        user["password_hash"] = _hash_password(normalized_password)
        user.pop("password", None)

    def authenticate(self, login, password) -> dict | None:
        normalized_login = login.strip().lower()
        if self._use_db():
            user = self._db_get_by_login(normalized_login)
        else:
            self._loaded = True
            user_id = self._users_by_login.get(normalized_login)
            user = self._users_by_id.get(user_id) if user_id else None
        if user is None:
            return None
        password_hash = str(user.get("password_hash") or "")
        if password_hash:
            return user if _verify_password(password, password_hash) else None
        legacy = str(user.get("password") or "")
        if legacy != password:
            return None
        new_hash = _hash_password(password)
        if self._use_db():
            try:
                self._db_update(str(user["user_id"]), int(user["tenant_id"]), password_hash=new_hash)
            except Exception:
                pass
        else:
            user["password_hash"] = new_hash
            user.pop("password", None)
        return user

    def get_user(self, user_id) -> dict | None:
        if self._use_db():
            try:
                return self._db_get_by_id(user_id)
            except Exception:
                pass  # DB unreachable — fall through to in-memory store
        self._loaded = True
        return self._users_by_id.get(user_id)

    def find_user_by_login(self, login) -> dict | None:
        normalized = str(login).strip().lower()
        if not normalized:
            return None
        if self._use_db():
            try:
                return self._db_get_by_login(normalized)
            except Exception:
                pass  # DB unreachable — fall through to in-memory store
        self._loaded = True
        uid = self._users_by_login.get(normalized)
        return self._users_by_id.get(uid) if uid else None

    def find_user_by_email(self, email) -> dict | None:
        normalized = str(email or "").strip().lower()
        if not normalized:
            return None
        if self._use_db():
            try:
                return self._db_get_by_email(normalized)
            except Exception:
                pass  # DB unreachable — fall through to in-memory store
        self._loaded = True
        for item in self._users_by_id.values():
            if str(item.get("email", "")).strip().lower() == normalized:
                return item
        return None

    def get_public_user(self, user_id) -> dict | None:
        normalized = str(user_id or "").strip()
        if not normalized:
            return None
        raw = self.get_user(normalized)
        return self._public_user(raw) if raw else None

    def upsert_platform_superadmin(
        self,
        *,
        login: str,
        password: str,
        platform_tenant_id: int,
        email: str | None = None,
        update_password: bool = False,
        force_password_change: bool = False,
    ) -> dict:
        normalized_tenant_id = _require_tenant_id(platform_tenant_id, operation="platform_superadmin_upsert")
        normalized_login = str(login).strip().lower()
        if not normalized_login:
            raise HTTPException(status_code=400, detail="login is required")
        normalized_password = str(password).strip()
        if len(normalized_password) < 12:
            raise HTTPException(status_code=400, detail="platform superadmin password must be at least 12 characters")
        normalized_email = str(email or "").strip().lower() or None
        if normalized_email and "@" not in normalized_email:
            raise HTTPException(status_code=400, detail="email is invalid")

        existing = self.find_user_by_login(normalized_login)
        if existing is None:
            extra = {
                "account_scope": "platform",
                "is_platform_user": True,
                "force_password_change": bool(force_password_change),
                "auth_source": "local",
            }
            if self._use_db():
                raw = self._db_create_user(
                    normalized_login, normalized_password, "Platform Superadmin",
                    [_PLATFORM_SUPERADMIN_ROLE], "ru", normalized_tenant_id,
                    normalized_email, extra,
                )
            else:
                self._loaded = True
                self._counter += 1
                user_id = f"local.{self._counter:03d}"
                raw = {
                    "user_id": user_id, "tenant_id": normalized_tenant_id, "login": normalized_login,
                    "password_hash": _hash_password(normalized_password), "display_name": "Platform Superadmin",
                    "roles": [_PLATFORM_SUPERADMIN_ROLE], "default_language": "ru", "auth_source": "local",
                    "account_scope": "platform", "is_platform_user": True,
                    "force_password_change": bool(force_password_change),
                }
                if normalized_email:
                    raw["email"] = normalized_email
                self._users_by_id[user_id] = raw
                self._users_by_login[normalized_login] = user_id
            return {"operation": "created", "user": self._public_user(raw)}

        user_tenant_id = _require_tenant_id(existing.get("tenant_id"), operation="platform_superadmin_existing_user")
        if user_tenant_id != normalized_tenant_id:
            raise HTTPException(status_code=409, detail="login belongs to another tenant; cannot repurpose as platform superadmin")

        changed = False
        updates: dict = {}
        if [str(r).strip() for r in existing.get("roles", []) if str(r).strip()] != [_PLATFORM_SUPERADMIN_ROLE]:
            updates["roles"] = [_PLATFORM_SUPERADMIN_ROLE]
            changed = True
        if existing.get("account_scope") != "platform":
            updates["account_scope"] = "platform"
            changed = True
        if not bool(existing.get("is_platform_user", False)):
            updates["is_platform_user"] = True
            changed = True
        if bool(existing.get("force_password_change", False)) != bool(force_password_change):
            updates["force_password_change"] = bool(force_password_change)
            changed = True
        if normalized_email and str(existing.get("email", "")).strip().lower() != normalized_email:
            updates["email"] = normalized_email
            changed = True
        if update_password:
            updates["password_hash"] = _hash_password(normalized_password)
            changed = True

        if changed:
            if self._use_db():
                raw = self._db_update(str(existing["user_id"]), normalized_tenant_id, **updates)
            else:
                existing.update(updates)
                raw = existing
        else:
            raw = existing
        return {"operation": "updated" if changed else "noop", "user": self._public_user(raw)}

    def reload_from_persistent_state(self) -> None:
        """Re-initialise in-memory fallback. No-op in DB mode."""
        self._users_by_id.clear()
        self._users_by_login.clear()
        self._counter = 0
        self._loaded = False


local_user_store = LocalUserStore()
