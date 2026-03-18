import hashlib
import hmac
import json
import secrets
from collections.abc import Iterable
from typing import Dict, List

from fastapi import HTTPException

from app.modules.integrations.service import get_setting, save_setting


_LOCAL_USERS_SETTINGS_KEY = "auth.local_users_json"
_PBKDF2_ITERATIONS = 200_000


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
        save_setting(_LOCAL_USERS_SETTINGS_KEY, json.dumps(payload), is_secret=True)

    def _load_once(self) -> None:
        if self._loaded:
            return
        self._loaded = True

        raw = get_setting(_LOCAL_USERS_SETTINGS_KEY)
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

            self._users_by_id[user_id] = item
            self._users_by_login[login] = user_id

            if user_id.startswith("local."):
                suffix = user_id.split(".", 1)[1]
                if suffix.isdigit():
                    max_id = max(max_id, int(suffix))

        stored_counter = payload.get("counter") if isinstance(payload, dict) else None
        self._counter = max(max_id, int(stored_counter) if isinstance(stored_counter, int) else 0)

    def _public_user(self, item: dict[str, object]) -> dict[str, object]:
        return {
            "user_id": item["user_id"],
            "login": item["login"],
            "display_name": item["display_name"],
            "roles": item["roles"],
            "default_language": item["default_language"],
            "auth_source": "local",
            "sync_with_ad": False,
        }

    def list_users(
        self,
        search: str | None = None,
        role: str | None = None,
        language: str | None = None,
    ) -> List[dict[str, object]]:
        self._load_once()
        normalized_search = (search or "").strip().lower()
        normalized_role = (role or "").strip().lower()
        normalized_language = (language or "").strip().lower()

        result: List[dict[str, object]] = []
        for item in self._users_by_id.values():
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
    ) -> dict[str, object]:
        self._load_once()
        normalized_login = login.strip().lower()
        if not normalized_login:
            raise HTTPException(status_code=400, detail="login is required")

        if normalized_login in self._users_by_login:
            raise HTTPException(status_code=409, detail="login already exists")

        self._counter += 1
        user_id = f"local.{self._counter:03d}"
        payload: dict[str, object] = {
            "user_id": user_id,
            "login": normalized_login,
            "password_hash": _hash_password(password),
            "display_name": display_name.strip(),
            "roles": [r.strip() for r in roles if r.strip()] or ["student"],
            "default_language": default_language,
            "auth_source": "local",
            "sync_with_ad": False,
        }

        self._users_by_id[user_id] = payload
        self._users_by_login[normalized_login] = user_id
        self._persist()
        return self._public_user(payload)

    def update_user(
        self,
        user_id: str,
        display_name: str | None = None,
        language: str | None = None,
        roles: List[str] | None = None,
    ) -> dict[str, object]:
        self._load_once()
        normalized_user_id = user_id.strip()
        user = self._users_by_id.get(normalized_user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="local user not found")

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

    def delete_user(self, user_id: str) -> bool:
        self._load_once()
        normalized_user_id = user_id.strip()
        user = self._users_by_id.pop(normalized_user_id, None)
        if user is None:
            raise HTTPException(status_code=404, detail="local user not found")

        normalized_login = str(user.get("login", "")).strip().lower()
        if normalized_login:
            self._users_by_login.pop(normalized_login, None)
        self._persist()
        return True

    def set_password(self, user_id: str, password: str) -> None:
        self._load_once()
        normalized_user_id = user_id.strip()
        user = self._users_by_id.get(normalized_user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="local user not found")

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


local_user_store = LocalUserStore()
