# SBS_UB 150 Module Normalization

## A-026.2 Scope
- Action: A-026.2
- Date: 2026-05-11
- Mode: planning/docs-only
- Authoritative tracker: SBS_UB.md
- This file role: dedicated working normalization source for baseline 150 modules

## Baseline and Extension Separation (Locked)
This file tracks the reconciled baseline and extension separation state.

- Baseline target modules: 150
- Baseline maturity: L0=0, L1=0, L2=13, L3=42, L4=68, L5=25, L6=2
- Baseline arithmetic: PASS (0+0+13+42+68+25+2=150)
- Extension modules: 25
- Total tracked modules: 175
- Separation policy: baseline and extension remain separate planes

Historical reconciliation details for A-026.3.B3 and A-026.3.B4 remain below.

## A-026.3.B4 — L3/L4 Matrix Reconciliation (COMPLETED)

**Residual Issue from A-026.3.B3**: B3 corrected 4 A-024.1/2 L2→L3 modules but did not account for 4 A-024.3/4/5 L3→L4 modules in matrix row updates.

**Root Cause**: After correcting L2→L3 transitions (4 modules), the matrix still showed L3=28, L4=62. But A-024 evidence proves:
- A-024.3: observability L3→L4
- A-024.4: attendance L3→L4, student_portal L3→L4
- A-024.5: university_core L3→L4

**Corrected Rows** (rows 21, 88, 129, 146):
- Current Level: L3 → L4
- Bucket: C → D
- Verified Level Source: A-024.3 / A-024.4 / A-024.5 evidence
- Capability Status: EVIDENCED_L4_AFTER_A024[3/4/5]
- Target Next Level: L5-readiness (consistent with Bucket D positioning)
- A-026 Action: A-026.6 (KPI/evidence/Brain-readiness mapping)

**Corrected Metrics**:
- Before patch (B3 residual): L0=0, L1=16, L2=21, L3=28, L4=62, L5=21, L6=2 ❌ (L3 overstated by 4)
- After patch: L0=0, L1=16, L2=21, L3=24, L4=66, L5=21, L6=2 ✓ (PASS)
- Arithmetic check: PASS

**Anti-Inflation Review**:
- ✓ No runtime code added
- ✓ No new maturity beyond prior A-024 evidence
- ✓ No API/frontend/KPI/Brain claims injected
- ✓ Matrix alignment only (no product changes)

**Impact**: A-026.4-SPEC unblocked with correct L3/L4 baseline. A-026.3 fully reconciled. A-026.3.B4 complete.

## A-026.4-SPEC — L2→L3 Service Logic Normalization Batch Specification

**Status**: SPEC ONLY

**Purpose**: Select a bounded L2 batch for future A-026.4-RUNTIME and define the deterministic backend service logic that would lift those modules from L2→L3. This section does not change any maturity level, runtime artifact, schema, endpoint, or test state.

### Source-of-Truth Snapshot

- Authoritative tracker: SBS_UB.md
- Reconciled matrix: SBS_UB_150_MODULE_NORMALIZATION.md
- Current baseline metrics: L0=0, L1=16, L2=13, L3=26, L4=72, L5=21, L6=2, total=150, arithmetic_check=PASS
- Extension metrics: extension_total_count=25, total_tracked_modules=175, separation=PASS
- Next action id in tracker: A-026.5-SPEC
- Runtime implementation status: complete

### Historical L2 Module Inventory (pre-A-026.4-RUNTIME)

L2 count before A-026.4-RUNTIME: 21.

| # | Module | Domain | Current Level | Current Gap | Required Work | Required Tests | Source |
|---:|---|---|---:|---|---|---|---|
| 5 | accreditation_compliance | Planned Expansion | L2 | FSM_workflow_missing | deterministic service logic | targeted tests | A-023.0 |
| 11 | ai_cost_governance | Planned Expansion | L2 | service_contract_missing | cost service determinism | contract tests | A-023.0 |
| 14 | ai_plagiarism | Research & Innovation | L2 | FSM_workflow_missing | plagiarism detection FSM | transition tests | A-023.0 |
| 32 | conference_management | Research & Innovation | L2 | FSM_workflow_missing | conference FSM transitions | transition tests | A-023.0 |
| 34 | contracts_legal_repository | Planned Expansion | L2 | service_contract_missing | legal contract service | contract tests | A-023.0 |
| 36 | counseling_case_management | Planned Expansion | L2 | service_contract_missing | case management service | contract tests | A-023.0 |
| 41 | developer_portal | Planned Expansion | L2 | service_contract_missing | developer service contract | contract tests | A-023.0 |
| 59 | federation_management | Planned Expansion | L2 | FSM_workflow_missing | federation FSM logic | transition tests | A-023.0 |
| 62 | health_services | Planned Expansion | L2 | FSM_workflow_missing | health service logic | transition tests | A-023.0 |
| 66 | human_approved_timetable_workflow | Planned Expansion | L2 | deterministic_service_logic_needed | L3 deterministic workflow state logic | L3 service logic / transition tests | A-026.3 runtime + A-026.3.B1 evidence |
| 80 | library_circulation | Planned Expansion | L2 | FSM_workflow_missing | circulation FSM logic | transition tests | A-023.0 |
| 83 | local_user_management | Planned Expansion | L2 | tenant_guard_missing | user management tenant guards | tenant tests | A-023.0 |
| 87 | notification_center | Planned Expansion | L2 | deterministic_service_logic_needed | deterministic notification composition/readiness logic without sending | notification logic / tenant / no-provider-call tests | A-026.3 runtime + A-026.3.B1 evidence |
| 116 | research_grants | Planned Expansion | L2 | FSM_workflow_missing | grants FSM logic | transition tests | A-023.0 |
| 125 | student_ai_tutor | Research & Innovation | L2 | FSM_workflow_missing | tutor FSM logic | transition tests | A-023.0 |
| 138 | timetable_approval_queue | Planned Expansion | L2 | deterministic_service_logic_needed | deterministic queue state/action logic | queue transition / forbidden action tests | A-026.3 runtime + A-026.3.B1 evidence |
| 139 | timetable_change_kpi_dashboard | Planned Expansion | L2 | deterministic_service_logic_needed | deterministic KPI readiness classification only | KPI readiness logic / no-fake-KPI tests | A-026.3 runtime + A-026.3.B1 evidence |
| 140 | timetable_change_proposal | Planned Expansion | L2 | deterministic_service_logic_needed | deterministic proposal evaluation rules | proposal logic / validation / boundary tests | A-026.3 runtime + A-026.3.B1 evidence |
| 141 | timetable_change_simulation | Planned Expansion | L2 | deterministic_service_logic_needed | deterministic simulation readiness classification | simulation logic / no-mutation / boundary tests | A-026.3 runtime + A-026.3.B1 evidence |
| 142 | timetable_recommendation_bridge | Planned Expansion | L2 | deterministic_service_logic_needed | deterministic recommendation envelope rules | bridge logic / determinism / no-AI-provider tests | A-026.3 runtime + A-026.3.B1 evidence |
| 150 | workload_management | Planned Expansion | L2 | deterministic_service_logic_needed | deterministic workload planning classification | workload logic / no-payroll-mutation tests | A-026.3 runtime + A-026.3.B1 evidence |

**Count check**: PASS (21 L2 rows)

### Selection Criteria

- Prefer coherent dependency chains over single isolated modules.
- Prefer deterministic backend logic that can be specified without schema, endpoint, or frontend work.
- Prefer low blast radius and strong testability.
- Prefer tenant-safe behavior with fail-closed handling.
- Avoid API, frontend, schema, event registry, Brain, or KPI overreach in this spec stage.

### L2 Suitability Scoring

Priority score formula: `Domain Leverage + Service Clarity + Testability + (6 - Tenant Risk) + (6 - Blast Radius)`, max 25.

| Module | Domain Leverage | Service Clarity | Tenant Risk | Testability | Blast Radius | Priority Score | Recommended |
|---|---:|---:|---:|---:|---:|---:|---|
| accreditation_compliance | 3 | 3 | 2 | 4 | 2 | 18 | DEFER_A0265 |
| ai_cost_governance | 4 | 3 | 2 | 4 | 2 | 19 | DEFER_A0265 |
| ai_plagiarism | 4 | 3 | 4 | 3 | 3 | 16 | DEFER_AFTER_VERIFICATION |
| conference_management | 3 | 3 | 3 | 3 | 2 | 16 | DEFER_A0265 |
| contracts_legal_repository | 3 | 4 | 2 | 4 | 3 | 17 | DEFER_A0265 |
| counseling_case_management | 3 | 3 | 3 | 4 | 3 | 15 | DEFER_AFTER_VERIFICATION |
| developer_portal | 3 | 4 | 2 | 4 | 3 | 17 | DEFER_A0265 |
| federation_management | 4 | 3 | 3 | 4 | 3 | 17 | DEFER_AFTER_VERIFICATION |
| health_services | 4 | 3 | 3 | 4 | 3 | 17 | DEFER_AFTER_VERIFICATION |
| human_approved_timetable_workflow | 5 | 5 | 2 | 5 | 2 | 23 | SELECT_A0264 |
| library_circulation | 4 | 4 | 3 | 4 | 2 | 19 | DEFER_A0265 |
| local_user_management | 4 | 3 | 4 | 4 | 4 | 14 | DO_NOT_TOUCH_NOW |
| notification_center | 5 | 4 | 2 | 4 | 3 | 21 | SELECT_A0264 |
| research_grants | 4 | 4 | 3 | 4 | 2 | 19 | DEFER_A0265 |
| student_ai_tutor | 4 | 3 | 3 | 4 | 3 | 17 | DEFER_AFTER_VERIFICATION |
| timetable_approval_queue | 5 | 4 | 3 | 4 | 2 | 20 | SELECT_A0264 |
| timetable_change_kpi_dashboard | 4 | 4 | 3 | 4 | 2 | 19 | SELECT_A0264 |
| timetable_change_proposal | 5 | 5 | 2 | 5 | 2 | 23 | SELECT_A0264 |
| timetable_change_simulation | 5 | 4 | 2 | 5 | 2 | 22 | SELECT_A0264 |
| timetable_recommendation_bridge | 5 | 4 | 2 | 4 | 2 | 21 | SELECT_A0264 |
| workload_management | 4 | 4 | 3 | 4 | 2 | 19 | SELECT_A0264 |

### Selected A-026.4 Batch

Selected batch size: 8.

| Selected Module | Current Level | Target Level | Why Selected | Expected L3 Logic | Required Tests | Risk |
|---|---:|---:|---|---|---|---|
| human_approved_timetable_workflow | L2 | L3 | Highest leverage workflow root; anchors the rest of the timetable chain | deterministic workflow state transitions and approval boundary logic | import, tenant negative, transition, forbidden action tests | medium |
| timetable_change_proposal | L2 | L3 | Core change request domain; clean rule surface | deterministic proposal evaluation and status logic | contract, validation, boundary tests | medium |
| timetable_change_simulation | L2 | L3 | Bounded simulation logic; no mutation needed | deterministic simulation readiness and conflict classification | negative, no-mutation, boundary tests | medium |
| timetable_recommendation_bridge | L2 | L3 | Bridge layer between recommendation and workflow decisions | deterministic envelope and mapping rules | determinism, no-provider-call tests | medium |
| timetable_approval_queue | L2 | L3 | Human review queue for bounded actions | deterministic queue state and allowed-action rules | transition, forbidden-action tests | medium |
| timetable_change_kpi_dashboard | L2 | L3 | Supports review-ready classification without KPI claims | deterministic readiness classification only | no-fake-KPI tests | medium |
| workload_management | L2 | L3 | Planning logic adjacent to timetable decisions | deterministic workload planning classification | contract, no-mutation tests | medium |
| notification_center | L2 | L3 | Cross-cutting tenant-safe notification preview logic | deterministic notification composition without provider calls | tenant, no-provider-call tests | high |

### A-026.4 L3 Implementation Standard

1. Deterministic backend business logic
- service functions do more than readiness contracts
- status, risk, classification, and action recommendations must be deterministic
- no fake data generation

2. Tenant fail-closed behavior
- invalid tenant rejected
- all outputs tenant-scoped
- no cross-tenant aggregation

3. Domain-specific rules
- module-specific classification
- allowed and forbidden actions
- next-state or readiness rules
- human review boundary where applicable
- risk, severity, and priority logic where applicable

4. Tests
- import tests
- tenant negative tests
- deterministic output tests
- status/risk/classification tests
- boundary tests
- anti-inflation tests

5. Anti-inflation
- no API claim
- no frontend claim
- no KPI lineage claim
- no Brain claim
- no L4/L5/L6 claim
- no autonomous critical action

### Module-by-Module Deep Specification

#### Module: human_approved_timetable_workflow

Current state: L2; source A-026.3 runtime + A-026.3.B1 evidence; primary gap is deterministic workflow state logic.

Intended L3 scope: compute approval-state transitions deterministically, enforce human-review boundaries, and fail closed on invalid tenant input. This module will not expose APIs, mutate data, or schedule autonomous actions.

Expected runtime files:
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/human_approved_timetable_workflow/service.py | augment | L3 workflow state logic |
| backend/tests/test_a0264_l2_to_l3_service_logic_normalization.py | add | shared deterministic tests |

L3 service functions:
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| validate_tenant_id | fail-closed tenant guard | tenant_id | normalized tenant_id or error | yes | yes |
| evaluate_workflow_state | classify workflow state | proposal state, actor state | workflow classification | yes | yes |
| determine_human_review_boundary | identify approval boundary | workflow payload | boundary decision | yes | yes |
| build_workflow_summary | summarize deterministic status | tenant-scoped payload | summary object | yes | yes |

Domain logic: statuses should include draft, pending_review, approved, rejected, and cancelled; allowed actions should be submit, review, approve, reject, and cancel; forbidden actions should include auto-approve, cross-tenant routing, and silent state mutation.

Tenant safety: reject missing, non-integer, or non-positive tenant ids; include tenant id in every returned payload; never aggregate across tenants.

Required tests: import validation, tenant fail-closed rejection, deterministic state transitions, forbidden action protection, and anti-inflation flags.

Anti-inflation boundary: no API endpoint, no frontend page, no DB mutation, no KPI values, no Brain signal, no event emission, no autonomous execution, L3 only.

#### Module: timetable_change_proposal

Current state: L2; source A-026.3 runtime + A-026.3.B1 evidence; primary gap is deterministic proposal evaluation rules.

Intended L3 scope: classify proposal validity, status, and next action deterministically. This module will not publish events or expose a proposal API.

Expected runtime files:
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/timetable_change_proposal/service.py | augment | L3 proposal evaluation logic |
| backend/tests/test_a0264_l2_to_l3_service_logic_normalization.py | add | shared deterministic tests |

L3 service functions:
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| validate_tenant_id | fail-closed tenant guard | tenant_id | normalized tenant_id or error | yes | yes |
| evaluate_proposal | classify proposal outcome | proposal payload | proposal verdict | yes | yes |
| classify_proposal_status | assign status bucket | proposal state | status object | yes | yes |
| list_forbidden_actions | block invalid operations | proposal context | forbidden action list | yes | yes |

Domain logic: statuses should include submitted, under_review, ready, rejected, and applied; allowed actions should include submit, review, revise, approve, and apply; forbidden actions should include auto-apply, cross-tenant reuse, and hidden mutation.

Tenant safety: keep all outputs tenant-scoped and reject malformed tenant ids before any classification.

Required tests: import validation, proposal-status classification, forbidden action protection, tenant negative tests, and anti-inflation flags.

Anti-inflation boundary: no API endpoint, no frontend page, no DB mutation, no KPI values, no Brain signal, no event emission, no autonomous execution, L3 only.

#### Module: timetable_change_simulation

Current state: L2; source A-026.3 runtime + A-026.3.B1 evidence; primary gap is deterministic simulation readiness classification.

Intended L3 scope: evaluate simulation readiness and conflict outcomes without mutating timetable data. This module will not simulate by calling external providers or writing state.

Expected runtime files:
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/timetable_change_simulation/service.py | augment | L3 simulation readiness logic |
| backend/tests/test_a0264_l2_to_l3_service_logic_normalization.py | add | shared deterministic tests |

L3 service functions:
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| validate_tenant_id | fail-closed tenant guard | tenant_id | normalized tenant_id or error | yes | yes |
| classify_simulation_readiness | readiness classification | simulation input | readiness verdict | yes | yes |
| detect_simulation_conflicts | identify deterministic conflicts | timetable snapshot | conflict summary | yes | yes |
| build_simulation_summary | package output | tenant-scoped payload | summary object | yes | yes |

Domain logic: statuses should include pending, simulated, conflict_detected, ready, and failed; allowed actions should include preview, classify, and review; forbidden actions should include any mutation or optimistic commit.

Tenant safety: tenant id required, outputs tenant-scoped, and cross-tenant conflict blending prohibited.

Required tests: readiness classification, no-mutation behavior, tenant fail-closed rejection, conflict boundary tests, and anti-inflation flags.

Anti-inflation boundary: no API endpoint, no frontend page, no DB mutation, no KPI values, no Brain signal, no event emission, no autonomous execution, L3 only.

#### Module: timetable_recommendation_bridge

Current state: L2; source A-026.3 runtime + A-026.3.B1 evidence; primary gap is deterministic recommendation envelope rules.

Intended L3 scope: transform recommendations into deterministic workflow envelopes and classify them for downstream review. This module will not call AI providers or emit autonomous decisions.

Expected runtime files:
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/timetable_recommendation_bridge/service.py | augment | L3 bridge rules |
| backend/tests/test_a0264_l2_to_l3_service_logic_normalization.py | add | shared deterministic tests |

L3 service functions:
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| validate_tenant_id | fail-closed tenant guard | tenant_id | normalized tenant_id or error | yes | yes |
| build_recommendation_envelope | map recommendation into envelope | recommendation payload | deterministic envelope | yes | yes |
| classify_bridge_readiness | readiness classification | bridge context | readiness verdict | yes | yes |
| list_forbidden_actions | block unsupported actions | bridge context | forbidden action list | yes | yes |

Domain logic: allowed actions should include map, preview, and review; forbidden actions should include direct execution, AI-provider calls, and cross-tenant reuse.

Tenant safety: every envelope must carry tenant scope and reject invalid tenants before any mapping.

Required tests: deterministic mapping, no-provider-call behavior, tenant negative tests, and anti-inflation flags.

Anti-inflation boundary: no API endpoint, no frontend page, no DB mutation, no KPI values, no Brain signal, no event emission, no autonomous execution, L3 only.

#### Module: timetable_approval_queue

Current state: L2; source A-026.3 runtime + A-026.3.B1 evidence; primary gap is deterministic queue state/action logic.

Intended L3 scope: classify queue states and allowed actions for review workflows. This module will not mutate production queue state or expose queue APIs.

Expected runtime files:
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/timetable_approval_queue/service.py | augment | L3 queue logic |
| backend/tests/test_a0264_l2_to_l3_service_logic_normalization.py | add | shared deterministic tests |

L3 service functions:
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| validate_tenant_id | fail-closed tenant guard | tenant_id | normalized tenant_id or error | yes | yes |
| determine_queue_state | classify queue state | queue payload | queue state object | yes | yes |
| allow_queue_transition | enforce allowed transitions | queue state, action | allow/deny verdict | yes | yes |
| block_forbidden_actions | list forbidden actions | queue context | forbidden action list | yes | yes |

Domain logic: allowed actions should include enqueue, review, approve, reject, and apply; forbidden actions should include silent approve, bypass review, and cross-tenant queue sharing.

Tenant safety: all queue evaluation remains tenant-bound and fail-closed.

Required tests: queue transition tests, forbidden action tests, tenant negative tests, deterministic output tests, and anti-inflation flags.

Anti-inflation boundary: no API endpoint, no frontend page, no DB mutation, no KPI values, no Brain signal, no event emission, no autonomous execution, L3 only.

#### Module: timetable_change_kpi_dashboard

Current state: L2; source A-026.3 runtime + A-026.3.B1 evidence; primary gap is deterministic KPI readiness classification only.

Intended L3 scope: classify whether backend evidence is ready for dashboard surfacing without inventing KPI values. This module will not publish frontend dashboards or claim KPI lineage.

Expected runtime files:
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/timetable_change_kpi_dashboard/service.py | augment | L3 readiness classifier |
| backend/tests/test_a0264_l2_to_l3_service_logic_normalization.py | add | shared deterministic tests |

L3 service functions:
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| validate_tenant_id | fail-closed tenant guard | tenant_id | normalized tenant_id or error | yes | yes |
| classify_dashboard_readiness | readiness classification | evidence context | readiness verdict | yes | yes |
| validate_no_fake_kpi | block invented KPI data | dashboard payload | allow/deny verdict | yes | yes |
| build_evidence_summary | summarise evidence state | tenant-scoped evidence | summary object | yes | yes |

Domain logic: outputs should distinguish ready, blocked, and incomplete states; forbidden actions include fabricating KPI values, implying frontend presence, or cross-tenant aggregation.

Tenant safety: all readiness decisions remain tenant-scoped and fail-closed.

Required tests: no-fake-KPI tests, evidence classification, tenant negative tests, and anti-inflation flags.

Anti-inflation boundary: no API endpoint, no frontend page, no DB mutation, no KPI values, no Brain signal, no event emission, no autonomous execution, L3 only.

#### Module: workload_management

Current state: L2; source A-026.3 runtime + A-026.3.B1 evidence; primary gap is deterministic workload planning classification.

Intended L3 scope: classify workload planning states and constraints deterministically. This module will not mutate payroll, scheduling, or assignment state.

Expected runtime files:
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/workload_management/service.py | augment | L3 workload planning logic |
| backend/tests/test_a0264_l2_to_l3_service_logic_normalization.py | add | shared deterministic tests |

L3 service functions:
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| validate_tenant_id | fail-closed tenant guard | tenant_id | normalized tenant_id or error | yes | yes |
| classify_workload_plan | classify planning state | workload payload | plan verdict | yes | yes |
| determine_constraint_set | compute planning constraints | workload context | constraint summary | yes | yes |
| block_mutating_actions | block unsafe actions | workload context | forbidden action list | yes | yes |

Domain logic: allowed actions should include assess, classify, and review; forbidden actions should include payroll mutation, auto-assignment, and cross-tenant mixing.

Tenant safety: tenant scoping required for all outputs.

Required tests: contract tests, no-mutation tests, tenant negative tests, and anti-inflation flags.

Anti-inflation boundary: no API endpoint, no frontend page, no DB mutation, no KPI values, no Brain signal, no event emission, no autonomous execution, L3 only.

#### Module: notification_center

Current state: L2; source A-026.3 runtime + A-026.3.B1 evidence; primary gap is deterministic notification composition/readiness logic without sending.

Intended L3 scope: compose notification previews and readiness states deterministically while keeping provider calls out of scope. This module will not send notifications or call external providers.

Expected runtime files:
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/notification_center/service.py | augment | L3 notification preview logic |
| backend/tests/test_a0264_l2_to_l3_service_logic_normalization.py | add | shared deterministic tests |

L3 service functions:
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| validate_tenant_id | fail-closed tenant guard | tenant_id | normalized tenant_id or error | yes | yes |
| compose_notification_preview | build deterministic preview | notification payload | preview object | yes | yes |
| classify_dispatch_readiness | classify send readiness | preview context | readiness verdict | yes | yes |
| block_provider_calls | prevent delivery side effects | dispatch context | forbidden action list | yes | yes |

Domain logic: allowed actions should include preview, classify, and review; forbidden actions should include send, deliver, cross-tenant reuse, and any direct provider invocation.

Tenant safety: mandatory tenant scope on all preview objects; fail closed on invalid tenant ids; no cross-tenant fanout.

Required tests: tenant negative tests, no-provider-call tests, deterministic preview tests, and anti-inflation flags.

Anti-inflation boundary: no API endpoint, no frontend page, no DB mutation, no KPI values, no Brain signal, no event emission, no autonomous execution, L3 only.

### Expected Runtime Files

| File | Expected Action | Reason |
|---|---|---|
| backend/app/modules/human_approved_timetable_workflow/service.py | augment | add deterministic L3 workflow logic |
| backend/app/modules/timetable_change_proposal/service.py | augment | add deterministic L3 proposal logic |
| backend/app/modules/timetable_change_simulation/service.py | augment | add deterministic L3 simulation logic |
| backend/app/modules/timetable_recommendation_bridge/service.py | augment | add deterministic L3 bridge logic |
| backend/app/modules/timetable_approval_queue/service.py | augment | upgrade queue logic from L2 contract to L3 rules |
| backend/app/modules/timetable_change_kpi_dashboard/service.py | augment | upgrade readiness classifier without KPI inflation |
| backend/app/modules/workload_management/service.py | augment | add deterministic workload planning logic |
| backend/app/modules/notification_center/service.py | augment | add deterministic tenant-safe preview logic |
| backend/tests/test_a0264_l2_to_l3_service_logic_normalization.py | add | shared targeted test file for selected batch |
| SBS_UB.md | update | control block and execution staging |
| SBS_UB_150_MODULE_NORMALIZATION.md | update | add this A-026.4-SPEC section |
| A-026.4-SPEC-L2_TO_L3_SERVICE_LOGIC_BATCH_SPECIFICATION_REPORT.md | add | audit-ready spec report |

### A-026.4 Targeted Test Plan

Preferred test file: backend/tests/test_a0264_l2_to_l3_service_logic_normalization.py

Targeted test count: 32 tests.

Test groups:
1. import validation for all 8 selected modules
2. tenant fail-closed validation for all 8 selected modules
3. deterministic domain logic for all 8 selected modules
4. status, risk, and classification outputs
5. forbidden action protection
6. anti-inflation flags and no-provider-call / no-mutation checks
7. no DB, external API, frontend, or autonomous execution behavior

### Expected Maturity Movement

No maturity movement in this spec phase.

If A-026.4-RUNTIME succeeds, selected modules move L2→L3 only.

Before A-026.4-RUNTIME:
- L0=0
- L1=16
- L2=21
- L3=24
- L4=66
- L5=21
- L6=2
- total=150
- maturity_arithmetic_check=PASS

If selected batch size is N:
- L0=0
- L1=16
- L2=21-N
- L3=24+N
- L4=66
- L5=21
- L6=2
- total=150
- maturity_arithmetic_check=PASS

If N=8:
- L0=0
- L1=16
- L2=13
- L3=32
- L4=66
- L5=21
- L6=2
- total=150
- maturity_arithmetic_check=PASS

### Anti-Inflation Boundaries

- no API endpoint
- no frontend page
- no DB mutation
- no KPI values
- no Brain signal
- no event emission unless later explicitly scoped
- no autonomous execution
- L3 only

### Definition of Done for Future A-026.4-RUNTIME

- selected batch remains exactly 8 modules unless re-approved
- service logic is deterministic and tenant-safe
- shared targeted tests pass
- no API, frontend, schema, or Brain claims are introduced
- SBS_UB.md metrics remain consistent with the runtime result
- the normalized matrix is updated only after implementation and validation

## A-026.4-RUNTIME — L2→L3 Service Logic Normalization

- Selected 8 modules moved from L2/B to L3/C.
- Deterministic backend service logic was added without API, frontend, KPI, Brain, or autonomous execution claims.
- Local compile and behavior assertions passed in this environment.
- A-026.5 will be needed for the L3→L4 operational visibility/API planning step.
- Extension 25 remains unchanged and separate.

## A-026.5-SPEC — L3→L4 Operational Visibility / API Surface Batch Specification

**Status**: SPEC ONLY

**Purpose**: select a bounded current-L3 batch for future A-026.5-RUNTIME and define what honest L4 operational visibility means for each selected module. This section does not create runtime code, routers, schemas, frontend pages, tests, or maturity movement.

### Source-of-Truth Snapshot

- Authoritative tracker: SBS_UB.md
- Reconciled matrix: SBS_UB_150_MODULE_NORMALIZATION.md
- Current baseline metrics: L0=0, L1=16, L2=13, L3=26, L4=72, L5=21, L6=2, total=150, arithmetic_check=PASS
- Extension metrics: extension_total_count=25, total_tracked_modules=175, separation=PASS
- Last completed action in tracker: A-026.4.B2.R1
- Next action in tracker before this spec: A-026.5-SPEC
- Runtime implementation status for A-026.5: not started

### L3 Extraction Summary

Current L3 modules were extracted from the full baseline matrix after A-026.4.B2.R1.

- expected L3 count: 32
- found L3 count: 32
- status: PASS

| # | Module | Domain | Current Level | Current Gap | Required Work | Required Tests | Source |
|---:|---|---|---:|---|---|---|---|
| 9 | ai_admissions_scoring | Research & Innovation | L3 | API_missing | expose scoring API readiness | route tests | A-023.0 |
| 10 | ai_copilot_ops | Planned Expansion | L3 | operational_visibility_or_API_depth_needed | operational visibility / API readiness specification | route or visibility contract tests | A-024.2 |
| 13 | ai_guardrails | AI/Knowledge/Reasoning | L3 | API_missing | guardrails control API | route tests | A-023.0 |
| 15 | ai_routing_control | Planned Expansion | L3 | operational_visibility_or_API_depth_needed | operational visibility / routing control surface readiness | route or visibility contract tests | A-024.1 |
| 17 | alumni_donation_portal | Administration & Governance | L3 | API_missing | donation API visibility | route tests | A-023.0 |
| 26 | blockchain_diploma | Administration & Governance | L3 | API_missing | diploma verification API | route tests | A-023.0 |
| 33 | contracts_hr | Finance & Billing | L3 | API_missing | HR contract API | route tests | A-023.0 |
| 35 | counseling | Student & Campus Life | L3 | API_missing | counseling API visibility | route tests | A-023.0 |
| 43 | digital_documents | Administration & Governance | L3 | API_missing | document API visibility | route tests | A-023.0 |
| 66 | human_approved_timetable_workflow | Planned Expansion | L3 | operational_visibility_or_API_depth_needed | operational visibility/API readiness specification | route/visibility contract tests | A-026.4-RUNTIME |
| 70 | internship | Student & Campus Life | L3 | API_missing | internship API visibility | route tests | A-023.0 |
| 79 | library | Student & Campus Life | L3 | API_missing | library API visibility | route tests | A-023.0 |
| 82 | lms_content | Administration & Governance | L3 | API_missing | content API visibility | route tests | A-023.0 |
| 84 | mobile_app | Student & Campus Life | L3 | frontend_missing | mobile app frontend visibility | frontend tests | A-023.0 |
| 87 | notification_center | Planned Expansion | L3 | operational_visibility_or_API_depth_needed | operational visibility/API readiness specification | route/visibility contract tests | A-026.4-RUNTIME |
| 93 | parent_portal | Student & Campus Life | L3 | API_missing | parent portal API | route tests | A-023.0 |
| 94 | parking | Student & Campus Life | L3 | API_missing | parking API visibility | route tests | A-023.0 |
| 97 | patents | Research & Innovation | L3 | API_missing | patent API visibility | route tests | A-023.0 |
| 102 | platform_health | Planned Expansion | L3 | operational_visibility_or_API_depth_needed | operational health visibility readiness | visibility contract tests | A-024.1 |
| 103 | platform_shared | Integrations & Platform | L3 | API_missing | shared services API | route tests | A-023.0 |
| 105 | procurement_approval_workflow | Planned Expansion | L3 | operational_visibility_or_API_depth_needed | operational workflow visibility/API readiness | route or workflow visibility tests | A-024.2 |
| 110 | publications | Research & Innovation | L3 | API_missing | publications API visibility | route tests | A-023.0 |
| 124 | sso_saml | Identity/Access/Security | L3 | API_missing | SAML API visibility | route tests | A-023.0 |
| 126 | student_feedback | Student & Campus Life | L3 | API_missing | feedback API visibility | route tests | A-023.0 |
| 127 | student_id_card | Student & Campus Life | L3 | API_missing | ID card API visibility | route tests | A-023.0 |
| 138 | timetable_approval_queue | Planned Expansion | L3 | operational_visibility_or_API_depth_needed | operational visibility/API readiness specification | route/visibility contract tests | A-026.4-RUNTIME |
| 139 | timetable_change_kpi_dashboard | Planned Expansion | L3 | operational_visibility_or_API_depth_needed | operational visibility/API readiness specification | route/visibility contract tests | A-026.4-RUNTIME |
| 140 | timetable_change_proposal | Planned Expansion | L3 | operational_visibility_or_API_depth_needed | operational visibility/API readiness specification | route/visibility contract tests | A-026.4-RUNTIME |
| 141 | timetable_change_simulation | Planned Expansion | L3 | operational_visibility_or_API_depth_needed | operational visibility/API readiness specification | route/visibility contract tests | A-026.4-RUNTIME |
| 142 | timetable_recommendation_bridge | Planned Expansion | L3 | operational_visibility_or_API_depth_needed | operational visibility/API readiness specification | route/visibility contract tests | A-026.4-RUNTIME |
| 145 | two_factor_auth | Identity/Access/Security | L3 | API_missing | 2FA API visibility | route tests | A-023.0 |
| 150 | workload_management | Planned Expansion | L3 | operational_visibility_or_API_depth_needed | operational visibility/API readiness specification | route/visibility contract tests | A-026.4-RUNTIME |

### L4 Readiness Classification

Priority score formula for A-026.5-SPEC: `Visibility Value + Route Feasibility + Security Clarity + Testability + (6 - Frontend Need) + (6 - Blast Radius)`, max 30. Higher scores favor bounded operational visibility with strong tenant/security clarity and low UI or blast-radius risk.

| Module | Visibility Value | Route Feasibility | Security Clarity | Frontend Need | Testability | Blast Radius | Priority Score | Recommendation |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| ai_admissions_scoring | 3 | 4 | 3 | 2 | 4 | 3 | 21 | DEFER_AFTER_VERIFICATION |
| ai_copilot_ops | 3 | 3 | 2 | 1 | 3 | 4 | 18 | DEFER_AFTER_VERIFICATION |
| ai_guardrails | 4 | 3 | 2 | 1 | 4 | 4 | 20 | DEFER_A0266 |
| ai_routing_control | 3 | 3 | 2 | 1 | 3 | 4 | 18 | DEFER_AFTER_VERIFICATION |
| alumni_donation_portal | 3 | 3 | 3 | 3 | 4 | 3 | 19 | DEFER_AFTER_VERIFICATION |
| blockchain_diploma | 4 | 4 | 4 | 1 | 4 | 3 | 24 | DEFER_AFTER_VERIFICATION |
| contracts_hr | 3 | 3 | 4 | 2 | 4 | 3 | 21 | DEFER_AFTER_VERIFICATION |
| counseling | 4 | 3 | 3 | 4 | 3 | 4 | 17 | DO_NOT_TOUCH_NOW |
| digital_documents | 4 | 4 | 4 | 2 | 4 | 3 | 23 | DEFER_AFTER_VERIFICATION |
| human_approved_timetable_workflow | 5 | 5 | 5 | 2 | 5 | 2 | 28 | SELECT_A0265 |
| internship | 3 | 3 | 3 | 3 | 4 | 3 | 20 | DEFER_AFTER_VERIFICATION |
| library | 3 | 3 | 3 | 4 | 3 | 3 | 17 | DEFER_AFTER_VERIFICATION |
| lms_content | 3 | 4 | 3 | 3 | 4 | 3 | 20 | DEFER_AFTER_VERIFICATION |
| mobile_app | 4 | 2 | 3 | 5 | 2 | 4 | 14 | DO_NOT_TOUCH_NOW |
| notification_center | 4 | 4 | 4 | 1 | 4 | 3 | 24 | SELECT_A0265 |
| parent_portal | 3 | 3 | 3 | 4 | 3 | 3 | 17 | DEFER_AFTER_VERIFICATION |
| parking | 2 | 3 | 3 | 3 | 4 | 2 | 19 | DEFER_AFTER_VERIFICATION |
| patents | 2 | 3 | 3 | 2 | 4 | 2 | 20 | DEFER_AFTER_VERIFICATION |
| platform_health | 4 | 4 | 4 | 1 | 4 | 2 | 25 | DEFER_AFTER_VERIFICATION |
| platform_shared | 3 | 4 | 4 | 1 | 4 | 2 | 24 | DEFER_AFTER_VERIFICATION |
| procurement_approval_workflow | 4 | 4 | 4 | 2 | 4 | 3 | 23 | DEFER_AFTER_VERIFICATION |
| publications | 2 | 3 | 3 | 2 | 4 | 2 | 20 | DEFER_AFTER_VERIFICATION |
| sso_saml | 4 | 3 | 2 | 1 | 3 | 5 | 18 | DO_NOT_TOUCH_NOW |
| student_feedback | 3 | 4 | 3 | 3 | 4 | 2 | 21 | DEFER_AFTER_VERIFICATION |
| student_id_card | 3 | 4 | 4 | 2 | 4 | 3 | 22 | DEFER_AFTER_VERIFICATION |
| timetable_approval_queue | 5 | 5 | 5 | 2 | 5 | 2 | 28 | SELECT_A0265 |
| timetable_change_kpi_dashboard | 4 | 5 | 5 | 1 | 5 | 2 | 28 | SELECT_A0265 |
| timetable_change_proposal | 5 | 5 | 5 | 2 | 5 | 2 | 28 | SELECT_A0265 |
| timetable_change_simulation | 4 | 3 | 3 | 1 | 4 | 4 | 21 | DEFER_AFTER_VERIFICATION |
| timetable_recommendation_bridge | 4 | 3 | 2 | 1 | 4 | 4 | 20 | DEFER_AFTER_VERIFICATION |
| two_factor_auth | 4 | 3 | 2 | 1 | 3 | 4 | 19 | DO_NOT_TOUCH_NOW |
| workload_management | 4 | 4 | 5 | 2 | 5 | 2 | 26 | SELECT_A0265 |

### Selected A-026.5 Batch

Selected batch size: 6.

| Selected Module | Current Level | Target Level | Why Selected | Expected L4 Surface | Required Tests | Risk |
|---|---:|---:|---|---|---|---|
| human_approved_timetable_workflow | L3 | L4 | highest operational leverage in the timetable chain; clear read-only admin visibility need | read-only admin workflow status/summary endpoint | route import, schema, permission, tenant isolation, anti-inflation | medium |
| timetable_change_proposal | L3 | L4 | proposal readiness is product-relevant and naturally exposed as controlled admin summary | read-only proposal readiness/admin summary endpoint | response contract, permission, tenant fail-closed, no-mutation | medium |
| timetable_approval_queue | L3 | L4 | human review queue needs controlled operational visibility before deeper governance work | read-only approval queue summary/list endpoint | route, permission, queue visibility, tenant leakage denial | medium |
| timetable_change_kpi_dashboard | L3 | L4 | backend readiness summary is valuable without claiming KPI lineage or frontend dashboard delivery | read-only KPI readiness/admin visibility endpoint | schema, tenant isolation, anti-fake-KPI, permission | medium |
| workload_management | L3 | L4 | workload planning needs safe admin visibility to support timetable operations | read-only workload readiness/constraint summary endpoint | permission, tenant fail-closed, no mutation, schema | medium |
| notification_center | L3 | L4 | notification preview/readiness has strong operational value while remaining provider-safe | read-only notification readiness/preview endpoint | permission, tenant isolation, no-provider-call, anti-inflation | high |

Deferred from the timetable chain for this first L4 slice:

- timetable_change_simulation: defer until solver/preview boundary is clearer
- timetable_recommendation_bridge: defer until recommendation/API boundary is clearer and provider ambiguity is fully isolated

### A-026.5 L4 Operational Visibility Standard

1. Backend API / route surface
- controlled read-only or admin-safe endpoint only
- no mutating endpoint unless explicitly re-approved in runtime
- endpoint must be tenant-safe and must not expose cross-tenant data

2. Schema / response contract
- Pydantic response schema or schema extension following existing router/schema patterns
- deterministic response shape
- no fake data fields and no implied runtime capability beyond L4

3. Permission / RBAC / ABAC
- `permission_dependency(...)` or repo-equivalent permission gate required
- no unauthenticated access
- role/scope documented per route
- ownership and tenant boundary enforced before response generation

4. Tenant safety
- tenant derived from auth context via `get_current_tenant` or repo-equivalent
- fail-closed if tenant is missing or invalid
- no default tenant fallback
- response confirms tenant isolation by explicit tenant scope or tenant-bound resource shape

5. Tests
- route import / registration validation
- response schema validation
- permission denial / auth guard validation
- tenant fail-closed validation
- no cross-tenant leakage validation where applicable
- anti-inflation validation
- read-only / no-mutation validation

6. Frontend/admin visibility
- frontend is optional, not automatic
- backend/admin route is sufficient for this bounded batch
- no broad dashboard or page rewrite in A-026.5-RUNTIME unless explicitly re-approved

7. Anti-inflation
- no Brain signal claim
- no KPI lineage claim unless explicitly implemented
- no autonomous action
- no solver/AI provider call
- no L5/L6 claim
- no fake operational data

### Module-by-Module Deep Specification

#### Module: human_approved_timetable_workflow

##### Current State
- Current Level: L3
- Target Level: L4
- Source: A-026.4-RUNTIME + A-026.4.B2.R1 evidence
- Existing L3 evidence: deterministic workflow classification, tenant fail-closed behavior, targeted and continuity pytest PASS
- Primary gap: no controlled operational visibility surface

##### Intended L4 Scope
- What this module will expose: read-only admin workflow status/readiness summary for human approval operations
- What this module will NOT expose: approval mutation endpoint, autonomous apply path, cross-tenant queue surface, Brain or KPI claims
- Read-only or mutating: read-only
- Product/admin visibility: admin/internal operational visibility only

##### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/human_approved_timetable_workflow/service.py | augment | shape L4 route-facing summary payload |
| backend/app/modules/human_approved_timetable_workflow/schemas.py | add | response schema for operational summary |
| backend/app/modules/human_approved_timetable_workflow/router.py | add | tenant-safe admin GET surface |

##### API / Route Contract
| Method | Path | Purpose | Auth/Permission | Tenant Handling | Response Schema |
|---|---|---|---|---|---|
| GET | /api/admin/timetable/human-approval/summary | expose workflow approval visibility summary | permission_dependency("timetable.workflow.read") | tenant from auth context, fail-closed | HumanApprovedTimetableWorkflowVisibilitySchema |

##### Response Schema
- tenant_id
- module
- operational_status
- visibility_level = "L4"
- classification
- allowed_actions
- forbidden_actions
- safety_flags
- evidence_notes
- no_autonomous_execution = true

##### Permission / Security Design
- permission required: `timetable.workflow.read`
- RBAC/ABAC requirement: admin or operations viewer scope only
- tenant source: `get_current_tenant`
- fail-closed behavior: 403/404 style denial when tenant or scope invalid
- cross-tenant prevention: service and router both bind returned summary to authenticated tenant only

##### Tests
| Test | Purpose |
|---|---|
| route import / registration | main.py wiring exists and endpoint registers |
| response schema contract | payload shape is deterministic and complete |
| permission denial | unauthorized actor is rejected |
| tenant fail-closed | missing or invalid tenant denies access |
| no cross-tenant leakage | tenant A cannot read tenant B summary |
| anti-inflation | no autonomous/API inflation beyond defined L4 summary |

##### Frontend Decision
- frontend required: NO
- reason: bounded admin-safe read-only API is sufficient to qualify operational visibility in this batch

##### Anti-Inflation Boundary
- no Brain signal
- no KPI lineage
- no autonomous execution
- no solver or AI-provider call
- no L5/L6 claim
- no fake data

#### Module: timetable_change_proposal

##### Current State
- Current Level: L3
- Target Level: L4
- Source: A-026.4-RUNTIME + A-026.4.B2.R1 evidence
- Existing L3 evidence: deterministic proposal evaluation and validation, tenant-safe outputs, 41/82 pytest PASS coverage
- Primary gap: no controlled admin/API surface for proposal readiness

##### Intended L4 Scope
- What this module will expose: read-only proposal readiness/status summary endpoint for authorized admins
- What this module will NOT expose: proposal mutation/apply endpoint, automatic submission, cross-tenant review access
- Read-only or mutating: read-only
- Product/admin visibility: admin/internal operational visibility

##### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/timetable_change_proposal/service.py | augment | L4 summary serialization for route |
| backend/app/modules/timetable_change_proposal/schemas.py | add | response schema for proposal visibility |
| backend/app/modules/timetable_change_proposal/router.py | add | read-only admin proposal readiness endpoint |

##### API / Route Contract
| Method | Path | Purpose | Auth/Permission | Tenant Handling | Response Schema |
|---|---|---|---|---|---|
| GET | /api/admin/timetable/change-proposals/readiness | expose proposal status/readiness summary | permission_dependency("timetable.change_proposal.read") | tenant from auth context, no fallback | TimetableChangeProposalVisibilitySchema |

##### Response Schema
- tenant_id
- module
- operational_status
- visibility_level = "L4"
- classification
- allowed_actions
- forbidden_actions
- safety_flags
- evidence_notes
- no_autonomous_execution = true

##### Permission / Security Design
- permission required: `timetable.change_proposal.read`
- RBAC/ABAC requirement: timetable-ops/admin reviewer role
- tenant source: `get_current_tenant`
- fail-closed behavior: deny if tenant absent, permission absent, or resource not tenant-owned
- cross-tenant prevention: no proposal summary may be returned across tenant boundary

##### Tests
| Test | Purpose |
|---|---|
| route registration | router imported and included in main app |
| schema test | response shape and status fields are deterministic |
| permission denial | unprivileged actor receives denial |
| tenant fail-closed | invalid tenant is blocked |
| no cross-tenant leakage | foreign tenant resources not visible |
| read-only behavior | GET endpoint does not mutate proposal state |

##### Frontend Decision
- frontend required: NO
- reason: controlled backend/admin API is sufficient for first L4 slice; UI work would widen blast radius

##### Anti-Inflation Boundary
- no Brain signal
- no KPI lineage
- no autonomous execution
- no solver or provider call
- no L5/L6 claim
- no fake data

#### Module: timetable_approval_queue

##### Current State
- Current Level: L3
- Target Level: L4
- Source: A-026.4-RUNTIME + A-026.4.B2.R1 evidence
- Existing L3 evidence: deterministic queue-item evaluation and forbidden-action logic
- Primary gap: no authorized operational visibility surface for queue state and manual decision readiness

##### Intended L4 Scope
- What this module will expose: read-only queue visibility endpoint for manual-review operations
- What this module will NOT expose: queue mutation/apply endpoint, hidden reviewer override, autonomous approval path
- Read-only or mutating: read-only
- Product/admin visibility: admin/internal review visibility

##### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/timetable_approval_queue/service.py | augment | route-ready queue visibility summary |
| backend/app/modules/timetable_approval_queue/schemas.py | add | queue visibility schema |
| backend/app/modules/timetable_approval_queue/router.py | add | admin-safe GET queue summary surface |

##### API / Route Contract
| Method | Path | Purpose | Auth/Permission | Tenant Handling | Response Schema |
|---|---|---|---|---|---|
| GET | /api/admin/timetable/approval-queue/summary | expose queue state and manual decision visibility | permission_dependency("timetable.approval_queue.read") | tenant from auth context, fail-closed | TimetableApprovalQueueVisibilitySchema |

##### Response Schema
- tenant_id
- module
- operational_status
- visibility_level = "L4"
- classification
- allowed_actions
- forbidden_actions
- safety_flags
- evidence_notes
- no_autonomous_execution = true

##### Permission / Security Design
- permission required: `timetable.approval_queue.read`
- RBAC/ABAC requirement: review queue viewer/approver role separation documented in runtime
- tenant source: `get_current_tenant`
- fail-closed behavior: deny when tenant/scope missing
- cross-tenant prevention: queue summaries filtered strictly by tenant context

##### Tests
| Test | Purpose |
|---|---|
| route import / registration | endpoint is wired into app |
| response schema test | queue summary shape matches schema |
| permission denial | missing scope denied |
| tenant fail-closed | invalid tenant denied |
| no cross-tenant leakage | queue data cannot escape tenant boundary |
| anti-inflation | response does not imply autonomous approval |

##### Frontend Decision
- frontend required: NO
- reason: admin-safe API visibility is enough for this bounded L4 slice

##### Anti-Inflation Boundary
- no Brain signal
- no KPI lineage
- no autonomous execution
- no hidden approval automation
- no L5/L6 claim
- no fake data

#### Module: timetable_change_kpi_dashboard

##### Current State
- Current Level: L3
- Target Level: L4
- Source: A-026.4-RUNTIME + A-026.4.B2.R1 evidence
- Existing L3 evidence: deterministic readiness classifier, full anti-inflation suite PASS after B2.R1 remediation
- Primary gap: no controlled operational visibility route for backend KPI readiness

##### Intended L4 Scope
- What this module will expose: read-only KPI readiness/admin visibility endpoint without KPI lineage or frontend dashboard claim
- What this module will NOT expose: dashboard UI, KPI calculation engine, Brain mapping, cross-tenant aggregation
- Read-only or mutating: read-only
- Product/admin visibility: backend/admin visibility only

##### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/timetable_change_kpi_dashboard/service.py | augment | route-facing KPI readiness summary |
| backend/app/modules/timetable_change_kpi_dashboard/schemas.py | add | KPI visibility response schema |
| backend/app/modules/timetable_change_kpi_dashboard/router.py | add | read-only KPI readiness endpoint |

##### API / Route Contract
| Method | Path | Purpose | Auth/Permission | Tenant Handling | Response Schema |
|---|---|---|---|---|---|
| GET | /api/admin/timetable/change-kpi/readiness | expose backend KPI readiness visibility | permission_dependency("timetable.change_kpi.read") | tenant from auth context; no default tenant | TimetableChangeKpiDashboardVisibilitySchema |

##### Response Schema
- tenant_id
- module
- operational_status
- visibility_level = "L4"
- classification
- allowed_actions
- forbidden_actions
- safety_flags
- evidence_notes
- no_autonomous_execution = true

##### Permission / Security Design
- permission required: `timetable.change_kpi.read`
- RBAC/ABAC requirement: admin analytics/timetable visibility scope only
- tenant source: `get_current_tenant`
- fail-closed behavior: deny when tenant absent or invalid
- cross-tenant prevention: no aggregate or foreign-tenant KPI readiness output

##### Tests
| Test | Purpose |
|---|---|
| route import / registration | router exists and is included |
| schema validation | readiness response matches explicit schema |
| permission denial | unprivileged actor cannot access route |
| tenant fail-closed | invalid tenant request denied |
| anti-fake-KPI | no fabricated KPI values or lineage fields appear |
| no cross-tenant leakage | summaries remain tenant-bound |

##### Frontend Decision
- frontend required: NO
- reason: L4 here is backend/admin operational visibility only; dashboard UI would overclaim surface readiness in this batch

##### Anti-Inflation Boundary
- no Brain signal
- no KPI lineage unless explicitly implemented later
- no autonomous execution
- no fake KPI values
- no L5/L6 claim
- no fake data

#### Module: workload_management

##### Current State
- Current Level: L3
- Target Level: L4
- Source: A-026.4-RUNTIME + A-026.4.B2.R1 evidence
- Existing L3 evidence: deterministic workload planning classification and policy review boundaries
- Primary gap: no operational visibility surface for workload readiness and constraints

##### Intended L4 Scope
- What this module will expose: read-only workload readiness/constraint summary for operations users
- What this module will NOT expose: assignment mutation, payroll mutation, auto-assignment, cross-tenant planning merge
- Read-only or mutating: read-only
- Product/admin visibility: admin/internal operational visibility

##### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/workload_management/service.py | augment | expose route-facing workload visibility summary |
| backend/app/modules/workload_management/schemas.py | add | workload visibility response schema |
| backend/app/modules/workload_management/router.py | add | read-only workload readiness endpoint |

##### API / Route Contract
| Method | Path | Purpose | Auth/Permission | Tenant Handling | Response Schema |
|---|---|---|---|---|---|
| GET | /api/admin/workload-management/readiness | expose workload readiness and constraint summary | permission_dependency("workload.read") | tenant from auth context, fail-closed | WorkloadManagementVisibilitySchema |

##### Response Schema
- tenant_id
- module
- operational_status
- visibility_level = "L4"
- classification
- allowed_actions
- forbidden_actions
- safety_flags
- evidence_notes
- no_autonomous_execution = true

##### Permission / Security Design
- permission required: `workload.read`
- RBAC/ABAC requirement: admin/planning viewer scope only
- tenant source: `get_current_tenant`
- fail-closed behavior: deny if tenant or scope missing
- cross-tenant prevention: no merged tenant planning data in responses

##### Tests
| Test | Purpose |
|---|---|
| route registration | router included in app |
| schema contract | response remains deterministic |
| permission denial | non-authorized actor blocked |
| tenant fail-closed | invalid tenant blocked |
| no cross-tenant leakage | tenant boundary enforced |
| no mutation | GET route cannot assign or mutate workload |

##### Frontend Decision
- frontend required: NO
- reason: bounded API visibility is sufficient and avoids UI-driven blast-radius growth

##### Anti-Inflation Boundary
- no Brain signal
- no KPI lineage
- no autonomous execution
- no payroll or assignment mutation
- no L5/L6 claim
- no fake data

#### Module: notification_center

##### Current State
- Current Level: L3
- Target Level: L4
- Source: A-026.4-RUNTIME + A-026.4.B2.R1 evidence
- Existing L3 evidence: tenant-safe notification readiness classification without provider calls
- Primary gap: no operational visibility route for notification readiness/preview state

##### Intended L4 Scope
- What this module will expose: read-only notification readiness/preview endpoint for admin visibility
- What this module will NOT expose: send endpoint, provider integration, cross-tenant broadcast, autonomous dispatch
- Read-only or mutating: read-only
- Product/admin visibility: admin/internal visibility only

##### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/notification_center/service.py | augment | route-facing preview/readiness summary |
| backend/app/modules/notification_center/schemas.py | add | notification visibility response schema |
| backend/app/modules/notification_center/router.py | add | read-only notification readiness endpoint |

##### API / Route Contract
| Method | Path | Purpose | Auth/Permission | Tenant Handling | Response Schema |
|---|---|---|---|---|---|
| GET | /api/admin/notification-center/readiness | expose notification preview/readiness visibility | permission_dependency("notifications.read") | tenant from auth context, fail-closed | NotificationCenterVisibilitySchema |

##### Response Schema
- tenant_id
- module
- operational_status
- visibility_level = "L4"
- classification
- allowed_actions
- forbidden_actions
- safety_flags
- evidence_notes
- no_autonomous_execution = true

##### Permission / Security Design
- permission required: `notifications.read`
- RBAC/ABAC requirement: notification admin/support visibility scope only
- tenant source: `get_current_tenant`
- fail-closed behavior: deny when tenant invalid or missing
- cross-tenant prevention: preview/readiness state never spans tenants

##### Tests
| Test | Purpose |
|---|---|
| route import / registration | router wiring exists |
| response schema | preview/readiness shape is deterministic |
| permission denial | unauthorized actor denied |
| tenant fail-closed | invalid tenant rejected |
| no cross-tenant leakage | tenant A cannot read tenant B preview state |
| no-provider-call | endpoint remains provider-free and read-only |

##### Frontend Decision
- frontend required: NO
- reason: admin-safe backend visibility is sufficient for this L4 slice; UI surfacing is deferred to avoid overclaiming product visibility

##### Anti-Inflation Boundary
- no Brain signal
- no KPI lineage
- no autonomous execution
- no provider call
- no L5/L6 claim
- no fake data

### Frontend Decision

- frontend included in A-026.5 selected batch: NO
- rationale: each selected module can honestly achieve L4 by adding bounded tenant-safe admin/API visibility without a new frontend page; UI work would increase blast radius and require separate build/lint/test commitments without improving the honesty of first-slice L4 claims

### Expected Runtime Files

| File | Expected Action | Reason |
|---|---|---|
| backend/app/modules/human_approved_timetable_workflow/service.py | augment | route-facing L4 summary support |
| backend/app/modules/human_approved_timetable_workflow/schemas.py | add | response schema |
| backend/app/modules/human_approved_timetable_workflow/router.py | add | read-only admin route |
| backend/app/modules/timetable_change_proposal/service.py | augment | route-facing L4 summary support |
| backend/app/modules/timetable_change_proposal/schemas.py | add | response schema |
| backend/app/modules/timetable_change_proposal/router.py | add | read-only admin route |
| backend/app/modules/timetable_approval_queue/service.py | augment | route-facing queue visibility summary |
| backend/app/modules/timetable_approval_queue/schemas.py | add | response schema |
| backend/app/modules/timetable_approval_queue/router.py | add | read-only admin route |
| backend/app/modules/timetable_change_kpi_dashboard/service.py | augment | route-facing KPI readiness summary |
| backend/app/modules/timetable_change_kpi_dashboard/schemas.py | add | response schema |
| backend/app/modules/timetable_change_kpi_dashboard/router.py | add | read-only admin route |
| backend/app/modules/workload_management/service.py | augment | route-facing workload visibility summary |
| backend/app/modules/workload_management/schemas.py | add | response schema |
| backend/app/modules/workload_management/router.py | add | read-only admin route |
| backend/app/modules/notification_center/service.py | augment | route-facing notification readiness summary |
| backend/app/modules/notification_center/schemas.py | add | response schema |
| backend/app/modules/notification_center/router.py | add | read-only admin route |
| backend/app/main.py | update | router import and registration |
| backend/tests/test_a0265_l3_to_l4_operational_visibility.py | add | targeted backend route/security tests |
| SBS_UB.md | update in runtime | execution state reconciliation |
| SBS_UB_150_MODULE_NORMALIZATION.md | update in runtime | selected rows would move L3->L4 after validation |
| A-026.5-RUNTIME-L3_TO_L4_OPERATIONAL_VISIBILITY_REPORT.md | add in runtime | evidence report |

### A-026.5 Targeted Test Plan

Preferred test file: `backend/tests/test_a0265_l3_to_l4_operational_visibility.py`

Backend test groups:
1. route import / app registration validation
2. response schema validation
3. permission denial / auth guard validation
4. tenant fail-closed validation
5. tenant isolation / no cross-tenant leakage
6. operational visibility output validation
7. anti-inflation validation
8. no mutation / read-only behavior

Expected backend test count:
- minimum: 20
- preferred: 30-50 for the selected 6-module batch

Frontend tests required in this batch: no, because frontend is not selected.

### Expected Maturity Movement

No maturity movement occurs in this spec action.

If A-026.5-RUNTIME succeeds, only the selected modules move from L3 to L4.

Before A-026.5-RUNTIME:
- L0=0
- L1=16
- L2=13
- L3=32
- L4=66
- L5=21
- L6=2

After A-026.5-RUNTIME if selected batch size is N:
- L0=0
- L1=16
- L2=13
- L3=32-N
- L4=66+N
- L5=21
- L6=2
- total=150
- maturity_arithmetic_check=PASS

If N=6:
- L0=0
- L1=16
- L2=13
- L3=26
- L4=72
- L5=21
- L6=2
- total=150
- maturity_arithmetic_check=PASS

### Security / SaaS Boundaries

- tenant isolation is mandatory for every planned route
- fail-closed tenant handling is mandatory; no default tenant fallback
- permission dependency or equivalent RBAC/ABAC gate is mandatory
- no cross-tenant leakage is allowed in payload, filtering, or resource lookup
- auditability/evidence notes should be preserved where operational visibility is exposed
- no provider call, no unsafe automation, and no hidden execution path is allowed in this L4 slice

### Anti-Inflation Boundaries

- no runtime code changes in this spec action
- no maturity movement in this spec action
- no fake API or frontend claim
- no Brain readiness or L5/L6 claim
- no autonomous action
- no fake operational data

### Definition of Done for Future A-026.5-RUNTIME

- selected batch remains exactly 6 modules unless re-approved
- each selected module gets a tenant-safe route surface, response schema, and permission dependency
- main app route registration is updated and validated
- targeted backend route/security tests pass
- no runtime mutation endpoint is introduced unless explicitly re-approved
- no frontend is added unless separately justified and tested
- SBS_UB.md metrics remain unchanged until runtime passes
- the normalized matrix is updated only after implementation and validation

## A-026.9-RUNTIME — L2→L3 Deterministic Service Logic Batch 2 Runtime Completion

**Status**: COMPLETE (targeted and continuity Docker pytest passed)

**Purpose**: Implement the selected bounded batch and reconcile the current maturity matrix after lifting eight L2 modules to deterministic L3 service logic.

### Pre-Selection L2 Extraction Summary

- expected L2 count: 21
- found L2 count: 21
- status: PASS
- tracker remains authoritative: SBS_UB.md
- runtime implementation: complete

### A-026.8 Exclusion Confirmation

The following modules were already lifted to L3 in A-026.8 and must not be selected again:

| Module | Expected Level After A-026.8 | Found Level | Status |
|---|---:|---:|---|
| digital_certificates | L3 | L3 | PASS |
| records_hub | L3 | L3 | PASS |
| student_success_analytics | L3 | L3 | PASS |
| publication_registry | L3 | L3 | PASS |
| research_projects | L3 | L3 | PASS |
| lms_assessment_center | L3 | L3 | PASS |
| lab_operations | L3 | L3 | PASS |
| internship_marketplace | L3 | L3 | PASS |

### Selected A-026.9 Batch

Selected batch size: 8.

| Selected Module | Current Level | Target Level | Why Selected | Expected L3 Logic | Required Tests | Risk |
|---|---:|---:|---|---|---|---|
| parking_permit_ops | L3 | L3 | clear deterministic permit readiness and eligibility rules | permit readiness, status, next_step, allowed/forbidden actions | tenant, determinism, boundary, anti-inflation | medium |
| parking_enforcement | L3 | L3 | operational workflow with explicit rule boundaries | enforcement review, risk, escalation, next_step | tenant, classification, forbidden-action tests | medium |
| event_registration_portal | L3 | L3 | high reuse value for event intake and eligibility review | registration readiness and status classification | tenant, readiness, forbidden-action, anti-inflation | medium |
| parent_engagement | L3 | L3 | strong engagement governance and deterministic readiness logic | outreach readiness and intervention classification | tenant, determinism, evidence, boundary tests | medium |
| alumni_relations_ops | L3 | L3 | operationally useful relationship workflow with clean rule set | alumni outreach readiness and risk classification | tenant, deterministic output, boundary tests | medium |
| donations_fundraising | L3 | L3 | measurable readiness/risk classification with clear evidence gates | fundraising readiness and review classification | tenant, forbidden-action, no-fake-data tests | medium |
| exam_integrity_analytics | L3 | L3 | high governance value with explicit integrity boundaries | integrity review readiness and escalation classification | tenant, determinism, anti-inflation, boundary | high |
| mobile_push_gateway | L3 | L3 | useful if kept provider-free with strict preview/readiness boundary | notification preview/readiness without sending | tenant, no-provider-call, determinism, boundary | high |

### Runtime Reconciliation

- targeted runtime validation: PASS (97 passed, 1 warning)
- continuity validation: PASS (579 passed, 1 warning)
- current L2 modules lifted to L3 in this batch: parking_permit_ops, parking_enforcement, event_registration_portal, parent_engagement, alumni_relations_ops, donations_fundraising, exam_integrity_analytics, mobile_push_gateway
- post-runtime counts: L2=13, L3=42, L4=68, L5=25, L6=2
- arithmetic check: PASS (total=150)

### A-026.9 L3 Deterministic Service Logic Standard

1. Deterministic business logic
- service function does more than return foundation contract
- module-specific classification/status/risk/readiness logic
- deterministic next recommended step

2. Tenant fail-closed behavior
- tenant_id=None rejected
- tenant_id=0 rejected
- tenant_id<0 rejected
- valid tenant_id accepted
- output tenant-scoped

3. Domain-specific rules
- module-specific statuses
- allowed actions
- forbidden actions
- required evidence
- readiness/risk classification

4. Tests
- import tests
- tenant fail-closed tests
- deterministic output tests
- classification/status/risk tests
- boundary tests
- anti-inflation tests

5. Anti-inflation
- no API claim
- no frontend claim
- no KPI claim
- no Brain claim
- no autonomous execution
- no L4/L5/L6 claim
- no external provider call

### Module-by-Module Deep Specification

#### Module: parking_permit_ops
- Current Level: L3
- Target Level: L3
- Source: A-026.9-RUNTIME
- Existing L2 evidence: deterministic foundation contract and tenant guard
- Primary gap: resolved
- Will do: evaluate permit readiness, eligibility state, and review routing deterministically
- Will NOT do: issue permits automatically, mutate records, expose APIs, or call external services
- Expected runtime file: backend/app/modules/parking_permit_ops/service.py
- L3 function: evaluate_parking_permit_ops_readiness(tenant_id, permit_payload)
- statuses: INCOMPLETE, UNDER_REVIEW, ELIGIBLE, BLOCKED
- classifications: READY_FOR_REVIEW, NEEDS_EVIDENCE, HUMAN_REVIEW_REQUIRED
- risk/readiness: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_PERMIT, REQUEST_EVIDENCE, ESCALATE_REVIEW
- forbidden actions: AUTO_ISSUE_PERMIT, AUTO_OVERRIDE_ELIGIBILITY
- required evidence: tenant_id, vehicle_context, permit_type, compliance_context
- human review boundary: eligibility decisions remain human-controlled
- required tests: tenant fail-closed, determinism, readiness levels, forbidden actions
- anti-inflation boundary: no API/frontend/DB/KPI/Brain/event/autonomy/provider claims, L3 only

#### Module: parking_enforcement
- Current Level: L3
- Target Level: L3
- Source: A-026.9-RUNTIME
- Existing L2 evidence: deterministic foundation contract and tenant guard
- Primary gap: resolved
- Will do: classify enforcement review state, risk, and escalation recommendations deterministically
- Will NOT do: issue citations, mutate enforcement outcomes, expose APIs, or call providers
- Expected runtime file: backend/app/modules/parking_enforcement/service.py
- L3 function: evaluate_parking_enforcement_readiness(tenant_id, enforcement_payload)
- statuses: REPORTED, REVIEWING, ESCALATED, CLOSED
- classifications: READY_FOR_REVIEW, NEEDS_SUPPORTING_EVIDENCE, HUMAN_REVIEW_REQUIRED
- risk/readiness: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_CASE, REQUEST_EVIDENCE, ESCALATE_REVIEW
- forbidden actions: AUTO_CITATION, AUTO_CLOSE_CASE, AUTO_OVERRIDE_POLICY
- required evidence: tenant_id, violation_context, evidence_snapshot, policy_context
- human review boundary: citation and closure remain human-controlled
- required tests: tenant validation, determinism, risk banding, forbidden actions
- anti-inflation boundary: no API/frontend/DB/KPI/Brain/event/autonomy/provider claims, L3 only

#### Module: event_registration_portal
- Current Level: L3
- Target Level: L3
- Source: A-026.9-RUNTIME
- Existing L2 evidence: deterministic foundation contract and tenant guard
- Primary gap: resolved
- Will do: evaluate registration readiness and eligibility routing deterministically
- Will NOT do: accept registrations automatically, mutate schedules, expose API/UI surfaces, or call providers
- Expected runtime file: backend/app/modules/event_registration_portal/service.py
- L3 function: evaluate_event_registration_portal_readiness(tenant_id, registration_payload)
- statuses: DRAFT, READY, PENDING_REVIEW, BLOCKED
- classifications: READY_FOR_REGISTRATION_REVIEW, NEEDS_PROFILE_COMPLETION, HUMAN_REVIEW_REQUIRED
- risk/readiness: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_REGISTRATION, REQUEST_EVIDENCE, ESCALATE_REVIEW
- forbidden actions: AUTO_CONFIRM_REGISTRATION, AUTO_OVERRIDE_CAPACITY, AUTO_WAITLIST_ASSIGNMENT
- required evidence: tenant_id, event_id, eligibility_context, capacity_context
- human review boundary: final registration approval remains human-controlled
- required tests: tenant validation, determinism, readiness/risk, forbidden actions
- anti-inflation boundary: no API/frontend/DB/KPI/Brain/event/autonomy/provider claims, L3 only

#### Module: parent_engagement
- Current Level: L3
- Target Level: L3
- Source: A-026.9-RUNTIME
- Existing L2 evidence: deterministic foundation contract and tenant guard
- Primary gap: resolved
- Will do: classify engagement readiness and outreach risk deterministically
- Will NOT do: send messages, mutate parent records, or call providers
- Expected runtime file: backend/app/modules/parent_engagement/service.py
- L3 function: evaluate_parent_engagement_readiness(tenant_id, engagement_payload)
- statuses: INACTIVE, CONTACT_PENDING, ENGAGED, BLOCKED
- classifications: READY_FOR_OUTREACH_REVIEW, NEEDS_CONTACT_EVIDENCE, HUMAN_REVIEW_REQUIRED
- risk/readiness: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_OUTREACH, REQUEST_EVIDENCE, ESCALATE_REVIEW
- forbidden actions: AUTO_SEND_MESSAGE, AUTO_MARK_ENGAGED, AUTO_OVERRIDE_CONTACT_RULES
- required evidence: tenant_id, contact_context, consent_context, outreach_context
- human review boundary: final outreach decisions remain human-controlled
- required tests: tenant validation, determinism, readiness/risk, forbidden actions
- anti-inflation boundary: no API/frontend/DB/KPI/Brain/event/autonomy/provider claims, L3 only

#### Module: alumni_relations_ops
- Current Level: L3
- Target Level: L3
- Source: A-026.9-RUNTIME
- Existing L2 evidence: deterministic foundation contract and tenant guard
- Primary gap: resolved
- Will do: classify alumni outreach readiness and relationship risk deterministically
- Will NOT do: send outreach, mutate data, expose APIs, or call providers
- Expected runtime file: backend/app/modules/alumni_relations_ops/service.py
- L3 function: evaluate_alumni_relations_ops_readiness(tenant_id, alumni_payload)
- statuses: NEW, VERIFIED, CONTACTABLE, BLOCKED
- classifications: READY_FOR_OUTREACH_REVIEW, NEEDS_PROFILE_EVIDENCE, HUMAN_REVIEW_REQUIRED
- risk/readiness: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_PROFILE, REQUEST_EVIDENCE, ESCALATE_REVIEW
- forbidden actions: AUTO_SEND_OUTREACH, AUTO_MARK_VERIFIED, AUTO_OVERRIDE_CONSENT
- required evidence: tenant_id, contact_context, consent_context, profile_context
- human review boundary: consent-sensitive outreach remains human-controlled
- required tests: tenant validation, determinism, readiness/risk, forbidden actions
- anti-inflation boundary: no API/frontend/DB/KPI/Brain/event/autonomy/provider claims, L3 only

#### Module: donations_fundraising
- Current Level: L3
- Target Level: L3
- Source: A-026.9-RUNTIME
- Existing L2 evidence: deterministic foundation contract and tenant guard
- Primary gap: resolved
- Will do: evaluate fundraising readiness and risk deterministically
- Will NOT do: process donations, mutate ledger state, expose APIs, or call payment providers
- Expected runtime file: backend/app/modules/donations_fundraising/service.py
- L3 function: evaluate_donations_fundraising_readiness(tenant_id, fundraising_payload)
- statuses: PIPELINE_EMPTY, PIPELINE_ACTIVE, REVIEW_REQUIRED, BLOCKED
- classifications: READY_FOR_REVIEW, NEEDS_SUPPORTING_EVIDENCE, HUMAN_REVIEW_REQUIRED
- risk/readiness: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_CAMPAIGN, REQUEST_EVIDENCE, ESCALATE_REVIEW
- forbidden actions: AUTO_LAUNCH_CAMPAIGN, AUTO_ALLOCATE_FUNDS, AUTO_OVERRIDE_COMPLIANCE
- required evidence: tenant_id, campaign_context, compliance_context, donor_context
- human review boundary: campaign and allocation approval remain human-controlled
- required tests: tenant validation, determinism, readiness/risk, forbidden actions
- anti-inflation boundary: no API/frontend/DB/KPI/Brain/event/autonomy/provider claims, L3 only

#### Module: exam_integrity_analytics
- Current Level: L3
- Target Level: L3
- Source: A-026.9-RUNTIME
- Existing L2 evidence: deterministic foundation contract and tenant guard
- Primary gap: resolved
- Will do: evaluate exam integrity review readiness and escalation risk deterministically
- Will NOT do: score exams autonomously, mutate results, expose APIs, or call providers
- Expected runtime file: backend/app/modules/exam_integrity_analytics/service.py
- L3 function: evaluate_exam_integrity_analytics_readiness(tenant_id, exam_payload)
- statuses: CLEAN, FLAGGED, UNDER_REVIEW, BLOCKED
- classifications: READY_FOR_REVIEW, NEEDS_EVIDENCE, HUMAN_REVIEW_REQUIRED
- risk/readiness: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_SIGNAL, REQUEST_EVIDENCE, ESCALATE_REVIEW
- forbidden actions: AUTO_ACCUSATION, AUTO_SCORE_MODIFICATION, AUTO_OVERRIDE_POLICY
- required evidence: tenant_id, exam_context, integrity_context, review_context
- human review boundary: integrity findings remain human-reviewed
- required tests: tenant validation, determinism, readiness/risk, anti-inflation
- anti-inflation boundary: no API/frontend/DB/KPI/Brain/event/autonomy/provider claims, L3 only

#### Module: mobile_push_gateway
- Current Level: L3
- Target Level: L3
- Source: A-026.9-RUNTIME
- Existing L2 evidence: deterministic foundation contract and tenant guard
- Primary gap: resolved
- Will do: preview notification readiness and routing deterministically without sending
- Will NOT do: send push notifications, call providers, mutate user records, or expose APIs
- Expected runtime file: backend/app/modules/mobile_push_gateway/service.py
- L3 function: evaluate_mobile_push_gateway_readiness(tenant_id, push_payload)
- statuses: PREVIEW_ONLY, READY_TO_SEND, BLOCKED, REVIEW_REQUIRED
- classifications: READY_FOR_PREVIEW, NEEDS_TEMPLATE_EVIDENCE, HUMAN_REVIEW_REQUIRED
- risk/readiness: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: PREVIEW_MESSAGE, REVIEW_TEMPLATE, REQUEST_EVIDENCE
- forbidden actions: AUTO_SEND_PUSH, AUTO_CALL_PROVIDER, AUTO_OVERRIDE_LIMITS
- required evidence: tenant_id, notification_context, template_context, consent_context
- human review boundary: send actions remain human-controlled
- required tests: tenant validation, determinism, readiness/risk, no-provider-call
- anti-inflation boundary: no API/frontend/DB/KPI/Brain/event/autonomy/provider claims, L3 only

### Expected Runtime Files
| File | Expected Action | Reason |
|---|---|---|
| backend/app/modules/parking_permit_ops/service.py | update | add deterministic permit readiness logic |
| backend/app/modules/parking_enforcement/service.py | update | add deterministic enforcement review logic |
| backend/app/modules/event_registration_portal/service.py | update | add deterministic registration readiness logic |
| backend/app/modules/parent_engagement/service.py | update | add deterministic engagement logic |
| backend/app/modules/alumni_relations_ops/service.py | update | add deterministic outreach logic |
| backend/app/modules/donations_fundraising/service.py | update | add deterministic fundraising logic |
| backend/app/modules/exam_integrity_analytics/service.py | update | add deterministic integrity analytics logic |
| backend/app/modules/mobile_push_gateway/service.py | update | add deterministic push preview logic |
| backend/tests/test_a0269_l2_to_l3_deterministic_service_logic_batch2.py | add | targeted deterministic L3 test suite |
| SBS_UB.md | update | tracker control block and execution staging |
| SBS_UB_150_MODULE_NORMALIZATION.md | update | add A-026.9-SPEC section and keep metrics unchanged |
| A-026.9-SPEC-L2_TO_L3_DETERMINISTIC_SERVICE_LOGIC_BATCH2_REPORT.md | add | runtime planning evidence report |

### A-026.9 Targeted Test Plan

Preferred test file: backend/tests/test_a0269_l2_to_l3_deterministic_service_logic_batch2.py

Test groups:
1. import validation
2. tenant fail-closed validation
3. deterministic output validation
4. classification/status/risk logic
5. required evidence validation
6. allowed/forbidden action validation
7. provider boundary validation where relevant
8. anti-inflation validation
9. no API/frontend/Brain/KPI behavior

Expected test count:
- minimum 35
- preferred 50–80 depending selected modules

Validation mode:
- fast direct Docker validation mode

Preferred fast Docker command:

```bash
cd /home/sbs/AI

docker run --rm \
   --env-file /home/sbs/AI/infra/.env \
   -v /home/sbs/AI/backend/app:/app/app \
   -v /home/sbs/AI/backend/tests:/app/tests \
   -w /app \
   ai-backend-tests:latest \
   python -m pytest -q \
   tests/test_a0269_l2_to_l3_deterministic_service_logic_batch2.py \
   -o addopts='' \
   --no-cov \
   -rA \
   --durations=30
```

### Expected Maturity Movement

Before A-026.9-RUNTIME:
- L0=0
- L1=0
- L2=21
- L3=34
- L4=68
- L5=25
- L6=2

After A-026.9-RUNTIME:
- L0=0
- L1=0
- L2=21-N
- L3=34+N
- L4=68
- L5=25
- L6=2
- total=150
- maturity_arithmetic_check=PASS

If selected batch size is 8:
- L2=13
- L3=42
- L4=68
- L5=25
- L6=2
- total=150
- maturity_arithmetic_check=PASS

In this spec action:
- do NOT change metrics yet
- record expected formula only

### Anti-Inflation Boundaries

- no runtime code changes
- no test implementation changes
- no API or router additions
- no frontend additions
- no DB mutations/migrations
- no KPI/Brain/autonomy claims
- no maturity-level changes in this spec phase

### Definition of Done (A-026.9-SPEC)

- 21-module L2 inventory extracted and verified
- bounded 6-8 module selection completed (selected N=8)
- deterministic L3 standard defined
- deep module-by-module runtime specifications defined
- expected runtime files and targeted test plan defined
- expected post-runtime formula documented
- SBS tracker and normalization spec sections updated
- standalone A-026.9 spec report created

---

## A-026.6-RUNTIME — L4→L5 Evidence / Governance / KPI / Brain-Readiness

**Status**: COMPLETE

**Commit**: test(wave14): A-026.6 implement L4 to L5 evidence governance readiness

**Selected batch**: 4 modules lifted from L4/Bucket-D to L5/Bucket-E.

| Module | Previous Level | New Level | Evidence Source |
|---|---:|---:|---|
| human_approved_timetable_workflow | L4 | L5 | A-026.6-RUNTIME deterministic L5-readiness contract |
| timetable_approval_queue | L4 | L5 | A-026.6-RUNTIME deterministic L5-readiness contract |
| timetable_change_kpi_dashboard | L4 | L5 | A-026.6-RUNTIME deterministic L5-readiness contract |
| workload_management | L4 | L5 | A-026.6-RUNTIME deterministic L5-readiness contract |

**Implementation summary**:
- deterministic evidence lineage contracts added to service.py for all 4 modules
- governance mapping contracts (category, human_review_owner, escalation_boundary) added
- KPI-readiness boundary fields added (no fake KPI values)
- Brain candidate/no-execution boundaries added
- L5-readiness Pydantic schemas added to schemas.py for all 4 modules
- read-only L5-readiness GET routes added to router.py for all 4 modules (permission-guarded, tenant-safe)
- test file: backend/tests/test_a0266_l4_to_l5_evidence_governance_readiness.py (58 tests PASS)
- A-026.3+A-026.4+A-026.5+A-026.6 continuity: 218 tests PASS

**Anti-inflation confirmation**:
- no autonomous execution
- no fake KPI values
- no Brain execution
- no L6 claim
- no frontend pages
- no DB mutations
- no event emission
- no provider calls
- extension 25 unchanged

**Metrics after A-026.6-RUNTIME**:
- L0=0, L1=16, L2=13, L3=26, L4=68, L5=25, L6=2, total=150, maturity_arithmetic_check=PASS

**Next action**: A-026.7-SPEC

## A-026.7-SPEC — Next L4→L5 Evidence / Governance / KPI / Brain-Readiness Batch Specification

**Status**: SPEC ONLY (planning phase, no runtime code)

**Purpose**: select a bounded current-L4 batch for future A-026.7-RUNTIME and define auditable L5-readiness contracts without runtime execution claims, autonomous actions, or fake Brain/KPI inflation.

### Source-of-Truth Snapshot (A-026.7-SPEC)

- **Authoritative tracker**: SBS_UB.md
- **Reconciled matrix**: SBS_UB_150_MODULE_NORMALIZATION.md
- **Current baseline metrics**: L0=0, L1=16, L2=13, L3=26, L4=68, L5=25, L6=2, total=150 (post-A-026.6-RUNTIME)
- **Extension metrics**: extension_total_count=25, total_tracked_modules=175, separation=PASS
- **Last completed action**: A-026.6-RUNTIME + A-026.6.B1 reconciliation
- **Current action**: A-026.7-SPEC (this planning phase)
- **Next action in tracker**: A-026.7-RUNTIME

### L4 Inventory (A-026.7-SPEC)

Current L4 modules extracted from baseline matrix after A-026.6-RUNTIME:

- **Expected L4 count**: 68 (verified; 4 modules moved L4→L5 in A-026.6)
- **Found L4 count**: 68 ✓
- **Status**: PASS

### Selected A-026.7 Batch

**Selected batch size**: 4 modules (high-value L4→L5-readiness candidates)

| # | Module | Domain | L4 Evidence Source | Primary Gap | Why Selected | Target | Risk |
|---:|---|---|---|---|---|---:|---|
| 1 | **attendance** | Student & Campus Life | A-024.4 | KPI_evidence_or_Brain_mapping_missing | Highest operational leverage for academic risk/governance; evidence lineage clear; deterministic governance boundary. | L5-readiness | medium |
| 2 | **observability** | Integrations & Platform | A-024.3 | KPI_evidence_or_Brain_mapping_missing | Strong platform health signal candidate; observability metrics map clearly to evidence lineage; infrastructure governance with high auditability. | L5-readiness | medium |
| 3 | **student_portal** | Student & Campus Life | A-024.4 | KPI_evidence_or_Brain_mapping_missing | Product-core visibility and governance; student-facing requires clear evidence lineage for user-impact decisions; deterministic readiness semantics. | L5-readiness | medium |
| 4 | **timetable_change_proposal** | Planned Expansion | A-026.5-RUNTIME | KPI_evidence_or_Brain_mapping_missing | Complements A-026.6 governance work; full timetable governance envelope with prior L4 approval queue work; deterministic proposal-to-evidence chain. | L5-readiness | medium |

### A-026.7 L5-Readiness Standard

Each selected module must deliver:

1. **Evidence Lineage Contract**: Explicit evidence sources from L4 visibility; deterministic evidence notes; completeness status (COMPLETE, PARTIAL, PENDING); no fake data.
2. **Governance Mapping**: Decision-support category; human-review owner; escalation boundary; allowed/forbidden action lists.
3. **KPI-Readiness Boundary**: KPI category; completeness status; confidence level; NO fake KPI computation; "READINESS"/"CANDIDATE" language only, not "COMPUTED"/"DERIVED".
4. **Brain-Readiness Boundary**: Signal candidate (YES/NO, deterministic only); execution=FORBIDDEN; no L6 claim.
5. **Tenant/Audit/Security**: Tenant-scoped evidence; fail-closed tenant handling; permission-aware access; audit_evidence_notes; human_review_required=true.
6. **Tests** (per module): Evidence contract, governance mapping, KPI boundary, Brain boundary, tenant/security, anti-inflation validation.

### Expected Runtime Files (A-026.7)

*Note: This specification does NOT create these files; runtime implementation will.*

| File | Action | Purpose |
|---|---|---|
| `backend/app/modules/attendance/service.py` | augment | Add L5-readiness function and safety flags |
| `backend/app/modules/attendance/schemas.py` | augment | Add L5-readiness response schema |
| `backend/app/modules/attendance/router.py` | add/augment | Add L5-readiness GET route with permission gate |
| `backend/app/modules/observability/service.py` | augment | Add L5-readiness governance mapping |
| `backend/app/modules/observability/schemas.py` | augment | Add L5-readiness response schema |
| `backend/app/modules/observability/router.py` | add/augment | Add L5-readiness GET route with permission gate |
| `backend/app/modules/student_portal/service.py` | augment | Add L5-readiness evidence/governance function |
| `backend/app/modules/student_portal/schemas.py` | augment | Add L5-readiness response schema |
| `backend/app/modules/student_portal/router.py` | add/augment | Add L5-readiness GET route with permission gate |
| `backend/app/modules/timetable_change_proposal/service.py` | augment | Add L5-readiness governance mapping |
| `backend/app/modules/timetable_change_proposal/schemas.py` | augment | Add L5-readiness response schema |
| `backend/app/modules/timetable_change_proposal/router.py` | add/augment | Add L5-readiness GET route with permission gate |
| `backend/app/main.py` | update | Register L5-readiness routes |
| `backend/tests/test_a0267_l4_to_l5_evidence_governance_readiness.py` | add | Targeted L5-readiness contract tests (32-50 tests) |
| `A-026.7-SPEC-NEXT_L4_TO_L5_EVIDENCE_GOVERNANCE_READINESS_BATCH_SPECIFICATION.md` | add | Full spec document (deliverable) |

### A-026.7 Targeted Test Plan

**Test file**: `backend/tests/test_a0267_l4_to_l5_evidence_governance_readiness.py`

**Test groups** (per module):
1. Import/registration validation (1-2 tests)
2. Evidence lineage contract (2-3 tests)
3. Governance mapping (2-3 tests)
4. KPI-readiness boundary (1-2 tests)
5. Brain-readiness boundary (2-3 tests)
6. Tenant/security (3-4 tests)
7. Audit/evidence trail (1-2 tests)
8. Anti-inflation (2-3 tests)

**Expected test count**: 32-50 targeted tests (4 modules × 8-12 tests per module)

**Continuity validation**: A-026.3+A-026.4+A-026.5+A-026.6+A-026.7 combined pytest (expected ~240+ PASS)

### Expected Maturity Movement (A-026.7)

**No movement in this SPEC phase.**

If A-026.7-RUNTIME succeeds:

```
Before: L0=0, L1=16, L2=13, L3=26, L4=68, L5=25, L6=2, total=150
After:  L0=0, L1=16, L2=13, L3=26, L4=64, L5=29, L6=2, total=150
Movement: L4: 68→64 (-4), L5: 25→29 (+4)
Arithmetic: PASS
```

### Anti-Inflation Boundaries (A-026.7-SPEC)

This specification introduces:
- ✓ NO runtime code
- ✓ NO maturity movement
- ✓ NO fake governance/KPI claims
- ✓ NO autonomous execution paths
- ✓ NO Brain execution
- ✓ NO L6 claims
- ✓ NO frontend pages
- ✓ NO database mutations
- ✓ NO provider calls

### Definition of Done (A-026.7-SPEC)

- ✓ Source-of-truth snapshot confirmed
- ✓ L4 inventory extracted and scored
- ✓ 4 modules selected with high L5-readiness fit
- ✓ L5-readiness standard defined
- ✓ Deep per-module specifications written with governance/KPI/Brain boundaries
- ✓ Test plan defined (32-50 targeted tests)
- ✓ Runtime files planned
- ✓ Expected maturity movement documented
- ✓ Security/SaaS boundaries defined
- ✓ Anti-inflation boundaries confirmed
- ✓ Full spec document delivered: A-026.7-SPEC-NEXT_L4_TO_L5_EVIDENCE_GOVERNANCE_READINESS_BATCH_SPECIFICATION.md

---
- ✓ Full spec document delivered: A-026.7-SPEC-NEXT_L4_TO_L5_EVIDENCE_GOVERNANCE_READINESS_BATCH_SPECIFICATION.md

---

## A-026.7.REPLAN — Strategic Pivot to Lower Maturity Gap Closure

**Status**: SPEC ONLY (planning/docs phase, no runtime code changes)

**Date**: 2026-05-12

**Purpose**: Strategic assessment of lower maturity gap closure (55 modules below L4) before continuing L4→L5 transitions. Evaluate 4 strategic options; select optimal batch; plan next runtime action.

### Decision Summary

**Discovered Issue**: After A-026.6-RUNTIME, 55 modules remain below L4 (L1=16, L2=13, L3=26, 36.7% of baseline). For SaaS/enterprise readiness, foundation gaps should be addressed before continuing top-layer L4→L5 transitions.

**Strategic Options Evaluated**:
| Option | Batch | Complexity | Gap Reduction | Product Visibility | Priority Score |
|---|---|---|---|---|---|
| A: L1→L2 First | 16 L1 modules (all service_contract_missing) | LOW | 55→39 (29%) | NONE (foundation) | 4.5/5.0 ✓ SELECTED |
| B: L2→L3 Next | 5-8 L2 modules (FSM/logic) | MEDIUM | Intermediate | NONE (internal) | 3.5/5.0 |
| C: L3→L4 Focused | 3-4 L3 modules (API/visibility) | MEDIUM-HIGH | Variable | HIGH (SaaS) | 4.0/5.0 |
| D: Mixed L1-L2-L3 | 6+3+2 modules | MIXED | Fragmented | Mixed | 3.0/5.0 |

**Decision**: **SELECT OPTION A — L1→L2 First (Bottom-Up Cleanup)**

**Rationale**:
1. All 16 L1 modules have identical gap: `service_contract_missing` (100% consistency)
2. Service contracts are lightweight — no routes, no frontend, no complex logic
3. Establishes reusable L2 service contract pattern
4. Reduces lower-level gap by 29% immediately (39 modules remain below L4)
5. Improves foundation consistency before heavier L3→L4 API work
6. Fast execution path (20-40 tests expected, 2-3 day estimate)
7. After L1→L2 succeeds, select L2→L3 or L3→L4 based on product priorities

### L1→L2 Batch (16 modules)

**All L1 Modules** (sorted by module number):

| # | Module | Domain | Current Gap | Target | Work Required | Tests | Status |
|---:|---|---|---|---:|---|---:|---|
| 18 | alumni_relations_ops | Planned Expansion | service_contract_missing | L2 | Deterministic service contract | 2-3 | PENDING_A026.7L1L2 |
| 42 | digital_certificates | Planned Expansion | service_contract_missing | L2 | Deterministic service contract | 2-3 | PENDING_A026.7L1L2 |
| 45 | donations_fundraising | Planned Expansion | service_contract_missing | L2 | Deterministic service contract | 2-3 | PENDING_A026.7L1L2 |
| 48 | event_registration_portal | Planned Expansion | service_contract_missing | L2 | Deterministic service contract | 2-3 | PENDING_A026.7L1L2 |
| 51 | exam_integrity_analytics | Planned Expansion | service_contract_missing | L2 | Deterministic service contract | 2-3 | PENDING_A026.7L1L2 |
| 71 | internship_marketplace | Planned Expansion | service_contract_missing | L2 | Deterministic service contract | 2-3 | PENDING_A026.7L1L2 |
| 77 | lab_operations | Planned Expansion | service_contract_missing | L2 | Deterministic service contract | 2-3 | PENDING_A026.7L1L2 |
| 81 | lms_assessment_center | Planned Expansion | service_contract_missing | L2 | Deterministic service contract | 2-3 | PENDING_A026.7L1L2 |
| 85 | mobile_push_gateway | Planned Expansion | service_contract_missing | L2 | Deterministic service contract | 2-3 | PENDING_A026.7L1L2 |
| 92 | parent_engagement | Planned Expansion | service_contract_missing | L2 | Deterministic service contract | 2-3 | PENDING_A026.7L1L2 |
| 95 | parking_enforcement | Planned Expansion | service_contract_missing | L2 | Deterministic service contract | 2-3 | PENDING_A026.7L1L2 |
| 96 | parking_permit_ops | Planned Expansion | service_contract_missing | L2 | Deterministic service contract | 2-3 | PENDING_A026.7L1L2 |
| 109 | publication_registry | Planned Expansion | service_contract_missing | L2 | Deterministic service contract | 2-3 | PENDING_A026.7L1L2 |
| 113 | records_hub | Planned Expansion | service_contract_missing | L2 | Deterministic service contract | 2-3 | PENDING_A026.7L1L2 |
| 117 | research_projects | Planned Expansion | service_contract_missing | L2 | Deterministic service contract | 2-3 | PENDING_A026.7L1L2 |
| 131 | student_success_analytics | Planned Expansion | service_contract_missing | L2 | Deterministic service contract | 2-3 | PENDING_A026.7L1L2 |

### Expected Maturity Formula

**Current State (post-A-026.6)**:
- L0=0, L1=16, L2=13, L3=26, L4=68, L5=25, L6=2, total=150

**After A-026.7.L1L2-RUNTIME (if all 16 succeed)**:
- L0=0, L1=0, L2=29, L3=26, L4=68, L5=25, L6=2, total=150
- **Gap reduction**: 55→26 modules below L4 (53% reduction)
- **Arithmetic check**: PASS ✓

### A-026.7-SPEC Status

**Deferred, NOT Invalidated**:
- Original A-026.7-SPEC remains valid and complete
- 4 L4→L5 candidates still relevant: attendance, observability, student_portal, timetable_change_proposal
- Full 722-line spec with deep per-module specifications and 32-50 test plan preserved
- Commit: b36e3e8 (A-026.7-SPEC select next L4 to L5 evidence governance batch)
- **Will resume after** L1→L2 and subsequent gap closures complete
- This is a priority shift, not cancellation

### Future Sequence (Approved Roadmap)

1. **A-026.7.L1L2-RUNTIME** ← **NEXT** (execute L1→L2 service contracts, 16 modules, 20-40 tests)
2. **A-026.7.L2L3-RUNTIME** (evaluate L2 batch, select 5-8 modules, implement FSM/service logic)
3. **A-026.7.L3L4-RUNTIME** (evaluate L3 batch, select 3-4 high-value modules, implement API/routes)
4. **A-026.7-RUNTIME** (resume original L4→L5 batch: attendance, observability, student_portal, timetable_change_proposal)

### Anti-Inflation Confirmation

A-026.7.REPLAN spec contains:
- ✓ NO runtime code implementation
- ✓ NO maturity metric changes
- ✓ NO service/schema/router modifications
- ✓ NO test implementations
- ✓ NO KPI/Brain/autonomy claims
- ✓ NO frontend pages
- ✓ A-026.7-SPEC preserved (not invalidated)

**Verdict**: PLANNING-ONLY, ANTI-INFLATION COMPLIANT ✓

---

## A-026.7.L1L2-RUNTIME — L1→L2 Foundation Service Contract Normalization

**Status**: RUNTIME COMPLETE

**Scope**: backend-only L1→L2 foundation service contract normalization for all 16 selected L1 modules.

### Runtime Outcome

- 16 modules lifted from L1/Bucket A to L2/Bucket B
- deterministic foundation service contracts implemented
- tenant fail-closed validation enforced (None/0/-1 rejected)
- targeted and continuity test evidence collected in fast Docker mode
- anti-inflation boundary preserved

### Selected Modules Lifted L1→L2

- alumni_relations_ops
- digital_certificates
- donations_fundraising
- event_registration_portal
- exam_integrity_analytics
- internship_marketplace
- lab_operations
- lms_assessment_center
- mobile_push_gateway
- parent_engagement
- parking_enforcement
- parking_permit_ops
- publication_registry
- records_hub
- research_projects
- student_success_analytics

### Test Evidence

- A-026.7 targeted (fast Docker): PASS (176 passed, 1 warning)
- Continuity (A-026.3 + A-026.4 + A-026.5 + A-026.6 + A-026.7): PASS (394 passed, 1 warning)
- tenant fail-closed coverage: PASS across all 16 modules
- deterministic contract output checks: PASS across all 16 modules
- anti-inflation safety-flag checks: PASS across all 16 modules

### Anti-Inflation Confirmation

- no API endpoints added
- no routers added
- no schemas added
- no frontend pages added
- no DB migrations added
- no KPI values/lineage claims added
- no Brain mapping/execution claims added
- no autonomous execution added
- no external provider calls added
- no L3/L4/L5/L6 claim in runtime code

### Metrics Update (After A-026.7.L1L2-RUNTIME)

- L0=0
- L1=0
- L2=29
- L3=26
- L4=68
- L5=25
- L6=2
- total=150
- maturity_arithmetic_check=PASS

### Bucket Update (After A-026.7.L1L2-RUNTIME)

- Bucket A=0
- Bucket B=29
- Bucket C=26
- Bucket D=68
- Bucket E=25
- Bucket F=2

### Extension Separation

- extension_total_count=25 (unchanged)
- total_tracked_modules=175 (unchanged)
- separation=PASS (baseline and extension remain isolated)

### Relationship to Deferred A-026.7-SPEC L4→L5 Backlog

- A-026.7-SPEC remains valid but deferred
- no cancellation of L4→L5 readiness backlog
- lower maturity gap closure executed first per A-026.7.REPLAN strategy

### Next Action

- A-026.8-SPEC

---

## A-026.8-SPEC — L2→L3 Deterministic Service Logic Batch Specification

**Status**: SPEC ONLY (planning-only, no runtime implementation)

**Purpose**: Select a bounded current-L2 batch for future A-026.8-RUNTIME and define deep deterministic L3 service-logic specifications with strict anti-inflation boundaries.

### L2 Extraction Summary

- expected L2 count: 29
- found L2 count: 29
- status: PASS
- tracker remains authoritative: SBS_UB.md
- runtime has not started: confirmed

### Selected A-026.8 Batch

Selected batch size: 8 (bounded, coherent, deterministic-logic safe)

| Selected Module | Current Level | Target Level | Why Selected | Expected L3 Logic | Required Tests | Risk |
|---|---:|---:|---|---|---|---|
| digital_certificates | L2 | L3 | stable post-A-026.7 foundation and high records trust value | certificate readiness/status and validation-state classification | tenant/logic/boundary/anti-inflation tests | medium |
| records_hub | L2 | L3 | core records reconciliation leverage | records completeness classification and remediation routing | tenant/logic/determinism tests | medium |
| student_success_analytics | L2 | L3 | high student-success governance value | risk/readiness banding and intervention recommendation classification | classification and boundary tests | medium |
| publication_registry | L2 | L3 | academic governance and traceability value | publication state/risk/readiness classification | state and forbidden-action tests | medium |
| research_projects | L2 | L3 | research workflow dependency and reuse value | project readiness/risk and next-step classification | readiness and transition tests | medium |
| lms_assessment_center | L2 | L3 | direct academic operations value | assessment readiness and control-state classification | deterministic output and classification tests | medium |
| lab_operations | L2 | L3 | operational planning coherence with facilities | capacity/safety/readiness classification | tenant and status boundary tests | medium |
| internship_marketplace | L2 | L3 | career outcomes and placement planning value | placement-readiness and risk classification | classification and anti-inflation tests | medium |

### A-026.8 L3 Deterministic Service Logic Standard

1. Deterministic business logic
- Service logic must do more than L2 foundation contract return.
- Each module must compute deterministic classification/status/readiness/risk outputs.
- Each output must include deterministic next recommended step.

2. Tenant fail-closed behavior
- tenant_id=None rejected
- tenant_id=0 rejected
- tenant_id<0 rejected
- valid tenant_id accepted
- all outputs tenant-scoped

3. Domain-specific rules
- module-specific statuses
- module-specific classifications
- readiness/risk levels
- allowed actions and forbidden actions
- required evidence list
- human-review boundary where relevant

4. Tests
- import validation
- tenant fail-closed checks
- deterministic output checks
- classification/status/risk checks
- boundary checks
- anti-inflation checks

5. Anti-inflation
- no API claim
- no frontend claim
- no KPI claim
- no Brain claim
- no autonomous execution
- no external provider call
- no L4/L5/L6 claim

### Module-by-Module Deep Specification

### Module: digital_certificates

#### Current State
- Current Level: L2
- Target Level: L3
- Source: A-026.7.L1L2-RUNTIME
- Existing L2 evidence: deterministic foundation contract + tenant fail-closed guard
- Primary gap: deterministic_service_logic_needed

#### Intended L3 Scope
- Will do: deterministic certificate readiness/state/risk classification and next-step logic
- Will NOT do: endpoints, frontend, DB mutation, signature provider integration, KPI/Brain/autonomy

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/digital_certificates/service.py | update | add L3 deterministic classification logic |

#### L3 Service Functions
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| classify_digital_certificate_state | classify certificate lifecycle state | tenant_id, certificate_payload | state, classification, next_step, actions, evidence | yes | yes |
| evaluate_digital_certificate_readiness | compute readiness/risk snapshot | tenant_id, validation_payload | readiness_level, risk_level, required_evidence_missing | yes | yes |

#### Domain Logic
- statuses: DRAFT, SUBMITTED, VERIFIED, REJECTED, EXPIRED
- classifications: READY_FOR_VERIFICATION, BLOCKED_DATA_GAP, REQUIRES_HUMAN_REVIEW
- risk/readiness: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: VALIDATE_METADATA, REVIEW_CERTIFICATE, MARK_VERIFIED
- forbidden actions: ISSUE_AUTONOMOUSLY, CALL_EXTERNAL_SIGN_PROVIDER
- required evidence: owner_identity, issuer_trace, issue_date, checksum
- human review boundary: verification/rejection decisions remain human-controlled

#### Tenant Safety
- invalid tenant: raise ValueError fail-closed
- valid tenant: deterministic scoped result
- output always includes tenant_id
- no cross-tenant lookup/aggregation

#### Required Tests
| Test | Purpose |
|---|---|
| test_digital_certificates_tenant_fail_closed | reject invalid tenant ids |
| test_digital_certificates_deterministic_classification | same input produces same classification |
| test_digital_certificates_readiness_levels | readiness and risk classification correctness |
| test_digital_certificates_forbidden_actions | anti-autonomy/provider boundaries |

#### Anti-Inflation Boundary
- no API endpoint, no frontend page, no DB mutation, no KPI values, no Brain signals, no event emission, no autonomous execution, L3 only

### Module: records_hub

#### Current State
- Current Level: L2
- Target Level: L3
- Source: A-026.7.L1L2-RUNTIME
- Existing L2 evidence: deterministic foundation contract
- Primary gap: deterministic_service_logic_needed

#### Intended L3 Scope
- Will do: deterministic records completeness and reconciliation state classification
- Will NOT do: API/portal, storage mutation, archival jobs, KPI/Brain logic

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/records_hub/service.py | update | add records completeness/reconciliation logic |

#### L3 Service Functions
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| classify_records_hub_state | classify records integrity state | tenant_id, records_payload | state, gaps, next_step, actions | yes | yes |
| evaluate_records_hub_readiness | summarize readiness and risk | tenant_id, records_payload | readiness_level, risk_level, missing_evidence | yes | yes |

#### Domain Logic
- statuses: COMPLETE, PARTIAL, INCONSISTENT, BLOCKED
- classifications: READY_FOR_RECONCILIATION, NEEDS_DATA_COMPLETION, HUMAN_REVIEW_REQUIRED
- risk/readiness: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: VALIDATE_RECORDS, FLAG_INCONSISTENCY, REQUEST_CORRECTION
- forbidden actions: AUTO_CORRECT_RECORDS, AUTO_APPROVE_RECORDS
- required evidence: student_id, source_system, record_timestamp, record_signature
- human review boundary: reconciliation acceptance remains human-approved

#### Tenant Safety
- invalid tenant rejected fail-closed
- valid tenant accepted with scoped output
- tenant_id always present in output
- no cross-tenant merge

#### Required Tests
| Test | Purpose |
|---|---|
| test_records_hub_tenant_fail_closed | fail-closed tenant behavior |
| test_records_hub_classification_determinism | deterministic classification outputs |
| test_records_hub_missing_evidence_classification | correct missing-evidence handling |
| test_records_hub_forbidden_actions | anti-autonomy boundary validation |

#### Anti-Inflation Boundary
- no API endpoint, no frontend page, no DB mutation, no KPI values, no Brain signals, no event emission, no autonomous execution, L3 only

### Module: student_success_analytics

#### Current State
- Current Level: L2
- Target Level: L3
- Source: A-026.7.L1L2-RUNTIME
- Existing L2 evidence: deterministic foundation contract
- Primary gap: deterministic_service_logic_needed

#### Intended L3 Scope
- Will do: deterministic success risk/readiness classification and intervention recommendation category
- Will NOT do: KPI calculations, ML scoring, autonomous interventions, API/frontend

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/student_success_analytics/service.py | update | add deterministic risk/readiness logic |

#### L3 Service Functions
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| assess_student_success_risk | classify risk/readiness band | tenant_id, student_context | risk_band, readiness_band, next_step | yes | yes |
| classify_student_success_state | classify intervention state | tenant_id, student_context | state, action_set, evidence_requirements | yes | yes |

#### Domain Logic
- statuses: STABLE, WATCHLIST, AT_RISK, CRITICAL_REVIEW
- classifications: READY_FOR_REVIEW, NEEDS_MORE_EVIDENCE, ESCALATE_TO_HUMAN
- risk/readiness: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_CASE, REQUEST_EVIDENCE, SCHEDULE_HUMAN_INTERVENTION
- forbidden actions: AUTO_INTERVENE, AUTO_DISMISS_RISK
- required evidence: attendance_context, grade_context, advisor_notes
- human review boundary: final intervention decisions require human approval

#### Tenant Safety
- invalid tenant rejected
- valid tenant returns deterministic tenant-scoped output
- no cross-tenant analytics aggregation

#### Required Tests
| Test | Purpose |
|---|---|
| test_student_success_tenant_fail_closed | reject invalid tenants |
| test_student_success_determinism | deterministic classification under same inputs |
| test_student_success_risk_banding | risk/readiness band correctness |
| test_student_success_forbidden_actions | no autonomous action boundary |

#### Anti-Inflation Boundary
- no API endpoint, no frontend page, no DB mutation, no KPI values, no Brain signals, no event emission, no autonomous execution, L3 only

### Module: publication_registry

#### Current State
- Current Level: L2
- Target Level: L3
- Source: A-026.7.L1L2-RUNTIME
- Existing L2 evidence: deterministic foundation contract
- Primary gap: deterministic_service_logic_needed

#### Intended L3 Scope
- Will do: deterministic publication-state and readiness classification
- Will NOT do: publication indexing jobs, external publisher calls, API/frontend

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/publication_registry/service.py | update | add publication lifecycle/readiness logic |

#### L3 Service Functions
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| classify_publication_registry_state | classify publication status/readiness | tenant_id, publication_payload | state, readiness, next_step | yes | yes |
| assess_publication_registry_risk | classify registry risk | tenant_id, publication_payload | risk_level, evidence_gaps, review_required | yes | yes |

#### Domain Logic
- statuses: DRAFT, PENDING_REVIEW, APPROVED, REJECTED, ARCHIVED
- classifications: READY_FOR_REVIEW, REQUIRES_METADATA_COMPLETION, HUMAN_REVIEW_REQUIRED
- risk/readiness: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: VALIDATE_METADATA, ROUTE_FOR_REVIEW, MARK_APPROVED
- forbidden actions: AUTO_PUBLISH, AUTO_APPROVE
- required evidence: author_id, publication_type, submission_date, source_reference
- human review boundary: approval/rejection remains human-controlled

#### Tenant Safety
- fail-closed invalid tenant behavior
- deterministic tenant-scoped output for valid tenant
- no cross-tenant publication aggregation

#### Required Tests
| Test | Purpose |
|---|---|
| test_publication_registry_tenant_fail_closed | tenant guard validation |
| test_publication_registry_state_classification | deterministic state classification |
| test_publication_registry_risk_assessment | risk and evidence-gap handling |
| test_publication_registry_forbidden_actions | anti-autonomy boundary |

#### Anti-Inflation Boundary
- no API endpoint, no frontend page, no DB mutation, no KPI values, no Brain signals, no event emission, no autonomous execution, L3 only

### Module: research_projects

#### Current State
- Current Level: L2
- Target Level: L3
- Source: A-026.7.L1L2-RUNTIME
- Existing L2 evidence: deterministic foundation contract
- Primary gap: deterministic_service_logic_needed

#### Intended L3 Scope
- Will do: deterministic project readiness/risk and governance-state classification
- Will NOT do: grant disbursement, workflow automation, API/frontend

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/research_projects/service.py | update | add project readiness and risk logic |

#### L3 Service Functions
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| evaluate_research_project_readiness | compute readiness profile | tenant_id, project_payload | readiness_level, blockers, next_step | yes | yes |
| classify_research_project_risk | classify project risk | tenant_id, project_payload | risk_level, escalation_needed, actions | yes | yes |

#### Domain Logic
- statuses: INITIATED, PLANNING, EXECUTION_READY, BLOCKED, UNDER_REVIEW
- classifications: READY_TO_PROGRESS, NEEDS_APPROVAL_INPUT, ESCALATE_HUMAN_REVIEW
- risk/readiness: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_SCOPE, REQUEST_EVIDENCE, ROUTE_HUMAN_REVIEW
- forbidden actions: AUTO_APPROVE_PROJECT, AUTO_ESCALATE_WITHOUT_REVIEW
- required evidence: project_owner, scope_document, compliance_context, timeline_context
- human review boundary: progression approval remains human-controlled

#### Tenant Safety
- invalid tenant rejected fail-closed
- tenant-scoped deterministic outputs for valid tenant
- no cross-tenant project decisioning

#### Required Tests
| Test | Purpose |
|---|---|
| test_research_projects_tenant_fail_closed | tenant validation |
| test_research_projects_readiness_determinism | deterministic readiness outcomes |
| test_research_projects_risk_classification | risk-level correctness |
| test_research_projects_forbidden_actions | anti-autonomy boundary |

#### Anti-Inflation Boundary
- no API endpoint, no frontend page, no DB mutation, no KPI values, no Brain signals, no event emission, no autonomous execution, L3 only

### Module: lms_assessment_center

#### Current State
- Current Level: L2
- Target Level: L3
- Source: A-026.7.L1L2-RUNTIME
- Existing L2 evidence: deterministic foundation contract
- Primary gap: deterministic_service_logic_needed

#### Intended L3 Scope
- Will do: deterministic assessment readiness and integrity-state classification
- Will NOT do: proctoring automation, grading automation, API/frontend

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/lms_assessment_center/service.py | update | add assessment control-state logic |

#### L3 Service Functions
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| classify_lms_assessment_state | classify assessment control state | tenant_id, assessment_payload | state, readiness, next_step, actions | yes | yes |
| assess_lms_assessment_risk | classify risk and evidence gaps | tenant_id, assessment_payload | risk_level, evidence_gaps, escalation | yes | yes |

#### Domain Logic
- statuses: CONFIG_PENDING, READY_FOR_REVIEW, BLOCKED, APPROVED_FOR_DELIVERY
- classifications: READY_FOR_HUMAN_REVIEW, NEEDS_CONFIGURATION, INTEGRITY_REVIEW_REQUIRED
- risk/readiness: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: VALIDATE_CONFIGURATION, REQUEST_CORRECTION, ROUTE_REVIEW
- forbidden actions: AUTO_PUBLISH_ASSESSMENT, AUTO_OVERRIDE_INTEGRITY_CHECK
- required evidence: rubric_presence, identity_policy, schedule_context, integrity_controls
- human review boundary: delivery approval remains human-controlled

#### Tenant Safety
- fail-closed invalid tenants
- deterministic tenant-scoped outputs for valid tenants
- no cross-tenant assessment data handling

#### Required Tests
| Test | Purpose |
|---|---|
| test_lms_assessment_tenant_fail_closed | tenant safety |
| test_lms_assessment_state_determinism | deterministic state outputs |
| test_lms_assessment_risk_boundaries | risk/readiness boundary behavior |
| test_lms_assessment_forbidden_actions | no autonomous publication |

#### Anti-Inflation Boundary
- no API endpoint, no frontend page, no DB mutation, no KPI values, no Brain signals, no event emission, no autonomous execution, L3 only

### Module: lab_operations

#### Current State
- Current Level: L2
- Target Level: L3
- Source: A-026.7.L1L2-RUNTIME
- Existing L2 evidence: deterministic foundation contract
- Primary gap: deterministic_service_logic_needed

#### Intended L3 Scope
- Will do: deterministic capacity/safety/readiness classification for lab operations
- Will NOT do: facility actuation, autonomous scheduling, API/frontend

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/lab_operations/service.py | update | add deterministic lab readiness logic |

#### L3 Service Functions
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| classify_lab_operations_state | classify lab operation state | tenant_id, lab_payload | state, readiness, actions, next_step | yes | yes |
| assess_lab_operations_risk | classify safety/capacity risk | tenant_id, lab_payload | risk_level, blockers, escalation | yes | yes |

#### Domain Logic
- statuses: CAPACITY_READY, CAPACITY_LIMITED, SAFETY_BLOCKED, REVIEW_REQUIRED
- classifications: READY_FOR_OPERATION, NEEDS_CAPACITY_ADJUSTMENT, HUMAN_SAFETY_REVIEW
- risk/readiness: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_CAPACITY, REQUEST_SAFETY_EVIDENCE, ESCALATE_HUMAN_REVIEW
- forbidden actions: AUTO_APPROVE_SAFETY, AUTO_ASSIGN_CAPACITY
- required evidence: safety_checklist, capacity_snapshot, supervisor_context
- human review boundary: safety override decisions remain human-controlled

#### Tenant Safety
- invalid tenant rejected
- valid tenant returns tenant-scoped deterministic output
- no cross-tenant capacity comparison

#### Required Tests
| Test | Purpose |
|---|---|
| test_lab_operations_tenant_fail_closed | tenant guard |
| test_lab_operations_state_classification | deterministic state logic |
| test_lab_operations_risk_classification | risk and escalation rules |
| test_lab_operations_forbidden_actions | no autonomous safety/capacity action |

#### Anti-Inflation Boundary
- no API endpoint, no frontend page, no DB mutation, no KPI values, no Brain signals, no event emission, no autonomous execution, L3 only

### Module: internship_marketplace

#### Current State
- Current Level: L2
- Target Level: L3
- Source: A-026.7.L1L2-RUNTIME
- Existing L2 evidence: deterministic foundation contract
- Primary gap: deterministic_service_logic_needed

#### Intended L3 Scope
- Will do: deterministic placement-readiness and matching-risk classification
- Will NOT do: autonomous matching, provider integrations, API/frontend

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/internship_marketplace/service.py | update | add placement-readiness and risk logic |

#### L3 Service Functions
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| classify_internship_marketplace_state | classify placement state | tenant_id, internship_payload | state, readiness, next_step, actions | yes | yes |
| assess_internship_marketplace_risk | classify matching and compliance risk | tenant_id, internship_payload | risk_level, evidence_gaps, review_required | yes | yes |

#### Domain Logic
- statuses: PROFILE_INCOMPLETE, READY_FOR_REVIEW, MATCH_READY, BLOCKED
- classifications: READY_FOR_MATCH_REVIEW, NEEDS_PROFILE_EVIDENCE, HUMAN_MATCH_REVIEW_REQUIRED
- risk/readiness: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_PROFILE, REQUEST_EVIDENCE, ROUTE_HUMAN_REVIEW
- forbidden actions: AUTO_MATCH_ASSIGNMENT, AUTO_COMPLIANCE_APPROVAL
- required evidence: profile_completeness, eligibility_context, compliance_acknowledgement
- human review boundary: match assignment remains human-controlled

#### Tenant Safety
- invalid tenant rejected fail-closed
- deterministic tenant-scoped output on valid tenant
- no cross-tenant candidate/placement blending

#### Required Tests
| Test | Purpose |
|---|---|
| test_internship_marketplace_tenant_fail_closed | tenant validation |
| test_internship_marketplace_determinism | deterministic classification |
| test_internship_marketplace_risk_and_readiness | readiness/risk correctness |
| test_internship_marketplace_forbidden_actions | no autonomous matching |

#### Anti-Inflation Boundary
- no API endpoint, no frontend page, no DB mutation, no KPI values, no Brain signals, no event emission, no autonomous execution, L3 only

### Expected A-026.8 Runtime Files

| File | Expected Action | Reason |
|---|---|---|
| backend/app/modules/digital_certificates/service.py | update | add deterministic L3 classification logic |
| backend/app/modules/records_hub/service.py | update | add deterministic records logic |
| backend/app/modules/student_success_analytics/service.py | update | add deterministic risk/readiness logic |
| backend/app/modules/publication_registry/service.py | update | add deterministic publication logic |
| backend/app/modules/research_projects/service.py | update | add deterministic project logic |
| backend/app/modules/lms_assessment_center/service.py | update | add deterministic assessment logic |
| backend/app/modules/lab_operations/service.py | update | add deterministic lab operations logic |
| backend/app/modules/internship_marketplace/service.py | update | add deterministic placement logic |
| backend/tests/test_a0268_l2_to_l3_deterministic_service_logic.py | add | targeted deterministic L3 test suite |
| SBS_UB.md | update in runtime | tracker runtime evidence reconciliation |
| SBS_UB_150_MODULE_NORMALIZATION.md | update in runtime | row-level L2→L3 movement after PASS evidence |
| A-026.8-RUNTIME-L2_TO_L3_DETERMINISTIC_SERVICE_LOGIC_REPORT.md | add in runtime | runtime evidence report |

### A-026.8 Targeted Test Plan

Preferred test file:
- backend/tests/test_a0268_l2_to_l3_deterministic_service_logic.py

Test groups:
1. import validation
2. tenant fail-closed validation
3. deterministic output validation
4. classification/status/risk logic validation
5. required evidence validation
6. allowed/forbidden action validation
7. anti-inflation validation
8. no provider/API/frontend/Brain/KPI behavior validation

Expected test count:
- minimum: 25
- preferred: 40-70

Validation mode:
- fast direct Docker mode (same bind-mount pattern used in A-026.7)

### Expected Maturity Movement

Before A-026.8-RUNTIME:
- L0=0
- L1=0
- L2=29
- L3=26
- L4=68
- L5=25
- L6=2

After A-026.8-RUNTIME:
- L0=0
- L1=0
- L2=29-N
- L3=26+N
- L4=68
- L5=25
- L6=2
- total=150
- maturity_arithmetic_check=PASS

If N=8:
- L2=21
- L3=34

Spec boundary:
- no metrics movement in A-026.8-SPEC

### Anti-Inflation Boundaries (A-026.8-SPEC)

- no runtime code changes
- no test implementation changes
- no API or router additions
- no frontend additions
- no DB mutations/migrations
- no KPI/Brain/autonomy claims
- no maturity-level changes in this spec phase

### Definition of Done (A-026.8-SPEC)

- 29-module L2 inventory extracted and verified
- bounded 6-8 module selection completed (selected N=8)
- deterministic L3 standard defined
- deep module-by-module runtime specifications defined
- expected runtime files and targeted test plan defined
- expected post-runtime formula documented
- SBS tracker and normalization spec sections updated
- standalone A-026.8 spec report created

---

## A-026.8-RUNTIME — L2→L3 Deterministic Service Logic Implementation

**Status**: COMPLETE (runtime implemented and validated)

### Runtime Scope

- implemented deterministic L3 service logic functions in 8 selected modules only
- preserved existing L2 foundation contracts and tenant fail-closed guards
- no router/API/schema/frontend/DB migration/event/KPI/Brain/provider/autonomy behavior added

### Selected Runtime Modules

- digital_certificates
- records_hub
- student_success_analytics
- publication_registry
- research_projects
- lms_assessment_center
- lab_operations
- internship_marketplace

### Runtime Validation Evidence

- targeted Docker pytest: PASS (backend/tests/test_a0268_l2_to_l3_deterministic_service_logic.py, 88 passed, 1 warning)
- continuity Docker pytest: PASS (A-026.3 through A-026.8 suite, 482 passed, 1 warning)
- scope and anti-inflation checks: PASS (git diff --check clean; runtime service files free of API/router/provider tokens)

### Maturity Movement (Authoritative)

- before: L0=0, L1=0, L2=29, L3=26, L4=68, L5=25, L6=2
- after: L0=0, L1=0, L2=21, L3=34, L4=68, L5=25, L6=2
- arithmetic check: PASS (0+0+21+34+68+25+2=150)
- extension metrics: unchanged (25), separation remains PASS

### Next Action

- A-026.9-SPEC

---

## A-026.6-SPEC - L4→L5 Evidence / Governance / KPI / Brain-Readiness Batch Specification

**Status**: SPEC ONLY (historical; A-026.6-RUNTIME completed)

**Purpose**: select a bounded current-L4 batch for future A-026.6-RUNTIME and define auditable L5-readiness contracts without runtime execution claims, autonomous actions, or fake Brain/KPI inflation.

### Source-of-Truth Snapshot

- Authoritative tracker: SBS_UB.md
- Reconciled matrix: SBS_UB_150_MODULE_NORMALIZATION.md
- Current baseline metrics: L0=0, L1=16, L2=13, L3=26, L4=72, L5=21, L6=2, total=150, arithmetic_check=PASS
- Extension metrics: extension_total_count=25, total_tracked_modules=175, separation=PASS
- Last completed action in tracker before this spec: A-026.5-RUNTIME
- Next action in tracker after this spec: A-026.6-RUNTIME
- Runtime implementation status for A-026.6: not started

### L4 Extraction Summary

Current L4 modules were extracted from the full baseline matrix after A-026.5-RUNTIME.

- expected L4 count: 72
- found L4 count: 72
- status: PASS
- full L4 inventory table is documented in: A-026.6-SPEC-L4_TO_L5_EVIDENCE_GOVERNANCE_READINESS_BATCH_SPECIFICATION_REPORT.md

### L4→L5-Readiness Suitability Scoring

Scoring criteria per module:
1. evidence lineage clarity
2. governance decision value
3. KPI mapping value
4. human-review boundary clarity
5. auditability
6. testability
7. blast radius

Scoring scale: 1 (low), 3 (medium), 5 (high).

Recommendation values:
- SELECT_A0266
- DEFER_A0267
- DEFER_AFTER_EVIDENCE_INDEX
- DO_NOT_TOUCH_NOW

Full 72-module scoring table is documented in the A-026.6 spec report.

### Selected A-026.6 Batch

Selected batch size: 4.

| Selected Module | Current Level | Target Level | Why Selected | Expected L5-Readiness Contract | Required Tests | Risk |
|---|---:|---:|---|---|---|---|
| human_approved_timetable_workflow | L4 | L5-readiness | strongest governance and human-approval semantics with recent A-026.5 visibility coverage | evidence lineage + governance mapping + KPI-readiness boundary + Brain boundary envelope | evidence/governance/KPI/Brain-boundary/tenant tests | medium |
| timetable_approval_queue | L4 | L5-readiness | explicit human-review queue with clear escalation and audit semantics | decision-support mapping with strict human-review gate and deterministic audit notes | queue governance + tenant isolation + anti-autonomy tests | medium |
| timetable_change_kpi_dashboard | L4 | L5-readiness | highest KPI/evidence-readiness leverage while preserving anti-fake-KPI boundary | KPI-readiness classification and evidence completeness mapping only | no-fake-KPI + evidence lineage + boundary tests | medium |
| workload_management | L4 | L5-readiness | strong planning-governance value and deterministic readiness semantics | governance-ready readiness contract with no assignment automation | governance mapping + no-mutation + tenant/audit tests | medium |

Deferred from A-026.6 first slice:
- notification_center (provider/send overclaim risk; defer until evidence index hardening)
- timetable_change_proposal (defer until proposal evidence lineage index is tightened)

## A-026.6 L5-Readiness Standard

For each selected module, L5-readiness requires:

1. Evidence lineage contract
- explicit evidence source references
- operational visibility source linkage
- deterministic evidence notes
- no fake data
- no unverifiable KPI values

2. Governance mapping
- decision-support category
- human-review owner
- escalation boundary
- allowed governance actions
- forbidden autonomous actions

3. KPI-readiness mapping
- KPI category or readiness status
- evidence completeness status
- confidence/rationale notes
- no fake KPI computation
- no KPI lineage claim unless explicitly implemented

4. Brain-readiness boundary
- signal_candidate_allowed only when deterministic and bounded
- no Brain execution
- no autonomous recommendation execution
- no L6 claim

5. Tenant/audit/security
- tenant-scoped evidence outputs
- no cross-tenant leakage
- permission-aware access design
- audit/evidence note fields
- fail-closed behavior

6. Tests
- evidence contract tests
- governance mapping tests
- KPI-readiness boundary tests
- Brain boundary tests
- tenant/audit/security tests
- anti-inflation tests

### Module: human_approved_timetable_workflow

#### Current State
- Current Level: L4
- Target Level: L5-readiness
- Source: A-026.5-RUNTIME
- Existing L4 evidence: tenant-safe read-only visibility route and targeted security tests
- Primary gap: evidence lineage and governance contract are not yet formalized

#### Intended L5-Readiness Scope
- What this module will map: workflow evidence lineage, governance decision support, escalation readiness
- What this module will NOT map: autonomous approval, Brain execution, L6 gate claims
- Human-review boundary: mandatory (human_review_required=true)
- KPI/evidence boundary: readiness/evidence classification only, no fabricated KPI values
- Brain boundary: signal candidate envelope only, execution forbidden

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/human_approved_timetable_workflow/service.py | augment | expose deterministic L5-readiness evidence/governance summary wrapper |
| backend/app/modules/human_approved_timetable_workflow/schemas.py | augment | add L5-readiness contract fields |
| backend/tests/test_a0266_l4_to_l5_evidence_governance_readiness.py | add | module L5-readiness contract validation |

#### L5-Readiness Contract Fields
- tenant_id
- module
- readiness_level="L5_READY"
- evidence_lineage_status
- governance_mapping_status
- kpi_readiness_status
- brain_readiness_boundary
- human_review_required=true
- confidence_status
- rationale_notes
- allowed_governance_actions
- forbidden_autonomous_actions
- no_autonomous_execution=true
- no_l6_claim=true
- tenant_scoped=true

#### Governance Mapping
- governance category: timetable_workflow_governance
- human review role: timetable_admin_reviewer
- escalation boundary: policy_violation_or_high_risk_workflow_only
- allowed actions: review, approve_for_manual_apply, reject, request_revision
- forbidden actions: auto_approve, auto_apply, cross_tenant_override
- audit note: deterministic governance decision note with tenant and actor scope

#### KPI / Evidence Mapping
- KPI category: workflow_evidence_readiness
- evidence source: workflow operational visibility summary + approval boundary state
- completeness: PARTIAL_UNTIL_INDEXED
- confidence: medium
- no fake KPI guarantee: enforced

#### Brain Boundary
- Brain signal candidate: YES (candidate envelope only)
- execution: forbidden
- no autonomous execution: required
- no L6 claim: required

#### Tests
| Test | Purpose |
|---|---|
| evidence lineage contract test | validate deterministic evidence_source and evidence_lineage_status |
| governance mapping test | validate allowed/forbidden governance actions and escalation boundary |
| KPI-readiness boundary test | validate no fabricated KPI values |
| Brain/no-autonomy boundary test | validate candidate-only and no execution fields |
| tenant-scoped output test | validate tenant isolation and fail-closed behavior |
| anti-inflation test | validate no_l6_claim and no_autonomous_execution fields |

### Module: timetable_approval_queue

#### Current State
- Current Level: L4
- Target Level: L5-readiness
- Source: A-026.5-RUNTIME
- Existing L4 evidence: tenant-safe queue visibility summary and read-only enforcement
- Primary gap: explicit governance lineage and human-escalation contract

#### Intended L5-Readiness Scope
- What this module will map: review queue governance mapping and audit-ready evidence notes
- What this module will NOT map: automated queue execution or autonomous approval
- Human-review boundary: mandatory reviewer decision boundary
- KPI/evidence boundary: queue evidence completeness only
- Brain boundary: no execution, candidate envelope optional only

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/timetable_approval_queue/service.py | augment | L5-readiness governance/evidence summary mapping |
| backend/app/modules/timetable_approval_queue/schemas.py | augment | extended readiness fields for governance and audit notes |
| backend/tests/test_a0266_l4_to_l5_evidence_governance_readiness.py | add | queue governance and anti-autonomy coverage |

#### L5-Readiness Contract Fields
- tenant_id
- module
- readiness_level="L5_READY"
- evidence_lineage_status
- governance_mapping_status
- kpi_readiness_status
- brain_readiness_boundary
- human_review_required=true
- confidence_status
- rationale_notes
- allowed_governance_actions
- forbidden_autonomous_actions
- no_autonomous_execution=true
- no_l6_claim=true
- tenant_scoped=true

#### Governance Mapping
- governance category: timetable_review_queue_governance
- human review role: queue_reviewer
- escalation boundary: unresolved_conflict_or_policy_breach
- allowed actions: enqueue, review, approve_for_manual_apply, reject, escalate
- forbidden actions: silent_approve, auto_apply, bypass_review
- audit note: queue review decision with deterministic status rationale

#### KPI / Evidence Mapping
- KPI category: queue_decision_readiness
- evidence source: queue visibility summary, review state, decision boundary markers
- completeness: PARTIAL_UNTIL_INDEXED
- confidence: medium
- no fake KPI guarantee: enforced

#### Brain Boundary
- Brain signal candidate: NO
- no autonomous execution: required
- no L6 claim: required

#### Tests
| Test | Purpose |
|---|---|
| evidence lineage contract test | validate evidence lineage and audit_note determinism |
| governance mapping test | validate escalation and action boundaries |
| KPI-readiness boundary test | validate readiness-only semantics |
| Brain/no-autonomy boundary test | validate no execution signal path |
| tenant-scoped output test | validate fail-closed tenant behavior |
| anti-inflation test | validate no_l6_claim and no_autonomous_execution |

### Module: timetable_change_kpi_dashboard

#### Current State
- Current Level: L4
- Target Level: L5-readiness
- Source: A-026.5-RUNTIME
- Existing L4 evidence: deterministic KPI-readiness visibility endpoint with anti-fake safeguards
- Primary gap: formal evidence lineage and governance-ready rationale envelope

#### Intended L5-Readiness Scope
- What this module will map: KPI-readiness-to-evidence mapping and governance rationale notes
- What this module will NOT map: KPI lineage claims without implementation, Brain execution, L6 gate readiness
- Human-review boundary: mandatory for governance decision usage
- KPI/evidence boundary: readiness and completeness only; no fake KPI computation
- Brain boundary: candidate envelope only if deterministic; execution prohibited

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/timetable_change_kpi_dashboard/service.py | augment | deterministic L5-readiness KPI/evidence mapping contract |
| backend/app/modules/timetable_change_kpi_dashboard/schemas.py | augment | readiness contract fields and audit rationale |
| backend/tests/test_a0266_l4_to_l5_evidence_governance_readiness.py | add | KPI boundary and governance evidence tests |

#### L5-Readiness Contract Fields
- tenant_id
- module
- readiness_level="L5_READY"
- evidence_lineage_status
- governance_mapping_status
- kpi_readiness_status
- brain_readiness_boundary
- human_review_required=true
- confidence_status
- rationale_notes
- allowed_governance_actions
- forbidden_autonomous_actions
- no_autonomous_execution=true
- no_l6_claim=true
- tenant_scoped=true

#### Governance Mapping
- governance category: timetable_kpi_governance_readiness
- human review role: timetable_analytics_reviewer
- escalation boundary: low_evidence_confidence_or_policy_alert
- allowed actions: review, annotate, escalate, defer
- forbidden actions: fabricate_kpi, auto_decide, autonomous_apply
- audit note: deterministic evidence completeness rationale

#### KPI / Evidence Mapping
- KPI category: timetable_change_readiness_kpi
- evidence source: operational summary, readiness classifiers, safety flags
- completeness: PARTIAL_OR_READY (deterministic)
- confidence: medium_high
- no fake KPI guarantee: enforced

#### Brain Boundary
- Brain signal candidate: YES (candidate only)
- execution: forbidden
- no autonomous execution: required
- no L6 claim: required

#### Tests
| Test | Purpose |
|---|---|
| evidence lineage contract test | validate deterministic lineage markers |
| governance mapping test | validate allowed governance actions and escalation |
| KPI-readiness boundary test | validate no fabricated KPI values or lineage overclaim |
| Brain/no-autonomy boundary test | validate candidate-only and no execution |
| tenant-scoped output test | validate tenant isolation and fail-closed behavior |
| anti-inflation test | validate no_l6_claim and no_autonomous_execution |

### Module: workload_management

#### Current State
- Current Level: L4
- Target Level: L5-readiness
- Source: A-026.5-RUNTIME
- Existing L4 evidence: deterministic workload readiness/constraints visibility route
- Primary gap: explicit governance-evidence contract for executive decision support

#### Intended L5-Readiness Scope
- What this module will map: workload governance-ready evidence envelope and human-review escalation boundaries
- What this module will NOT map: auto-assignment, payroll mutation, autonomous workload execution
- Human-review boundary: mandatory
- KPI/evidence boundary: readiness confidence only
- Brain boundary: candidate envelope optional only, execution disallowed

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/workload_management/service.py | augment | L5-readiness evidence/governance wrapper |
| backend/app/modules/workload_management/schemas.py | augment | workload governance-readiness contract extension |
| backend/tests/test_a0266_l4_to_l5_evidence_governance_readiness.py | add | workload L5-readiness boundary tests |

#### L5-Readiness Contract Fields
- tenant_id
- module
- readiness_level="L5_READY"
- evidence_lineage_status
- governance_mapping_status
- kpi_readiness_status
- brain_readiness_boundary
- human_review_required=true
- confidence_status
- rationale_notes
- allowed_governance_actions
- forbidden_autonomous_actions
- no_autonomous_execution=true
- no_l6_claim=true
- tenant_scoped=true

#### Governance Mapping
- governance category: workload_planning_governance
- human review role: workload_planning_reviewer
- escalation boundary: high_risk_workload_or_policy_conflict
- allowed actions: assess, classify, recommend_manual_adjustment, escalate
- forbidden actions: auto_assign, auto_override_constraints, payroll_mutation
- audit note: deterministic planning evidence rationale with tenant scope

#### KPI / Evidence Mapping
- KPI category: workload_readiness_evidence
- evidence source: workload readiness and constraint summary
- completeness: PARTIAL_UNTIL_INDEXED
- confidence: medium
- no fake KPI guarantee: enforced

#### Brain Boundary
- Brain signal candidate: YES (candidate only)
- execution: forbidden
- no autonomous execution: required
- no L6 claim: required

#### Tests
| Test | Purpose |
|---|---|
| evidence lineage contract test | validate source and evidence status determinism |
| governance mapping test | validate review/escalation boundaries |
| KPI-readiness boundary test | validate no fabricated KPI values |
| Brain/no-autonomy boundary test | validate candidate-only boundary |
| tenant-scoped output test | validate tenant isolation and fail-closed handling |
| anti-inflation test | validate no_l6_claim and no_autonomous_execution |

### Expected A-026.6 Runtime Files

| File | Expected Action | Reason |
|---|---|---|
| backend/app/modules/human_approved_timetable_workflow/service.py | augment | add L5-readiness evidence/governance wrapper fields |
| backend/app/modules/human_approved_timetable_workflow/schemas.py | augment | extend visibility schema with readiness contract fields |
| backend/app/modules/timetable_approval_queue/service.py | augment | add queue governance-readiness mapping |
| backend/app/modules/timetable_approval_queue/schemas.py | augment | extend queue schema for readiness contract |
| backend/app/modules/timetable_change_kpi_dashboard/service.py | augment | add deterministic KPI/evidence readiness mapping envelope |
| backend/app/modules/timetable_change_kpi_dashboard/schemas.py | augment | extend KPI schema for governance/evidence fields |
| backend/app/modules/workload_management/service.py | augment | add workload governance-readiness mapping |
| backend/app/modules/workload_management/schemas.py | augment | extend workload schema for readiness contract |
| backend/tests/test_a0266_l4_to_l5_evidence_governance_readiness.py | add | targeted L5-readiness contract and anti-inflation suite |
| SBS_UB.md | update in runtime | reconcile runtime result and next action |
| SBS_UB_150_MODULE_NORMALIZATION.md | update in runtime | selected rows move L4→L5 after validation |
| A-026.6-RUNTIME-L4_TO_L5_EVIDENCE_GOVERNANCE_READINESS_REPORT.md | add in runtime | runtime evidence report |

## A-026.6 Targeted Test Plan

Preferred test file:
- backend/tests/test_a0266_l4_to_l5_evidence_governance_readiness.py

Test groups:
1. evidence lineage contract validation
2. governance mapping validation
3. human-review boundary validation
4. KPI-readiness boundary validation
5. Brain boundary and no-autonomous-execution validation
6. tenant-scoped evidence validation
7. audit/evidence note validation
8. anti-inflation validation

Expected backend test count:
- minimum: 18
- preferred: 25-40 for selected 4-module batch

Validation mode for runtime:
- USE_FAST_DOCKER_RUN_MODE
- compose path remains slow but functional and optional for parity sanity

### Expected Maturity Movement

No maturity movement occurs in this spec action.

If A-026.6-RUNTIME succeeds for selected batch size N:
- L0=0
- L1=16
- L2=13
- L3=26
- L4=72-N
- L5=21+N
- L6=2
- total=150
- maturity_arithmetic_check=PASS

If N=3:
- L4=69
- L5=24

If N=4:
- L4=68
- L5=25

### Security / SaaS Boundaries

- tenant isolation is mandatory for every readiness contract
- fail-closed tenant handling is mandatory; no default tenant fallback
- permission-aware access design is mandatory for operational surfaces
- no cross-tenant leakage is allowed in evidence payloads or governance notes
- auditability and evidence traceability are mandatory
- human approval boundary is mandatory
- no unsafe automation and no unguarded provider call paths

### Anti-Inflation Boundaries

- no runtime code changes in this spec action
- no maturity movement in this spec action
- no fake KPI values
- no fake Brain execution claims
- no autonomous action
- no L6 claim

### Definition of Done for Future A-026.6-RUNTIME

- selected batch remains exactly 4 modules unless re-approved
- each selected module produces deterministic L5-readiness contract fields
- evidence lineage, governance mapping, KPI-readiness boundary, and Brain boundary tests pass
- no autonomous execution path is introduced
- no fake KPI or fake Brain claims are introduced
- tenant isolation and fail-closed behavior are preserved
- SBS_UB.md and matrix updates happen only after runtime validation succeeds
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
| Bucket A - L0/L1 Foundation Normalization | L0-L1 | 0 | foundation and contract gaps | L2-ready foundations completed for baseline | A-026.7.L1L2-RUNTIME |
| Bucket B - L2 Service Contract Normalization | L2 | 21 | deterministic service logic gaps | L3 deterministic backend slices | A-026.9-SPEC |
| Bucket C - L3 Operational Visibility Normalization | L3 | 34 | API/visibility/test depth gaps | L4 operational readiness | A-026.5 |
| Bucket D - L4 Brain/Evidence Readiness | L4 | 68 | KPI/evidence/Brain mapping gaps | selective L5-readiness candidates | A-026.6 |
| Bucket E - L5 E2E/Gate Closure | L5 | 25 | gate continuity and E2E closure | selective L6 proofs | A-026.7 |
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

## Full Baseline 150 Module Normalization Matrix

| # | Module | Domain | Current Level | Bucket | Verified Level Source | Capability Verification Status | Primary Gap | Target Next Level | Required Work | Required Tests | Risk | Priority | A-026.x Action |
|---:|---|---|---:|---|---|---|---|---:|---|---|---|---|---|
| 1 | academic_integrity | Administration & Governance | L5 | E | A-023.0 | EVIDENCED_LEVEL_ONLY | E2E_gate_missing | L6 | E2E path and gate evidence | gate continuity | high | medium | A-026.7 |
| 2 | academic_records | Core Academic | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | KPI lineage mapping | lineage contract | medium | medium | A-026.6 |
| 3 | access_control | Identity/Access/Security | L5 | E | A-023.0 | EVIDENCED_LEVEL_ONLY | E2E_gate_missing | L6 | E2E and gate evidence | gate continuity | high | high | A-026.7 |
| 4 | accreditation | Administration & Governance | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | KPI evidence lineage | lineage mapping | medium | low | A-026.6 |
| 5 | accreditation_compliance | Planned Expansion | L2 | B | A-023.0 | EVIDENCED_LEVEL_ONLY | FSM_workflow_missing | L3 | deterministic service logic | targeted tests | medium | high | A-026.4 |
| 6 | admin | Administration & Governance | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | API_missing | L5 | verify admin API scope | route tests | medium | low | A-026.5 |
| 7 | admissions | Administration & Governance | L5 | E | A-023.0 | EVIDENCED_LEVEL_ONLY | E2E_gate_missing | L6 | E2E for admissions workflows | gate continuity | high | high | A-026.7 |
| 8 | advising | Student & Campus Life | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | frontend_missing | L5 | verify advising dashboard UX | frontend tests | medium | medium | A-026.5 |
| 9 | ai_admissions_scoring | Research & Innovation | L3 | C | A-023.0 | EVIDENCED_LEVEL_ONLY | API_missing | L4 | expose scoring API readiness | route tests | medium | high | A-026.5 |
| 10 | ai_copilot_ops | Planned Expansion | L3 | C | A-024.2 | EVIDENCED_L3_AFTER_A0242 | operational_visibility_or_API_depth_needed | L4 | operational visibility / API readiness specification | route or visibility contract tests | medium | high | A-026.5 |
| 11 | ai_cost_governance | Planned Expansion | L2 | B | A-023.0 | EVIDENCED_LEVEL_ONLY | service_contract_missing | L3 | cost service determinism | contract tests | medium | high | A-026.4 |
| 12 | ai_gateway | Integrations & Platform | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | Brain_mapping_missing | L5 | Brain signal gateway mapping | mapping tests | medium | high | A-026.6 |
| 13 | ai_guardrails | AI/Knowledge/Reasoning | L3 | C | A-023.0 | EVIDENCED_LEVEL_ONLY | API_missing | L4 | guardrails control API | route tests | medium | high | A-026.5 |
| 14 | ai_plagiarism | Research & Innovation | L2 | B | A-023.0 | EVIDENCED_LEVEL_ONLY | FSM_workflow_missing | L3 | plagiarism detection FSM | transition tests | medium | high | A-026.4 |
| 15 | ai_routing_control | Planned Expansion | L3 | C | A-024.1 | EVIDENCED_L3_AFTER_A0241 | operational_visibility_or_API_depth_needed | L4 | operational visibility / routing control surface readiness | route or visibility contract tests | medium | high | A-026.5 |
| 16 | alumni | Administration & Governance | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | alumni metrics lineage | lineage mapping | medium | low | A-026.6 |
| 17 | alumni_donation_portal | Administration & Governance | L3 | C | A-023.0 | EVIDENCED_LEVEL_ONLY | API_missing | L4 | donation API visibility | route tests | medium | medium | A-026.5 |
| 18 | alumni_relations_ops | Planned Expansion | L3 | C | A-026.9-RUNTIME | EVIDENCED_L3_AFTER_A0269 | operational_visibility_or_API_depth_needed | L4 | operational visibility/API readiness specification | route/visibility/security contract tests | medium | high | A-026.10-SPEC |
| 19 | analytics | Integrations & Platform | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | Brain_mapping_missing | L5 | analytics brain mapping | mapping tests | medium | medium | A-026.6 |
| 20 | asset_inventory | Finance & Billing | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | asset KPI lineage | lineage mapping | medium | medium | A-026.6 |
| 21 | attendance | Student & Campus Life | L4 | D | A-024.4 | EVIDENCED_L4_AFTER_A0244 | KPI_evidence_or_Brain_mapping_missing | L5-readiness | attendance KPI/evidence lineage and governance mapping | lineage/mapping contract tests | medium | high | A-026.6 |
| 22 | audit | Administration & Governance | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | audit trail evidence mapping | lineage mapping | medium | high | A-026.6 |
| 23 | auth | Identity/Access/Security | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | Brain_mapping_missing | L5 | auth event mapping | mapping tests | medium | high | A-026.6 |
| 24 | backup | Integrations & Platform | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | verification_pending | L5 | verify backup determinism | deterministic unit tests | medium | low | A-026.5 |
| 25 | billing | Finance & Billing | L6 | F | A-023.0 | EVIDENCED_LEVEL_ONLY | preserve_only | L6 | preserve gate continuity | regression tests | medium | high | A-026.7 |
| 26 | blockchain_diploma | Administration & Governance | L3 | C | A-023.0 | EVIDENCED_LEVEL_ONLY | API_missing | L4 | diploma verification API | route tests | medium | medium | A-026.5 |
| 27 | brain_core | AI/Knowledge/Reasoning | L5 | E | A-023.0 | EVIDENCED_LEVEL_ONLY | E2E_gate_missing | L6 | brain E2E and gates | gate continuity | high | high | A-026.7 |
| 28 | budget_planning | Finance & Billing | L5 | E | A-023.0 | EVIDENCED_LEVEL_ONLY | E2E_gate_missing | L6 | budget planning E2E gates | gate continuity | high | high | A-026.7 |
| 29 | campus_sla | Administration & Governance | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | SLA KPI lineage | lineage mapping | medium | low | A-026.6 |
| 30 | career_services | Student & Campus Life | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | career outcomes mapping | lineage mapping | medium | medium | A-026.6 |
| 31 | communications | Integrations & Platform | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | Brain_mapping_missing | L5 | comms event mapping | mapping tests | medium | low | A-026.6 |
| 32 | conference_management | Research & Innovation | L2 | B | A-023.0 | EVIDENCED_LEVEL_ONLY | FSM_workflow_missing | L3 | conference FSM transitions | transition tests | medium | low | A-026.4 |
| 33 | contracts_hr | Finance & Billing | L3 | C | A-023.0 | EVIDENCED_LEVEL_ONLY | API_missing | L4 | HR contract API | route tests | medium | low | A-026.5 |
| 34 | contracts_legal_repository | Planned Expansion | L2 | B | A-023.0 | EVIDENCED_LEVEL_ONLY | service_contract_missing | L3 | legal contract service | contract tests | medium | high | A-026.4 |
| 35 | counseling | Student & Campus Life | L3 | C | A-023.0 | EVIDENCED_LEVEL_ONLY | API_missing | L4 | counseling API visibility | route tests | medium | high | A-026.5 |
| 36 | counseling_case_management | Planned Expansion | L2 | B | A-023.0 | EVIDENCED_LEVEL_ONLY | service_contract_missing | L3 | case management service | contract tests | medium | high | A-026.4 |
| 37 | courses | Core Academic | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | course KPI mapping | lineage mapping | medium | high | A-026.6 |
| 38 | currency_localization | Finance & Billing | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | Brain_mapping_missing | L5 | currency signal mapping | mapping tests | medium | low | A-026.6 |
| 39 | degree_progress | Core Academic | L5 | E | A-023.0 | EVIDENCED_LEVEL_ONLY | E2E_gate_missing | L6 | degree E2E and gates | gate continuity | high | high | A-026.7 |
| 40 | delinquency_collections | Finance & Billing | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | delinquency KPI lineage | lineage mapping | medium | high | A-026.6 |
| 41 | developer_portal | Planned Expansion | L2 | B | A-023.0 | EVIDENCED_LEVEL_ONLY | service_contract_missing | L3 | developer service contract | contract tests | medium | low | A-026.4 |
| 42 | digital_certificates | Planned Expansion | L3 | C | A-026.8-RUNTIME | EVIDENCED_L3_AFTER_A0268 | operational_visibility_or_API_depth_needed | L4 | operational visibility/API readiness specification | route/visibility/security contract tests | medium | high | A-026.9 |
| 43 | digital_documents | Administration & Governance | L3 | C | A-023.0 | EVIDENCED_LEVEL_ONLY | API_missing | L4 | document API visibility | route tests | medium | low | A-026.5 |
| 44 | dining | Student & Campus Life | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | dining KPI mapping | lineage mapping | medium | low | A-026.6 |
| 45 | donations_fundraising | Planned Expansion | L3 | C | A-026.9-RUNTIME | EVIDENCED_L3_AFTER_A0269 | operational_visibility_or_API_depth_needed | L4 | operational visibility/API readiness specification | route/visibility/security contract tests | medium | high | A-026.10-SPEC |
| 46 | enrollments | Core Academic | L5 | E | A-023.0 | EVIDENCED_LEVEL_ONLY | E2E_gate_missing | L6 | enrollment E2E and gates | gate continuity | high | high | A-026.7 |
| 47 | equipment_booking | Research & Innovation | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | Brain_mapping_missing | L5 | equipment utilization signal | mapping tests | medium | medium | A-026.6 |
| 48 | event_registration_portal | Planned Expansion | L3 | C | A-026.9-RUNTIME | EVIDENCED_L3_AFTER_A0269 | operational_visibility_or_API_depth_needed | L4 | operational visibility/API readiness specification | route/visibility/security contract tests | medium | high | A-026.10-SPEC |
| 49 | events_management | Student & Campus Life | L5 | E | A-023.0 | EVIDENCED_LEVEL_ONLY | E2E_gate_missing | L6 | events E2E and gates | gate continuity | high | high | A-026.7 |
| 50 | exam_governance | Core Academic | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | exam metrics mapping | lineage mapping | medium | high | A-026.6 |
| 51 | exam_integrity_analytics | Planned Expansion | L3 | C | A-026.9-RUNTIME | EVIDENCED_L3_AFTER_A0269 | operational_visibility_or_API_depth_needed | L4 | operational visibility/API readiness specification | route/visibility/security contract tests | medium | high | A-026.10-SPEC |
| 52 | exam_proctoring | Workflow & Process Automation | L5 | E | A-023.0 | EVIDENCED_LEVEL_ONLY | E2E_gate_missing | L6 | proctoring E2E and gates | gate continuity | high | high | A-026.7 |
| 53 | expense_controls | Finance & Billing | L5 | E | A-023.0 | EVIDENCED_LEVEL_ONLY | E2E_gate_missing | L6 | expense E2E and gates | gate continuity | high | high | A-026.7 |
| 54 | facilities_work_orders | Workflow & Process Automation | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | work order KPI mapping | lineage mapping | medium | medium | A-026.6 |
| 55 | faculty | Administration & Governance | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | Brain_mapping_missing | L5 | faculty workload signal | mapping tests | medium | high | A-026.6 |
| 56 | faculty_copilot | Research & Innovation | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | Brain_mapping_missing | L5 | copilot research signal | mapping tests | medium | high | A-026.6 |
| 57 | faculty_performance_kpis | Administration & Governance | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | performance KPI lineage | lineage mapping | medium | high | A-026.6 |
| 58 | feature_flags | Administration & Governance | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | verification_pending | L5 | verify feature flag scope | contract tests | medium | low | A-026.5 |
| 59 | federation_management | Planned Expansion | L2 | B | A-023.0 | EVIDENCED_LEVEL_ONLY | FSM_workflow_missing | L3 | federation FSM logic | transition tests | medium | low | A-026.4 |
| 60 | financial_aid | Finance & Billing | L5 | E | A-023.0 | EVIDENCED_LEVEL_ONLY | E2E_gate_missing | L6 | aid E2E and gates | gate continuity | high | high | A-026.7 |
| 61 | grades | Core Academic | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | grading KPI lineage | lineage mapping | medium | high | A-026.6 |
| 62 | health_services | Planned Expansion | L2 | B | A-023.0 | EVIDENCED_LEVEL_ONLY | FSM_workflow_missing | L3 | health service logic | transition tests | medium | low | A-026.4 |
| 63 | help | Administration & Governance | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | verification_pending | L5 | verify help desk scope | contract tests | medium | low | A-026.5 |
| 64 | housing | Student & Campus Life | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | housing KPI mapping | lineage mapping | medium | medium | A-026.6 |
| 65 | hr_payroll | Finance & Billing | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | payroll KPI lineage | lineage mapping | medium | high | A-026.6 |
| 66 | human_approved_timetable_workflow | Planned Expansion | L5 | E | A-026.6-RUNTIME | EVIDENCED_L5_READY_AFTER_A0266 | autonomous_execution_and_closed_loop_validation_missing | L6-readiness | controlled human-approved closed-loop governance / autonomous boundary validation | closed-loop safety / no-autonomy-breakout / human approval tests | medium | high | A-026.7 |
| 67 | i18n | Integrations & Platform | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | verification_pending | L5 | verify i18n contract completeness | contract tests | medium | low | A-026.5 |
| 68 | identity | Identity/Access/Security | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | Brain_mapping_missing | L5 | identity event mapping | mapping tests | medium | high | A-026.6 |
| 69 | integrations | Integrations & Platform | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | verification_pending | L5 | verify integration breadth | contract tests | medium | low | A-026.5 |
| 70 | internship | Student & Campus Life | L3 | C | A-023.0 | EVIDENCED_LEVEL_ONLY | API_missing | L4 | internship API visibility | route tests | medium | medium | A-026.5 |
| 71 | internship_marketplace | Planned Expansion | L3 | C | A-026.8-RUNTIME | EVIDENCED_L3_AFTER_A0268 | operational_visibility_or_API_depth_needed | L4 | operational visibility/API readiness specification | route/visibility/security contract tests | medium | high | A-026.9 |
| 72 | interventions | Administration & Governance | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | Brain_mapping_missing | L5 | intervention signal mapping | mapping tests | medium | high | A-026.6 |
| 73 | invoices | Finance & Billing | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | invoice KPI lineage | lineage mapping | medium | high | A-026.6 |
| 74 | ip_management | Research & Innovation | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | Brain_mapping_missing | L5 | IP portfolio signal | mapping tests | medium | medium | A-026.6 |
| 75 | jobs | Integrations & Platform | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | verification_pending | L5 | verify job board scope | contract tests | medium | low | A-026.5 |
| 76 | knowledge_retrieval | Research & Innovation | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | Brain_mapping_missing | L5 | retrieval signal mapping | mapping tests | medium | high | A-026.6 |
| 77 | lab_operations | Planned Expansion | L3 | C | A-026.8-RUNTIME | EVIDENCED_L3_AFTER_A0268 | operational_visibility_or_API_depth_needed | L4 | operational visibility/API readiness specification | route/visibility/security contract tests | medium | high | A-026.9 |
| 78 | ldap | Identity/Access/Security | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | verification_pending | L5 | verify LDAP integration scope | contract tests | medium | medium | A-026.5 |
| 79 | library | Student & Campus Life | L3 | C | A-023.0 | EVIDENCED_LEVEL_ONLY | API_missing | L4 | library API visibility | route tests | medium | medium | A-026.5 |
| 80 | library_circulation | Planned Expansion | L2 | B | A-023.0 | EVIDENCED_LEVEL_ONLY | FSM_workflow_missing | L3 | circulation FSM logic | transition tests | medium | high | A-026.4 |
| 81 | lms_assessment_center | Planned Expansion | L3 | C | A-026.8-RUNTIME | EVIDENCED_L3_AFTER_A0268 | operational_visibility_or_API_depth_needed | L4 | operational visibility/API readiness specification | route/visibility/security contract tests | medium | high | A-026.9 |
| 82 | lms_content | Administration & Governance | L3 | C | A-023.0 | EVIDENCED_LEVEL_ONLY | API_missing | L4 | content API visibility | route tests | medium | medium | A-026.5 |
| 83 | local_user_management | Planned Expansion | L2 | B | A-023.0 | EVIDENCED_LEVEL_ONLY | tenant_guard_missing | L3 | user management tenant guards | tenant tests | high | high | A-026.4 |
| 84 | mobile_app | Student & Campus Life | L3 | C | A-023.0 | EVIDENCED_LEVEL_ONLY | frontend_missing | L4 | mobile app frontend visibility | frontend tests | medium | medium | A-026.5 |
| 85 | mobile_push_gateway | Planned Expansion | L3 | C | A-026.9-RUNTIME | EVIDENCED_L3_AFTER_A0269 | operational_visibility_or_API_depth_needed | L4 | operational visibility/API readiness specification | route/visibility/security contract tests | medium | high | A-026.10-SPEC |
| 86 | model_evaluation | Research & Innovation | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | Brain_mapping_missing | L5 | model eval signal mapping | mapping tests | medium | high | A-026.6 |
| 87 | notification_center | Planned Expansion | L4 | D | A-026.5-RUNTIME | EVIDENCED_L4_AFTER_A0265_RUNTIME | KPI_evidence_or_Brain_mapping_missing | L5-readiness | KPI/evidence/Brain-readiness mapping | lineage/mapping contract tests | high | high | A-026.6 |
| 88 | observability | Integrations & Platform | L4 | D | A-024.3 | EVIDENCED_L4_AFTER_A0243 | KPI_evidence_or_Brain_mapping_missing | L5-readiness | KPI/evidence/Brain-readiness mapping | lineage/mapping contract tests | medium | high | A-026.6 |
| 89 | online_payments | Finance & Billing | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | payment KPI lineage | lineage mapping | medium | high | A-026.6 |
| 90 | operations | Administration & Governance | L5 | E | A-023.0 | EVIDENCED_LEVEL_ONLY | E2E_gate_missing | L6 | ops E2E and gates | gate continuity | high | high | A-026.7 |
| 91 | org_structure | Administration & Governance | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | org KPI mapping | lineage mapping | medium | low | A-026.6 |
| 92 | parent_engagement | Planned Expansion | L3 | C | A-026.9-RUNTIME | EVIDENCED_L3_AFTER_A0269 | operational_visibility_or_API_depth_needed | L4 | operational visibility/API readiness specification | route/visibility/security contract tests | medium | high | A-026.10-SPEC |
| 93 | parent_portal | Student & Campus Life | L3 | C | A-023.0 | EVIDENCED_LEVEL_ONLY | API_missing | L4 | parent portal API | route tests | medium | medium | A-026.5 |
| 94 | parking | Student & Campus Life | L3 | C | A-023.0 | EVIDENCED_LEVEL_ONLY | API_missing | L4 | parking API visibility | route tests | medium | low | A-026.5 |
| 95 | parking_enforcement | Planned Expansion | L3 | C | A-026.9-RUNTIME | EVIDENCED_L3_AFTER_A0269 | operational_visibility_or_API_depth_needed | L4 | operational visibility/API readiness specification | route/visibility/security contract tests | medium | high | A-026.10-SPEC |
| 96 | parking_permit_ops | Planned Expansion | L3 | C | A-026.9-RUNTIME | EVIDENCED_L3_AFTER_A0269 | operational_visibility_or_API_depth_needed | L4 | operational visibility/API readiness specification | route/visibility/security contract tests | medium | high | A-026.10-SPEC |
| 97 | patents | Research & Innovation | L3 | C | A-023.0 | EVIDENCED_LEVEL_ONLY | API_missing | L4 | patent API visibility | route tests | medium | low | A-026.5 |
| 98 | payment_reconciliation | Finance & Billing | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | reconciliation KPI mapping | lineage mapping | medium | high | A-026.6 |
| 99 | pdpl | Identity/Access/Security | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | verification_pending | L5 | verify PDPL contract completeness | contract tests | medium | medium | A-026.5 |
| 100 | plans | Administration & Governance | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | planning KPI mapping | lineage mapping | medium | low | A-026.6 |
| 101 | platform | Integrations & Platform | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | verification_pending | L5 | verify platform contract | contract tests | medium | low | A-026.5 |
| 102 | platform_health | Planned Expansion | L3 | C | A-024.1 | EVIDENCED_L3_AFTER_A0241 | operational_visibility_or_API_depth_needed | L4 | operational health visibility readiness | visibility contract tests | medium | low | A-026.5 |
| 103 | platform_shared | Integrations & Platform | L3 | C | A-023.0 | EVIDENCED_LEVEL_ONLY | API_missing | L4 | shared services API | route tests | medium | low | A-026.5 |
| 104 | procurement | Finance & Billing | L5 | E | A-023.0 | EVIDENCED_LEVEL_ONLY | E2E_gate_missing | L6 | procurement E2E and gates | gate continuity | high | high | A-026.7 |
| 105 | procurement_approval_workflow | Planned Expansion | L3 | C | A-024.2 | EVIDENCED_L3_AFTER_A0242 | operational_visibility_or_API_depth_needed | L4 | operational workflow visibility/API readiness | route or workflow visibility tests | medium | high | A-026.5 |
| 106 | profiles | Administration & Governance | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | Brain_mapping_missing | L5 | profile signal mapping | mapping tests | medium | low | A-026.6 |
| 107 | programs | Core Academic | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | program KPI mapping | lineage mapping | medium | high | A-026.6 |
| 108 | prompt_management | Research & Innovation | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | Brain_mapping_missing | L5 | prompt signal mapping | mapping tests | medium | high | A-026.6 |
| 109 | publication_registry | Planned Expansion | L3 | C | A-026.8-RUNTIME | EVIDENCED_L3_AFTER_A0268 | operational_visibility_or_API_depth_needed | L4 | operational visibility/API readiness specification | route/visibility/security contract tests | medium | high | A-026.9 |
| 110 | publications | Research & Innovation | L3 | C | A-023.0 | EVIDENCED_LEVEL_ONLY | API_missing | L4 | publications API visibility | route tests | medium | low | A-026.5 |
| 111 | quotas | Finance & Billing | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | quota KPI lineage | lineage mapping | medium | low | A-026.6 |
| 112 | rbac | Identity/Access/Security | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | Brain_mapping_missing | L5 | RBAC event mapping | mapping tests | medium | high | A-026.6 |
| 113 | records_hub | Planned Expansion | L3 | C | A-026.8-RUNTIME | EVIDENCED_L3_AFTER_A0268 | operational_visibility_or_API_depth_needed | L4 | operational visibility/API readiness specification | route/visibility/security contract tests | medium | high | A-026.9 |
| 114 | research | Research & Innovation | L5 | E | A-023.0 | EVIDENCED_LEVEL_ONLY | E2E_gate_missing | L6 | research E2E and gates | gate continuity | high | high | A-026.7 |
| 115 | research_ethics | Research & Innovation | L5 | E | A-023.0 | EVIDENCED_LEVEL_ONLY | E2E_gate_missing | L6 | ethics E2E and gates | gate continuity | high | high | A-026.7 |
| 116 | research_grants | Planned Expansion | L2 | B | A-023.0 | EVIDENCED_LEVEL_ONLY | FSM_workflow_missing | L3 | grants FSM logic | transition tests | medium | high | A-026.4 |
| 117 | research_projects | Planned Expansion | L3 | C | A-026.8-RUNTIME | EVIDENCED_L3_AFTER_A0268 | operational_visibility_or_API_depth_needed | L4 | operational visibility/API readiness specification | route/visibility/security contract tests | medium | high | A-026.9 |
| 118 | room_booking | Core Academic | L5 | E | A-023.0 | EVIDENCED_LEVEL_ONLY | E2E_gate_missing | L6 | room booking E2E gates | gate continuity | high | high | A-026.7 |
| 119 | scheduling | Core Academic | L6 | F | A-023.0 | EVIDENCED_LEVEL_ONLY | preserve_only | L6 | preserve gate continuity | regression tests | medium | high | A-026.7 |
| 120 | scholarship | Finance & Billing | L5 | E | A-023.0 | EVIDENCED_LEVEL_ONLY | E2E_gate_missing | L6 | scholarship E2E gates | gate continuity | high | high | A-026.7 |
| 121 | security | Identity/Access/Security | L5 | E | A-023.0 | EVIDENCED_LEVEL_ONLY | E2E_gate_missing | L6 | security E2E and gates | gate continuity | high | high | A-026.7 |
| 122 | security_operations | Identity/Access/Security | L5 | E | A-023.0 | EVIDENCED_LEVEL_ONLY | E2E_gate_missing | L6 | security ops E2E gates | gate continuity | high | high | A-026.7 |
| 123 | service_accounts | Administration & Governance | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | Brain_mapping_missing | L5 | account signal mapping | mapping tests | medium | low | A-026.6 |
| 124 | sso_saml | Identity/Access/Security | L3 | C | A-023.0 | EVIDENCED_LEVEL_ONLY | API_missing | L4 | SAML API visibility | route tests | medium | high | A-026.5 |
| 125 | student_ai_tutor | Research & Innovation | L2 | B | A-023.0 | EVIDENCED_LEVEL_ONLY | FSM_workflow_missing | L3 | tutor FSM logic | transition tests | medium | high | A-026.4 |
| 126 | student_feedback | Student & Campus Life | L3 | C | A-023.0 | EVIDENCED_LEVEL_ONLY | API_missing | L4 | feedback API visibility | route tests | medium | low | A-026.5 |
| 127 | student_id_card | Student & Campus Life | L3 | C | A-023.0 | EVIDENCED_LEVEL_ONLY | API_missing | L4 | ID card API visibility | route tests | medium | low | A-026.5 |
| 128 | student_life | Student & Campus Life | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | life KPI mapping | lineage mapping | medium | medium | A-026.6 |
| 129 | student_portal | Student & Campus Life | L4 | D | A-024.4 | EVIDENCED_L4_AFTER_A0244 | KPI_evidence_or_Brain_mapping_missing | L5-readiness | student portal evidence/governance mapping | lineage/mapping contract tests | medium | high | A-026.6 |
| 130 | student_services | Student & Campus Life | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | services KPI mapping | lineage mapping | medium | medium | A-026.6 |
| 131 | student_success_analytics | Planned Expansion | L3 | C | A-026.8-RUNTIME | EVIDENCED_L3_AFTER_A0268 | operational_visibility_or_API_depth_needed | L4 | operational visibility/API readiness specification | route/visibility/security contract tests | medium | high | A-026.9 |
| 132 | students | Student & Campus Life | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | student KPI mapping | lineage mapping | medium | high | A-026.6 |
| 133 | subscriptions | Finance & Billing | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | subscription KPI lineage | lineage mapping | medium | low | A-026.6 |
| 134 | syllabus_governance | Core Academic | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | Brain_mapping_missing | L5 | syllabus signal mapping | mapping tests | medium | high | A-026.6 |
| 135 | teaching_quality | Core Academic | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | Brain_mapping_missing | L5 | quality signal mapping | mapping tests | medium | high | A-026.6 |
| 136 | tenants | Identity/Access/Security | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | Brain_mapping_missing | L5 | tenant event mapping | mapping tests | medium | high | A-026.6 |
| 137 | thesis | Research & Innovation | L5 | E | A-023.0 | EVIDENCED_LEVEL_ONLY | E2E_gate_missing | L6 | thesis E2E and gates | gate continuity | high | high | A-026.7 |
| 138 | timetable_approval_queue | Planned Expansion | L5 | E | A-026.6-RUNTIME | EVIDENCED_L5_READY_AFTER_A0266 | autonomous_execution_and_closed_loop_validation_missing | L6-readiness | controlled human-approved closed-loop governance / autonomous boundary validation | closed-loop safety / no-autonomy-breakout / human approval tests | medium | high | A-026.7 |
| 139 | timetable_change_kpi_dashboard | Planned Expansion | L5 | E | A-026.6-RUNTIME | EVIDENCED_L5_READY_AFTER_A0266 | autonomous_execution_and_closed_loop_validation_missing | L6-readiness | controlled human-approved closed-loop governance / autonomous boundary validation | closed-loop safety / no-autonomy-breakout / human approval tests | medium | medium | A-026.7 |
| 140 | timetable_change_proposal | Planned Expansion | L4 | D | A-026.5-RUNTIME | EVIDENCED_L4_AFTER_A0265_RUNTIME | KPI_evidence_or_Brain_mapping_missing | L5-readiness | KPI/evidence/Brain-readiness mapping | lineage/mapping contract tests | medium | high | A-026.6 |
| 141 | timetable_change_simulation | Planned Expansion | L3 | C | A-026.4-RUNTIME | EVIDENCED_L3_AFTER_A0264 | operational_visibility_or_API_depth_needed | L4 | operational visibility/API readiness specification | route/visibility contract tests | medium | high | A-026.5 |
| 142 | timetable_recommendation_bridge | Planned Expansion | L3 | C | A-026.4-RUNTIME | EVIDENCED_L3_AFTER_A0264 | operational_visibility_or_API_depth_needed | L4 | operational visibility/API readiness specification | route/visibility contract tests | medium | high | A-026.5 |
| 143 | transcripts | Core Academic | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | transcript KPI mapping | lineage mapping | medium | high | A-026.6 |
| 144 | transport | Student & Campus Life | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | transport KPI mapping | lineage mapping | medium | low | A-026.6 |
| 145 | two_factor_auth | Identity/Access/Security | L3 | C | A-023.0 | EVIDENCED_LEVEL_ONLY | API_missing | L4 | 2FA API visibility | route tests | medium | high | A-026.5 |
| 146 | university_core | Administration & Governance | L4 | D | A-024.5 | EVIDENCED_L4_AFTER_A0245 | KPI_evidence_or_Brain_mapping_missing | L5-readiness | university core evidence readiness mapping | lineage/mapping contract tests | medium | high | A-026.6 |
| 147 | usage | Finance & Billing | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | KPI_evidence_missing | L5 | usage KPI lineage | lineage mapping | medium | high | A-026.6 |
| 148 | visitor_management | Student & Campus Life | L5 | E | A-023.0 | EVIDENCED_LEVEL_ONLY | E2E_gate_missing | L6 | visitor E2E and gates | gate continuity | high | high | A-026.7 |
| 149 | workflows | Administration & Governance | L4 | D | A-023.0 | EVIDENCED_LEVEL_ONLY | Brain_mapping_missing | L5 | workflow signal mapping | mapping tests | medium | medium | A-026.6 |
| 150 | workload_management | Planned Expansion | L5 | E | A-026.6-RUNTIME | EVIDENCED_L5_READY_AFTER_A0266 | autonomous_execution_and_closed_loop_validation_missing | L6-readiness | controlled human-approved closed-loop governance / autonomous boundary validation | closed-loop safety / no-autonomy-breakout / human approval tests | medium | high | A-026.7 |

## Full Extension 25 Module Registry Matrix

| # | Extension Module | Domain | Initial Level | Runtime Created? | Baseline Impact | Capability Status | Related Killer Workflow | Required Work | Priority | Future Action |
|---:|---|---|---:|---|---|---|---|---|---|---|
| 1 | digital_credentials_wallet | Academic | L0 | NO | NO | PLANNING_ONLY | digital credential issuance governance | define service contract and governance policy | high | A-027+ |
| 2 | micro_credentials_stack | Academic | L0 | NO | NO | PLANNING_ONLY | stackable credential design governance | design credential stacking model | high | A-027+ |
| 3 | alumni_career_outcomes | Student Success | L0 | NO | NO | PLANNING_ONLY | alumni outcomes analytics | define outcomes schema and KPI lineage | medium | A-026+ |
| 4 | grant_peer_review | Research | L0 | NO | NO | PLANNING_ONLY | research grant peer-review workflow | define review FSM and approval queues | high | A-027+ |
| 5 | research_data_governance | Research | L0 | NO | NO | PLANNING_ONLY | research data access and retention | define data governance policy contracts | high | A-027+ |
| 6 | llm_eval_harness | AI Platform | L0 | NO | NO | PLANNING_ONLY | model evaluation deterministic gates | define evaluation service contract | high | A-025.2 |
| 7 | prompt_lifecycle_governance | AI Platform | L0 | NO | NO | PLANNING_ONLY | prompt release governance approval | define prompt version and release FSM | high | A-025.2 |
| 8 | knowledge_retrieval_fabric | AI Platform | L0 | NO | NO | PLANNING_ONLY | retrieval quality audit and drift | define orchestration and lineage contracts | high | A-025.2 |
| 9 | ai_model_registry | AI Platform | L0 | NO | NO | PLANNING_ONLY | model governance and policy hooks | define model lifecycle inventory | high | A-025.3 |
| 10 | model_cost_optimizer | Finance/AI | L0 | NO | NO | PLANNING_ONLY | cost optimization recommendations | define cost optimization advisory service | medium | A-026+ |
| 11 | copilot_safety_ops | AI Governance | L0 | NO | NO | PLANNING_ONLY | policy violation triage queue | define safety gate and policy FSM | high | A-025.3 |
| 12 | policy_simulation_lab | Governance | L0 | NO | NO | PLANNING_ONLY | policy impact simulation | define no-mutation simulation contracts | medium | A-026+ |
| 13 | incident_command_center | Security/Governance | L0 | NO | NO | PLANNING_ONLY | cross-domain incident dispatch | define incident FSM and routing rules | high | A-026+ |
| 14 | threat_intel_fusion | Security | L0 | NO | NO | PLANNING_ONLY | threat signal normalization | define threat signal fusion service | high | A-026+ |
| 15 | privacy_request_orchestrator | Compliance | L0 | NO | NO | PLANNING_ONLY | DSAR and privacy operations | define privacy request FSM and SLA | high | A-026+ |
| 16 | data_retention_orchestrator | Compliance | L0 | NO | NO | PLANNING_ONLY | retention policy enforcement | define retention policy service contract | high | A-026+ |
| 17 | billing_reconciliation_ops | Finance | L0 | NO | NO | PLANNING_ONLY | reconciliation discrepancy closure | define reconciliation workflow FSM | high | A-025.3 |
| 18 | revenue_leak_detection | Finance | L0 | NO | NO | PLANNING_ONLY | revenue anomaly surfacing | define anomaly detection and alert service | medium | A-026+ |
| 19 | procurement_vendor_risk | Procurement | L0 | NO | NO | PLANNING_ONLY | vendor risk assessment workflow | define risk scoring and audit lineage | high | A-026+ |
| 20 | classroom_iot_telemetry | Campus | L0 | NO | NO | PLANNING_ONLY | IoT telemetry ingestion | define telemetry ingestion contracts | medium | A-027+ |
| 21 | energy_optimization_ops | Campus | L0 | NO | NO | PLANNING_ONLY | energy optimization recommendations | define optimization advisory service | medium | A-027+ |
| 22 | transport_fleet_ops | Campus | L0 | NO | NO | PLANNING_ONLY | fleet operations visibility | define fleet status and incident service | medium | A-027+ |
| 23 | admissions_yield_prediction | Admissions | L0 | NO | NO | PLANNING_ONLY | yield prediction advisory workflow | define yield advisory service and guidance | high | A-026+ |
| 24 | student_success_playbooks | Student Success | L0 | NO | NO | PLANNING_ONLY | intervention playbook approvals | define playbook orchestration and approval FSM | high | A-026+ |
| 25 | faculty_workload_optimizer | HR/Faculty | L0 | NO | NO | PLANNING_ONLY | workload planning recommendations | define workload advisory service | high | A-027+ |

## Matrix Verification Summary

### Baseline Matrix Verification

| Check | Expected | Found | Status |
|---|---:|---:|---|
| Baseline rows | 150 | 150 | PASS |
| Duplicate baseline modules | 0 | 0 | PASS |
| L0 count | 0 | 0 | PASS |
| L1 count | 0 | 0 | PASS |
| L2 count | 29 | 29 | PASS |
| L3 count | 26 | 26 | PASS |
| L4 count | 68 | 68 | PASS |
| L5 count | 25 | 25 | PASS |
| L6 count | 2 | 2 | PASS |
| maturity_arithmetic_check | PASS | PASS | PASS |

### Baseline Bucket Verification

| Bucket | Expected | Found | Status |
|---|---:|---:|---|
| Bucket A | 0 | 0 | PASS |
| Bucket B | 29 | 29 | PASS |
| Bucket C | 26 | 26 | PASS |
| Bucket D | 68 | 68 | PASS |
| Bucket E | 25 | 25 | PASS |
| Bucket F | 2 | 2 | PASS |

### Extension Matrix Verification

| Check | Expected | Found | Status |
|---|---:|---:|---|
| Extension rows | 25 | 25 | PASS |
| Duplicate extension modules | 0 | 0 | PASS |
| Runtime-created extension claims | 0 unless evidenced | 0 | PASS |
| Baseline impact | 0 | 0 | PASS |
| All extensions at L0 | 25 | 25 | PASS |

## A-026.3.B2 — Post-A0263 Matrix Reconciliation

- Reason: A-026.4-SPEC found L2_MATRIX_MISMATCH (expected L2=21, matrix showed 17)
- Correction: 8 A-026.3 baseline rows reconciled from stale L0/L1 to L2
- Post-A-026.3 reconciled baseline metrics: L0=0, L1=16, L2=21, L3=24, L4=66, L5=21, L6=2, total=150, maturity_arithmetic_check=PASS
- Scope boundary: no runtime code changes and no new maturity movement beyond approved A-026.3
- Alignment: matrix now matches authoritative metrics in SBS_UB.md
- Decision: A-026.4-SPEC may resume

## A-026.2.B3 — A-026.3 Batch Deep Implementation Specification

### L2 Implementation Contract Standard

Every A-026.3 module must conform to L2 standard by end of A-026.3:

1. **Package Structure**
   - backend/app/modules/<module_name>/__init__.py must exist
   - backend/app/modules/<module_name>/service.py must exist
   - FOUNDATION.md recommended for L0 modules becoming L2

2. **Service Contract**
   - Pure deterministic functions (no DB mutation, no external calls without guards)
   - Typed constants or dictionary-contract schemas
   - Tenant_id validation on entry
   - No endpoint/router exposure in service.py
   - No frontend claims

3. **Tenant Safety (Critical)**
   - validate_tenant_id(tenant_id) function required
   - Fail-closed: reject tenant_id=None, tenant_id<=0, invalid format
   - No cross-tenant aggregation
   - All returned data must include tenant_id scope

4. **FSM/Status Anchors**
   - Status constants defined where workflow/state exists
   - Transition rules or allowed_actions constants
   - Forbidden_actions constants where applicable

5. **Anti-Inflation Boundaries**
   - no_api_claim = true (documented in module docstring)
   - no_frontend_claim = true
   - no_brain_claim = true
   - no_autonomous_execution = true
   - no_e2e_claim = true
   - target_level_only = L2

6. **Tests**
   - import test: module imports without error
   - tenant validation test: fail-closed on bad tenant_id
   - determinism test: repeated calls = same output
   - FSM/constants test: status values are valid
   - anti-inflation test: no API/frontend markers present

### Module-by-Module Deep Implementation Specification

#### Module 1: human_approved_timetable_workflow

**Current State**
- Current Level: L0
- Target Level: L2
- Primary Gap: foundation_missing (no package exists yet)
- Why Selected: High-priority workflow foundation, many other timetable modules depend on this contract

**Intended L2 Scope**
- Will do: Define foundation package and deterministic service contract for human-approved workflows
- Will NOT do: Auto-apply timetable changes, implement scheduling logic, create API endpoints, create frontend UX, claim Brain readiness

**Expected Files**
- backend/app/modules/human_approved_timetable_workflow/__init__.py
- backend/app/modules/human_approved_timetable_workflow/service.py

**Service Contract Functions**
- `validate_workflow_tenant(tenant_id: int)` → bool (fail-closed)
- `get_workflow_status_contract()` → dict with approved workflow status schema

**FSM/Status Constants**
```
WORKFLOW_STATUS = {
    'DRAFT': 'initial proposal state',
    'PENDING_HUMAN_REVIEW': 'awaiting human decision',
    'HUMAN_APPROVED': 'approved for manual application',
    'HUMAN_REJECTED': 'rejected by human reviewer',
    'CANCELLED': 'workflow cancelled'
}
FORBIDDEN_ACTIONS = ['AUTO_APPLY', 'AUTO_OPTIMIZE', 'AUTONOMOUS_ROLLBACK']
## A-026.4-RUNTIME — L2→L3 Service Logic Normalization

- Selected 8 modules moved from L2/B to L3/C.
- Deterministic backend service logic was added without API, frontend, KPI, Brain, or autonomous execution claims.
- Local compile and behavior assertions passed in this environment.
- A-026.5 will be needed for the L3→L4 operational visibility/API planning step.
- Extension 25 remains unchanged and separate.
HUMAN_APPROVAL_REQUIRED = True
```

**Tenant Guard**
- validate_workflow_tenant: reject tenant_id None/≤0
- All workflow records scoped to tenant_id
- No cross-tenant workflow visibility

**Required Tests**
- test_human_approved_workflow_import
- test_workflow_tenant_validation_fail_closed
- test_workflow_status_constants_valid
- test_workflow_determinism
- test_no_auto_apply_claim

---

#### Module 2: timetable_change_proposal

**Current State**
- Current Level: L0
- Target Level: L2
- Primary Gap: foundation_missing
- Why Selected: Core change request domain, must be deterministic

**Intended L2 Scope**
- Will do: Deterministic proposal contract with payload validation
- Will NOT do: Scheduling conflict detection, optimization, automatic approval

**Expected Files**
- backend/app/modules/timetable_change_proposal/__init__.py
- backend/app/modules/timetable_change_proposal/service.py

**Service Contract Functions**
- `validate_proposal_tenant(tenant_id: int)` → bool
- `validate_proposal_payload(payload: dict)` → (bool, dict) with error details
- `get_proposal_schema()` → dict defining expected proposal structure

**FSM/Status Constants**
```
PROPOSAL_STATUS = {
    'SUBMITTED': 'initial proposal',
    'UNDER_REVIEW': 'being evaluated',
    'READY_FOR_SIMULATION': 'approved for simulation testing',
    'REJECTED': 'rejected during review',
    'APPLIED': 'change has been applied'
}
```

**Tenant Guard**
- validate_proposal_tenant: fail-closed on invalid tenant
- All proposals scoped by tenant_id
- No cross-tenant proposal access

**Required Tests**
- test_proposal_import
- test_proposal_tenant_guard
- test_proposal_schema_validation
- test_proposal_determinism
- test_proposal_no_autoconf_claim

---

#### Module 3: timetable_change_simulation

**Current State**
- Current Level: L0
- Target Level: L2
- Primary Gap: service_contract_missing
- Why Selected: Blocks KPI and approval logic, guards required

**Intended L2 Scope**
- Will do: Simulation request/response contract with input validation
- Will NOT do: Real timetable mutation, optimization solving, conflict resolution

**Expected Files**
- backend/app/modules/timetable_change_simulation/__init__.py
- backend/app/modules/timetable_change_simulation/service.py

**Service Contract Functions**
- `validate_simulation_tenant(tenant_id: int)` → bool
- `validate_simulation_request(request: dict)` → (bool, dict)
- `get_simulation_readiness_response()` → dict

**FSM/Status Constants**
```
SIMULATION_STATUS = {
    'PENDING': 'awaiting simulation',
    'SIMULATED': 'simulation completed',
    'CONFLICT_DETECTED': 'conflicts found in simulation',
    'READY_FOR_APPROVAL': 'no conflicts, ready for human review',
    'SIMULATION_FAILED': 'simulation process encountered error'
}
FORBIDDEN_MUTATIONS = ['APPLY_TIMETABLE', 'COMMIT_CHANGES', 'AUTO_RESOLVE_CONFLICTS']
```

**Tenant Guard**
- validate_simulation_tenant: fail-closed
- simulation input must include tenant_id
- No cross-tenant simulation data

**Required Tests**
- test_simulation_import
- test_simulation_tenant_guard
- test_simulation_input_validation
- test_simulation_no_mutation_claim
- test_simulation_contract_determinism

---

#### Module 4: timetable_recommendation_bridge

**Current State**
- Current Level: L0
- Target Level: L2
- Primary Gap: service_contract_missing
- Why Selected: Bridge prerequisite for later governance layers

**Intended L2 Scope**
- Will do: Deterministic recommendation envelope contract
- Will NOT do: AI provider calls, automatic recommendations, autonomous execution

**Expected Files**
- backend/app/modules/timetable_recommendation_bridge/__init__.py
- backend/app/modules/timetable_recommendation_bridge/service.py

**Service Contract Functions**
- `validate_bridge_tenant(tenant_id: int)` → bool
- `create_recommendation_envelope(simulation_result: dict)` → dict

**Constants**
```
RECOMMENDATION_SOURCE = {
    'SIMULATION_ANALYSIS': 'analysis from simulation module',
    'HISTORICAL_PATTERNS': 'patterns from historical data',
    'PENDING': 'recommendation not yet available'
}
BRIDGE_MODE = 'DETERMINISTIC_ENVELOPE_ONLY'
NO_AI_PROVIDER_CALLS = True
```

**Tenant Guard**
- validate_bridge_tenant
- All recommendations scoped to tenant

**Required Tests**
- test_bridge_import
- test_bridge_tenant_guard
- test_bridge_envelope_determinism
- test_no_ai_calls
- test_bridge_contract

---

#### Module 5: timetable_approval_queue

**Current State**
- Current Level: L1 (foundation exists, L1 markers found in A-023.0)
- Target Level: L2
- Primary Gap: service_contract_missing
- Why Selected: Required for bounded human review workflow, L1→L2 is service contract gap

**Intended L2 Scope**
- Will do: Queue contract and status constants for human review
- Will NOT do: Actual queue persistence (unless already existing), automatic action, autonomous decision

**Expected Files**
- backend/app/modules/timetable_approval_queue/service.py (augment existing)

**Service Contract Functions**
- `validate_queue_tenant(tenant_id: int)` → bool
- `enqueue_for_review(item: dict)` → dict with queue_id
- `get_queue_status_contract()` → dict

**FSM/Status Constants**
```
QUEUE_STATUS = {
    'PENDING_REVIEW': 'awaiting human decision',
    'IN_PROGRESS': 'reviewer is examining',
    'APPROVED_PENDING_APPLY': 'approved, awaiting apply command',
    'REJECTED': 'rejected by reviewer',
    'APPLIED': 'changes applied'
}
ALLOWED_ACTIONS = ['APPROVE', 'REJECT', 'REQUEST_MORE_INFO', 'REASSIGN_REVIEWER']
FORBIDDEN_AUTO_ACTIONS = ['AUTO_APPROVE', 'AUTO_APPLY', 'AUTO_REJECT']
```

**Tenant Guard**
- validate_queue_tenant
- Queue items scoped by tenant
- No cross-tenant queue visibility

**Required Tests**
- test_queue_import
- test_queue_tenant_guard
- test_queue_status_contract
- test_forbidden_auto_actions
- test_queue_determinism

---

#### Module 6: timetable_change_kpi_dashboard

**Current State**
- Current Level: L1
- Target Level: L2
- Primary Gap: verification_pending
- Why Selected: Validation-focused, must verify backend contract dependency before dashboard claims

**Intended L2 Scope**
- Will do: Backend-facing KPI readiness contract (no frontend yet)
- Will NOT do: Frontend dashboard exposure, KPI values computation, Brain signal claims

**Expected Files**
- backend/app/modules/timetable_change_kpi_dashboard/service.py (augment or create)

**Service Contract Functions**
- `validate_kpi_dashboard_tenant(tenant_id: int)` → bool
- `get_kpi_readiness_contract()` → dict with readiness fields

**Contract Output**
```
KPI_READINESS = {
    'tenant_id': <int>,
    'module': 'timetable_change',
    'kpi_readiness_status': 'BACKEND_CONTRACT_ONLY',
    'frontend_claim': False,
    'kpi_values_available': False,
    'brain_mapping_status': 'NOT_AVAILABLE',
    'target_level': 'L2'
}
```

**Tenant Guard**
- validate_kpi_dashboard_tenant
- All KPI readiness scoped by tenant

**Required Tests**
- test_kpi_dashboard_import
- test_kpi_tenant_guard
- test_kpi_readiness_contract_no_frontend_claim
- test_kpi_no_brain_mapping_claim
- test_kpi_determinism

---

#### Module 7: workload_management

**Current State**
- Current Level: L1
- Target Level: L2
- Primary Gap: service_contract_missing
- Why Selected: Work level governance, L1→L2 service contract needed

**Intended L2 Scope**
- Will do: Deterministic workload planning contract
- Will NOT do: Payroll mutation, schedule mutation, automatic workload assignment

**Expected Files**
- backend/app/modules/workload_management/service.py (augment existing)

**Service Contract Functions**
- `validate_workload_tenant(tenant_id: int)` → bool
- `get_workload_readiness_contract()` → dict
- `validate_workload_input(payload: dict)` → (bool, dict)

**FSM/Status Constants**
```
WORKLOAD_STATUS = {
    'PLANNING': 'initial planning stage',
    'UNDER_REVIEW': 'awaiting approval',
    'READY_FOR_ASSIGNMENT': 'approved, ready for assignment',
    'ASSIGNED': 'workload assigned to staff',
    'MONITORED': 'workload being monitored',
    'COMPLETED': 'workload cycle complete'
}
FORBIDDEN_AUTO_ACTIONS = ['AUTO_ASSIGN', 'AUTO_OVERRIDE_CONSTRAINTS', 'AUTO_MUTATE_PAYROLL']
```

**Tenant Guard**
- validate_workload_tenant
- All workload scoped by tenant

**Required Tests**
- test_workload_import
- test_workload_tenant_guard
- test_workload_contract
- test_no_auto_assign_claim
- test_workload_determinism

---

#### Module 8: notification_center

**Current State**
- Current Level: L1
- Target Level: L2
- Primary Gap: tenant_guard_missing (critical)
- Why Selected: High priority, tenant safety critical

**Intended L2 Scope**
- Will do: Tenant-safe notification contract (no actual sending)
- Will NOT do: Email/SMS/push provider calls, cross-tenant broadcasts, automatic notification generation

**Expected Files**
- backend/app/modules/notification_center/service.py (augment existing)

**Service Contract Functions**
- `validate_notification_tenant(tenant_id: int)` → bool (CRITICAL)
- `build_notification_contract(tenant_id: int, type: str)` → dict
- `get_notification_types()` → dict

**FSM/Status Constants**
```
NOTIFICATION_TYPE = {
    'WORKFLOW_APPROVED': 'workflow has been approved',
    'WORKFLOW_REJECTED': 'workflow has been rejected',
    'WORKLOAD_ASSIGNED': 'workload has been assigned',
    'REVIEW_NEEDED': 'human review is needed',
    'CHANGE_APPLIED': 'timetable change has been applied'
}
NOTIFICATION_STATUS = {
    'QUEUED': 'notification queued',
    'COMPOSED': 'notification message composed',
    'READY_FOR_DISPATCH': 'ready to send (but not sent)',
    'SEND_FAILED': 'send attempt failed'
}
NO_SENDING = True
NO_PROVIDER_CALLS = True
TENANT_ISOLATION_REQUIRED = True
```

**Tenant Guard (CRITICAL)**
- validate_notification_tenant: MUST fail-closed on invalid tenant_id
- tenant_id=None → rejection
- tenant_id≤0 → rejection
- All notifications must include tenant_id scope
- NO cross-tenant notification visibility
- NO cross-tenant broadcast capability

**Required Tests**
- test_notification_import
- test_notification_tenant_guard_fail_closed (critical)
- test_notification_tenant_guard_negative_rejection
- test_notification_contract
- test_no_actual_sending_claim
- test_notification_determinism

### Shared A-026.3 Test File Specification

**Test File**: backend/tests/test_a0263_foundation_service_normalization.py

**Test Structure**:
1. **Import Validation** (1 shared test)
   - All 8 module service files import successfully
   - All required functions are callable

2. **Tenant Validation Suite** (8 module-specific tests)
   - Each module: test_<module>_tenant_validation_fail_closed()
   - Rejects tenant_id=None, tenant_id≤0
   - Accepts valid tenant_id

3. **Contract Output Validation** (1 shared test)
   - All modules return required common fields: tenant_id, module, status/readiness_status
   - All returns are deterministic (JSON-serializable)

4. **Module-Specific Constants** (8 module-specific tests)
   - Workflow modules: test_workflow_status_constants_valid()
   - Queue modules: test_forbidden_actions_constants_defined()
   - Notification module: test_notification_types_constants_valid()

5. **Anti-Inflation Validation** (8 module-specific tests)
   - Each module: test_<module>_anti_inflation_flags()
   - Assert: no_api_claim, no_frontend_claim, no_brain_claim, no_autonomous_execution, target_level=L2

6. **Determinism** (8 module-specific tests)
   - Each module: test_<module>_determinism()
   - Repeated calls with same input produce identical output

**Expected Test Count**: Minimum 16 tests (shared: 2, per-module: ~1.75 avg)
**Acceptable Range**: 16–30 tests

### A-026.3 Implementation Scope Boundaries

| Area | Allowed | Forbidden |
|---|---|---|
| Backend module files | Create __init__.py, service.py | No routers, no endpoints |
| Service contracts | Pure functions, tenant guards, FSM constants | DB mutations, external provider calls |
| Tenant guards | validate_tenant_id, fail-closed logic | Cross-tenant data, bypass logic |
| FSM/status constants | Status values, transitions, allowed actions | Autonomous execution, auto-apply claims |
| Tests | Import, tenant validation, determinism, anti-inflation | Production tests, E2E tests, performance tests |
| API | No API endpoints created | Any endpoint creation forbidden |
| Frontend | No frontend visibility | Any frontend claim forbidden |
| KPI | No KPI values, no lineage claims | KPI computation, Brain mapping |
| Brain | No Brain signal mapping | Any Brain governance claim |
| Events | No event publishing from these modules | Any event emission |
| DB/Migrations | No DB schema changes | Any schema creation |
| External providers | No calls (fail-closed) | Any email/SMS/push calls |
| Maturity claims | L2 only after tests pass | No L3/L4/L5/L6 claims |

### Expected A-026.3 Implementation Files

| File | Created? | Reason |
|---|---|---|
| backend/app/modules/human_approved_timetable_workflow/__init__.py | YES | L0→L2 requires new package |
| backend/app/modules/human_approved_timetable_workflow/service.py | YES | L0→L2 requires service contract |
| backend/app/modules/timetable_change_proposal/__init__.py | YES | L0→L2 requires new package |
| backend/app/modules/timetable_change_proposal/service.py | YES | L0→L2 requires service contract |
| backend/app/modules/timetable_change_simulation/__init__.py | YES | L0→L2 requires new package |
| backend/app/modules/timetable_change_simulation/service.py | YES | L0→L2 requires service contract |
| backend/app/modules/timetable_recommendation_bridge/__init__.py | YES | L0→L2 requires new package |
| backend/app/modules/timetable_recommendation_bridge/service.py | YES | L0→L2 requires service contract |
| backend/app/modules/timetable_approval_queue/service.py | AUGMENT | L1→L2 requires service contract upgrade |
| backend/app/modules/timetable_change_kpi_dashboard/service.py | AUGMENT | L1→L2 requires service contract upgrade |
| backend/app/modules/workload_management/service.py | AUGMENT | L1→L2 requires service contract upgrade |
| backend/app/modules/notification_center/service.py | AUGMENT | L1→L2 requires tenant guard + contract |
| backend/tests/test_a0263_foundation_service_normalization.py | YES | Shared test file for all 8 modules |
| SBS_UB_150_MODULE_NORMALIZATION.md | UPDATE | Add B3 section, mark modules as A-026.3 spec complete |
| SBS_UB.md | UPDATE | Control block + B3 execution block |
| A-026.2.B3-A0263_BATCH_DEEP_IMPLEMENTATION_SPECIFICATION_REPORT.md | CREATE | B3 report documenting this specification |

### A-026.3 Definition of Done

A-026.3 implementation is CLOSED only when:
1. All 8 modules implemented to L2 contract standard (service.py exists with contract functions)
2. All 4 new packages (human_approved_timetable_workflow, timetable_change_proposal, timetable_change_simulation, timetable_recommendation_bridge) created
3. All 4 augmented modules (timetable_approval_queue, timetable_change_kpi_dashboard, workload_management, notification_center) have service.py with L2 contract
4. backend/tests/test_a0263_foundation_service_normalization.py exists with ≥16 tests, all PASS
5. git diff --check PASS (no whitespace/conflict errors)
6. No API endpoints created (grep -r "router\|@app.post\|@app.get" backend/app/modules/timetable* backend/app/modules/workload_management backend/app/modules/notification_center = only inside service.py, not in router)
7. No frontend pages created (no changes to frontend/app/**/page.tsx for timetable modules)
8. No KPI/Brain lineage claims (modules return kpi_readiness=BACKEND_CONTRACT_ONLY)
9. No maturity levels changed beyond L0/L1→L2 for selected 8 modules
10. Baseline arithmetic remains: L0=4, L1=20, L2=13, L3=24, L4=66, L5=21, L6=2, sum=150
11. Extension 25 isolation maintained (no extension modules merged into baseline)
12. A-026.3 report created documenting implementation
13. SBS_UB.md updated with A-026.3 completion block
14. Scoped commit only (3 files staged: SBS_UB.md, SBS_UB_150_MODULE_NORMALIZATION.md, A-026.3 report)

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

## A-026.10-SPEC — Final L2 Cleanup / Remaining L2→L3 Deterministic Logic Specification

Status: SPEC ONLY (planning/docs-only)

Purpose: extract all remaining L2 modules, confirm inventory integrity, select final L2->L3 deterministic cleanup strategy, and define module-specific L3 implementation contracts for the future runtime.

### Repo Hygiene Snapshot

- branch: main
- git status --short: clean
- git diff --name-only: clean
- git diff --stat: clean
- risk assessment: no unexpected dirty/untracked runtime artifacts at spec start

| File | Type | Related Action | Risk | Recommended Handling |
|---|---|---|---|---|
| None detected at spec start | workspace state | A-026.10-SPEC | low | proceed with docs-only update |

### Source-of-Truth Confirmation

- SBS_UB.md remains authoritative tracker.
- A-026.9-RUNTIME remains closed/validated.
- A-026.10-RUNTIME has not started in this spec phase.
- next_action_id before this spec: A-026.10-SPEC.
- baseline metrics at spec start: L0=0, L1=0, L2=13, L3=42, L4=68, L5=25, L6=2, total=150.
- extension separation unchanged: extension_total_count=25, total_tracked_modules=175, separation=PASS.

### Remaining L2 Extraction Summary

Extraction source: Full Baseline 150 Module Normalization Matrix (canonical rows).

| # | Module | Domain | Current Level | Current Gap | Required Work | Required Tests | Source |
|---:|---|---|---:|---|---|---|---|
| 5 | accreditation_compliance | Planned Expansion | L2 | FSM_workflow_missing | deterministic service logic | targeted tests | A-023.0 |
| 11 | ai_cost_governance | Planned Expansion | L2 | service_contract_missing | cost service determinism | contract tests | A-023.0 |
| 14 | ai_plagiarism | Research & Innovation | L2 | FSM_workflow_missing | plagiarism detection FSM | transition tests | A-023.0 |
| 32 | conference_management | Research & Innovation | L2 | FSM_workflow_missing | conference FSM transitions | transition tests | A-023.0 |
| 34 | contracts_legal_repository | Planned Expansion | L2 | service_contract_missing | legal contract service | contract tests | A-023.0 |
| 36 | counseling_case_management | Planned Expansion | L2 | service_contract_missing | case management service | contract tests | A-023.0 |
| 41 | developer_portal | Planned Expansion | L2 | service_contract_missing | developer service contract | contract tests | A-023.0 |
| 59 | federation_management | Planned Expansion | L2 | FSM_workflow_missing | federation FSM logic | transition tests | A-023.0 |
| 62 | health_services | Planned Expansion | L2 | FSM_workflow_missing | health service logic | transition tests | A-023.0 |
| 80 | library_circulation | Planned Expansion | L2 | FSM_workflow_missing | circulation FSM logic | transition tests | A-023.0 |
| 83 | local_user_management | Planned Expansion | L2 | tenant_guard_missing | user management tenant guards | tenant tests | A-023.0 |
| 116 | research_grants | Planned Expansion | L2 | FSM_workflow_missing | grants FSM logic | transition tests | A-023.0 |
| 125 | student_ai_tutor | Research & Innovation | L2 | FSM_workflow_missing | tutor FSM logic | transition tests | A-023.0 |

- expected L2 count: 13
- found L2 count: 13
- status: PASS

### A-026.8 and A-026.9 Exclusion Confirmation

These modules are already L3 in the canonical matrix and are excluded from A-026.10 selection.

| Module | Expected Level | Found Level | Status |
|---|---:|---:|---|
| digital_certificates | L3 | L3 | PASS |
| records_hub | L3 | L3 | PASS |
| student_success_analytics | L3 | L3 | PASS |
| publication_registry | L3 | L3 | PASS |
| research_projects | L3 | L3 | PASS |
| lms_assessment_center | L3 | L3 | PASS |
| lab_operations | L3 | L3 | PASS |
| internship_marketplace | L3 | L3 | PASS |
| parking_permit_ops | L3 | L3 | PASS |
| parking_enforcement | L3 | L3 | PASS |
| event_registration_portal | L3 | L3 | PASS |
| parent_engagement | L3 | L3 | PASS |
| alumni_relations_ops | L3 | L3 | PASS |
| donations_fundraising | L3 | L3 | PASS |
| exam_integrity_analytics | L3 | L3 | PASS |
| mobile_push_gateway | L3 | L3 | PASS |

### Remaining L2 Readiness Scoring

Priority score model (max 40):
Domain Value + SaaS Value + L2 Quality + Logic Clarity + (6 - Tenant Risk) + Testability + (6 - Provider/AI Risk) + (6 - Blast Radius).

| Module | Domain Value | SaaS Value | L2 Quality | Logic Clarity | Tenant Risk | Testability | Provider/AI Risk | Blast Radius | Priority Score | Recommendation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| accreditation_compliance | 4 | 4 | 4 | 4 | 2 | 4 | 1 | 2 | 27 | SELECT_A02610 |
| ai_cost_governance | 4 | 4 | 4 | 4 | 3 | 4 | 3 | 3 | 23 | SELECT_A02610 |
| ai_plagiarism | 4 | 4 | 4 | 3 | 4 | 3 | 4 | 3 | 19 | SELECT_A02610 |
| conference_management | 3 | 3 | 4 | 4 | 2 | 4 | 1 | 2 | 25 | SELECT_A02610 |
| contracts_legal_repository | 4 | 4 | 4 | 4 | 3 | 4 | 1 | 3 | 25 | SELECT_A02610 |
| counseling_case_management | 4 | 4 | 4 | 4 | 3 | 4 | 1 | 3 | 25 | SELECT_A02610 |
| developer_portal | 3 | 4 | 4 | 4 | 2 | 4 | 1 | 2 | 26 | SELECT_A02610 |
| federation_management | 3 | 3 | 4 | 4 | 3 | 4 | 1 | 2 | 25 | SELECT_A02610 |
| health_services | 4 | 4 | 4 | 4 | 3 | 4 | 2 | 3 | 24 | SELECT_A02610 |
| library_circulation | 4 | 4 | 4 | 4 | 2 | 4 | 1 | 2 | 27 | SELECT_A02610 |
| local_user_management | 4 | 5 | 4 | 4 | 5 | 4 | 1 | 4 | 20 | SELECT_A02610 |
| research_grants | 4 | 4 | 4 | 4 | 3 | 4 | 1 | 3 | 25 | SELECT_A02610 |
| student_ai_tutor | 4 | 4 | 4 | 3 | 4 | 3 | 5 | 4 | 15 | SELECT_A02610 |

### Final L2 Cleanup Strategy

Decision: Option A selected (all 13 modules in one runtime) because all 13 have existing package and service.py foundations, the scope is bounded to service-logic uplift, and prior batch evidence supports a similar load profile.

| Selected Module | Current Level | Target Level | Runtime Group | Why Selected | Expected L3 Logic | Required Tests | Risk |
|---|---:|---:|---|---|---|---|---|
| accreditation_compliance | L2 | L3 | A-026.10-RUNTIME | compliance leverage, deterministic policy readiness | compliance state/risk/readiness logic | tenant, classification, boundary | medium |
| ai_cost_governance | L2 | L3 | A-026.10-RUNTIME | cost governance reuse and controls | deterministic cost readiness and guardrails | tenant, deterministic, anti-provider | medium |
| ai_plagiarism | L2 | L3 | A-026.10-RUNTIME | integrity risk value | deterministic plagiarism review state | tenant, transition, anti-autonomy | high |
| conference_management | L2 | L3 | A-026.10-RUNTIME | event orchestration reusability | deterministic conference readiness/fsm | tenant, transition, boundary | medium |
| contracts_legal_repository | L2 | L3 | A-026.10-RUNTIME | legal governance dependency | deterministic legal contract readiness | tenant, contract, forbidden-action | medium |
| counseling_case_management | L2 | L3 | A-026.10-RUNTIME | case governance dependency | deterministic counseling case routing | tenant, status, boundary | medium |
| developer_portal | L2 | L3 | A-026.10-RUNTIME | platform control-plane value | deterministic developer onboarding state | tenant, contract, anti-inflation | medium |
| federation_management | L2 | L3 | A-026.10-RUNTIME | identity federation governance | deterministic federation state machine | tenant, transition, policy checks | medium |
| health_services | L2 | L3 | A-026.10-RUNTIME | student wellbeing domain value | deterministic health service triage readiness | tenant, risk, boundary | medium |
| library_circulation | L2 | L3 | A-026.10-RUNTIME | circulation workflow value | deterministic circulation lifecycle rules | tenant, transition, anti-autonomy | medium |
| local_user_management | L2 | L3 | A-026.10-RUNTIME | high SaaS tenancy impact | deterministic user lifecycle and tenant guard logic | tenant-negative, boundary, anti-cross-tenant | high |
| research_grants | L2 | L3 | A-026.10-RUNTIME | research governance value | deterministic grant workflow readiness | tenant, status/risk, boundary | medium |
| student_ai_tutor | L2 | L3 | A-026.10-RUNTIME | strategic AI module cleanup | deterministic tutoring readiness without provider execution | tenant, provider-boundary, anti-autonomy | high |

## A-026.10 Final L2→L3 Deterministic Service Logic Standard

1. Deterministic business logic
- service function does more than return foundation contract
- module-specific classification/readiness/risk/status
- deterministic next recommended step

2. Tenant fail-closed behavior
- tenant_id=None rejected
- tenant_id=0 rejected
- tenant_id<0 rejected
- valid tenant_id accepted
- output tenant-scoped

3. Domain-specific rules
- module-specific statuses
- allowed actions
- forbidden actions
- required evidence
- readiness/risk classification

4. Tests
- import tests
- tenant fail-closed tests
- deterministic output tests
- classification/status/risk tests
- boundary tests
- provider boundary tests where relevant
- anti-inflation tests

5. Anti-inflation
- no API claim
- no frontend claim
- no KPI claim
- no Brain claim
- no autonomous execution
- no L4/L5/L6 claim
- no external provider call

### Module-by-Module Deep Specification

### Module: accreditation_compliance

#### Current State
- Current Level: L2
- Target Level: L3
- Source: A-023.0
- Existing L2 evidence: deterministic contract skeleton and tenant guard
- Primary gap: FSM_workflow_missing

#### Intended L3 Scope
- What this module will do in A-026.10-RUNTIME: deterministic accreditation readiness and policy exception classification.
- What this module will NOT do: no API route, no external regulator submission, no autonomous approval.

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/accreditation_compliance/service.py | update | add deterministic accreditation readiness/risk logic |

#### L3 Service Functions
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| evaluate_accreditation_compliance_readiness | classify readiness/risk | tenant_id, compliance_payload | status/classification/risk/next_step/actions/evidence | yes | yes |

#### Domain Logic
- statuses: DRAFT, IN_REVIEW, READY, BLOCKED
- classifications: READY_FOR_COMPLIANCE_REVIEW, NEEDS_POLICY_EVIDENCE, HUMAN_REVIEW_REQUIRED
- risk/readiness levels: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_COMPLIANCE, REQUEST_EVIDENCE, ESCALATE_REVIEW
- forbidden actions: AUTO_APPROVE, AUTO_SUBMIT
- required evidence: policy_context, audit_context, control_context
- human review boundary: compliance approvals are human-controlled

#### Tenant Safety
- invalid tenant behavior: fail-closed ValueError
- valid tenant behavior: deterministic tenant-scoped result
- tenant scope in output: tenant_id always present
- cross-tenant prevention: no cross-tenant aggregation

#### Required Tests
| Test | Purpose |
|---|---|
| test_accreditation_import | import contract exists |
| test_accreditation_tenant_fail_closed | reject invalid tenant ids |
| test_accreditation_deterministic_readiness | deterministic outputs |
| test_accreditation_forbidden_actions | anti-autonomy guard |

#### Anti-Inflation Boundary
- no API endpoint
- no frontend page
- no DB mutation
- no KPI values
- no Brain signal
- no event emission
- no autonomous execution
- no external provider call
- L3 only

### Module: ai_cost_governance

#### Current State
- Current Level: L2
- Target Level: L3
- Source: A-023.0
- Existing L2 evidence: deterministic contract skeleton and tenant guard
- Primary gap: service_contract_missing

#### Intended L3 Scope
- What this module will do in A-026.10-RUNTIME: deterministic cost governance readiness and risk banding.
- What this module will NOT do: no provider calls, no budget mutation, no autonomous enforcement.

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/ai_cost_governance/service.py | update | add deterministic cost governance logic |

#### L3 Service Functions
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| evaluate_ai_cost_governance_readiness | classify budget/risk state | tenant_id, cost_payload | status/classification/risk/next_step/actions/evidence | yes | yes |

#### Domain Logic
- statuses: BASELINE, WATCH, REVIEW_REQUIRED, BLOCKED
- classifications: READY_FOR_GOVERNANCE_REVIEW, NEEDS_COST_EVIDENCE, HUMAN_REVIEW_REQUIRED
- risk/readiness levels: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_COST_POLICY, REQUEST_EVIDENCE, ESCALATE_REVIEW
- forbidden actions: AUTO_BLOCK_SPEND, AUTO_OVERRIDE_POLICY
- required evidence: spend_context, policy_context, variance_context

#### Tenant Safety
- invalid tenant behavior: fail-closed
- valid tenant behavior: deterministic scoped output
- tenant scope in output: required
- cross-tenant prevention: no shared spend rollups

#### Required Tests
| Test | Purpose |
|---|---|
| test_ai_cost_governance_import | module import viability |
| test_ai_cost_governance_tenant_fail_closed | tenant safety |
| test_ai_cost_governance_deterministic_logic | deterministic output |
| test_ai_cost_governance_no_provider_actions | no provider/autonomy |

#### Anti-Inflation Boundary
- no API endpoint
- no frontend page
- no DB mutation
- no KPI values
- no Brain signal
- no event emission
- no autonomous execution
- no external provider call
- L3 only

### Module: ai_plagiarism

#### Current State
- Current Level: L2
- Target Level: L3
- Source: A-023.0
- Existing L2 evidence: deterministic contract skeleton and tenant guard
- Primary gap: FSM_workflow_missing

#### Intended L3 Scope
- What this module will do in A-026.10-RUNTIME: deterministic plagiarism review state/risk classification.
- What this module will NOT do: no autonomous accusation, no model/provider invocation in runtime path.

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/ai_plagiarism/service.py | update | add deterministic plagiarism state logic |

#### L3 Service Functions
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| evaluate_ai_plagiarism_readiness | classify integrity review state | tenant_id, plagiarism_payload | status/classification/risk/next_step/actions/evidence | yes | yes |

#### Domain Logic
- statuses: CLEAN, FLAGGED, UNDER_REVIEW, BLOCKED
- classifications: READY_FOR_REVIEW, NEEDS_EVIDENCE, HUMAN_REVIEW_REQUIRED
- risk/readiness levels: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_SIGNAL, REQUEST_EVIDENCE, ESCALATE_REVIEW
- forbidden actions: AUTO_ACCUSATION, AUTO_PENALTY
- required evidence: submission_context, similarity_context, policy_context

#### Tenant Safety
- invalid tenant behavior: fail-closed
- valid tenant behavior: deterministic output
- tenant scope in output: required
- cross-tenant prevention: no cross-tenant similarity fusion

#### Required Tests
| Test | Purpose |
|---|---|
| test_ai_plagiarism_import | import path |
| test_ai_plagiarism_tenant_fail_closed | tenant guard |
| test_ai_plagiarism_state_determinism | deterministic state |
| test_ai_plagiarism_forbidden_actions | anti-autonomy boundaries |

#### Anti-Inflation Boundary
- no API endpoint
- no frontend page
- no DB mutation
- no KPI values
- no Brain signal
- no event emission
- no autonomous execution
- no external provider call
- L3 only

### Module: conference_management

#### Current State
- Current Level: L2
- Target Level: L3
- Source: A-023.0
- Existing L2 evidence: deterministic contract skeleton and tenant guard
- Primary gap: FSM_workflow_missing

#### Intended L3 Scope
- What this module will do in A-026.10-RUNTIME: deterministic conference lifecycle/readiness transitions.
- What this module will NOT do: no registration side effects, no API surfaces.

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/conference_management/service.py | update | add deterministic conference readiness FSM |

#### L3 Service Functions
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| evaluate_conference_management_readiness | classify event lifecycle state | tenant_id, conference_payload | status/classification/risk/next_step/actions/evidence | yes | yes |

#### Domain Logic
- statuses: DRAFT, PREPARING, READY, BLOCKED
- classifications: READY_FOR_REVIEW, NEEDS_EVENT_EVIDENCE, HUMAN_REVIEW_REQUIRED
- risk/readiness levels: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_PLAN, REQUEST_EVIDENCE, ESCALATE_REVIEW
- forbidden actions: AUTO_PUBLISH_EVENT, AUTO_OVERRIDE_CAPACITY
- required evidence: schedule_context, venue_context, compliance_context

#### Tenant Safety
- invalid tenant behavior: fail-closed
- valid tenant behavior: deterministic output
- tenant scope in output: required
- cross-tenant prevention: no shared event state

#### Required Tests
| Test | Purpose |
|---|---|
| test_conference_import | import validation |
| test_conference_tenant_fail_closed | tenant guard |
| test_conference_fsm_determinism | deterministic transitions |
| test_conference_forbidden_actions | anti-autonomy |

#### Anti-Inflation Boundary
- no API endpoint
- no frontend page
- no DB mutation
- no KPI values
- no Brain signal
- no event emission
- no autonomous execution
- no external provider call
- L3 only

### Module: contracts_legal_repository

#### Current State
- Current Level: L2
- Target Level: L3
- Source: A-023.0
- Existing L2 evidence: deterministic contract skeleton and tenant guard
- Primary gap: service_contract_missing

#### Intended L3 Scope
- What this module will do in A-026.10-RUNTIME: deterministic legal contract review readiness.
- What this module will NOT do: no legal execution, no document mutation.

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/contracts_legal_repository/service.py | update | add deterministic legal contract readiness logic |

#### L3 Service Functions
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| evaluate_contracts_legal_repository_readiness | classify legal review state | tenant_id, legal_payload | status/classification/risk/next_step/actions/evidence | yes | yes |

#### Domain Logic
- statuses: DRAFT, REVIEW_PENDING, READY, BLOCKED
- classifications: READY_FOR_LEGAL_REVIEW, NEEDS_DOCUMENT_EVIDENCE, HUMAN_REVIEW_REQUIRED
- risk/readiness levels: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_CONTRACT, REQUEST_EVIDENCE, ESCALATE_REVIEW
- forbidden actions: AUTO_EXECUTE_CONTRACT, AUTO_APPROVE_TERMS
- required evidence: clause_context, signature_context, jurisdiction_context

#### Tenant Safety
- invalid tenant behavior: fail-closed
- valid tenant behavior: deterministic output
- tenant scope in output: required
- cross-tenant prevention: no cross-tenant document access

#### Required Tests
| Test | Purpose |
|---|---|
| test_legal_repo_import | import validation |
| test_legal_repo_tenant_fail_closed | tenant guard |
| test_legal_repo_deterministic_readiness | deterministic behavior |
| test_legal_repo_forbidden_actions | anti-autonomy |

#### Anti-Inflation Boundary
- no API endpoint
- no frontend page
- no DB mutation
- no KPI values
- no Brain signal
- no event emission
- no autonomous execution
- no external provider call
- L3 only

### Module: counseling_case_management

#### Current State
- Current Level: L2
- Target Level: L3
- Source: A-023.0
- Existing L2 evidence: deterministic contract skeleton and tenant guard
- Primary gap: service_contract_missing

#### Intended L3 Scope
- What this module will do in A-026.10-RUNTIME: deterministic case triage/readiness logic.
- What this module will NOT do: no autonomous case closure, no messaging/provider calls.

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/counseling_case_management/service.py | update | add deterministic counseling case logic |

#### L3 Service Functions
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| evaluate_counseling_case_management_readiness | classify case workflow state | tenant_id, case_payload | status/classification/risk/next_step/actions/evidence | yes | yes |

#### Domain Logic
- statuses: INTAKE, UNDER_REVIEW, READY, BLOCKED
- classifications: READY_FOR_CASE_REVIEW, NEEDS_CASE_EVIDENCE, HUMAN_REVIEW_REQUIRED
- risk/readiness levels: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_CASE, REQUEST_EVIDENCE, ESCALATE_REVIEW
- forbidden actions: AUTO_CLOSE_CASE, AUTO_ASSIGN_INTERVENTION
- required evidence: intake_context, consent_context, history_context

#### Tenant Safety
- invalid tenant behavior: fail-closed
- valid tenant behavior: deterministic output
- tenant scope in output: required
- cross-tenant prevention: strict tenant case boundary

#### Required Tests
| Test | Purpose |
|---|---|
| test_counseling_case_import | import validation |
| test_counseling_case_tenant_fail_closed | tenant guard |
| test_counseling_case_deterministic_logic | deterministic output |
| test_counseling_case_forbidden_actions | anti-autonomy |

#### Anti-Inflation Boundary
- no API endpoint
- no frontend page
- no DB mutation
- no KPI values
- no Brain signal
- no event emission
- no autonomous execution
- no external provider call
- L3 only

### Module: developer_portal

#### Current State
- Current Level: L2
- Target Level: L3
- Source: A-023.0
- Existing L2 evidence: deterministic contract skeleton and tenant guard
- Primary gap: service_contract_missing

#### Intended L3 Scope
- What this module will do in A-026.10-RUNTIME: deterministic onboarding/readiness policy logic.
- What this module will NOT do: no API key issuance, no platform mutation.

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/developer_portal/service.py | update | add deterministic developer readiness logic |

#### L3 Service Functions
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| evaluate_developer_portal_readiness | classify onboarding state | tenant_id, portal_payload | status/classification/risk/next_step/actions/evidence | yes | yes |

#### Domain Logic
- statuses: NEW, VERIFIED, READY, BLOCKED
- classifications: READY_FOR_ONBOARDING_REVIEW, NEEDS_PROFILE_EVIDENCE, HUMAN_REVIEW_REQUIRED
- risk/readiness levels: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_PROFILE, REQUEST_EVIDENCE, ESCALATE_REVIEW
- forbidden actions: AUTO_ISSUE_KEYS, AUTO_APPROVE_ACCESS
- required evidence: profile_context, policy_ack_context, compliance_context

#### Tenant Safety
- invalid tenant behavior: fail-closed
- valid tenant behavior: deterministic output
- tenant scope in output: required
- cross-tenant prevention: no cross-tenant account mapping

#### Required Tests
| Test | Purpose |
|---|---|
| test_developer_portal_import | import validation |
| test_developer_portal_tenant_fail_closed | tenant guard |
| test_developer_portal_deterministic_logic | deterministic output |
| test_developer_portal_forbidden_actions | anti-autonomy |

#### Anti-Inflation Boundary
- no API endpoint
- no frontend page
- no DB mutation
- no KPI values
- no Brain signal
- no event emission
- no autonomous execution
- no external provider call
- L3 only

### Module: federation_management

#### Current State
- Current Level: L2
- Target Level: L3
- Source: A-023.0
- Existing L2 evidence: deterministic contract skeleton and tenant guard
- Primary gap: FSM_workflow_missing

#### Intended L3 Scope
- What this module will do in A-026.10-RUNTIME: deterministic federation state transitions and policy checks.
- What this module will NOT do: no identity provider calls or autonomous sync execution.

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/federation_management/service.py | update | add deterministic federation FSM logic |

#### L3 Service Functions
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| evaluate_federation_management_readiness | classify federation readiness state | tenant_id, federation_payload | status/classification/risk/next_step/actions/evidence | yes | yes |

#### Domain Logic
- statuses: CONFIG_PENDING, VALIDATING, READY, BLOCKED
- classifications: READY_FOR_FEDERATION_REVIEW, NEEDS_CONFIG_EVIDENCE, HUMAN_REVIEW_REQUIRED
- risk/readiness levels: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_CONFIG, REQUEST_EVIDENCE, ESCALATE_REVIEW
- forbidden actions: AUTO_BIND_FEDERATION, AUTO_OVERRIDE_POLICY
- required evidence: idp_context, mapping_context, policy_context

#### Tenant Safety
- invalid tenant behavior: fail-closed
- valid tenant behavior: deterministic output
- tenant scope in output: required
- cross-tenant prevention: no cross-tenant federation linkage

#### Required Tests
| Test | Purpose |
|---|---|
| test_federation_import | import validation |
| test_federation_tenant_fail_closed | tenant guard |
| test_federation_fsm_determinism | deterministic transitions |
| test_federation_forbidden_actions | anti-autonomy/provider boundary |

#### Anti-Inflation Boundary
- no API endpoint
- no frontend page
- no DB mutation
- no KPI values
- no Brain signal
- no event emission
- no autonomous execution
- no external provider call
- L3 only

### Module: health_services

#### Current State
- Current Level: L2
- Target Level: L3
- Source: A-023.0
- Existing L2 evidence: deterministic contract skeleton and tenant guard
- Primary gap: FSM_workflow_missing

#### Intended L3 Scope
- What this module will do in A-026.10-RUNTIME: deterministic triage/readiness and escalation rules.
- What this module will NOT do: no medical action execution, no provider integration.

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/health_services/service.py | update | add deterministic health service readiness logic |

#### L3 Service Functions
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| evaluate_health_services_readiness | classify triage/review state | tenant_id, health_payload | status/classification/risk/next_step/actions/evidence | yes | yes |

#### Domain Logic
- statuses: INTAKE, REVIEW, READY, BLOCKED
- classifications: READY_FOR_SERVICE_REVIEW, NEEDS_CLINICAL_EVIDENCE, HUMAN_REVIEW_REQUIRED
- risk/readiness levels: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_CASE, REQUEST_EVIDENCE, ESCALATE_REVIEW
- forbidden actions: AUTO_DIAGNOSIS, AUTO_DISPATCH
- required evidence: case_context, consent_context, compliance_context

#### Tenant Safety
- invalid tenant behavior: fail-closed
- valid tenant behavior: deterministic output
- tenant scope in output: required
- cross-tenant prevention: no cross-tenant patient blending

#### Required Tests
| Test | Purpose |
|---|---|
| test_health_services_import | import validation |
| test_health_services_tenant_fail_closed | tenant guard |
| test_health_services_deterministic_logic | deterministic output |
| test_health_services_forbidden_actions | anti-autonomy/provider boundary |

#### Anti-Inflation Boundary
- no API endpoint
- no frontend page
- no DB mutation
- no KPI values
- no Brain signal
- no event emission
- no autonomous execution
- no external provider call
- L3 only

### Module: library_circulation

#### Current State
- Current Level: L2
- Target Level: L3
- Source: A-023.0
- Existing L2 evidence: deterministic contract skeleton and tenant guard
- Primary gap: FSM_workflow_missing

#### Intended L3 Scope
- What this module will do in A-026.10-RUNTIME: deterministic circulation lifecycle and hold/review readiness.
- What this module will NOT do: no autonomous checkout override or account mutation.

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/library_circulation/service.py | update | add deterministic circulation logic |

#### L3 Service Functions
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| evaluate_library_circulation_readiness | classify circulation state | tenant_id, circulation_payload | status/classification/risk/next_step/actions/evidence | yes | yes |

#### Domain Logic
- statuses: AVAILABLE, HOLD_PENDING, CHECKOUT_REVIEW, BLOCKED
- classifications: READY_FOR_CIRCULATION_REVIEW, NEEDS_ACCOUNT_EVIDENCE, HUMAN_REVIEW_REQUIRED
- risk/readiness levels: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_ACCOUNT, REQUEST_EVIDENCE, ESCALATE_REVIEW
- forbidden actions: AUTO_CHECKOUT_OVERRIDE, AUTO_FINE_OVERRIDE
- required evidence: account_context, hold_context, policy_context

#### Tenant Safety
- invalid tenant behavior: fail-closed
- valid tenant behavior: deterministic output
- tenant scope in output: required
- cross-tenant prevention: no shared patron records

#### Required Tests
| Test | Purpose |
|---|---|
| test_library_circulation_import | import validation |
| test_library_circulation_tenant_fail_closed | tenant guard |
| test_library_circulation_fsm_determinism | deterministic transitions |
| test_library_circulation_forbidden_actions | anti-autonomy |

#### Anti-Inflation Boundary
- no API endpoint
- no frontend page
- no DB mutation
- no KPI values
- no Brain signal
- no event emission
- no autonomous execution
- no external provider call
- L3 only

### Module: local_user_management

#### Current State
- Current Level: L2
- Target Level: L3
- Source: A-023.0
- Existing L2 evidence: deterministic contract skeleton and tenant guard
- Primary gap: tenant_guard_missing

#### Intended L3 Scope
- What this module will do in A-026.10-RUNTIME: deterministic user lifecycle/readiness logic with strict tenant isolation.
- What this module will NOT do: no autonomous provisioning, no cross-tenant identity operations.

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/local_user_management/service.py | update | add deterministic user state and tenant safety logic |

#### L3 Service Functions
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| evaluate_local_user_management_readiness | classify user lifecycle state | tenant_id, user_payload | status/classification/risk/next_step/actions/evidence | yes | yes |

#### Domain Logic
- statuses: NEW, VERIFIED, READY, BLOCKED
- classifications: READY_FOR_USER_REVIEW, NEEDS_IDENTITY_EVIDENCE, HUMAN_REVIEW_REQUIRED
- risk/readiness levels: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_USER, REQUEST_EVIDENCE, ESCALATE_REVIEW
- forbidden actions: AUTO_PROVISION_PRIVILEGED_USER, AUTO_CROSS_TENANT_LINK
- required evidence: identity_context, policy_context, access_context

#### Tenant Safety
- invalid tenant behavior: fail-closed
- valid tenant behavior: deterministic output
- tenant scope in output: required
- cross-tenant prevention: hard deny for cross-tenant references

#### Required Tests
| Test | Purpose |
|---|---|
| test_local_user_management_import | import validation |
| test_local_user_management_tenant_fail_closed | strict tenant guard |
| test_local_user_management_deterministic_logic | deterministic output |
| test_local_user_management_cross_tenant_forbidden | anti-cross-tenant boundary |

#### Anti-Inflation Boundary
- no API endpoint
- no frontend page
- no DB mutation
- no KPI values
- no Brain signal
- no event emission
- no autonomous execution
- no external provider call
- L3 only

### Module: research_grants

#### Current State
- Current Level: L2
- Target Level: L3
- Source: A-023.0
- Existing L2 evidence: deterministic contract skeleton and tenant guard
- Primary gap: FSM_workflow_missing

#### Intended L3 Scope
- What this module will do in A-026.10-RUNTIME: deterministic grant workflow readiness/risk classification.
- What this module will NOT do: no autonomous award decisions, no fund disbursement actions.

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/research_grants/service.py | update | add deterministic grant workflow logic |

#### L3 Service Functions
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| evaluate_research_grants_readiness | classify grant review state | tenant_id, grant_payload | status/classification/risk/next_step/actions/evidence | yes | yes |

#### Domain Logic
- statuses: DRAFT, UNDER_REVIEW, READY, BLOCKED
- classifications: READY_FOR_GRANT_REVIEW, NEEDS_APPLICATION_EVIDENCE, HUMAN_REVIEW_REQUIRED
- risk/readiness levels: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_GRANT, REQUEST_EVIDENCE, ESCALATE_REVIEW
- forbidden actions: AUTO_AWARD_GRANT, AUTO_APPROVE_COMPLIANCE
- required evidence: proposal_context, budget_context, compliance_context

#### Tenant Safety
- invalid tenant behavior: fail-closed
- valid tenant behavior: deterministic output
- tenant scope in output: required
- cross-tenant prevention: no cross-tenant grant mixing

#### Required Tests
| Test | Purpose |
|---|---|
| test_research_grants_import | import validation |
| test_research_grants_tenant_fail_closed | tenant guard |
| test_research_grants_fsm_determinism | deterministic transitions |
| test_research_grants_forbidden_actions | anti-autonomy boundary |

#### Anti-Inflation Boundary
- no API endpoint
- no frontend page
- no DB mutation
- no KPI values
- no Brain signal
- no event emission
- no autonomous execution
- no external provider call
- L3 only

### Module: student_ai_tutor

#### Current State
- Current Level: L2
- Target Level: L3
- Source: A-023.0
- Existing L2 evidence: deterministic contract skeleton and tenant guard
- Primary gap: FSM_workflow_missing

#### Intended L3 Scope
- What this module will do in A-026.10-RUNTIME: deterministic tutoring readiness and human-review routing logic.
- What this module will NOT do: no model/provider execution, no autonomous tutoring actions.

#### Expected Runtime Files
| File | Action | Purpose |
|---|---|---|
| backend/app/modules/student_ai_tutor/service.py | update | add deterministic tutor readiness/risk logic |

#### L3 Service Functions
| Function | Purpose | Input | Output | Deterministic | Tenant-Safe |
|---|---|---|---|---|---|
| evaluate_student_ai_tutor_readiness | classify tutoring readiness state | tenant_id, tutor_payload | status/classification/risk/next_step/actions/evidence | yes | yes |

#### Domain Logic
- statuses: INTAKE, PREPARED, REVIEW_REQUIRED, BLOCKED
- classifications: READY_FOR_TUTOR_REVIEW, NEEDS_LEARNING_EVIDENCE, HUMAN_REVIEW_REQUIRED
- risk/readiness levels: LOW/MEDIUM/HIGH and READY/PENDING/BLOCKED
- allowed actions: REVIEW_CONTEXT, REQUEST_EVIDENCE, ESCALATE_REVIEW
- forbidden actions: AUTO_GENERATE_LEARNING_PLAN, AUTO_EXECUTE_PROVIDER_CALL
- required evidence: learner_context, policy_context, consent_context

#### Tenant Safety
- invalid tenant behavior: fail-closed
- valid tenant behavior: deterministic output
- tenant scope in output: required
- cross-tenant prevention: no learner profile blending

#### Required Tests
| Test | Purpose |
|---|---|
| test_student_ai_tutor_import | import validation |
| test_student_ai_tutor_tenant_fail_closed | tenant guard |
| test_student_ai_tutor_deterministic_logic | deterministic output |
| test_student_ai_tutor_provider_boundary | no provider call/no autonomy |

#### Anti-Inflation Boundary
- no API endpoint
- no frontend page
- no DB mutation
- no KPI values
- no Brain signal
- no event emission
- no autonomous execution
- no external provider call
- L3 only

### Expected A-026.10 Runtime Files

| File | Expected Action | Reason |
|---|---|---|
| backend/app/modules/accreditation_compliance/service.py | update | deterministic L3 accreditation logic |
| backend/app/modules/ai_cost_governance/service.py | update | deterministic L3 cost governance logic |
| backend/app/modules/ai_plagiarism/service.py | update | deterministic L3 plagiarism logic |
| backend/app/modules/conference_management/service.py | update | deterministic L3 conference logic |
| backend/app/modules/contracts_legal_repository/service.py | update | deterministic L3 legal contract logic |
| backend/app/modules/counseling_case_management/service.py | update | deterministic L3 case logic |
| backend/app/modules/developer_portal/service.py | update | deterministic L3 developer readiness logic |
| backend/app/modules/federation_management/service.py | update | deterministic L3 federation FSM logic |
| backend/app/modules/health_services/service.py | update | deterministic L3 health service logic |
| backend/app/modules/library_circulation/service.py | update | deterministic L3 circulation logic |
| backend/app/modules/local_user_management/service.py | update | deterministic L3 tenant-safe user logic |
| backend/app/modules/research_grants/service.py | update | deterministic L3 grants logic |
| backend/app/modules/student_ai_tutor/service.py | update | deterministic L3 tutor readiness logic |
| backend/tests/test_a02610_final_l2_to_l3_deterministic_service_logic.py | add | targeted final L2->L3 test suite |
| SBS_UB.md | update in runtime | tracker reconciliation after runtime evidence |
| SBS_UB_150_MODULE_NORMALIZATION.md | update in runtime | row-level L2->L3 movement after PASS validation |
| A-026.10-RUNTIME-FINAL_L2_TO_L3_DETERMINISTIC_SERVICE_LOGIC_REPORT.md | add in runtime | authoritative runtime evidence report |

### A-026.10 Targeted Test Plan

Preferred test file:
- backend/tests/test_a02610_final_l2_to_l3_deterministic_service_logic.py

Test groups:
1. import validation
2. tenant fail-closed validation
3. deterministic output validation
4. classification/status/risk logic
5. required evidence validation
6. allowed/forbidden action validation
7. provider boundary validation where relevant
8. anti-inflation validation
9. no API/frontend/Brain/KPI behavior

Expected test count:
- 80-140 tests acceptable for all 13 modules

Validation mode:
- fast direct Docker validation mode

Preferred fast Docker command:

```bash
cd /home/sbs/AI

docker run --rm \
   --env-file /home/sbs/AI/infra/.env \
   -v /home/sbs/AI/backend/app:/app/app \
   -v /home/sbs/AI/backend/tests:/app/tests \
   -w /app \
   ai-backend-tests:latest \
   python -m pytest -q \
   tests/test_a02610_final_l2_to_l3_deterministic_service_logic.py \
   -o addopts='' \
   --no-cov \
   -rA \
   --durations=30
```

Continuity target:
- include A-026.3 through A-026.10 suites

### Expected Maturity Movement

Current (spec-time, unchanged):
- L0=0
- L1=0
- L2=13
- L3=42
- L4=68
- L5=25
- L6=2

If Option A (N=13) passes in runtime:
- L0=0
- L1=0
- L2=0
- L3=55
- L4=68
- L5=25
- L6=2
- total=150
- maturity_arithmetic_check=PASS

Spec-phase rule:
- no maturity movement in A-026.10-SPEC

### Anti-Inflation Boundaries

- no runtime code changes in this spec
- no test implementation in this spec
- no API/router/schema/frontend additions
- no DB migrations/mutations
- no KPI/Brain/autonomy claims
- no L4/L5/L6 overclaim

### Definition of Done for Future A-026.10-RUNTIME

- remaining L2 extraction stays at 13 unless matrix changes are explicitly approved
- selected 13 modules are implemented with deterministic L3 service logic and tenant fail-closed safety
- targeted suite passes in fast Docker mode
- continuity suite (A-026.3 through A-026.10) passes
- no API/frontend/KPI/Brain/autonomy overclaim appears in runtime artifacts
- SBS_UB.md and matrix rows update only after implementation plus validation

- VERIFICATION_PENDING must be used where direct evidence is not yet attached.
- This file does not replace SBS_UB.md authority; it supports execution planning only.
