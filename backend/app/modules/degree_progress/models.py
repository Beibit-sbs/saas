from __future__ import annotations

from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ProgramRequirementModel(Base):
    __tablename__ = "app_degree_progress_requirements"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    program_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    minimum_credits: Mapped[int] = mapped_column(BigInteger, nullable=False)
    minimum_gpa: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_degree_requirements_tenant_id_id"),
        UniqueConstraint("tenant_id", "program_id", "name", name="ux_degree_requirements_program_name"),
        CheckConstraint("minimum_credits >= 0", name="ck_degree_requirements_minimum_credits_non_negative"),
        CheckConstraint("minimum_gpa >= 0", name="ck_degree_requirements_minimum_gpa_non_negative"),
        Index("ix_degree_requirements_tenant_program_active", "tenant_id", "program_id", "is_active"),
    )


class ProgramRequirementItemModel(Base):
    __tablename__ = "app_degree_progress_requirement_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    requirement_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    credits: Mapped[int] = mapped_column(BigInteger, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_degree_requirement_items_tenant_id_id"),
        UniqueConstraint(
            "tenant_id",
            "requirement_id",
            "course_id",
            name="ux_degree_requirement_items_unique_course",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "requirement_id"],
            ["app_degree_progress_requirements.tenant_id", "app_degree_progress_requirements.id"],
            ondelete="CASCADE",
            name="fk_degree_requirement_items_requirement",
        ),
        CheckConstraint("credits >= 0", name="ck_degree_requirement_items_credits_non_negative"),
        Index("ix_degree_requirement_items_tenant_requirement", "tenant_id", "requirement_id"),
    )
