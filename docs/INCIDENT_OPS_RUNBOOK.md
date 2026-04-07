# Incident Ops Runbook

## Purpose

This runbook defines the operational response flow for production incidents in the current pilot architecture, without redesigning platform components.

## Scope

- API node
- worker and scheduler runtime
- PostgreSQL connectivity
- webhook and outbox processing
- metrics and health visibility

## Key Signals

Use these endpoints as the primary signal source:

- `GET /health/live`
- `GET /health/ready`
- `GET /health/worker`
- `GET /health/deep`
- `GET /metrics/ops`
- `GET /metrics/latency`
- `GET /api/v1/internal/webhooks/failed-deliveries`

Key metric fields to watch first:

- `event_queue_size`
- `failed_webhooks`
- `dead_webhooks`
- `retry_backlog`
- `failed_automation_executions`
- `dead_automation_executions`
- `failed_jobs`
- `dead_jobs`
- `developer_api_error_count`

Structured logs include `request_id` and `trace_id` for correlation across API requests, events, worker processing, and webhook retries.

## Severity Levels

- `SEV-1`: full outage or cross-tenant security risk
- `SEV-2`: critical capability degradation (worker/webhooks/scheduler)
- `SEV-3`: partial degradation with workaround

## Standard Incident Flow

1. Confirm incident scope from health and metrics endpoints.
2. Contain blast radius by pausing risky automations or integrations.
3. Restore service in the smallest safe change.
4. Validate recovery with endpoint checks and smoke tests.
5. Capture timeline, root cause, and preventive actions.

## Fast Triage Commands

Systemd deployment:

```bash
systemctl status platform-api.service --no-pager
systemctl status platform-worker.service --no-pager
systemctl status platform-scheduler.service --no-pager
```

Health checks:

```bash
curl -fsS https://<host>/health/live
curl -fsS https://<host>/health/ready
curl -fsS https://<host>/health/worker
curl -fsS https://<host>/health/deep
```

Operational metrics:

```bash
curl -fsS https://<host>/metrics/ops
curl -fsS https://<host>/metrics/latency
curl -fsS -H "Authorization: Bearer <METRICS_TOKEN>" https://<host>/metrics
```

## Scenario Playbooks

### 1) Database Unreachable

Detection:

- `/health/deep` returns `503` or `dependencies.postgresql.healthy=false`
- API `5xx` rate increases

Actions:

1. Validate PostgreSQL process and connection limits.
2. Verify disk and WAL health.
3. If needed, temporarily stop worker and scheduler to reduce write pressure.
4. Recover DB service.
5. Re-check `/health/deep` and `/health/worker`.
6. Start worker and scheduler in controlled order.

Exit criteria:

- database health green for at least 5 minutes
- queue growth stabilizes

### 2) Worker Stalled Or Crashing

Detection:

- `/health/worker` returns `503`
- `/metrics/ops.event_queue_size` grows continuously
- `outbox_event_dead_lettered` logs increase

Actions:

1. Restart `platform-worker.service`.
2. Search logs by `trace_id` to identify recurring failing flow.
3. Isolate problematic automation rule or webhook destination.
4. Confirm new heartbeat and backlog reduction.

Exit criteria:

- worker heartbeat fresh
- backlog trending down

### 2b) Outbox Backlog Growing But Worker Is Alive

Detection:

- `/health/worker` returns `200`
- `/metrics/ops.event_queue_size` keeps growing
- `/metrics/ops.failed_jobs` or `/metrics/ops.failed_automation_executions` also trend upward

Actions:

1. Confirm worker loop is running but throughput is below arrival rate.
2. Inspect structured logs for repeated handler failures by `trace_id` and `event_type`.
3. Run the targeted pilot smoke path to separate systemic breakage from one bad event class.
4. Pause or disable the failing downstream dependency if backlog growth is caused by webhook or automation retries.
5. Scale worker concurrency only after confirming failures are not deterministic.

Exit criteria:

- backlog plateaus and begins decreasing
- no repeated terminal failures for the same event class

### 3) Webhook Delivery Exhaustion

Detection:

- `/metrics/ops.failed_webhooks` or `/metrics/ops.retry_backlog` grows
- internal failed deliveries endpoint returns rising failures
- logs include `webhook_delivery_exhausted`

Actions:

1. Inspect failed deliveries list and classify by target.
2. Verify target endpoint availability and auth secrets.
3. Disable or throttle failing target to protect queue throughput.
4. Re-enable after downstream recovery.

Exit criteria:

- failed delivery rate drops
- retry backlog returns to baseline

### 3b) Webhook Retry Storm

Detection:

- `/metrics/ops.retry_backlog` spikes rapidly
- `webhook_delivery_exhausted` or repeated `503` responses dominate logs
- downstream endpoint owner confirms instability or rate limiting

Actions:

1. Group failures by `target_url` and `event_type`.
2. Temporarily deactivate the worst subscription or block the downstream target at the scheduler/worker layer.
3. Confirm queue recovery before re-enabling delivery attempts.
4. Re-run `POST /api/v1/internal/webhooks/retry-failed` in controlled batches only after downstream recovery.

Exit criteria:

- retry backlog is shrinking for 15 minutes
- no new exhausted deliveries are created for the affected target

### 4) Scheduler Not Running

Detection:

- `/health/deep` shows `dependencies.scheduler.healthy=false`
- `/metrics/ops.scheduler_last_run` is stale

Actions:

1. Check `platform-scheduler.service` state and recent logs.
2. Restart scheduler service.
3. Validate a known scheduled task completion timestamp.

Exit criteria:

- scheduler last run updates normally

### 4b) Automation Failures

Detection:

- `/metrics/ops.failed_automation_executions` or `/metrics/ops.dead_automation_executions` rises
- AI Copilot automation health queries report failed rules
- logs include `automation_execution_failed`

Actions:

1. List recent executions and isolate the rule ids failing most often.
2. Disable the offending rule if it is creating queue pressure or broken notifications.
3. Validate action payload assumptions against the triggering event payload.
4. Re-run a single evaluation with internal automation endpoint before re-enabling the rule.

Exit criteria:

- failing execution count stops rising
- replayed evaluation completes successfully

### 5) Tenant Isolation Suspicion (SEV-1)

Detection:

- report of cross-tenant data visibility
- inconsistent tenant-scoped list results

Actions:

1. Freeze risky admin operations for affected scope.
2. Collect request/trace ids from affected calls.
3. Validate repository-level tenant filters in impacted endpoints.
4. Apply minimal forward fix and run tenant safety tests.

Exit criteria:

- tenant audit tests green on affected modules
- no cross-tenant exposure in reproduced scenario

### 6) Database Latency, Connection Saturation, Or Migration Drift

Detection:

- `/health/deep` flips between healthy/degraded with `dependencies.postgresql.healthy=false`
- request latency percentiles rise while API process stays healthy
- post-deploy failures begin after schema change or migration window

Actions:

1. Check connection pool saturation and PostgreSQL wait events.
2. Verify the running schema version matches the intended release.
3. If drift is suspected, stop write-heavy worker and scheduler paths first.
4. Roll forward or back only with a verified migration plan; do not hot-edit schema manually during incident response.

Exit criteria:

- database probe stable for 15 minutes
- no schema mismatch between release artifact and database

### 7) Developer API Abuse Or Misconfiguration

Detection:

- `/metrics/latency.developer_api_error_count` rises sharply
- public API logs show abnormal `401`, `403`, or `5xx` concentration for one app
- support reports credential misuse or excessive polling

Actions:

1. Identify offending developer app and tenant from API logs.
2. Rotate the app secret or disable the installation if misuse is confirmed.
3. Validate scope assignment and tenant installation before restoring access.
4. Notify the integration owner with evidence: endpoint, rate, status codes, and request window.

Exit criteria:

- error count returns to expected baseline
- rotated credentials validated through smoke flow

## Recovery Validation Checklist

- `/health/live`, `/health/ready`, `/health/worker` are green
- `/health/deep.status` is `ok` or known `degraded` with accepted cause
- `/metrics/ops` backlog and failures are not increasing abnormally
- `bash scripts/platform_smoke_check.sh` passes on the deployed release or equivalent environment
- critical smoke tests pass
- incident timeline captured with `request_id` and `trace_id`

## Post-Incident Follow-Up

1. Create RCA within 24 hours.
2. Add preventive test if incident exposed a coverage gap.
3. Add alert threshold tuning if detection was delayed.
4. Update this runbook if procedure changed.