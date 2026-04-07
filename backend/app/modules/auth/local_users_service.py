import hashlib
import hmac
import json
import secrets
from collections.abc import Iterable
from typing import Dict, List

from fastapi import HTTPException

from app.modules.integrations.service import get_global_setting, save_global_setting


_LOCAL_USERS_SETTINGS_KEY = "auth.local_users_json"
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


class LocalUserStore:
    def __init__(self) -> None:
        self._users_by_id: Dict[str, dict[str, object]] = {}
        self._users_by_login: Dict[str, str] = {}
        self._counter = 0
        self._loaded = False

    def _persist(self) -> None:
        payload = {
            "counter": self._counter,
            "users": list(self._users_by_id.values()),
        }
        save_global_setting(_LOCAL_USERS_SETTINGS_KEY, json.dumps(payload), is_secret=True)

    def _load_once(self) -> None:
        if self._loaded:
            return
        self._loaded = True

        raw = get_global_setting(_LOCAL_USERS_SETTINGS_KEY)
        if raw is None or not raw.value:
            return

        try:
            payload = json.loads(raw.value)
        except json.JSONDecodeError:
            return

        users = payload.get("users") if isinstance(payload, dict) else None
        if not isinstance(users, list):
            return

        max_id = 0
        for item in users:
            if not isinstance(item, dict):
                continue
            user_id = str(item.get("user_id", "")).strip()
            login = str(item.get("login", "")).strip().lower()
            if not user_id or not login:
                continue

            if "tenant_id" not in item:
                # Fail-closed: legacy rows without tenant must be remediated explicitly.
                raise HTTPException(status_code=500, detail="local user tenant remediation required")

            self._users_by_id[user_id] = item
            self._users_by_login[login] = user_id

            if user_id.startswith("local."):
                suffix = user_id.split(".", 1)[1]
                if suffix.isdigit():
                    max_id = max(max_id, int(suffix))

        stored_counter = payload.get("counter") if isinstance(payload, dict) else None
        self._counter = max(max_id, int(stored_counter) if isinstance(stored_counter, int) else 0)

    def reload_from_persistent_state(self) -> None:
        self._users_by_id.clear()
        self._users_by_login.clear()
        self._counter = 0
        self._loaded = False
        self._load_once()

    def _public_user(self, item: dict[str, object]) -> dict[str, object]:
        tenant_id = _require_tenant_id(item.get("tenant_id"), operation="local_user_public_projection")
        projection: dict[str, object] = {
            "user_id": item["user_id"],
            "login": item["login"],
            "display_name": item["display_name"],
            "roles": item["roles"],
            "default_language": item["default_language"],
            "tenant_id": tenant_id,
            "auth_source": "local",
            "sync_with_ad": False,
        }
        if "account_scope" in item:
            projection["account_scope"] = item["account_scope"]
        if "is_platform_user" in item:
            projection["is_platform_user"] = bool(item.get("is_platform_user"))
        if "email" in item and str(item.get("email", "")).strip():
            projection["email"] = str(item.get("email", "")).strip().lower()
        if bool(item.get("force_password_change", False)):
            projection["force_password_change"] = True
        return projection

    def list_users(
        self,
        search: str | None = None,
        role: str | None = None,
        language: str | None = None,
        tenant_id: int | None = None,
    ) -> List[dict[str, object]]:
        self._load_once()
        normalized_search = (search or "").strip().lower()
        normalized_role = (role or "").strip().lower()
        normalized_language = (language or "").strip().lower()

        result: List[dict[str, object]] = []
        for item in self._users_by_id.values():
            item_tenant_id = _require_tenant_id(item.get("tenant_id"), operation="local_user_list")
            if tenant_id is not None and item_tenant_id != int(tenant_id):
                continue

            if normalized_search:
                haystack = " ".join(
                    [
                        str(item.get("user_id", "")),
                        str(item.get("login", "")),
                        str(item.get("display_name", "")),
                    ]
                ).lower()
                if normalized_search not in haystack:
                    continue

            item_roles = [str(value).strip().lower() for value in item.get("roles", []) if str(value).strip()]
            if normalized_role and normalized_role not in item_roles:
                continue

            item_language = str(item.get("default_language", "")).strip().lower()
            if normalized_language and normalized_language != item_language:
                continue

            result.append(self._public_user(item))

        return result

    def _normalize_roles(self, roles: Iterable[str]) -> List[str]:
        normalized = [str(role).strip() for role in roles if str(role).strip()]
        return normalized or ["student"]

    def create_user(
        self,
        login: str,
        password: str,
        display_name: str,
        roles: List[str],
        default_language: str,
        tenant_id: int,
        email: str | None = None,
    ) -> dict[str, object]:
        self._load_once()
        normalized_tenant_id = _require_tenant_id(tenant_id, operation="local_user_create")
        normalized_login = login.strip().lower()
        if not normalized_login:
            raise HTTPException(status_code=400, detail="login is required")

        normalized_email = str(email or "").strip().lower()
        if normalized_email and "@" not in normalized_email:
            raise HTTPException(status_code=400, detail="email is invalid")

        if normalized_login in self._users_by_login:
            raise HTTPException(status_code=409, detail="login already exists")

        if normalized_email:
            existing_by_email = self.find_user_by_email(normalized_email)
            if existing_by_email is not None:
                raise HTTPException(status_code=409, detail="email already exists")

        from app.modules.billing.service import assert_billing_write_allowed, assert_quota_with_increment

        assert_billing_write_allowed(normalized_tenant_id, action="local_users.create")
        assert_quota_with_increment(normalized_tenant_id, "users", increment=1)

        self._counter += 1
        user_id = f"local.{self._counter:03d}"
        payload: dict[str, object] = {
            "user_id": user_id,
            "login": normalized_login,
            "password_hash": _hash_password(password),
            "display_name": display_name.strip(),
            "roles": [r.strip() for r in roles if r.strip()] or ["student"],
            "default_language": default_language,
            "tenant_id": normalized_tenant_id,
            "auth_source": "local",
            "sync_with_ad": False,
        }
        if normalized_email:
            payload["email"] = normalized_email

        self._users_by_id[user_id] = payload
        self._users_by_login[normalized_login] = user_id
        self._persist()

        try:
            from app.modules.usage.service import record_usage_event

            record_usage_event(normalized_tenant_id, "users_created", 1)
        except Exception:
            pass

        return self._public_user(payload)

    def update_user(
        self,
        user_id: str,
        tenant_id: int,
        display_name: str | None = None,
        language: str | None = None,
        roles: List[str] | None = None,
    ) -> dict[str, object]:
        self._load_once()
        from app.modules.billing.service import assert_billing_write_allowed

        normalized_user_id = user_id.strip()
        user = self._users_by_id.get(normalized_user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="local user not found")
        user_tenant_id = _require_tenant_id(user.get("tenant_id"), operation="local_user_update")
        if user_tenant_id != int(tenant_id):
            raise HTTPException(status_code=404, detail="local user not found")

        assert_billing_write_allowed(int(tenant_id), action="local_users.update")

        changed = False
        if display_name is not None:
            normalized_display_name = display_name.strip()
            if not normalized_display_name:
                raise HTTPException(status_code=400, detail="display_name is required")
            user["display_name"] = normalized_display_name
            changed = True

        if language is not None:
            normalized_language = language.strip().lower()
            if not normalized_language:
                raise HTTPException(status_code=400, detail="language is required")
            user["default_language"] = normalized_language
            changed = True

        if roles is not None:
            user["roles"] = self._normalize_roles(roles)
            changed = True

        if not changed:
            raise HTTPException(status_code=400, detail="no fields to update")

        self._persist()
        return self._public_user(user)

    def delete_user(self, user_id: str, tenant_id: int) -> bool:
        self._load_once()
        from app.modules.billing.service import assert_billing_write_allowed

        normalized_user_id = user_id.strip()
        user = self._users_by_id.get(normalized_user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="local user not found")
        user_tenant_id = _require_tenant_id(user.get("tenant_id"), operation="local_user_delete")
        if user_tenant_id != int(tenant_id):
            raise HTTPException(status_code=404, detail="local user not found")

        assert_billing_write_allowed(int(tenant_id), action="local_users.delete")

        user = self._users_by_id.pop(normalized_user_id, None)
        if user is None:
            raise HTTPException(status_code=404, detail="local user not found")

        normalized_login = str(user.get("login", "")).strip().lower()
        if normalized_login:
            self._users_by_login.pop(normalized_login, None)
        self._persist()
        return True

    def set_password(self, user_id: str, password: str, tenant_id: int) -> None:
        self._load_once()
        from app.modules.billing.service import assert_billing_write_allowed

        normalized_user_id = user_id.strip()
        user = self._users_by_id.get(normalized_user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="local user not found")
        user_tenant_id = _require_tenant_id(user.get("tenant_id"), operation="local_user_password_set")
        if user_tenant_id != int(tenant_id):
            raise HTTPException(status_code=404, detail="local user not found")

        assert_billing_write_allowed(int(tenant_id), action="local_users.set_password")

        normalized_password = password.strip()
        if len(normalized_password) < 6:
            raise HTTPException(status_code=400, detail="password must be at least 6 characters")

        user["password_hash"] = _hash_password(normalized_password)
        user.pop("password", None)
        self._persist()

    def authenticate(self, login: str, password: str) -> dict[str, object] | None:
        self._load_once()
        normalized_login = login.strip().lower()
        user_id = self._users_by_login.get(normalized_login)
        if not user_id:
            return None

        user = self._users_by_id.get(user_id)
        if not user:
            return None

        password_hash = str(user.get("password_hash") or "")
        if password_hash:
            if not _verify_password(password, password_hash):
                return None
            return user

        # Backward compatibility: migrate old plaintext value on successful login.
        legacy_password = str(user.get("password") or "")
        if legacy_password != password:
            return None

        user["password_hash"] = _hash_password(password)
        user.pop("password", None)
        self._persist()

        return user

    def get_user(self, user_id: str) -> dict[str, object] | None:
        self._load_once()
        return self._users_by_id.get(user_id)

    def find_user_by_login(self, login: str) -> dict[str, object] | None:
        self._load_once()
        normalized_login = str(login).strip().lower()
        if not normalized_login:
            return None
        user_id = self._users_by_login.get(normalized_login)
        if not user_id:
            return None
        return self._users_by_id.get(user_id)

    def find_user_by_email(self, email: str) -> dict[str, object] | None:
        self._load_once()
        normalized_email = str(email or "").strip().lower()
        if not normalized_email:
            return None
        for item in self._users_by_id.values():
            if str(item.get("email", "")).strip().lower() == normalized_email:
                return item
        return None

    def get_public_user(self, user_id: str) -> dict[str, object] | None:
        self._load_once()
        normalized_user_id = str(user_id or "").strip()
        if not normalized_user_id:
            return None
        row = self._users_by_id.get(normalized_user_id)
        if row is None:
            return None
        return self._public_user(row)

    def upsert_platform_superadmin(
        self,
        *,
        login: str,
        password: str,
        platform_tenant_id: int,
        email: str | None = None,
        update_password: bool = False,
        force_password_change: bool = False,
    ) -> dict[str, object]:
        self._load_once()
        tenant_id = _require_tenant_id(platform_tenant_id, operation="platform_superadmin_upsert")
        normalized_login = str(login).strip().lower()
        if not normalized_login:
            raise HTTPException(status_code=400, detail="login is required")

        normalized_password = str(password).strip()
        if len(normalized_password) < 12:
            raise HTTPException(status_code=400, detail="platform superadmin password must be at least 12 characters")

        normalized_email = str(email or "").strip().lower()
        if normalized_email and "@" not in normalized_email:
            raise HTTPException(status_code=400, detail="email is invalid")

        existing = self.find_user_by_login(normalized_login)
        if existing is None:
            created = self.create_user(
                login=normalized_login,
                password=normalized_password,
                display_name="Platform Superadmin",
                roles=[_PLATFORM_SUPERADMIN_ROLE],
                default_language="ru",
                tenant_id=tenant_id,
            )
            raw = self._users_by_id[str(created["user_id"])]
            raw["roles"] = [_PLATFORM_SUPERADMIN_ROLE]
            raw["account_scope"] = "platform"
            raw["is_platform_user"] = True
            raw["force_password_change"] = bool(force_password_change)
            if normalized_email:
                raw["email"] = normalized_email
            self._persist()
            return {
                "operation": "created",
                "user": self._public_user(raw),
            }

        user_tenant_id = _require_tenant_id(existing.get("tenant_id"), operation="platform_superadmin_existing_user")
        if user_tenant_id != tenant_id:
            raise HTTPException(
                status_code=409,
                detail="login belongs to another tenant; cannot repurpose as platform superadmin",
            )

        changed = False
        user_roles = [str(role).strip() for role in existing.get("roles", []) if str(role).strip()]
        if user_roles != [_PLATFORM_SUPERADMIN_ROLE]:
            existing["roles"] = [_PLATFORM_SUPERADMIN_ROLE]
            changed = True

        if existing.get("account_scope") != "platform":
            existing["account_scope"] = "platform"
            changed = True

        if not bool(existing.get("is_platform_user", False)):
            existing["is_platform_user"] = True
            changed = True

        current_force_password_change = bool(existing.get("force_password_change", False))
        if current_force_password_change != bool(force_password_change):
            existing["force_password_change"] = bool(force_password_change)
            changed = True

        if normalized_email and str(existing.get("email", "")).strip().lower() != normalized_email:
            existing["email"] = normalized_email
            changed = True

        if update_password:
            self.set_password(str(existing.get("user_id", "")), normalized_password, tenant_id=tenant_id)
            changed = True

        if changed:
            self._persist()

        return {
            "operation": "updated" if changed else "noop",
            "user": self._public_user(existing),
        }


local_user_store = LocalUserStore()
