#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<EOF
Usage:
  bash scripts/risk_phase_f1_post_release_next_action.sh [--execute]

Options:
  --execute   Run the resolved next action when it is executable now.
EOF
}

execute="false"
if [[ $# -gt 0 ]]; then
  case "$1" in
    --execute)
      execute="true"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[f1-next] ERROR: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
fi

status_output="$(bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_status.sh")"
next_action="$(printf '%s\n' "${status_output}" | awk -F= '$1=="NEXT_ACTION" {print $2; exit}')"
window="$(printf '%s\n' "${status_output}" | awk -F= '$1=="WINDOW" {print $2; exit}')"

if [[ -z "${next_action}" ]]; then
  echo "[f1-next] ERROR: failed to resolve NEXT_ACTION from status output" >&2
  printf '%s\n' "${status_output}" >&2
  exit 1
fi

echo "[f1-next] WINDOW=${window}"
echo "[f1-next] NEXT_ACTION=${next_action}"

resolve_command() {
  local action="$1"
  case "${action}" in
    run_day7_review)
      echo "bash scripts/risk_phase_f1_post_release_day_review.sh --phase day7"
      ;;
    run_official_day7_review)
      echo "bash scripts/risk_phase_f1_post_release_day_review.sh --phase day7"
      ;;
    run_day14_review)
      echo "bash scripts/risk_phase_f1_post_release_day_review.sh --phase day14"
      ;;
    run_official_day14_review)
      echo "bash scripts/risk_phase_f1_post_release_day_review.sh --phase day14"
      ;;
    run_day30_review)
      echo "bash scripts/risk_phase_f1_post_release_day_review.sh --phase day30"
      ;;
    run_official_day30_review)
      echo "bash scripts/risk_phase_f1_post_release_day_review.sh --phase day30"
      ;;
    prepare_f1_10_signoff)
      echo "bash scripts/risk_phase_f1_post_release_gate.sh"
      ;;
    wait_day7_due_then_run_official_day7_review)
      echo ""
      ;;
    wait_day14_due_then_run_official_day14_review)
      echo ""
      ;;
    wait_day30_due_then_run_official_day30_review)
      echo ""
      ;;
    *)
      echo ""
      ;;
  esac
}

cmd="$(resolve_command "${next_action}")"

if [[ "${execute}" != "true" ]]; then
  if [[ -n "${cmd}" ]]; then
    echo "[f1-next] COMMAND=${cmd}"
  else
    echo "[f1-next] COMMAND=none (wait/timebox or manual decision required)"
  fi
  exit 0
fi

if [[ -z "${cmd}" ]]; then
  echo "[f1-next] INFO: execution skipped; next action is wait/manual (${next_action})"
  exit 0
fi

echo "[f1-next] EXECUTING=${cmd}"
cd "${ROOT_DIR}"
# shellcheck disable=SC2086
${cmd}
