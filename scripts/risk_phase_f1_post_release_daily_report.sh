#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACTS_DIR="${ROOT_DIR}/docs/runbooks/artifacts"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
NOW_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
OUT_FILE="${ARTIFACTS_DIR}/f1_risk_post_release_daily_report_${STAMP}.md"

usage() {
  cat <<EOF
Usage:
  bash scripts/risk_phase_f1_post_release_daily_report.sh

Creates:
  docs/runbooks/artifacts/f1_risk_post_release_daily_report_<UTC_TIMESTAMP>.md
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

mkdir -p "${ARTIFACTS_DIR}"

set +e
daily_output="$(bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_daily_check.sh" 2>&1)"
daily_rc=$?
due_output="$(bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_due_alert.sh" 2>&1)"
due_rc=$?
set -e

{
  cat <<EOF
# F1 Risk Post-Release Daily Report

- Generated at (UTC): ${NOW_UTC}
- Daily check exit code: ${daily_rc}
- Due alert exit code: ${due_rc}

## Daily Check Output

\`\`\`text
EOF
  printf '%s\n' "${daily_output}"
  cat <<'EOF'
```

## Due Alert Output

```text
EOF
  printf '%s\n' "${due_output}"
  cat <<'EOF'
```

## Interpretation

- Exit code `0`: on-track wait window or fully complete.
- Exit code `1`: blocked/invalid state (operator review required).
- Exit code `2`: action is due now (run next official step).
EOF
} >"${OUT_FILE}"

echo "[f1-daily-report] created artifact: ${OUT_FILE}"

exit 0
