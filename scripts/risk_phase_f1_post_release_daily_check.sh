#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<EOF
Usage:
  bash scripts/risk_phase_f1_post_release_daily_check.sh

Exit codes:
  0  On-track (wait window) or fully complete.
  1  Blocked/error state.
  2  Action is due now.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

status_output="$(bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_status.sh")"
gate_output="$(bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_gate.sh" || true)"
next_output="$(bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_next_action.sh")"

get_value() {
  local key="$1"
  local body="$2"
  printf '%s\n' "${body}" | awk -F= -v k="${key}" '$1==k {print $2; exit}'
}

f19_status="$(get_value "F1.9_STATUS" "${status_output}")"
window="$(get_value "WINDOW" "${status_output}")"
next_action="$(get_value "NEXT_ACTION" "${status_output}")"
gate_state="$(get_value "F1.9_GATE" "${gate_output}")"
gate_reason="$(get_value "REASON" "${gate_output}")"

health=""
exit_code=0

if [[ "${f19_status}" == "BLOCKED" ]]; then
  health="BLOCKED"
  exit_code=1
elif [[ "${gate_state}" == "PASS" ]]; then
  health="READY_FOR_F1_10"
  exit_code=0
elif [[ "${next_action}" == wait_* ]]; then
  health="ON_TRACK_WAIT"
  exit_code=0
elif [[ "${next_action}" == run_* || "${next_action}" == prepare_* ]]; then
  health="ACTION_DUE"
  exit_code=2
else
  health="UNKNOWN_NEEDS_REVIEW"
  exit_code=1
fi

echo "F1.9_DAILY_HEALTH=${health}"
echo "F1.9_STATUS=${f19_status}"
echo "WINDOW=${window}"
echo "NEXT_ACTION=${next_action}"
echo "GATE=${gate_state}"
if [[ -n "${gate_reason}" ]]; then
  echo "GATE_REASON=${gate_reason}"
fi
echo "EXIT_CODE_HINT=${exit_code}"

# Helpful operator context for terminal runs.
echo "---"
printf '%s\n' "${next_output}"

exit "${exit_code}"
