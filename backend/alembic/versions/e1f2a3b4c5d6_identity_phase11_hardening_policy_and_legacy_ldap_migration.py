"""identity phase 1.1 hardening policy and legacy ldap migration

Revision ID: e1f2a3b4c5d6
Revises: f6a2d1e9b3c4
Create Date: 2026-03-28 03:30:00.000000
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from urllib.parse import urlparse

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: str | Sequence[str] | None = "f6a2d1e9b3c4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_MIGRATION_MARKER_KEY = "migrated_from_legacy"


def _table_exists(conn: sa.engine.Connection, table_name: str) -> bool:
    row = conn.execute(
        sa.text(
            """
            SELECT 1
              FROM information_schema.tables
             WHERE table_schema = 'public'
               AND table_name = :table_name
             LIMIT 1
            """
        ),
        {"table_name": str(table_name)},
    ).fetchone()
    return row is not None


def _column_exists(conn: sa.engine.Connection, table_name: str, column_name: str) -> bool:
    row = conn.execute(
        sa.text(
            """
            SELECT 1
              FROM information_schema.columns
             WHERE table_schema = 'public'
               AND table_name = :table_name
               AND column_name = :column_name
             LIMIT 1
            """
        ),
        {"table_name": str(table_name), "column_name": str(column_name)},
    ).fetchone()
    return row is not None


def _ensure_base_identity_schema(conn: sa.engine.Connection) -> None:
    if not _table_exists(conn, "app_identity_providers"):
        op.execute(
            """
            CREATE TABLE IF NOT EXISTS app_identity_providers (
                id BIGSERIAL PRIMARY KEY,
                tenant_id BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
                type VARCHAR(16) NOT NULL,
                name VARCHAR(128) NOT NULL,
                is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
                config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                is_default BOOLEAN NOT NULL DEFAULT FALSE,
                priority INTEGER NOT NULL DEFAULT 100,
                allow_local_login BOOLEAN NOT NULL DEFAULT TRUE,
                allow_external_login BOOLEAN NOT NULL DEFAULT TRUE,
                login_hint VARCHAR(256) NOT NULL DEFAULT '',
                auto_provision BOOLEAN NOT NULL DEFAULT TRUE,
                require_mapping BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_identity_providers_tenant_name UNIQUE (tenant_id, name)
            )
            """
        )

    if not _table_exists(conn, "app_identity_provider_secrets"):
        op.execute(
            """
            CREATE TABLE IF NOT EXISTS app_identity_provider_secrets (
                provider_id BIGINT PRIMARY KEY REFERENCES app_identity_providers(id) ON DELETE CASCADE,
                tenant_id BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
                bind_password_enc TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_identity_provider_secrets_provider_tenant UNIQUE (provider_id, tenant_id)
            )
            """
        )

    if not _table_exists(conn, "app_identity_mappings"):
        op.execute(
            """
            CREATE TABLE IF NOT EXISTS app_identity_mappings (
                id BIGSERIAL PRIMARY KEY,
                tenant_id BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
                provider_id BIGINT NOT NULL REFERENCES app_identity_providers(id) ON DELETE CASCADE,
                external_group VARCHAR(512) NOT NULL,
                platform_role VARCHAR(128) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_identity_mappings_group UNIQUE (tenant_id, provider_id, external_group)
            )
            """
        )

    if not _table_exists(conn, "app_external_identities"):
        op.execute(
            """
            CREATE TABLE IF NOT EXISTS app_external_identities (
                id BIGSERIAL PRIMARY KEY,
                tenant_id BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
                provider_id BIGINT NOT NULL REFERENCES app_identity_providers(id) ON DELETE CASCADE,
                local_user_id VARCHAR(128) NOT NULL,
                external_user_id VARCHAR(512) NOT NULL,
                username VARCHAR(256),
                email VARCHAR(256),
                synced_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_external_identities_tenant_provider_external UNIQUE (tenant_id, provider_id, external_user_id),
                CONSTRAINT uq_external_identities_tenant_provider_local UNIQUE (tenant_id, provider_id, local_user_id)
            )
            """
        )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_identity_providers_tenant_default_priority
            ON app_identity_providers (tenant_id, is_default, priority)
        """
    )


def _to_bool(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _to_int(value: str | None, default: int) -> int:
    try:
        return int(str(value or "").strip())
    except Exception:
        return int(default)


def _parse_server_uri(uri: str) -> tuple[str, int, bool]:
    raw = str(uri or "").strip()
    if not raw:
        return "", 636, True

    parsed = urlparse(raw)
    if parsed.scheme:
        host = (parsed.hostname or "").strip()
        use_ssl = parsed.scheme.lower() == "ldaps"
        port = int(parsed.port or (636 if use_ssl else 389))
        return host, port, use_ssl

    host = raw.replace("ldap://", "").replace("ldaps://", "").strip().split("/", 1)[0]
    if ":" in host:
        left, right = host.rsplit(":", 1)
        host = left.strip()
        try:
            port = int(right)
        except Exception:
            port = 636
    else:
        port = 636
    return host, port, True


def _tenant_id_from_key(key: str) -> int | None:
    parts = key.split(":", 2)
    if len(parts) != 3:
        return None
    if parts[0] != "tenant":
        return None
    try:
        tenant_id = int(parts[1])
    except Exception:
        return None
    if tenant_id <= 0:
        return None
    if not parts[2].startswith("ldap."):
        return None
    return tenant_id


def _collect_legacy_ldap_settings(conn: sa.engine.Connection) -> dict[int, dict[str, str]]:
    rows = conn.execute(
        sa.text(
            """
            SELECT key, value
              FROM app_integration_settings
             WHERE key LIKE :pattern
            """
        ),
        {"pattern": "tenant:%:ldap.%"},
    ).fetchall()

    grouped: dict[int, dict[str, str]] = {}
    for key, value in rows:
        tenant_id = _tenant_id_from_key(str(key or ""))
        if tenant_id is None:
            continue
        scoped_key = str(key).split(":", 2)[2]
        grouped.setdefault(tenant_id, {})[scoped_key] = str(value or "")
    return grouped


def _provider_exists(conn: sa.engine.Connection, tenant_id: int) -> bool:
    row = conn.execute(
        sa.text(
            """
            SELECT 1
              FROM app_identity_providers
             WHERE tenant_id = :tenant_id
               AND type IN ('ldap', 'ad')
             LIMIT 1
            """
        ),
        {"tenant_id": int(tenant_id)},
    ).fetchone()
    return row is not None


def _has_default_provider(conn: sa.engine.Connection, tenant_id: int) -> bool:
    row = conn.execute(
        sa.text(
            """
            SELECT 1
              FROM app_identity_providers
             WHERE tenant_id = :tenant_id
               AND is_default = TRUE
             LIMIT 1
            """
        ),
        {"tenant_id": int(tenant_id)},
    ).fetchone()
    return row is not None


def _insert_legacy_provider(
    conn: sa.engine.Connection,
    *,
    tenant_id: int,
    settings: dict[str, str],
) -> int | None:
    enabled = _to_bool(settings.get("ldap.enabled", "false"))
    server_uri = str(settings.get("ldap.server_uri", "")).strip()
    bind_dn = str(settings.get("ldap.bind_dn", "")).strip()
    base_dn = str(settings.get("ldap.base_dn", "")).strip()

    has_any_config = bool(server_uri or bind_dn or base_dn or enabled)
    if not has_any_config:
        return None

    host, port, use_ssl = _parse_server_uri(server_uri)
    config: dict[str, object] = {
        "host": host,
        "port": int(port),
        "use_ssl": bool(use_ssl),
        "base_dn": base_dn,
        "bind_dn": bind_dn,
        "user_filter": str(settings.get("ldap.user_filter", "(sAMAccountName={username})")).strip() or "(sAMAccountName={username})",
        "group_attribute": str(settings.get("ldap.group_attribute", "memberOf")).strip() or "memberOf",
        "display_name_attribute": str(settings.get("ldap.display_name_attribute", "displayName")).strip() or "displayName",
        "login_attribute": str(settings.get("ldap.login_attribute", "sAMAccountName")).strip() or "sAMAccountName",
        "external_id_attribute": str(settings.get("ldap.external_id_attribute", "objectGUID")).strip() or "objectGUID",
        "email_attribute": str(settings.get("ldap.email_attribute", "mail")).strip() or "mail",
        "timeout_seconds": _to_int(settings.get("ldap.timeout_seconds"), 5),
        _MIGRATION_MARKER_KEY: True,
    }

    raw_group_map = str(settings.get("ldap.group_role_map_json", "{}")).strip() or "{}"
    parsed_group_map: dict[str, str] = {}
    try:
        candidate = json.loads(raw_group_map)
        if isinstance(candidate, dict):
            for key, value in candidate.items():
                group = str(key or "").strip()
                role = str(value or "").strip()
                if group and role:
                    parsed_group_map[group] = role
    except Exception:
        parsed_group_map = {}

    require_mapping = bool(parsed_group_map)
    is_default = not _has_default_provider(conn, tenant_id)

    provider_name = f"legacy-ldap-migrated-tenant-{int(tenant_id)}"
    provider_row = conn.execute(
        sa.text(
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
                require_mapping,
                created_at,
                updated_at
            )
            VALUES (
                :tenant_id,
                'ldap',
                :name,
                :is_enabled,
                :config_json,
                :is_default,
                100,
                TRUE,
                TRUE,
                'Use enterprise directory credentials',
                TRUE,
                :require_mapping,
                NOW(),
                NOW()
            )
            RETURNING id
            """
        ),
        {
            "tenant_id": int(tenant_id),
            "name": provider_name,
            "is_enabled": bool(enabled),
            "config_json": json.dumps(config),
            "is_default": bool(is_default),
            "require_mapping": bool(require_mapping),
        },
    ).fetchone()
    if provider_row is None:
        return None

    provider_id = int(provider_row[0])
    bind_password = str(settings.get("ldap.bind_password", "")).strip()
    if bind_password:
        conn.execute(
            sa.text(
                """
                INSERT INTO app_identity_provider_secrets(provider_id, tenant_id, bind_password_enc)
                VALUES (:provider_id, :tenant_id, :bind_password_enc)
                ON CONFLICT (provider_id)
                DO UPDATE SET
                    tenant_id = EXCLUDED.tenant_id,
                    bind_password_enc = EXCLUDED.bind_password_enc,
                    updated_at = NOW()
                """
            ),
            {
                "provider_id": int(provider_id),
                "tenant_id": int(tenant_id),
                "bind_password_enc": bind_password,
            },
        )

    for group, role in parsed_group_map.items():
        conn.execute(
            sa.text(
                """
                INSERT INTO app_identity_mappings(tenant_id, provider_id, external_group, platform_role, created_at, updated_at)
                VALUES (:tenant_id, :provider_id, :external_group, :platform_role, NOW(), NOW())
                ON CONFLICT (tenant_id, provider_id, external_group)
                DO UPDATE SET
                    platform_role = EXCLUDED.platform_role,
                    updated_at = NOW()
                """
            ),
            {
                "tenant_id": int(tenant_id),
                "provider_id": int(provider_id),
                "external_group": group,
                "platform_role": role,
            },
        )

    return provider_id


def upgrade() -> None:
    conn = op.get_bind()
    _ensure_base_identity_schema(conn)

    if not _column_exists(conn, "app_identity_providers", "is_default"):
        op.add_column(
            "app_identity_providers",
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
    if not _column_exists(conn, "app_identity_providers", "priority"):
        op.add_column(
            "app_identity_providers",
            sa.Column("priority", sa.Integer(), nullable=False, server_default=sa.text("100")),
        )
    if not _column_exists(conn, "app_identity_providers", "allow_local_login"):
        op.add_column(
            "app_identity_providers",
            sa.Column("allow_local_login", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        )
    if not _column_exists(conn, "app_identity_providers", "allow_external_login"):
        op.add_column(
            "app_identity_providers",
            sa.Column("allow_external_login", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        )
    if not _column_exists(conn, "app_identity_providers", "login_hint"):
        op.add_column(
            "app_identity_providers",
            sa.Column("login_hint", sa.String(length=256), nullable=False, server_default=sa.text("''")),
        )
    if not _column_exists(conn, "app_identity_providers", "auto_provision"):
        op.add_column(
            "app_identity_providers",
            sa.Column("auto_provision", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        )
    if not _column_exists(conn, "app_identity_providers", "require_mapping"):
        op.add_column(
            "app_identity_providers",
            sa.Column("require_mapping", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        )

    legacy_by_tenant = _collect_legacy_ldap_settings(conn)
    for tenant_id, settings in legacy_by_tenant.items():
        if _provider_exists(conn, int(tenant_id)):
            continue
        _insert_legacy_provider(conn, tenant_id=int(tenant_id), settings=settings)

    if _column_exists(conn, "app_identity_providers", "is_default"):
        op.alter_column("app_identity_providers", "is_default", server_default=None)
    if _column_exists(conn, "app_identity_providers", "priority"):
        op.alter_column("app_identity_providers", "priority", server_default=None)
    if _column_exists(conn, "app_identity_providers", "allow_local_login"):
        op.alter_column("app_identity_providers", "allow_local_login", server_default=None)
    if _column_exists(conn, "app_identity_providers", "allow_external_login"):
        op.alter_column("app_identity_providers", "allow_external_login", server_default=None)
    if _column_exists(conn, "app_identity_providers", "login_hint"):
        op.alter_column("app_identity_providers", "login_hint", server_default=None)
    if _column_exists(conn, "app_identity_providers", "auto_provision"):
        op.alter_column("app_identity_providers", "auto_provision", server_default=None)
    if _column_exists(conn, "app_identity_providers", "require_mapping"):
        op.alter_column("app_identity_providers", "require_mapping", server_default=None)


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            DELETE FROM app_identity_providers
             WHERE config_json ->> :marker = 'true'
            """
        ),
        {"marker": _MIGRATION_MARKER_KEY},
    )

    if _table_exists(conn, "app_identity_providers"):
        op.execute("DROP INDEX IF EXISTS ix_identity_providers_tenant_default_priority")
        if _column_exists(conn, "app_identity_providers", "require_mapping"):
            op.drop_column("app_identity_providers", "require_mapping")
        if _column_exists(conn, "app_identity_providers", "auto_provision"):
            op.drop_column("app_identity_providers", "auto_provision")
        if _column_exists(conn, "app_identity_providers", "login_hint"):
            op.drop_column("app_identity_providers", "login_hint")
        if _column_exists(conn, "app_identity_providers", "allow_external_login"):
            op.drop_column("app_identity_providers", "allow_external_login")
        if _column_exists(conn, "app_identity_providers", "allow_local_login"):
            op.drop_column("app_identity_providers", "allow_local_login")
        if _column_exists(conn, "app_identity_providers", "priority"):
            op.drop_column("app_identity_providers", "priority")
        if _column_exists(conn, "app_identity_providers", "is_default"):
            op.drop_column("app_identity_providers", "is_default")
