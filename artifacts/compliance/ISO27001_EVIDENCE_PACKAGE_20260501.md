# ISO 27001 Evidence Package (Annex A)

## Scope

- Prepared on (UTC): 2026-05-01
- Prepared by: Platform Engineering
- Scope: SBS University Brain platform baseline (backend, frontend, infra, gates, observability)
- Purpose: Enterprise buyer due diligence package (GCC track)
- Certification status: Not an external certification report; evidence package only

## Baseline Validation Snapshot

- Safe gate: PASS
- Smoke gate: PASS (passed=9 failed=0)
- Release gate: PASS
- E2E smoke: PASS (50 passed)
- Domain DB integration matrix: PASS (40 passed)

## Annex A Control Mapping (Evidence-Backed)

| ISO 27001 Control | Control Area | Evidence Source | Status |
|---|---|---|---|
| A.9 Access Control | RBAC + tenant isolation | `GCC_TENANT_ISOLATION_PROOF_20260501.md`, Day 2 Security Gap Matrix, security regression/gate outputs | VERIFIED |
| A.12 Operations Security | Operational release safety and quality gates | `scripts/university_pilot_safe_gate.sh`, `scripts/platform_smoke_check.sh`, `scripts/release_gate.sh`, Day 13-14 gate logs | VERIFIED |
| A.13 Communications Security | Tenant-safe data handling and request isolation boundaries | `GCC_TENANT_ISOLATION_PROOF_20260501.md`, domain endpoint smoke and DB integration results | VERIFIED |
| A.14 System Acquisition, Development and Maintenance | Data integrity and regression controls | Day 9 Data Integrity Report, domain DB matrix (40/40), contract/openapi regression pass | VERIFIED |
| A.16 Incident Management | Observability and incident detection readiness | Day 12 Observability Readiness Pack, alert gate pass (`F3.5_ALERT_GATE=PASS`) | VERIFIED |
| A.17 Information Security Aspects of Business Continuity Management | Backup and rollback readiness | DR rehearsal artifacts in `backups/`, release gate rollback-readiness PASS | VERIFIED |
| A.18 Compliance | GCC compliance matrix and PDPL-aligned artifacts | GCC matrix in `AUDIT_14_STRICT_PLAN.md` section 10.2, GCC compliance files in `artifacts/compliance/` | PARTIAL |

## Included Files

- `GCC_ENTERPRISE_SALE_TRACK_ARTIFACT_PACK_20260501.md`
- `GCC_PDPL_SECTION14_COMPLIANCE_STATEMENT_20260501.md`
- `GCC_TENANT_ISOLATION_PROOF_20260501.md`
- `GCC_AUDIT_TRAIL_RETENTION_POLICY_7Y_20260501.md`
- `GCC_DATA_DELETION_RIGHT_TO_ERASURE_PROCEDURE_20260501.md`

## Residual Gaps (Explicit)

- 7-year audit retention is documented at policy level; platform enforcement remains TBD.
- Data deletion/right-to-erasure is documented at process level; dedicated API implementation remains TBD.
- This package supports customer due diligence and internal governance; third-party ISO audit attestation is out of scope.

## Conclusion

ISO 27001-aligned evidence package is assembled and review-ready for GCC sales track discussions, with residual gaps explicitly documented above.
