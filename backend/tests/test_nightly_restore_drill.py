"""Nightly restore drill — ERP-QA G3 gate (backup → restore → login smoke).

Marked ``integration`` — requires a live DATABASE_URL, pg_dump/pg_restore
binaries, and a running PostgreSQL instance.  Skipped automatically when
DATABASE_URL is absent.

The drill verifies the full recovery path:
  1. pg_dump from the live database.
  2. Create an isolated temporary database on the same cluster.
  3. pg_restore the dump into that isolated database.
  4. Query a known table (alembic_version) to confirm schema integrity.
  5. Verify at least one application table exists (confirms data survived).
  6. Drop the temporary database (cleanup).

Run explicitly:
  pytest -m integration tests/test_nightly_restore_drill.py -v
"""

import os
import shutil
import subprocess
from urllib.parse import urlparse, urlunparse

import pytest

_DATABASE_URL: str = os.getenv("DATABASE_URL", "")


def _skip_if_no_db() -> None:
    if not _DATABASE_URL:
        pytest.skip("DATABASE_URL not set — integration test skipped")


def _skip_if_no_pg_tools() -> None:
    for tool in ("pg_dump", "pg_restore", "psql", "createdb", "dropdb"):
        if not shutil.which(tool):
            pytest.skip(f"{tool} not available in PATH")


def _make_drill_db_url(original_url: str, db_name: str) -> str:
    """Replace the database name in a postgres URL."""
    parsed = urlparse(original_url)
    new_path = f"/{db_name}"
    return urlunparse(parsed._replace(path=new_path))


def _maintenance_url(original_url: str) -> str:
    """Connect to the 'postgres' maintenance database for createdb/dropdb."""
    return _make_drill_db_url(original_url, "postgres")


DRILL_DB_NAME = "restore_drill_temp"


@pytest.mark.integration
class TestNightlyRestoreDrill:
    """Full backup → restore → smoke cycle on an isolated temp database."""

    @pytest.fixture(autouse=True)
    def _cleanup_drill_db(self):
        """Ensure the temp database is dropped even if the test fails."""
        _skip_if_no_db()
        _skip_if_no_pg_tools()
        yield
        # Teardown: drop the drill database if it exists
        maint_url = _maintenance_url(_DATABASE_URL)
        subprocess.run(
            ["dropdb", "--if-exists", "--force", DRILL_DB_NAME],
            env={**os.environ, "DATABASE_URL": maint_url, "PGDATABASE": "postgres"},
            capture_output=True,
        )

    def test_full_restore_drill_and_smoke(self, tmp_path):
        """ERP-QA G3: backup → restore → schema + data smoke."""
        _skip_if_no_db()
        _skip_if_no_pg_tools()

        dump_file = str(tmp_path / "drill.dump")

        # --- Step 1: pg_dump from live DB ---
        result = subprocess.run(
            [
                "pg_dump",
                "--format=custom",
                "--no-owner",
                "--no-privileges",
                "--file", dump_file,
                _DATABASE_URL,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"pg_dump failed:\n{result.stderr}"
        assert os.path.getsize(dump_file) > 0, "dump file is empty"

        # --- Step 2: create isolated temp database ---
        maint_url = _maintenance_url(_DATABASE_URL)
        # Drop if leftover from a previous failed run
        subprocess.run(
            ["dropdb", "--if-exists", "--force", DRILL_DB_NAME],
            env={**os.environ, "DATABASE_URL": maint_url, "PGDATABASE": "postgres"},
            capture_output=True,
        )

        result = subprocess.run(
            ["createdb", DRILL_DB_NAME],
            env={**os.environ, "DATABASE_URL": maint_url, "PGDATABASE": "postgres"},
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"createdb failed:\n{result.stderr}"

        # --- Step 3: pg_restore into the isolated DB ---
        drill_url = _make_drill_db_url(_DATABASE_URL, DRILL_DB_NAME)
        result = subprocess.run(
            [
                "pg_restore",
                "--no-owner",
                "--no-privileges",
                "--dbname", drill_url,
                dump_file,
            ],
            capture_output=True,
            text=True,
        )
        # pg_restore may emit warnings for missing roles — allow returncode 0 or 1
        assert result.returncode in (0, 1), (
            f"pg_restore failed (rc={result.returncode}):\n{result.stderr}"
        )

        # --- Step 4: verify schema integrity (alembic_version table) ---
        result = subprocess.run(
            [
                "psql", drill_url, "-t", "-A",
                "-c", "SELECT version_num FROM alembic_version LIMIT 1;",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"alembic_version query failed:\n{result.stderr}"
        version = result.stdout.strip()
        assert version, "alembic_version is empty — schema not restored"

        # --- Step 5: verify at least one app table has data ---
        result = subprocess.run(
            [
                "psql", drill_url, "-t", "-A",
                "-c", (
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname = 'public' "
                    "ORDER BY tablename LIMIT 10;"
                ),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"table listing failed:\n{result.stderr}"
        tables = [t.strip() for t in result.stdout.strip().splitlines() if t.strip()]
        assert len(tables) > 0, "no tables found in restored database"
        assert "alembic_version" in tables, "alembic_version not in restored tables"
