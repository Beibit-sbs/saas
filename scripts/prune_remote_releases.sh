#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 user@server [keep_count]"
  exit 1
fi

TARGET="$1"
KEEP_COUNT="${2:-2}"

ssh "$TARGET" "set -euo pipefail; \
  mkdir -p ~/releases; \
  cd ~/releases; \
  ls -1dt release-* 2>/dev/null | awk 'NR>${KEEP_COUNT}' | xargs -r rm -rf --; \
  echo '[prune] kept newest ${KEEP_COUNT} releases'"

echo "Remote release prune completed on ${TARGET}"