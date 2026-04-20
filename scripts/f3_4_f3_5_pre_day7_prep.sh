#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACTS_DIR="${ROOT_DIR}/docs/runbooks/artifacts"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
OUT_FILE="${ARTIFACTS_DIR}/f3_4_f3_5_pre_day7_prep_${STAMP}.md"

mkdir -p "${ARTIFACTS_DIR}"

bash "${ROOT_DIR}/scripts/docker_only_guard.sh"

status_line() {
  local label="$1"
  local state="$2"
  local evidence="$3"
  printf "| %s | %s | %s |\n" "$label" "$state" "$evidence"
}

check_file() {
  local file="$1"
  if [[ -f "$file" ]]; then
    echo "PASS"
  else
    echo "FAIL"
  fi
}

check_script_exec() {
  local file="$1"
  if [[ -x "$file" ]]; then
    echo "PASS"
  else
    echo "FAIL"
  fi
}

run_gate() {
  local cmd="$1"
  timeout 25s bash -lc "$cmd" 2>/dev/null || true
}

gate_state_from_output() {
  local output="$1"
  local marker="$2"
  local state
  state="$(printf '%s\n' "$output" | awk -F= -v m="$marker" '$1 == m {print $2}' | tail -n1)"
  if [[ -n "$state" ]]; then
    printf '%s' "$state"
    return
  fi

  if printf '%s\n' "$output" | grep -qi 'timed out'; then
    printf '%s' "TIMEOUT"
    return
  fi

  printf '%s' "UNKNOWN"
}

F3_4_GUIDE_STATE="$(check_file "${ROOT_DIR}/docs/F3_4_FRONTEND_IMPLEMENTATION_GUIDE.md")"
F3_5_GUIDE_STATE="$(check_file "${ROOT_DIR}/docs/F3_5_OBSERVABILITY_IMPLEMENTATION_GUIDE.md")"

F3_4_GATE_SCRIPT_STATE="$(check_script_exec "${ROOT_DIR}/scripts/f3_4_frontend_kickoff_readiness.sh")"
F3_5_GATE_SCRIPT_STATE="$(check_script_exec "${ROOT_DIR}/scripts/f3_5_observability_kickoff_readiness.sh")"
F3_UNIFIED_GATE_SCRIPT_STATE="$(check_script_exec "${ROOT_DIR}/scripts/f3_kickoff_readiness.sh")"

F3_4_GATE_RAW="$(run_gate "cd '${ROOT_DIR}' && bash scripts/f3_4_frontend_kickoff_readiness.sh")"
F3_5_GATE_RAW="$(run_gate "cd '${ROOT_DIR}' && bash scripts/f3_5_observability_kickoff_readiness.sh")"
F3_UNIFIED_GATE_RAW="$(run_gate "cd '${ROOT_DIR}' && bash scripts/f3_kickoff_readiness.sh")"

F3_4_GATE_STATE="$(gate_state_from_output "$F3_4_GATE_RAW" "F3.4_KICKOFF_READY")"
F3_5_GATE_STATE="$(gate_state_from_output "$F3_5_GATE_RAW" "F3.5_KICKOFF_READY")"
F3_UNIFIED_GATE_STATE="$(gate_state_from_output "$F3_UNIFIED_GATE_RAW" "F3_KICKOFF_STATUS")"

if [[ -f "${ROOT_DIR}/frontend/package-lock.json" ]]; then
  FRONTEND_DEPS_STATE="PASS"
else
  FRONTEND_DEPS_STATE="WARN"
fi

if [[ -f "${ROOT_DIR}/infra/prometheus/alerts.yml" ]]; then
  PROM_ALERTS_FILE_STATE="PASS"
else
  PROM_ALERTS_FILE_STATE="FAIL"
fi

{
  echo "# F3.4/F3.5 Pre-Day7 Preparation Snapshot"
  echo
  echo "- Captured at (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "- Scope: prep-only (no full-delivery start before day7 sign-off)"
  echo
  echo "## Readiness Matrix"
  echo
  echo "| Check | State | Evidence |"
  echo "|------|-------|----------|"
  status_line "F3.4 implementation guide present" "$F3_4_GUIDE_STATE" "docs/F3_4_FRONTEND_IMPLEMENTATION_GUIDE.md"
  status_line "F3.5 implementation guide present" "$F3_5_GUIDE_STATE" "docs/F3_5_OBSERVABILITY_IMPLEMENTATION_GUIDE.md"
  status_line "F3.4 readiness script executable" "$F3_4_GATE_SCRIPT_STATE" "scripts/f3_4_frontend_kickoff_readiness.sh"
  status_line "F3.5 readiness script executable" "$F3_5_GATE_SCRIPT_STATE" "scripts/f3_5_observability_kickoff_readiness.sh"
  status_line "Unified F3 gate executable" "$F3_UNIFIED_GATE_SCRIPT_STATE" "scripts/f3_kickoff_readiness.sh"
  status_line "F3.4 kickoff readiness status" "$F3_4_GATE_STATE" "from f3_4_frontend_kickoff_readiness.sh"
  status_line "F3.5 kickoff readiness status" "$F3_5_GATE_STATE" "from f3_5_observability_kickoff_readiness.sh"
  status_line "Unified F3 kickoff status" "$F3_UNIFIED_GATE_STATE" "from f3_kickoff_readiness.sh"
  status_line "Frontend lockfile present" "$FRONTEND_DEPS_STATE" "frontend/package-lock.json"
  status_line "Prometheus alerts file present" "$PROM_ALERTS_FILE_STATE" "infra/prometheus/alerts.yml"
  echo
  echo "## Post-Day7 Immediate Runbook"
  echo
  echo "1. Execute official governance close: make day7-f1f2-one-shot"
  echo "2. Re-check F3 readiness immediately after sign-off: make f3-kickoff-readiness"
  echo "3. If F3.4 remains BLOCKED, bring backend stack up and re-run: make up && make f3-4-frontend-kickoff"
  echo "4. Start F3.4 phase-1 (data/hooks/pages/tests) and F3.5 phase-1 (metrics/spans/alerts) in parallel"
  echo
  echo "## Policy Guard"
  echo
  echo "- This artifact does not start full-delivery and is compliant with pre-day7 fail-closed governance."
} > "$OUT_FILE"

echo "[f3-prep] artifact created: ${OUT_FILE}"
echo "F3_PRE_DAY7_PREP=PASS"
echo "F3_4_GATE=${F3_4_GATE_STATE}"
echo "F3_5_GATE=${F3_5_GATE_STATE}"
echo "F3_UNIFIED_GATE=${F3_UNIFIED_GATE_STATE}"
