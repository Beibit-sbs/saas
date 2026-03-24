# Release Gate v1

## Purpose

Release Gate v1 blocks unsafe merges and deploys by enforcing deterministic checks for tenant isolation, platform regressions, frontend regressions, and migration safety.

## Mandatory CI Jobs

The CI workflow defines separate required gates:

- `tenant-safety-gate`
- `platform-regression-gate`
- `frontend-safety-gate`
- `migration-safety-gate`
- `template-validation`

A change is merge-ready only if all required jobs pass.

## Required Checks Before Merge

1. Tenant safety audit passes:
   - `pytest -q tests/platform/test_platform_tenant_safety_audit_v1.py`
2. Platform regression gate passes:
   - `pytest -q tests/platform/`
   - `pytest -q -m security_regression`
3. Frontend safety gate passes:
   - `npm run type-check`
   - `npm run test:frontend`
4. Template validation passes:
   - `pytest -q tests/test_template_validation.py`

## Required Checks Before Deploy

Run local pre-release command:

```bash
bash scripts/release_check.sh
```

This script enforces:

- backend tenant safety gate
- backend platform regression gate
- critical security regression tests
- migration smoke (`upgrade -> downgrade -1 -> re-upgrade`)
- frontend type-check and tests

Any failure returns non-zero and blocks release.

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

No additional CI infrastructure is introduced in v1.
