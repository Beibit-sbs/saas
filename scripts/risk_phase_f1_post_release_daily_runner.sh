#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<EOF
Usage:
  bash scripts/risk_phase_f1_post_release_daily_runner.sh [--no-report] [--auto-execute-due]

Options:
  --no-report         Skip markdown report artifact generation.
  --auto-execute-due  If daily check returns ACTION_DUE (rc=2), execute next action automatically.

Exit codes:
  0  On-track wait window or fully complete.
  1  Blocked/error state.
  2  Action is due now.
EOF
}

make_report="true"
auto_execute_due="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-report)
      make_report="false"
      shift
      ;;
    --auto-execute-due)
      auto_execute_due="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[f1-daily-runner] ERROR: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

run_daily_check() {
  set +e
  local out
  out="$(bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_daily_check.sh" 2>&1)"
  local rc=$?
  set -e
  printf '%s\n' "${out}"
  return "${rc}"
}

set +e
daily_output="$(run_daily_check)"
daily_rc=$?
set -e

echo "[f1-daily-runner] INITIAL_RC=${daily_rc}"
printf '%s\n' "${daily_output}"

if [[ "${auto_execute_due}" == "true" && "${daily_rc}" -eq 2 ]]; then
  echo "[f1-daily-runner] ACTION_DUE detected, executing next action"
  bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_next_action.sh" --execute

  set +e
  daily_output="$(run_daily_check)"
  daily_rc=$?
  set -e

  echo "[f1-daily-runner] POST_EXEC_RC=${daily_rc}"
  printf '%s\n' "${daily_output}"
fi

if [[ "${make_report}" == "true" ]]; then
  report_output="$(bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_daily_report.sh")"
  echo "[f1-daily-runner] ${report_output}"
fi

exit "${daily_rc}"
