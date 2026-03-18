#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 user@server"
  exit 1
fi

TARGET="$1"
ARCHIVE="release-$(date +%Y%m%d-%H%M%S).tar.gz"

tar --exclude-vcs --exclude='.env' --exclude='node_modules' --exclude='.venv' -czf "$ARCHIVE" .
scp "$ARCHIVE" "$TARGET:~/"
ssh "$TARGET" "mkdir -p ~/app && tar -xzf ~/$ARCHIVE -C ~/app && cd ~/app/infra && cp -n .env.example .env && docker compose --env-file .env up -d --build"

echo "Deploy completed to $TARGET"
