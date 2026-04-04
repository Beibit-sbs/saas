# Pilot Deployment Checklist

## Purpose

This checklist is the final go-live gate for the university pilot.

For canonical release discipline and evidence fields, use `docs/RELEASE_CHECKLIST.md` together with this pilot-specific checklist.

## Pre-Deployment

1. Release artifact built and versioned.
2. `bash scripts/release_gate.sh` passes.
3. `bash scripts/platform_smoke_check.sh` passes in the target environment or an equivalent pre-prod stack.
4. Tenant safety and RBAC isolation tests are green.
5. Backup created and backup file path recorded.
6. Restore drill owner, target window, and recovery objective documented.
7. Environment variables validated:
   - `DATABASE_URL`
   - `REDIS_URL`
   - `JWT_SECRET`
   - `API_BASE_URL`
   - `ADMIN_PANEL_URL`
   - `INTERNAL_API_TOKEN` or `PLATFORM_INTERNAL_TOKEN` according to deployment wiring
8. Role mapping for `platform_admin`, `institution_admin`, `academic_admin`, `it_support`, `developer`, and `ops_engineer` approved.
9. Feature flag matrix reviewed and per-tenant exceptions documented.
10. Rollback release symlink or previous artifact confirmed available.

## Deployment Window

1. Freeze non-essential admin changes.
2. Announce deployment start and expected validation window.
3. Deploy release artifact to the application host.
4. Restart in this order:
   - API
   - worker
   - scheduler
5. Confirm reverse proxy health and TLS reachability.

## Immediate Validation

1. `GET /health` returns `200`.
2. `GET /health/db` returns expected status for the environment.
3. `GET /health/worker` returns reachable heartbeat.
4. `GET /health/comprehensive` is `healthy` or approved `degraded`.
5. `GET /metrics/ops` exposes:
   - `dead_webhooks`
   - `dead_automation_executions`
   - `dead_jobs`
6. `GET /metrics/latency` exposes `developer_api_error_count`.
7. `bash scripts/platform_smoke_check.sh` passes.

## Pilot Governance Validation

1. Ops Console visible only to authorized operational roles.
2. Developer Apps console visible only to developer-capable roles.
3. Federation surfaces visible only to approved institution/platform admins.
4. No cross-tenant data is visible in tenant-scoped admin walkthroughs.

## First 30 Minutes After Deploy

1. Watch `event_queue_size`, `retry_backlog`, `failed_webhooks`, and `developer_api_error_count`.
2. Confirm no repeating `automation_execution_failed` or `webhook_delivery_exhausted` bursts.
3. Confirm AI Copilot and KPI refresh complete for at least one tenant.
4. Confirm at least one developer app auth flow remains healthy if enabled.

## Rollback Criteria

Rollback immediately if any of the following occur:

- persistent `5xx` growth after restart
- tenant isolation anomaly
- worker heartbeat missing after restart attempts
- webhook retry backlog grows without recovery path
- smoke script fails on core paths

## Rollback Steps

1. Repoint current symlink or deployment target to the previous release.
2. Restart API, worker, and scheduler.
3. Re-run health endpoints.
4. Re-run smoke script.
5. Open incident timeline and attach request ids / trace ids.

## Sign-Off

| Checkpoint | Owner | Status |
| --- | --- | --- |
| Release gate | TBD | TBD |
| Smoke gate | TBD | TBD |
| Backup ready | TBD | TBD |
| RBAC mapping approved | TBD | TBD |
| Pilot business sign-off | TBD | TBD |