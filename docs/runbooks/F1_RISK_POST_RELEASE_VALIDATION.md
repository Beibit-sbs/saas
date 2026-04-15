# F1 Risk Post-Release Validation Runbook

## Purpose

Operational playbook for F1.9 post-release validation of the risk pipeline.

## Cadence

1. Day-0: create baseline artifact.
2. Day-1: initial quick health check.
3. Day-3: data correctness and trend check.
4. Day-7: final validation and feature readiness.

## Pre-Pilot Operating Mode (Current)

Use this mode while pilot traffic is not yet enabled:

1. Continue F2 implementation in parallel (do not block on day-1/day-3/day-7 calendar checkpoints).
2. Keep F1.9 in lightweight operational monitoring mode via daily runner / CI checks.
3. Treat day-1/day-3/day-7 reviews as reliability and operational-readiness evidence, not business-impact proof.
4. Use day-1/day-3/day-7 outputs as pre-pilot quality gates; finalize product-impact conclusions only after pilot traffic is available.

## Day-0 Baseline Capture

Run from repo root:

```bash
bash scripts/risk_phase_f1_post_release_day0.sh
```

Expected output:

- Baseline markdown file under docs/runbooks/artifacts.
- Embedded evidence for backend risk checks and promtool rules validation.
- Due dates for day-7/day-14/day-30 reviews.

## Prepare Review Templates

Run once after day-0 baseline is created:

```bash
bash scripts/risk_phase_f1_post_release_prepare_reviews.sh
```

Expected output:

- `f1_risk_day1_review_TEMPLATE.md`
- `f1_risk_day3_review_TEMPLATE.md`
- `f1_risk_day7_review_TEMPLATE.md`

All files are created in `docs/runbooks/artifacts` and prefilled with due dates from the latest day-0 baseline artifact.

## Status Snapshot

Run anytime to see current phase state, due dates, detected review artifacts, and next action:

```bash
bash scripts/risk_phase_f1_post_release_status.sh
```

## Calendar Export

Export review schedule as ICS (day-7/day-14/day-30):

```bash
bash scripts/risk_phase_f1_post_release_calendar_export.sh
```

Output file:

- `docs/runbooks/artifacts/f1_risk_post_release_review_schedule.ics`

## Snapshot Artifact

Generate a single markdown artifact with both `status` and `gate` outputs:

```bash
bash scripts/risk_phase_f1_post_release_snapshot.sh
```

Output file pattern:

- `docs/runbooks/artifacts/f1_risk_post_release_snapshot_<UTC_TIMESTAMP>.md`

Snapshot includes:

- `status` output
- `gate` output + exit code
- `due_alert` output + exit code

## Next Action Orchestrator

Resolve and print the current next action:

```bash
bash scripts/risk_phase_f1_post_release_next_action.sh
```

Attempt execution when action is currently runnable:

```bash
bash scripts/risk_phase_f1_post_release_next_action.sh --execute
```

Notes:

- The orchestration is due-date-safe for all phases: day7/day14/day30.
- Before each due date it returns an explicit wait-state action (no premature official review execution).

## Daily Health Check

Single command to evaluate daily operational state:

```bash
bash scripts/risk_phase_f1_post_release_daily_check.sh
```

Exit codes:

- `0`: on-track wait window or fully complete.
- `1`: blocked/invalid state (operator review required).
- `2`: action is due now (run next official step).

## Daily Report Artifact

Generate a timestamped markdown report with full `daily_check` output:

```bash
bash scripts/risk_phase_f1_post_release_daily_report.sh
```

Output file pattern:

- `docs/runbooks/artifacts/f1_risk_post_release_daily_report_<UTC_TIMESTAMP>.md`

Report includes:

- `daily_check` output + exit code
- `due_alert` output + exit code

## Daily Runner (Automation Entry Point)

Single command for automation (scheduler/CI):

```bash
bash scripts/risk_phase_f1_post_release_daily_runner.sh
```

Options:

- `--no-report`: run daily health evaluation without generating markdown artifact.
- `--auto-execute-due`: if state is action-due (`rc=2`), execute resolved next action and re-check.

## JSON State Export

Generate machine-readable state snapshot for scheduler/integration:

```bash
bash scripts/risk_phase_f1_post_release_state_export.sh
```

Output file pattern:

- `docs/runbooks/artifacts/f1_risk_post_release_state_<UTC_TIMESTAMP>.json`

State export includes `due_alert` block:

- `state`
- `next_pending_phase`
- `due_date_utc`
- `days_remaining`
- `alert_level`
- `alert_action`
- `exit_code`

## Publish Latest Artifacts

Create deterministic latest copies for integration consumers:

```bash
bash scripts/risk_phase_f1_post_release_publish_latest.sh --generate
```

Published files:

- `docs/runbooks/artifacts/f1_risk_post_release_state_latest.json`
- `docs/runbooks/artifacts/f1_risk_post_release_daily_report_latest.md`
- `docs/runbooks/artifacts/f1_risk_post_release_snapshot_latest.md`

## Verify Latest Artifacts

Validate deterministic latest files against newest timestamped artifacts and expected keys:

```bash
bash scripts/risk_phase_f1_post_release_verify_latest.sh
```

Verification now includes manifest contract checks:

- `generated_at_utc` exists in latest manifest.
- `manifest_latest` is byte-equal to newest timestamped manifest artifact.
- Manifest `path` fields for `state_latest`, `daily_report_latest`, `snapshot_latest` match expected deterministic artifact paths.
- Manifest `sha256` values match current SHA256 of published latest artifacts.
- Manifest `source_artifacts.state|daily_report|snapshot.file` values must match newest timestamped source artifact filenames.
- Manifest `source_artifacts.state|daily_report|snapshot.sha256` values must match checksum of newest timestamped source artifacts.
- Manifest `artifacts.*.size_bytes` and `source_artifacts.*.size_bytes` values must match actual byte size of latest and newest timestamped source artifacts.

Verification also enforces semantic cross-artifact consistency:

- `state_latest` values for `f1_9_status`, `window`, `next_action`, `daily_health`, `alert_level` must match corresponding lines in `daily_report_latest` and `snapshot_latest`.
- `state_latest.due_alert.next_pending_phase`, `due_date_utc`, `days_remaining`, `alert_action` must also match the embedded due-alert section in `daily_report_latest` and `snapshot_latest`.
- `state_latest.due_alert.state`, `due_alert.exit_code`, `gate.state`, and `gate.reason` must stay identical to the operator-facing values embedded in `daily_report_latest` and `snapshot_latest`.
- `snapshot_latest` must also stay aligned with `state_latest.schedule.*`, `state_latest.artifacts.*`, and `gate.missing_phases` because snapshot is the operator handoff artifact carrying full status/gate context.
- `state_latest.daily_check_exit_code` must match the `Daily check exit code` line in `daily_report_latest`, and `state_latest.gate.exit_code` must match the `Gate Output` exit code in `snapshot_latest`.
- `state_latest.due_alert.today_utc` must match the `Due Alert Output` section in both markdown artifacts, and when present `state_latest.gate.today_utc/window/next_action` must match the `Gate Output` section in `snapshot_latest`.
- `state_latest.today_utc/window/next_action` and `daily_check_exit_code` must also match the specific `Status Output` / `Daily Check Output` sections, including `EXIT_CODE_HINT`, not just appear somewhere in the markdown.
- Snapshot parity is section-scoped: `Status Output` must match schedule/artifact/top-level status fields, and `Gate Output` must match gate reason/missing phases/provenance fields from `state_latest`.
- Daily report parity is also section-scoped: `Daily Check Output` must match `daily_health/status/window/next_action/gate/gate_reason/EXIT_CODE_HINT`, and `Due Alert Output` plus frontmatter due-exit-code must match due-alert semantics from `state_latest`.
- `due_alert.next_action` is exported and validated explicitly: `Due Alert Output` `NEXT_ACTION` must match `state_latest.due_alert.next_action` (not inferred from top-level action fields).
- Residual file-wide markdown key-grep checks for report/snapshot are removed; parity relies on explicit section-scoped extraction/comparison to keep fail-closed checks deterministic.
- Structural markdown contract is fail-closed: required sections must exist and preserve expected order (`Daily Check Output -> Due Alert Output -> Interpretation` in daily report, `Status Output -> Gate Output -> Due Alert Output -> Notes` in snapshot).
- Structural markdown contract is also uniqueness-scoped: each required section heading must appear exactly once in daily report and snapshot.
- Structural markdown sections are fence-scoped: required report/snapshot sections must include explicit ```text fenced payload blocks.
- Fence contract is closed-block scoped: required ` ```text ` payload blocks must be properly closed with matching terminating fences.
- Fenced payload contract is uniqueness-scoped: each required section must contain exactly one ` ```text ` opener and one matching closing fence.
- Exit-code contract is type-scoped: extracted exit-code fields from state/report/snapshot must be numeric before semantic comparisons.
- `DAYS_REMAINING` contract is type-scoped: due-alert `DAYS_REMAINING` in `state_latest`, `daily_report_latest`, and `snapshot_latest` must be numeric before semantic comparisons.
- `DAYS_REMAINING` is also calendar-consistency validated in `state_latest`: value must equal UTC day delta between `due_alert.due_date_utc` and `due_alert.today_utc`; mismatches are fail-closed before cross-artifact parity.
- `F1.9_DUE_ALERT` in `state_latest.due_alert` is enum-validated (`ACTIVE|BLOCKED|COMPLETE|UNKNOWN`) before semantic comparisons.
- `ALERT_LEVEL` in `state_latest.due_alert` is enum-validated (`none|low|medium|high|critical`) before semantic comparisons.
- `ALERT_ACTION` in `state_latest.due_alert` is enum-validated against the due-alert action contract set (`fix_blocker_before_schedule_tracking`, `ready_for_f1_10_signoff`, `manual_review_required`, `run_official_review_immediately`, `run_official_review_today`, `prepare_and_run_review_within_48h`, `prepare_review_window`, `monitor_schedule`).
- `window` in `state_latest` is enum-validated (`pre_day7|day7_to_day14|day14_to_day30|post_day30`) before semantic comparisons.
- `window` in `state_latest` is additionally coherence-validated: the expected window is derived from `today_utc` vs `schedule.day7_due/day14_due/day30_due` using UTC epoch arithmetic, and must match the declared `window` value (fail-closed on any mismatch).
- `schedule.day7_due`, `schedule.day14_due`, `schedule.day30_due` are monotonicity-validated: due dates must be strictly increasing (`day7_due < day14_due < day30_due`) before window/due-phase semantics.
- Review artifact file existence is enforced: when `state_latest.artifacts.day7_review`, `day14_review`, or `day30_review` is non-empty, the declared filename must exist on disk in the artifacts directory; any declared-but-missing artifact fails verification.
- Artifact filename format is validated in `state_latest.artifacts`: `day0_baseline` must match `f1_risk_day0_baseline_YYYYMMDD_HHMMSS.md`; optional `day7_review/day14_review/day30_review` must match their phase-specific filename patterns when present.
- `next_action` in `state_latest` is enum-validated against the status workflow action set (`run_day7_review`, `wait_day7_due_then_run_official_day7_review`, `run_official_day7_review`, `wait_day14_due_then_run_official_day14_review`, `run_official_day14_review`, `wait_day30_due_then_run_official_day30_review`, `run_official_day30_review`, `prepare_f1_10_signoff`).
- `daily_health` and `daily_check_exit_code` in `state_latest` are workflow-derived validated from `f1_9_status`, `gate.state`, and `next_action` using the daily-check decision model.
- `F1.9_GATE` in `state_latest.gate` is enum-validated (`PASS|FAIL`) before semantic comparisons.
- Gate FAIL workflow contract is validated in `state_latest`: `gate.reason` must be one of known FAIL reasons, `gate.exit_code` must be `1`, and `missing_phases` must be present only when `reason=missing_official_review_artifacts`; `gate.next_action` is enum-validated against the allowed FAIL gate action set (`bash scripts/risk_phase_f1_post_release_day0.sh`, `wait_due_window_then_run_official_reviews`, `wait_day14_due_then_run_official_day14_review`, `wait_day30_due_then_run_official_day30_review`, `run_missing_official_reviews_immediately`, `generate_official_non_early_review_artifacts`).
- Gate FAIL reason-scoped coherence is enforced: `missing_day0_baseline -> bash scripts/risk_phase_f1_post_release_day0.sh` (no `window`/`missing_phases`), `early_rehearsal_artifact_detected -> generate_official_non_early_review_artifacts` (no `window`/`missing_phases`), and `missing_official_review_artifacts` requires `window` + `missing_phases` with `window -> next_action` mapping (`pre_day7 -> wait_due_window_then_run_official_reviews`, `day7_to_day14 -> wait_day14_due_then_run_official_day14_review`, `day14_to_day30 -> wait_day30_due_then_run_official_day30_review`, `post_day30 -> run_missing_official_reviews_immediately`).
- Gate `missing_phases` token contract is validated for `missing_official_review_artifacts`: value must be a space-separated list of unique phase tokens from `day7|day14|day30`.
- Gate PASS workflow contract is also validated in `state_latest`: `gate.exit_code` must be `0`, `gate.reason`, `gate.window`, `gate.next_action`, `gate.missing_phases` must be absent, and top-level `next_action` must be `prepare_f1_10_signoff`.
- Gate metadata presence is reason-scoped in markdown artifacts: under `FAIL`, `REASON` and `NEXT_ACTION` must exist; `WINDOW` must exist only when `reason=missing_official_review_artifacts`; under `PASS`, `REASON`/`WINDOW`/`NEXT_ACTION` must be absent.
- `due_alert.next_action` is internal-consistency validated in `state_latest`: it must match top-level `next_action`.
- Non-`ACTIVE` due-alert states are workflow-contract validated in `state_latest`: `BLOCKED`, `COMPLETE`, `UNKNOWN` must map to exact `alert_level`, `alert_action`, and `due_alert.exit_code` tuples.
- `ACTIVE` due-alert state is threshold-contract validated in `state_latest`: `DAYS_REMAINING` buckets must map to exact `alert_level`, `alert_action`, and `due_alert.exit_code` tuples.
- Under `ACTIVE`, `NEXT_PENDING_PHASE` is window-coherence validated: `pre_day7 -> day7`, `day7_to_day14 -> day14`, `day14_to_day30|post_day30 -> day30`.
- Due-alert exit code is therefore coherence-validated against state semantics (not only cross-artifact parity).
- Due-alert phase/date/today/days fields are state-scoped: `ACTIVE` requires them (with exact single-line presence in report/snapshot), while non-`ACTIVE` states require those fields to be absent in state/report/snapshot.
- `NEXT_PENDING_PHASE` in `state_latest.due_alert` is enum-validated (`day7|day14|day30`) before semantic comparisons.
- Phase-to-schedule coherence is enforced: due-alert `DUE_DATE_UTC` in `state_latest`, `daily_report_latest`, and `snapshot_latest` must match the schedule date for `NEXT_PENDING_PHASE` (`day7 -> schedule.day7_due`, `day14 -> schedule.day14_due`, `day30 -> schedule.day30_due`).
- Date-format contract is type-scoped: all date fields (`DUE_DATE_UTC`, `TODAY_UTC`, `DAY7_DUE`, `DAY14_DUE`, `DAY30_DUE`) in state/report/snapshot must match `YYYY-MM-DD` (`^[0-9]{4}-[0-9]{2}-[0-9]{2}$`) before semantic comparisons.
- TODAY_UTC cross-field consistency is internally enforced in `state_latest`: top-level `today_utc` must equal `due_alert.today_utc`, and when `gate.today_utc` is present it must also equal `today_utc`; any internal divergence is fail-closed before cross-artifact comparisons.
- Snapshot `Due Alert Output` semantic parity is now complete: `F1.9_DUE_ALERT`, `NEXT_PENDING_PHASE`, `DUE_DATE_UTC`, `TODAY_UTC`, `DAYS_REMAINING`, `NEXT_ACTION`, `ALERT_LEVEL`, `ALERT_ACTION` are all section-extracted and fail-closed compared against `state_latest.due_alert.*` fields, matching the parity model already applied to `daily_report_latest`.
- Direct report/snapshot parity is enforced for `NEXT_ACTION`: `daily_report_latest` `Daily Check Output` `NEXT_ACTION` must equal `snapshot_latest` `Status Output` `NEXT_ACTION`, and due-alert `NEXT_ACTION` must match between report and snapshot as well.
- Direct report/snapshot parity is enforced for all key due-alert fields in `Due Alert Output`: `F1.9_DUE_ALERT`, `NEXT_PENDING_PHASE`, `DUE_DATE_UTC`, `TODAY_UTC`, `DAYS_REMAINING`, `NEXT_ACTION`, `ALERT_LEVEL`, `ALERT_ACTION` must match between `daily_report_latest` and `snapshot_latest`.
- Direct report/snapshot parity is enforced for due-alert exit code metadata as well: `daily_report_latest` frontmatter `Due alert exit code` must match `snapshot_latest` `Due Alert Output` exit code.
- Direct report/snapshot parity is enforced for status field `F1.9_STATUS`: `daily_report_latest` `Daily Check Output` `F1.9_STATUS` must equal `snapshot_latest` `Status Output` `F1.9_STATUS`.
- Direct gate-state parity is enforced: `snapshot_latest` `Gate Output` `F1.9_GATE` must match both `state_latest.gate.state` and `daily_report_latest` `Daily Check Output` `GATE`.
- Direct report/snapshot parity is enforced for `WINDOW`: `daily_report_latest` `Daily Check Output` `WINDOW` must equal `snapshot_latest` `Status Output` `WINDOW`.
- Under `F1.9_GATE=FAIL`, direct report/snapshot parity is also enforced for `GATE_REASON`: `daily_report_latest` `Daily Check Output` `GATE_REASON` must equal `snapshot_latest` `Gate Output` `REASON`.
- Gate/Status `TODAY_UTC` parity is direct in `snapshot_latest`: when `Gate Output` exposes `TODAY_UTC`, it must match `Status Output` `TODAY_UTC`.
- Gate due-date fields are reason-scoped validated in `snapshot_latest` `Gate Output`: for `missing_official_review_artifacts` and `early_rehearsal_artifact_detected`, `DAY7_DUE`/`DAY14_DUE`/`DAY30_DUE` must each appear exactly once and match both `state_latest.schedule.*` and `snapshot_latest` `Status Output`; for `missing_day0_baseline`, these fields must be absent.
- Snapshot `Due Alert Output` exit code is now explicitly section-validated against `state_latest.due_alert.exit_code` (same as gate exit-code parity model).
- Frontmatter and section exit-code metadata are uniqueness-validated: required frontmatter labels and `- Exit code:` lines in `Gate Output`/`Due Alert Output` must each appear exactly once.
- Exit-code semantic coherence is now enforced: `state_latest.gate.exit_code` must be non-zero when `gate.state=FAIL` and zero when `gate.state!=FAIL`; `state_latest.due_alert.exit_code` must be zero when `due_alert.state` is `ACTIVE` or `SAFE`, and non-zero when `due_alert.state` is `WARNING` or `OVERDUE`.
- Cross-artifact DAYS_REMAINING boundary alignment is now enforced for ACTIVE due_alert: `daily_report_latest` and `snapshot_latest` DAYS_REMAINING must fall within same alert_level boundaries as `state_latest` (overdue/critical at <0, overdue/high at 0, high at ≤2, medium at ≤7, low at >7) to ensure alert_level semantic coherence across artifacts.
- Report Daily Check Output field uniqueness is now enforced: when gate is FAIL, `F1.9_DAILY_HEALTH` and `F1.9_STATUS` must each appear exactly once in `daily_report_latest` Daily Check Output section.
- Snapshot Status Output field uniqueness is now enforced: `WINDOW` and `NEXT_ACTION` must each appear exactly once in `snapshot_latest` Status Output section.
- Report frontmatter exit-code line uniqueness is now enforced: `daily_report_latest` frontmatter must contain exactly one `Daily check exit code:` line and exactly one `Due alert exit code:` line, preventing duplicate frontmatter injection.
- Snapshot section exit-code line uniqueness is now enforced: `snapshot_latest` Gate Output and Due Alert Output must each contain exactly one `- Exit code:` line, preventing duplicate section-level exit code injection.
- Snapshot Status Output field line uniqueness is now enforced: `snapshot_latest` Status Output must contain exactly one line each for DAY0_BASELINE, DAY7_DUE, DAY14_DUE, DAY30_DUE, DAY7_ARTIFACT, DAY14_ARTIFACT, DAY30_ARTIFACT, preventing duplicate date/artifact field injection.
- Section payload keys are uniqueness-validated: critical `KEY=` lines in required report/snapshot sections must each appear exactly once.
- Optional gate provenance is presence-scoped: `MISSING_PHASES=` in `Gate Output` must appear exactly once when required by state, and must be absent when not required.
- Latest and newest timestamped `state/report/snapshot/manifest` artifacts must be non-empty; zero-byte files are treated as invalid.
- Any mismatch is fail-closed (`verify_latest` exits non-zero).

Optional strict freshness checks:

- `--require-fresh-report` enforces max lag between newest `state` and newest `daily_report` artifacts.
- `--max-report-lag-seconds N` sets allowed lag threshold (default `86400`).
- `--require-fresh-snapshot` enforces max lag between newest `state` and newest `snapshot` artifacts.
- `--max-snapshot-lag-seconds N` sets allowed lag threshold (default `86400`).
- `--require-coherent-artifact-timestamps` enforces max skew between newest timestamped `state`/`daily_report`/`snapshot` artifacts.
- `--max-artifact-skew-seconds N` sets allowed skew threshold (default `300`).
- `--require-coherent-embedded-timestamps` enforces that embedded `generated_at/captured_at` metadata inside `state_latest`, `daily_report_latest`, and `snapshot_latest` matches each artifact filename timestamp.
- `--max-embedded-timestamp-skew-seconds N` sets allowed embedded-timestamp skew threshold (default `5`).
- `--require-recent-state` enforces max wall-clock age of newest timestamped `state` artifact.
- `--max-state-age-seconds N` sets allowed wall-clock age threshold (default `900`).
- `--require-coherent-manifest-time` enforces `generated_at_utc` coherence in `manifest_latest` against newest artifact timestamp.
- `--max-manifest-lag-seconds N` sets allowed manifest generation lag threshold (default `300`).
- `--max-manifest-filename-skew-seconds N` sets allowed skew between `manifest_<ts>.json` timestamp and `generated_at_utc` (default `300`).
- `--require-recent-manifest` enforces max wall-clock age of newest timestamped manifest artifact.
- `--max-manifest-age-seconds N` sets allowed wall-clock age threshold for newest manifest artifact (default `900`).
- `--reject-future-timestamps` enforces that newest state/report/snapshot/manifest timestamps are not ahead of wall-clock time.
- `--max-future-skew-seconds N` sets allowed positive future skew tolerance (default `30`).

## CI Pipeline Entrypoint

Run full operational chain in one command:

```bash
bash scripts/risk_phase_f1_post_release_ci.sh --no-report
```

Project shortcut:

```bash
make f1-post-release-ci
```

Evidence-mode shortcut (generates fresh daily report artifact):

```bash
make f1-post-release-ci-full
```

Strict due-alert mode:

```bash
bash scripts/risk_phase_f1_post_release_ci.sh --no-report --fail-on-due-alert
```

```bash
make f1-post-release-ci-strict
```

Strict report-freshness mode (optional):

```bash
bash scripts/risk_phase_f1_post_release_ci.sh --no-report --require-fresh-report --max-report-lag-seconds 86400
```

Strict snapshot-freshness mode (optional):

```bash
bash scripts/risk_phase_f1_post_release_ci.sh --no-report --require-fresh-snapshot --max-snapshot-lag-seconds 86400
```

Make shortcut (fresh report + strict freshness):

```bash
make f1-post-release-ci-fresh-strict
```

Strict-all mode (optional):

```bash
bash scripts/risk_phase_f1_post_release_ci.sh --strict-all
```

`--strict-all` combines:

1. `--fail-on-due-alert`
2. `--require-fresh-report --max-report-lag-seconds 86400`
3. `--require-fresh-snapshot --max-snapshot-lag-seconds 86400`
4. `--require-coherent-artifact-timestamps --max-artifact-skew-seconds 300`
5. `--require-coherent-embedded-timestamps --max-embedded-timestamp-skew-seconds 5`
6. `--require-recent-state --max-state-age-seconds 900`
7. `--require-coherent-manifest-time --max-manifest-lag-seconds 300`
8. `--max-manifest-filename-skew-seconds 300`
9. `--require-recent-manifest --max-manifest-age-seconds 900`
10. `--reject-future-timestamps --max-future-skew-seconds 30`

Make shortcut:

```bash
make f1-post-release-ci-strict-all
```

Super-strict shortcut:

```bash
make f1-post-release-ci-super-strict
```

Under `--strict-all`, CI now also enforces embedded timestamp coherence for `state/report/snapshot` latest artifacts.

Pipeline order:

1. `daily_runner`
2. `due_alert`
3. `state_export`
4. `snapshot`
5. `publish_latest`
6. `manifest`
7. `verify_latest`

Notes:

- `publish_latest` selects only timestamped source artifacts (excludes `*_latest.*`).
- CI script exit code mirrors `daily_runner` (`0|1|2`).
- With `--fail-on-due-alert`, CI returns `2` when due-alert reports escalation (`rc=2`).

Manifest outputs:

- `docs/runbooks/artifacts/f1_risk_post_release_manifest_<UTC_TIMESTAMP>.json`
- `docs/runbooks/artifacts/f1_risk_post_release_manifest_latest.json`

## Due Alert

Compute nearest pending phase, days remaining, and alert level:

```bash
bash scripts/risk_phase_f1_post_release_due_alert.sh
```

Exit codes:

- `0`: scheduled or upcoming-week state.
- `2`: due-soon / due-today / overdue attention needed.
- `1`: parsing/runtime error.

## Day-7 Review

Command (strict due-date check):

```bash
bash scripts/risk_phase_f1_post_release_day_review.sh --phase day7
```

Optional rehearsal before due date:

```bash
bash scripts/risk_phase_f1_post_release_day_review.sh --phase day7 --allow-early
```

1. Re-run synthetic risk smoke checks.
2. Inspect recent alert history for noise and flapping.
3. Add a day-7 artifact in docs/runbooks/artifacts with findings and actions.

## Day-14 Review

Command:

```bash
bash scripts/risk_phase_f1_post_release_day_review.sh --phase day14
```

1. Evaluate false_positive_rate drift and threshold suitability.
2. Record any threshold or policy changes and expected impact.
3. Add a day-14 artifact in docs/runbooks/artifacts.

## Day-30 Review

Command:

```bash
bash scripts/risk_phase_f1_post_release_day_review.sh --phase day30
```

1. Compute dropout_risk_reduction_percent delta against day-0 baseline.
2. Review intervention_conversion_rate and advisor_action_latency_p95 trends.
3. Publish summary for F1.10 final sign-off readiness.

## Exit Criteria

- Day-0/day-7/day-14/day-30 artifacts exist and are complete.
- No unresolved critical alert spikes.
- KPI trend supports proceeding to F1.10 DoD sign-off.

## Completion Gate

Run before F1.10 sign-off:

```bash
bash scripts/risk_phase_f1_post_release_gate.sh
```

Expected pass conditions:

- Official day7/day14/day30 review artifacts exist.
- No artifact is marked with EARLY_EXECUTION=true.
- Script prints F1.9_GATE=PASS.

On FAIL, script now prints:

- `MISSING_PHASES` (which official phases are absent)
- `WINDOW` (`pre_day7`, `day7_to_day14`, `day14_to_day30`, `post_day30`)
- `NEXT_ACTION` (операционная подсказка следующей команды)
