#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<EOF
Usage:
  bash scripts/risk_phase_f1_post_release_ci.sh [--auto-execute-due] [--no-report] [--fail-on-due-alert] [--require-fresh-report] [--max-report-lag-seconds N] [--require-fresh-snapshot] [--max-snapshot-lag-seconds N] [--require-coherent-artifact-timestamps] [--max-artifact-skew-seconds N] [--require-coherent-embedded-timestamps] [--max-embedded-timestamp-skew-seconds N] [--require-recent-state] [--max-state-age-seconds N] [--require-coherent-manifest-time] [--max-manifest-lag-seconds N] [--max-manifest-filename-skew-seconds N] [--require-recent-manifest] [--max-manifest-age-seconds N] [--reject-future-timestamps] [--max-future-skew-seconds N] [--strict-all]

Pipeline:
  1) daily runner
  2) due alert
  3) JSON state export
  4) snapshot artifact
  5) publish latest artifacts
  6) manifest artifact
  7) verify latest artifacts

Options:
  --auto-execute-due  If daily runner sees ACTION_DUE (rc=2), auto-run next action and re-check.
  --no-report         Skip markdown daily report generation inside daily runner.
  --fail-on-due-alert Return rc=2 when due_alert signals due-soon/due-now/overdue.
  --require-fresh-report  Enforce max lag between newest state and report artifacts during verify.
  --max-report-lag-seconds N  Max allowed lag for --require-fresh-report (default: 86400).
  --require-fresh-snapshot  Enforce max lag between newest state and snapshot artifacts during verify.
  --max-snapshot-lag-seconds N  Max allowed lag for --require-fresh-snapshot (default: 86400).
  --require-coherent-artifact-timestamps  Enforce max skew between newest state/report/snapshot artifact timestamps.
  --max-artifact-skew-seconds N  Max allowed skew for --require-coherent-artifact-timestamps (default: 300).
  --require-coherent-embedded-timestamps  Enforce embedded generated/captured timestamps inside latest artifacts match filename timestamps.
  --max-embedded-timestamp-skew-seconds N  Max allowed embedded timestamp skew (default: 5).
  --require-recent-state  Enforce max wall-clock age of newest state artifact.
  --max-state-age-seconds N  Max allowed age for newest state artifact (default: 900).
  --require-coherent-manifest-time  Enforce generated_at_utc coherence against newest artifact timestamp.
  --max-manifest-lag-seconds N  Max allowed manifest generation lag vs newest artifact timestamp (default: 300).
  --max-manifest-filename-skew-seconds N  Max allowed skew between manifest filename timestamp and generated_at_utc (default: 300).
  --require-recent-manifest  Enforce max wall-clock age of newest manifest artifact.
  --max-manifest-age-seconds N  Max allowed wall-clock age for newest manifest artifact (default: 900).
  --reject-future-timestamps  Enforce that newest artifacts/manifest timestamps are not in the future.
  --max-future-skew-seconds N  Allowed positive skew into future (default: 30).
  --strict-all        Shorthand: fail-on-due-alert + freshness + coherence + state recency + manifest-time checks.

Exit codes:
  0  On-track wait window or fully complete.
  1  Blocked/error state.
  2  Action is due now.
EOF
}

auto_execute_due="false"
no_report="false"
fail_on_due_alert="false"
require_fresh_report="false"
max_report_lag_seconds=""
require_fresh_snapshot="false"
max_snapshot_lag_seconds=""
require_coherent_artifact_timestamps="false"
max_artifact_skew_seconds=""
require_coherent_embedded_timestamps="false"
max_embedded_timestamp_skew_seconds=""
require_recent_state="false"
max_state_age_seconds=""
require_coherent_manifest_time="false"
max_manifest_lag_seconds=""
max_manifest_filename_skew_seconds=""
require_recent_manifest="false"
max_manifest_age_seconds=""
reject_future_timestamps="false"
max_future_skew_seconds=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --auto-execute-due)
      auto_execute_due="true"
      shift
      ;;
    --no-report)
      no_report="true"
      shift
      ;;
    --fail-on-due-alert)
      fail_on_due_alert="true"
      shift
      ;;
    --require-fresh-report)
      require_fresh_report="true"
      shift
      ;;
    --max-report-lag-seconds)
      if [[ -z "${2:-}" ]]; then
        echo "[f1-ci] ERROR: --max-report-lag-seconds requires a value" >&2
        usage
        exit 1
      fi
      max_report_lag_seconds="$2"
      shift 2
      ;;
    --require-fresh-snapshot)
      require_fresh_snapshot="true"
      shift
      ;;
    --max-snapshot-lag-seconds)
      if [[ -z "${2:-}" ]]; then
        echo "[f1-ci] ERROR: --max-snapshot-lag-seconds requires a value" >&2
        usage
        exit 1
      fi
      max_snapshot_lag_seconds="$2"
      shift 2
      ;;
    --require-coherent-artifact-timestamps)
      require_coherent_artifact_timestamps="true"
      shift
      ;;
    --max-artifact-skew-seconds)
      if [[ -z "${2:-}" ]]; then
        echo "[f1-ci] ERROR: --max-artifact-skew-seconds requires a value" >&2
        usage
        exit 1
      fi
      max_artifact_skew_seconds="$2"
      shift 2
      ;;
    --require-coherent-embedded-timestamps)
      require_coherent_embedded_timestamps="true"
      shift
      ;;
    --max-embedded-timestamp-skew-seconds)
      if [[ -z "${2:-}" ]]; then
        echo "[f1-ci] ERROR: --max-embedded-timestamp-skew-seconds requires a value" >&2
        usage
        exit 1
      fi
      max_embedded_timestamp_skew_seconds="$2"
      shift 2
      ;;
    --require-recent-state)
      require_recent_state="true"
      shift
      ;;
    --max-state-age-seconds)
      if [[ -z "${2:-}" ]]; then
        echo "[f1-ci] ERROR: --max-state-age-seconds requires a value" >&2
        usage
        exit 1
      fi
      max_state_age_seconds="$2"
      shift 2
      ;;
    --require-coherent-manifest-time)
      require_coherent_manifest_time="true"
      shift
      ;;
    --max-manifest-lag-seconds)
      if [[ -z "${2:-}" ]]; then
        echo "[f1-ci] ERROR: --max-manifest-lag-seconds requires a value" >&2
        usage
        exit 1
      fi
      max_manifest_lag_seconds="$2"
      shift 2
      ;;
    --max-manifest-filename-skew-seconds)
      if [[ -z "${2:-}" ]]; then
        echo "[f1-ci] ERROR: --max-manifest-filename-skew-seconds requires a value" >&2
        usage
        exit 1
      fi
      max_manifest_filename_skew_seconds="$2"
      shift 2
      ;;
    --require-recent-manifest)
      require_recent_manifest="true"
      shift
      ;;
    --max-manifest-age-seconds)
      if [[ -z "${2:-}" ]]; then
        echo "[f1-ci] ERROR: --max-manifest-age-seconds requires a value" >&2
        usage
        exit 1
      fi
      max_manifest_age_seconds="$2"
      shift 2
      ;;
    --reject-future-timestamps)
      reject_future_timestamps="true"
      shift
      ;;
    --max-future-skew-seconds)
      if [[ -z "${2:-}" ]]; then
        echo "[f1-ci] ERROR: --max-future-skew-seconds requires a value" >&2
        usage
        exit 1
      fi
      max_future_skew_seconds="$2"
      shift 2
      ;;
    --strict-all)
      fail_on_due_alert="true"
      require_fresh_report="true"
      require_fresh_snapshot="true"
      require_coherent_artifact_timestamps="true"
      require_coherent_embedded_timestamps="true"
      require_recent_state="true"
      require_coherent_manifest_time="true"
      require_recent_manifest="true"
      reject_future_timestamps="true"
      max_report_lag_seconds="86400"
      max_snapshot_lag_seconds="86400"
      max_artifact_skew_seconds="300"
      max_embedded_timestamp_skew_seconds="5"
      max_state_age_seconds="900"
      max_manifest_lag_seconds="300"
      max_manifest_filename_skew_seconds="300"
      max_manifest_age_seconds="900"
      max_future_skew_seconds="30"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[f1-ci] ERROR: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

daily_args=()
if [[ "${auto_execute_due}" == "true" ]]; then
  daily_args+=(--auto-execute-due)
fi
if [[ "${no_report}" == "true" ]]; then
  daily_args+=(--no-report)
fi

set +e
bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_daily_runner.sh" "${daily_args[@]}"
daily_rc=$?
set -e

echo "[f1-ci] daily_runner_rc=${daily_rc}"

set +e
due_output="$(bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_due_alert.sh" 2>&1)"
due_rc=$?
set -e

echo "[f1-ci] due_alert_rc=${due_rc}"
printf '%s\n' "${due_output}"

bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_state_export.sh"

bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_snapshot.sh"

# Publish latest from the freshly generated artifacts.
bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_publish_latest.sh"

bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_manifest.sh"

# Guard deterministic consumers.
verify_args=()
if [[ "${require_fresh_report}" == "true" ]]; then
  verify_args+=(--require-fresh-report)
fi
if [[ -n "${max_report_lag_seconds}" ]]; then
  verify_args+=(--max-report-lag-seconds "${max_report_lag_seconds}")
fi
if [[ "${require_fresh_snapshot}" == "true" ]]; then
  verify_args+=(--require-fresh-snapshot)
fi
if [[ -n "${max_snapshot_lag_seconds}" ]]; then
  verify_args+=(--max-snapshot-lag-seconds "${max_snapshot_lag_seconds}")
fi
if [[ "${require_coherent_artifact_timestamps}" == "true" ]]; then
  verify_args+=(--require-coherent-artifact-timestamps)
fi
if [[ -n "${max_artifact_skew_seconds}" ]]; then
  verify_args+=(--max-artifact-skew-seconds "${max_artifact_skew_seconds}")
fi
if [[ "${require_coherent_embedded_timestamps}" == "true" ]]; then
  verify_args+=(--require-coherent-embedded-timestamps)
fi
if [[ -n "${max_embedded_timestamp_skew_seconds}" ]]; then
  verify_args+=(--max-embedded-timestamp-skew-seconds "${max_embedded_timestamp_skew_seconds}")
fi
if [[ "${require_recent_state}" == "true" ]]; then
  verify_args+=(--require-recent-state)
fi
if [[ -n "${max_state_age_seconds}" ]]; then
  verify_args+=(--max-state-age-seconds "${max_state_age_seconds}")
fi
if [[ "${require_coherent_manifest_time}" == "true" ]]; then
  verify_args+=(--require-coherent-manifest-time)
fi
if [[ -n "${max_manifest_lag_seconds}" ]]; then
  verify_args+=(--max-manifest-lag-seconds "${max_manifest_lag_seconds}")
fi
if [[ -n "${max_manifest_filename_skew_seconds}" ]]; then
  verify_args+=(--max-manifest-filename-skew-seconds "${max_manifest_filename_skew_seconds}")
fi
if [[ "${require_recent_manifest}" == "true" ]]; then
  verify_args+=(--require-recent-manifest)
fi
if [[ -n "${max_manifest_age_seconds}" ]]; then
  verify_args+=(--max-manifest-age-seconds "${max_manifest_age_seconds}")
fi
if [[ "${reject_future_timestamps}" == "true" ]]; then
  verify_args+=(--reject-future-timestamps)
fi
if [[ -n "${max_future_skew_seconds}" ]]; then
  verify_args+=(--max-future-skew-seconds "${max_future_skew_seconds}")
fi
bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_verify_latest.sh" "${verify_args[@]}"

final_rc="${daily_rc}"
if [[ "${final_rc}" -eq 0 && "${fail_on_due_alert}" == "true" && "${due_rc}" -eq 2 ]]; then
  final_rc=2
fi

echo "[f1-ci] completed pipeline"
exit "${final_rc}"
