#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACTS_DIR="${ROOT_DIR}/docs/runbooks/artifacts"
OUT_FILE="${ARTIFACTS_DIR}/f1_risk_post_release_review_schedule.ics"

bash "${ROOT_DIR}/scripts/docker_only_guard.sh"

latest_day0="$(ls -1 "${ARTIFACTS_DIR}"/f1_risk_day0_baseline_*.md 2>/dev/null | tail -n 1 || true)"
if [[ -z "${latest_day0}" ]]; then
  echo "[f1-calendar] ERROR: missing day-0 baseline artifact" >&2
  exit 1
fi

parse_due() {
  local key="$1"
  awk -F': ' -v k="$key" '$0 ~ k {print $2; exit}' "${latest_day0}"
}

day7="$(parse_due "Day 7 review due")"
day14="$(parse_due "Day 14 review due")"
day30="$(parse_due "Day 30 review due")"

if [[ -z "${day7}" || -z "${day14}" || -z "${day30}" ]]; then
  echo "[f1-calendar] ERROR: failed to parse one or more due dates" >&2
  exit 1
fi

to_ics_date() {
  echo "${1//-/}"
}

day7_ics="$(to_ics_date "${day7}")"
day14_ics="$(to_ics_date "${day14}")"
day30_ics="$(to_ics_date "${day30}")"
created_ts="$(date -u +%Y%m%dT%H%M%SZ)"

cat >"${OUT_FILE}" <<EOF
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//AI Platform//F1 Risk Post Release//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH

BEGIN:VEVENT
UID:f1-risk-day7@ai-platform
DTSTAMP:${created_ts}
DTSTART;VALUE=DATE:${day7_ics}
SUMMARY:F1 Risk Day-7 Review
DESCRIPTION:Run official Day-7 review and capture artifact.
END:VEVENT

BEGIN:VEVENT
UID:f1-risk-day14@ai-platform
DTSTAMP:${created_ts}
DTSTART;VALUE=DATE:${day14_ics}
SUMMARY:F1 Risk Day-14 Review
DESCRIPTION:Run official Day-14 review and capture artifact.
END:VEVENT

BEGIN:VEVENT
UID:f1-risk-day30@ai-platform
DTSTAMP:${created_ts}
DTSTART;VALUE=DATE:${day30_ics}
SUMMARY:F1 Risk Day-30 Review
DESCRIPTION:Run official Day-30 review and capture artifact.
END:VEVENT

END:VCALENDAR
EOF

echo "[f1-calendar] exported: ${OUT_FILE}"