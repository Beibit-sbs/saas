# SBS UB — DUPLICATION & CONTRADICTION REGISTER (TASK 4)

Date: 2026-06-19 · Mode: read-only registration. NOTHING deleted/merged in Phase A.
Policy: register now → pick canonical → consolidate later as scoped slices with compatibility + regression. No wholesale refactor of working code in one pass.

## 1. Semantic duplication families (modules)

| ID | Family / conflict | Modules involved | Likely canonical | Conflict type | Resolution (staged) | Risk | Status |
|---|---|---|---|---|---|---|---|
| D-01 | Academic Operations split | `academic_operations` (has router, 40 routes) + `academic_operations_runtime` (no router.py) | `academic_operations` | Two modules, one domain; `_runtime` may be a partial/dead shell | Confirm `_runtime` consumers; if none, deprecate; else fold into base | Med (cert vertical V03) | REGISTERED |
| D-02 | Research family | `research`, `research_science`, `research_projects`, `research_grants`, `research_ethics`, `innovation_commercialization` | `research_science` (cert closure A-047.13) | Overlapping research entities; A-053 innovation superseded | Map entity ownership; innovation_commercialization is superseded+UNTRACKED → drop-or-fold | Med | REGISTERED |
| D-03 | Accreditation family | `quality_accreditation` (cert A-050.15), `accreditation`, `accreditation_compliance`, `accreditation_dashboard` | `quality_accreditation` | 4 modules, one domain | Treat `accreditation*` as sub-surfaces of quality_accreditation; verify no duplicate tables | Med | REGISTERED |
| D-04 | HR payroll | `hr_payroll`, `hr_payroll_integration`, `hr_staff_governance` | `hr_staff_governance` (cert A-039) | core vs integration-adapter vs governance | Keep integration as adapter; ensure single payroll entity owner | Low | REGISTERED |
| D-05 | Student services | `student_services`, `student_services_support` | `student_services_support` (A-042 closure + active A-055 tree) | Two modules, one domain | `student_services` likely legacy → verify consumers, deprecate | Med | REGISTERED |
| D-06 | Document workflow | `document_workflow`, `document_workflow_os`, `workflows`, + 9 `*_workflow` modules | `document_workflow_os` (?) needs confirm | Two doc-workflow modules + workflow sprawl | Pick one doc-workflow canonical; unified approval layer is a later consolidation | High (many consumers) | REGISTERED |
| D-07 | Notification / communications | `communications`, `notification_center`, `notification_gateway_integration`, `mobile_push_gateway`, `parent_engagement` | `communications` (active V15 / A-054 consolidation) | 5 modules for one comms domain | A-054 wave IS the consolidation; finish it, fold the others as adapters | Med | IN PROGRESS (A-054) |
| D-08 | Identity / access | `auth`, `identity`, `access_control`, `rbac`, `local_user_management`, `service_accounts` + adapters `ldap`,`sso_saml`,`identity_provider_integration`,`two_factor_auth` | `auth`+`rbac`+`identity` core; rest adapters | Possible overlapping identity models | Define single identity/tenant context (TASK 10.1) BEFORE merging; adapters stay | High (security) | REGISTERED |
| D-09 | Audit trail | `audit` (shared), `brain_decision_audit_trail` (brain), `degree_audit` (academic — NOT a dup) | `audit` shared | Brain has separate audit path | Ensure brain audit writes through shared `audit` contract | Med | REGISTERED |

## 2. Contradictions (docs vs reality)

| ID | Contradiction | Evidence | Resolution | Priority | Status |
|---|---|---|---|---|---|
| C-01 | Admissions CRM (V12) marked closed (A-045.4.B1) but **code UNTRACKED in git** | snapshot: `backend/app/modules/admissions_crm/`, migration `acrm0452rt01`, 5 tests all `??` | Git reconciliation: verify tests pass, then commit as evidence-gated slice (NOT `git add .`) | **P1** | OPEN |
| C-02 | Index docs say active wave = A-026 (May) but reality = A-055 (Jun) | SBS_UB_ACTIVE_WAVE/ROADMAP/MODULE_INVENTORY vs git log | Tracker normalization (TASK 10): mark stale, point to SBS_UB.md + GLOBAL-ROADMAP-R3 | P2 | OPEN |
| C-03 | Closure reports claim PASS but tests were red-on-commit | finance `_models.py`/`_audit_evidence_security.py` were red (route 53/perm 48) — fixed A-055.29; quality FE 19→27; security/campus/ddc missing testids | Re-verification pass per vertical; fix stale assertions (evidence-gated) | P2 | PARTIAL (finance done) |
| C-04 | Innovation/Commercialization (A-053) audit-only + superseded + **UNTRACKED** | snapshot; A-053.x AUDIT reports, no closure | Decide drop vs fold into research; do not count as vertical | P2 | OPEN |

## 3. Safe consolidation protocol (applies to all D-entries)

1. Confirm canonical implementation by consumers (grep imports/routes), not by name.
2. Build compatibility layer if the legacy interface has live consumers.
3. Migrate consumers.
4. Add regression tests.
5. Only then deprecate; delete only when zero usage proven.
6. Any DB/table merge → migration + HUMAN_REVIEW_REQUIRED if it touches existing data.

## 4. Phase A verdict on duplication

Duplication is REAL and structural (notification ×5, identity ×6+, research ×6, accreditation ×4, two academic_operations, two student_services). It is NOT fixable in one pass and MUST NOT be force-merged. Recommended: unify the **notification family (already in progress, A-054)** and resolve the **two git-untracked verticals (C-01, C-04)** first; defer identity/workflow consolidation to dedicated scoped efforts.
