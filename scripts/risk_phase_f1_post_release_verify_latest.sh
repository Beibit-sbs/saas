#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACTS_DIR="${ROOT_DIR}/docs/runbooks/artifacts"

usage() {
  cat <<EOF
Usage:
  bash scripts/risk_phase_f1_post_release_verify_latest.sh [--require-fresh-report] [--max-report-lag-seconds N] [--require-fresh-snapshot] [--max-snapshot-lag-seconds N] [--require-coherent-artifact-timestamps] [--max-artifact-skew-seconds N] [--require-coherent-embedded-timestamps] [--max-embedded-timestamp-skew-seconds N] [--require-recent-state] [--max-state-age-seconds N] [--require-coherent-manifest-time] [--max-manifest-lag-seconds N] [--max-manifest-filename-skew-seconds N] [--require-recent-manifest] [--max-manifest-age-seconds N] [--reject-future-timestamps] [--max-future-skew-seconds N]

Checks:
  1) latest deterministic files exist
  2) latest deterministic files match newest timestamped artifacts
  3) expected schema keys exist in latest JSON/markdown outputs

Options:
  --require-fresh-report      Enforce max lag between newest state and newest report artifacts.
  --max-report-lag-seconds N  Max allowed report lag in seconds (default: 86400).
  --require-fresh-snapshot      Enforce max lag between newest state and newest snapshot artifacts.
  --max-snapshot-lag-seconds N  Max allowed snapshot lag in seconds (default: 86400).
  --require-coherent-artifact-timestamps  Enforce max skew between newest timestamped state/report/snapshot artifacts.
  --max-artifact-skew-seconds N  Max allowed skew between state/report/snapshot timestamps (default: 300).
  --require-coherent-embedded-timestamps  Enforce embedded generated/captured timestamps inside latest artifacts match filename timestamps.
  --max-embedded-timestamp-skew-seconds N  Max allowed skew between embedded timestamp and filename timestamp (default: 5).
  --require-recent-state      Enforce max wall-clock age of newest timestamped state artifact.
  --max-state-age-seconds N   Max allowed age for newest state artifact (default: 900).
  --require-coherent-manifest-time  Enforce generated_at_utc coherence against newest artifact timestamp.
  --max-manifest-lag-seconds N  Max allowed manifest generation lag vs newest artifact timestamp (default: 300).
  --max-manifest-filename-skew-seconds N  Max allowed skew between manifest filename timestamp and generated_at_utc (default: 300).
  --require-recent-manifest  Enforce max wall-clock age of newest timestamped manifest artifact.
  --max-manifest-age-seconds N  Max allowed wall-clock age for newest manifest artifact (default: 900).
  --reject-future-timestamps  Enforce that newest artifacts/manifest timestamps are not in the future.
  --max-future-skew-seconds N  Allowed positive skew into future (default: 30).
EOF
}

require_fresh_report="false"
max_report_lag_seconds="86400"
require_fresh_snapshot="false"
max_snapshot_lag_seconds="86400"
require_coherent_artifact_timestamps="false"
max_artifact_skew_seconds="300"
require_coherent_embedded_timestamps="false"
max_embedded_timestamp_skew_seconds="5"
require_recent_state="false"
max_state_age_seconds="900"
require_coherent_manifest_time="false"
max_manifest_lag_seconds="300"
max_manifest_filename_skew_seconds="300"
require_recent_manifest="false"
max_manifest_age_seconds="900"
reject_future_timestamps="false"
max_future_skew_seconds="30"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --require-fresh-report)
      require_fresh_report="true"
      shift
      ;;
    --max-report-lag-seconds)
      if [[ -z "${2:-}" ]]; then
        echo "[f1-verify-latest] ERROR: --max-report-lag-seconds requires a value" >&2
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
        echo "[f1-verify-latest] ERROR: --max-snapshot-lag-seconds requires a value" >&2
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
        echo "[f1-verify-latest] ERROR: --max-artifact-skew-seconds requires a value" >&2
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
        echo "[f1-verify-latest] ERROR: --max-embedded-timestamp-skew-seconds requires a value" >&2
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
        echo "[f1-verify-latest] ERROR: --max-state-age-seconds requires a value" >&2
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
        echo "[f1-verify-latest] ERROR: --max-manifest-lag-seconds requires a value" >&2
        exit 1
      fi
      max_manifest_lag_seconds="$2"
      shift 2
      ;;
    --max-manifest-filename-skew-seconds)
      if [[ -z "${2:-}" ]]; then
        echo "[f1-verify-latest] ERROR: --max-manifest-filename-skew-seconds requires a value" >&2
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
        echo "[f1-verify-latest] ERROR: --max-manifest-age-seconds requires a value" >&2
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
        echo "[f1-verify-latest] ERROR: --max-future-skew-seconds requires a value" >&2
        exit 1
      fi
      max_future_skew_seconds="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[f1-verify-latest] ERROR: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

state_latest="${ARTIFACTS_DIR}/f1_risk_post_release_state_latest.json"
report_latest="${ARTIFACTS_DIR}/f1_risk_post_release_daily_report_latest.md"
snapshot_latest="${ARTIFACTS_DIR}/f1_risk_post_release_snapshot_latest.md"
manifest_latest="${ARTIFACTS_DIR}/f1_risk_post_release_manifest_latest.json"

latest_state_ts="$(ls -1 "${ARTIFACTS_DIR}"/f1_risk_post_release_state_*.json 2>/dev/null | grep -v '_latest\.json$' | tail -n 1 || true)"
latest_report_ts="$(ls -1 "${ARTIFACTS_DIR}"/f1_risk_post_release_daily_report_*.md 2>/dev/null | grep -v '_latest\.md$' | tail -n 1 || true)"
latest_snapshot_ts="$(ls -1 "${ARTIFACTS_DIR}"/f1_risk_post_release_snapshot_*.md 2>/dev/null | grep -v '_latest\.md$' | tail -n 1 || true)"
latest_manifest_ts="$(ls -1 "${ARTIFACTS_DIR}"/f1_risk_post_release_manifest_*.json 2>/dev/null | grep -v '_latest\.json$' | tail -n 1 || true)"

require_nonempty_file() {
  local f="$1"
  if [[ ! -f "${f}" ]]; then
    echo "[f1-verify-latest] ERROR: missing file ${f}" >&2
    exit 1
  fi
  if [[ ! -s "${f}" ]]; then
    echo "[f1-verify-latest] ERROR: empty file ${f}" >&2
    exit 1
  fi
}

require_nonempty_file "${state_latest}"
require_nonempty_file "${report_latest}"
require_nonempty_file "${snapshot_latest}"
require_nonempty_file "${manifest_latest}"
require_nonempty_file "${latest_state_ts}"
require_nonempty_file "${latest_report_ts}"
require_nonempty_file "${latest_snapshot_ts}"
require_nonempty_file "${latest_manifest_ts}"

if [[ -z "${latest_state_ts}" || -z "${latest_report_ts}" || -z "${latest_snapshot_ts}" || -z "${latest_manifest_ts}" ]]; then
  echo "[f1-verify-latest] ERROR: missing timestamped source artifacts for comparison" >&2
  exit 1
fi

if ! cmp -s "${state_latest}" "${latest_state_ts}"; then
  echo "[f1-verify-latest] ERROR: state_latest does not match newest timestamped state artifact" >&2
  exit 1
fi
if ! cmp -s "${report_latest}" "${latest_report_ts}"; then
  echo "[f1-verify-latest] ERROR: daily_report_latest does not match newest timestamped report artifact" >&2
  exit 1
fi
if ! cmp -s "${snapshot_latest}" "${latest_snapshot_ts}"; then
  echo "[f1-verify-latest] ERROR: snapshot_latest does not match newest timestamped snapshot artifact" >&2
  exit 1
fi
if ! cmp -s "${manifest_latest}" "${latest_manifest_ts}"; then
  echo "[f1-verify-latest] ERROR: manifest_latest does not match newest timestamped manifest artifact" >&2
  exit 1
fi

extract_ts_token() {
  local file_path="$1"
  basename "${file_path}" | sed -E 's/.*_([0-9]{8}_[0-9]{6})\..*/\1/'
}

to_epoch_utc() {
  local stamp="$1"
  date -u -d "${stamp:0:4}-${stamp:4:2}-${stamp:6:2} ${stamp:9:2}:${stamp:11:2}:${stamp:13:2}" +%s
}

to_epoch_iso_utc() {
  local iso="$1"
  date -u -d "${iso}" +%s
}

if [[ "${require_fresh_report}" == "true" ]]; then
  state_stamp="$(extract_ts_token "${latest_state_ts}")"
  report_stamp="$(extract_ts_token "${latest_report_ts}")"

  if [[ ! "${max_report_lag_seconds}" =~ ^[0-9]+$ ]]; then
    echo "[f1-verify-latest] ERROR: --max-report-lag-seconds must be an integer" >&2
    exit 1
  fi

  if [[ ! "${state_stamp}" =~ ^[0-9]{8}_[0-9]{6}$ || ! "${report_stamp}" =~ ^[0-9]{8}_[0-9]{6}$ ]]; then
    echo "[f1-verify-latest] ERROR: unable to parse timestamps for freshness check" >&2
    exit 1
  fi

  state_epoch="$(to_epoch_utc "${state_stamp}")"
  report_epoch="$(to_epoch_utc "${report_stamp}")"
  lag_seconds=$((state_epoch - report_epoch))

  if (( lag_seconds < 0 )); then
    lag_seconds=0
  fi

  if (( lag_seconds > max_report_lag_seconds )); then
    echo "[f1-verify-latest] ERROR: daily_report_latest is stale vs newest state (lag=${lag_seconds}s > ${max_report_lag_seconds}s)" >&2
    exit 1
  fi

  echo "[f1-verify-latest] report_freshness_lag_seconds=${lag_seconds} (threshold=${max_report_lag_seconds})"
fi

if [[ "${require_fresh_snapshot}" == "true" ]]; then
  state_stamp="$(extract_ts_token "${latest_state_ts}")"
  snapshot_stamp="$(extract_ts_token "${latest_snapshot_ts}")"

  if [[ ! "${max_snapshot_lag_seconds}" =~ ^[0-9]+$ ]]; then
    echo "[f1-verify-latest] ERROR: --max-snapshot-lag-seconds must be an integer" >&2
    exit 1
  fi

  if [[ ! "${state_stamp}" =~ ^[0-9]{8}_[0-9]{6}$ || ! "${snapshot_stamp}" =~ ^[0-9]{8}_[0-9]{6}$ ]]; then
    echo "[f1-verify-latest] ERROR: unable to parse timestamps for snapshot freshness check" >&2
    exit 1
  fi

  state_epoch="$(to_epoch_utc "${state_stamp}")"
  snapshot_epoch="$(to_epoch_utc "${snapshot_stamp}")"
  lag_seconds=$((state_epoch - snapshot_epoch))

  if (( lag_seconds < 0 )); then
    lag_seconds=0
  fi

  if (( lag_seconds > max_snapshot_lag_seconds )); then
    echo "[f1-verify-latest] ERROR: snapshot_latest is stale vs newest state (lag=${lag_seconds}s > ${max_snapshot_lag_seconds}s)" >&2
    exit 1
  fi

  echo "[f1-verify-latest] snapshot_freshness_lag_seconds=${lag_seconds} (threshold=${max_snapshot_lag_seconds})"
fi

if [[ "${require_coherent_artifact_timestamps}" == "true" ]]; then
  state_stamp="$(extract_ts_token "${latest_state_ts}")"
  report_stamp="$(extract_ts_token "${latest_report_ts}")"
  snapshot_stamp="$(extract_ts_token "${latest_snapshot_ts}")"

  if [[ ! "${max_artifact_skew_seconds}" =~ ^[0-9]+$ ]]; then
    echo "[f1-verify-latest] ERROR: --max-artifact-skew-seconds must be an integer" >&2
    exit 1
  fi

  if [[ ! "${state_stamp}" =~ ^[0-9]{8}_[0-9]{6}$ || ! "${report_stamp}" =~ ^[0-9]{8}_[0-9]{6}$ || ! "${snapshot_stamp}" =~ ^[0-9]{8}_[0-9]{6}$ ]]; then
    echo "[f1-verify-latest] ERROR: unable to parse timestamps for coherence check" >&2
    exit 1
  fi

  state_epoch="$(to_epoch_utc "${state_stamp}")"
  report_epoch="$(to_epoch_utc "${report_stamp}")"
  snapshot_epoch="$(to_epoch_utc "${snapshot_stamp}")"

  min_epoch="${state_epoch}"
  max_epoch="${state_epoch}"
  for epoch in "${report_epoch}" "${snapshot_epoch}"; do
    if (( epoch < min_epoch )); then
      min_epoch="${epoch}"
    fi
    if (( epoch > max_epoch )); then
      max_epoch="${epoch}"
    fi
  done

  skew_seconds=$((max_epoch - min_epoch))
  if (( skew_seconds > max_artifact_skew_seconds )); then
    echo "[f1-verify-latest] ERROR: artifact timestamp skew too high (skew=${skew_seconds}s > ${max_artifact_skew_seconds}s)" >&2
    exit 1
  fi

  echo "[f1-verify-latest] artifact_timestamp_skew_seconds=${skew_seconds} (threshold=${max_artifact_skew_seconds})"
fi

extract_markdown_frontmatter_value() {
  local label="$1"
  local file="$2"
  awk -F': ' -v label="- ${label}" '$1 == label {print $2; exit}' "${file}"
}

count_markdown_frontmatter_label_occurrences() {
  local label="$1"
  local file="$2"
  awk -F': ' -v label="- ${label}" '$1 == label { count++ } END { print count + 0 }' "${file}"
}

extract_markdown_section_exit_code() {
  local heading="$1"
  local file="$2"
  awk -v heading="## ${heading}" '
    $0 == heading { in_section=1; next }
    in_section && /^## / { in_section=0 }
    in_section && $0 ~ /^- Exit code: / {
      sub(/^- Exit code: /, "", $0)
      print $0
      exit
    }
  ' "${file}"
}

extract_markdown_section_kv() {
  local heading="$1"
  local key="$2"
  local file="$3"
  awk -v heading="## ${heading}" -v key="${key}" '
    $0 == heading { in_section=1; next }
    in_section && /^## / { in_section=0 }
    in_section && $0 ~ ("^" key "=") {
      sub("^" key "=", "", $0)
      print $0
      exit
    }
  ' "${file}"
}

extract_markdown_heading_line() {
  local heading="$1"
  local file="$2"
  awk -v heading="## ${heading}" '
    $0 == heading {
      print NR
      exit
    }
  ' "${file}"
}

count_markdown_heading_occurrences() {
  local heading="$1"
  local file="$2"
  awk -v heading="## ${heading}" '
    $0 == heading { count++ }
    END { print count + 0 }
  ' "${file}"
}

section_has_text_code_fence() {
  local heading="$1"
  local file="$2"
  awk -v heading="## ${heading}" '
    $0 == heading { in_section=1; next }
    in_section && /^## / { in_section=0 }
    in_section && $0 == "```text" { print "yes"; exit }
  ' "${file}"
}

section_has_closed_text_code_fence() {
  local heading="$1"
  local file="$2"
  awk -v heading="## ${heading}" '
    $0 == heading { in_section=1; next }
    in_section && /^## / { in_section=0 }
    in_section && $0 == "```text" { opened=1; next }
    in_section && opened && $0 == "```" { print "yes"; exit }
  ' "${file}"
}

count_section_exact_line_occurrences() {
  local heading="$1"
  local exact_line="$2"
  local file="$3"
  awk -v heading="## ${heading}" -v exact_line="${exact_line}" '
    $0 == heading { in_section=1; next }
    in_section && /^## / { in_section=0 }
    in_section && $0 == exact_line { count++ }
    END { print count + 0 }
  ' "${file}"
}

count_section_line_prefix_occurrences() {
  local heading="$1"
  local prefix="$2"
  local file="$3"
  awk -v heading="## ${heading}" -v prefix="${prefix}" '
    $0 == heading { in_section=1; next }
    in_section && /^## / { in_section=0 }
    in_section && index($0, prefix) == 1 { count++ }
    END { print count + 0 }
  ' "${file}"
}

require_section_prefix_once() {
  local heading="$1"
  local prefix="$2"
  local file="$3"
  local context_label="$4"
  local count
  count="$(count_section_line_prefix_occurrences "${heading}" "${prefix}" "${file}")"
  if [[ "${count}" != "1" ]]; then
    echo "[f1-verify-latest] ERROR: ${context_label} must contain exactly one '${prefix}' line" >&2
    exit 1
  fi
}

if [[ "${require_coherent_embedded_timestamps}" == "true" ]]; then
  if [[ ! "${max_embedded_timestamp_skew_seconds}" =~ ^[0-9]+$ ]]; then
    echo "[f1-verify-latest] ERROR: --max-embedded-timestamp-skew-seconds must be an integer" >&2
    exit 1
  fi

  state_stamp="$(extract_ts_token "${latest_state_ts}")"
  report_stamp="$(extract_ts_token "${latest_report_ts}")"
  snapshot_stamp="$(extract_ts_token "${latest_snapshot_ts}")"

  state_embedded_utc="$(awk 'index($0, "\"generated_at_utc\"") > 0 { n=split($0, parts, "\""); if (n >= 4) { print parts[4] }; exit }' "${state_latest}")"
  report_embedded_utc="$(extract_markdown_frontmatter_value "Generated at (UTC)" "${report_latest}")"
  snapshot_embedded_utc="$(extract_markdown_frontmatter_value "Captured at (UTC)" "${snapshot_latest}")"

  if [[ -z "${state_embedded_utc}" || -z "${report_embedded_utc}" || -z "${snapshot_embedded_utc}" ]]; then
    echo "[f1-verify-latest] ERROR: unable to extract embedded timestamps from latest artifacts" >&2
    exit 1
  fi
  if [[ ! "${state_embedded_utc}" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ || ! "${report_embedded_utc}" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ || ! "${snapshot_embedded_utc}" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ ]]; then
    echo "[f1-verify-latest] ERROR: embedded timestamp format is invalid in latest artifacts" >&2
    exit 1
  fi

  state_file_epoch="$(to_epoch_utc "${state_stamp}")"
  report_file_epoch="$(to_epoch_utc "${report_stamp}")"
  snapshot_file_epoch="$(to_epoch_utc "${snapshot_stamp}")"
  state_embedded_epoch="$(to_epoch_iso_utc "${state_embedded_utc}")"
  report_embedded_epoch="$(to_epoch_iso_utc "${report_embedded_utc}")"
  snapshot_embedded_epoch="$(to_epoch_iso_utc "${snapshot_embedded_utc}")"

  state_embedded_skew_seconds=$((state_embedded_epoch - state_file_epoch))
  report_embedded_skew_seconds=$((report_embedded_epoch - report_file_epoch))
  snapshot_embedded_skew_seconds=$((snapshot_embedded_epoch - snapshot_file_epoch))

  for var_name in state_embedded_skew_seconds report_embedded_skew_seconds snapshot_embedded_skew_seconds; do
    skew_value="${!var_name}"
    if (( skew_value < 0 )); then
      printf -v "${var_name}" '%s' "$(( -skew_value ))"
    fi
  done

  max_embedded_observed_skew="${state_embedded_skew_seconds}"
  for skew in "${report_embedded_skew_seconds}" "${snapshot_embedded_skew_seconds}"; do
    if (( skew > max_embedded_observed_skew )); then
      max_embedded_observed_skew="${skew}"
    fi
  done

  if (( max_embedded_observed_skew > max_embedded_timestamp_skew_seconds )); then
    echo "[f1-verify-latest] ERROR: embedded artifact timestamp skew too high (observed=${max_embedded_observed_skew}s > ${max_embedded_timestamp_skew_seconds}s)" >&2
    exit 1
  fi

  echo "[f1-verify-latest] embedded_timestamp_skew_seconds=${max_embedded_observed_skew} (threshold=${max_embedded_timestamp_skew_seconds})"
fi

if [[ "${require_recent_state}" == "true" ]]; then
  state_stamp="$(extract_ts_token "${latest_state_ts}")"

  if [[ ! "${max_state_age_seconds}" =~ ^[0-9]+$ ]]; then
    echo "[f1-verify-latest] ERROR: --max-state-age-seconds must be an integer" >&2
    exit 1
  fi

  if [[ ! "${state_stamp}" =~ ^[0-9]{8}_[0-9]{6}$ ]]; then
    echo "[f1-verify-latest] ERROR: unable to parse state timestamp for recency check" >&2
    exit 1
  fi

  now_epoch="$(date -u +%s)"
  state_epoch="$(to_epoch_utc "${state_stamp}")"
  state_age_seconds=$((now_epoch - state_epoch))

  if (( state_age_seconds < 0 )); then
    state_age_seconds=0
  fi

  if (( state_age_seconds > max_state_age_seconds )); then
    echo "[f1-verify-latest] ERROR: newest state artifact is too old (age=${state_age_seconds}s > ${max_state_age_seconds}s)" >&2
    exit 1
  fi

  echo "[f1-verify-latest] state_age_seconds=${state_age_seconds} (threshold=${max_state_age_seconds})"
fi

if [[ "${require_recent_manifest}" == "true" ]]; then
  manifest_stamp="$(extract_ts_token "${latest_manifest_ts}")"

  if [[ ! "${max_manifest_age_seconds}" =~ ^[0-9]+$ ]]; then
    echo "[f1-verify-latest] ERROR: --max-manifest-age-seconds must be an integer" >&2
    exit 1
  fi

  if [[ ! "${manifest_stamp}" =~ ^[0-9]{8}_[0-9]{6}$ ]]; then
    echo "[f1-verify-latest] ERROR: unable to parse manifest timestamp for recency check" >&2
    exit 1
  fi

  now_epoch="$(date -u +%s)"
  manifest_epoch="$(to_epoch_utc "${manifest_stamp}")"
  manifest_age_seconds=$((now_epoch - manifest_epoch))

  if (( manifest_age_seconds < 0 )); then
    manifest_age_seconds=0
  fi

  if (( manifest_age_seconds > max_manifest_age_seconds )); then
    echo "[f1-verify-latest] ERROR: newest manifest artifact is too old (age=${manifest_age_seconds}s > ${max_manifest_age_seconds}s)" >&2
    exit 1
  fi

  echo "[f1-verify-latest] manifest_age_seconds=${manifest_age_seconds} (threshold=${max_manifest_age_seconds})"
fi

require_key() {
  local key="$1"
  local file="$2"
  if ! grep -F -q -- "${key}" "${file}"; then
    echo "[f1-verify-latest] ERROR: missing key '${key}' in ${file}" >&2
    exit 1
  fi
}

require_key '"f1_9_status"' "${state_latest}"
require_key '"today_utc"' "${state_latest}"
require_key '"window"' "${state_latest}"
require_key '"next_action"' "${state_latest}"
require_key '"daily_health"' "${state_latest}"
require_key '"due_alert"' "${state_latest}"
require_key '"alert_level"' "${state_latest}"

require_key 'F1.9_DAILY_HEALTH=' "${report_latest}"
require_key 'NEXT_ACTION=' "${report_latest}"
require_key 'F1.9_DUE_ALERT=' "${report_latest}"
require_key 'ALERT_LEVEL=' "${report_latest}"

require_key 'F1.9_STATUS=' "${snapshot_latest}"
require_key 'F1.9_GATE=' "${snapshot_latest}"
require_key 'F1.9_DUE_ALERT=' "${snapshot_latest}"
require_key 'ALERT_LEVEL=' "${snapshot_latest}"
require_key '"generated_at_utc"' "${manifest_latest}"
require_key '"artifacts"' "${manifest_latest}"
require_key '"source_artifacts"' "${manifest_latest}"

if [[ "$(count_markdown_frontmatter_label_occurrences "Generated at (UTC)" "${report_latest}")" != "1" || "$(count_markdown_frontmatter_label_occurrences "Daily check exit code" "${report_latest}")" != "1" || "$(count_markdown_frontmatter_label_occurrences "Due alert exit code" "${report_latest}")" != "1" ]]; then
  echo "[f1-verify-latest] ERROR: daily_report_latest frontmatter labels must appear exactly once" >&2
  exit 1
fi
if [[ "$(count_markdown_frontmatter_label_occurrences "Captured at (UTC)" "${snapshot_latest}")" != "1" ]]; then
  echo "[f1-verify-latest] ERROR: snapshot_latest captured-at frontmatter label must appear exactly once" >&2
  exit 1
fi

report_daily_line="$(extract_markdown_heading_line "Daily Check Output" "${report_latest}")"
report_due_line="$(extract_markdown_heading_line "Due Alert Output" "${report_latest}")"
report_interpretation_line="$(extract_markdown_heading_line "Interpretation" "${report_latest}")"
report_daily_count="$(count_markdown_heading_occurrences "Daily Check Output" "${report_latest}")"
report_due_count="$(count_markdown_heading_occurrences "Due Alert Output" "${report_latest}")"
report_interpretation_count="$(count_markdown_heading_occurrences "Interpretation" "${report_latest}")"

if [[ -z "${report_daily_line}" || -z "${report_due_line}" || -z "${report_interpretation_line}" ]]; then
  echo "[f1-verify-latest] ERROR: daily_report_latest is missing required sections" >&2
  exit 1
fi
if [[ "${report_daily_count}" != "1" || "${report_due_count}" != "1" || "${report_interpretation_count}" != "1" ]]; then
  echo "[f1-verify-latest] ERROR: daily_report_latest contains duplicate required sections" >&2
  exit 1
fi
if (( report_daily_line >= report_due_line || report_due_line >= report_interpretation_line )); then
  echo "[f1-verify-latest] ERROR: daily_report_latest section order is invalid (expected Daily Check Output -> Due Alert Output -> Interpretation)" >&2
  exit 1
fi
if [[ "$(section_has_text_code_fence "Daily Check Output" "${report_latest}")" != "yes" || "$(section_has_text_code_fence "Due Alert Output" "${report_latest}")" != "yes" ]]; then
  echo "[f1-verify-latest] ERROR: daily_report_latest required sections must contain ```text fenced blocks" >&2
  exit 1
fi
if [[ "$(section_has_closed_text_code_fence "Daily Check Output" "${report_latest}")" != "yes" || "$(section_has_closed_text_code_fence "Due Alert Output" "${report_latest}")" != "yes" ]]; then
  echo "[f1-verify-latest] ERROR: daily_report_latest required sections must contain properly closed ```text fenced blocks" >&2
  exit 1
fi
fence_open_line='```text'
fence_close_line='```'
if [[ "$(count_section_exact_line_occurrences "Daily Check Output" "${fence_open_line}" "${report_latest}")" != "1" || "$(count_section_exact_line_occurrences "Due Alert Output" "${fence_open_line}" "${report_latest}")" != "1" || "$(count_section_exact_line_occurrences "Daily Check Output" "${fence_close_line}" "${report_latest}")" != "1" || "$(count_section_exact_line_occurrences "Due Alert Output" "${fence_close_line}" "${report_latest}")" != "1" ]]; then
  echo "[f1-verify-latest] ERROR: daily_report_latest required sections must contain exactly one fenced payload block" >&2
  exit 1
fi

snapshot_status_line="$(extract_markdown_heading_line "Status Output" "${snapshot_latest}")"
snapshot_gate_line="$(extract_markdown_heading_line "Gate Output" "${snapshot_latest}")"
snapshot_due_line="$(extract_markdown_heading_line "Due Alert Output" "${snapshot_latest}")"
snapshot_notes_line="$(extract_markdown_heading_line "Notes" "${snapshot_latest}")"
snapshot_status_count="$(count_markdown_heading_occurrences "Status Output" "${snapshot_latest}")"
snapshot_gate_count="$(count_markdown_heading_occurrences "Gate Output" "${snapshot_latest}")"
snapshot_due_count="$(count_markdown_heading_occurrences "Due Alert Output" "${snapshot_latest}")"
snapshot_notes_count="$(count_markdown_heading_occurrences "Notes" "${snapshot_latest}")"

if [[ -z "${snapshot_status_line}" || -z "${snapshot_gate_line}" || -z "${snapshot_due_line}" || -z "${snapshot_notes_line}" ]]; then
  echo "[f1-verify-latest] ERROR: snapshot_latest is missing required sections" >&2
  exit 1
fi
if [[ "${snapshot_status_count}" != "1" || "${snapshot_gate_count}" != "1" || "${snapshot_due_count}" != "1" || "${snapshot_notes_count}" != "1" ]]; then
  echo "[f1-verify-latest] ERROR: snapshot_latest contains duplicate required sections" >&2
  exit 1
fi
if (( snapshot_status_line >= snapshot_gate_line || snapshot_gate_line >= snapshot_due_line || snapshot_due_line >= snapshot_notes_line )); then
  echo "[f1-verify-latest] ERROR: snapshot_latest section order is invalid (expected Status Output -> Gate Output -> Due Alert Output -> Notes)" >&2
  exit 1
fi
if [[ "$(section_has_text_code_fence "Status Output" "${snapshot_latest}")" != "yes" || "$(section_has_text_code_fence "Gate Output" "${snapshot_latest}")" != "yes" || "$(section_has_text_code_fence "Due Alert Output" "${snapshot_latest}")" != "yes" ]]; then
  echo "[f1-verify-latest] ERROR: snapshot_latest required sections must contain ```text fenced blocks" >&2
  exit 1
fi
if [[ "$(section_has_closed_text_code_fence "Status Output" "${snapshot_latest}")" != "yes" || "$(section_has_closed_text_code_fence "Gate Output" "${snapshot_latest}")" != "yes" || "$(section_has_closed_text_code_fence "Due Alert Output" "${snapshot_latest}")" != "yes" ]]; then
  echo "[f1-verify-latest] ERROR: snapshot_latest required sections must contain properly closed ```text fenced blocks" >&2
  exit 1
fi
if [[ "$(count_section_exact_line_occurrences "Status Output" "${fence_open_line}" "${snapshot_latest}")" != "1" || "$(count_section_exact_line_occurrences "Gate Output" "${fence_open_line}" "${snapshot_latest}")" != "1" || "$(count_section_exact_line_occurrences "Due Alert Output" "${fence_open_line}" "${snapshot_latest}")" != "1" || "$(count_section_exact_line_occurrences "Status Output" "${fence_close_line}" "${snapshot_latest}")" != "1" || "$(count_section_exact_line_occurrences "Gate Output" "${fence_close_line}" "${snapshot_latest}")" != "1" || "$(count_section_exact_line_occurrences "Due Alert Output" "${fence_close_line}" "${snapshot_latest}")" != "1" ]]; then
  echo "[f1-verify-latest] ERROR: snapshot_latest required sections must contain exactly one fenced payload block" >&2
  exit 1
fi
if [[ "$(count_section_line_prefix_occurrences "Gate Output" "- Exit code: " "${snapshot_latest}")" != "1" || "$(count_section_line_prefix_occurrences "Due Alert Output" "- Exit code: " "${snapshot_latest}")" != "1" ]]; then
  echo "[f1-verify-latest] ERROR: snapshot_latest exit-code lines must appear exactly once in Gate/Due sections" >&2
  exit 1
fi

require_section_prefix_once "Daily Check Output" "F1.9_DAILY_HEALTH=" "${report_latest}" "daily_report_latest Daily Check Output"
require_section_prefix_once "Daily Check Output" "F1.9_STATUS=" "${report_latest}" "daily_report_latest Daily Check Output"
require_section_prefix_once "Daily Check Output" "WINDOW=" "${report_latest}" "daily_report_latest Daily Check Output"
require_section_prefix_once "Daily Check Output" "NEXT_ACTION=" "${report_latest}" "daily_report_latest Daily Check Output"
require_section_prefix_once "Daily Check Output" "GATE=" "${report_latest}" "daily_report_latest Daily Check Output"
require_section_prefix_once "Daily Check Output" "EXIT_CODE_HINT=" "${report_latest}" "daily_report_latest Daily Check Output"

require_section_prefix_once "Due Alert Output" "F1.9_DUE_ALERT=" "${report_latest}" "daily_report_latest Due Alert Output"
require_section_prefix_once "Due Alert Output" "NEXT_ACTION=" "${report_latest}" "daily_report_latest Due Alert Output"
require_section_prefix_once "Due Alert Output" "ALERT_LEVEL=" "${report_latest}" "daily_report_latest Due Alert Output"
require_section_prefix_once "Due Alert Output" "ALERT_ACTION=" "${report_latest}" "daily_report_latest Due Alert Output"

require_section_prefix_once "Status Output" "F1.9_STATUS=" "${snapshot_latest}" "snapshot_latest Status Output"
require_section_prefix_once "Status Output" "TODAY_UTC=" "${snapshot_latest}" "snapshot_latest Status Output"
require_section_prefix_once "Status Output" "DAY0_BASELINE=" "${snapshot_latest}" "snapshot_latest Status Output"
require_section_prefix_once "Status Output" "DAY7_DUE=" "${snapshot_latest}" "snapshot_latest Status Output"
require_section_prefix_once "Status Output" "DAY14_DUE=" "${snapshot_latest}" "snapshot_latest Status Output"
require_section_prefix_once "Status Output" "DAY30_DUE=" "${snapshot_latest}" "snapshot_latest Status Output"
require_section_prefix_once "Status Output" "DAY7_ARTIFACT=" "${snapshot_latest}" "snapshot_latest Status Output"
require_section_prefix_once "Status Output" "DAY14_ARTIFACT=" "${snapshot_latest}" "snapshot_latest Status Output"
require_section_prefix_once "Status Output" "DAY30_ARTIFACT=" "${snapshot_latest}" "snapshot_latest Status Output"
require_section_prefix_once "Status Output" "NEXT_ACTION=" "${snapshot_latest}" "snapshot_latest Status Output"
require_section_prefix_once "Status Output" "WINDOW=" "${snapshot_latest}" "snapshot_latest Status Output"

require_section_prefix_once "Gate Output" "F1.9_GATE=" "${snapshot_latest}" "snapshot_latest Gate Output"
require_section_prefix_once "Gate Output" "TODAY_UTC=" "${snapshot_latest}" "snapshot_latest Gate Output"

require_section_prefix_once "Due Alert Output" "F1.9_DUE_ALERT=" "${snapshot_latest}" "snapshot_latest Due Alert Output"
require_section_prefix_once "Due Alert Output" "NEXT_ACTION=" "${snapshot_latest}" "snapshot_latest Due Alert Output"
require_section_prefix_once "Due Alert Output" "ALERT_LEVEL=" "${snapshot_latest}" "snapshot_latest Due Alert Output"
require_section_prefix_once "Due Alert Output" "ALERT_ACTION=" "${snapshot_latest}" "snapshot_latest Due Alert Output"

state_sha="$(sha256sum "${state_latest}" | awk '{print $1}')"
report_sha="$(sha256sum "${report_latest}" | awk '{print $1}')"
snapshot_sha="$(sha256sum "${snapshot_latest}" | awk '{print $1}')"

extract_manifest_field() {
  local section="$1"
  local field="$2"
  local file="$3"
  awk -v section="${section}" -v field="${field}" '
    BEGIN { in_section=0 }
    index($0, "\"" section "\"") > 0 && index($0, "{") > 0 { in_section=1; next }
    in_section && index($0, "\"" field "\"") > 0 {
      n=split($0, parts, "\"")
      if (n >= 4) {
        print parts[4]
      }
      exit
    }
    in_section && $0 ~ /^[[:space:]]*\}[[:space:]]*,?[[:space:]]*$/ { in_section=0 }
  ' "${file}"
}

extract_json_string_field() {
  local key="$1"
  local file="$2"
  awk -v key="\"${key}\"" '
    index($0, key) > 0 {
      n=split($0, parts, "\"")
      if (n >= 4) {
        print parts[4]
      }
      exit
    }
  ' "${file}"
}

extract_nested_json_string_field() {
  local object="$1"
  local key="$2"
  local file="$3"
  awk -v object="\"${object}\"" -v key="\"${key}\"" '
    BEGIN { in_object=0 }
    index($0, object) > 0 && index($0, "{") > 0 { in_object=1; next }
    in_object && index($0, key) > 0 {
      n=split($0, parts, "\"")
      if (n >= 4) {
        print parts[4]
      }
      exit
    }
    in_object && $0 ~ /^[[:space:]]*\}[[:space:]]*,?[[:space:]]*$/ { in_object=0 }
  ' "${file}"
}

extract_manifest_numeric_field() {
  local section="$1"
  local field="$2"
  local file="$3"
  awk -v section="${section}" -v field="${field}" '
    BEGIN { in_section=0 }
    index($0, "\"" section "\"") > 0 && index($0, "{") > 0 { in_section=1; next }
    in_section && index($0, "\"" field "\"") > 0 {
      line=$0
      sub(/^.*:[[:space:]]*/, "", line)
      sub(/[[:space:]]*,?[[:space:]]*$/, "", line)
      print line
      exit
    }
    in_section && $0 ~ /^[[:space:]]*\}[[:space:]]*,?[[:space:]]*$/ { in_section=0 }
  ' "${file}"
}

extract_nested_json_numeric_field() {
  local object="$1"
  local key="$2"
  local file="$3"
  awk -v object="\"${object}\"" -v key="\"${key}\"" '
    BEGIN { in_object=0 }
    index($0, object) > 0 && index($0, "{") > 0 { in_object=1; next }
    in_object && index($0, key) > 0 {
      line=$0
      sub(/^.*:[[:space:]]*/, "", line)
      sub(/[[:space:]]*,?[[:space:]]*$/, "", line)
      print line
      exit
    }
    in_object && $0 ~ /^[[:space:]]*\}[[:space:]]*,?[[:space:]]*$/ { in_object=0 }
  ' "${file}"
}

manifest_state_path="$(extract_manifest_field "state_latest" "path" "${manifest_latest}")"
manifest_report_path="$(extract_manifest_field "daily_report_latest" "path" "${manifest_latest}")"
manifest_snapshot_path="$(extract_manifest_field "snapshot_latest" "path" "${manifest_latest}")"

manifest_state_sha="$(extract_manifest_field "state_latest" "sha256" "${manifest_latest}")"
manifest_report_sha="$(extract_manifest_field "daily_report_latest" "sha256" "${manifest_latest}")"
manifest_snapshot_sha="$(extract_manifest_field "snapshot_latest" "sha256" "${manifest_latest}")"
manifest_state_size="$(extract_manifest_numeric_field "state_latest" "size_bytes" "${manifest_latest}")"
manifest_report_size="$(extract_manifest_numeric_field "daily_report_latest" "size_bytes" "${manifest_latest}")"
manifest_snapshot_size="$(extract_manifest_numeric_field "snapshot_latest" "size_bytes" "${manifest_latest}")"

manifest_source_state_file="$(extract_manifest_field "state" "file" "${manifest_latest}")"
manifest_source_report_file="$(extract_manifest_field "daily_report" "file" "${manifest_latest}")"
manifest_source_snapshot_file="$(extract_manifest_field "snapshot" "file" "${manifest_latest}")"
manifest_source_state_sha="$(extract_manifest_field "state" "sha256" "${manifest_latest}")"
manifest_source_report_sha="$(extract_manifest_field "daily_report" "sha256" "${manifest_latest}")"
manifest_source_snapshot_sha="$(extract_manifest_field "snapshot" "sha256" "${manifest_latest}")"
manifest_source_state_size="$(extract_manifest_numeric_field "state" "size_bytes" "${manifest_latest}")"
manifest_source_report_size="$(extract_manifest_numeric_field "daily_report" "size_bytes" "${manifest_latest}")"
manifest_source_snapshot_size="$(extract_manifest_numeric_field "snapshot" "size_bytes" "${manifest_latest}")"
manifest_generated_at_utc="$(extract_json_string_field "generated_at_utc" "${manifest_latest}")"

if [[ -z "${manifest_state_path}" || -z "${manifest_report_path}" || -z "${manifest_snapshot_path}" ]]; then
  echo "[f1-verify-latest] ERROR: manifest is missing expected artifact path fields" >&2
  exit 1
fi

if [[ -z "${manifest_state_sha}" || -z "${manifest_report_sha}" || -z "${manifest_snapshot_sha}" ]]; then
  echo "[f1-verify-latest] ERROR: manifest is missing expected SHA256 fields" >&2
  exit 1
fi
if [[ -z "${manifest_state_size}" || -z "${manifest_report_size}" || -z "${manifest_snapshot_size}" ]]; then
  echo "[f1-verify-latest] ERROR: manifest is missing expected latest artifact size fields" >&2
  exit 1
fi

if [[ -z "${manifest_source_state_file}" || -z "${manifest_source_report_file}" || -z "${manifest_source_snapshot_file}" ]]; then
  echo "[f1-verify-latest] ERROR: manifest is missing source artifact provenance fields" >&2
  exit 1
fi
if [[ -z "${manifest_source_state_sha}" || -z "${manifest_source_report_sha}" || -z "${manifest_source_snapshot_sha}" ]]; then
  echo "[f1-verify-latest] ERROR: manifest is missing source artifact provenance SHA256 fields" >&2
  exit 1
fi
if [[ -z "${manifest_source_state_size}" || -z "${manifest_source_report_size}" || -z "${manifest_source_snapshot_size}" ]]; then
  echo "[f1-verify-latest] ERROR: manifest is missing source artifact provenance size fields" >&2
  exit 1
fi
if [[ -z "${manifest_generated_at_utc}" ]]; then
  echo "[f1-verify-latest] ERROR: unable to extract generated_at_utc from manifest_latest" >&2
  exit 1
fi
if [[ ! "${manifest_generated_at_utc}" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ ]]; then
  echo "[f1-verify-latest] ERROR: generated_at_utc format is invalid in manifest_latest" >&2
  exit 1
fi

if [[ "${manifest_state_path}" != "docs/runbooks/artifacts/f1_risk_post_release_state_latest.json" ]]; then
  echo "[f1-verify-latest] ERROR: unexpected manifest path for state_latest" >&2
  exit 1
fi
if [[ "${manifest_report_path}" != "docs/runbooks/artifacts/f1_risk_post_release_daily_report_latest.md" ]]; then
  echo "[f1-verify-latest] ERROR: unexpected manifest path for daily_report_latest" >&2
  exit 1
fi
if [[ "${manifest_snapshot_path}" != "docs/runbooks/artifacts/f1_risk_post_release_snapshot_latest.md" ]]; then
  echo "[f1-verify-latest] ERROR: unexpected manifest path for snapshot_latest" >&2
  exit 1
fi

if [[ "${state_sha}" != "${manifest_state_sha}" ]]; then
  echo "[f1-verify-latest] ERROR: manifest SHA mismatch for state_latest" >&2
  exit 1
fi
if [[ "${report_sha}" != "${manifest_report_sha}" ]]; then
  echo "[f1-verify-latest] ERROR: manifest SHA mismatch for daily_report_latest" >&2
  exit 1
fi
if [[ "${snapshot_sha}" != "${manifest_snapshot_sha}" ]]; then
  echo "[f1-verify-latest] ERROR: manifest SHA mismatch for snapshot_latest" >&2
  exit 1
fi

latest_state_size_actual="$(wc -c < "${state_latest}" | tr -d '[:space:]')"
latest_report_size_actual="$(wc -c < "${report_latest}" | tr -d '[:space:]')"
latest_snapshot_size_actual="$(wc -c < "${snapshot_latest}" | tr -d '[:space:]')"

if [[ "${manifest_state_size}" != "${latest_state_size_actual}" ]]; then
  echo "[f1-verify-latest] ERROR: manifest size mismatch for state_latest" >&2
  exit 1
fi
if [[ "${manifest_report_size}" != "${latest_report_size_actual}" ]]; then
  echo "[f1-verify-latest] ERROR: manifest size mismatch for daily_report_latest" >&2
  exit 1
fi
if [[ "${manifest_snapshot_size}" != "${latest_snapshot_size_actual}" ]]; then
  echo "[f1-verify-latest] ERROR: manifest size mismatch for snapshot_latest" >&2
  exit 1
fi

if [[ "${manifest_source_state_file}" != "${latest_state_ts##*/}" ]]; then
  echo "[f1-verify-latest] ERROR: manifest source state file does not match newest timestamped state artifact" >&2
  exit 1
fi
if [[ "${manifest_source_report_file}" != "${latest_report_ts##*/}" ]]; then
  echo "[f1-verify-latest] ERROR: manifest source report file does not match newest timestamped report artifact" >&2
  exit 1
fi
if [[ "${manifest_source_snapshot_file}" != "${latest_snapshot_ts##*/}" ]]; then
  echo "[f1-verify-latest] ERROR: manifest source snapshot file does not match newest timestamped snapshot artifact" >&2
  exit 1
fi

source_state_sha_actual="$(sha256sum "${latest_state_ts}" | awk '{print $1}')"
source_report_sha_actual="$(sha256sum "${latest_report_ts}" | awk '{print $1}')"
source_snapshot_sha_actual="$(sha256sum "${latest_snapshot_ts}" | awk '{print $1}')"
source_state_size_actual="$(wc -c < "${latest_state_ts}" | tr -d '[:space:]')"
source_report_size_actual="$(wc -c < "${latest_report_ts}" | tr -d '[:space:]')"
source_snapshot_size_actual="$(wc -c < "${latest_snapshot_ts}" | tr -d '[:space:]')"

if [[ "${manifest_source_state_sha}" != "${source_state_sha_actual}" ]]; then
  echo "[f1-verify-latest] ERROR: manifest source SHA mismatch for newest timestamped state artifact" >&2
  exit 1
fi
if [[ "${manifest_source_report_sha}" != "${source_report_sha_actual}" ]]; then
  echo "[f1-verify-latest] ERROR: manifest source SHA mismatch for newest timestamped report artifact" >&2
  exit 1
fi
if [[ "${manifest_source_snapshot_sha}" != "${source_snapshot_sha_actual}" ]]; then
  echo "[f1-verify-latest] ERROR: manifest source SHA mismatch for newest timestamped snapshot artifact" >&2
  exit 1
fi
if [[ "${manifest_source_state_size}" != "${source_state_size_actual}" ]]; then
  echo "[f1-verify-latest] ERROR: manifest source size mismatch for newest timestamped state artifact" >&2
  exit 1
fi
if [[ "${manifest_source_report_size}" != "${source_report_size_actual}" ]]; then
  echo "[f1-verify-latest] ERROR: manifest source size mismatch for newest timestamped report artifact" >&2
  exit 1
fi
if [[ "${manifest_source_snapshot_size}" != "${source_snapshot_size_actual}" ]]; then
  echo "[f1-verify-latest] ERROR: manifest source size mismatch for newest timestamped snapshot artifact" >&2
  exit 1
fi

if [[ "${require_coherent_manifest_time}" == "true" ]]; then
  manifest_stamp="$(extract_ts_token "${latest_manifest_ts}")"

  if [[ ! "${max_manifest_lag_seconds}" =~ ^[0-9]+$ ]]; then
    echo "[f1-verify-latest] ERROR: --max-manifest-lag-seconds must be an integer" >&2
    exit 1
  fi
  if [[ ! "${max_manifest_filename_skew_seconds}" =~ ^[0-9]+$ ]]; then
    echo "[f1-verify-latest] ERROR: --max-manifest-filename-skew-seconds must be an integer" >&2
    exit 1
  fi

  if [[ ! "${manifest_stamp}" =~ ^[0-9]{8}_[0-9]{6}$ ]]; then
    echo "[f1-verify-latest] ERROR: unable to parse manifest filename timestamp" >&2
    exit 1
  fi

  state_stamp="$(extract_ts_token "${latest_state_ts}")"
  report_stamp="$(extract_ts_token "${latest_report_ts}")"
  snapshot_stamp="$(extract_ts_token "${latest_snapshot_ts}")"

  if [[ ! "${state_stamp}" =~ ^[0-9]{8}_[0-9]{6}$ || ! "${report_stamp}" =~ ^[0-9]{8}_[0-9]{6}$ || ! "${snapshot_stamp}" =~ ^[0-9]{8}_[0-9]{6}$ ]]; then
    echo "[f1-verify-latest] ERROR: unable to parse timestamps for manifest-time coherence check" >&2
    exit 1
  fi

  state_epoch="$(to_epoch_utc "${state_stamp}")"
  report_epoch="$(to_epoch_utc "${report_stamp}")"
  snapshot_epoch="$(to_epoch_utc "${snapshot_stamp}")"
  manifest_epoch="$(to_epoch_iso_utc "${manifest_generated_at_utc}")"
  manifest_file_epoch="$(to_epoch_utc "${manifest_stamp}")"

  newest_artifact_epoch="${state_epoch}"
  for epoch in "${report_epoch}" "${snapshot_epoch}"; do
    if (( epoch > newest_artifact_epoch )); then
      newest_artifact_epoch="${epoch}"
    fi
  done

  manifest_lag_seconds=$((manifest_epoch - newest_artifact_epoch))
  if (( manifest_lag_seconds < 0 )); then
    echo "[f1-verify-latest] ERROR: manifest generated_at_utc is older than newest artifact timestamp" >&2
    exit 1
  fi

  if (( manifest_lag_seconds > max_manifest_lag_seconds )); then
    echo "[f1-verify-latest] ERROR: manifest generation lag too high (lag=${manifest_lag_seconds}s > ${max_manifest_lag_seconds}s)" >&2
    exit 1
  fi

  manifest_filename_skew_seconds=$((manifest_epoch - manifest_file_epoch))
  if (( manifest_filename_skew_seconds < 0 )); then
    manifest_filename_skew_seconds=$(( -manifest_filename_skew_seconds ))
  fi
  if (( manifest_filename_skew_seconds > max_manifest_filename_skew_seconds )); then
    echo "[f1-verify-latest] ERROR: manifest filename/generated_at_utc skew too high (skew=${manifest_filename_skew_seconds}s > ${max_manifest_filename_skew_seconds}s)" >&2
    exit 1
  fi

  echo "[f1-verify-latest] manifest_generation_lag_seconds=${manifest_lag_seconds} (threshold=${max_manifest_lag_seconds})"
  echo "[f1-verify-latest] manifest_filename_skew_seconds=${manifest_filename_skew_seconds} (threshold=${max_manifest_filename_skew_seconds})"
fi

if [[ "${reject_future_timestamps}" == "true" ]]; then
  if [[ ! "${max_future_skew_seconds}" =~ ^[0-9]+$ ]]; then
    echo "[f1-verify-latest] ERROR: --max-future-skew-seconds must be an integer" >&2
    exit 1
  fi

  now_epoch="$(date -u +%s)"
  report_epoch="$(to_epoch_utc "$(extract_ts_token "${latest_report_ts}")")"
  snapshot_epoch="$(to_epoch_utc "$(extract_ts_token "${latest_snapshot_ts}")")"
  state_epoch="$(to_epoch_utc "$(extract_ts_token "${latest_state_ts}")")"
  manifest_file_epoch="$(to_epoch_utc "$(extract_ts_token "${latest_manifest_ts}")")"
  manifest_generated_at_epoch="$(to_epoch_iso_utc "${manifest_generated_at_utc}")"

  future_state=$((state_epoch - now_epoch))
  future_report=$((report_epoch - now_epoch))
  future_snapshot=$((snapshot_epoch - now_epoch))
  future_manifest_file=$((manifest_file_epoch - now_epoch))
  future_manifest_generated=$((manifest_generated_at_epoch - now_epoch))

  max_observed_future_skew="0"
  for skew in "${future_state}" "${future_report}" "${future_snapshot}" "${future_manifest_file}" "${future_manifest_generated}"; do
    if (( skew > max_observed_future_skew )); then
      max_observed_future_skew="${skew}"
    fi
  done

  if (( max_observed_future_skew > max_future_skew_seconds )); then
    echo "[f1-verify-latest] ERROR: future timestamp skew too large (observed=${max_observed_future_skew}s > ${max_future_skew_seconds}s)" >&2
    exit 1
  fi

  echo "[f1-verify-latest] future_timestamp_skew_seconds=${max_observed_future_skew} (threshold=${max_future_skew_seconds})"
fi

state_status="$(extract_json_string_field "f1_9_status" "${state_latest}")"
state_today_utc="$(extract_json_string_field "today_utc" "${state_latest}")"
state_window="$(extract_json_string_field "window" "${state_latest}")"
state_next_action="$(extract_json_string_field "next_action" "${state_latest}")"
state_daily_health="$(extract_json_string_field "daily_health" "${state_latest}")"
state_daily_check_exit_code="$(awk 'index($0, "\"daily_check_exit_code\"") > 0 { line=$0; sub(/^.*:[[:space:]]*/, "", line); sub(/[[:space:]]*,?[[:space:]]*$/, "", line); print line; exit }' "${state_latest}")"
state_alert_level="$(extract_json_string_field "alert_level" "${state_latest}")"
state_due_alert_state="$(extract_nested_json_string_field "due_alert" "state" "${state_latest}")"
state_due_phase="$(extract_nested_json_string_field "due_alert" "next_pending_phase" "${state_latest}")"
state_due_date_utc="$(extract_nested_json_string_field "due_alert" "due_date_utc" "${state_latest}")"
state_due_today_utc="$(extract_nested_json_string_field "due_alert" "today_utc" "${state_latest}")"
state_due_days_remaining="$(extract_nested_json_string_field "due_alert" "days_remaining" "${state_latest}")"
state_due_next_action="$(extract_nested_json_string_field "due_alert" "next_action" "${state_latest}")"
state_due_alert_action="$(extract_nested_json_string_field "due_alert" "alert_action" "${state_latest}")"
state_due_exit_code="$(extract_nested_json_numeric_field "due_alert" "exit_code" "${state_latest}")"
state_gate_state="$(extract_nested_json_string_field "gate" "state" "${state_latest}")"
state_gate_reason="$(extract_nested_json_string_field "gate" "reason" "${state_latest}")"
state_gate_missing_phases="$(extract_nested_json_string_field "gate" "missing_phases" "${state_latest}")"
state_gate_today_utc="$(extract_nested_json_string_field "gate" "today_utc" "${state_latest}")"
state_gate_window="$(extract_nested_json_string_field "gate" "window" "${state_latest}")"
state_gate_next_action="$(extract_nested_json_string_field "gate" "next_action" "${state_latest}")"
state_gate_exit_code="$(extract_nested_json_numeric_field "gate" "exit_code" "${state_latest}")"
state_schedule_day7_due="$(extract_nested_json_string_field "schedule" "day7_due" "${state_latest}")"
state_schedule_day14_due="$(extract_nested_json_string_field "schedule" "day14_due" "${state_latest}")"
state_schedule_day30_due="$(extract_nested_json_string_field "schedule" "day30_due" "${state_latest}")"
state_day0_baseline="$(extract_nested_json_string_field "artifacts" "day0_baseline" "${state_latest}")"
state_day7_review_artifact="$(extract_nested_json_string_field "artifacts" "day7_review" "${state_latest}")"
state_day14_review_artifact="$(extract_nested_json_string_field "artifacts" "day14_review" "${state_latest}")"
state_day30_review_artifact="$(extract_nested_json_string_field "artifacts" "day30_review" "${state_latest}")"

if [[ -z "${state_status}" || -z "${state_today_utc}" || -z "${state_window}" || -z "${state_next_action}" || -z "${state_daily_health}" || -z "${state_daily_check_exit_code}" || -z "${state_alert_level}" || -z "${state_due_alert_state}" || -z "${state_due_next_action}" || -z "${state_due_alert_action}" || -z "${state_due_exit_code}" || -z "${state_gate_state}" || -z "${state_gate_exit_code}" || -z "${state_schedule_day7_due}" || -z "${state_schedule_day14_due}" || -z "${state_schedule_day30_due}" || -z "${state_day0_baseline}" ]]; then
  echo "[f1-verify-latest] ERROR: unable to extract required semantic fields from state_latest" >&2
  exit 1
fi

report_daily_check_exit_code="$(extract_markdown_frontmatter_value "Daily check exit code" "${report_latest}")"
report_due_alert_exit_code="$(extract_markdown_frontmatter_value "Due alert exit code" "${report_latest}")"
report_daily_check_exit_code_count="$(grep -c "^- Daily check exit code:" "${report_latest}" 2>/dev/null || true)"
report_due_alert_exit_code_count="$(grep -c "^- Due alert exit code:" "${report_latest}" 2>/dev/null || true)"
report_daily_check_health="$(extract_markdown_section_kv "Daily Check Output" "F1.9_DAILY_HEALTH" "${report_latest}")"
report_daily_check_status="$(extract_markdown_section_kv "Daily Check Output" "F1.9_STATUS" "${report_latest}")"
report_daily_check_window="$(extract_markdown_section_kv "Daily Check Output" "WINDOW" "${report_latest}")"
report_daily_check_next_action="$(extract_markdown_section_kv "Daily Check Output" "NEXT_ACTION" "${report_latest}")"
report_daily_check_gate="$(extract_markdown_section_kv "Daily Check Output" "GATE" "${report_latest}")"
report_daily_check_gate_reason="$(extract_markdown_section_kv "Daily Check Output" "GATE_REASON" "${report_latest}")"
report_daily_check_exit_hint="$(extract_markdown_section_kv "Daily Check Output" "EXIT_CODE_HINT" "${report_latest}")"
report_due_state="$(extract_markdown_section_kv "Due Alert Output" "F1.9_DUE_ALERT" "${report_latest}")"
report_due_phase="$(extract_markdown_section_kv "Due Alert Output" "NEXT_PENDING_PHASE" "${report_latest}")"
report_due_date_utc="$(extract_markdown_section_kv "Due Alert Output" "DUE_DATE_UTC" "${report_latest}")"
report_due_today_utc="$(extract_markdown_section_kv "Due Alert Output" "TODAY_UTC" "${report_latest}")"
report_due_days_remaining="$(extract_markdown_section_kv "Due Alert Output" "DAYS_REMAINING" "${report_latest}")"
report_due_next_action="$(extract_markdown_section_kv "Due Alert Output" "NEXT_ACTION" "${report_latest}")"
report_due_alert_level="$(extract_markdown_section_kv "Due Alert Output" "ALERT_LEVEL" "${report_latest}")"
report_due_alert_action="$(extract_markdown_section_kv "Due Alert Output" "ALERT_ACTION" "${report_latest}")"
snapshot_gate_exit_code="$(extract_markdown_section_exit_code "Gate Output" "${snapshot_latest}")"
snapshot_due_exit_code="$(extract_markdown_section_exit_code "Due Alert Output" "${snapshot_latest}")"
snapshot_status_day0_baseline="$(extract_markdown_section_kv "Status Output" "DAY0_BASELINE" "${snapshot_latest}")"
snapshot_status_day7_due="$(extract_markdown_section_kv "Status Output" "DAY7_DUE" "${snapshot_latest}")"
snapshot_status_day14_due="$(extract_markdown_section_kv "Status Output" "DAY14_DUE" "${snapshot_latest}")"
snapshot_status_day30_due="$(extract_markdown_section_kv "Status Output" "DAY30_DUE" "${snapshot_latest}")"
snapshot_status_day7_artifact="$(extract_markdown_section_kv "Status Output" "DAY7_ARTIFACT" "${snapshot_latest}")"
snapshot_status_day14_artifact="$(extract_markdown_section_kv "Status Output" "DAY14_ARTIFACT" "${snapshot_latest}")"
snapshot_status_day30_artifact="$(extract_markdown_section_kv "Status Output" "DAY30_ARTIFACT" "${snapshot_latest}")"
snapshot_status_status="$(extract_markdown_section_kv "Status Output" "F1.9_STATUS" "${snapshot_latest}")"
snapshot_status_today_utc="$(extract_markdown_section_kv "Status Output" "TODAY_UTC" "${snapshot_latest}")"
snapshot_status_window="$(extract_markdown_section_kv "Status Output" "WINDOW" "${snapshot_latest}")"
snapshot_status_next_action="$(extract_markdown_section_kv "Status Output" "NEXT_ACTION" "${snapshot_latest}")"
snapshot_due_today_utc="$(extract_markdown_section_kv "Due Alert Output" "TODAY_UTC" "${snapshot_latest}")"
snapshot_due_date_utc="$(extract_markdown_section_kv "Due Alert Output" "DUE_DATE_UTC" "${snapshot_latest}")"
snapshot_due_days_remaining="$(extract_markdown_section_kv "Due Alert Output" "DAYS_REMAINING" "${snapshot_latest}")"
snapshot_due_state="$(extract_markdown_section_kv "Due Alert Output" "F1.9_DUE_ALERT" "${snapshot_latest}")"
snapshot_due_phase="$(extract_markdown_section_kv "Due Alert Output" "NEXT_PENDING_PHASE" "${snapshot_latest}")"
snapshot_due_next_action="$(extract_markdown_section_kv "Due Alert Output" "NEXT_ACTION" "${snapshot_latest}")"
snapshot_due_alert_level="$(extract_markdown_section_kv "Due Alert Output" "ALERT_LEVEL" "${snapshot_latest}")"
snapshot_due_alert_action="$(extract_markdown_section_kv "Due Alert Output" "ALERT_ACTION" "${snapshot_latest}")"
snapshot_gate_state="$(extract_markdown_section_kv "Gate Output" "F1.9_GATE" "${snapshot_latest}")"
snapshot_gate_reason="$(extract_markdown_section_kv "Gate Output" "REASON" "${snapshot_latest}")"
snapshot_gate_missing_phases="$(extract_markdown_section_kv "Gate Output" "MISSING_PHASES" "${snapshot_latest}")"
snapshot_gate_today_utc="$(extract_markdown_section_kv "Gate Output" "TODAY_UTC" "${snapshot_latest}")"
snapshot_gate_day7_due="$(extract_markdown_section_kv "Gate Output" "DAY7_DUE" "${snapshot_latest}")"
snapshot_gate_day14_due="$(extract_markdown_section_kv "Gate Output" "DAY14_DUE" "${snapshot_latest}")"
snapshot_gate_day30_due="$(extract_markdown_section_kv "Gate Output" "DAY30_DUE" "${snapshot_latest}")"
snapshot_gate_window="$(extract_markdown_section_kv "Gate Output" "WINDOW" "${snapshot_latest}")"
snapshot_gate_next_action="$(extract_markdown_section_kv "Gate Output" "NEXT_ACTION" "${snapshot_latest}")"

if [[ -z "${report_daily_check_exit_code}" || -z "${report_due_alert_exit_code}" || -z "${report_daily_check_health}" || -z "${report_daily_check_status}" || -z "${report_daily_check_window}" || -z "${report_daily_check_next_action}" || -z "${report_daily_check_gate}" || -z "${report_daily_check_exit_hint}" || -z "${report_due_state}" || -z "${report_due_next_action}" || -z "${report_due_alert_level}" || -z "${report_due_alert_action}" || -z "${snapshot_gate_exit_code}" || -z "${snapshot_due_exit_code}" || -z "${snapshot_status_day0_baseline}" || -z "${snapshot_status_day7_due}" || -z "${snapshot_status_day14_due}" || -z "${snapshot_status_day30_due}" || -z "${snapshot_status_status}" || -z "${snapshot_status_today_utc}" || -z "${snapshot_status_window}" || -z "${snapshot_status_next_action}" || -z "${snapshot_due_state}" || -z "${snapshot_due_next_action}" || -z "${snapshot_due_alert_level}" || -z "${snapshot_due_alert_action}" || -z "${snapshot_gate_state}" ]]; then
  echo "[f1-verify-latest] ERROR: unable to extract required section-aware semantic fields from latest markdown artifacts" >&2
  exit 1
fi
report_gate_reason_count="$(count_section_line_prefix_occurrences "Daily Check Output" "GATE_REASON=" "${report_latest}")"
report_daily_check_health_count="$(count_section_line_prefix_occurrences "Daily Check Output" "F1.9_DAILY_HEALTH=" "${report_latest}")"
report_daily_check_status_count="$(count_section_line_prefix_occurrences "Daily Check Output" "F1.9_STATUS=" "${report_latest}")"
report_due_phase_count="$(count_section_line_prefix_occurrences "Due Alert Output" "NEXT_PENDING_PHASE=" "${report_latest}")"
report_due_date_count="$(count_section_line_prefix_occurrences "Due Alert Output" "DUE_DATE_UTC=" "${report_latest}")"
report_due_today_count="$(count_section_line_prefix_occurrences "Due Alert Output" "TODAY_UTC=" "${report_latest}")"
report_due_days_count="$(count_section_line_prefix_occurrences "Due Alert Output" "DAYS_REMAINING=" "${report_latest}")"
snapshot_gate_reason_count="$(count_section_line_prefix_occurrences "Gate Output" "REASON=" "${snapshot_latest}")"
snapshot_gate_exit_code_line_count="$(grep -c "^- Exit code:" <(sed -n '/^## Gate Output/,/^## /p' "${snapshot_latest}") 2>/dev/null || true)"
snapshot_gate_day7_due_count="$(count_section_line_prefix_occurrences "Gate Output" "DAY7_DUE=" "${snapshot_latest}")"
snapshot_gate_day14_due_count="$(count_section_line_prefix_occurrences "Gate Output" "DAY14_DUE=" "${snapshot_latest}")"
snapshot_gate_day30_due_count="$(count_section_line_prefix_occurrences "Gate Output" "DAY30_DUE=" "${snapshot_latest}")"
snapshot_gate_window_count="$(count_section_line_prefix_occurrences "Gate Output" "WINDOW=" "${snapshot_latest}")"
snapshot_gate_next_action_count="$(count_section_line_prefix_occurrences "Gate Output" "NEXT_ACTION=" "${snapshot_latest}")"
snapshot_status_window_count="$(count_section_line_prefix_occurrences "Status Output" "WINDOW=" "${snapshot_latest}")"
snapshot_status_next_action_count="$(count_section_line_prefix_occurrences "Status Output" "NEXT_ACTION=" "${snapshot_latest}")"
snapshot_status_day0_baseline_count="$(count_section_line_prefix_occurrences "Status Output" "DAY0_BASELINE=" "${snapshot_latest}")"
snapshot_status_day7_due_count="$(count_section_line_prefix_occurrences "Status Output" "DAY7_DUE=" "${snapshot_latest}")"
snapshot_status_day14_due_count="$(count_section_line_prefix_occurrences "Status Output" "DAY14_DUE=" "${snapshot_latest}")"
snapshot_status_day30_due_count="$(count_section_line_prefix_occurrences "Status Output" "DAY30_DUE=" "${snapshot_latest}")"
snapshot_status_day7_artifact_count="$(count_section_line_prefix_occurrences "Status Output" "DAY7_ARTIFACT=" "${snapshot_latest}")"
snapshot_status_day14_artifact_count="$(count_section_line_prefix_occurrences "Status Output" "DAY14_ARTIFACT=" "${snapshot_latest}")"
snapshot_status_day30_artifact_count="$(count_section_line_prefix_occurrences "Status Output" "DAY30_ARTIFACT=" "${snapshot_latest}")"
snapshot_due_phase_count="$(count_section_line_prefix_occurrences "Due Alert Output" "NEXT_PENDING_PHASE=" "${snapshot_latest}")"
snapshot_due_exit_code_line_count="$(grep -c "^- Exit code:" <(sed -n '/^## Due Alert Output/,/^## /p' "${snapshot_latest}") 2>/dev/null || true)"
snapshot_due_date_count="$(count_section_line_prefix_occurrences "Due Alert Output" "DUE_DATE_UTC=" "${snapshot_latest}")"
snapshot_due_today_count="$(count_section_line_prefix_occurrences "Due Alert Output" "TODAY_UTC=" "${snapshot_latest}")"
snapshot_due_days_count="$(count_section_line_prefix_occurrences "Due Alert Output" "DAYS_REMAINING=" "${snapshot_latest}")"
if [[ ! "${state_daily_check_exit_code}" =~ ^[0-9]+$ || ! "${state_due_exit_code}" =~ ^[0-9]+$ || ! "${state_gate_exit_code}" =~ ^[0-9]+$ || ! "${report_daily_check_exit_code}" =~ ^[0-9]+$ || ! "${report_due_alert_exit_code}" =~ ^[0-9]+$ || ! "${report_daily_check_exit_hint}" =~ ^[0-9]+$ || ! "${snapshot_gate_exit_code}" =~ ^[0-9]+$ || ! "${snapshot_due_exit_code}" =~ ^[0-9]+$ ]]; then
  echo "[f1-verify-latest] ERROR: exit-code fields must be numeric in state/report/snapshot artifacts" >&2
  exit 1
fi
# #120: report frontmatter exit-code line uniqueness
if [[ "${report_daily_check_exit_code_count}" != "1" || "${report_due_alert_exit_code_count}" != "1" ]]; then
  echo "[f1-verify-latest] ERROR: report frontmatter must contain exactly one 'Daily check exit code:' and one 'Due alert exit code:' line (found: daily=${report_daily_check_exit_code_count}, due=${report_due_alert_exit_code_count})" >&2
  exit 1
fi
# #121: snapshot section exit-code line uniqueness
if [[ "${snapshot_gate_exit_code_line_count}" != "1" ]]; then
  echo "[f1-verify-latest] ERROR: snapshot Gate Output must contain exactly one '- Exit code:' line (found: ${snapshot_gate_exit_code_line_count})" >&2
  exit 1
fi
if [[ "${snapshot_due_exit_code_line_count}" != "1" ]]; then
  echo "[f1-verify-latest] ERROR: snapshot Due Alert Output must contain exactly one '- Exit code:' line (found: ${snapshot_due_exit_code_line_count})" >&2
  exit 1
fi
# #122: snapshot Status Output field line uniqueness
if [[ "${snapshot_status_day0_baseline_count}" != "1" || "${snapshot_status_day7_due_count}" != "1" || "${snapshot_status_day14_due_count}" != "1" || "${snapshot_status_day30_due_count}" != "1" || "${snapshot_status_day7_artifact_count}" != "1" || "${snapshot_status_day14_artifact_count}" != "1" || "${snapshot_status_day30_artifact_count}" != "1" ]]; then
  echo "[f1-verify-latest] ERROR: snapshot Status Output must contain exactly one DAY0_BASELINE/DAY7_DUE/DAY14_DUE/DAY30_DUE/DAY7_ARTIFACT/DAY14_ARTIFACT/DAY30_ARTIFACT line each (found: baseline=${snapshot_status_day0_baseline_count}, d7=${snapshot_status_day7_due_count}, d14=${snapshot_status_day14_due_count}, d30=${snapshot_status_day30_due_count}, a7=${snapshot_status_day7_artifact_count}, a14=${snapshot_status_day14_artifact_count}, a30=${snapshot_status_day30_artifact_count})" >&2
  exit 1
fi
re_date='^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
if [[ ! "${state_today_utc}" =~ ${re_date} || ! "${state_schedule_day7_due}" =~ ${re_date} || ! "${state_schedule_day14_due}" =~ ${re_date} || ! "${state_schedule_day30_due}" =~ ${re_date} || ! "${snapshot_status_today_utc}" =~ ${re_date} || ! "${snapshot_status_day7_due}" =~ ${re_date} || ! "${snapshot_status_day14_due}" =~ ${re_date} || ! "${snapshot_status_day30_due}" =~ ${re_date} ]]; then
  echo "[f1-verify-latest] ERROR: core date fields in state/snapshot must match YYYY-MM-DD format" >&2
  exit 1
fi
# #96: f1_9_status enum gate
if [[ ! "${state_status}" =~ ^(IN_PROGRESS|COMPLETE|BLOCKED)$ ]]; then
  echo "[f1-verify-latest] ERROR: f1_9_status in state_latest must be one of: IN_PROGRESS, COMPLETE, BLOCKED" >&2
  exit 1
fi
# #97: day0_baseline artifact existence gate
if [[ -z "${state_day0_baseline}" ]]; then
  echo "[f1-verify-latest] ERROR: state_latest artifacts.day0_baseline must be non-empty" >&2
  exit 1
fi
if [[ ! -f "${ARTIFACTS_DIR}/${state_day0_baseline}" ]]; then
  echo "[f1-verify-latest] ERROR: state_latest day0_baseline artifact '${state_day0_baseline}' declared but not found in artifacts dir" >&2
  exit 1
fi
# #93: review artifact file existence gate
if [[ -n "${state_day7_review_artifact}" && ! -f "${ARTIFACTS_DIR}/${state_day7_review_artifact}" ]]; then
  echo "[f1-verify-latest] ERROR: state_latest day7_review artifact '${state_day7_review_artifact}' declared but not found in artifacts dir" >&2
  exit 1
fi
if [[ -n "${state_day14_review_artifact}" && ! -f "${ARTIFACTS_DIR}/${state_day14_review_artifact}" ]]; then
  echo "[f1-verify-latest] ERROR: state_latest day14_review artifact '${state_day14_review_artifact}' declared but not found in artifacts dir" >&2
  exit 1
fi
if [[ -n "${state_day30_review_artifact}" && ! -f "${ARTIFACTS_DIR}/${state_day30_review_artifact}" ]]; then
  echo "[f1-verify-latest] ERROR: state_latest day30_review artifact '${state_day30_review_artifact}' declared but not found in artifacts dir" >&2
  exit 1
fi
# #98: daily_health enum gate
if [[ ! "${state_daily_health}" =~ ^(ON_TRACK_WAIT|ACTION_DUE|BLOCKED|READY_FOR_F1_10|UNKNOWN_NEEDS_REVIEW)$ ]]; then
  echo "[f1-verify-latest] ERROR: daily_health in state_latest must be one of: ON_TRACK_WAIT, ACTION_DUE, BLOCKED, READY_FOR_F1_10, UNKNOWN_NEEDS_REVIEW" >&2
  exit 1
fi
if [[ ! "${state_due_alert_state}" =~ ^(ACTIVE|BLOCKED|COMPLETE|UNKNOWN)$ ]]; then
  echo "[f1-verify-latest] ERROR: due_alert F1.9_DUE_ALERT in state_latest must be one of: ACTIVE, BLOCKED, COMPLETE, UNKNOWN" >&2
  exit 1
fi
if [[ ! "${state_alert_level}" =~ ^(none|low|medium|high|critical)$ ]]; then
  echo "[f1-verify-latest] ERROR: due_alert ALERT_LEVEL in state_latest must be one of: none, low, medium, high, critical" >&2
  exit 1
fi
if [[ ! "${state_due_alert_action}" =~ ^(fix_blocker_before_schedule_tracking|ready_for_f1_10_signoff|manual_review_required|run_official_review_immediately|run_official_review_today|prepare_and_run_review_within_48h|prepare_review_window|monitor_schedule)$ ]]; then
  echo "[f1-verify-latest] ERROR: due_alert ALERT_ACTION in state_latest is not in the allowed contract set" >&2
  exit 1
fi
# #102: artifact filename format gate
if [[ ! "${state_day0_baseline}" =~ ^f1_risk_day0_baseline_[0-9]{8}_[0-9]{6}\.md$ ]]; then
  echo "[f1-verify-latest] ERROR: state_latest artifacts.day0_baseline must follow filename format f1_risk_day0_baseline_YYYYMMDD_HHMMSS.md" >&2
  exit 1
fi
if [[ -n "${state_day7_review_artifact}" && ! "${state_day7_review_artifact}" =~ ^f1_risk_day7_review_[0-9]{8}_[0-9]{6}\.md$ ]]; then
  echo "[f1-verify-latest] ERROR: state_latest artifacts.day7_review must follow filename format f1_risk_day7_review_YYYYMMDD_HHMMSS.md when present" >&2
  exit 1
fi
if [[ -n "${state_day14_review_artifact}" && ! "${state_day14_review_artifact}" =~ ^f1_risk_day14_review_[0-9]{8}_[0-9]{6}\.md$ ]]; then
  echo "[f1-verify-latest] ERROR: state_latest artifacts.day14_review must follow filename format f1_risk_day14_review_YYYYMMDD_HHMMSS.md when present" >&2
  exit 1
fi
if [[ -n "${state_day30_review_artifact}" && ! "${state_day30_review_artifact}" =~ ^f1_risk_day30_review_[0-9]{8}_[0-9]{6}\.md$ ]]; then
  echo "[f1-verify-latest] ERROR: state_latest artifacts.day30_review must follow filename format f1_risk_day30_review_YYYYMMDD_HHMMSS.md when present" >&2
  exit 1
fi
if [[ ! "${state_window}" =~ ^(pre_day7|day7_to_day14|day14_to_day30|post_day30)$ ]]; then
  echo "[f1-verify-latest] ERROR: window in state_latest must be one of: pre_day7, day7_to_day14, day14_to_day30, post_day30" >&2
  exit 1
fi
# #92: window-coherence: state.window must be derivable from today_utc vs schedule
state_today_epoch_w="$(date -u -d "${state_today_utc}" +%s 2>/dev/null || true)"
state_day7_epoch_w="$(date -u -d "${state_schedule_day7_due}" +%s 2>/dev/null || true)"
state_day14_epoch_w="$(date -u -d "${state_schedule_day14_due}" +%s 2>/dev/null || true)"
state_day30_epoch_w="$(date -u -d "${state_schedule_day30_due}" +%s 2>/dev/null || true)"
if [[ -z "${state_today_epoch_w}" || -z "${state_day7_epoch_w}" || -z "${state_day14_epoch_w}" || -z "${state_day30_epoch_w}" ]]; then
  echo "[f1-verify-latest] ERROR: unable to parse today_utc or schedule dates as epochs for window coherence check" >&2
  exit 1
fi
# #100: schedule monotonicity gate
if (( state_day7_epoch_w >= state_day14_epoch_w || state_day14_epoch_w >= state_day30_epoch_w )); then
  echo "[f1-verify-latest] ERROR: schedule due dates in state_latest must be strictly increasing: day7_due < day14_due < day30_due" >&2
  exit 1
fi
if (( state_today_epoch_w < state_day7_epoch_w )); then
  expected_state_window="pre_day7"
elif (( state_today_epoch_w < state_day14_epoch_w )); then
  expected_state_window="day7_to_day14"
elif (( state_today_epoch_w < state_day30_epoch_w )); then
  expected_state_window="day14_to_day30"
else
  expected_state_window="post_day30"
fi
if [[ "${state_window}" != "${expected_state_window}" ]]; then
  echo "[f1-verify-latest] ERROR: window in state_latest is '${state_window}' but derived from today_utc/schedule is '${expected_state_window}'" >&2
  exit 1
fi
if [[ ! "${state_next_action}" =~ ^(run_day7_review|wait_day7_due_then_run_official_day7_review|run_official_day7_review|wait_day14_due_then_run_official_day14_review|run_official_day14_review|wait_day30_due_then_run_official_day30_review|run_official_day30_review|prepare_f1_10_signoff)$ ]]; then
  echo "[f1-verify-latest] ERROR: next_action in state_latest is not in the allowed status workflow action set" >&2
  exit 1
fi
if [[ ! "${state_gate_state}" =~ ^(PASS|FAIL)$ ]]; then
  echo "[f1-verify-latest] ERROR: gate F1.9_GATE in state_latest must be PASS or FAIL" >&2
  exit 1
fi
if [[ "${state_status}" == "BLOCKED" ]]; then
  expected_state_daily_health="BLOCKED"
  expected_state_daily_check_exit_code="1"
elif [[ "${state_gate_state}" == "PASS" ]]; then
  expected_state_daily_health="READY_FOR_F1_10"
  expected_state_daily_check_exit_code="0"
elif [[ "${state_next_action}" == wait_* ]]; then
  expected_state_daily_health="ON_TRACK_WAIT"
  expected_state_daily_check_exit_code="0"
elif [[ "${state_next_action}" == run_* || "${state_next_action}" == prepare_* ]]; then
  expected_state_daily_health="ACTION_DUE"
  expected_state_daily_check_exit_code="2"
else
  expected_state_daily_health="UNKNOWN_NEEDS_REVIEW"
  expected_state_daily_check_exit_code="1"
fi
if [[ "${state_daily_health}" != "${expected_state_daily_health}" || "${state_daily_check_exit_code}" != "${expected_state_daily_check_exit_code}" ]]; then
  echo "[f1-verify-latest] ERROR: daily_check fields in state_latest are inconsistent with status/gate/next_action workflow contract" >&2
  exit 1
fi
if [[ "${state_gate_state}" == "FAIL" ]]; then
  if [[ -z "${state_gate_reason}" || -z "${state_gate_next_action}" ]]; then
    echo "[f1-verify-latest] ERROR: gate FAIL in state_latest requires non-empty reason/next_action" >&2
    exit 1
  fi
  if [[ "${report_gate_reason_count}" != "1" || "${snapshot_gate_reason_count}" != "1" || "${snapshot_gate_next_action_count}" != "1" ]]; then
    echo "[f1-verify-latest] ERROR: gate FAIL requires exactly one REASON line in report/snapshot and exactly one NEXT_ACTION line in snapshot Gate Output" >&2
    exit 1
  fi
  # #118: report Daily Check field uniqueness for FAIL gate
  if [[ "${report_daily_check_health_count}" != "1" || "${report_daily_check_status_count}" != "1" ]]; then
    echo "[f1-verify-latest] ERROR: report Daily Check Output must contain exactly one F1.9_DAILY_HEALTH and exactly one F1.9_STATUS line (found: health=${report_daily_check_health_count}, status=${report_daily_check_status_count})" >&2
    exit 1
  fi
  if [[ ! "${state_gate_reason}" =~ ^(missing_day0_baseline|missing_official_review_artifacts|early_rehearsal_artifact_detected)$ ]]; then
    echo "[f1-verify-latest] ERROR: gate REASON in state_latest is not in the allowed FAIL reason set" >&2
    exit 1
  fi
  if [[ "${state_gate_exit_code}" != "1" ]]; then
    echo "[f1-verify-latest] ERROR: gate exit_code in state_latest must be 1 when F1.9_GATE=FAIL" >&2
    exit 1
  fi
  if [[ "${state_gate_reason}" == "missing_official_review_artifacts" && -z "${state_gate_missing_phases}" ]]; then
    echo "[f1-verify-latest] ERROR: gate missing_phases in state_latest must be present when REASON=missing_official_review_artifacts" >&2
    exit 1
  fi
  # #104: reason-scoped gate metadata contract (WINDOW and MISSING_PHASES)
  if [[ "${state_gate_reason}" == "missing_official_review_artifacts" ]]; then
    if [[ -z "${state_gate_window}" ]]; then
      echo "[f1-verify-latest] ERROR: gate WINDOW in state_latest must be present when REASON=missing_official_review_artifacts" >&2
      exit 1
    fi
    if [[ "${snapshot_gate_window_count}" != "1" ]]; then
      echo "[f1-verify-latest] ERROR: snapshot_latest Gate Output must contain exactly one WINDOW= line when REASON=missing_official_review_artifacts" >&2
      exit 1
    fi
  else
    if [[ -n "${state_gate_window}" || "${snapshot_gate_window_count}" != "0" ]]; then
      echo "[f1-verify-latest] ERROR: gate WINDOW must be absent in state/snapshot when REASON is not missing_official_review_artifacts" >&2
      exit 1
    fi
    if [[ -n "${state_gate_missing_phases}" ]]; then
      echo "[f1-verify-latest] ERROR: gate missing_phases must be absent in state_latest when REASON is not missing_official_review_artifacts" >&2
      exit 1
    fi
  fi
  # #105: missing_phases token contract for missing_official_review_artifacts
  if [[ "${state_gate_reason}" == "missing_official_review_artifacts" ]]; then
    if [[ ! "${state_gate_missing_phases}" =~ ^(day7|day14|day30)( (day7|day14|day30))*$ ]]; then
      echo "[f1-verify-latest] ERROR: gate missing_phases in state_latest must be a space-separated list of day7/day14/day30" >&2
      exit 1
    fi
    phase_token_count="$(awk '{print NF}' <<<"${state_gate_missing_phases}")"
    unique_phase_token_count="$(tr ' ' '\n' <<<"${state_gate_missing_phases}" | sed '/^$/d' | sort -u | wc -l | tr -d ' ')"
    if [[ "${phase_token_count}" != "${unique_phase_token_count}" ]]; then
      echo "[f1-verify-latest] ERROR: gate missing_phases in state_latest must not contain duplicate phase tokens" >&2
      exit 1
    fi
  fi
  # #94: gate NEXT_ACTION enum gate (FAIL branch)
  if [[ ! "${state_gate_next_action}" =~ ^(bash scripts/risk_phase_f1_post_release_day0\.sh|wait_due_window_then_run_official_reviews|wait_day14_due_then_run_official_day14_review|wait_day30_due_then_run_official_day30_review|run_missing_official_reviews_immediately|generate_official_non_early_review_artifacts)$ ]]; then
    echo "[f1-verify-latest] ERROR: gate NEXT_ACTION in state_latest is not in the allowed FAIL gate action set" >&2
    exit 1
  fi
  # #106/#107: reason/window -> gate NEXT_ACTION coherence contract
  case "${state_gate_reason}" in
    missing_day0_baseline)
      expected_gate_next_action_by_reason="bash scripts/risk_phase_f1_post_release_day0.sh"
      ;;
    early_rehearsal_artifact_detected)
      expected_gate_next_action_by_reason="generate_official_non_early_review_artifacts"
      ;;
    missing_official_review_artifacts)
      case "${state_gate_window}" in
        pre_day7)
          expected_gate_next_action_by_reason="wait_due_window_then_run_official_reviews"
          ;;
        day7_to_day14)
          expected_gate_next_action_by_reason="wait_day14_due_then_run_official_day14_review"
          ;;
        day14_to_day30)
          expected_gate_next_action_by_reason="wait_day30_due_then_run_official_day30_review"
          ;;
        post_day30)
          expected_gate_next_action_by_reason="run_missing_official_reviews_immediately"
          ;;
        *)
          echo "[f1-verify-latest] ERROR: gate WINDOW in state_latest must be one of: pre_day7, day7_to_day14, day14_to_day30, post_day30 when REASON=missing_official_review_artifacts" >&2
          exit 1
          ;;
      esac
      ;;
  esac
  if [[ "${state_gate_next_action}" != "${expected_gate_next_action_by_reason}" ]]; then
    echo "[f1-verify-latest] ERROR: gate NEXT_ACTION in state_latest is inconsistent with REASON/WINDOW contract" >&2
    exit 1
  fi
elif [[ "${state_gate_state}" == "PASS" ]]; then
  if [[ -n "${state_gate_reason}" || -n "${state_gate_window}" || -n "${state_gate_next_action}" || -n "${state_gate_missing_phases}" ]]; then
    echo "[f1-verify-latest] ERROR: gate PASS in state_latest must not include reason/window/next_action/missing_phases" >&2
    exit 1
  fi
  if [[ "${state_gate_exit_code}" != "0" ]]; then
    echo "[f1-verify-latest] ERROR: gate exit_code in state_latest must be 0 when F1.9_GATE=PASS" >&2
    exit 1
  fi
  if [[ "${report_gate_reason_count}" != "0" || "${snapshot_gate_reason_count}" != "0" || "${snapshot_gate_window_count}" != "0" || "${snapshot_gate_next_action_count}" != "0" ]]; then
    echo "[f1-verify-latest] ERROR: gate PASS requires absence of REASON in report/snapshot and absence of WINDOW/NEXT_ACTION in snapshot Gate Output" >&2
    exit 1
  fi
  # #95: gate=PASS forces top-level next_action=prepare_f1_10_signoff
  if [[ "${state_next_action}" != "prepare_f1_10_signoff" ]]; then
    echo "[f1-verify-latest] ERROR: top-level next_action in state_latest must be 'prepare_f1_10_signoff' when F1.9_GATE=PASS" >&2
    exit 1
  fi
fi
if [[ "${state_due_next_action}" != "${state_next_action}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert NEXT_ACTION in state_latest must match top-level next_action" >&2
  exit 1
fi
case "${state_due_alert_state}" in
  BLOCKED)
    expected_state_alert_level="high"
    expected_state_alert_action="fix_blocker_before_schedule_tracking"
    expected_state_due_exit_code="2"
    ;;
  COMPLETE)
    expected_state_alert_level="none"
    expected_state_alert_action="ready_for_f1_10_signoff"
    expected_state_due_exit_code="0"
    ;;
  UNKNOWN)
    expected_state_alert_level="high"
    expected_state_alert_action="manual_review_required"
    expected_state_due_exit_code="2"
    ;;
  ACTIVE)
    expected_state_alert_level=""
    expected_state_alert_action=""
    expected_state_due_exit_code=""
    ;;
esac
if [[ "${state_due_alert_state}" != "ACTIVE" ]]; then
  if [[ "${state_alert_level}" != "${expected_state_alert_level}" || "${state_due_alert_action}" != "${expected_state_alert_action}" || "${state_due_exit_code}" != "${expected_state_due_exit_code}" ]]; then
    echo "[f1-verify-latest] ERROR: non-ACTIVE due_alert state in state_latest is inconsistent with alert_level/alert_action/exit_code contract" >&2
    exit 1
  fi
fi
# #119: snapshot Status Output field uniqueness
if [[ "${snapshot_status_window_count}" != "1" || "${snapshot_status_next_action_count}" != "1" ]]; then
  echo "[f1-verify-latest] ERROR: snapshot Status Output must contain exactly one WINDOW and exactly one NEXT_ACTION line (found: window=${snapshot_status_window_count}, next_action=${snapshot_status_next_action_count})" >&2
  exit 1
fi
if [[ "${state_due_alert_state}" == "ACTIVE" ]]; then
  if [[ -z "${state_due_phase}" || -z "${state_due_date_utc}" || -z "${state_due_today_utc}" || -z "${state_due_days_remaining}" || -z "${report_due_phase}" || -z "${report_due_date_utc}" || -z "${report_due_today_utc}" || -z "${report_due_days_remaining}" || -z "${snapshot_due_phase}" || -z "${snapshot_due_date_utc}" || -z "${snapshot_due_today_utc}" || -z "${snapshot_due_days_remaining}" ]]; then
    echo "[f1-verify-latest] ERROR: ACTIVE due_alert requires phase/date/today/days fields in state/report/snapshot" >&2
    exit 1
  fi
  if [[ "${report_due_phase_count}" != "1" || "${report_due_date_count}" != "1" || "${report_due_today_count}" != "1" || "${report_due_days_count}" != "1" || "${snapshot_due_phase_count}" != "1" || "${snapshot_due_date_count}" != "1" || "${snapshot_due_today_count}" != "1" || "${snapshot_due_days_count}" != "1" ]]; then
    echo "[f1-verify-latest] ERROR: ACTIVE due_alert requires exactly one phase/date/today/days line in report/snapshot Due Alert Output" >&2
    exit 1
  fi
  if [[ ! "${state_due_days_remaining}" =~ ^[0-9]+$ || ! "${report_due_days_remaining}" =~ ^[0-9]+$ || ! "${snapshot_due_days_remaining}" =~ ^[0-9]+$ ]]; then
    echo "[f1-verify-latest] ERROR: ACTIVE due_alert DAYS_REMAINING fields must be numeric in state/report/snapshot artifacts" >&2
    exit 1
  fi
  if [[ ! "${state_due_today_utc}" =~ ${re_date} || ! "${state_due_date_utc}" =~ ${re_date} || ! "${report_due_date_utc}" =~ ${re_date} || ! "${report_due_today_utc}" =~ ${re_date} || ! "${snapshot_due_today_utc}" =~ ${re_date} || ! "${snapshot_due_date_utc}" =~ ${re_date} ]]; then
    echo "[f1-verify-latest] ERROR: ACTIVE due_alert date fields must match YYYY-MM-DD format in state/report/snapshot" >&2
    exit 1
  fi
  if [[ ! "${state_due_phase}" =~ ^(day7|day14|day30)$ ]]; then
    echo "[f1-verify-latest] ERROR: ACTIVE due_alert NEXT_PENDING_PHASE in state_latest must be one of: day7, day14, day30" >&2
    exit 1
  fi
  # #101: ACTIVE phase-window coherence gate
  case "${state_window}" in
    pre_day7)
      expected_due_phase_by_window="day7"
      ;;
    day7_to_day14)
      expected_due_phase_by_window="day14"
      ;;
    day14_to_day30|post_day30)
      expected_due_phase_by_window="day30"
      ;;
  esac
  if [[ "${state_due_phase}" != "${expected_due_phase_by_window}" ]]; then
    echo "[f1-verify-latest] ERROR: ACTIVE due_alert NEXT_PENDING_PHASE (${state_due_phase}) is inconsistent with state window (${state_window}); expected ${expected_due_phase_by_window}" >&2
    exit 1
  fi
  case "${state_due_phase}" in
    day7)
      expected_due_date_by_phase="${state_schedule_day7_due}"
      ;;
    day14)
      expected_due_date_by_phase="${state_schedule_day14_due}"
      ;;
    day30)
      expected_due_date_by_phase="${state_schedule_day30_due}"
      ;;
  esac
  if [[ "${state_due_date_utc}" != "${expected_due_date_by_phase}" ]]; then
    echo "[f1-verify-latest] ERROR: due_alert DUE_DATE_UTC in state_latest is inconsistent with schedule for NEXT_PENDING_PHASE" >&2
    exit 1
  fi
  if [[ "${report_due_date_utc}" != "${expected_due_date_by_phase}" ]]; then
    echo "[f1-verify-latest] ERROR: due_alert DUE_DATE_UTC in daily_report_latest is inconsistent with schedule for NEXT_PENDING_PHASE" >&2
    exit 1
  fi
  if [[ "${snapshot_due_date_utc}" != "${expected_due_date_by_phase}" ]]; then
    echo "[f1-verify-latest] ERROR: due_alert DUE_DATE_UTC in snapshot_latest is inconsistent with schedule for NEXT_PENDING_PHASE" >&2
    exit 1
  fi
  state_due_today_epoch="$(date -u -d "${state_due_today_utc}" +%s 2>/dev/null || true)"
  state_due_date_epoch="$(date -u -d "${state_due_date_utc}" +%s 2>/dev/null || true)"
  if [[ -z "${state_due_today_epoch}" || -z "${state_due_date_epoch}" ]]; then
    echo "[f1-verify-latest] ERROR: unable to parse due_alert dates in state_latest as calendar dates" >&2
    exit 1
  fi
  expected_state_due_days_remaining="$(( (state_due_date_epoch - state_due_today_epoch) / 86400 ))"
  if [[ "${state_due_days_remaining}" != "${expected_state_due_days_remaining}" ]]; then
    echo "[f1-verify-latest] ERROR: due_alert DAYS_REMAINING in state_latest is inconsistent with DUE_DATE_UTC and TODAY_UTC" >&2
    exit 1
  fi
  if (( state_due_days_remaining < 0 )); then
    expected_state_alert_level="critical"
    expected_state_alert_action="run_official_review_immediately"
    expected_state_due_exit_code="2"
  elif (( state_due_days_remaining == 0 )); then
    expected_state_alert_level="high"
    expected_state_alert_action="run_official_review_today"
    expected_state_due_exit_code="2"
  elif (( state_due_days_remaining <= 2 )); then
    expected_state_alert_level="high"
    expected_state_alert_action="prepare_and_run_review_within_48h"
    expected_state_due_exit_code="2"
  elif (( state_due_days_remaining <= 7 )); then
    expected_state_alert_level="medium"
    expected_state_alert_action="prepare_review_window"
    expected_state_due_exit_code="0"
  else
    expected_state_alert_level="low"
    expected_state_alert_action="monitor_schedule"
    expected_state_due_exit_code="0"
  fi
  if [[ "${state_alert_level}" != "${expected_state_alert_level}" || "${state_due_alert_action}" != "${expected_state_alert_action}" || "${state_due_exit_code}" != "${expected_state_due_exit_code}" ]]; then
    echo "[f1-verify-latest] ERROR: ACTIVE due_alert in state_latest is inconsistent with DAYS_REMAINING threshold contract" >&2
    exit 1
  fi
  if [[ "${state_today_utc}" != "${state_due_today_utc}" ]]; then
    echo "[f1-verify-latest] ERROR: TODAY_UTC internal consistency failure: state_latest today_utc != due_alert.today_utc" >&2
    exit 1
  fi
else
  if [[ -n "${state_due_phase}" || -n "${state_due_date_utc}" || -n "${state_due_today_utc}" || -n "${state_due_days_remaining}" || -n "${report_due_phase}" || -n "${report_due_date_utc}" || -n "${report_due_today_utc}" || -n "${report_due_days_remaining}" || -n "${snapshot_due_phase}" || -n "${snapshot_due_date_utc}" || -n "${snapshot_due_today_utc}" || -n "${snapshot_due_days_remaining}" ]]; then
    echo "[f1-verify-latest] ERROR: non-ACTIVE due_alert must not expose phase/date/today/days fields in state/report/snapshot" >&2
    exit 1
  fi
  if [[ "${report_due_phase_count}" != "0" || "${report_due_date_count}" != "0" || "${report_due_today_count}" != "0" || "${report_due_days_count}" != "0" || "${snapshot_due_phase_count}" != "0" || "${snapshot_due_date_count}" != "0" || "${snapshot_due_today_count}" != "0" || "${snapshot_due_days_count}" != "0" ]]; then
    echo "[f1-verify-latest] ERROR: non-ACTIVE due_alert sections in report/snapshot must not contain phase/date/today/days lines" >&2
    exit 1
  fi
fi
if [[ -n "${state_gate_today_utc}" && "${state_gate_today_utc}" != "${state_today_utc}" ]]; then
  echo "[f1-verify-latest] ERROR: TODAY_UTC internal consistency failure: state_latest gate.today_utc != today_utc" >&2
  exit 1
fi
if [[ "${report_daily_check_exit_code}" != "${state_daily_check_exit_code}" ]]; then
  echo "[f1-verify-latest] ERROR: daily_check_exit_code mismatch between state_latest and daily_report_latest" >&2
  exit 1
fi
if [[ "${report_due_alert_exit_code}" != "${state_due_exit_code}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert_exit_code mismatch between state_latest and daily_report_latest" >&2
  exit 1
fi
if [[ "${report_due_alert_exit_code}" != "${snapshot_due_exit_code}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert exit code mismatch between daily_report_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${report_daily_check_health}" != "${state_daily_health}" ]]; then
  echo "[f1-verify-latest] ERROR: daily_check F1.9_DAILY_HEALTH mismatch between state_latest and daily_report_latest" >&2
  exit 1
fi
if [[ "${report_daily_check_status}" != "${state_status}" ]]; then
  echo "[f1-verify-latest] ERROR: daily_check F1.9_STATUS mismatch between state_latest and daily_report_latest" >&2
  exit 1
fi
if [[ "${report_daily_check_status}" != "${snapshot_status_status}" ]]; then
  echo "[f1-verify-latest] ERROR: F1.9_STATUS mismatch between daily_report_latest Daily Check Output and snapshot_latest Status Output" >&2
  exit 1
fi
if [[ "${report_daily_check_window}" != "${state_window}" ]]; then
  echo "[f1-verify-latest] ERROR: daily_check WINDOW mismatch between state_latest and daily_report_latest" >&2
  exit 1
fi
if [[ "${report_daily_check_next_action}" != "${state_next_action}" ]]; then
  echo "[f1-verify-latest] ERROR: daily_check NEXT_ACTION mismatch between state_latest and daily_report_latest" >&2
  exit 1
fi
if [[ "${report_daily_check_gate}" != "${state_gate_state}" ]]; then
  echo "[f1-verify-latest] ERROR: daily_check GATE mismatch between state_latest and daily_report_latest" >&2
  exit 1
fi
# #108: direct/report-snapshot parity for gate state
if [[ "${snapshot_gate_state}" != "${state_gate_state}" ]]; then
  echo "[f1-verify-latest] ERROR: gate F1.9_GATE mismatch between state_latest and snapshot_latest Gate Output" >&2
  exit 1
fi
if [[ "${report_daily_check_gate}" != "${snapshot_gate_state}" ]]; then
  echo "[f1-verify-latest] ERROR: GATE mismatch between daily_report_latest Daily Check Output and snapshot_latest Gate Output" >&2
  exit 1
fi
if [[ "${state_gate_state}" == "FAIL" && "${report_daily_check_gate_reason}" != "${state_gate_reason}" ]]; then
  echo "[f1-verify-latest] ERROR: daily_check GATE_REASON mismatch between state_latest and daily_report_latest" >&2
  exit 1
fi
if [[ "${report_daily_check_exit_hint}" != "${state_daily_check_exit_code}" ]]; then
  echo "[f1-verify-latest] ERROR: daily_check EXIT_CODE_HINT mismatch between state_latest and daily_report_latest" >&2
  exit 1
fi
if [[ "${report_due_state}" != "${state_due_alert_state}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert F1.9_DUE_ALERT mismatch between state_latest and daily_report_latest" >&2
  exit 1
fi
if [[ "${report_due_phase}" != "${state_due_phase}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert NEXT_PENDING_PHASE mismatch between state_latest and daily_report_latest" >&2
  exit 1
fi
if [[ "${report_due_date_utc}" != "${state_due_date_utc}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert DUE_DATE_UTC mismatch between state_latest and daily_report_latest" >&2
  exit 1
fi
if [[ "${report_due_today_utc}" != "${state_due_today_utc}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert TODAY_UTC mismatch between state_latest and daily_report_latest" >&2
  exit 1
fi
if [[ "${report_due_days_remaining}" != "${state_due_days_remaining}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert DAYS_REMAINING mismatch between state_latest and daily_report_latest" >&2
  exit 1
fi
if [[ "${report_due_next_action}" != "${state_due_next_action}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert NEXT_ACTION mismatch between state_latest and daily_report_latest" >&2
  exit 1
fi
if [[ "${report_due_alert_level}" != "${state_alert_level}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert ALERT_LEVEL mismatch between state_latest and daily_report_latest" >&2
  exit 1
fi
if [[ "${report_due_alert_action}" != "${state_due_alert_action}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert ALERT_ACTION mismatch between state_latest and daily_report_latest" >&2
  exit 1
fi
if [[ "${snapshot_gate_exit_code}" != "${state_gate_exit_code}" ]]; then
  echo "[f1-verify-latest] ERROR: gate exit code mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${snapshot_due_exit_code}" != "${state_due_exit_code}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert exit code mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${state_gate_state}" == "FAIL" && "${snapshot_gate_reason}" != "${state_gate_reason}" ]]; then
  echo "[f1-verify-latest] ERROR: gate REASON mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${state_gate_state}" == "FAIL" && "${report_daily_check_gate_reason}" != "${snapshot_gate_reason}" ]]; then
  echo "[f1-verify-latest] ERROR: GATE_REASON mismatch between daily_report_latest Daily Check Output and snapshot_latest Gate Output" >&2
  exit 1
fi
if [[ "${snapshot_status_day0_baseline}" != "${state_day0_baseline}" ]]; then
  echo "[f1-verify-latest] ERROR: status DAY0_BASELINE mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${snapshot_status_day7_due}" != "${state_schedule_day7_due}" ]]; then
  echo "[f1-verify-latest] ERROR: status DAY7_DUE mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${snapshot_status_day14_due}" != "${state_schedule_day14_due}" ]]; then
  echo "[f1-verify-latest] ERROR: status DAY14_DUE mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${snapshot_status_day30_due}" != "${state_schedule_day30_due}" ]]; then
  echo "[f1-verify-latest] ERROR: status DAY30_DUE mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${snapshot_status_day7_artifact}" != "${state_day7_review_artifact}" ]]; then
  echo "[f1-verify-latest] ERROR: status DAY7_ARTIFACT mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${snapshot_status_day14_artifact}" != "${state_day14_review_artifact}" ]]; then
  echo "[f1-verify-latest] ERROR: status DAY14_ARTIFACT mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${snapshot_status_day30_artifact}" != "${state_day30_review_artifact}" ]]; then
  echo "[f1-verify-latest] ERROR: status DAY30_ARTIFACT mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${snapshot_status_today_utc}" != "${state_today_utc}" ]]; then
  echo "[f1-verify-latest] ERROR: status TODAY_UTC mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${snapshot_status_window}" != "${state_window}" ]]; then
  echo "[f1-verify-latest] ERROR: status WINDOW mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
# #109: direct WINDOW parity between daily_report and snapshot Status Output
if [[ "${report_daily_check_window}" != "${snapshot_status_window}" ]]; then
  echo "[f1-verify-latest] ERROR: WINDOW mismatch between daily_report_latest Daily Check Output and snapshot_latest Status Output" >&2
  exit 1
fi
if [[ "${snapshot_status_next_action}" != "${state_next_action}" ]]; then
  echo "[f1-verify-latest] ERROR: status NEXT_ACTION mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
# #103: direct NEXT_ACTION parity between daily_report and snapshot Status Output
if [[ "${report_daily_check_next_action}" != "${snapshot_status_next_action}" ]]; then
  echo "[f1-verify-latest] ERROR: NEXT_ACTION mismatch between daily_report_latest Daily Check Output and snapshot_latest Status Output" >&2
  exit 1
fi
if [[ "${snapshot_due_today_utc}" != "${state_due_today_utc}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert TODAY_UTC mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${snapshot_due_date_utc}" != "${state_due_date_utc}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert DUE_DATE_UTC mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${snapshot_due_days_remaining}" != "${state_due_days_remaining}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert DAYS_REMAINING mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${snapshot_due_state}" != "${state_due_alert_state}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert F1.9_DUE_ALERT mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${snapshot_due_phase}" != "${state_due_phase}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert NEXT_PENDING_PHASE mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${snapshot_due_next_action}" != "${state_due_next_action}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert NEXT_ACTION mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
# #111: direct Due Alert parity between daily_report and snapshot (state-independent)
if [[ "${report_due_state}" != "${snapshot_due_state}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert F1.9_DUE_ALERT mismatch between daily_report_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${report_due_phase}" != "${snapshot_due_phase}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert NEXT_PENDING_PHASE mismatch between daily_report_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${report_due_date_utc}" != "${snapshot_due_date_utc}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert DUE_DATE_UTC mismatch between daily_report_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${report_due_today_utc}" != "${snapshot_due_today_utc}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert TODAY_UTC mismatch between daily_report_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${report_due_days_remaining}" != "${snapshot_due_days_remaining}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert DAYS_REMAINING mismatch between daily_report_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${report_due_next_action}" != "${snapshot_due_next_action}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert NEXT_ACTION mismatch between daily_report_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${report_due_alert_level}" != "${snapshot_due_alert_level}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert ALERT_LEVEL mismatch between daily_report_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${report_due_alert_action}" != "${snapshot_due_alert_action}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert ALERT_ACTION mismatch between daily_report_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${snapshot_due_alert_level}" != "${state_alert_level}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert ALERT_LEVEL mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
if [[ "${snapshot_due_alert_action}" != "${state_due_alert_action}" ]]; then
  echo "[f1-verify-latest] ERROR: due_alert ALERT_ACTION mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
if [[ -n "${state_gate_today_utc}" && "${snapshot_gate_today_utc}" != "${state_gate_today_utc}" ]]; then
  echo "[f1-verify-latest] ERROR: gate TODAY_UTC mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
if [[ -n "${snapshot_gate_today_utc}" && "${snapshot_gate_today_utc}" != "${snapshot_status_today_utc}" ]]; then
  echo "[f1-verify-latest] ERROR: gate TODAY_UTC mismatch between snapshot_latest Gate Output and snapshot_latest Status Output" >&2
  exit 1
fi
if [[ -n "${state_gate_window}" && "${snapshot_gate_window}" != "${state_gate_window}" ]]; then
  echo "[f1-verify-latest] ERROR: gate WINDOW mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
if [[ -n "${state_gate_next_action}" && "${snapshot_gate_next_action}" != "${state_gate_next_action}" ]]; then
  echo "[f1-verify-latest] ERROR: gate NEXT_ACTION mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
snapshot_gate_missing_phases_count="$(count_section_line_prefix_occurrences "Gate Output" "MISSING_PHASES=" "${snapshot_latest}")"
if [[ -n "${state_gate_missing_phases}" && "${snapshot_gate_missing_phases_count}" != "1" ]]; then
  echo "[f1-verify-latest] ERROR: snapshot_latest Gate Output must contain exactly one MISSING_PHASES= line when state requires it" >&2
  exit 1
fi
if [[ -z "${state_gate_missing_phases}" && "${snapshot_gate_missing_phases_count}" != "0" ]]; then
  echo "[f1-verify-latest] ERROR: snapshot_latest Gate Output must not contain MISSING_PHASES= line when state does not require it" >&2
  exit 1
fi
if [[ -n "${state_gate_missing_phases}" && "${snapshot_gate_missing_phases}" != "${state_gate_missing_phases}" ]]; then
  echo "[f1-verify-latest] ERROR: gate MISSING_PHASES mismatch between state_latest and snapshot_latest" >&2
  exit 1
fi
# #114: reason-scoped gate due-date contract (Gate Output must align with schedule/status)
if [[ "${state_gate_state}" == "FAIL" && ( "${state_gate_reason}" == "missing_official_review_artifacts" || "${state_gate_reason}" == "early_rehearsal_artifact_detected" ) ]]; then
  if [[ "${snapshot_gate_day7_due_count}" != "1" || "${snapshot_gate_day14_due_count}" != "1" || "${snapshot_gate_day30_due_count}" != "1" ]]; then
    echo "[f1-verify-latest] ERROR: snapshot_latest Gate Output must contain exactly one DAY7_DUE/DAY14_DUE/DAY30_DUE line for this FAIL reason" >&2
    exit 1
  fi
  if [[ "${snapshot_gate_day7_due}" != "${state_schedule_day7_due}" || "${snapshot_gate_day14_due}" != "${state_schedule_day14_due}" || "${snapshot_gate_day30_due}" != "${state_schedule_day30_due}" ]]; then
    echo "[f1-verify-latest] ERROR: gate DAY*_DUE mismatch between state_latest schedule and snapshot_latest Gate Output" >&2
    exit 1
  fi
  if [[ "${snapshot_gate_day7_due}" != "${snapshot_status_day7_due}" || "${snapshot_gate_day14_due}" != "${snapshot_status_day14_due}" || "${snapshot_gate_day30_due}" != "${snapshot_status_day30_due}" ]]; then
    echo "[f1-verify-latest] ERROR: gate DAY*_DUE mismatch between snapshot_latest Gate Output and snapshot_latest Status Output" >&2
    exit 1
  fi
fi
if [[ "${state_gate_state}" == "FAIL" && "${state_gate_reason}" == "missing_day0_baseline" ]]; then
  if [[ "${snapshot_gate_day7_due_count}" != "0" || "${snapshot_gate_day14_due_count}" != "0" || "${snapshot_gate_day30_due_count}" != "0" ]]; then
    echo "[f1-verify-latest] ERROR: snapshot_latest Gate Output must not contain DAY*_DUE lines when REASON=missing_day0_baseline" >&2
    exit 1
  fi
fi

# #99: cross-artifact TODAY_UTC direct parity (report Due Alert Output ↔ snapshot Status Output)
if [[ "${report_due_today_utc}" != "${snapshot_status_today_utc}" ]]; then
  echo "[f1-verify-latest] ERROR: TODAY_UTC mismatch between daily_report_latest Due Alert Output and snapshot_latest Status Output" >&2
  exit 1
fi

# #116: exit-code semantic coherence validations
# Gate exit code must align with gate state: FAIL→non-zero, PASS→zero
if [[ "${state_gate_state}" == "FAIL" ]]; then
  if [[ "${state_gate_exit_code}" == "0" ]]; then
    echo "[f1-verify-latest] ERROR: gate.exit_code must be non-zero when gate.state=FAIL (found: ${state_gate_exit_code})" >&2
    exit 1
  fi
else
  if [[ "${state_gate_exit_code}" != "0" ]]; then
    echo "[f1-verify-latest] ERROR: gate.exit_code must be zero when gate.state!=FAIL (found: ${state_gate_exit_code})" >&2
    exit 1
  fi
fi

# Due alert exit code must align with due_alert state: ACTIVE/SAFE→zero, WARNING/OVERDUE→non-zero
case "${state_due_alert_state}" in
  ACTIVE|SAFE)
    if [[ "${state_due_exit_code}" != "0" ]]; then
      echo "[f1-verify-latest] ERROR: due_alert.exit_code must be zero when due_alert.state=${state_due_alert_state} (found: ${state_due_exit_code})" >&2
      exit 1
    fi
    ;;
  WARNING|OVERDUE)
    if [[ "${state_due_exit_code}" == "0" ]]; then
      echo "[f1-verify-latest] ERROR: due_alert.exit_code must be non-zero when due_alert.state=${state_due_alert_state} (found: ${state_due_exit_code})" >&2
      exit 1
    fi
    ;;
  *)
    echo "[f1-verify-latest] ERROR: due_alert.state has unexpected value: ${state_due_alert_state}" >&2
    exit 1
    ;;
esac

# #117: cross-artifact DAYS_REMAINING boundary threshold alignment
# For ACTIVE due_alert, report and snapshot DAYS_REMAINING must trigger same alert_level boundaries as state
if [[ "${state_due_alert_state}" == "ACTIVE" ]]; then
  if [[ ! "${report_due_days_remaining}" =~ ^[0-9]+$ || ! "${snapshot_due_days_remaining}" =~ ^[0-9]+$ ]]; then
    echo "[f1-verify-latest] ERROR: report and snapshot DAYS_REMAINING must be numeric for ACTIVE due_alert (found: report=${report_due_days_remaining}, snapshot=${snapshot_due_days_remaining})" >&2
    exit 1
  fi
  # Validate that report DAYS_REMAINING triggers same alert level threshold as state
  if (( state_due_days_remaining < 0 )); then
    if (( report_due_days_remaining >= 0 )); then
      echo "[f1-verify-latest] ERROR: report DAYS_REMAINING suggests different alert_level threshold than state (state overdue, report not overdue)" >&2
      exit 1
    fi
  elif (( state_due_days_remaining == 0 )); then
    if [[ "${report_due_days_remaining}" != "0" ]]; then
      echo "[f1-verify-latest] ERROR: report DAYS_REMAINING must be 0 when state is 0 for alert_level coherence" >&2
      exit 1
    fi
  elif (( state_due_days_remaining <= 2 )); then
    if [[ ! "${report_due_days_remaining}" =~ ^[0-2]$ ]]; then
      echo "[f1-verify-latest] ERROR: report DAYS_REMAINING must be ≤2 when state is ≤2 (found: ${report_due_days_remaining})" >&2
      exit 1
    fi
  elif (( state_due_days_remaining <= 7 )); then
    if (( report_due_days_remaining > 7 )); then
      echo "[f1-verify-latest] ERROR: report DAYS_REMAINING must be ≤7 when state is ≤7 (found: ${report_due_days_remaining})" >&2
      exit 1
    fi
  fi
  # Validate that snapshot DAYS_REMAINING also respects state boundaries
  if (( state_due_days_remaining < 0 )); then
    if (( snapshot_due_days_remaining >= 0 )); then
      echo "[f1-verify-latest] ERROR: snapshot DAYS_REMAINING suggests different alert_level threshold than state (state overdue, snapshot not overdue)" >&2
      exit 1
    fi
  elif (( state_due_days_remaining == 0 )); then
    if [[ "${snapshot_due_days_remaining}" != "0" ]]; then
      echo "[f1-verify-latest] ERROR: snapshot DAYS_REMAINING must be 0 when state is 0 for alert_level coherence" >&2
      exit 1
    fi
  elif (( state_due_days_remaining <= 2 )); then
    if [[ ! "${snapshot_due_days_remaining}" =~ ^[0-2]$ ]]; then
      echo "[f1-verify-latest] ERROR: snapshot DAYS_REMAINING must be ≤2 when state is ≤2 (found: ${snapshot_due_days_remaining})" >&2
      exit 1
    fi
  elif (( state_due_days_remaining <= 7 )); then
    if (( snapshot_due_days_remaining > 7 )); then
      echo "[f1-verify-latest] ERROR: snapshot DAYS_REMAINING must be ≤7 when state is ≤7 (found: ${snapshot_due_days_remaining})" >&2
      exit 1
    fi
  fi
fi

echo "[f1-verify-latest] OK: latest artifacts are consistent and schema-complete"
echo "[f1-verify-latest] state=${latest_state_ts##*/}"
echo "[f1-verify-latest] report=${latest_report_ts##*/}"
echo "[f1-verify-latest] snapshot=${latest_snapshot_ts##*/}"
