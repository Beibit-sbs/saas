# F2 Playbooks Post-Release Validation Protocol

## Overview

Post-release validation for F2 Auto Intervention Playbooks feature.
Feature flag: `interventions.auto_playbooks`

## Review Schedule

| Phase  | Trigger               | Focus                                          |
|--------|----------------------|------------------------------------------------|
| Day 0  | On release           | Baseline capture, flag gate verification       |
| Day 1  | `DAY1_DUE` from baseline | Quick initial health check                    |
| Day 3  | `DAY3_DUE` from baseline | Data correctness, alert noise, early patterns |
| Day 7  | `DAY7_DUE` from baseline | KPI trend confirmation, feature adoption       |

## KPIs (from F2.1 Product Contract)

- **North-star**: `intervention_conversion_rate = playbook_executions_improved_risk / all_completed_playbook_executions`
- **Guardrail 1**: `playbook_execution_latency_p95` — p95 time from execution created to last mandatory step completed
- **Guardrail 2**: `auto_playbook_trigger_precision` — auto-triggered / total executions (noise control)
- **Guardrail 3**: `playbook_abandonment_rate` — abandoned / all started executions

## Alert Rules (Prometheus)

- `PlaybookExecutionLatencyP95High` — latency degradation
- `PlaybookAbandonmentRateHigh` — abandonment spike

## Scripts

| Script                                          | Purpose                           |
|-------------------------------------------------|-----------------------------------|
| `scripts/f2_playbooks_post_release_day0.sh`     | Generate day-0 baseline artifact  |
| `scripts/f2_playbooks_post_release_status.sh`   | Current status + next action      |
| `scripts/f2_playbooks_post_release_gate.sh`     | F2.9 completion gate (PASS/FAIL)  |
| `scripts/f2_playbooks_post_release_day_review.sh --phase day7\|day14\|day30` | Phase review runner |

## Workflow

### Step 1 — Day-0 baseline (run on release day)

```bash
bash scripts/f2_playbooks_post_release_day0.sh
```

Generates `docs/runbooks/artifacts/f2_playbooks_day0_baseline_<stamp>.md`.
Sets review schedule.

### Step 2 — Check status at any time

```bash
bash scripts/f2_playbooks_post_release_status.sh
```

Returns current `WINDOW`, `NEXT_ACTION`.

### Step 3 — Run official review (on/after due date)

```bash
# Official (on/after due date only):
bash scripts/f2_playbooks_post_release_day_review.sh --phase day7
bash scripts/f2_playbooks_post_release_day_review.sh --phase day14
bash scripts/f2_playbooks_post_release_day_review.sh --phase day30

# Rehearsal (before due date, EARLY_EXECUTION=true in artifact):
bash scripts/f2_playbooks_post_release_day_review.sh --phase day7 --allow-early
```

### Step 4 — Check completion gate

```bash
bash scripts/f2_playbooks_post_release_gate.sh
# F2.9_GATE=PASS → eligible for F2.10 sign-off
```

### Step 5 — Rollback (if needed)

See [F2_PLAYBOOKS_RELEASE_ROLLBACK.md](F2_PLAYBOOKS_RELEASE_ROLLBACK.md).

Key action:
```bash
# Disable feature flag (per tenant or globally)
# Confirm write-path returns 403, read endpoints return 200
```

## Review Checklist Template

Each review artifact should include:

- [ ] Backend playbook tests passing (router + security guards + observability)
- [ ] Prometheus alert rules validated (promtool)
- [ ] KPI delta vs day-0 baseline documented
- [ ] Alert noise status reviewed
- [ ] Feature flag rollout phase progression documented
- [ ] Tenant feedback / escalations reviewed
- [ ] Verdict: PASS / CONDITIONAL / FAIL

## Exit Criteria for F2.9 → F2.10

`F2.9_GATE=PASS` requires:
1. Day-0 baseline artifact present
2. Official day-7 review artifact present (non-early)
3. Official day-14 review artifact present (non-early)
4. Official day-30 review artifact present (non-early)

Run: `bash scripts/f2_playbooks_post_release_gate.sh`

## References

- Rollout/rollback runbook: [F2_PLAYBOOKS_RELEASE_ROLLBACK.md](F2_PLAYBOOKS_RELEASE_ROLLBACK.md)
- F2 audit: `docs/AUDIT_SBS_2026.md` section F2
- F1 analogue: [F1_RISK_POST_RELEASE_VALIDATION.md](F1_RISK_POST_RELEASE_VALIDATION.md)
