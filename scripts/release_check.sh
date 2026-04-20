#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE=(docker compose --env-file .env)

run_backend_checks() {
  "${COMPOSE[@]}" run --rm --no-deps backend-tests "$@"
}

resolve_migration_rollback_target() {
	local head_revision revision_file down_revision_block

	head_revision="$(run_backend_checks alembic heads | awk 'NR==1 {print $1}')"
	revision_file="${ROOT_DIR}/backend/alembic/versions/${head_revision}"_*.py
	down_revision_block="$(sed -n '/^down_revision\([[:space:]]*:[^=]*\)\?[[:space:]]*=[[:space:]]*(/,/)/p' ${revision_file})"

	if [[ -n "${down_revision_block}" ]]; then
		# Merge revisions make `alembic downgrade -1` ambiguous; targeting either
		# parent downgrades the database back to the full parent set.
		printf '%s\n' "${down_revision_block}" | grep -oE '["'"'"'][0-9a-f]+["'"'"']' | head -n1 | tr -d '"'"'"''
		return 0
	fi

	echo "-1"
}

bash "${ROOT_DIR}/scripts/preflight_checks.sh"

pushd "${ROOT_DIR}/infra" >/dev/null
"${COMPOSE[@]}" up -d db redis pgbouncer

echo "[release-check] architecture governance gate"
run_backend_checks pytest -q --no-cov --disable-warnings tests/platform/test_platform_architecture_guardrails_v1.py

echo "[release-check] tenant safety gate"
run_backend_checks pytest -q --no-cov --disable-warnings tests/platform/test_platform_tenant_safety_audit_v1.py

echo "[release-check] platform regression gate"
run_backend_checks pytest -q --no-cov --disable-warnings tests/platform/

if [[ "${RELEASE_ENABLE_DOMAIN_GATE:-true}" == "true" ]]; then
	echo "[release-check] domain layer gate"
	popd >/dev/null
	bash "${ROOT_DIR}/scripts/domain_layer_gate.sh"
	pushd "${ROOT_DIR}/infra" >/dev/null
else
	echo "[release-check] domain layer gate skipped (RELEASE_ENABLE_DOMAIN_GATE=false)"
fi

echo "[release-check] security regression gate"
run_backend_checks pytest -q --no-cov --disable-warnings -m security_regression

echo "[release-check] template validation gate"
run_backend_checks pytest -q --no-cov --disable-warnings tests/test_template_validation.py

if [[ "${RELEASE_ENABLE_DATA_LAYER_GATE:-true}" == "true" ]]; then
	echo "[release-check] data layer gate"
	popd >/dev/null
	bash "${ROOT_DIR}/scripts/data_layer_gate.sh"
	pushd "${ROOT_DIR}/infra" >/dev/null
else
	echo "[release-check] data layer gate skipped (RELEASE_ENABLE_DATA_LAYER_GATE=false)"
fi

echo "[release-check] migration safety gate"
run_backend_checks alembic heads
run_backend_checks alembic upgrade head
if [[ "${RELEASE_ENABLE_MIGRATION_ROLLBACK_TEST:-false}" == "true" ]]; then
	rollback_target="$(resolve_migration_rollback_target)"
	echo "[release-check] WARN: explicit migration rollback test enabled"
	echo "[release-check] rollback target: ${rollback_target}"
	run_backend_checks alembic downgrade "${rollback_target}"
	run_backend_checks alembic upgrade head
else
	echo "[release-check] safe mode: rollback migration test skipped"
	echo "[release-check] set RELEASE_ENABLE_MIGRATION_ROLLBACK_TEST=true to enable downgrade/upgrade check"
fi

echo "[release-check] frontend safety gate"
"${ROOT_DIR}/scripts/check_permission_parity.sh"
"${COMPOSE[@]}" run --rm frontend-tests npm run type-check
"${COMPOSE[@]}" run --rm frontend-tests npm run lint
"${COMPOSE[@]}" run --rm frontend-tests npm run test:frontend

if [[ "${RELEASE_ENABLE_F3_ALERT_GATE:-true}" == "true" ]]; then
	echo "[release-check] F3 observability alerts gate enabled"
	popd >/dev/null
	bash "${ROOT_DIR}/scripts/f3_observability_alerts_gate.sh"
	pushd "${ROOT_DIR}/infra" >/dev/null
else
	echo "[release-check] F3 observability alerts gate skipped (RELEASE_ENABLE_F3_ALERT_GATE=false)"
fi

if [[ "${RELEASE_ENABLE_SMOKE_GATE:-false}" == "true" ]]; then
  echo "[release-check] optional smoke gate enabled"
  popd >/dev/null
  bash "${ROOT_DIR}/scripts/platform_smoke_check.sh"
else
  popd >/dev/null
fi

echo "[release-check] docker-only safety gates passed"
