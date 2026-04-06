from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class OrgUnitType(str, Enum):
    UNIVERSITY = "university"
    SCHOOL = "school"
    FACULTY = "faculty"
    DEPARTMENT = "department"
    UMO = "umo"
    REGISTRAR_OFFICE = "registrar_office"
    DEANS_OFFICE = "deans_office"
    ADVISORY_UNIT = "advisory_unit"
    ACADEMIC_COMMITTEE = "academic_committee"
    ACADEMIC_COMMISSION = "academic_commission"


org_unit_type_enum = SAEnum(
    OrgUnitType,
    name="org_unit_type",
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
    validate_strings=True,
)


class OrgUnitModel(Base):
    __tablename__ = "app_org_org_units"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    unit_type: Mapped[OrgUnitType] = mapped_column(org_unit_type_enum, nullable=False)
    parent_unit_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    head_person_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "parent_unit_id"],
            ["app_org_org_units.tenant_id", "app_org_org_units.id"],
            name="fk_org_units_parent",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "code", name="ux_org_org_units_tenant_code"),
        UniqueConstraint("tenant_id", "id", name="ux_org_org_units_tenant_id_id"),
        CheckConstraint(
            "parent_unit_id IS NULL OR parent_unit_id != id",
            name="ck_org_org_units_no_self_parent",
        ),
        Index("ix_org_org_units_tenant_type", "tenant_id", "unit_type"),
        Index("ix_org_org_units_tenant_parent", "tenant_id", "parent_unit_id"),
        Index("ix_org_org_units_tenant_active", "tenant_id", "active"),
    )
