from __future__ import annotations

from app.core.db import get_raw_conn

import json
import logging
import os
import secrets
from base64 import urlsafe_b64encode
from contextlib import contextmanager
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from typing import Any

from app.core.errors import DependencyUnavailableError
from app.modules.auth.local_users_service import local_user_store
from app.modules.identity.identity_errors import (
    IdentityError,
    IdentityGroupFetchFailed,
    IdentityInvalidCredentials,
    IdentityLdapBindFailed,
    IdentityLdapConnectFailed,
    IdentityLdapUserNotFound,
    IdentityMappingEmpty,
    IdentityMappingInvalid,
    IdentityProviderDisabled,
    IdentityProviderNotFound,
    IdentityProviderUnavailable,
    IdentityRateLimited,
    IdentityAccountLocked,
)
from app.modules.rbac.service import sync_user_roles_from_trusted_source


logger = logging.getLogger("app.identity")
_SECRET_PREFIX = "enc:v1:"


try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


def _db_url() -> str | None:
    raw = os.getenv("DATABASE_URL", "").strip()
    if not raw:
        return None
    return raw.replace("postgresql+psycopg://", "postgresql://", 1)


@contextmanager
def _conn():
    url = _db_url()
    if not url or psycopg is None:
        raise DependencyUnavailableError("identity database unavailable")

    try:
        with get_raw_conn() as conn:
            yield conn
    except IdentityError:
        raise
    except DependencyUnavailableError:
        raise
    except Exception as exc:
        raise DependencyUnavailableError("identity database unavailable") from exc


def _raw_encryption_secret() -> str:
    explicit = os.getenv("INTEGRATIONS_ENCRYPTION_KEY", "").strip()
    if explicit:
        return explicit
    return os.getenv("JWT_SECRET", "change_me_jwt_secret")


def _encrypt_secret(value: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return ""
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:  # pragma: no cover
        raise DependencyUnavailableError("identity encryption dependency unavailable") from exc

    digest = sha256(_raw_encryption_secret().encode("utf-8")).digest()
    key = urlsafe_b64encode(digest)
    token = Fernet(key).encrypt(normalized.encode("utf-8")).decode("utf-8")
    return f"{_SECRET_PREFIX}{token}"


def _decrypt_secret(value: str | None) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if not raw.startswith(_SECRET_PREFIX):
        return raw

    try:
        from cryptography.fernet import Fernet, InvalidToken
    except ImportError as exc:  # pragma: no cover
        raise DependencyUnavailableError("identity encryption dependency unavailable") from exc

    digest = sha256(_raw_encryption_secret().encode("utf-8")).digest()
    key = urlsafe_b64encode(digest)
    token = raw[len(_SECRET_PREFIX) :]
    try:
        return Fernet(key).decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return ""


def _iso(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _validate_provider_type(provider_type: str) -> str:
    normalized = str(provider_type).strip().lower()
    if normalized not in {"local", "ldap", "ad"}:
        raise IdentityMappingInvalid("provider type must be local, ldap, or ad")
    return normalized


def _validate_external_group(value: str) -> str:
    normalized = str(value).strip()
    if not normalized or len(normalized) > 512:
        raise IdentityMappingInvalid("external_group is invalid")
    return normalized


def _validate_role(conn: Any, *, tenant_id: int, role: str) -> str:
    normalized = str(role).strip()
    if not normalized:
        raise IdentityMappingInvalid("platform_role is required")

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
              FROM app_roles
             WHERE name = %s
               AND tenant_id IN (%s, 1)
             LIMIT 1
            """,
            (normalized, int(tenant_id)),
        )
        if cur.fetchone() is None:
            raise IdentityMappingInvalid("platform_role does not exist")
    return normalized


def _normalized_mappings(conn: Any, *, tenant_id: int, mappings: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    if not mappings:
        return []

    normalized: list[dict[str, str]] = []
    for row in mappings:
        external_group = _validate_external_group((row or {}).get("external_group", ""))
        platform_role = _validate_role(conn, tenant_id=int(tenant_id), role=(row or {}).get("platform_role", ""))
        normalized.append({"external_group": external_group, "platform_role": platform_role})

    dedup: dict[str, str] = {}
    for row in normalized:
        dedup[row["external_group"].lower()] = row["platform_role"]
    return [
        {"external_group": group, "platform_role": role}
        for group, role in sorted(dedup.items(), key=lambda item: item[0])
    ]


def _normalized_config(config: dict[str, Any] | None) -> dict[str, Any]:
    source = config or {}
    host = str(source.get("host", "")).strip()
    if host.startswith("ldap://") or host.startswith("ldaps://"):
        host = host.split("://", 1)[1]

    timeout_seconds = int(source.get("timeout_seconds", 5) or 5)
    timeout_seconds = max(1, min(timeout_seconds, 30))

    return {
        "host": host,
        "port": int(source.get("port", 636 if bool(source.get("use_ssl", True)) else 389) or 0),
        "use_ssl": bool(source.get("use_ssl", True)),
        "base_dn": str(source.get("base_dn", "")).strip(),
        "bind_dn": str(source.get("bind_dn", "")).strip(),
        "user_filter": str(source.get("user_filter", "(sAMAccountName={username})")).strip() or "(sAMAccountName={username})",
        "group_attribute": str(source.get("group_attribute", "memberOf")).strip() or "memberOf",
        "display_name_attribute": str(source.get("display_name_attribute", "displayName")).strip() or "displayName",
        "login_attribute": str(source.get("login_attribute", "sAMAccountName")).strip() or "sAMAccountName",
        "external_id_attribute": str(source.get("external_id_attribute", "objectGUID")).strip() or "objectGUID",
        "email_attribute": str(source.get("email_attribute", "mail")).strip() or "mail",
        "timeout_seconds": timeout_seconds,
    }


def _normalized_policy(policy: dict[str, Any] | None) -> dict[str, Any]:
    source = policy or {}
    return {
        "is_default": bool(source.get("is_default", False)),
        "priority": max(0, int(source.get("priority", 100) or 100)),
        "allow_local_login": bool(source.get("allow_local_login", True)),
        "allow_external_login": bool(source.get("allow_external_login", True)),
        "login_hint": str(source.get("login_hint", "")).strip(),
        "auto_provision": bool(source.get("auto_provision", True)),
        "require_mapping": bool(source.get("require_mapping", True)),
    }


@dataclass
class IdentityProviderRecord:
    id: int
    tenant_id: int
    type: str
    name: str
    is_enabled: bool
    config_json: dict[str, Any]
    created_at: str
    updated_at: str
    mapping_count: int
    has_bind_password: bool
    is_default: bool
    priority: int
    allow_local_login: bool
    allow_external_login: bool
    login_hint: str
    auto_provision: bool
    require_mapping: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "type": self.type,
            "name": self.name,
            "is_enabled": self.is_enabled,
            "config": self.config_json,
            "mapping_count": self.mapping_count,
            "has_bind_password": self.has_bind_password,
            "is_default": self.is_default,
            "priority": self.priority,
            "allow_local_login": self.allow_local_login,
            "allow_external_login": self.allow_external_login,
            "login_hint": self.login_hint,
            "auto_provision": self.auto_provision,
            "require_mapping": self.require_mapping,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class IdentityMappingRecord:
    id: int
    tenant_id: int
    provider_id: int
    external_group: str
    platform_role: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "provider_id": self.provider_id,
            "external_group": self.external_group,
            "platform_role": self.platform_role,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def _row_to_provider(row: tuple[Any, ...]) -> IdentityProviderRecord:
    config = row[5] if isinstance(row[5], dict) else {}
    return IdentityProviderRecord(
        id=int(row[0]),
        tenant_id=int(row[1]),
        type=str(row[2]),
        name=str(row[3]),
        is_enabled=bool(row[4]),
        config_json=config,
        created_at=_iso(row[6]),
        updated_at=_iso(row[7]),
        mapping_count=int(row[8]),
        has_bind_password=bool(row[9]),
        is_default=bool(row[10]),
        priority=int(row[11]),
        allow_local_login=bool(row[12]),
        allow_external_login=bool(row[13]),
        login_hint=str(row[14] or ""),
        auto_provision=bool(row[15]),
        require_mapping=bool(row[16]),
    )


def _row_to_mapping(row: tuple[Any, ...]) -> IdentityMappingRecord:
    return IdentityMappingRecord(
        id=int(row[0]),
        tenant_id=int(row[1]),
        provider_id=int(row[2]),
        external_group=str(row[3]),
        platform_role=str(row[4]),
        created_at=_iso(row[5]),
        updated_at=_iso(row[6]),
    )


def _unset_default_provider(conn: Any, *, tenant_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE app_identity_providers SET is_default = FALSE WHERE tenant_id = %s",
            (int(tenant_id),),
        )


def list_directory_providers(*, tenant_id: int) -> list[dict[str, Any]]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    p.id,
                    p.tenant_id,
                    p.type,
                    p.name,
                    p.is_enabled,
                    p.config_json,
                    p.created_at,
                    p.updated_at,
                    COALESCE(COUNT(m.id), 0) AS mapping_count,
                    CASE WHEN COALESCE(s.bind_password_enc, '') <> '' THEN TRUE ELSE FALSE END AS has_bind_password,
                    p.is_default,
                    p.priority,
                    p.allow_local_login,
                    p.allow_external_login,
                    p.login_hint,
                    p.auto_provision,
                    p.require_mapping
                FROM app_identity_providers p
                LEFT JOIN app_identity_mappings m
                    ON m.provider_id = p.id
                   AND m.tenant_id = p.tenant_id
                LEFT JOIN app_identity_provider_secrets s
                    ON s.provider_id = p.id
                   AND s.tenant_id = p.tenant_id
                WHERE p.tenant_id = %s
                GROUP BY p.id, s.bind_password_enc
                ORDER BY p.is_default DESC, p.priority ASC, p.created_at DESC
                """,
                (int(tenant_id),),
            )
            rows = cur.fetchall() or []
    return [_row_to_provider(row).to_dict() for row in rows]


def list_identity_mappings(*, tenant_id: int, provider_id: int | None = None) -> list[dict[str, Any]]:
    with _conn() as conn:
        with conn.cursor() as cur:
            if provider_id is not None:
                cur.execute(
                    """
                    SELECT id, tenant_id, provider_id, external_group, platform_role, created_at, updated_at
                      FROM app_identity_mappings
                     WHERE tenant_id = %s AND provider_id = %s
                     ORDER BY id ASC
                    """,
                    (int(tenant_id), int(provider_id)),
                )
            else:
                cur.execute(
                    """
                    SELECT id, tenant_id, provider_id, external_group, platform_role, created_at, updated_at
                      FROM app_identity_mappings
                     WHERE tenant_id = %s
                     ORDER BY provider_id ASC, id ASC
                    """,
                    (int(tenant_id),),
                )
            rows = cur.fetchall() or []
    return [_row_to_mapping(row).to_dict() for row in rows]


def _replace_mappings(conn: Any, *, tenant_id: int, provider_id: int, mappings: list[dict[str, str]]) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM app_identity_mappings WHERE tenant_id = %s AND provider_id = %s",
            (int(tenant_id), int(provider_id)),
        )
        for row in mappings:
            cur.execute(
                """
                INSERT INTO app_identity_mappings(tenant_id, provider_id, external_group, platform_role)
                VALUES (%s, %s, %s, %s)
                """,
                (int(tenant_id), int(provider_id), row["external_group"], row["platform_role"]),
            )


def create_identity_mapping(*, tenant_id: int, provider_id: int, external_group: str, platform_role: str) -> dict[str, Any]:
    with _conn() as conn:
        _load_provider_with_secret(conn, tenant_id=int(tenant_id), provider_id=int(provider_id))
        normalized_group = _validate_external_group(external_group)
        normalized_role = _validate_role(conn, tenant_id=int(tenant_id), role=platform_role)

        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO app_identity_mappings(tenant_id, provider_id, external_group, platform_role)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, tenant_id, provider_id, external_group, platform_role, created_at, updated_at
                    """,
                    (int(tenant_id), int(provider_id), normalized_group, normalized_role),
                )
            except Exception as exc:
                message = str(exc).lower()
                if "uq_identity_mappings_group" in message or "duplicate key" in message:
                    raise IdentityMappingInvalid("mapping already exists") from exc
                raise
            row = cur.fetchone()
        conn.commit()
    return _row_to_mapping(row).to_dict()


def update_identity_mapping(*, tenant_id: int, mapping_id: int, external_group: str, platform_role: str) -> dict[str, Any]:
    with _conn() as conn:
        normalized_group = _validate_external_group(external_group)
        normalized_role = _validate_role(conn, tenant_id=int(tenant_id), role=platform_role)

        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE app_identity_mappings
                   SET external_group = %s,
                       platform_role = %s,
                       updated_at = NOW()
                 WHERE tenant_id = %s AND id = %s
                 RETURNING id, tenant_id, provider_id, external_group, platform_role, created_at, updated_at
                """,
                (normalized_group, normalized_role, int(tenant_id), int(mapping_id)),
            )
            row = cur.fetchone()
            if row is None:
                raise IdentityMappingInvalid("mapping not found")
        conn.commit()
    return _row_to_mapping(row).to_dict()


def delete_identity_mapping(*, tenant_id: int, mapping_id: int) -> bool:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM app_identity_mappings WHERE tenant_id = %s AND id = %s",
                (int(tenant_id), int(mapping_id)),
            )
            deleted = cur.rowcount > 0
        conn.commit()
    return bool(deleted)


def _upsert_secret(conn: Any, *, tenant_id: int, provider_id: int, bind_password: str | None) -> None:
    if bind_password is None:
        return
    encrypted = _encrypt_secret(bind_password)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO app_identity_provider_secrets(provider_id, tenant_id, bind_password_enc)
            VALUES (%s, %s, %s)
            ON CONFLICT (provider_id)
            DO UPDATE SET
                tenant_id = EXCLUDED.tenant_id,
                bind_password_enc = EXCLUDED.bind_password_enc,
                updated_at = NOW()
            """,
            (int(provider_id), int(tenant_id), encrypted),
        )


def _load_provider_with_secret(conn: Any, *, tenant_id: int, provider_id: int) -> tuple[IdentityProviderRecord, str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                p.id,
                p.tenant_id,
                p.type,
                p.name,
                p.is_enabled,
                p.config_json,
                p.created_at,
                p.updated_at,
                COALESCE(COUNT(m.id), 0) AS mapping_count,
                CASE WHEN COALESCE(s.bind_password_enc, '') <> '' THEN TRUE ELSE FALSE END AS has_bind_password,
                p.is_default,
                p.priority,
                p.allow_local_login,
                p.allow_external_login,
                p.login_hint,
                p.auto_provision,
                p.require_mapping,
                COALESCE(s.bind_password_enc, '') AS bind_password_enc
            FROM app_identity_providers p
            LEFT JOIN app_identity_mappings m
                ON m.provider_id = p.id
               AND m.tenant_id = p.tenant_id
            LEFT JOIN app_identity_provider_secrets s
                ON s.provider_id = p.id
               AND s.tenant_id = p.tenant_id
            WHERE p.tenant_id = %s AND p.id = %s
            GROUP BY p.id, s.bind_password_enc
            """,
            (int(tenant_id), int(provider_id)),
        )
        row = cur.fetchone()
    if row is None:
        raise IdentityProviderNotFound()
    return _row_to_provider(row[:17]), str(row[17] or "")


def _load_provider_by_name(conn: Any, *, tenant_id: int, provider_name: str) -> tuple[IdentityProviderRecord, str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT p.id
              FROM app_identity_providers p
             WHERE p.tenant_id = %s
               AND lower(p.name) = %s
             LIMIT 1
            """,
            (int(tenant_id), str(provider_name).strip().lower()),
        )
        row = cur.fetchone()
    if row is None:
        raise IdentityProviderNotFound()
    return _load_provider_with_secret(conn, tenant_id=int(tenant_id), provider_id=int(row[0]))


def _select_default_or_priority_provider(conn: Any, *, tenant_id: int) -> tuple[IdentityProviderRecord, str] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT p.id
              FROM app_identity_providers p
             WHERE p.tenant_id = %s
               AND p.is_enabled = TRUE
             ORDER BY p.is_default DESC, p.priority ASC, p.id ASC
             LIMIT 1
            """,
            (int(tenant_id),),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return _load_provider_with_secret(conn, tenant_id=int(tenant_id), provider_id=int(row[0]))


def create_directory_provider(
    *,
    tenant_id: int,
    provider_type: str,
    name: str,
    is_enabled: bool,
    config: dict[str, Any] | None,
    bind_password: str | None,
    mappings: list[dict[str, Any]] | None,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_type = _validate_provider_type(provider_type)
    normalized_name = str(name).strip()
    if not normalized_name:
        raise IdentityMappingInvalid("provider name is required")

    normalized_config = _normalized_config(config)

    with _conn() as conn:
        normalized_policy = _normalized_policy(policy)
        normalized_mappings = _normalized_mappings(conn, tenant_id=int(tenant_id), mappings=mappings)

        if normalized_type in {"ldap", "ad"}:
            required = ("host", "base_dn", "bind_dn")
            missing = [field for field in required if not str(normalized_config.get(field, "")).strip()]
            if missing:
                raise IdentityMappingInvalid(f"provider config is incomplete: missing {', '.join(missing)}")
            if not bind_password:
                raise IdentityMappingInvalid("bind password is required for ldap/ad providers")

        if normalized_policy["is_default"]:
            _unset_default_provider(conn, tenant_id=int(tenant_id))

        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO app_identity_providers(
                        tenant_id,
                        type,
                        name,
                        is_enabled,
                        config_json,
                        is_default,
                        priority,
                        allow_local_login,
                        allow_external_login,
                        login_hint,
                        auto_provision,
                        require_mapping
                    )
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        int(tenant_id),
                        normalized_type,
                        normalized_name,
                        bool(is_enabled),
                        json.dumps(normalized_config),
                        bool(normalized_policy["is_default"]),
                        int(normalized_policy["priority"]),
                        bool(normalized_policy["allow_local_login"]),
                        bool(normalized_policy["allow_external_login"]),
                        str(normalized_policy["login_hint"]),
                        bool(normalized_policy["auto_provision"]),
                        bool(normalized_policy["require_mapping"]),
                    ),
                )
            except Exception as exc:
                message = str(exc).lower()
                if "uq_identity_providers_tenant_name" in message or "duplicate key" in message:
                    raise IdentityMappingInvalid("identity provider name already exists for tenant") from exc
                raise
            provider_id = int(cur.fetchone()[0])

        _upsert_secret(conn, tenant_id=int(tenant_id), provider_id=provider_id, bind_password=bind_password)
        _replace_mappings(conn, tenant_id=int(tenant_id), provider_id=provider_id, mappings=normalized_mappings)
        conn.commit()

        provider, _ = _load_provider_with_secret(conn, tenant_id=int(tenant_id), provider_id=provider_id)
    return provider.to_dict()


def update_directory_provider(
    *,
    tenant_id: int,
    provider_id: int,
    payload: dict[str, Any],
) -> dict[str, Any]:
    with _conn() as conn:
        provider, _existing_secret = _load_provider_with_secret(conn, tenant_id=int(tenant_id), provider_id=int(provider_id))

        provider_type = payload.get("type", provider.type)
        name = payload.get("name", provider.name)
        is_enabled = bool(payload.get("is_enabled", provider.is_enabled))
        config = dict(provider.config_json)
        if "config" in payload and isinstance(payload.get("config"), dict):
            config.update(_normalized_config(payload.get("config")))

        normalized_type = _validate_provider_type(str(provider_type))
        normalized_name = str(name).strip()
        if not normalized_name:
            raise IdentityMappingInvalid("provider name is required")

        payload_policy = payload.get("policy") if isinstance(payload.get("policy"), dict) else {}
        policy = _normalized_policy(
            {
                "is_default": payload_policy.get("is_default", payload.get("is_default", provider.is_default)),
                "priority": payload_policy.get("priority", payload.get("priority", provider.priority)),
                "allow_local_login": payload_policy.get(
                    "allow_local_login",
                    payload.get("allow_local_login", provider.allow_local_login),
                ),
                "allow_external_login": payload_policy.get(
                    "allow_external_login",
                    payload.get("allow_external_login", provider.allow_external_login),
                ),
                "login_hint": payload_policy.get("login_hint", payload.get("login_hint", provider.login_hint)),
                "auto_provision": payload_policy.get("auto_provision", payload.get("auto_provision", provider.auto_provision)),
                "require_mapping": payload_policy.get("require_mapping", payload.get("require_mapping", provider.require_mapping)),
            }
        )

        if normalized_type in {"ldap", "ad"}:
            required = ("host", "base_dn", "bind_dn")
            missing = [field for field in required if not str(config.get(field, "")).strip()]
            if missing:
                raise IdentityMappingInvalid(f"provider config is incomplete: missing {', '.join(missing)}")

        if policy["is_default"]:
            _unset_default_provider(conn, tenant_id=int(tenant_id))

        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE app_identity_providers
                   SET type = %s,
                       name = %s,
                       is_enabled = %s,
                       config_json = %s::jsonb,
                       is_default = %s,
                       priority = %s,
                       allow_local_login = %s,
                       allow_external_login = %s,
                       login_hint = %s,
                       auto_provision = %s,
                       require_mapping = %s,
                       updated_at = NOW()
                 WHERE id = %s AND tenant_id = %s
                """,
                (
                    normalized_type,
                    normalized_name,
                    bool(is_enabled),
                    json.dumps(config),
                    bool(policy["is_default"]),
                    int(policy["priority"]),
                    bool(policy["allow_local_login"]),
                    bool(policy["allow_external_login"]),
                    str(policy["login_hint"]),
                    bool(policy["auto_provision"]),
                    bool(policy["require_mapping"]),
                    int(provider_id),
                    int(tenant_id),
                ),
            )

        _upsert_secret(conn, tenant_id=int(tenant_id), provider_id=int(provider_id), bind_password=payload.get("bind_password"))

        if "mappings" in payload:
            _replace_mappings(
                conn,
                tenant_id=int(tenant_id),
                provider_id=int(provider_id),
                mappings=_normalized_mappings(conn, tenant_id=int(tenant_id), mappings=payload.get("mappings") or []),
            )

        conn.commit()
        updated, _ = _load_provider_with_secret(conn, tenant_id=int(tenant_id), provider_id=int(provider_id))
    return updated.to_dict()


def _provider_uri(config: dict[str, Any]) -> str:
    host = str(config.get("host", "")).strip()
    if not host:
        raise IdentityMappingInvalid("provider host is required")
    if host.startswith("ldap://") or host.startswith("ldaps://"):
        return host
    scheme = "ldaps" if bool(config.get("use_ssl", True)) else "ldap"
    port = int(config.get("port", 636 if scheme == "ldaps" else 389) or 0)
    if port > 0:
        return f"{scheme}://{host}:{port}"
    return f"{scheme}://{host}"


def _parse_group_values(entry: Any, group_attr: str) -> list[str]:
    if group_attr not in entry:
        return []
    values = entry[group_attr].value
    if values is None:
        return []
    if isinstance(values, str):
        return [values]
    return [str(item) for item in values]


def _group_roles(conn: Any, *, tenant_id: int, provider_id: int, groups: list[str]) -> list[str]:
    if not groups:
        return []

    normalized = [item.strip().lower() for item in groups if item.strip()]
    if not normalized:
        return []

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT external_group, platform_role
              FROM app_identity_mappings
             WHERE tenant_id = %s
               AND provider_id = %s
            """,
            (int(tenant_id), int(provider_id)),
        )
        rows = cur.fetchall() or []

    role_map = {str(row[0]).strip().lower(): str(row[1]).strip() for row in rows}
    return sorted({role_map[group] for group in normalized if group in role_map and role_map[group]})


def _upsert_external_identity(
    conn: Any,
    *,
    tenant_id: int,
    provider_id: int,
    local_user_id: str,
    external_user_id: str,
    username: str,
    email: str,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO app_external_identities(
                tenant_id,
                provider_id,
                local_user_id,
                external_user_id,
                username,
                email,
                synced_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (tenant_id, provider_id, external_user_id)
            DO UPDATE SET
                local_user_id = EXCLUDED.local_user_id,
                username = EXCLUDED.username,
                email = EXCLUDED.email,
                synced_at = NOW(),
                updated_at = NOW()
            """,
            (
                int(tenant_id),
                int(provider_id),
                str(local_user_id),
                str(external_user_id),
                str(username or ""),
                str(email or ""),
            ),
        )


def _normalize_ldap_exception(exc: Exception, *, stage: str) -> IdentityError:
    message = str(exc).lower()
    if "invalidcredentials" in message or "invalid credentials" in message:
        return IdentityInvalidCredentials(details=f"{stage}:{exc}")
    if stage == "bind_user":
        return IdentityLdapBindFailed(details=str(exc))
    if stage == "bind_service":
        if "timeout" in message or "socket" in message or "connection" in message:
            return IdentityLdapConnectFailed(details=str(exc))
        return IdentityLdapBindFailed(details=str(exc))
    if "timeout" in message or "socket" in message or "connection" in message:
        return IdentityLdapConnectFailed(details=str(exc))
    if stage == "search":
        return IdentityLdapUserNotFound(details=str(exc))
    if stage == "group":
        return IdentityGroupFetchFailed(details=str(exc))
    return IdentityProviderUnavailable(details=f"{stage}:{exc}")


def _ldap_search_groups(
    *,
    provider: IdentityProviderRecord,
    bind_password: str,
    username: str,
    password: str | None,
) -> tuple[str, str, str, str, list[str]]:
    try:
        from ldap3 import ALL, Connection, Server
        from ldap3.core.exceptions import LDAPException
        from ldap3.utils.conv import escape_filter_chars
    except ImportError as exc:  # pragma: no cover
        raise IdentityProviderUnavailable(details=f"ldap_dependency:{exc}") from exc

    config = provider.config_json
    server = Server(
        _provider_uri(config),
        get_info=ALL,
        connect_timeout=int(config.get("timeout_seconds", 5) or 5),
        use_ssl=bool(config.get("use_ssl", True)),
    )

    try:
        with Connection(server, user=str(config.get("bind_dn", "")), password=bind_password, auto_bind=True) as service_conn:
            user_filter = str(config.get("user_filter", "(sAMAccountName={username})"))
            search_filter = user_filter.format(username=escape_filter_chars(str(username)))
            group_attr = str(config.get("group_attribute", "memberOf"))
            display_name_attr = str(config.get("display_name_attribute", "displayName"))
            login_attr = str(config.get("login_attribute", "sAMAccountName"))
            external_id_attr = str(config.get("external_id_attribute", "objectGUID"))
            email_attr = str(config.get("email_attribute", "mail"))

            attrs = [display_name_attr, login_attr, group_attr, external_id_attr, email_attr]
            search_ok = service_conn.search(
                search_base=str(config.get("base_dn", "")),
                search_filter=search_filter,
                attributes=attrs,
            )
            if not search_ok or not service_conn.entries:
                raise IdentityLdapUserNotFound(details=f"username={username}")

            entry = service_conn.entries[0]
            if password is not None:
                try:
                    with Connection(server, user=entry.entry_dn, password=password, auto_bind=True):
                        pass
                except LDAPException as exc:
                    raise _normalize_ldap_exception(exc, stage="bind_user") from exc

            groups = _parse_group_values(entry, group_attr)
            resolved_login = str(entry[login_attr].value) if login_attr in entry and entry[login_attr].value else str(username)
            resolved_login = resolved_login.strip().lower()
            display_name = (
                str(entry[display_name_attr].value)
                if display_name_attr in entry and entry[display_name_attr].value
                else resolved_login
            )
            external_user_id = (
                str(entry[external_id_attr].value)
                if external_id_attr in entry and entry[external_id_attr].value
                else entry.entry_dn
            )
            email = str(entry[email_attr].value) if email_attr in entry and entry[email_attr].value else ""
            return resolved_login, display_name, external_user_id, email, groups
    except IdentityError:
        raise
    except LDAPException as exc:
        raise _normalize_ldap_exception(exc, stage="bind_service") from exc


def preview_provider_mapping(*, tenant_id: int, provider_id: int, username: str) -> dict[str, Any]:
    normalized_username = str(username).strip()
    if not normalized_username:
        raise IdentityLdapUserNotFound(details="empty username")

    with _conn() as conn:
        provider, secret_enc = _load_provider_with_secret(conn, tenant_id=int(tenant_id), provider_id=int(provider_id))
        if not provider.is_enabled:
            raise IdentityProviderDisabled()
        if provider.type not in {"ldap", "ad"}:
            raise IdentityMappingInvalid("mapping preview is only available for ldap/ad providers")

        bind_password = _decrypt_secret(secret_enc)
        if not bind_password:
            raise IdentityProviderUnavailable(details="missing bind password")

        resolved_login, display_name, external_user_id, email, groups = _ldap_search_groups(
            provider=provider,
            bind_password=bind_password,
            username=normalized_username,
            password=None,
        )
        roles = _group_roles(conn, tenant_id=int(tenant_id), provider_id=int(provider.id), groups=groups)

    return {
        "provider_id": provider.id,
        "username": resolved_login,
        "display_name": display_name,
        "external_user_id": external_user_id,
        "email": email,
        "groups": groups,
        "mapped_roles": roles,
        "mapping_empty": len(roles) == 0,
    }


def test_directory_provider(
    *,
    tenant_id: int,
    provider_id: int,
    login: str | None = None,
    password: str | None = None,
) -> dict[str, Any]:
    with _conn() as conn:
        provider, secret_enc = _load_provider_with_secret(conn, tenant_id=int(tenant_id), provider_id=int(provider_id))
        if provider.type == "local":
            return {
                "provider_id": provider.id,
                "status": "ok",
                "mode": "local",
                "message": "local provider does not require external connectivity",
            }

        if provider.type not in {"ldap", "ad"}:
            raise IdentityMappingInvalid("unsupported provider type")

        bind_password = _decrypt_secret(secret_enc)
        if not bind_password:
            raise IdentityProviderUnavailable(details="missing bind password")

        checked_user = False
        if login:
            _ldap_search_groups(provider=provider, bind_password=bind_password, username=login, password=password)
            checked_user = password is not None
        else:
            _ldap_search_groups(provider=provider, bind_password=bind_password, username="healthcheck", password=None)

        return {
            "provider_id": provider.id,
            "status": "ok",
            "mode": provider.type,
            "mapping_count": provider.mapping_count,
            "user_check": checked_user,
        }


@lru_cache(maxsize=1)
def _get_security_redis():
    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url:
        return None
    try:
        import redis
    except ImportError:  # pragma: no cover
        return None

    try:
        client = redis.Redis.from_url(redis_url, decode_responses=True, socket_timeout=1)
        client.ping()
        return client
    except Exception:
        return None


def _security_limits() -> tuple[int, int, int, int, int]:
    ip_limit = max(1, int(os.getenv("IDENTITY_LOGIN_RATE_LIMIT_IP", "20") or 20))
    user_limit = max(1, int(os.getenv("IDENTITY_LOGIN_RATE_LIMIT_USER", "10") or 10))
    window_seconds = max(10, int(os.getenv("IDENTITY_LOGIN_RATE_WINDOW_SECONDS", "60") or 60))
    lock_threshold = max(3, int(os.getenv("IDENTITY_LOGIN_LOCK_THRESHOLD", "5") or 5))
    lock_seconds = max(30, int(os.getenv("IDENTITY_LOGIN_LOCK_SECONDS", "900") or 900))
    return ip_limit, user_limit, window_seconds, lock_threshold, lock_seconds


def _security_key(prefix: str, tenant_id: int, value: str) -> str:
    return f"identity:{prefix}:{int(tenant_id)}:{value.strip().lower()}"


def _check_rate_limit(*, tenant_id: int, ip: str, username: str) -> None:
    ip_limit, user_limit, window_seconds, _, _ = _security_limits()
    client = _get_security_redis()
    if client is None:
        return

    for key, limit in (
        (_security_key("rl:ip", tenant_id, ip), ip_limit),
        (_security_key("rl:user", tenant_id, username), user_limit),
    ):
        count = int(client.incr(key))
        if count == 1:
            client.expire(key, int(window_seconds))
        if count > limit:
            raise IdentityRateLimited(details=f"key={key},count={count},limit={limit}")


def _check_account_lock(*, tenant_id: int, username: str) -> None:
    client = _get_security_redis()
    if client is None:
        return
    lock_key = _security_key("lock", tenant_id, username)
    if int(client.exists(lock_key)) > 0:
        raise IdentityAccountLocked()


def _record_failed_login(*, tenant_id: int, username: str) -> None:
    _, _, window_seconds, lock_threshold, lock_seconds = _security_limits()
    client = _get_security_redis()
    if client is None:
        return
    fail_key = _security_key("fail", tenant_id, username)
    lock_key = _security_key("lock", tenant_id, username)

    attempts = int(client.incr(fail_key))
    if attempts == 1:
        client.expire(fail_key, int(window_seconds))
    if attempts >= lock_threshold:
        client.setex(lock_key, int(lock_seconds), "1")


def _clear_failed_login(*, tenant_id: int, username: str) -> None:
    client = _get_security_redis()
    if client is None:
        return
    client.delete(_security_key("fail", tenant_id, username))
    client.delete(_security_key("lock", tenant_id, username))


def _authenticate_local(login: str, password: str, tenant_id: int) -> dict[str, Any] | None:
    local_user = local_user_store.authenticate(login, password)
    if local_user is None:
        return None
    local_user_tenant = local_user.get("tenant_id")
    if local_user_tenant is None:
        return None
    if int(local_user_tenant) != int(tenant_id):
        return None
    user_id = str(local_user.get("user_id", ""))
    roles = [str(item).strip() for item in local_user.get("roles", []) if str(item).strip()]
    sync_user_roles_from_trusted_source(user_id, roles, tenant_id=int(tenant_id))
    return {
        "user_id": user_id,
        "display_name": str(local_user.get("display_name", user_id)),
        "roles": roles,
        "language": str(local_user.get("default_language", "ru")),
        "auth_source": "local",
        "sync_with_ad": False,
    }


def _authenticate_via_provider(
    conn: Any,
    *,
    tenant_id: int,
    provider: IdentityProviderRecord,
    secret_enc: str,
    login: str,
    password: str,
) -> dict[str, Any]:
    if provider.type not in {"ldap", "ad"}:
        raise IdentityMappingInvalid("unsupported provider type")

    bind_password = _decrypt_secret(secret_enc)
    if not bind_password:
        raise IdentityProviderUnavailable(details="missing bind password")

    resolved_login, display_name, external_user_id, email, groups = _ldap_search_groups(
        provider=provider,
        bind_password=bind_password,
        username=login,
        password=password,
    )

    roles = _group_roles(conn, tenant_id=int(tenant_id), provider_id=int(provider.id), groups=groups)
    if provider.require_mapping and not roles:
        raise IdentityMappingEmpty()

    local_user = local_user_store.find_user_by_login(resolved_login)
    if local_user is None:
        if not provider.auto_provision:
            raise IdentityMappingInvalid("auto provisioning disabled")
        local_user = local_user_store.create_user(
            login=resolved_login,
            password=secrets.token_urlsafe(24),
            display_name=display_name,
            roles=roles or ["student"],
            default_language="ru",
            tenant_id=int(tenant_id),
        )
    else:
        local_user_tenant = local_user.get("tenant_id")
        if local_user_tenant is None or int(local_user_tenant) != int(tenant_id):
            raise IdentityMappingInvalid("identity tenant mismatch")
        local_user = local_user_store.update_user(
            user_id=str(local_user.get("user_id", "")),
            tenant_id=int(tenant_id),
            display_name=display_name,
            roles=roles or list(local_user.get("roles", [])),
        )

    local_user_id = str(local_user.get("user_id", ""))
    sync_user_roles_from_trusted_source(local_user_id, roles or list(local_user.get("roles", [])), tenant_id=int(tenant_id))
    _upsert_external_identity(
        conn,
        tenant_id=int(tenant_id),
        provider_id=int(provider.id),
        local_user_id=local_user_id,
        external_user_id=external_user_id,
        username=resolved_login,
        email=email,
    )

    return {
        "user_id": local_user_id,
        "display_name": str(local_user.get("display_name", display_name)),
        "roles": roles or [str(item).strip() for item in local_user.get("roles", []) if str(item).strip()],
        "language": str(local_user.get("default_language", "ru")),
        "auth_source": provider.type,
        "sync_with_ad": True,
        "provider": provider.name,
    }


def _resolve_provider_for_login(
    conn: Any,
    *,
    tenant_id: int,
    provider_name: str | None,
) -> tuple[IdentityProviderRecord, str] | None:
    selected_name = str(provider_name or "").strip().lower()
    if selected_name:
        if selected_name == "local":
            return None
        return _load_provider_by_name(conn, tenant_id=int(tenant_id), provider_name=selected_name)

    return _select_default_or_priority_provider(conn, tenant_id=int(tenant_id))


def authenticate_tenant_login(
    *,
    tenant_id: int,
    login: str,
    password: str,
    provider_name: str | None = None,
    client_ip: str = "unknown",
) -> dict[str, Any]:
    normalized_login = str(login).strip()
    if not normalized_login:
        raise IdentityInvalidCredentials(details="empty login")
    normalized_password = str(password)
    if not normalized_password:
        raise IdentityInvalidCredentials(details="empty password")

    _check_rate_limit(tenant_id=int(tenant_id), ip=str(client_ip or "unknown"), username=normalized_login)
    _check_account_lock(tenant_id=int(tenant_id), username=normalized_login)

    normalized_provider_name = str(provider_name or "").strip().lower()
    local_auth_allowed = not normalized_provider_name or normalized_provider_name == "local"

    try:
        with _conn() as conn:
            provider_bundle = _resolve_provider_for_login(
                conn,
                tenant_id=int(tenant_id),
                provider_name=provider_name,
            )

            if provider_bundle is None:
                local = _authenticate_local(normalized_login, normalized_password, int(tenant_id))
                if local is None:
                    _record_failed_login(tenant_id=int(tenant_id), username=normalized_login)
                    raise IdentityInvalidCredentials(details="local auth failed")
                _clear_failed_login(tenant_id=int(tenant_id), username=normalized_login)
                return local

            provider, secret_enc = provider_bundle
            if not provider.is_enabled:
                raise IdentityProviderDisabled()

            if provider.allow_local_login:
                local = _authenticate_local(normalized_login, normalized_password, int(tenant_id))
                if local is not None:
                    _clear_failed_login(tenant_id=int(tenant_id), username=normalized_login)
                    return local

            if provider.type == "local" or not provider.allow_external_login:
                _record_failed_login(tenant_id=int(tenant_id), username=normalized_login)
                raise IdentityInvalidCredentials(details="external login disabled")

            try:
                result = _authenticate_via_provider(
                    conn,
                    tenant_id=int(tenant_id),
                    provider=provider,
                    secret_enc=secret_enc,
                    login=normalized_login,
                    password=normalized_password,
                )
                conn.commit()
            except IdentityError as exc:
                if isinstance(exc, (IdentityInvalidCredentials, IdentityLdapUserNotFound, IdentityMappingEmpty, IdentityMappingInvalid)):
                    _record_failed_login(tenant_id=int(tenant_id), username=normalized_login)
                raise
    except DependencyUnavailableError:
        if local_auth_allowed:
            local = _authenticate_local(normalized_login, normalized_password, int(tenant_id))
            if local is not None:
                _clear_failed_login(tenant_id=int(tenant_id), username=normalized_login)
                return local
        raise

    _clear_failed_login(tenant_id=int(tenant_id), username=normalized_login)
    logger.info(
        "identity_login_success",
        extra={
            "tenant_id": int(tenant_id),
            "auth_source": result.get("auth_source"),
            "provider": result.get("provider"),
            "user_id": result.get("user_id"),
        },
    )
    return result
