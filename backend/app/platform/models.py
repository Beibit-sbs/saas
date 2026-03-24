from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PlatformTenantSettingsModel(Base):
    __tablename__ = "app_platform_tenant_settings"

    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        primary_key=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    settings_json: Mapped[dict] = mapped_column(postgresql.JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    quotas_json: Mapped[dict] = mapped_column(postgresql.JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    limits_json: Mapped[dict] = mapped_column(postgresql.JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class PlatformFeatureFlagModel(Base):
    __tablename__ = "app_platform_feature_flags"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=True)
    scope: Mapped[str] = mapped_column(String(32), nullable=False, default="platform")
    module: Mapped[str] = mapped_column(String(128), nullable=False)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class PlatformPlanModel(Base):
    __tablename__ = "app_platform_plans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    features_json: Mapped[dict] = mapped_column(postgresql.JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    limits_json: Mapped[dict] = mapped_column(postgresql.JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class PlatformSubscriptionModel(Base):
    __tablename__ = "app_platform_subscriptions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False)
    plan_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app_platform_plans.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    started_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    ends_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PlatformUsageCounterModel(Base):
    __tablename__ = "app_platform_usage_counters"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False)
    metric: Mapped[str] = mapped_column(String(128), nullable=False)
    period_key: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class PlatformJobModel(Base):
    __tablename__ = "app_platform_jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False)
    job_type: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    payload_json: Mapped[dict] = mapped_column(postgresql.JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    result_json: Mapped[dict | None] = mapped_column(postgresql.JSONB, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class PlatformNotificationModel(Base):
    __tablename__ = "app_platform_notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    target: Mapped[str] = mapped_column(String(512), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload_json: Mapped[dict] = mapped_column(postgresql.JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
