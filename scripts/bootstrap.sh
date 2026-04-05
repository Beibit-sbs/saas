#!/usr/bin/env bash
set -euo pipefail

# Docker-only bootstrap: build images and materialize the stack.

bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_only_guard.sh"

if [[ ! -f "infra/.env" ]]; then
  echo "infra/.env not found. Copy infra/.env.example first."
  exit 1
fi

(
  cd infra
  docker compose --env-file .env build
)

echo "Bootstrap complete: Docker images are built. Use docker compose --env-file infra/.env up -d --build to start the stack."
