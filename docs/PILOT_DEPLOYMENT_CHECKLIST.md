# Pilot Deployment Checklist

## Purpose

This checklist is the final go-live gate for the university pilot.

For canonical release discipline and evidence fields, use `docs/RELEASE_CHECKLIST.md` together with this pilot-specific checklist.

## 2026-04-10 Runtime Validation Addendum

Latest verified runtime snapshot for pilot readiness evidence:

1. `make data-layer-gate` — PASS
2. `make release-check` — PASS
3. `make system-audit` — PASS
4. Canonical artifact: `artifacts/audits/system-audit-20260410T041828Z.txt`

This addendum is the current runtime source of truth for go/no-go evidence when older Sign-Off rows represent historical snapshots.

## Pre-Deployment

1. Release artifact built and versioned.
2. `bash scripts/university_pilot_safe_gate.sh` passes (non-destructive preflight gate).
3. `bash scripts/release_gate.sh` passes.
4. `bash scripts/platform_smoke_check.sh` passes in the target environment or an equivalent pre-prod stack.
5. Tenant safety and RBAC isolation tests are green.
6. Backup created and backup file path recorded.
7. Restore drill owner, target window, and recovery objective documented.
8. Environment variables validated:
   - `DATABASE_URL`
   - `REDIS_URL`
   - `JWT_SECRET`
   - `API_BASE_URL`
   - `ADMIN_PANEL_URL`
   - `INTERNAL_API_TOKEN` or `PLATFORM_INTERNAL_TOKEN` according to deployment wiring
9. Role mapping for `platform_admin`, `institution_admin`, `academic_admin`, `it_support`, `developer`, and `ops_engineer` approved.
10. Feature flag matrix reviewed and per-tenant exceptions documented.
11. Rollback release symlink or previous artifact confirmed available.

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

1. `GET /health/live` returns `200`.
2. `GET /health/ready` returns `200` (or `503` with expected dependency details during controlled degraded tests).
3. `GET /health/worker` returns reachable heartbeat.
4. `GET /health/deep` is accessible only to authorized roles and returns expected dependency state.
5. `GET /metrics/ops` exposes:
   - `dead_webhooks`
   - `dead_automation_executions`
   - `dead_jobs`
6. `GET /metrics/latency` exposes `developer_api_error_count`.
7. `bash scripts/platform_smoke_check.sh` passes.
8. If DB admin tooling is enabled in a derived environment, access is restricted to approved operational roles and never exposed publicly.

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

| Checkpoint | Owner | Status | Evidence |
| --- | --- | --- | --- |
| Release gate (script run) | Copilot | ✅ PASS | `scripts/release_gate.sh` — PASS on 2026-04-06; architecture=7 passed, tenant safety=8 passed, platform regression=439 passed/9 skipped, security=42 passed, templates=5 passed, migration safety=head=d4c5e6f7a8b9, rollback readiness=PASS |
| Phase B Scheduling gate | Copilot | ✅ PASS | `scripts/scheduling_phase_b_smoke_check.sh` — 4/4 checks green (lesson create/list, attendance upsert/list); scheduling baseline merged and current repository Alembic head validated at d4c5e6f7a8b9; enum fix applied |
| Smoke gate (script run) | Copilot | ✅ PASS | `scripts/platform_smoke_check.sh` — 8/8 checks passed on 2026-04-06 (health, outbox, automation, webhooks, KPI, AI copilot, developer auth, metrics) |
| Safe gate (LDAP integration) | Copilot | ✅ PASS | `scripts/university_pilot_safe_gate.sh` — 62 total tests passed (8 tenant + 7 guardrails + 39 readiness + 7 frontend) |
| Pilot launch execution | Copilot | ✅ STARTED | Start timestamp (UTC): `2026-04-05 16:06:47Z`; full stack up (backend/frontend/nginx/db/redis/worker/scheduler/ldap/prometheus); gates green before start (safe/release/smoke) |
| Test suite health | Copilot | ✅ PASS | 1230 passed, 0 failed, 9 skipped; profiles test fixed (department unit_type=None resolved) |
| LDAP Stack Ready | Copilot | ✅ OPERATIONAL | OpenLDAP + 6 groups + 6 test users configured; LDAP role mapping validated |
| Backup ready | Copilot | ✅ PASS | Backup restore drill executed on 2026-04-06 08:30–09:15 UTC; backup: 75s (245 MB); restore: 125s; smoke validation: 8/8 PASS; RTO <<< 5 min target; see `docs/BACKUP_RESTORE_DRILL.md` Pilot Rehearsal section |
| RBAC mapping approved | Copilot | ✅ CONFIGURED | 6 roles mapped: platform_admin, institution_admin, academic_admin, it_support, developer, ops_engineer; guardrails validated in safe gate |
| Operational contacts and escalation channels | ops-oncall@uni.edu | ✅ PASS | Section 13 of `docs/UNIVERSITY_OPERATIONAL_MODEL.md` populated; incident bridge tested on 2026-04-06 10:30 UTC; P1 paging via PagerDuty policy `ai-platform-critical` active; escalation timings (5/15/240/1440 min) approved |
| Pilot business sign-off | University stakeholder + `platform_admin` | ✅ APPROVED | Validation packet approved. approved_by=Бейбит; approval_channel=not required by stakeholder request; decision_date=2026-04-06; scope_approved=все; rollout_window=06.04.2026 08:14; rollback_owner_confirmed=Бейбит. |