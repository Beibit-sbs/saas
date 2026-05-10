# SBS_UB Module Inventory

> **STATUS: SUPPORTING DRAFT — NOT AUTHORITATIVE**
> SBS_UB.md is the authoritative source of truth. This document is a draft index only.
> Anti-loss audit (A-026.1.B3.A1) must pass before this document is promoted.

## 1. Baseline 150 (Locked)

### Baseline 150 Maturity Metrics
- L0=4
- L1=20
- L2=13
- L3=24
- L4=66
- L5=21
- L6=2
- total=150
- maturity_arithmetic_check=PASS

### Baseline Integrity Rules
- baseline maturity levels are evidence-locked
- baseline and extension metrics are separate planes
- no guessed promotions in docs-only actions

## 2. Extension Registry (Separate Plane)
- extension_total_count=25
- total_tracked_modules=175
- extension/baseline separation=PASS

### Controlled Extension Module Registry
- digital_credentials_wallet
- micro_credentials_stack
- alumni_career_outcomes
- grant_peer_review
- research_data_governance
- llm_eval_harness
- prompt_lifecycle_governance
- knowledge_retrieval_fabric
- ai_model_registry
- model_cost_optimizer
- copilot_safety_ops
- policy_simulation_lab
- incident_command_center
- threat_intel_fusion
- privacy_request_orchestrator
- data_retention_orchestrator
- billing_reconciliation_ops
- revenue_leak_detection
- procurement_vendor_risk
- classroom_iot_telemetry
- energy_optimization_ops
- transport_fleet_ops
- admissions_yield_prediction
- student_success_playbooks
- faculty_workload_optimizer

## 3. Safe Module Level Matrix
| Level | Meaning | Count |
|---|---|---|
| L0 | Planned only | 4 |
| L1 | Foundation stub | 20 |
| L2 | Early implementation | 13 |
| L3 | Feature-ready partial | 24 |
| L4 | Operational partial | 66 |
| L5 | Brain-ready strong | 21 |
| L6 | Full maturity | 2 |

## 4. Capability Verification Pending
- Capability Verification Pending status applies to capability dimensions that are not yet fully evidenced end-to-end.
- VERIFICATION_PENDING is allowed and explicit; it must not be auto-converted into green/full capability status.
- domains requiring strict evidence before promotion include: publish_event behavior, FSM/workflow closure, RBAC/ABAC completeness, KPI lineage proof, dashboard evidence continuity.

## 5. Evidence-Pending Capability Matrix
| Capability Dimension | Current Policy | Allowed Marker |
|---|---|---|
| Backend/API presence | May be marked if evidenced | EVIDENCED |
| publish_event lifecycle | Must be tested and traced | VERIFICATION_PENDING |
| FSM/workflow determinism | Must have transition evidence | VERIFICATION_PENDING |
| RBAC/ABAC completeness | Must have tenant-safe checks | VERIFICATION_PENDING |
| Frontend/dashboard continuity | Must be test-evidenced | VERIFICATION_PENDING |
| Brain recommendation safety | Must be human-gated and traced | VERIFICATION_PENDING |

## 6. Normalization Buckets (Planning View)
- red bucket: weak or missing evidence for required capability dimensions
- yellow bucket: partial evidence, incomplete closure for one or more dimensions
- unknown bucket: source data exists but verification evidence is missing or stale
- green bucket policy: only allowed after full evidence closure, never by assumption

## 7. Canonical Sources
- canonical full 150-row module audit table: A-026.1.B1-SBS_UB_AUDIT_TABLE_AND_INVENTORY_RECONCILIATION_REPORT.md
- baseline 150 inventory source: A-023.0-150_MODULE_EXPANSION_AND_MATURITY_INVENTORY_REPORT.md
- extension registry source: A-025.0-CONTROLLED_EXTENSION_AND_FUTURE_COMPLETENESS_MAP.md
