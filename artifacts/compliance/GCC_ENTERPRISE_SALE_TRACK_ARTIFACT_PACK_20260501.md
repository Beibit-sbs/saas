# GCC Enterprise Sale Track Artifact Pack

## Scope

This pack provides compliance-facing evidence for enterprise sales and due-diligence in GCC markets (including Saudi Arabia), using production-like controls validated in the current platform baseline.

- Prepared on (UTC): 2026-05-01
- Prepared by: Platform Engineering
- Applicable system: University management SaaS platform
- Data classification: Multi-tenant, mixed operational + academic records

## Included Artifacts

1. PDPL section 14 compliance statement:
   - [GCC_PDPL_SECTION14_COMPLIANCE_STATEMENT_20260501.md](GCC_PDPL_SECTION14_COMPLIANCE_STATEMENT_20260501.md)
2. Tenant isolation proof:
   - [GCC_TENANT_ISOLATION_PROOF_20260501.md](GCC_TENANT_ISOLATION_PROOF_20260501.md)
3. Audit trail 7-year retention policy:
   - [GCC_AUDIT_TRAIL_RETENTION_POLICY_7Y_20260501.md](GCC_AUDIT_TRAIL_RETENTION_POLICY_7Y_20260501.md)
4. Data deletion and right-to-erasure procedure:
   - [GCC_DATA_DELETION_RIGHT_TO_ERASURE_PROCEDURE_20260501.md](GCC_DATA_DELETION_RIGHT_TO_ERASURE_PROCEDURE_20260501.md)
5. Brain Core demo rehearsal runbook and evidence:
   - [BRAIN_CORE_DEMO_RUNBOOK_20260501.md](BRAIN_CORE_DEMO_RUNBOOK_20260501.md)
6. Performance benchmarks certification (p99 latency, SLA declarations):
   - [PERFORMANCE_BENCHMARKS_CERTIFICATION_20260501.md](PERFORMANCE_BENCHMARKS_CERTIFICATION_20260501.md)

## Validation Evidence References

- Smoke gate script: [scripts/platform_smoke_check.sh](../../scripts/platform_smoke_check.sh)
- Release gate script: [scripts/release_gate.sh](../../scripts/release_gate.sh)
- Domain DB integration tests:
  - [backend/tests/test_domain_module_db_integration.py](../../backend/tests/test_domain_module_db_integration.py)
- Domain endpoint smoke tests:
  - [backend/tests/test_domain_endpoint_smoke_http200.py](../../backend/tests/test_domain_endpoint_smoke_http200.py)

## Current Baseline Result

- platform_smoke_check: PASS (9/9 checks)
- release_gate: PASS
- educational domain gate: PASS
- data layer gate: PASS
- rollback readiness check: PASS

## Commercial Use Note

This artifact pack is prepared for customer security and compliance review. Contract-level legal interpretation must be validated by legal counsel in the target jurisdiction.
