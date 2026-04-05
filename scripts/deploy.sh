#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

bash "${ROOT_DIR}/scripts/preflight_checks.sh"

if [[ "${DEPLOY_SKIP_RELEASE_GATE:-false}" != "true" ]]; then
  bash "${ROOT_DIR}/scripts/release_gate.sh"
else
  echo "[deploy] WARN: DEPLOY_SKIP_RELEASE_GATE=true (release gate bypassed)"
fi

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 user@server"
  exit 1
fi

TARGET="$1"
ARCHIVE="release-$(date +%Y%m%d-%H%M%S).tar.gz"

pushd "${ROOT_DIR}" >/dev/null
tar --exclude-vcs --exclude='.env' --exclude='node_modules' --exclude='.[v]env' -czf "$ARCHIVE" .
scp "$ARCHIVE" "$TARGET:~/"
ssh "$TARGET" "mkdir -p ~/app && tar -xzf ~/$ARCHIVE -C ~/app && cd ~/app/infra && cp -n .env.example .env && docker compose --env-file .env up -d --build"
popd >/dev/null

echo "Deploy completed to $TARGET"
