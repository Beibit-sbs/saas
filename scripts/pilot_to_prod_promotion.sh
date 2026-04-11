#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PROMOTION_DIR="${ROOT_DIR}/artifacts/promotion"
PROMOTION_REPORT="${PROMOTION_DIR}/pilot-to-prod-${STAMP}.txt"

DRY_RUN="${PROMOTION_DRY_RUN:-true}"
RUN_GATES="${PROMOTION_RUN_GATES:-true}"
RUN_SMOKE="${PROMOTION_RUN_SMOKE:-true}"
RUN_PILOT_SAFE="${PROMOTION_RUN_PILOT_SAFE:-true}"
TARGET="${PROMOTION_TARGET:-}"
HEALTH_URL="${PROMOTION_HEALTH_URL:-}"
REMOTE_SMOKE="${PROMOTION_REMOTE_SMOKE:-true}"
REMOTE_PRUNE="${PROMOTION_REMOTE_PRUNE:-true}"
KEEP_RELEASES="${PROMOTION_KEEP_RELEASES:-2}"

mkdir -p "${PROMOTION_DIR}"

log() {
  echo "$1" | tee -a "${PROMOTION_REPORT}"
}

section() {
  log ""
  log "=== $1 ==="
}

run_cmd() {
  log "[run] $*"
  "$@" | tee -a "${PROMOTION_REPORT}"
}

section "pilot-to-prod promotion"
log "timestamp_utc=${STAMP}"
log "dry_run=${DRY_RUN}"
log "run_gates=${RUN_GATES}"
log "run_smoke=${RUN_SMOKE}"
log "run_pilot_safe=${RUN_PILOT_SAFE}"
log "remote_smoke=${REMOTE_SMOKE}"
log "remote_prune=${REMOTE_PRUNE}"
log "keep_releases=${KEEP_RELEASES}"

section "preflight"
run_cmd bash "${ROOT_DIR}/scripts/preflight_checks.sh"

if [[ "${RUN_GATES}" == "true" ]]; then
  section "release gate"
  run_cmd bash "${ROOT_DIR}/scripts/release_gate.sh"

  section "domain layer gate"
  run_cmd bash "${ROOT_DIR}/scripts/domain_layer_gate.sh"

  if [[ "${RUN_PILOT_SAFE}" == "true" ]]; then
    section "pilot safe gate"
    run_cmd bash "${ROOT_DIR}/scripts/university_pilot_safe_gate.sh"
  fi

  if [[ "${RUN_SMOKE}" == "true" ]]; then
    section "platform smoke gate"
    run_cmd bash "${ROOT_DIR}/scripts/platform_smoke_check.sh"
  fi
else
  section "gates"
  log "skipped by PROMOTION_RUN_GATES=false"
fi

section "artifact fingerprint"
run_cmd git -C "${ROOT_DIR}" rev-parse HEAD
run_cmd git -C "${ROOT_DIR}" status --short

if [[ "${DRY_RUN}" == "true" ]]; then
  section "deploy"
  log "DRY RUN: deploy step skipped"
  log "set PROMOTION_DRY_RUN=false and PROMOTION_TARGET=user@server to execute deploy"
  log "promotion_report=${PROMOTION_REPORT}"
  exit 0
fi

if [[ -z "${TARGET}" ]]; then
  log "FAIL: PROMOTION_TARGET is required when PROMOTION_DRY_RUN=false"
  exit 1
fi

if [[ -z "${HEALTH_URL}" ]]; then
  log "FAIL: PROMOTION_HEALTH_URL is required when PROMOTION_DRY_RUN=false"
  exit 1
fi

section "remote ssh preflight"
if ! ssh -o BatchMode=yes -o ConnectTimeout=10 "${TARGET}" "hostname" </dev/null | tee -a "${PROMOTION_REPORT}"; then
  log "FAIL: non-interactive SSH preflight failed for ${TARGET}"
  exit 1
fi

section "deploy"
run_cmd bash "${ROOT_DIR}/scripts/deploy.sh" "${TARGET}"

section "post-deploy health"
run_cmd curl -fsS "${HEALTH_URL}/health/live"
run_cmd curl -fsS "${HEALTH_URL}/health/ready"

if [[ "${REMOTE_SMOKE}" == "true" ]]; then
  section "post-deploy remote smoke"
  run_cmd ssh "${TARGET}" "cd ~/current && DOCKER_ONLY_GUARD_SKIP_PROCESS_CHECK=1 bash scripts/platform_smoke_check.sh"
else
  section "post-deploy remote smoke"
  log "skipped by PROMOTION_REMOTE_SMOKE=false"
fi

if [[ "${REMOTE_PRUNE}" == "true" ]]; then
  section "post-deploy release prune"
  run_cmd bash "${ROOT_DIR}/scripts/prune_remote_releases.sh" "${TARGET}" "${KEEP_RELEASES}"
else
  section "post-deploy release prune"
  log "skipped by PROMOTION_REMOTE_PRUNE=false"
fi

section "result"
log "PASS: pilot-to-prod promotion completed"
log "promotion_report=${PROMOTION_REPORT}"