#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE=(docker compose --env-file .env)

bash "${ROOT_DIR}/scripts/docker_only_guard.sh"

pushd "${ROOT_DIR}/infra" >/dev/null

# Isolated synthetic check: run in backend-tests without live DB dependencies.
"${COMPOSE[@]}" run --rm --no-deps -e DATABASE_URL= backend-tests pytest -q \
  tests/modules/interventions/test_risk_observability_metrics.py --no-cov

"${COMPOSE[@]}" run --rm --no-deps --entrypoint promtool prometheus check rules /etc/prometheus/alerts.yml

echo "[risk-f1-smoke] PASS: risk observability metrics tests and alert rules are valid"

popd >/dev/null
