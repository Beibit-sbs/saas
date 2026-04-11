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
RELEASE_NAME="${ARCHIVE%.tar.gz}"

pushd "${ROOT_DIR}" >/dev/null
tar --exclude-vcs --exclude='.env' --exclude='node_modules' --exclude='.[v]env' -czf "$ARCHIVE" .
scp "$ARCHIVE" "$TARGET:~/"
ssh "$TARGET" "set -euo pipefail; \
  mkdir -p ~/releases; \
  rm -rf ~/releases/${RELEASE_NAME}; \
  mkdir -p ~/releases/${RELEASE_NAME}; \
  tar -xzf ~/${ARCHIVE} -C ~/releases/${RELEASE_NAME}; \
  if [ -L ~/current ]; then PREV_TARGET=\$(readlink -f ~/current || true); else PREV_TARGET=; fi; \
  if [ -n \"\${PREV_TARGET:-}\" ]; then ln -sfn \"\${PREV_TARGET}\" ~/previous; fi; \
  if [ -f ~/shared/.env ]; then mkdir -p ~/releases/${RELEASE_NAME}/infra && cp ~/shared/.env ~/releases/${RELEASE_NAME}/infra/.env; fi; \
  if [ ! -f ~/releases/${RELEASE_NAME}/infra/.env ]; then cp -n ~/releases/${RELEASE_NAME}/infra/.env.example ~/releases/${RELEASE_NAME}/infra/.env; fi; \
  ln -sfn ~/releases/${RELEASE_NAME} ~/current; \
  cd ~/current/infra && docker compose --env-file .env up -d --build"
rm -f "$ARCHIVE"
popd >/dev/null

echo "Deploy completed to $TARGET (release=${RELEASE_NAME})"
