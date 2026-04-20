#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACTS_DIR="${ROOT_DIR}/docs/runbooks/artifacts"

bash "${ROOT_DIR}/scripts/docker_only_guard.sh"

latest_artifact() {
  local pattern="$1"
  ls -1 "${ARTIFACTS_DIR}"/${pattern} 2>/dev/null | tail -n 1 || true
}

parse_gate_status() {
  local key="$1"
  awk -F= -v k="$key" '$1==k {print $2; exit}'
}

echo "[f4-readiness] checking F1/F2 post-release gates"
f1_gate_output="$(bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_gate.sh" 2>&1 || true)"
f2_gate_output="$(bash "${ROOT_DIR}/scripts/f2_playbooks_post_release_gate.sh" 2>&1 || true)"

f1_gate_status="$(printf '%s\n' "${f1_gate_output}" | parse_gate_status "F1.9_GATE")"
f2_gate_status="$(printf '%s\n' "${f2_gate_output}" | parse_gate_status "F2.9_GATE")"

if [[ -z "${f1_gate_status}" ]]; then
  f1_gate_status="UNKNOWN"
fi
if [[ -z "${f2_gate_status}" ]]; then
  f2_gate_status="UNKNOWN"
fi

f1_dod_artifact="$(latest_artifact "f1_risk_dod_signoff_*.md")"
f2_dod_artifact="$(latest_artifact "f2_playbooks_dod_signoff_*.md")"

f1_dod_status="MISSING"
f2_dod_status="MISSING"
if [[ -n "${f1_dod_artifact}" ]]; then
  f1_dod_status="PRESENT"
fi
if [[ -n "${f2_dod_artifact}" ]]; then
  f2_dod_status="PRESENT"
fi

if [[ "${f1_gate_status}" == "PASS" && "${f2_gate_status}" == "PASS" && "${f1_dod_status}" == "PRESENT" && "${f2_dod_status}" == "PRESENT" ]]; then
  echo "[f4-readiness] PASS: entry criteria for F4 kickoff satisfied"
  echo "F4_ENTRY_READY=PASS"
  echo "F1_9_GATE=PASS"
  echo "F2_9_GATE=PASS"
  echo "F1_10_DOD=${f1_dod_artifact##*/}"
  echo "F2_10_DOD=${f2_dod_artifact##*/}"
  exit 0
fi

echo "[f4-readiness] BLOCKED: F4 kickoff entry criteria not satisfied"
echo "F4_ENTRY_READY=FAIL"
echo "F1_9_GATE=${f1_gate_status}"
echo "F2_9_GATE=${f2_gate_status}"
echo "F1_10_DOD=${f1_dod_status}"
echo "F2_10_DOD=${f2_dod_status}"

echo "NEXT_ACTION_1=run day7 one-shot on/after due date: make day7-f1f2-one-shot"
echo "NEXT_ACTION_2=re-run readiness gate: bash scripts/f4_kickoff_readiness.sh"
exit 1
