# F2 Playbooks Release and Rollback Runbook

## Scope

This runbook defines tenant rollout and rollback steps for F2 Auto Intervention Playbooks.

Feature flag key:
- `interventions.auto_playbooks`

Write-path policy:
- When disabled, playbook write endpoints are blocked with `403`.
- Read endpoints remain available (read-only rollback mode).

## Preconditions

1. Backend image with F2.8 guards is deployed.
2. Targeted F2 test bundle passed:
   - `tests/modules/interventions/test_router_playbooks_phase2.py`
   - `tests/modules/interventions/test_playbook_security_guards.py`
   - `tests/modules/interventions/test_risk_observability_metrics.py`
3. Observability alerts are active:
   - `PlaybookExecutionLatencyP95High`
   - `PlaybookAbandonmentRateHigh`
4. Latest DB backup is valid (`bash scripts/rollback_check.sh`).

## Rollout Strategy

### Phase 0: Disabled Baseline

Keep `interventions.auto_playbooks=false` for all tenants.
Validate that read endpoints are still available for support diagnostics.

### Phase 1: Canary (1 tenant)

1. Enable flag for exactly one pilot tenant.
2. Monitor for at least 24h:
   - playbook execution errors
   - p95 execution latency
   - abandonment rate
3. If no incident: move to Phase 2.

### Phase 2: Expanded Canary (3 tenants)

1. Enable flag for 3 pilot tenants total.
2. Monitor for at least 48h using the same KPIs.
3. If stable: move to Phase 3.

### Phase 3: Cohort Rollout

1. Enable flag for rollout cohort tenants.
2. Keep write-path kill switch ready (`interventions.auto_playbooks=false`).
3. Continue daily KPI checks during rollout window.

## Rollback

Trigger rollback immediately if one of the following is true:

1. Error spike on playbook write endpoints.
2. Sustained p95 latency breach.
3. Sustained abandonment anomaly.
4. Tenant isolation or permission regression.

Rollback actions:

1. Disable `interventions.auto_playbooks` for affected tenants (or globally by policy).
2. Confirm write endpoints return `403` and read endpoints remain available.
3. Run `bash scripts/rollback_check.sh`.
4. If deployment rollback is required, use `bash scripts/rollback_to_previous_release.sh <user@server>`.
5. Open incident note with tenant list, timestamps, and mitigation actions.

## Verification Checklist

1. Flag state per tenant is correct.
2. Write-path gate works (blocked when disabled).
3. Read-only access works when disabled.
4. Alerts and dashboards are green.
5. Audit logs contain rollout/rollback actions.

## Evidence Template

Record the following in audit notes:

1. Rollout phase reached (1 tenant, 3 tenants, cohort).
2. Time window and on-call owner.
3. KPI snapshots and alert state.
4. Rollback decision (if any) and exact flag changes.
