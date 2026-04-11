#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 user@server"
  exit 1
fi

TARGET="$1"

ssh "$TARGET" "set -euo pipefail; \
  if [ ! -L ~/previous ]; then echo '[rollback] FAIL: ~/previous symlink not found'; exit 1; fi; \
  PREV_TARGET=\$(readlink -f ~/previous); \
  if [ ! -d \"\${PREV_TARGET}\" ]; then echo '[rollback] FAIL: previous release target missing'; exit 1; fi; \
  if [ -L ~/current ]; then CUR_TARGET=\$(readlink -f ~/current || true); else CUR_TARGET=; fi; \
  ln -sfn \"\${PREV_TARGET}\" ~/current; \
  if [ -n \"\${CUR_TARGET:-}\" ]; then ln -sfn \"\${CUR_TARGET}\" ~/previous; fi; \
  cd ~/current/infra && docker compose --env-file .env up -d --build"

echo "Rollback completed on ${TARGET}"