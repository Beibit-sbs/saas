# Release Gate v1

## Purpose

Release Gate v1 blocks unsafe merges and deploys by enforcing deterministic checks for tenant isolation, platform regressions, frontend regressions, and migration safety.

Current validated baseline snapshot (2026-04-06):
- Architecture governance gate: 7 passed
- Tenant safety gate: 8 passed
- Platform regression gate: 439 passed, 9 skipped
- Security regression gate: 42 passed
- Template validation gate: 5 passed
- Frontend safety gate: 147 passed
- Migration safety gate: head `d4c5e6f7a8b9`

Canonical release checklist:

- `docs/RELEASE_CHECKLIST.md`

## Mandatory CI Jobs

The CI workflow defines separate required gates:

- `architecture-governance-gate`
- `tenant-safety-gate`
- `platform-regression-gate`
- `security-regression-gate`
- `frontend-safety-gate`
- `migration-safety-gate`
- `template-validation`

A change is merge-ready only if all required jobs pass.

## Required Checks Before Merge

1. Tenant safety audit passes:
   - `pytest -q tests/platform/test_platform_tenant_safety_audit_v1.py`
2. Architecture governance guardrails pass:
   - `pytest -q tests/platform/test_platform_architecture_guardrails_v1.py`
3. Platform regression gate passes:
   - `pytest -q tests/platform/`
   - `pytest -q -m security_regression`
4. Frontend safety gate passes:
   - `npm run type-check`
   - `npm run test:frontend`
5. Template validation passes:
   - `pytest -q tests/test_template_validation.py`

## Required Checks Before Deploy

Run unified Docker pre-release command:

```bash
bash scripts/release_gate.sh
```

This command enforces:

- backend tenant safety gate
- backend architecture governance gate
- backend platform regression gate
- critical security regression tests
- template validation
- migration safety (`alembic heads`, `alembic upgrade head`)
- frontend type-check and tests
- rollback readiness checks (latest backup artifact + restore tooling validation)

Any failure returns non-zero and blocks release.

Optional explicit modes:

- `RELEASE_ENABLE_MIGRATION_ROLLBACK_TEST=true` to run `downgrade -1 -> re-upgrade`
- `RELEASE_ENABLE_SMOKE_GATE=true` to include `scripts/platform_smoke_check.sh`
- `ROLLBACK_ENABLE_RESTORE_DRILL=true` when isolated restore-rehearsal DB is provisioned

## Migration Safety Expectations

Migration safety gate uses a test PostgreSQL database and requires:

1. `alembic heads` to log current heads
2. `alembic upgrade head`
3. `alembic downgrade -1`
4. `alembic upgrade head`

This catches:

- broken migration graph/head resolution
- irreversible recent migration issues
- re-apply failures after rollback of latest revision

## Tenant Safety Gate Strategy

Tenant isolation is treated as a hard release blocker. The dedicated gate is intentionally isolated for readability and quick diagnosis.

Blocking rule:

- any failure in `tests/platform/test_platform_tenant_safety_audit_v1.py` blocks merge and release

## What Blocks A Release

Release is blocked when any of these occur:

- tenant safety audit fails
- architecture governance guardrails fail
- platform regression suite fails
- security regression marker suite fails
- TypeScript type-check fails
- frontend tests fail
- migration smoke fails
- template validation fails

## Fast vs Long Pipeline Split

Current split keeps execution simple and readable:

- fast safety gates:
  - `tenant-safety-gate`
  - `frontend-safety-gate`
  - `template-validation`
- deeper safety gates:
  - `platform-regression-gate`
  - `migration-safety-gate`
   - `test-evidence-artifacts`
   - `frontend-role-zones-e2e-gate`
- release aggregate gate:
   - `release-readiness-gate` (fails if any required gate failed)

No additional CI infrastructure is introduced in v1.

## Scope Notes

- Admin console quality is currently higher than role-specific end-user portals.
- Student/faculty full UX journeys are tracked as productization work and should be explicitly validated in pilot release criteria for derived projects.
