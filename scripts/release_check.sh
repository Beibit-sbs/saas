#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE=(docker compose --env-file .env)

run_backend_checks() {
  "${COMPOSE[@]}" run --rm --no-deps backend-tests "$@"
}

bash "${ROOT_DIR}/scripts/preflight_checks.sh"

pushd "${ROOT_DIR}/infra" >/dev/null
"${COMPOSE[@]}" up -d db redis

echo "[release-check] architecture governance gate"
run_backend_checks pytest -q tests/platform/test_platform_architecture_guardrails_v1.py

echo "[release-check] tenant safety gate"
run_backend_checks pytest -q tests/platform/test_platform_tenant_safety_audit_v1.py

echo "[release-check] platform regression gate"
run_backend_checks pytest -q tests/platform/

echo "[release-check] security regression gate"
run_backend_checks pytest -q -m security_regression

echo "[release-check] template validation gate"
run_backend_checks pytest -q tests/test_template_validation.py

echo "[release-check] migration safety gate"
run_backend_checks alembic heads
run_backend_checks alembic upgrade head
if [[ "${RELEASE_ENABLE_MIGRATION_ROLLBACK_TEST:-false}" == "true" ]]; then
	echo "[release-check] WARN: explicit migration rollback test enabled"
	run_backend_checks alembic downgrade -1
	run_backend_checks alembic upgrade head
else
	echo "[release-check] safe mode: rollback migration test skipped"
	echo "[release-check] set RELEASE_ENABLE_MIGRATION_ROLLBACK_TEST=true to enable downgrade/upgrade check"
fi

echo "[release-check] frontend safety gate"
"${COMPOSE[@]}" run --rm frontend-tests npm run type-check
"${COMPOSE[@]}" run --rm frontend-tests npm run test:frontend

if [[ "${RELEASE_ENABLE_SMOKE_GATE:-false}" == "true" ]]; then
  echo "[release-check] optional smoke gate enabled"
  popd >/dev/null
  bash "${ROOT_DIR}/scripts/platform_smoke_check.sh"
else
  popd >/dev/null
fi

echo "[release-check] docker-only safety gates passed"
