#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACTS_DIR="${ROOT_DIR}/docs/runbooks/artifacts"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
NOW_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
OUT_FILE="${ARTIFACTS_DIR}/f1_risk_post_release_state_${STAMP}.json"

usage() {
  cat <<EOF
Usage:
  bash scripts/risk_phase_f1_post_release_state_export.sh

Creates:
  docs/runbooks/artifacts/f1_risk_post_release_state_<UTC_TIMESTAMP>.json
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

mkdir -p "${ARTIFACTS_DIR}"

set +e
status_output="$(bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_status.sh" 2>&1)"
status_rc=$?
gate_output="$(bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_gate.sh" 2>&1)"
gate_rc=$?
daily_output="$(bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_daily_check.sh" 2>&1)"
daily_rc=$?
due_output="$(bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_due_alert.sh" 2>&1)"
due_rc=$?
set -e

if (( status_rc != 0 )); then
  echo "[f1-state-export] ERROR: unable to collect status output" >&2
  printf '%s\n' "${status_output}" >&2
  exit 1
fi

kv() {
  local key="$1"
  local body="$2"
  printf '%s\n' "${body}" | awk -F= -v k="${key}" '$1==k {print $2; exit}'
}

json_escape() {
  local s="${1:-}"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\r'/}"
  printf '%s' "${s}"
}

f19_status="$(kv "F1.9_STATUS" "${status_output}")"
today_utc="$(kv "TODAY_UTC" "${status_output}")"
window="$(kv "WINDOW" "${status_output}")"
next_action="$(kv "NEXT_ACTION" "${status_output}")"

day0_baseline="$(kv "DAY0_BASELINE" "${status_output}")"
day7_due="$(kv "DAY7_DUE" "${status_output}")"
day14_due="$(kv "DAY14_DUE" "${status_output}")"
day30_due="$(kv "DAY30_DUE" "${status_output}")"

day7_artifact="$(kv "DAY7_ARTIFACT" "${status_output}")"
day14_artifact="$(kv "DAY14_ARTIFACT" "${status_output}")"
day30_artifact="$(kv "DAY30_ARTIFACT" "${status_output}")"

gate_state="$(kv "F1.9_GATE" "${gate_output}")"
gate_reason="$(kv "REASON" "${gate_output}")"
gate_missing_phases="$(kv "MISSING_PHASES" "${gate_output}")"

health="$(kv "F1.9_DAILY_HEALTH" "${daily_output}")"
if [[ -z "${health}" ]]; then
  health="UNKNOWN"
fi

due_state="$(kv "F1.9_DUE_ALERT" "${due_output}")"
due_phase="$(kv "NEXT_PENDING_PHASE" "${due_output}")"
due_date_utc="$(kv "DUE_DATE_UTC" "${due_output}")"
due_today_utc="$(kv "TODAY_UTC" "${due_output}")"
due_days_remaining="$(kv "DAYS_REMAINING" "${due_output}")"
due_next_action="$(kv "NEXT_ACTION" "${due_output}")"
due_level="$(kv "ALERT_LEVEL" "${due_output}")"
due_action="$(kv "ALERT_ACTION" "${due_output}")"
gate_today_utc="$(kv "TODAY_UTC" "${gate_output}")"
gate_window="$(kv "WINDOW" "${gate_output}")"
gate_next_action="$(kv "NEXT_ACTION" "${gate_output}")"

{
  echo "{"
  echo "  \"generated_at_utc\": \"$(json_escape "${NOW_UTC}")\"," 
  echo "  \"f1_9_status\": \"$(json_escape "${f19_status}")\"," 
  echo "  \"today_utc\": \"$(json_escape "${today_utc}")\"," 
  echo "  \"window\": \"$(json_escape "${window}")\"," 
  echo "  \"next_action\": \"$(json_escape "${next_action}")\"," 
  echo "  \"daily_health\": \"$(json_escape "${health}")\"," 
  echo "  \"daily_check_exit_code\": ${daily_rc},"
  echo "  \"due_alert\": {"
  echo "    \"state\": \"$(json_escape "${due_state}")\"," 
  echo "    \"next_pending_phase\": \"$(json_escape "${due_phase}")\"," 
  echo "    \"due_date_utc\": \"$(json_escape "${due_date_utc}")\"," 
  echo "    \"today_utc\": \"$(json_escape "${due_today_utc}")\"," 
  echo "    \"days_remaining\": \"$(json_escape "${due_days_remaining}")\"," 
  echo "    \"next_action\": \"$(json_escape "${due_next_action}")\"," 
  echo "    \"alert_level\": \"$(json_escape "${due_level}")\"," 
  echo "    \"alert_action\": \"$(json_escape "${due_action}")\"," 
  echo "    \"exit_code\": ${due_rc}"
  echo "  },"
  echo "  \"gate\": {"
  echo "    \"state\": \"$(json_escape "${gate_state}")\"," 
  echo "    \"reason\": \"$(json_escape "${gate_reason}")\"," 
  echo "    \"missing_phases\": \"$(json_escape "${gate_missing_phases}")\"," 
  echo "    \"today_utc\": \"$(json_escape "${gate_today_utc}")\"," 
  echo "    \"window\": \"$(json_escape "${gate_window}")\"," 
  echo "    \"next_action\": \"$(json_escape "${gate_next_action}")\"," 
  echo "    \"exit_code\": ${gate_rc}"
  echo "  },"
  echo "  \"schedule\": {"
  echo "    \"day7_due\": \"$(json_escape "${day7_due}")\"," 
  echo "    \"day14_due\": \"$(json_escape "${day14_due}")\"," 
  echo "    \"day30_due\": \"$(json_escape "${day30_due}")\""
  echo "  },"
  echo "  \"artifacts\": {"
  echo "    \"day0_baseline\": \"$(json_escape "${day0_baseline}")\"," 
  echo "    \"day7_review\": \"$(json_escape "${day7_artifact}")\"," 
  echo "    \"day14_review\": \"$(json_escape "${day14_artifact}")\"," 
  echo "    \"day30_review\": \"$(json_escape "${day30_artifact}")\""
  echo "  }"
  echo "}"
} >"${OUT_FILE}"

echo "[f1-state-export] created artifact: ${OUT_FILE}"
