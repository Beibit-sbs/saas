# SBS UB — AUTHORITATIVE SYSTEM EVIDENCE INVENTORY (TASK 2)

Date: 2026-06-19 · Mode: read-only · Altitude: per product vertical (not per-module; 241 backend modules roll up into these).

Status legend: CLOSED_WITH_EVIDENCE · RUNTIME_VERIFIED · PARTIAL_RUNTIME · ACTIVE_RUNTIME · SPEC_COMPLETE · DOCS_ONLY · DUPLICATED · BLOCKED_CODE · BLOCKED_EXTERNAL.
"Evidence" = closure/cert report + tracked code + tests. Statuses are cross-checked against code on disk, not taken from docs alone.

## A. Canonical source-of-truth (TASK 1 result)

- Authoritative tracker: **SBS_UB.md** (control center; per-brain vertical_status / next_action_id).
- Latest strategic decision: **GLOBAL-ROADMAP-R1/R2/R3** (2026-06-16): strict strong_closed = 9/20, CONTINUE_VERTICAL_CLOSURE, next = Communications.
- Target architecture map: **NATIONAL_UNIVERSITY_OS_TREE.md** (24 layers, candidate families). *(untracked — see snapshot)*
- Strategic policy: **SBS_UB_STRATEGIC_EXECUTION_POLICY_20_STRONG_VERTICALS_BEFORE_PRODUCTION.md**. *(untracked)*
- STALE / non-authoritative (describe May A-026, reality is A-055): SBS_UB_ACTIVE_WAVE / COMPLETED_WAVES / ROADMAP / MODULE_INVENTORY / EVIDENCE_INDEX.

## B. Vertical evidence matrix

| V | Vertical | Backend module(s) | Git | BE tests | Closure/cert report | Status | Notes / problems |
|---|---|---|---|---|---|---|---|
| V01 | Executive Governance | executive_governance, executive_control_tower | tracked | yes | A-034 chain / A-048 brain | CLOSED_WITH_EVIDENCE | closure evidence historical; not re-verified this session |
| V02 | Student Lifecycle | student_lifecycle, students | tracked | yes | A-035.5-B1 / A-051 brain | CLOSED_WITH_EVIDENCE | historical |
| V03 | Academic Operations | academic_operations (+ academic_operations_runtime) | tracked | 7 | A-036.5-B1 / A-052.16 cert | CLOSED_WITH_EVIDENCE | **dup pair**: `_runtime` has no router.py → see register D-01 |
| V04 | Research / Science | research_science (+ research, research_projects…) | tracked | 4 | A-037.5-B1 / A-047.13 cert | CLOSED_WITH_EVIDENCE | **research family** = several modules → register D-02 |
| V05 | Quality / Accreditation | quality_accreditation (+ accreditation×3) | tracked | 5 | A-038.5-B1 / A-050.15 cert | CLOSED_WITH_EVIDENCE | accreditation dup family D-03; FE test drift (route 19→27) — P2 |
| V06 | HR / Staff Governance | hr_staff_governance (+ hr_payroll×2) | tracked | yes | A-039.5-B1 | CLOSED_WITH_EVIDENCE | hr_payroll dup family D-04 |
| V07 | Finance / Procurement / Asset | finance_procurement_asset | tracked | 5+ | A-040.5-B1 | RUNTIME_VERIFIED | **re-verified this session** (52 backend pass after fixing red models/security tests in A-055.29) |
| V08 | Document / Decree / Correspondence | document_decree_correspondence | tracked | yes | A-041.5-B1 | CLOSED_WITH_EVIDENCE | FE `ddc-audit-timeline` testid missing — P2 |
| V09 | Student Services / Welfare | student_services_support (+ student_services) | tracked | 4 | A-042.5-B1 | RUNTIME_VERIFIED | re-verified (A-055 tree); dup vs `student_services` D-05 |
| V10 | Security / Access / Compliance | security_access_compliance | tracked | yes | A-043.5-B1 | CLOSED_WITH_EVIDENCE | FE `sac-permission-denied-panel` testid missing — P2 |
| V11 | Campus / Facilities / Housing / Transport | campus_facilities_housing_transport | tracked | yes | A-044.5-B1 | CLOSED_WITH_EVIDENCE | FE `campus-facilities-permission-denied` testid missing — P2 |
| V12 | Admissions / Recruitment / Yield | admissions_crm | **UNTRACKED** | 5 | A-045.4.B1 closure | BLOCKED_CODE (git) | **code + migration + 5 tests NEVER committed** → P1 git reconciliation |
| V13 | Integration / Provider Readiness | integration_provider_readiness | tracked | yes | A-046 chain | PARTIAL_RUNTIME | per R1/R2: readiness/governance lane, not strict-strong |
| V14 | Library / Archive / Knowledge | library, library_circulation, knowledge_retrieval | tracked | partial | candidate pool | PARTIAL_RUNTIME | open candidate family |
| V15 | Communications / Notification / Community | communications, notification_center, mobile_push_gateway | tracked | **0 dedicated** | A-054.1–.9 (active chain) | ACTIVE_RUNTIME | current wave; only platform/brain notif tests exist → dedicated tests gap |
| V16 | Data Platform / Analytics / KPI | analytics, reporting_runtime | tracked | partial | candidate pool | PARTIAL_RUNTIME | missing data_catalog/kpi_certification (see memory gaps) |
| V17 | AI Brain Core | brain_core | tracked | 12 | A-048 chain | RUNTIME_VERIFIED (largest test surface) | governance console partial |
| V18 | Infrastructure / Ops / SRE | observability, platform_health, backup | tracked | yes | candidate pool | PARTIAL_RUNTIME | open candidate family |
| V19–V25 | Career/Alumni, LMS, Exam, Legal, Ministry, Medical, Integrity | various (alumni, lms_*, exam_*, contracts_legal_*, ministry_*, …) | tracked | varies | A-045.0-SPEC only | SPEC_COMPLETE / PARTIAL | not closed; some have runtime modules but no closure chain |
| — | Innovation / Commercialization (A-053) | innovation_commercialization | **UNTRACKED** | 0 | A-053.x AUDIT only (superseded) | DEPRECATED/UNTRACKED | superseded extension over Research; code uncommitted → P1 reconcile-or-drop |

## C. Honest aggregate

- Strict strong-closed: **9/20** (per GLOBAL-ROADMAP-R2). ~55% to production target.
- **Re-verified by me this session:** V07 Finance only (full backend green after fixing latent red tests). All other "closed" verticals rely on HISTORICAL closure evidence not re-run this session — and finance proved closure evidence can drift, so treat historical CLOSED_WITH_EVIDENCE as "closed-at-the-time, re-verification pending."
- **Git ≠ code reality:** V12 Admissions CRM and A-053 Innovation are on disk but uncommitted → the single most concrete integrity gap.

## D. Coverage vs maturity (honest split)

| Dimension | State |
|---|---|
| Functional coverage (code exists) | high (241 backend / 81 FE modules) |
| Runtime verification (tests run THIS session) | low — only finance fully re-verified |
| Security verification | not run this session (BLOCKED until Phase C) |
| Operational readiness (Docker/E2E) | unverified here (docker-only FE; likely BLOCKED_EXTERNAL in this env) |
| Production readiness | NO — 9/20, latent test debt, git unreconciled |
| AI/Brain maturity | partial — brain_core present + human-gated; cross-vertical wiring is the A-055 tree (in progress) |
