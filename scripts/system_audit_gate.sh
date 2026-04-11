#!/usr/bin/env bash
set -euo pipefail

# One-shot full quality/security gate for local validation.
# Safe mode: does not reset volumes and does not mutate DB schema beyond normal app startup.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE=(docker compose --env-file .env)
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
AUDIT_DIR="${ROOT_DIR}/artifacts/audits"
AUDIT_REPORT="${AUDIT_DIR}/system-audit-${STAMP}.txt"

mkdir -p "${AUDIT_DIR}"

log() {
	echo "$1" | tee -a "${AUDIT_REPORT}"
}

section() {
	log ""
	log "=== $1 ==="
}

run_cmd() {
	log "[run] $*"
	"$@" | tee -a "${AUDIT_REPORT}"
}

log "=== system audit ==="
log "timestamp_utc=${STAMP}"

run_cmd bash "${ROOT_DIR}/scripts/preflight_checks.sh"

pushd "${ROOT_DIR}/infra" >/dev/null

section "bootstrap"
run_cmd "${COMPOSE[@]}" up -d db redis backend frontend nginx

section "core layer"
run_cmd "${COMPOSE[@]}" exec -T backend ruff check .
run_cmd "${COMPOSE[@]}" run --rm --no-deps backend-tests pytest -q --disable-warnings tests/platform/test_platform_architecture_guardrails_v1.py
run_cmd "${COMPOSE[@]}" run --rm --no-deps backend-tests pytest -q --disable-warnings tests/platform/test_platform_tenant_safety_audit_v1.py

section "application layer"
run_cmd "${COMPOSE[@]}" run --rm --no-deps backend-tests pytest -q --disable-warnings

section "security layer"
run_cmd "${COMPOSE[@]}" run --rm --no-deps backend-tests pytest -q --disable-warnings -m security_regression

section "access layer"
run_cmd "${ROOT_DIR}/scripts/check_permission_parity.sh"

section "frontend layer"
run_cmd "${COMPOSE[@]}" run --rm -T frontend-tests npm run lint
run_cmd "${COMPOSE[@]}" run --rm -T frontend-tests npm run test:frontend

popd >/dev/null

section "domain layer"
run_cmd bash "${ROOT_DIR}/scripts/domain_layer_gate.sh"

section "data layer"
run_cmd bash "${ROOT_DIR}/scripts/data_layer_gate.sh"

section "ops layer"
run_cmd bash "${ROOT_DIR}/scripts/rollback_check.sh"

log "[system-audit] OK: core/application/security/access/frontend/domain/data/ops layers are green."
log "audit_report=${AUDIT_REPORT}"
