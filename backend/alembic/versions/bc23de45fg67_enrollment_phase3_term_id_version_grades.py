"""enrollment phase3: term_id FK, history version, grade fields

Revision ID: bc23de45fg67
Revises: ab12cd34ef56
Create Date: 2026-03-23 16:00:00.000000

Changes
-------
1. Add ``app_enrollments_terms`` — minimal placeholder for academic terms.
   Enrollment references terms via composite FK (tenant_id, term_id).

2. In ``app_enrollments_enrollments``:
   - Drop ``term_key`` (String) column and related indexes.
   - Add ``term_id`` (BigInteger NOT NULL) with composite FK to terms.
   - Add ``grade_code`` (String 32, nullable) — placeholder for Grades module.
   - Add ``grade_points`` (Numeric 5,2, nullable) — placeholder for Grades module.
   - Recreate indexes using ``term_id``.

3. In ``app_enrollments_status_history``:
   - Add ``version`` (BigInteger NOT NULL, server_default=1) — records the
     resulting enrollment version at the time of each transition.
   - Add CHECK constraint ``version >= 1``.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "bc23de45fg67"
down_revision = "ab12cd34ef56"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Create app_enrollments_terms
    # ------------------------------------------------------------------
    op.create_table(
        "app_enrollments_terms",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("term_code", sa.String(length=64), nullable=False),
        sa.Column("term_name", sa.String(length=255), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'active'"),
        ),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.CheckConstraint(
            "status IN ('active', 'inactive', 'archived')",
            name="ck_enrollment_terms_status",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_enrollment_terms_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "term_code", name="ux_enrollment_terms_tenant_code"),
    )
    op.create_index(
        "ix_enrollment_terms_tenant_status",
        "app_enrollments_terms",
        ["tenant_id", "status"],
    )

    # ------------------------------------------------------------------
    # 2. Migrate app_enrollments_enrollments: term_key → term_id
    # ------------------------------------------------------------------

    # 2a. Drop old term_key-based indexes first.
    op.drop_index(
        "ix_enrollments_one_active_triplet",
        table_name="app_enrollments_enrollments",
    )
    op.drop_index(
        "ix_enrollments_tenant_course_term_status",
        table_name="app_enrollments_enrollments",
    )
    op.drop_index(
        "ix_enrollments_tenant_student_term",
        table_name="app_enrollments_enrollments",
    )

    # 2b. Drop term_key column.
    op.drop_column("app_enrollments_enrollments", "term_key")

    # 2c. Add term_id column (NOT NULL — assumes Phase 2 tables are empty in dev;
    #     for a live migration with data, populate term_id before removing nullable).
    op.add_column(
        "app_enrollments_enrollments",
        sa.Column("term_id", sa.BigInteger(), nullable=False),
    )

    # 2d. Add composite FK (tenant_id, term_id) → app_enrollments_terms.
    op.create_foreign_key(
        "fk_enrollments_tenant_term_id",
        "app_enrollments_enrollments",
        "app_enrollments_terms",
        ["tenant_id", "term_id"],
        ["tenant_id", "id"],
        ondelete="RESTRICT",
    )

    # 2e. Add grade placeholder columns.
    op.add_column(
        "app_enrollments_enrollments",
        sa.Column("grade_code", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "app_enrollments_enrollments",
        sa.Column("grade_points", sa.Numeric(5, 2), nullable=True),
    )

    # 2f. Recreate indexes with term_id.
    op.create_index(
        "ix_enrollments_tenant_course_term_status",
        "app_enrollments_enrollments",
        ["tenant_id", "course_id", "term_id", "enrollment_status"],
    )
    op.create_index(
        "ix_enrollments_tenant_student_term",
        "app_enrollments_enrollments",
        ["tenant_id", "student_profile_id", "term_id"],
    )
    op.create_index(
        "ix_enrollments_one_active_triplet",
        "app_enrollments_enrollments",
        ["tenant_id", "student_profile_id", "course_id", "term_id"],
        unique=True,
        postgresql_where=sa.text(
            "enrollment_status IN ('pending', 'enrolled', 'waitlist', 'suspended')"
        ),
    )

    # ------------------------------------------------------------------
    # 3. Add version to app_enrollments_status_history
    # ------------------------------------------------------------------
    op.add_column(
        "app_enrollments_status_history",
        sa.Column(
            "version",
            sa.BigInteger(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )
    op.create_check_constraint(
        "ck_enrollment_status_history_version_positive",
        "app_enrollments_status_history",
        "version >= 1",
    )


def downgrade() -> None:
    # 3. Remove version from status history.
    op.drop_constraint(
        "ck_enrollment_status_history_version_positive",
        "app_enrollments_status_history",
        type_="check",
    )
    op.drop_column("app_enrollments_status_history", "version")

    # 2f. Drop term_id indexes.
    op.drop_index(
        "ix_enrollments_one_active_triplet",
        table_name="app_enrollments_enrollments",
    )
    op.drop_index(
        "ix_enrollments_tenant_student_term",
        table_name="app_enrollments_enrollments",
    )
    op.drop_index(
        "ix_enrollments_tenant_course_term_status",
        table_name="app_enrollments_enrollments",
    )

    # 2e. Drop grade columns.
    op.drop_column("app_enrollments_enrollments", "grade_points")
    op.drop_column("app_enrollments_enrollments", "grade_code")

    # 2d. Drop term FK.
    op.drop_constraint(
        "fk_enrollments_tenant_term_id",
        "app_enrollments_enrollments",
        type_="foreignkey",
    )

    # 2c. Drop term_id column.
    op.drop_column("app_enrollments_enrollments", "term_id")

    # 2b. Restore term_key.
    op.add_column(
        "app_enrollments_enrollments",
        sa.Column("term_key", sa.String(length=64), nullable=False, server_default="UNKNOWN"),
    )
    op.alter_column("app_enrollments_enrollments", "term_key", server_default=None)

    # 2a. Restore old term_key-based indexes.
    op.create_index(
        "ix_enrollments_tenant_student_term",
        "app_enrollments_enrollments",
        ["tenant_id", "student_profile_id", "term_key"],
    )
    op.create_index(
        "ix_enrollments_tenant_course_term_status",
        "app_enrollments_enrollments",
        ["tenant_id", "course_id", "term_key", "enrollment_status"],
    )
    op.create_index(
        "ix_enrollments_one_active_triplet",
        "app_enrollments_enrollments",
        ["tenant_id", "student_profile_id", "course_id", "term_key"],
        unique=True,
        postgresql_where=sa.text(
            "enrollment_status IN ('pending', 'enrolled', 'waitlist', 'suspended')"
        ),
    )

    # 1. Drop terms table.
    op.drop_index("ix_enrollment_terms_tenant_status", table_name="app_enrollments_terms")
    op.drop_table("app_enrollments_terms")
