#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACTS_DIR="${ROOT_DIR}/docs/runbooks/artifacts"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
NOW_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
OUT_TS="${ARTIFACTS_DIR}/f1_risk_post_release_manifest_${STAMP}.json"
OUT_LATEST="${ARTIFACTS_DIR}/f1_risk_post_release_manifest_latest.json"

usage() {
  cat <<EOF
Usage:
  bash scripts/risk_phase_f1_post_release_manifest.sh

Creates:
  docs/runbooks/artifacts/f1_risk_post_release_manifest_<UTC_TIMESTAMP>.json
  docs/runbooks/artifacts/f1_risk_post_release_manifest_latest.json
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

state_latest="${ARTIFACTS_DIR}/f1_risk_post_release_state_latest.json"
report_latest="${ARTIFACTS_DIR}/f1_risk_post_release_daily_report_latest.md"
snapshot_latest="${ARTIFACTS_DIR}/f1_risk_post_release_snapshot_latest.md"

state_source="$(ls -1 "${ARTIFACTS_DIR}"/f1_risk_post_release_state_*.json 2>/dev/null | grep -v '_latest\.json$' | tail -n 1 || true)"
report_source="$(ls -1 "${ARTIFACTS_DIR}"/f1_risk_post_release_daily_report_*.md 2>/dev/null | grep -v '_latest\.md$' | tail -n 1 || true)"
snapshot_source="$(ls -1 "${ARTIFACTS_DIR}"/f1_risk_post_release_snapshot_*.md 2>/dev/null | grep -v '_latest\.md$' | tail -n 1 || true)"

require_nonempty_file() {
  local f="$1"
  if [[ ! -f "${f}" ]]; then
    echo "[f1-manifest] ERROR: missing required file ${f}" >&2
    exit 1
  fi
  if [[ ! -s "${f}" ]]; then
    echo "[f1-manifest] ERROR: required file is empty: ${f}" >&2
    exit 1
  fi
}

require_nonempty_file "${state_latest}"
require_nonempty_file "${report_latest}"
require_nonempty_file "${snapshot_latest}"
require_nonempty_file "${state_source}"
require_nonempty_file "${report_source}"
require_nonempty_file "${snapshot_source}"

state_source_name="$(basename "${state_source}")"
report_source_name="$(basename "${report_source}")"
snapshot_source_name="$(basename "${snapshot_source}")"

sha_state="$(sha256sum "${state_latest}" | awk '{print $1}')"
sha_report="$(sha256sum "${report_latest}" | awk '{print $1}')"
sha_snapshot="$(sha256sum "${snapshot_latest}" | awk '{print $1}')"
size_state="$(wc -c < "${state_latest}" | tr -d '[:space:]')"
size_report="$(wc -c < "${report_latest}" | tr -d '[:space:]')"
size_snapshot="$(wc -c < "${snapshot_latest}" | tr -d '[:space:]')"
sha_source_state="$(sha256sum "${state_source}" | awk '{print $1}')"
sha_source_report="$(sha256sum "${report_source}" | awk '{print $1}')"
sha_source_snapshot="$(sha256sum "${snapshot_source}" | awk '{print $1}')"
size_source_state="$(wc -c < "${state_source}" | tr -d '[:space:]')"
size_source_report="$(wc -c < "${report_source}" | tr -d '[:space:]')"
size_source_snapshot="$(wc -c < "${snapshot_source}" | tr -d '[:space:]')"

build_manifest() {
  local out_file="$1"
  cat >"${out_file}" <<EOF
{
  "generated_at_utc": "${NOW_UTC}",
  "artifacts": {
    "state_latest": {
      "path": "docs/runbooks/artifacts/f1_risk_post_release_state_latest.json",
      "sha256": "${sha_state}",
      "size_bytes": ${size_state}
    },
    "daily_report_latest": {
      "path": "docs/runbooks/artifacts/f1_risk_post_release_daily_report_latest.md",
      "sha256": "${sha_report}",
      "size_bytes": ${size_report}
    },
    "snapshot_latest": {
      "path": "docs/runbooks/artifacts/f1_risk_post_release_snapshot_latest.md",
      "sha256": "${sha_snapshot}",
      "size_bytes": ${size_snapshot}
    }
  },
  "source_artifacts": {
    "state": {
      "file": "${state_source_name}",
      "sha256": "${sha_source_state}",
      "size_bytes": ${size_source_state}
    },
    "daily_report": {
      "file": "${report_source_name}",
      "sha256": "${sha_source_report}",
      "size_bytes": ${size_source_report}
    },
    "snapshot": {
      "file": "${snapshot_source_name}",
      "sha256": "${sha_source_snapshot}",
      "size_bytes": ${size_source_snapshot}
    }
  }
}
EOF
}

mkdir -p "${ARTIFACTS_DIR}"
build_manifest "${OUT_TS}"
cp -f "${OUT_TS}" "${OUT_LATEST}"

echo "[f1-manifest] created: ${OUT_TS}"
echo "[f1-manifest] updated: ${OUT_LATEST}"
