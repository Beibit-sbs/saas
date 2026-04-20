#!/usr/bin/env bash
# F3.5 observability alerts gate.
# Usage:
#   bash scripts/f3_observability_alerts_gate.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ALERTS_FILE="${ROOT_DIR}/infra/prometheus/alerts.yml"
COMPOSE_FILE="${ROOT_DIR}/infra/docker-compose.yml"
ENV_FILE="${ROOT_DIR}/infra/.env"

required_alerts=(
  "F3CohortAnalysisLatencyHigh"
  "F3CohortOperationErrorRateHigh"
  "F3GuardrailPassRateLow"
  "F3AnalysisQueueBacklogHigh"
)

if [[ ! -f "${ALERTS_FILE}" ]]; then
  echo "[f3-alert-gate] BLOCKED: alerts config not found: ${ALERTS_FILE}"
  echo "F3.5_ALERT_GATE=FAIL"
  echo "ALERTS_FILE_EXISTS=FAIL"
  exit 1
fi

missing=()
for alert_name in "${required_alerts[@]}"; do
  if ! rg -n "alert:\\s+${alert_name}" "${ALERTS_FILE}" >/dev/null 2>&1; then
    missing+=("${alert_name}")
  fi
done

if [[ "${#missing[@]}" -gt 0 ]]; then
  echo "[f3-alert-gate] BLOCKED: missing required F3 alert rules"
  printf '[f3-alert-gate] missing: %s\n' "${missing[*]}"
  echo "F3.5_ALERT_GATE=FAIL"
  echo "ALERTS_FILE_EXISTS=PASS"
  echo "REQUIRED_ALERTS_PRESENT=FAIL"
  exit 1
fi

if [[ ! -f "${ENV_FILE}" || ! -f "${COMPOSE_FILE}" ]]; then
  echo "[f3-alert-gate] BLOCKED: compose prerequisites missing"
  echo "F3.5_ALERT_GATE=FAIL"
  echo "ALERTS_FILE_EXISTS=PASS"
  echo "REQUIRED_ALERTS_PRESENT=PASS"
  echo "PROMTOOL_CHECK=FAIL"
  exit 1
fi

promtool_output="$(docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" \
  run --rm --no-deps -T --entrypoint promtool prometheus \
  check rules /etc/prometheus/alerts.yml 2>&1)"

if ! grep -q "SUCCESS:" <<<"${promtool_output}"; then
  echo "[f3-alert-gate] BLOCKED: promtool validation failed"
  echo "${promtool_output}"
  echo "F3.5_ALERT_GATE=FAIL"
  echo "ALERTS_FILE_EXISTS=PASS"
  echo "REQUIRED_ALERTS_PRESENT=PASS"
  echo "PROMTOOL_CHECK=FAIL"
  exit 1
fi

rules_found="$(awk '/SUCCESS:/ {print $2; exit}' <<<"${promtool_output}")"

echo "[f3-alert-gate] PASS: F3 observability alerts are valid"
echo "F3.5_ALERT_GATE=PASS"
echo "ALERTS_FILE_EXISTS=PASS"
echo "REQUIRED_ALERTS_PRESENT=PASS"
echo "PROMTOOL_CHECK=PASS"
echo "RULES_FOUND=${rules_found:-unknown}"
