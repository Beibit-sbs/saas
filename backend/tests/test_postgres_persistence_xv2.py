"""XV2: PostgreSQL Persistence Verification
Tests that data written directly to PostgreSQL is durable and visible across connections.
Uses raw SQLAlchemy (not the service layer) to isolate storage behavior.
"""
import os

import pytest
from sqlalchemy import text

from app.core.db import build_engine


@pytest.fixture(scope="module")
def pg_engine(original_database_url):
    """Create a direct SQLAlchemy engine to the PostgreSQL DB.

    Depends on the session-scoped ``original_database_url`` fixture (defined in
    conftest.py) which captures DATABASE_URL at conftest import time — before
    any autouse ``reset_shared_state`` teardown can pop it.  This makes the
    fixture reliable in both narrow (isolated) and full-suite pytest runs.
    """
    if not original_database_url:
        pytest.skip("DATABASE_URL is not configured for DB integration checks")

    # Restore DATABASE_URL so build_engine() can read it (reset_shared_state
    # intentionally pops it for in-memory test isolation).
    os.environ["DATABASE_URL"] = original_database_url
    engine = build_engine()
    yield engine
    engine.dispose()


class TestPostgresMigrations:
    """Verify that all Alembic migrations have been applied."""

    def test_alembic_version_table_exists(self, pg_engine):
        """alembic_version table must exist — proves migrations ran."""
        with pg_engine.connect() as conn:
            result = conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_name='alembic_version'")
            )
            rows = result.fetchall()
        assert len(rows) == 1, "alembic_version table must exist"

    def test_migration_head_applied(self, pg_engine):
        """At least one migration revision must be recorded."""
        with pg_engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            rows = result.fetchall()
        assert len(rows) >= 1, "At least one Alembic revision must be applied"
        version = rows[0][0]
        assert version, f"version_num must not be empty, got: {version!r}"
        print(f"\n[XV2] Alembic head: {version}")

    def test_university_students_table_exists(self, pg_engine):
        """Core domain table 'university_students' must exist."""
        with pg_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name='university_students'"
                )
            )
            rows = result.fetchall()
        assert len(rows) == 1, "university_students table must exist in PostgreSQL"

    def test_minimum_tables_count(self, pg_engine):
        """At least 50 public tables must exist (full schema deployed)."""
        with pg_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_type='BASE TABLE'"
                )
            )
            count = result.scalar()
        assert count >= 50, f"Expected >= 50 tables, got {count}"
        print(f"\n[XV2] Total tables: {count}")


class TestPostgresCRUD:
    """Verify basic CRUD operations persist data directly in PostgreSQL."""

    TABLE = "university_students"
    TENANT_ID = "1"

    def test_insert_student_persists(self, pg_engine):
        """Direct INSERT must be readable back from PostgreSQL."""
        student_key = "xv2-persist-test-001"
        # cleanup any leftover from prior run
        with pg_engine.begin() as conn:
            conn.execute(
                text(f"DELETE FROM {self.TABLE} WHERE student_id = :s AND tenant_id = :t"),
                {"s": student_key, "t": self.TENANT_ID},
            )

        # INSERT directly via SQLAlchemy
        with pg_engine.begin() as conn:
            conn.execute(
                text(
                    f"INSERT INTO {self.TABLE} (student_id, first_name, last_name, email, status, tenant_id, created_at) "
                    "VALUES (:s, 'XV2', 'PersistTest', 'xv2persist@university.edu', 'active', :t, NOW())"
                ),
                {"s": student_key, "t": self.TENANT_ID},
            )

        # read back in a separate connection
        with pg_engine.connect() as conn:
            result = conn.execute(
                text(
                    f"SELECT student_id, first_name, last_name, email, status, tenant_id "
                    f"FROM {self.TABLE} WHERE student_id = :s AND tenant_id = :t"
                ),
                {"s": student_key, "t": self.TENANT_ID},
            )
            row = result.fetchone()

        assert row is not None, "Inserted row must be readable from PostgreSQL"
        assert row[0] == student_key
        assert row[1] == "XV2"
        assert row[2] == "PersistTest"
        assert row[3] == "xv2persist@university.edu"
        assert row[4] == "active"
        assert row[5] == self.TENANT_ID
        print(f"\n[XV2] CREATE: row persisted and read back: {row}")

    def test_update_student_persists(self, pg_engine):
        """Direct UPDATE must be reflected in a subsequent independent read."""
        student_key = "xv2-persist-test-001"

        with pg_engine.begin() as conn:
            conn.execute(
                text(
                    f"UPDATE {self.TABLE} SET last_name = 'UpdatedTest' "
                    "WHERE student_id = :s AND tenant_id = :t"
                ),
                {"s": student_key, "t": self.TENANT_ID},
            )

        with pg_engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT last_name FROM {self.TABLE} WHERE student_id = :s AND tenant_id = :t"),
                {"s": student_key, "t": self.TENANT_ID},
            )
            row = result.fetchone()

        assert row is not None, "Row must still exist after update"
        assert row[0] == "UpdatedTest", f"Expected 'UpdatedTest', got {row[0]!r}"
        print(f"\n[XV2] UPDATE: persisted correctly")

    def test_delete_student_removes_row(self, pg_engine):
        """Direct DELETE must remove the row from PostgreSQL permanently."""
        student_key = "xv2-persist-test-001"

        with pg_engine.begin() as conn:
            conn.execute(
                text(f"DELETE FROM {self.TABLE} WHERE student_id = :s AND tenant_id = :t"),
                {"s": student_key, "t": self.TENANT_ID},
            )

        with pg_engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT COUNT(*) FROM {self.TABLE} WHERE student_id = :s AND tenant_id = :t"),
                {"s": student_key, "t": self.TENANT_ID},
            )
            count = result.scalar()

        assert count == 0, f"Deleted row must not exist in PostgreSQL, found {count}"
        print(f"\n[XV2] DELETE: row removed successfully")


class TestPostgresTransactionIsolation:
    """Verify that uncommitted data is not visible to other connections."""

    def test_uncommitted_not_visible(self, pg_engine):
        """Data in an open (not committed) transaction should not leak to other sessions."""
        student_key = "xv2-isolation-test-001"
        conn1 = pg_engine.connect()
        conn2 = pg_engine.connect()

        try:
            conn2.execute(
                text("DELETE FROM university_students WHERE student_id = :student_id AND tenant_id = :tenant_id"),
                {"student_id": student_key, "tenant_id": str(TestPostgresCRUD.TENANT_ID)},
            )
            conn2.commit()

            # Begin transaction on conn1, insert row, do NOT commit
            tx = conn1.begin()
            conn1.execute(
                text(
                    "INSERT INTO university_students (student_id, first_name, last_name, email, status, tenant_id, created_at) "
                    "VALUES (:student_id, 'ISO', 'TEST', 'iso@test.edu', 'active', :tenant_id, NOW())"
                ),
                {"student_id": student_key, "tenant_id": str(TestPostgresCRUD.TENANT_ID)},
            )

            # conn2 should NOT see the uncommitted row
            result = conn2.execute(
                text("SELECT COUNT(*) FROM university_students WHERE student_id = :student_id AND tenant_id = :tenant_id"),
                {"student_id": student_key, "tenant_id": str(TestPostgresCRUD.TENANT_ID)},
            )
            count = result.scalar()
            assert count == 0, f"Uncommitted data must not be visible: found {count} rows"

            tx.rollback()

            conn2.execute(
                text("DELETE FROM university_students WHERE student_id = :student_id AND tenant_id = :tenant_id"),
                {"student_id": student_key, "tenant_id": str(TestPostgresCRUD.TENANT_ID)},
            )
            conn2.commit()
            print(f"\n[XV2] Isolation: uncommitted data correctly invisible")
        finally:
            conn1.close()
            conn2.close()
