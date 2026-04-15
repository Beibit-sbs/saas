#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACTS_DIR="${ROOT_DIR}/docs/runbooks/artifacts"

bash "${ROOT_DIR}/scripts/docker_only_guard.sh"

latest_day0="$(ls -1 "${ARTIFACTS_DIR}"/f1_risk_day0_baseline_*.md 2>/dev/null | tail -n 1 || true)"
if [[ -z "${latest_day0}" ]]; then
  echo "F1.9_STATUS=BLOCKED"
  echo "REASON=missing_day0_baseline"
  exit 1
fi

parse_due() {
  local key="$1"
  awk -F': ' -v k="$key" '$0 ~ k {print $2; exit}' "${latest_day0}"
}

day1_due="$(parse_due "Day 1 review due")"
day3_due="$(parse_due "Day 3 review due")"
day7_due="$(parse_due "Day 7 review due")"

today="$(date -u +%Y-%m-%d)"

latest_for_phase() {
  local phase="$1"
  ls -1 "${ARTIFACTS_DIR}"/f1_risk_${phase}_review_20*.md 2>/dev/null | tail -n 1 || true
}

artifact_early_flag() {
  local file="$1"
  if [[ -z "${file}" || ! -f "${file}" ]]; then
    echo ""
    return 0
  fi
  awk -F': ' '$1 == "- EARLY_EXECUTION" {print $2; exit}' "${file}"
}

day1_artifact="$(latest_for_phase day1)"
day3_artifact="$(latest_for_phase day3)"
day7_artifact="$(latest_for_phase day7)"

day1_early="$(artifact_early_flag "${day1_artifact}")"
day3_early="$(artifact_early_flag "${day3_artifact}")"
day7_early="$(artifact_early_flag "${day7_artifact}")"

next_action=""
if [[ -z "${day1_artifact}" ]]; then
  if [[ "${today}" < "${day1_due}" ]]; then
    next_action="wait_day1_due_then_run_official_day1_review"
  else
    next_action="run_official_day1_review"
  fi
elif [[ "${day1_early}" == "true" ]]; then
  if [[ "${today}" < "${day1_due}" ]]; then
    next_action="wait_day1_due_then_run_official_day1_review"
  else
    next_action="run_official_day1_review"
  fi
elif [[ -z "${day3_artifact}" ]]; then
  if [[ "${today}" < "${day3_due}" ]]; then
    next_action="wait_day3_due_then_run_official_day3_review"
  else
    next_action="run_official_day3_review"
  fi
elif [[ "${day3_early}" == "true" ]]; then
  if [[ "${today}" < "${day3_due}" ]]; then
    next_action="wait_day3_due_then_run_official_day3_review"
  else
    next_action="run_official_day3_review"
  fi
elif [[ -z "${day7_artifact}" ]]; then
  if [[ "${today}" < "${day7_due}" ]]; then
    next_action="wait_day7_due_then_run_official_day7_review"
  else
    next_action="run_official_day7_review"
  fi
elif [[ "${day7_early}" == "true" ]]; then
  if [[ "${today}" < "${day7_due}" ]]; then
    next_action="wait_day7_due_then_run_official_day7_review"
  else
    next_action="run_official_day7_review"
  fi
else
  next_action="prepare_f1_10_signoff"
fi

echo "F1.9_STATUS=IN_PROGRESS"
echo "TODAY_UTC=${today}"
echo "DAY0_BASELINE=${latest_day0##*/}"
echo "DAY1_DUE=${day1_due}"
echo "DAY3_DUE=${day3_due}"
echo "DAY7_DUE=${day7_due}"
echo "DAY1_ARTIFACT=${day1_artifact##*/}"
echo "DAY3_ARTIFACT=${day3_artifact##*/}"
echo "DAY7_ARTIFACT=${day7_artifact##*/}"
echo "NEXT_ACTION=${next_action}"

if [[ "${today}" < "${day1_due}" ]]; then
  echo "WINDOW=pre_day1"
elif [[ "${today}" < "${day3_due}" ]]; then
  echo "WINDOW=day1_to_day3"
elif [[ "${today}" < "${day7_due}" ]]; then
  echo "WINDOW=day3_to_day7"
else
  echo "WINDOW=post_day7"
fi