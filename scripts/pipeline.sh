#!/usr/bin/env bash
set -euo pipefail

# Docker-only pipeline: build, run, verify, and stop through compose.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE=(docker compose --env-file .env)

bash "${ROOT_DIR}/scripts/preflight_checks.sh"

pushd "${ROOT_DIR}/infra" >/dev/null
if [[ "${PIPELINE_ALLOW_DATA_RESET:-false}" == "true" ]]; then
  echo "[pipeline] WARN: explicit data reset mode enabled (down -v)"
  "${COMPOSE[@]}" down -v || true
else
  echo "[pipeline] safe mode: preserving docker volumes (set PIPELINE_ALLOW_DATA_RESET=true to allow reset)"
fi
"${COMPOSE[@]}" up -d --build
"${COMPOSE[@]}" exec -T backend ruff check .
"${COMPOSE[@]}" exec -T backend pytest -q
"${COMPOSE[@]}" exec -T backend pytest -q tests/test_template_validation.py
"${COMPOSE[@]}" run --rm frontend-tests npm run lint
"${COMPOSE[@]}" run --rm frontend-tests npm run test:frontend
"${COMPOSE[@]}" exec -T nginx wget -qO /dev/null http://127.0.0.1/health/live
"${COMPOSE[@]}" exec -T nginx wget -qO /dev/null http://127.0.0.1/
popd >/dev/null

echo "Pipeline OK: docker-only build, tests, and edge health checks passed."
