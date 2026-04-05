from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.modules.integrations.service import get_setting, save_setting


_SERVICE_ACCOUNTS_KEY = "auth.service_accounts_json"


_state_lock = Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def _load_accounts(*, tenant_id: int) -> list[dict[str, Any]]:
    entry = get_setting(_SERVICE_ACCOUNTS_KEY, tenant_id=tenant_id)
    if entry is None or not entry.value:
        return []
    try:
        payload = json.loads(entry.value)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in payload:
        if isinstance(item, dict):
            rows.append(dict(item))
    return rows


def _save_accounts(*, tenant_id: int, rows: list[dict[str, Any]]) -> None:
    save_setting(_SERVICE_ACCOUNTS_KEY, json.dumps(rows), is_secret=True, tenant_id=tenant_id)


def list_service_accounts(*, tenant_id: int) -> list[dict[str, Any]]:
    rows = _load_accounts(tenant_id=tenant_id)
    result: list[dict[str, Any]] = []
    for item in rows:
        result.append(
            {
                "account_id": item.get("account_id"),
                "name": item.get("name"),
                "permissions": item.get("permissions", []),
                "active": bool(item.get("active", False)),
                "platform_global": bool(item.get("platform_global", False)),
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
            }
        )
    return result


def get_service_account(*, tenant_id: int, account_id: str) -> dict[str, Any] | None:
    account = _find_account(tenant_id=tenant_id, account_id=account_id)
    if account is None:
        return None
    return {
        "account_id": account.get("account_id"),
        "name": account.get("name"),
        "permissions": account.get("permissions", []),
        "active": bool(account.get("active", False)),
        "platform_global": bool(account.get("platform_global", False)),
        "created_at": account.get("created_at"),
        "updated_at": account.get("updated_at"),
    }


def is_service_account_active(*, tenant_id: int, account_id: str) -> bool:
    account = _find_account(tenant_id=tenant_id, account_id=account_id)
    if account is None:
        return False
    return bool(account.get("active", False))


def create_service_account(
    *,
    tenant_id: int,
    name: str,
    permissions: list[str],
    platform_global: bool = False,
) -> dict[str, Any]:
    normalized_name = str(name).strip()
    if not normalized_name:
        raise ValueError("service account name is required")
    normalized_permissions = [str(item).strip() for item in permissions if str(item).strip()]
    if not normalized_permissions:
        raise ValueError("service account permissions are required")
    if platform_global and int(tenant_id) != 1:
        raise ValueError("platform-global service account requires platform tenant")

    account_id = f"svc.{secrets.token_hex(6)}"
    secret = secrets.token_urlsafe(24)
    row = {
        "account_id": account_id,
        "name": normalized_name,
        "tenant_id": int(tenant_id),
        "permissions": normalized_permissions,
        "platform_global": bool(platform_global),
        "active": True,
        "secret_hash": _hash_secret(secret),
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }

    with _state_lock:
        rows = _load_accounts(tenant_id=tenant_id)
        rows.append(row)
        _save_accounts(tenant_id=tenant_id, rows=rows)

    public_row = dict(row)
    public_row.pop("secret_hash", None)
    public_row["secret"] = secret
    return public_row


def _find_account(*, tenant_id: int, account_id: str) -> dict[str, Any] | None:
    normalized_account_id = str(account_id).strip()
    if not normalized_account_id:
        return None
    rows = _load_accounts(tenant_id=tenant_id)
    for item in rows:
        if str(item.get("account_id", "")).strip() == normalized_account_id:
            return item
    return None


def issue_service_token_material(
    *,
    tenant_id: int,
    account_id: str,
    secret: str,
) -> dict[str, Any]:
    account = _find_account(tenant_id=tenant_id, account_id=account_id)
    if account is None:
        raise ValueError("service account not found")
    if not bool(account.get("active", False)):
        raise ValueError("service account disabled")
    expected = str(account.get("secret_hash", "")).strip()
    provided = _hash_secret(str(secret))
    if not expected or not hmac.compare_digest(expected, provided):
        raise ValueError("invalid service account secret")
    return {
        "account_id": str(account.get("account_id")),
        "permissions": [str(item) for item in account.get("permissions", []) if str(item).strip()],
        "platform_global": bool(account.get("platform_global", False)),
    }


def revoke_service_account(*, tenant_id: int, account_id: str) -> bool:
    normalized_account_id = str(account_id).strip()
    if not normalized_account_id:
        return False
    with _state_lock:
        rows = _load_accounts(tenant_id=tenant_id)
        changed = False
        for item in rows:
            if str(item.get("account_id", "")).strip() != normalized_account_id:
                continue
            if not bool(item.get("active", False)):
                return False
            item["active"] = False
            item["updated_at"] = _now_iso()
            changed = True
            break
        if changed:
            _save_accounts(tenant_id=tenant_id, rows=rows)
        return changed
