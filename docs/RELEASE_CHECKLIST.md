# Release Checklist

## Purpose

This is the canonical release checklist for Docker release readiness, deployment approval, and rollback evidence.

Use this checklist together with:

- `bash scripts/release_gate.sh`
- `docs/RELEASE_GATE.md`
- `docs/BACKUP_RESTORE_DRILL.md`
- `docs/runbooks/RECOVERY.md`

## 1. Pre-Merge Gate Evidence

All required merge gates must be green in CI:

- `architecture-governance-gate`
- `tenant-safety-gate`
- `platform-regression-gate`
- `security-regression-gate`
- `frontend-safety-gate`
- `migration-safety-gate`
- `template-validation`

Blocking rule:

- If any gate is red, the change is not merge-ready.

Evidence to record:

- commit SHA
- branch / pull request
- CI run URL
- failed gate name if blocked

## 2. Docker Release Gate

Before deploy, run:

```bash
bash scripts/release_gate.sh
```

Expected outcome:

- release checks pass
- rollback readiness checks pass
- command exits with `0`

Optional explicit modes:

- `RELEASE_ENABLE_MIGRATION_ROLLBACK_TEST=true`
- `RELEASE_ENABLE_SMOKE_GATE=true`
- `ROLLBACK_ENABLE_RESTORE_DRILL=true`

Evidence to record:

- command used
- exit code
- log path if archived

## 3. Deployment Preconditions

Confirm before deployment starts:

- target environment `.env` reviewed
- latest backup exists and path is recorded
- previous release artifact or rollback target is available
- deployment owner and rollback owner are identified
- deployment window and validation window are announced

## 4. Immediate Post-Deploy Validation

Validate after deploy:

- `/health/live` returns `200`
- `/health/ready` returns `200`
- `/health/deep` shows `dependencies.postgresql.healthy=true`
- `/health/worker` reports reachable heartbeat
- smoke validation passes in target environment
- no tenant isolation anomaly is observed
- no sustained `5xx` spike is observed

## 5. Rollback Readiness

Rollback evidence must exist before sign-off:

- latest backup artifact is readable
- `scripts/backup_db.sh` and `scripts/restore_db.sh` are executable
- restore procedure is documented in `docs/BACKUP_RESTORE_DRILL.md`
- recovery procedure is documented in `docs/runbooks/RECOVERY.md`
- destructive restore requires explicit operator confirmation

If an isolated rehearsal DB is available, additionally record:

- restore start time
- restore finish time
- total restore duration
- validation result after restore

## 6. Sign-Off Record

Record final sign-off with:

- release SHA
- environment
- release gate result
- smoke result
- backup artifact path
- rollback owner
- approver name
- timestamp

## 7. Stop Conditions

Do not continue release if any of these are true:

- any required CI gate is red
- docker `scripts/release_gate.sh` fails
- backup artifact is missing or unreadable
- rollback target is unknown
- smoke validation fails
- tenant isolation or permission anomaly is detected