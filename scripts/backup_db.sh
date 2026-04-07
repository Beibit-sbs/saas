#!/usr/bin/env bash
set -euo pipefail

if ! command -v pg_dump >/dev/null 2>&1; then
  echo "pg_dump not found"
  exit 1
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is required"
  exit 1
fi

BACKUP_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"
TARGET="${1:-$BACKUP_DIR/ai_platform_${STAMP}.dump}"

if [[ -f "$TARGET" && "${BACKUP_ALLOW_OVERWRITE:-false}" != "true" ]]; then
  echo "Refusing to overwrite existing backup: $TARGET"
  echo "Set BACKUP_ALLOW_OVERWRITE=true to replace it explicitly"
  exit 1
fi

pg_dump \
  --format=custom \
  --no-owner \
  --no-privileges \
  --file "$TARGET" \
  "$DATABASE_URL"

echo "Backup created: $TARGET"