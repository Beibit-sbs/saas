#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<EOF
Usage:
  bash scripts/risk_phase_f1_post_release_due_alert.sh

Outputs:
  - next pending official review phase
  - due date and days remaining
  - alert level and action hint

Exit codes:
  0  Scheduled or upcoming week
  2  Due soon / due today / overdue
  1  Error state
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

status_output="$(bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_status.sh")"

kv() {
  local key="$1"
  local body="$2"
  printf '%s\n' "${body}" | awk -F= -v k="${key}" '$1==k {print $2; exit}'
}

f19_status="$(kv "F1.9_STATUS" "${status_output}")"
today="$(kv "TODAY_UTC" "${status_output}")"
next_action="$(kv "NEXT_ACTION" "${status_output}")"
day7_due="$(kv "DAY7_DUE" "${status_output}")"
day14_due="$(kv "DAY14_DUE" "${status_output}")"
day30_due="$(kv "DAY30_DUE" "${status_output}")"

if [[ -z "${f19_status}" || -z "${today}" || -z "${next_action}" ]]; then
  echo "[f1-due-alert] ERROR: failed to parse status output" >&2
  exit 1
fi

if [[ "${f19_status}" == "BLOCKED" ]]; then
  echo "F1.9_DUE_ALERT=BLOCKED"
  echo "NEXT_ACTION=${next_action}"
  echo "ALERT_LEVEL=high"
  echo "ALERT_ACTION=fix_blocker_before_schedule_tracking"
  exit 2
fi

phase=""
due_date=""

case "${next_action}" in
  *day7*)
    phase="day7"
    due_date="${day7_due}"
    ;;
  *day14*)
    phase="day14"
    due_date="${day14_due}"
    ;;
  *day30*)
    phase="day30"
    due_date="${day30_due}"
    ;;
  prepare_f1_10_signoff)
    echo "F1.9_DUE_ALERT=COMPLETE"
    echo "NEXT_ACTION=${next_action}"
    echo "ALERT_LEVEL=none"
    echo "ALERT_ACTION=ready_for_f1_10_signoff"
    exit 0
    ;;
  *)
    echo "F1.9_DUE_ALERT=UNKNOWN"
    echo "NEXT_ACTION=${next_action}"
    echo "ALERT_LEVEL=high"
    echo "ALERT_ACTION=manual_review_required"
    exit 2
    ;;
esac

if [[ -z "${due_date}" ]]; then
  echo "[f1-due-alert] ERROR: due date is empty for phase ${phase}" >&2
  exit 1
fi

today_epoch="$(date -u -d "${today}" +%s)"
due_epoch="$(date -u -d "${due_date}" +%s)"
days_remaining="$(( (due_epoch - today_epoch) / 86400 ))"

alert_level=""
alert_action=""
exit_code=0

if (( days_remaining < 0 )); then
  alert_level="critical"
  alert_action="run_official_review_immediately"
  exit_code=2
elif (( days_remaining == 0 )); then
  alert_level="high"
  alert_action="run_official_review_today"
  exit_code=2
elif (( days_remaining <= 2 )); then
  alert_level="high"
  alert_action="prepare_and_run_review_within_48h"
  exit_code=2
elif (( days_remaining <= 7 )); then
  alert_level="medium"
  alert_action="prepare_review_window"
  exit_code=0
else
  alert_level="low"
  alert_action="monitor_schedule"
  exit_code=0
fi

echo "F1.9_DUE_ALERT=ACTIVE"
echo "NEXT_PENDING_PHASE=${phase}"
echo "DUE_DATE_UTC=${due_date}"
echo "TODAY_UTC=${today}"
echo "DAYS_REMAINING=${days_remaining}"
echo "NEXT_ACTION=${next_action}"
echo "ALERT_LEVEL=${alert_level}"
echo "ALERT_ACTION=${alert_action}"

exit "${exit_code}"
