# SBS_UB Evidence Index

> **STATUS: SUPPORTING DRAFT — NOT AUTHORITATIVE**
> SBS_UB.md is the authoritative source of truth. This document is a draft index only.
> Anti-loss audit (A-026.1.B3.A1) must pass before this document is promoted.

## 1. Backend Full Regression and Coverage Baseline
- authoritative full backend regression after blocker remediation:
  - 9070 passed, 28 skipped, 88 deselected, 7 warnings
  - exit code: 0
- coverage baseline:
  - 87.07
  - threshold policy: PASS when >= 80

## 2. Tenant and Security Regression Evidence
- tenant/security regression slice: PASS
- cross-tenant leakage checks: fail-closed policy validated
- ministry KPI suppression/whitelist/audit contract: validated in baseline wave evidence

## 3. Frontend Evidence
- frontend full tests: PASS
- 118 files passed, 814 tests passed
- frontend lint: PASS
- frontend build: PASS
- accepted warning profile retained where explicitly classified non-blocking

## 4. Gates and Release Evidence
- safe gate: PASS
- smoke gate: PASS
- release gate: PASS
- release classification accepts non-blocking infrastructure warning only when explicitly documented

## 5. Targeted Tests by Action
- A-024.8.B2 and A-024.8.B3: full backend + continuity packs + frontend reruns
- A-025.3: rector KPI drilldown backend and frontend focused test packs
- A-026.1.B2-RUNTIME: import sanity PASS, targeted runtime tests PASS, narrow neighboring regression PASS

## 6. Accepted Warnings Policy
- warnings can be accepted only when:
  - tests remain green
  - behavior is deterministic and non-destructive
  - warning category is documented and classified as non-blocking
- warnings cannot be used to hide failing regressions

## 7. Stale Image Rule
- stale image risk must be cleared before baseline confirmations that depend on rebuilt test images
- if evidence run is image-sensitive, rebuild backend-tests/frontend-tests image before final verdict

## 8. Timeout-Prone Selector Rule
- broad selector runs may timeout in this environment
- required mitigation: use explicit file-list regression pack for deterministic execution and evidence capture
- file-list approach is preferred when timeout risk is known

## 9. Canonical Evidence Sources
- A-024.8.B1-FULL_REGRESSION_COVERAGE_GATE_BASELINE_REPORT.md
- A-024.8.B2-BLOCKING_REGRESSION_REMEDIATION_REPORT.md
- A-024.8.B3-QUALITY_BASELINE_CONFIRMATION_REPORT.md
- A-025.3-RECTOR_KPI_DRILLDOWN_EVIDENCE_IMPLEMENTATION_REPORT.md
- A-026.1.B1-SBS_UB_AUDIT_TABLE_AND_INVENTORY_RECONCILIATION_REPORT.md
