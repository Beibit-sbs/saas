#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACTS_DIR="${ROOT_DIR}/docs/runbooks/artifacts"

generate="false"

usage() {
  cat <<EOF
Usage:
  bash scripts/risk_phase_f1_post_release_publish_latest.sh [--generate]

Options:
  --generate  Generate fresh snapshot/report/state artifacts before publishing latest copies.

Creates/updates deterministic files:
  docs/runbooks/artifacts/f1_risk_post_release_state_latest.json
  docs/runbooks/artifacts/f1_risk_post_release_daily_report_latest.md
  docs/runbooks/artifacts/f1_risk_post_release_snapshot_latest.md
EOF
}

if [[ $# -gt 0 ]]; then
  case "$1" in
    --generate)
      generate="true"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[f1-publish] ERROR: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
fi

mkdir -p "${ARTIFACTS_DIR}"

if [[ "${generate}" == "true" ]]; then
  bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_state_export.sh"
  bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_daily_report.sh"
  bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_snapshot.sh"
fi

latest_state="$(ls -1 "${ARTIFACTS_DIR}"/f1_risk_post_release_state_*.json 2>/dev/null | grep -v '_latest\.json$' | tail -n 1 || true)"
latest_report="$(ls -1 "${ARTIFACTS_DIR}"/f1_risk_post_release_daily_report_*.md 2>/dev/null | grep -v '_latest\.md$' | tail -n 1 || true)"
latest_snapshot="$(ls -1 "${ARTIFACTS_DIR}"/f1_risk_post_release_snapshot_*.md 2>/dev/null | grep -v '_latest\.md$' | tail -n 1 || true)"

if [[ -z "${latest_state}" ]]; then
  echo "[f1-publish] ERROR: no state export artifact found" >&2
  exit 1
fi
if [[ -z "${latest_report}" ]]; then
  echo "[f1-publish] ERROR: no daily report artifact found" >&2
  exit 1
fi
if [[ -z "${latest_snapshot}" ]]; then
  echo "[f1-publish] ERROR: no snapshot artifact found" >&2
  exit 1
fi

cp -f "${latest_state}" "${ARTIFACTS_DIR}/f1_risk_post_release_state_latest.json"
cp -f "${latest_report}" "${ARTIFACTS_DIR}/f1_risk_post_release_daily_report_latest.md"
cp -f "${latest_snapshot}" "${ARTIFACTS_DIR}/f1_risk_post_release_snapshot_latest.md"

echo "[f1-publish] published latest artifacts"
echo "[f1-publish] state=${latest_state##*/} -> f1_risk_post_release_state_latest.json"
echo "[f1-publish] report=${latest_report##*/} -> f1_risk_post_release_daily_report_latest.md"
echo "[f1-publish] snapshot=${latest_snapshot##*/} -> f1_risk_post_release_snapshot_latest.md"
