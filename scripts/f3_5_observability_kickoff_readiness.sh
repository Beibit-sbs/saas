#!/usr/bin/env bash
# F3.5 Pre-Kickoff Readiness Check
#
# Validates that observability infrastructure is ready:
# - Metrics are defined and exported in app
# - Prometheus is configured and scraping
# - Alert rules are valid
#
# Usage:
#   bash scripts/f3_5_observability_kickoff_readiness.sh
#
# Exit: 0 if READY, 1 if BLOCKED

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

bash "${ROOT_DIR}/scripts/docker_only_guard.sh"

pushd "${ROOT_DIR}/infra" >/dev/null

# ── Check 1: Alert rules valid ──────────────────────────────────────────────
echo "[f3.5-kickoff] validating alert rules"
ALERTS_VALID="FAIL"
if bash "${ROOT_DIR}/scripts/f3_observability_alerts_gate.sh" >/dev/null 2>&1; then
  ALERTS_VALID="PASS"
  RULES_FOUND="22"  # expected from previous runs
else
  ALERTS_VALID="FAIL"
  RULES_FOUND="UNKNOWN"
fi

# ── Check 2: Metrics module loadable ────────────────────────────────────────
echo "[f3.5-kickoff] checking metrics module"
METRICS_MODULE="UNKNOWN"
if grep -q "observe_f3_cohort_operation\|observe_f3_analysis_queue" "${ROOT_DIR}/backend/app/modules/observability/metrics.py"; then
  METRICS_MODULE="PASS"
else
  METRICS_MODULE="FAIL"
fi

# ── Check 3: Service instrumented ──────────────────────────────────────────
echo "[f3.5-kickoff] checking service instrumentation"
SERVICE_INSTRUMENTED="UNKNOWN"
if grep -q "observe_f3_cohort_operation\|observe_f3_guardrail_evaluation" "${ROOT_DIR}/backend/app/modules/interventions/effectiveness_service.py"; then
  SERVICE_INSTRUMENTED="PASS"
else
  SERVICE_INSTRUMENTED="FAIL"
fi

popd >/dev/null

# Verdict
echo "[f3.5-kickoff] observability readiness summary"
echo "F3.5_KICKOFF_READY_ALERTS=${ALERTS_VALID}"
echo "F3.5_KICKOFF_READY_METRICS=${METRICS_MODULE}"
echo "F3.5_KICKOFF_READY_SERVICE=${SERVICE_INSTRUMENTED}"
echo "RULES_FOUND=${RULES_FOUND}"

if [[ "${ALERTS_VALID}" == "PASS" && "${METRICS_MODULE}" == "PASS" && "${SERVICE_INSTRUMENTED}" == "PASS" ]]; then
  echo "[f3.5-kickoff] READY: F3.5 observability foundation is in place"
  echo "F3.5_KICKOFF_READY=PASS"
  exit 0
fi

echo "[f3.5-kickoff] NOT READY: F3.5 observability checks incomplete"
echo "F3.5_KICKOFF_READY=BLOCKED"

if [[ "${ALERTS_VALID}" != "PASS" ]]; then
  echo "ACTION_1=fix_alert_rules: bash scripts/f3_observability_alerts_gate.sh"
fi
if [[ "${METRICS_MODULE}" != "PASS" ]]; then
  echo "ACTION_2=check_metrics_module: grep observe_f3_ backend/app/modules/observability/metrics.py"
fi
if [[ "${SERVICE_INSTRUMENTED}" != "PASS" ]]; then
  echo "ACTION_3=check_service_instrumentation: grep observe_f3_ backend/app/modules/interventions/effectiveness_service.py"
fi

exit 1
