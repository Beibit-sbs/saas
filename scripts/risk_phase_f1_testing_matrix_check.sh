#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE=(docker compose --env-file .env)

bash "${ROOT_DIR}/scripts/docker_only_guard.sh"

pushd "${ROOT_DIR}/infra" >/dev/null

# Unit + integration + contract + load-profile bundle for F1 risk domain.
"${COMPOSE[@]}" run --rm --no-deps -e DATABASE_URL= backend-tests pytest -q \
  tests/modules/interventions/test_risk_observability_metrics.py \
  tests/modules/interventions/test_router_interventions_risk_phasec.py \
  tests/test_rate_limit.py::test_risk_recompute_rate_limit_returns_429_and_audits \
  --no-cov

# E2E advisor flow evidence.
set -a
source "${ROOT_DIR}/infra/.env"
set +a
E2E_AUTH_BYPASS_ENABLED=true "${COMPOSE[@]}" run --rm --no-deps \
  -e E2E_BASE_URL=https://nginx \
  -e JWT_SECRET="${JWT_SECRET}" \
  frontend-tests \
  sh -lc "npm run test:e2e -- e2e/smoke/interventions.spec.ts --reporter=list --retries=0"

echo "[risk-f1-testing-matrix] PASS: unit/integration/contract/load/e2e checks are green"

popd >/dev/null
