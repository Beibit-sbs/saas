from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class BillingSubscriptionStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class BillingPlanModel(Base):
    __tablename__ = "app_billing_plans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    features: Mapped[dict[str, bool]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    limits: Mapped[dict[str, int]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class BillingTenantSubscriptionModel(Base):
    __tablename__ = "app_billing_tenant_subscriptions"

    tenant_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    plan_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app_billing_plans.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_plan_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("app_billing_plans.id", ondelete="SET NULL"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        Index("ix_app_billing_tenant_subscriptions_plan_id", "plan_id"),
        Index("ix_app_billing_tenant_subscriptions_status", "status"),
    )


class BillingUsageCounterModel(Base):
    __tablename__ = "app_billing_usage_counters"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    metric: Mapped[str] = mapped_column(String(64), nullable=False)
    period_key: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        Index("ix_app_billing_usage_counters_tenant_metric_period", "tenant_id", "metric", "period_key", unique=True),
    )


class BillingInvoiceModel(Base):
    __tablename__ = "app_billing_invoices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    period_key: Mapped[str] = mapped_column(String(32), nullable=False)
    plan_code: Mapped[str] = mapped_column(String(64), nullable=False)
    base_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    usage_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, server_default=text("'USD'"))
    breakdown: Mapped[dict[str, int]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        Index("ix_app_billing_invoices_tenant_period", "tenant_id", "period_key", unique=True),
    )
