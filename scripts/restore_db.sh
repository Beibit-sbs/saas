#!/usr/bin/env bash
set -euo pipefail

if ! command -v pg_restore >/dev/null 2>&1; then
  echo "pg_restore not found"
  exit 1
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is required"
  exit 1
fi

SOURCE="${1:-}"
if [[ -z "$SOURCE" ]]; then
  echo "Usage: $0 path/to/backup.dump"
  exit 1
fi

if [[ ! -f "$SOURCE" ]]; then
  echo "Backup file not found: $SOURCE"
  exit 1
fi

pg_restore \
  --clean \
  --if-exists \
  --no-owner \
  --no-privileges \
  --dbname "$DATABASE_URL" \
  "$SOURCE"

echo "Restore completed from: $SOURCE"