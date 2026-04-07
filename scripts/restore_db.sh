#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  restore_db.sh [--database-url <url>] [--dry-run] <dump_file>
  restore_db.sh [--database-url <url>] --execute --confirm RESTORE <dump_file>
  restore_db.sh [--dry-run] <target_database_url> <dump_file>
  restore_db.sh --execute --confirm RESTORE <target_database_url> <dump_file>

Behavior:
  - Safe by default: validates inputs and backup readability without modifying the target DB.
  - Destructive restore requires BOTH --execute and --confirm RESTORE.
  - Target database URL can be passed via --database-url, DATABASE_URL, or legacy positional arg.
EOF
}

mask_database_url() {
  printf '%s' "$1" | sed -E 's#(://[^:/]+:)[^@]+@#\1***@#'
}

if ! command -v pg_restore >/dev/null 2>&1; then
  echo "pg_restore not found"
  exit 1
fi

EXECUTE_RESTORE=false
CONFIRM_TEXT=""
TARGET_DATABASE_URL="${DATABASE_URL:-}"
POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --database-url)
      if [[ $# -lt 2 ]]; then
        echo "--database-url requires a value"
        usage
        exit 1
      fi
      TARGET_DATABASE_URL="$2"
      shift 2
      ;;
    --dry-run)
      EXECUTE_RESTORE=false
      shift
      ;;
    --execute)
      EXECUTE_RESTORE=true
      shift
      ;;
    --confirm)
      if [[ $# -lt 2 ]]; then
        echo "--confirm requires a value"
        usage
        exit 1
      fi
      CONFIRM_TEXT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      POSITIONAL_ARGS+=("$1")
      shift
      ;;
  esac
done

SOURCE=""
if [[ ${#POSITIONAL_ARGS[@]} -eq 1 ]]; then
  SOURCE="${POSITIONAL_ARGS[0]}"
elif [[ ${#POSITIONAL_ARGS[@]} -eq 2 ]]; then
  TARGET_DATABASE_URL="${POSITIONAL_ARGS[0]}"
  SOURCE="${POSITIONAL_ARGS[1]}"
else
  usage
  exit 1
fi

if [[ -z "${TARGET_DATABASE_URL}" ]]; then
  echo "DATABASE_URL is required (env, --database-url, or positional target_database_url)"
  exit 1
fi

if [[ -z "$SOURCE" ]]; then
  usage
  exit 1
fi

if [[ ! -f "$SOURCE" ]]; then
  echo "Backup file not found: $SOURCE"
  exit 1
fi

MASKED_DATABASE_URL="$(mask_database_url "$TARGET_DATABASE_URL")"

echo "[restore] target database: ${MASKED_DATABASE_URL}"
echo "[restore] backup file: ${SOURCE}"

if ! pg_restore --list "$SOURCE" >/dev/null; then
  echo "[restore] FAIL: backup artifact is not readable by pg_restore"
  exit 1
fi

if [[ "$EXECUTE_RESTORE" != "true" ]]; then
  echo "[restore] safe mode: restore not executed"
  echo "[restore] rerun with --execute --confirm RESTORE to apply pg_restore --clean --if-exists"
  exit 0
fi

if [[ "${CONFIRM_TEXT}" != "RESTORE" ]]; then
  echo "[restore] FAIL: destructive restore requires --confirm RESTORE"
  exit 1
fi

pg_restore \
  --clean \
  --if-exists \
  --no-owner \
  --no-privileges \
  --dbname "$TARGET_DATABASE_URL" \
  "$SOURCE"

echo "Restore completed from: $SOURCE"