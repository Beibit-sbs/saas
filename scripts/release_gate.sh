#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# F3 observability alerting is part of standard release path by default.
export RELEASE_ENABLE_F3_ALERT_GATE="${RELEASE_ENABLE_F3_ALERT_GATE:-true}"

echo "[release-gate] running release checks"
bash "${ROOT_DIR}/scripts/release_check.sh"

echo "[release-gate] running phase-b scheduling smoke checks"
bash "${ROOT_DIR}/scripts/scheduling_phase_b_smoke_check.sh"

echo "[release-gate] stopping compose services before rollback readiness checks"
pushd "${ROOT_DIR}/infra" >/dev/null
docker compose --env-file .env down --remove-orphans
popd >/dev/null

echo "[release-gate] running rollback readiness checks"
bash "${ROOT_DIR}/scripts/rollback_check.sh"

echo "[release-gate] PASS: release gate and rollback readiness are green"