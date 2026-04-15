# F1 Risk Post-Release Daily Report

- Generated at (UTC): 2026-04-12T17:59:24Z
- Daily check exit code: 0
- Due alert exit code: 0

## Daily Check Output

```text
F1.9_DAILY_HEALTH=ON_TRACK_WAIT
F1.9_STATUS=IN_PROGRESS
WINDOW=pre_day7
NEXT_ACTION=wait_day7_due_then_run_official_day7_review
GATE=FAIL
GATE_REASON=missing_official_review_artifacts
EXIT_CODE_HINT=0
---
[f1-next] WINDOW=pre_day7
[f1-next] NEXT_ACTION=wait_day7_due_then_run_official_day7_review
[f1-next] COMMAND=none (wait/timebox or manual decision required)
```

## Due Alert Output

```text
F1.9_DUE_ALERT=ACTIVE
NEXT_PENDING_PHASE=day7
DUE_DATE_UTC=2026-04-19
TODAY_UTC=2026-04-12
DAYS_REMAINING=7
NEXT_ACTION=wait_day7_due_then_run_official_day7_review
ALERT_LEVEL=medium
ALERT_ACTION=prepare_review_window
```

## Interpretation

- Exit code `0`: on-track wait window or fully complete.
- Exit code `1`: blocked/invalid state (operator review required).
- Exit code `2`: action is due now (run next official step).
