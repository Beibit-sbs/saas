# SBS_UB 150 Module Normalization

## A-026.2 Scope
- Action: A-026.2
- Date: 2026-05-11
- Mode: planning/docs-only
- Authoritative tracker: SBS_UB.md
- This file role: dedicated working normalization source for baseline 150 modules

## Baseline and Extension Separation (Locked)
- Baseline target modules: 150
- Baseline maturity: L0=4, L1=20, L2=13, L3=24, L4=66, L5=21, L6=2
- Baseline arithmetic: PASS (4+20+13+24+66+21+2=150)
- Extension modules: 25
- Total tracked modules: 175
- Separation policy: baseline and extension remain separate planes

## Normalization Philosophy
1. No fake green.
2. No guessed capability status.
3. No maturity movement without implementation plus validation.
4. L0/L1/L2 are acceptable when honest, but each needs remediation path.
5. L4/L5/L6 cannot be claimed without API/frontend/evidence/Brain/E2E proof.
6. Baseline 150 and extension 25 remain separate.
7. Killer flows remain paused until normalization plan is accepted.
8. Every red/yellow/unknown item maps to real work, not symbol changes.

## Maturity Level Criteria

### L0 - Planned / no runtime foundation
Required evidence:
- listed in canonical baseline
- no fake implementation claim

### L1 - Foundation stub
Required evidence:
- module package exists
- FOUNDATION.md or equivalent exists
- __init__.py exists
- import path may exist
- no service/API claim unless present

### L2 - Contract/service skeleton
Required evidence:
- service.py or contract exists
- tenant validation or guard constants where applicable
- FSM/status constants where applicable
- import/contract tests
- no fake business logic claim

### L3 - Deterministic backend business logic
Required evidence:
- deterministic service functions
- tenant fail-closed behavior
- domain rules/status/risk/classification logic
- targeted tests
- no fake API/frontend claim

### L4 - Operational visibility / API / dashboard readiness
Required evidence:
- read-only or controlled API endpoint where product-relevant
- frontend/admin/dashboard visibility if applicable
- backend tests
- frontend tests if frontend exists
- tenant/security checks
- KPI/evidence summary where relevant

### L5 - Brain/governance/evidence readiness
Required evidence:
- KPI/evidence lineage
- Brain signal candidate or governance mapping
- human review boundary where decisions are involved
- audit/evidence trail
- dashboard/queue visibility
- no autonomous critical action

### L6 - Full production/e2e maturity
Required evidence:
- cross-feature E2E
- full regression/coverage
- frontend tests/lint/build
- tenant/security regression
- safe gate
- smoke gate
- release gate
- rollback readiness

## Gap Taxonomy
| Gap Type | Meaning | Evidence Required To Clear | Target Level Impact | Priority |
|---|---|---|---|---|
| foundation_missing | Module is planned or package-only | package plus foundation artifacts and import viability | L0/L1 -> L2 readiness | high |
| service_contract_missing | service/contract skeleton absent or incomplete | service contract, typed I/O, deterministic stubs | L1 -> L2 | high |
| tenant_guard_missing | tenant fail-closed guards absent or unverified | tenant context checks, negative tests | L2+ hardening | high |
| FSM_workflow_missing | status flow/FSM not explicit | status constants, transition rules, tests | L2 -> L3 | high |
| API_missing | product-relevant API not exposed | router endpoint contract tests | L3 -> L4 | medium |
| frontend_missing | operational visibility absent where required | admin/dashboard visibility and frontend tests | L3 -> L4 | medium |
| tests_missing | insufficient deterministic or contract tests | backend unit/contract tests, negative tests | any level confidence | high |
| publish_event_missing | domain event publication missing/unverified | event emit contract and tests | L3/L4 -> L5-readiness | medium |
| KPI_evidence_missing | KPI lineage not mapped | KPI lineage map and audit proof | L4 -> L5-readiness | medium |
| Brain_mapping_missing | Brain signal mapping not established | Brain candidate mapping plus review boundary | L4 -> L5-readiness | medium |
| dashboard_UX_missing | review/queue dashboard not available | dashboard backlog item and testable acceptance | L4 -> L5-readiness | medium |
| tenant_safety_unverified | cross-tenant behavior unverified | fail-closed and isolation regression tests | any operational level | high |
| E2E_gate_missing | no gate-level evidence | safe/smoke/release gate evidence | L5 -> L6 | high |
| verification_pending | capability claim not yet verified by evidence | direct file/test/route evidence anchors | prevents false-green claims | high |

## Baseline 150 Remediation Buckets
| Bucket | Current Levels | Module Count | Main Gap | Target Outcome | A-026.x Action |
|---|---|---:|---|---|---|
| Bucket A - L0/L1 Foundation Normalization | L0-L1 | 24 | foundation and contract gaps | L2-ready foundations | A-026.3 |
| Bucket B - L2 Service Contract Normalization | L2 | 13 | deterministic service logic gaps | L3 deterministic backend slices | A-026.4 |
| Bucket C - L3 Operational Visibility Normalization | L3 | 24 | API/visibility/test depth gaps | L4 operational readiness | A-026.5 |
| Bucket D - L4 Brain/Evidence Readiness | L4 | 66 | KPI/evidence/Brain mapping gaps | selective L5-readiness candidates | A-026.6 |
| Bucket E - L5 E2E/Gate Closure | L5 | 21 | gate continuity and E2E closure | selective L6 proofs | A-026.7 |
| Bucket F - Preserve / Regression Only | L6 | 2 | regression risk only | preserve quality baseline | A-026.7 |

## Initial Module Normalization Matrix (Safe)
Note:
- This is an initial verified subset.
- Full 150 row-by-row capability matrix is VERIFICATION_PENDING and will be expanded in A-026.3/A-026.4 with direct evidence anchors.
- No row in this section implies achieved target level.

| # | Module | Current Level | Bucket | Verified Evidence Source | Primary Gap | Target Next Level | Required Work | Required Tests | Risk | Priority |
|---:|---|---:|---|---|---|---:|---|---|---|---|
| 1 | human_approved_timetable_workflow | L0 | A | A-023.0 section 9 + SBS_UB A-022 references | foundation_missing | L2 | create foundation package and deterministic service contract plan | import/contract tests | medium | high |
| 2 | timetable_change_proposal | L0 | A | A-023.0 section 9 | foundation_missing | L2 | define proposal service contract and status model | service contract tests | medium | high |
| 3 | timetable_change_simulation | L0 | A | A-023.0 section 9 | service_contract_missing | L2 | define simulation service interface and input validation | contract and negative tests | medium | high |
| 4 | timetable_recommendation_bridge | L0 | A | A-023.0 section 9 | service_contract_missing | L2 | define deterministic recommendation bridge contract | contract tests | medium | high |
| 5 | timetable_approval_queue | L1 | A | A-023.0 section 9 | service_contract_missing | L2 | add queue service skeleton and status constants | import and contract tests | medium | high |
| 6 | timetable_change_kpi_dashboard | L1 | A | A-023.0 section 9 | verification_pending | L2 | verify backend contract dependency before dashboard claims | verification checklist tests | medium | medium |
| 7 | workload_management | L1 | A | A-023.0 section 9 | service_contract_missing | L2 | design deterministic workload service contract | contract tests | medium | high |
| 8 | notification_center | L1 | A | A-023.0 section 9 | tenant_guard_missing | L2 | define tenant-safe notification contract | tenant negative tests | medium | high |
| 9 | library_circulation | L2 | B | A-023.0 section 9 | tests_missing | L3 | move from skeleton to deterministic rules | targeted backend tests | medium | high |
| 10 | research_grants | L2 | B | A-023.0 section 9 | FSM_workflow_missing | L3 | define deterministic status transitions | transition tests | medium | high |
| 11 | ai_plagiarism | L2 | B | A-023.0 section 9 | tenant_safety_unverified | L3 | verify fail-closed tenant behavior | tenant regression tests | high | high |
| 12 | ai_guardrails | L3 | C | A-023.0 section 9 | API_missing | L4 | evaluate product-relevant controlled API exposure | route contract tests | medium | medium |
| 13 | sso_saml | L3 | C | A-023.0 section 9 | operational_visibility missing | L4 | verify admin visibility and support diagnostics | backend plus visibility tests | medium | medium |
| 14 | university_core | L3 | C | A-023.0 section 9 | verification_pending | L4 | evidence reconsolidation before visibility claims | verification tests | medium | medium |
| 15 | grades | L4 | D | A-023.0 section 9 + A-024.8 summary | KPI_evidence_missing | L5 | define KPI/evidence lineage candidates | lineage contract checks | medium | medium |
| 16 | faculty | L4 | D | A-023.0 section 9 + A-024.8 summary | Brain_mapping_missing | L5 | map candidate brain signals with human review boundary | mapping validation tests | medium | medium |
| 17 | operations | L5 | E | A-023.0 section 9 + A-026.0 plan | E2E_gate_missing | L6 | select narrow E2E path and gate evidence plan | gate continuity tests | high | medium |
| 18 | scheduling | L6 | F | A-023.0 section 10 + A-024.8.B3 | preserve_only | L6 | no inflation, regression-only protection | regression/smoke continuity | medium | high |

## A-026.3 First Implementation Batch (Planning Selection)
Constraint profile:
- 5-10 modules
- foundation/service normalization
- no frontend-first scope
- no Brain autonomy
- no L5/L6 claims

| Selected Module | Current Level | Target Level | Why Selected | Required Work | Required Tests | Risk |
|---|---:|---:|---|---|---|---|
| human_approved_timetable_workflow | L0 | L2 | high leverage workflow dependency | foundation plus service contract scaffold | import and contract tests | medium |
| timetable_change_proposal | L0 | L2 | core change request domain | deterministic proposal contract | schema/contract tests | medium |
| timetable_change_simulation | L0 | L2 | blocks later KPI and approval logic | simulation contract and input guards | negative and contract tests | medium |
| timetable_recommendation_bridge | L0 | L2 | bridge prerequisite for later governance | deterministic bridge service contract | deterministic unit tests | medium |
| timetable_approval_queue | L1 | L2 | required for bounded human review workflow | queue contract and status constants | contract plus transition tests | medium |
| timetable_change_kpi_dashboard | L1 | L2 | KPI dashboard depends on backend contract | backend-facing contract normalization only | contract tests | medium |
| workload_management | L1 | L2 | linked planning workload surface | deterministic workload contract | contract tests | medium |
| notification_center | L1 | L2 | cross-cutting operational notifications | tenant-safe service contract and guard checks | tenant fail-closed tests | high |

## A-026.x Normalization Roadmap
| Action | Theme | Scope | Code? | Tests? | Expected Output |
|---|---|---|---|---|---|
| A-026.2 | planning / dedicated 150 normalization document | criteria, taxonomy, buckets, first batch | no | no | approved baseline normalization plan |
| A-026.3 | L0/L1/L2 foundation-service normalization batch 1 | selected 8 modules, backend contracts only | yes | yes | deterministic service/contract uplift evidence |
| A-026.4 | service/API/test normalization batch 2 | remaining high-priority L2 targets | yes | yes | L2->L3 normalization closure for batch 2 |
| A-026.5 | L3/L4 operational visibility normalization batch | API/visibility where product-relevant | yes | yes | selective L3->L4 readiness improvements |
| A-026.6 | KPI/evidence/Brain-readiness normalization batch | lineage, mapping, audit boundary | yes | yes | selective L4->L5-readiness evidence |
| A-026.7 | E2E/gate continuity for selected candidates | narrow L5 candidates only | yes | yes | gate continuity evidence and regression safety |
| A-026.8 | final A-026 normalization closure report | full reconciliation and anti-inflation review | no | no | A-026 closure with evidence index |

## Killer Flow Resume Criteria
Killer flows can resume only when:
1. A-026.2 normalization plan is accepted.
2. A-026.3 first remediation batch is closed with tests.
3. No unresolved runtime leftovers remain.
4. No guessed capability matrix remains.
5. Red/yellow/unknown gaps are classified with remediation paths.
6. Critical future workflow modules have at least service/API/test readiness.
7. Tracker remains evidence-based.
8. Quality baseline remains protected.

## Anti-Fake and Anti-Inflation Guards
- No maturity levels are changed in A-026.2.
- No row in this document is treated as achieved-state promotion.
- VERIFICATION_PENDING must be used where direct evidence is not yet attached.
- This file does not replace SBS_UB.md authority; it supports execution planning only.
