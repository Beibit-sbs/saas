#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACTS_DIR="${ROOT_DIR}/docs/runbooks/artifacts"

bash "${ROOT_DIR}/scripts/docker_only_guard.sh"

latest_day0="$(ls -1 "${ARTIFACTS_DIR}"/f1_risk_day0_baseline_*.md 2>/dev/null | tail -n 1 || true)"
if [[ -z "${latest_day0}" ]]; then
  echo "F1.9_GATE=FAIL"
  echo "REASON=missing_day0_baseline"
  echo "NEXT_ACTION=bash scripts/risk_phase_f1_post_release_day0.sh"
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

early_flag() {
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

day1_early="$(early_flag "${day1_artifact}")"
day3_early="$(early_flag "${day3_artifact}")"
day7_early="$(early_flag "${day7_artifact}")"

missing=""
if [[ -z "${day1_artifact}" ]]; then
  missing="${missing} day1"
fi
if [[ -z "${day3_artifact}" ]]; then
  missing="${missing} day3"
fi
if [[ -z "${day7_artifact}" ]]; then
  missing="${missing} day7"
fi

if [[ -n "${missing}" ]]; then
  echo "F1.9_GATE=FAIL"
  echo "REASON=missing_official_review_artifacts"
  echo "MISSING_PHASES=${missing# }"
  echo "TODAY_UTC=${today}"
  echo "DAY1_DUE=${day1_due}"
  echo "DAY3_DUE=${day3_due}"
  echo "DAY7_DUE=${day7_due}"
  echo "DAY1_ARTIFACT=${day1_artifact##*/}"
  echo "DAY3_ARTIFACT=${day3_artifact##*/}"
  echo "DAY7_ARTIFACT=${day7_artifact##*/}"

  if [[ "${today}" < "${day1_due}" ]]; then
    echo "WINDOW=pre_day1"
    echo "NEXT_ACTION=wait_due_window_then_run_official_reviews"
  elif [[ "${today}" < "${day3_due}" ]]; then
    echo "WINDOW=day1_to_day3"
    echo "NEXT_ACTION=wait_day3_due_then_run_official_day3_review"
  elif [[ "${today}" < "${day7_due}" ]]; then
    echo "WINDOW=day3_to_day7"
    echo "NEXT_ACTION=wait_day7_due_then_run_official_day7_review"
  else
    echo "WINDOW=post_day7"
    echo "NEXT_ACTION=run_missing_official_reviews_immediately"
  fi
  exit 1
fi

if [[ "${day1_early}" == "true" || "${day3_early}" == "true" || "${day7_early}" == "true" ]]; then
  echo "F1.9_GATE=FAIL"
  echo "REASON=early_rehearsal_artifact_detected"
  echo "TODAY_UTC=${today}"
  echo "DAY1_DUE=${day1_due}"
  echo "DAY3_DUE=${day3_due}"
  echo "DAY7_DUE=${day7_due}"
  echo "DAY1_EARLY=${day1_early}"
  echo "DAY3_EARLY=${day3_early}"
  echo "DAY7_EARLY=${day7_early}"
  echo "NEXT_ACTION=generate_official_non_early_review_artifacts"
  exit 1
fi

echo "F1.9_GATE=PASS"
echo "TODAY_UTC=${today}"
echo "DAY1_DUE=${day1_due}"
echo "DAY3_DUE=${day3_due}"
echo "DAY7_DUE=${day7_due}"
echo "DAY0_BASELINE=${latest_day0##*/}"
echo "DAY1_ARTIFACT=${day1_artifact##*/}"
echo "DAY3_ARTIFACT=${day3_artifact##*/}"
echo "DAY7_ARTIFACT=${day7_artifact##*/}"
echo "NEXT=eligible_for_f1_10_signoff"