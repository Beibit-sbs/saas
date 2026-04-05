#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

TMP_MATCHES="$(mktemp)"
TMP_VIOLATIONS="$(mktemp)"
trap 'rm -f "$TMP_MATCHES" "$TMP_VIOLATIONS"' EXIT

# Strict allowlist for loopback usage:
# - compose healthchecks
# - nginx allow 127.0.0.1
# - pipeline internal nginx-in-container probes
allow_file() {
  local file="$1"
  case "$file" in
    infra/docker-compose.yml|infra/nginx/nginx.conf|scripts/pipeline.sh)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

rg -n --hidden \
  --glob '!frontend/node_modules/**' \
  --glob '!**/.git/**' \
  --glob '!**/.pytest_cache/**' \
  --glob '!**/.ruff_cache/**' \
  --glob '!scripts/grep_policy_gate.sh' \
  'localhost|127\.0\.0\.1' . > "$TMP_MATCHES" || true

if [[ -s "$TMP_MATCHES" ]]; then
  while IFS= read -r line; do
    file="${line#./}"
    file="${file%%:*}"
    if ! allow_file "$file"; then
      printf '%s\n' "$line" >> "$TMP_VIOLATIONS"
    fi
  done < "$TMP_MATCHES"
fi

if [[ -s "$TMP_VIOLATIONS" ]]; then
  echo "grep policy gate FAILED: non-whitelisted loopback matches found"
  cat "$TMP_VIOLATIONS"
  exit 1
fi

echo "grep policy gate PASSED"
