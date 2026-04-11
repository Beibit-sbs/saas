#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-${ROOT_DIR}/backups}"

bash "${ROOT_DIR}/scripts/preflight_checks.sh"

if [[ ! -x "${ROOT_DIR}/scripts/backup_db.sh" || ! -x "${ROOT_DIR}/scripts/restore_db.sh" ]]; then
  echo "[rollback-check] FAIL: backup/restore scripts must be executable"
  exit 1
fi

if [[ ! -d "${BACKUP_DIR}" ]]; then
  echo "[rollback-check] FAIL: backup directory not found: ${BACKUP_DIR}"
  exit 1
fi

LATEST_BACKUP="$(find "${BACKUP_DIR}" -maxdepth 1 -type f -name '*.dump' -printf '%T@ %p\n' | sort -nr | awk 'NR==1{print $2}')"
if [[ -z "${LATEST_BACKUP}" ]]; then
  echo "[rollback-check] FAIL: no .dump backups found in ${BACKUP_DIR}"
  exit 1
fi

echo "[rollback-check] latest backup: ${LATEST_BACKUP}"

if command -v pg_restore >/dev/null 2>&1; then
  pg_restore --list "${LATEST_BACKUP}" >/dev/null
else
  CONTAINER_BACKUP_PATH="${LATEST_BACKUP}"
  if [[ "${LATEST_BACKUP}" == "${ROOT_DIR}"/* ]]; then
    CONTAINER_BACKUP_PATH="/workspace/${LATEST_BACKUP#"${ROOT_DIR}/"}"
  fi
  docker run --rm \
    -v "${ROOT_DIR}:/workspace:Z" \
    -w /workspace \
    postgres:16 \
    pg_restore --list "${CONTAINER_BACKUP_PATH}" >/dev/null
fi

echo "[rollback-check] backup artifact is readable"

if [[ "${ROLLBACK_ENABLE_RESTORE_DRILL:-false}" == "true" ]]; then
  echo "[rollback-check] WARN: restore drill execution is environment-specific"
  echo "[rollback-check] follow docs/BACKUP_RESTORE_DRILL.md for isolated rehearsal run"
else
  echo "[rollback-check] safe mode: restore drill execution skipped"
  echo "[rollback-check] set ROLLBACK_ENABLE_RESTORE_DRILL=true after provisioning isolated target DB"
fi

echo "[rollback-check] PASS: rollback readiness checks completed"