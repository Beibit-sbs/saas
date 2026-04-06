from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PersonModel(Base):
    __tablename__ = "app_profiles_people"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    external_person_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="active",
        server_default=text("'active'"),
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    version: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_profiles_people_tenant_id_id"),
        UniqueConstraint("tenant_id", "email", name="ux_profiles_people_tenant_email"),
        Index(
            "ux_profiles_people_tenant_external_person_key",
            "tenant_id",
            "external_person_key",
            unique=True,
            postgresql_where=text("external_person_key IS NOT NULL"),
        ),
        Index("ix_profiles_people_tenant_email", "tenant_id", "email"),
        Index("ix_profiles_people_tenant_status", "tenant_id", "status"),
    )


class DepartmentModel(Base):
    __tablename__ = "app_profiles_departments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="department",
        server_default=text("'department'"),
    )
    parent_department_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    head_person_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="active",
        server_default=text("'active'"),
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    version: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_profiles_departments_tenant_id_id"),
        UniqueConstraint("tenant_id", "code", name="ux_profiles_departments_tenant_code"),
        ForeignKeyConstraint(
            ["tenant_id", "parent_department_id"],
            ["app_profiles_departments.tenant_id", "app_profiles_departments.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "head_person_id"],
            ["app_profiles_people.tenant_id", "app_profiles_people.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_profiles_departments_tenant_name", "tenant_id", "name"),
        Index("ix_profiles_departments_tenant_parent", "tenant_id", "parent_department_id"),
        Index("ix_profiles_departments_tenant_type", "tenant_id", "unit_type"),
        Index("ix_profiles_departments_tenant_head", "tenant_id", "head_person_id"),
        Index("ix_profiles_departments_tenant_status", "tenant_id", "status"),
    )


class ProgramModel(Base):
    __tablename__ = "app_profiles_programs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    degree_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="active",
        server_default=text("'active'"),
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    version: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_profiles_programs_tenant_id_id"),
        UniqueConstraint("tenant_id", "code", name="ux_profiles_programs_tenant_code"),
        ForeignKeyConstraint(
            ["tenant_id", "department_id"],
            ["app_profiles_departments.tenant_id", "app_profiles_departments.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_profiles_programs_tenant_department", "tenant_id", "department_id"),
        Index("ix_profiles_programs_tenant_degree_type", "tenant_id", "degree_type"),
        Index("ix_profiles_programs_tenant_status", "tenant_id", "status"),
    )


class StudentModel(Base):
    __tablename__ = "app_profiles_students"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    person_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    program_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    student_number: Mapped[str] = mapped_column(String(64), nullable=False)
    cohort_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    status: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="active",
        server_default=text("'active'"),
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    version: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_profiles_students_tenant_id_id"),
        UniqueConstraint("tenant_id", "person_id", name="ux_profiles_students_tenant_person"),
        UniqueConstraint(
            "tenant_id",
            "student_number",
            name="ux_profiles_students_tenant_student_number",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "person_id"],
            ["app_profiles_people.tenant_id", "app_profiles_people.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "program_id"],
            ["app_profiles_programs.tenant_id", "app_profiles_programs.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_profiles_students_tenant_program", "tenant_id", "program_id"),
        Index("ix_profiles_students_tenant_status", "tenant_id", "status"),
        Index("ix_profiles_students_tenant_cohort", "tenant_id", "cohort_year"),
    )


class FacultyModel(Base):
    __tablename__ = "app_profiles_faculty"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    person_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    department_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    faculty_number: Mapped[str] = mapped_column(String(64), nullable=False)
    academic_title: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="active",
        server_default=text("'active'"),
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    version: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_profiles_faculty_tenant_id_id"),
        UniqueConstraint("tenant_id", "person_id", name="ux_profiles_faculty_tenant_person"),
        UniqueConstraint(
            "tenant_id",
            "faculty_number",
            name="ux_profiles_faculty_tenant_faculty_number",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "person_id"],
            ["app_profiles_people.tenant_id", "app_profiles_people.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "department_id"],
            ["app_profiles_departments.tenant_id", "app_profiles_departments.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_profiles_faculty_tenant_department", "tenant_id", "department_id"),
        Index("ix_profiles_faculty_tenant_status", "tenant_id", "status"),
    )