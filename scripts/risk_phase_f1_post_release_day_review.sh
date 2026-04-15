#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE=(docker compose --env-file .env)
ARTIFACTS_DIR="${ROOT_DIR}/docs/runbooks/artifacts"

usage() {
  cat <<EOF
Usage:
  bash scripts/risk_phase_f1_post_release_day_review.sh --phase <day1|day3|day7> [--allow-early]

Options:
  --phase        Review phase to execute.
  --allow-early  Allow execution before due date (records EARLY_EXECUTION=true in artifact).
EOF
}

phase=""
allow_early="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --phase)
      phase="${2:-}"
      shift 2
      ;;
    --allow-early)
      allow_early="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[f1-review] ERROR: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${phase}" ]]; then
  echo "[f1-review] ERROR: --phase is required" >&2
  usage
  exit 1
fi

case "${phase}" in
  day1|day3|day7) ;;
  *)
    echo "[f1-review] ERROR: invalid phase '${phase}' (expected day1|day3|day7)" >&2
    exit 1
    ;;
esac

bash "${ROOT_DIR}/scripts/docker_only_guard.sh"

latest_day0="$(ls -1 "${ARTIFACTS_DIR}"/f1_risk_day0_baseline_*.md 2>/dev/null | tail -n 1 || true)"
if [[ -z "${latest_day0}" ]]; then
  echo "[f1-review] ERROR: day-0 baseline artifact not found" >&2
  exit 1
fi

due_key=""
case "${phase}" in
  day1) due_key="Day 1 review due" ;;
  day3) due_key="Day 3 review due" ;;
  day7) due_key="Day 7 review due" ;;
esac

due_date="$(awk -F': ' -v key="${due_key}" '$0 ~ key {print $2; exit}' "${latest_day0}")"
if [[ -z "${due_date}" ]]; then
  echo "[f1-review] ERROR: failed to parse due date (${due_key}) from ${latest_day0}" >&2
  exit 1
fi

today_utc="$(date -u +%Y-%m-%d)"
if [[ "${allow_early}" != "true" && "${today_utc}" < "${due_date}" ]]; then
  echo "[f1-review] ERROR: phase ${phase} is not due yet (today=${today_utc}, due=${due_date}). Use --allow-early for rehearsal." >&2
  exit 1
fi

pushd "${ROOT_DIR}/infra" >/dev/null

BACKEND_TEST_OUTPUT="$(${COMPOSE[@]} run --rm --no-deps -e DATABASE_URL= backend-tests pytest -q \
  tests/modules/interventions/test_risk_observability_metrics.py \
  tests/modules/interventions/test_router_interventions_risk_phasec.py::test_v1_recompute_scores_burst_profile_p95_under_slo \
  tests/test_rate_limit.py::test_risk_recompute_rate_limit_returns_429_and_audits \
  --no-cov -rA)"

PROMTOOL_OUTPUT="$(${COMPOSE[@]} run --rm --no-deps --entrypoint promtool prometheus check rules /etc/prometheus/alerts.yml)"

popd >/dev/null

STAMP="$(date -u +%Y%m%d_%H%M%S)"
OUT_FILE="${ARTIFACTS_DIR}/f1_risk_${phase}_review_${STAMP}.md"
FILLED_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
EARLY_FLAG="false"
if [[ "${today_utc}" < "${due_date}" ]]; then
  EARLY_FLAG="true"
fi

cat >"${OUT_FILE}" <<EOF
# F1 Risk Post-Release ${phase^^} Review

- Source baseline: ${latest_day0##*/}
- Review due date: ${due_date}
- Filled at (UTC): ${FILLED_UTC}
- EARLY_EXECUTION: ${EARLY_FLAG}

## Verification Snapshot

### Backend risk checks

\`\`\`text
${BACKEND_TEST_OUTPUT}
\`\`\`

### Prometheus rules validation

\`\`\`text
${PROMTOOL_OUTPUT}
\`\`\`

## KPI Notes

- dropout_risk_reduction_percent: TODO (requires business-period delta data)
- false_positive_rate: TODO (requires labeling window)
- intervention_conversion_rate: TODO (requires intervention outcome aggregation)
- advisor_action_latency_p95: TODO (requires period trend from analytics/metrics)

## Decisions / Actions

- [ ] No action required
- [ ] Threshold tuning required
- [ ] Alert tuning required
- [ ] Incident follow-up required

## Sign-off

- Reviewer: TODO
- Status: TODO
EOF

echo "[f1-review] created artifact: ${OUT_FILE}"