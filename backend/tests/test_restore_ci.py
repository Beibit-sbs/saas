"""CI backup/restore integration test (P2-4).

Marked `integration` — requires a live DATABASE_URL and pg_dump/pg_restore
binaries.  Skipped automatically in the no-DB unit-test environment.

What it covers:
  1. A real pg_dump is taken from the live database.
  2. The produced dump file is validated as readable by pg_restore --list.
  3. The backup service helper _run_pg_restore_command succeeds in dry-run
     mode (pg_restore --list only — no actual data loaded).

Run explicitly:
  pytest -m integration tests/test_restore_ci.py -v
"""

import os
import shutil
import subprocess

import pytest

from app.modules.backup import service as backup_service

# Capture DATABASE_URL at import time — conftest.py autouse fixture removes it
# from os.environ before each test to keep the suite deterministic.
_DATABASE_URL: str = os.getenv("DATABASE_URL", "")


def _skip_if_no_db() -> None:
    if not _DATABASE_URL:
        pytest.skip("DATABASE_URL not set — integration test skipped")


def _skip_if_no_pg_tools() -> None:
    if not shutil.which("pg_dump"):
        pytest.skip("pg_dump not available in PATH")
    if not shutil.which("pg_restore"):
        pytest.skip("pg_restore not available in PATH")


@pytest.mark.integration
def test_backup_dump_is_restorable(tmp_path: pytest.TempPathFactory) -> None:
    """Backup from live DB must be readable by pg_restore --list."""
    _skip_if_no_db()
    _skip_if_no_pg_tools()

    db_url = _DATABASE_URL
    dump_file = tmp_path / "ci_restore_check.dump"

    # Step 1: create a real dump using the production backup helper.
    backup_service._run_pg_dump_command(db_url, str(dump_file))

    assert dump_file.exists(), "pg_dump produced no output file"
    assert dump_file.stat().st_size > 0, "pg_dump output is empty"

    # Step 2: verify the dump is structurally valid (pg_restore --list does not
    # restore anything — it only reads the table of contents).
    result = subprocess.run(
        ["pg_restore", "--list", str(dump_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"pg_restore --list failed:\n{result.stderr}\n{result.stdout}"
    )

    toc_lines = [ln for ln in result.stdout.splitlines() if ln.strip() and not ln.startswith(";")]
    assert len(toc_lines) > 0, "pg_restore --list returned an empty table of contents"


@pytest.mark.integration
def test_restore_script_dry_run(tmp_path: pytest.TempPathFactory) -> None:
    """The top-level restore_db.sh must validate a real dump in safe mode."""
    _skip_if_no_db()
    _skip_if_no_pg_tools()

    from pathlib import Path

    db_url = _DATABASE_URL
    dump_file = tmp_path / "ci_dry_run_check.dump"
    backup_service._run_pg_dump_command(db_url, str(dump_file))

    # Locate restore_db.sh — PROJECT_ROOT is set in backend-tests container.
    # Fall back to a sibling traversal for local runs.
    project_root_env = os.environ.get("PROJECT_ROOT", "")
    if project_root_env:
        restore_script = Path(project_root_env) / "scripts" / "restore_db.sh"
    else:
        restore_script = Path(__file__).resolve().parent
        while restore_script.parent != restore_script:
            candidate = restore_script / "scripts" / "restore_db.sh"
            if candidate.exists():
                restore_script = candidate
                break
            restore_script = restore_script.parent
        else:
            pytest.skip("restore_db.sh not found — repo not mounted")

    if not restore_script.exists():
        pytest.skip(f"restore_db.sh not found at {restore_script}")

    result = subprocess.run(
        ["bash", str(restore_script), "--database-url", db_url, str(dump_file)],
        capture_output=True,
        text=True,
        env={**os.environ, "DATABASE_URL": db_url},
    )
    # Dry-run (no --execute) should exit 0 and print confirmation message.
    assert result.returncode == 0, (
        f"restore_db.sh dry-run failed:\n{result.stderr}\n{result.stdout}"
    )
    assert "safe mode" in result.stdout.lower() or "restore not executed" in result.stdout.lower(), (
        f"Expected dry-run message, got:\n{result.stdout}"
    )


@pytest.mark.integration
def test_restore_requires_confirm_flag(tmp_path: pytest.TempPathFactory) -> None:
    """restore_db.sh with --execute but without --confirm RESTORE must fail."""
    _skip_if_no_db()
    _skip_if_no_pg_tools()

    from pathlib import Path

    db_url = _DATABASE_URL
    dump_file = tmp_path / "ci_confirm_check.dump"
    backup_service._run_pg_dump_command(db_url, str(dump_file))

    project_root_env = os.environ.get("PROJECT_ROOT", "")
    if project_root_env:
        restore_script = Path(project_root_env) / "scripts" / "restore_db.sh"
    else:
        restore_script = Path(__file__).resolve().parent
        while restore_script.parent != restore_script:
            candidate = restore_script / "scripts" / "restore_db.sh"
            if candidate.exists():
                restore_script = candidate
                break
            restore_script = restore_script.parent
        else:
            pytest.skip("restore_db.sh not found — repo not mounted")

    if not restore_script.exists():
        pytest.skip(f"restore_db.sh not found at {restore_script}")

    result = subprocess.run(
        ["bash", str(restore_script), "--database-url", db_url, "--execute", str(dump_file)],
        capture_output=True,
        text=True,
        env={**os.environ, "DATABASE_URL": db_url},
    )
    assert result.returncode != 0, (
        "restore_db.sh should fail when --confirm RESTORE is missing"
    )
