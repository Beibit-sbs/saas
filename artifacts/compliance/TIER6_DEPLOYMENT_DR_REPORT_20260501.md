# TIER-6: Deployment & Disaster Recovery Report

**Date:** 2026-05-01  
**Auditor:** Enterprise Sale Track Automated Audit  
**Scope:** SBS UB Platform — Deployment pipeline, Backup/Restore, DR drills, Incident Response  
**Status:** ✅ PASS (RPO single-host caveat documented)

---

## 6.1 — Deployment Pipeline

### Scripts

| Script | Path | Status |
|--------|------|--------|
| `deploy.sh` | `scripts/deploy.sh` | ✅ EXISTS, executable |
| `backup_db.sh` | `scripts/backup_db.sh` | ✅ EXISTS, executable |
| `restore_db.sh` | `scripts/restore_db.sh` | ✅ EXISTS, executable |

### Deploy Script Security

`scripts/deploy.sh` implements safe deployment practice:

| Check | Result |
|-------|--------|
| `set -euo pipefail` | ✅ Fails fast on any error |
| Runs `preflight_checks.sh` before deploy | ✅ Pre-deploy validation gate |
| Runs `release_gate.sh` before deploy | ✅ All tests must pass |
| `.env` excluded from release archive | ✅ `--exclude='.env'` in tar |
| Uses `~/shared/.env` on server | ✅ Secrets not in artifact |
| Atomic symlink switch `~/current` | ✅ Zero-downtime symlink approach |
| Previous release preserved (`~/previous`) | ✅ Rollback path exists |
| `docker compose up -d --build` on target | ✅ Container re-build on each deploy |

**Gate bypass:** `DEPLOY_SKIP_RELEASE_GATE=true` is logged as `WARN` — not silent. ✅

### Release Gate

`scripts/release_gate.sh` (verified PASS on Day 13 + Day 14 of audit):
- Backend pytest: 6683 passed, 0 failed
- Safe gate: PASS
- Smoke gate: PASS (`passed=9 failed=0`)

---

## 6.2 — Backup Procedure

### `scripts/backup_db.sh`

| Feature | Detail |
|---------|--------|
| Format | `pg_dump --format=custom` (compressed, selective restore) |
| Overwrite protection | Refuses to overwrite unless `BACKUP_ALLOW_OVERWRITE=true` | 
| Timestamped filename | `ai_platform_YYYYMMDD_HHMMSS.dump` |
| Error handling | `set -euo pipefail` |
| Validates env | Checks `DATABASE_URL` and `pg_dump` availability |

### Existing Backup Files

```
backups/
├── dr_rehearsal_platform_source_20260325_020323.dump  (391K)
├── dr_rehearsal_platform_source_20260325_020338.dump  (391K)
└── dr_rehearsal_platform_source_20260325_020351.dump  (391K)
```

3 independent backup dumps from DR rehearsal on 2026-03-25. ✅

---

## 6.3 — Restore Procedure

### `scripts/restore_db.sh`

| Feature | Detail |
|---------|--------|
| Dry-run by default | Validates without touching database |
| Destructive restore | Requires BOTH `--execute` AND `--confirm RESTORE` |
| Credential masking | `mask_database_url()` hides password in logs |
| Error handling | `set -euo pipefail` |
| Input validation | Checks `pg_restore`, `DATABASE_URL`, and dump file |

**Restore is fail-closed by design** — no accidental overwrites. ✅

---

## 6.4 — DR Drills

### Drill 1 — DR-LOCAL-SIM-01 (2026-04-18)

| Metric | Target | Actual |
|--------|--------|--------|
| RTO | 00:05:00 | **00:03:20** ✅ |
| RPO | 00:01:00 | NOT MEASURABLE (single-host) |
| API health endpoints | PASS | ✅ |
| Authentication path | PASS | ✅ |
| Critical workflows | PASS | ✅ |
| Data consistency checks | PASS | ✅ |
| Audit logging continuity | PASS | ✅ |

### Drill 2 — DR-LOCAL-SIM-02 (2026-04-18)

| Metric | Target | Actual |
|--------|--------|--------|
| RTO | 00:05:00 | **00:03:55** ✅ |
| RPO | 00:01:00 | NOT MEASURABLE (single-host) |

**Scenario:** Degraded dependency and recovery simulation.

**After-action artifacts:**
- `artifacts/compliance/DR_MULTI_REGION_AFTER_ACTION_DRILL_01_LOCAL_SIM_20260418.md`
- `artifacts/compliance/DR_MULTI_REGION_AFTER_ACTION_DRILL_02_LOCAL_SIM_20260418.md`

**Note on RPO:** Both drills run on a single-host emulation (no cross-region replica). RPO cannot be measured in this environment. Full multi-region RPO measurement is scheduled with DBA when region-separated data plane is available. This is a known open item, not a blocker for pilot deployment.

---

## 6.5 — Incident Response Runbook

**File:** `docs/INCIDENT_OPS_RUNBOOK.md` ✅

| Runbook Section | Present |
|-----------------|---------|
| Severity levels (SEV-1/2/3) | ✅ |
| Standard incident flow (5-step) | ✅ |
| Key health/metrics endpoints | ✅ |
| Fast triage commands | ✅ |
| Key signals to monitor | ✅ |

**Health endpoints verified:**
- `GET /health/live` — liveness probe
- `GET /health/ready` — readiness probe  
- `GET /health/worker` — background worker health
- `GET /health/deep` — deep system health
- `GET /metrics/ops` — operational metrics
- `GET /metrics/latency` — latency percentiles

---

## 6.6 — Deployment Checklist

**File:** `docs/PILOT_DEPLOYMENT_CHECKLIST.md` ✅

| Item | Status |
|------|--------|
| Pilot deployment checklist documented | ✅ |
| Deployment blueprint documented | ✅ (`docs/DEPLOYMENT_BLUEPRINT.md`) |
| Backup/restore drill documented | ✅ (`docs/BACKUP_RESTORE_DRILL.md`) |
| Guardrails documented | ✅ (`docs/GUARDRAILS.md`) |
| Brain Core admin runbook | ✅ (`docs/BRAIN_CORE_ADMIN_API_RUNBOOK.md`) |
| Runbooks directory | ✅ (`docs/runbooks/`) |

---

## 6.7 — Gate Proof (Latest Two Runs)

From Day 13 (initial gate) and Day 14 (red-team final gate):

| Gate | Day 13 | Day 14 |
|------|--------|--------|
| `university_pilot_safe_gate.sh` | ✅ PASS | ✅ PASS |
| `platform_smoke_check.sh` | ✅ `passed=9 failed=0` | ✅ `passed=9 failed=0` |
| `release_gate.sh` | ✅ PASS | ✅ PASS |
| E2E Playwright smoke | ✅ `50 passed` | ✅ `50 passed` |
| Domain DB integration | ✅ `40 passed` | ✅ `40 passed` |
| Backend pytest | ✅ `6680 passed` | ✅ `6683 passed, 0 failed` |
| Silent failures | ✅ 0 | ✅ 0 |
| Routers without RBAC | ✅ 0 | ✅ 0 |

**Two consecutive gate runs without CRITICAL findings.** ✅

---

## 6.8 — 7-Year Audit Retention

Addressed in dedicated artifact:
- `artifacts/compliance/AUDIT_RETENTION_7Y_ENFORCEMENT_20260501.md`
- Migration `vm01wx23yz45` — schema-level retention policy enforced ✅

---

## 6.9 — NCAAA / ISO 27001 A.17 Business Continuity Mapping

| ISO 27001 Control | Evidence |
|-------------------|---------|
| A.17.1.1 Planning information security continuity | DR drills DR-LOCAL-SIM-01/02 |
| A.17.1.2 Implementing information security continuity | `restore_db.sh` + `backup_db.sh` |
| A.17.1.3 Verify, review and evaluate | 2× drill after-action reports (April 2026) |
| A.17.2.1 Availability of information processing | 3 backup dumps in `backups/` |

---

## Summary

| Category | Status | Notes |
|----------|--------|-------|
| Deployment pipeline | ✅ PASS | Gate-gated, atomic, secret-safe |
| Backup procedure | ✅ PASS | `pg_dump` custom, overwrite-protected |
| Restore procedure | ✅ PASS | Fail-closed, requires explicit `--confirm` |
| DR drills | ✅ PASS | RTO 03:20–03:55 (target 05:00) |
| RPO measurement | ⚠️ OPEN | Single-host only — multi-region drill pending |
| Incident runbook | ✅ PASS | SEV-1/2/3, health endpoints, triage commands |
| Gate proof | ✅ PASS | 2× consecutive clean gates |
| 7-year retention | ✅ PASS | Schema migration + policy artifact |

**Overall: ✅ PASS**  
RPO open item is documented, tracked, and does not block pilot deployment.
