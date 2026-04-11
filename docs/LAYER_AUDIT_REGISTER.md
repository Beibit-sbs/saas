# Layer Audit Register

Date: 2026-04-09  
Owner: Platform Engineering

## Purpose

This register defines how every platform layer is audited with explicit evidence.

Primary objective:
- prevent false-green full audits where one layer (for example data layer) is not explicitly validated.

## Mandatory Full Audit Command

```bash
make system-audit
```

Expected evidence artifact:
- `artifacts/audits/system-audit-<UTCSTAMP>.txt`

A release candidate is non-compliant if artifact is missing or if any required layer section is absent.

## Layer Coverage Matrix

1. Core layer
- scope: architecture guardrails, tenant safety baseline, core code quality
- checks:
  - `ruff check .`
  - `pytest -q tests/platform/test_platform_architecture_guardrails_v1.py`
  - `pytest -q tests/platform/test_platform_tenant_safety_audit_v1.py`

2. Application layer
- scope: backend application behavior regressions
- checks:
  - `pytest -q --disable-warnings`

3. Security layer
- scope: security regression markers
- checks:
  - `pytest -q --disable-warnings -m security_regression`

4. Access layer
- scope: frontend/backend permission parity (RBAC contract)
- checks:
  - `scripts/check_permission_parity.sh`

5. Frontend layer
- scope: lint + behavior tests
- checks:
  - `npm run lint`
  - `npm run test:frontend`

6. Domain layer
- scope: educational workflow consistency and tenant-safe domain behavior
- checks:
  - `scripts/domain_layer_gate.sh`

7. Data layer
- scope: migration safety, tenant/context integrity, persistence/reconciliation checks
- checks:
  - `scripts/data_layer_gate.sh`

8. Ops layer
- scope: rollback readiness and backup artifact guardrails
- checks:
  - `scripts/rollback_check.sh`

## Evidence Retention Policy

For each release candidate keep:
- latest successful `system-audit` artifact path;
- commit SHA used for audit run;
- operator and timestamp;
- explicit confirmation that all layer sections are present and green.

Minimum retention recommendation:
- keep last 20 successful full-audit artifacts per environment.

## Audit Review Checklist

1. Verify artifact exists: `artifacts/audits/system-audit-<UTCSTAMP>.txt`.
2. Verify sections exist for all 8 layers.
3. Verify each section has successful command output and no failed command.
4. Attach artifact path and commit SHA to release ticket/change request.

## Related Documents

- `docs/RELEASE_GATE.md`
- `docs/DATA_LAYER_AUDIT_REGISTER.md`
- `docs/domain-layer-max-upgrade-roadmap.md`