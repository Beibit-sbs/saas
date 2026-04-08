#!/usr/bin/env bash
set -euo pipefail

# Verifies that every frontend permission constant is present in backend
# route guards and/or RBAC baseline permission sets.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v rg >/dev/null 2>&1; then
  echo "error: ripgrep (rg) is required for this check" >&2
  exit 2
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

FRONTEND_FILE="$TMP_DIR/frontend_permissions.txt"
BACKEND_ROUTE_FILE="$TMP_DIR/backend_route_permissions.txt"
BACKEND_RBAC_FILE="$TMP_DIR/backend_rbac_permissions.txt"
BACKEND_ALL_FILE="$TMP_DIR/backend_permissions_all.txt"
MISSING_FILE="$TMP_DIR/frontend_missing_in_backend.txt"

awk -F'"' '/^[[:space:]]*[A-Z0-9_]+:[[:space:]]*"[a-z0-9_.]+"/{print $2}' frontend/shared/config/permissions.ts \
  | sort -u > "$FRONTEND_FILE"

rg -o 'permission_dependency\("[a-z0-9_.]+"\)' backend/app backend/modules --glob '*.py' \
  | sed -E 's/.*\("([a-z0-9_.]+)"\).*/\1/' \
  | sort -u > "$BACKEND_ROUTE_FILE"

rg -o '"[a-z0-9_.]+"' backend/app/modules/rbac/service.py \
  | tr -d '"' \
  | rg '^[a-z]+(\.[a-z_]+)+$' \
  | sort -u > "$BACKEND_RBAC_FILE"

cat "$BACKEND_ROUTE_FILE" "$BACKEND_RBAC_FILE" | sort -u > "$BACKEND_ALL_FILE"

comm -23 "$FRONTEND_FILE" "$BACKEND_ALL_FILE" > "$MISSING_FILE"

frontend_count="$(wc -l < "$FRONTEND_FILE" | tr -d ' ')"
backend_route_count="$(wc -l < "$BACKEND_ROUTE_FILE" | tr -d ' ')"
backend_union_count="$(wc -l < "$BACKEND_ALL_FILE" | tr -d ' ')"
missing_count="$(wc -l < "$MISSING_FILE" | tr -d ' ')"

echo "Frontend permissions: $frontend_count"
echo "Backend guarded permissions: $backend_route_count"
echo "Backend permission universe: $backend_union_count"

if [[ "$missing_count" -gt 0 ]]; then
  echo ""
  echo "ERROR: frontend permissions missing in backend permission set:"
  cat "$MISSING_FILE"
  exit 1
fi

echo "OK: all frontend permission constants are present in backend permissions."
