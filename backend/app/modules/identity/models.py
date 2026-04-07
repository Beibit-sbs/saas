from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class IdentityProvider(Base):
    __tablename__ = "app_identity_providers"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_identity_providers_tenant_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    priority: Mapped[int] = mapped_column(nullable=False, default=100)
    allow_local_login: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allow_external_login: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    login_hint: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    auto_provision: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    require_mapping: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class IdentityProviderSecret(Base):
    __tablename__ = "app_identity_provider_secrets"
    __table_args__ = (UniqueConstraint("provider_id", "tenant_id", name="uq_identity_provider_secrets_provider_tenant"),)

    provider_id: Mapped[int] = mapped_column(
        ForeignKey("app_identity_providers.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tenant_id: Mapped[int] = mapped_column(ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False)
    bind_password_enc: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ExternalIdentity(Base):
    __tablename__ = "app_external_identities"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "provider_id",
            "external_user_id",
            name="uq_external_identities_tenant_provider_external",
        ),
        UniqueConstraint(
            "tenant_id",
            "provider_id",
            "local_user_id",
            name="uq_external_identities_tenant_provider_local",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False)
    provider_id: Mapped[int] = mapped_column(ForeignKey("app_identity_providers.id", ondelete="CASCADE"), nullable=False)
    local_user_id: Mapped[str] = mapped_column(String(128), nullable=False)
    external_user_id: Mapped[str] = mapped_column(String(512), nullable=False)
    username: Mapped[str | None] = mapped_column(String(256), nullable=True)
    email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class IdentityMapping(Base):
    __tablename__ = "app_identity_mappings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "provider_id", "external_group", name="uq_identity_mappings_group"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False)
    provider_id: Mapped[int] = mapped_column(ForeignKey("app_identity_providers.id", ondelete="CASCADE"), nullable=False)
    external_group: Mapped[str] = mapped_column(String(512), nullable=False)
    platform_role: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
