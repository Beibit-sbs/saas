"""add app_local_users table and migrate from JSON blob

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-04-11 01:00:00.000000

"""

from __future__ import annotations

from alembic import op

revision = "d2e3f4a5b6c7"
down_revision = "a0b1c2d3e4f5"
branch_labels = None
depends_on = None

_LOCAL_USERS_KEY = "auth.local_users_json"


def upgrade() -> None:
    op.execute(
        """
        CREATE SEQUENCE IF NOT EXISTS app_local_users_id_seq START 1
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app_local_users (
            user_id         TEXT        PRIMARY KEY
                                        DEFAULT 'local.' || LPAD(nextval('app_local_users_id_seq')::TEXT, 3, '0'),
            tenant_id       BIGINT      NOT NULL CHECK (tenant_id > 0),
            login           TEXT        NOT NULL,
            password_hash   TEXT        NOT NULL DEFAULT '',
            display_name    TEXT        NOT NULL DEFAULT '',
            roles           JSONB       NOT NULL DEFAULT '["student"]'::jsonb,
            default_language TEXT       NOT NULL DEFAULT 'ru',
            email           TEXT,
            account_scope   TEXT,
            is_platform_user BOOLEAN    NOT NULL DEFAULT FALSE,
            force_password_change BOOLEAN NOT NULL DEFAULT FALSE,
            auth_source     TEXT        NOT NULL DEFAULT 'local',
            status          TEXT        NOT NULL DEFAULT 'active',
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CHECK (length(trim(user_id)) > 0),
            CHECK (length(trim(login)) > 0)
        )
        """
    )

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_app_local_users_login
        ON app_local_users (login)
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_app_local_users_tenant
        ON app_local_users (tenant_id)
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_app_local_users_tenant_login
        ON app_local_users (tenant_id, login)
        """
    )

    # Data migration: move existing users from JSON blob to proper rows.
    # Uses a PL/pgSQL block so it is a no-op when the settings table is absent
    # or the key does not exist.
    op.execute(
        f"""
        DO $$
        DECLARE
            _raw    TEXT;
            _blob   JSONB;
            _user   JSONB;
            _max_id BIGINT := 0;
            _suffix BIGINT;
        BEGIN
            IF to_regclass('public.app_integration_settings') IS NULL THEN
                RETURN;
            END IF;

            SELECT value INTO _raw
            FROM app_integration_settings
            WHERE key = '{_LOCAL_USERS_KEY}';

            IF _raw IS NULL THEN
                RETURN;
            END IF;

            BEGIN
                _blob := _raw::jsonb;
            EXCEPTION WHEN others THEN
                RETURN;
            END;

            FOR _user IN SELECT * FROM jsonb_array_elements(_blob -> 'users')
            LOOP
                -- Skip rows without tenant_id (legacy guard)
                CONTINUE WHEN _user ->> 'tenant_id' IS NULL;

                INSERT INTO app_local_users (
                    user_id,
                    tenant_id,
                    login,
                    password_hash,
                    display_name,
                    roles,
                    default_language,
                    email,
                    account_scope,
                    is_platform_user,
                    force_password_change,
                    auth_source,
                    status
                ) VALUES (
                    _user ->> 'user_id',
                    (_user ->> 'tenant_id')::BIGINT,
                    lower(trim(_user ->> 'login')),
                    coalesce(_user ->> 'password_hash', _user ->> 'password', ''),
                    coalesce(trim(_user ->> 'display_name'), ''),
                    coalesce(_user -> 'roles', '["student"]'::jsonb),
                    coalesce(_user ->> 'default_language', 'ru'),
                    nullif(trim(coalesce(_user ->> 'email', '')), ''),
                    nullif(trim(coalesce(_user ->> 'account_scope', '')), ''),
                    coalesce((_user ->> 'is_platform_user')::BOOLEAN, FALSE),
                    coalesce((_user ->> 'force_password_change')::BOOLEAN, FALSE),
                    coalesce(_user ->> 'auth_source', 'local'),
                    'active'
                )
                ON CONFLICT (user_id) DO NOTHING;

                -- Track max numeric suffix to sync the sequence
                IF (_user ->> 'user_id') LIKE 'local.%' THEN
                    BEGIN
                        _suffix := (substring(_user ->> 'user_id' FROM 7))::BIGINT;
                        IF _suffix > _max_id THEN
                            _max_id := _suffix;
                        END IF;
                    EXCEPTION WHEN others THEN
                        -- non-numeric suffix — skip
                    END;
                END IF;
            END LOOP;

            -- Advance sequence to be at least as high as migrated data
            IF _max_id > 0 THEN
                PERFORM setval('app_local_users_id_seq', _max_id, TRUE);
            END IF;

            -- Remove the JSON blob now that data is in proper rows
            DELETE FROM app_integration_settings WHERE key = '{_LOCAL_USERS_KEY}';
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS app_local_users")
    op.execute("DROP SEQUENCE IF EXISTS app_local_users_id_seq")
