#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE=(docker compose --env-file .env)

bash "${ROOT_DIR}/scripts/docker_only_guard.sh"

if [[ ! -f "${ROOT_DIR}/infra/.env" ]]; then
  echo "[preflight] FAIL: infra/.env not found. Copy infra/.env.example first."
  exit 1
fi

pushd "${ROOT_DIR}/infra" >/dev/null
if ! "${COMPOSE[@]}" config -q; then
  echo "[preflight] FAIL: docker compose configuration is invalid"
  exit 1
fi
popd >/dev/null

echo "[preflight] OK: guard/env/compose checks passed"