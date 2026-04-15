#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACTS_DIR="${ROOT_DIR}/docs/runbooks/artifacts"

bash "${ROOT_DIR}/scripts/docker_only_guard.sh"

latest_day0="$(ls -1 "${ARTIFACTS_DIR}"/f1_risk_day0_baseline_*.md 2>/dev/null | tail -n 1 || true)"
if [[ -z "${latest_day0}" ]]; then
  echo "[f1-post-release] ERROR: day-0 baseline artifact not found in ${ARTIFACTS_DIR}" >&2
  exit 1
fi

extract_due_date() {
  local label="$1"
  local file="$2"
  awk -F': ' -v key="$label" '$0 ~ key {print $2; exit}' "$file"
}

day1_due="$(extract_due_date "Day 1 review due" "${latest_day0}")"
day3_due="$(extract_due_date "Day 3 review due" "${latest_day0}")"
day7_due="$(extract_due_date "Day 7 review due" "${latest_day0}")"

if [[ -z "${day1_due}" || -z "${day3_due}" || -z "${day7_due}" ]]; then
  echo "[f1-post-release] ERROR: failed to parse due dates from ${latest_day0}" >&2
  exit 1
fi

create_template() {
  local phase="$1"
  local due_date="$2"
  local outfile="${ARTIFACTS_DIR}/f1_risk_${phase}_review_TEMPLATE.md"

  if [[ -f "${outfile}" ]]; then
    echo "[f1-post-release] SKIP: template already exists: ${outfile}"
    return 0
  fi

  cat >"${outfile}" <<EOF
# F1 Risk Post-Release ${phase^^} Review (Template)

- Source baseline: ${latest_day0##*/}
- Review due date: ${due_date}
- Filled at (UTC): <YYYY-MM-DDTHH:MM:SSZ>

## Review Scope

- [ ] Data freshness verified
- [ ] Alert noise/flapping reviewed
- [ ] Risk pipeline synthetic checks executed (if applicable)

## KPI Notes

- dropout_risk_reduction_percent: <value or note>
- false_positive_rate: <value or note>
- intervention_conversion_rate: <value or note>
- advisor_action_latency_p95: <value or note>

## Decisions / Actions

- [ ] No action required
- [ ] Threshold tuning required
- [ ] Alert tuning required
- [ ] Incident follow-up required

## Evidence

- Commands executed:
  - <command>
- Outputs:
  - <summary>

## Sign-off

- Reviewer: <name>
- Status: <PASS | WATCH | ACTION_REQUIRED>
EOF

  echo "[f1-post-release] CREATED: ${outfile}"
}

create_template "day1" "${day1_due}"
create_template "day3" "${day3_due}"
create_template "day7" "${day7_due}"

echo "[f1-post-release] DONE: review templates prepared from ${latest_day0##*/}"