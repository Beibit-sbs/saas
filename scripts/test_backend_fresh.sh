#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE=(docker compose --env-file .env)

if [[ "${1:-}" == "--no-build" ]]; then
  rebuild="false"
  shift
else
  rebuild="${BACKEND_TESTS_REBUILD:-true}"
fi

pushd "${ROOT_DIR}/infra" >/dev/null

if [[ "${rebuild}" == "true" ]]; then
  echo "[test-backend-fresh] rebuilding backend-tests image"
  "${COMPOSE[@]}" build backend-tests
else
  echo "[test-backend-fresh] reusing existing backend-tests image"
fi

echo "[test-backend-fresh] running backend-tests pytest -q $*"
"${COMPOSE[@]}" run --rm --no-deps backend-tests pytest -q "$@"
