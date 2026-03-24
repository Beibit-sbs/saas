#!/usr/bin/env bash
set -euo pipefail

# Pre-release validation gate for backend, tenant safety, migrations, and frontend checks.
#
# Usage:
#   bash scripts/release_check.sh
#
# Optional env vars:
#   DATABASE_URL  — required only for the migration smoke step.
#                   Accepts both postgresql:// and postgresql+psycopg:// formats;
#                   Alembic normalises the URL internally.
#                   Example: postgresql://postgres:postgres@127.0.0.1:5432/platform_ci
#   JWT_SECRET    — overrides the test-only JWT secret (default is safe for local runs only)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"
VENV_PYTHON="${BACKEND_DIR}/.venv/bin/python3"
VENV_ALEMBIC="${BACKEND_DIR}/.venv/bin/alembic"

JWT_SECRET="${JWT_SECRET:-test-suite-secret-not-for-prod-1234567890}"
export JWT_SECRET

# ---------------------------------------------------------------------------
# Guard: ensure the backend virtualenv is present and usable.
# ---------------------------------------------------------------------------
check_venv() {
  if [[ ! -x "${VENV_PYTHON}" ]]; then
    echo "[release-check] ERROR: backend virtualenv not found at ${VENV_PYTHON}"
    echo "[release-check] Run: cd backend && python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'"
    exit 1
  fi
}

# ---------------------------------------------------------------------------
# Backend unit/in-memory gates.
# DATABASE_URL is explicitly unset so that db_available() returns False and
# all platform repositories use their in-memory stores, matching the intent
# of tests/conftest.py.  Any pre-existing DATABASE_URL in the shell
# (e.g. postgresql+psycopg://...) must not leak into these test runs.
# ---------------------------------------------------------------------------
run_backend_checks() {
  echo "[release-check] backend: tenant safety gate"
  (
    cd "${BACKEND_DIR}"
    env -u DATABASE_URL "${VENV_PYTHON}" -m pytest -q \
      tests/platform/test_platform_tenant_safety_audit_v1.py
  )

  echo "[release-check] backend: platform regression gate"
  (
    cd "${BACKEND_DIR}"
    env -u DATABASE_URL "${VENV_PYTHON}" -m pytest -q tests/platform/
  )

  echo "[release-check] backend: critical security regression"
  (
    cd "${BACKEND_DIR}"
    env -u DATABASE_URL "${VENV_PYTHON}" -m pytest -q -m security_regression
  )
}

# ---------------------------------------------------------------------------
# Migration smoke — requires a live PostgreSQL instance via DATABASE_URL.
# Skipped (with a notice, not a failure) when DATABASE_URL is absent so that
# the script remains runnable in environments without a local database.
# ---------------------------------------------------------------------------
run_migration_smoke() {
  if [[ -z "${DATABASE_URL:-}" ]]; then
    echo "[release-check] migration gate: DATABASE_URL not set — skipping migration smoke"
    echo "[release-check] To run migrations: export DATABASE_URL='postgresql://user:pass@host:5432/dbname'"
    return 0
  fi

  # Reject the SQLAlchemy dialect prefix when passed by mistake; alembic/env.py
  # performs the postgresql:// → postgresql+psycopg:// normalisation itself.
  # We accept both to be safe, but we want a clearly formatted error for
  # completely invalid values.
  if [[ "${DATABASE_URL}" != postgresql://* && "${DATABASE_URL}" != postgresql+psycopg://* ]]; then
    echo "[release-check] migration gate: ERROR: DATABASE_URL does not look like a PostgreSQL DSN"
    echo "[release-check] Expected format: postgresql://user:pass@host:5432/dbname"
    exit 1
  fi

  if [[ ! -x "${VENV_ALEMBIC}" ]]; then
    echo "[release-check] ERROR: alembic not found at ${VENV_ALEMBIC}"
    exit 1
  fi

  echo "[release-check] migration gate: log heads"
  (
    cd "${BACKEND_DIR}"
    "${VENV_ALEMBIC}" heads
  )

  echo "[release-check] migration gate: upgrade -> downgrade -1 -> upgrade"
  (
    cd "${BACKEND_DIR}"
    "${VENV_ALEMBIC}" upgrade head
    "${VENV_ALEMBIC}" downgrade -1
    "${VENV_ALEMBIC}" upgrade head
  )
}

# ---------------------------------------------------------------------------
# Frontend gates.
# ---------------------------------------------------------------------------
run_frontend_checks() {
  if ! command -v npm >/dev/null 2>&1; then
    echo "[release-check] ERROR: npm not found — install Node.js to run frontend gates"
    exit 1
  fi

  echo "[release-check] frontend gate: type-check"
  (
    cd "${FRONTEND_DIR}"
    npm run type-check
  )

  echo "[release-check] frontend gate: tests"
  (
    cd "${FRONTEND_DIR}"
    npm run test:frontend
  )
}

# ---------------------------------------------------------------------------
# Entry point.
# ---------------------------------------------------------------------------
main() {
  check_venv

  run_backend_checks
  run_migration_smoke
  run_frontend_checks

  echo ""
  echo "[release-check] ✓ all safety gates passed"
}

main "$@"
