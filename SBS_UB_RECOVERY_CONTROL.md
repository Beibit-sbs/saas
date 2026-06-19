# SBS UB — RECOVERY CONTROL (focus spine)

> This is the SHORT always-current control file. Re-read this first to reorient.
> Detailed outputs live in the other SBS_UB_FULL_RECOVERY_*.md artifacts.
> Update this after EVERY slice. Keep it short.

## Continuation state

- current_phase: **Recovery COMPLETE (PASS_WITH_NOTES); resumed A-055 tree**
- current_recovery_action: none — tree mode (last: A-055.30 commit 9771a195)
- next_exact_action: A-055.31 (type FpaBridgeResponse.records on frontend + live-render acknowledgement list) OR a deferred recovery item (D-07 notification consolidation / C-04 decision). User-driven.
- mode_gate: evidence-gated commits only; no `git add .`.
- recovery_commits: 7777b4f8, 6a6b0374, c9270408, 2adbd818, c290b467 (verdict PASS_WITH_NOTES; see SBS_UB_FULL_RECOVERY_VERIFICATION_REPORT.md).
- tree_commits_after_recovery: 9771a195 (A-055.30), 1993b497 (A-055.31).
- NOTE: finance student-finance referral area SATURATED (.27-.31). Pivoted to D-07.
- D-07 DONE (commit 0472fce1): recon CORRECTED the ×5 over-count → 1 canonical (communications) + 1 superseded (notification_center, now deprecation-signalled) + 1 used-adapter (notification_gateway_integration) + 2 intentional L2 stubs (mobile_push_gateway, parent_engagement — do NOT remove). notification_center route removal = deferred deprecation cycle.
- D-05 DONE (commit bb5384b1): NOT a duplicate (tickets surface vs welfare vertical, both active). No code change.
- META-FINDING: 2/2 dup recons (D-07, D-05) REFUTED the duplicate framing. The Phase-A dup register was name-stem heuristic, not deep code analysis; most "families" are intentional L2 stubs / adapters / distinct surfaces. Codebase is LESS duplicated than names imply. Evidence-first prevented 2 harmful merges.
- D-08 DONE (commit 55270d7f): SECURITY — single canonical user store (auth LocalUserStore -> app_local_users); identity=federation only; NO split-brain. Not duplicated.
- 3/3 dup recons (D-07/D-05/D-08) refuted the name-stem dup framing (register section 8). Conclusion: dup backlog is mostly non-issues; only real item was notification_center (deprecation-signalled). Remaining families (D-02/03/04/06/09) likely same shape; recon cheaply IF needed before any merge, never force-merge.
- Faculty/Teaching branch: VERIFIED SOLID (34 backend + 34 frontend tests pass; modules compile; NO latent breakage). It is already a comprehensive vertical (faculty CRUD/contracts/workload/teaching-quality/capacity/proctoring/office-hours/brain-context) — like finance, it is SATURATED; adding micro-nodes here is low value.
- DIGITAL TWIN STARTED (A-056.1, commit 87822451): new `digital_twin` module — read-only backend shell (GET /state, /safety-boundaries), reuses existing 5 signal registries + 6 capacity modules (no duplication), safety-bounded (no autonomy/hidden-scoring), tenant fail-closed, 11 tests pass. NO DB store / NO fake metrics at shell stage.
- A-056.2 DONE (commit dee49f41): Digital Twin FRONTEND shell — /console/digital-twin page + nav + DIGITAL_TWIN_STATE_READ permission + test, all committed together (no dead-link). Full-stack read-only shell now complete.
- A-056.3 DONE (commit 256a8d05): Digital Twin FIRST REAL computation — deterministic capacity what-if (POST /simulate/capacity, new digital_twin.simulate.run perm, route 3). Computes projected_students/classroom_util/dorm_pressure/risks on real inputs, evidence-tagged to source modules, incomplete_data when source missing (never guessed), human-gated, viewer-denied, fake_metrics=false. 15 backend + 1 frontend tests pass.
- A-056.4 DONE (commit 60d7a878): Digital Twin reads LIVE enrollments for current_students (use_live_sources, best-effort + honest fallback, evidence mode live/caller_provided, no new route/permission). 17 backend + 1 frontend tests pass. Cross-module coupling is service-level only, try/except wrapped.
- A-056.5 DONE (commit 1a6800c5): Digital Twin EARLY WARNING — POST /early-warning/capacity (route 4) classifies capacity ratios into high/medium warnings with recommended human actions (escalate_to_scheduling_and_facilities / escalate_to_housing_office), requires_human_approval, no autonomy; signal registries declared as candidate sources (NOT fabricated counts). 20 backend + 1 frontend tests pass. Note: student_risk registry is a governance/contract module (no live signal counts) — do NOT fabricate counts; wire real signal instances only if/when they exist.
- A-056.6 DONE (commit 6fd733d1): Digital Twin named what-if SCENARIO REGISTRY — POST /scenarios/capacity (route 5) runs baseline/+10/+20/+30 side by side for executive review, each with projection+warnings, reuses early-warning. 22 backend + 1 frontend tests pass.
- A-056.7 DONE (commit 8fac5f59): Digital Twin reads LIVE classroom_capacity = sum(campus_rooms.capacity) via shared list_entities_for_tenant (best-effort, evidence mode=live/source=campus_rooms, honest fallback). Propagates to early-warning + scenarios. 23 backend + 1 frontend tests pass. No route/perm/schema change.
- A-056.8 DONE (commit 09bf98c6): audited human scenario DECISION — POST /scenarios/decision (new digital_twin.decision.record perm, route 6). Records accepted/rejected/deferred to the REAL audit trail via audit.log_admin_action -> app_audit_events (no new table/migration — a decision IS an audit record), no_autonomous_execution, invalid->422, viewer denied. 26 backend + 1 frontend tests pass. Closes #21 loop.
- Digital Twin arc (.1-.8) COMPLETE end-to-end: observe -> deterministic compute -> live enrollments -> warn -> executive scenarios -> live room capacity -> audited human decision. Full #21 principle realised on REAL data, no autonomy/fake-metrics. THE FULL PRINCIPLE: Brain sees / twin simulates / workflow proposes / human approves / audit records.
- A-056.9 DONE (commit 3fb1cdee): executive decision LOG read-back — GET /scenarios/decisions (route 7) reads recorded decisions back from the audit trail (audit.list_admin_actions filtered to the decision action). Closes the decision loop both ways. 28 backend + 1 frontend tests pass.
- Digital Twin arc (.1-.9) COMPLETE with a closed reviewable decision loop. 9 nodes, route 7 / perm 4, all on REAL data, no autonomy/fake-metrics. THE full #21 principle end-to-end.
- A-056.R1 DONE (commit e1a5fb67): multi-agent ADVERSARIAL REVIEW of A-056.1-.9 (Ultracode workflow) -> 23 findings, 15 confirmed (8 refuted), ALL FIXED. Notable: non-finite input (inf/nan) was a real 500 (now clean 400 via service _validate_finite + router _guard, because a pydantic 422 echoing inf fails Starlette json serialisation); F10 was a real PROD-ACCESS gap (digital_twin perms granted to NO role -> 403 + hidden nav -> fixed in rbac/service union); least-privilege decision.read perm; tenant fail-closed proven on all 7 routes (42 cases). Verified: inf->400 6, classroom 3, fail-closed 42, non-slow 41, frontend 1, tsc clean, rbac additive.
- A-056.10 DONE (commit 66f058f4): second twin DOMAIN — resource-consumption what-if (/simulate/resource, /early-warning/resource; route 7->9). Deterministic days-of-stock + reorder/stockout warning with human action; R1 hardening baked in (finite validation->400, fail-closed, no-audit, viewer denied). 20 resource tests pass.
- A-056.R2 DONE (commit b0695d36): resource-domain adversarial review -> 3 findings, ALL 3 confirmed, all fixed. R2-F1 (HIGH): current_stock=NaN -> 500 was the R1 bug class RE-INTRODUCED via Field(ge=0) (NaN<0 -> pydantic 422 echoing NaN -> Starlette serialise fail -> 500); fix = plain float + _validate_finite. R2-F3 (HIGH): stock/tiny-consumption -> inf days -> 500; fix = math.isfinite guard on quotient. R2-F2 (LOW): classify on raw quotient not rounded. 25 resource tests pass.
- META-LESSON: per-node adversarial review caught a HIGH bug I had just hardened in R1 and re-introduced. Run the Ultracode review loop on EVERY new node. Both twin domains (capacity, resource) now adversarially reviewed + hardened.
- A-056.11 (live resource stock) NOT DONE — HONEST BLOCKER: asset_inventory models individual assets (asset_inventory_items: asset_code/name/category/...), NOT consumable stock levels; no clean current_stock source. Anti-fake: do NOT fabricate stock from item counts. Resource live-wire deferred until a real stock-level source exists.
- DONE (commit de918504): adversarial review of SHIPPED finance-office referral chain (A-055.26-.31) found 13 -> 8 confirmed. THE BIG ONE: the A-055.29 acknowledge endpoint returned HTTP 500 on EVERY authorized call (wrote to a non-existent MODEL_BY_FAMILY key -> KeyError) AND its ledger could never populate. It shipped "green" because the only test asserted viewer->403 (denied before the service runs) — the success path was NEVER exercised. Fixed: write FinanceBridgeRecord via family="bridges" + bridge_family="student_finance_referrals" (the value GET filters on) + metadata + anti-fake flags on response + positive regression test. Finance api 20 passed. F8 (status-transition validator in 3 hardship handlers, LOW) deferred.
- META-LESSON (now a project rule): EVERY write endpoint needs an authorized-SUCCESS test, not just an RBAC-denial test; a denial-only test gives false green on a 100%-broken endpoint. Ultracode adversarial review on shipped code found a real prod bug in my own A-055.29 work that conventional testing missed.
- DONE (commit 8be8fe06): adversarial review of hardship write chain (A-055.20-.27) -> 16, 9 confirmed (7 refuted -> security/anti-fake/tenant/RBAC posture is SOUND). Real defect: hardship status transitions unguarded -> a write-authorized caller could record a finance-office referral DIRECTLY on a readiness_evaluated hardship, SKIPPING the human-review gate (audit-integrity hole), re-mutate terminal state, evidence-gap after referral. Fix: _HARDSHIP_ALLOWED_TRANSITIONS + _validate_hardship_transition on the 3 handlers (referral now requires human_review_outcome_recorded first) + 3 rejection tests. 19 services tests pass. Deferred (documented): JSONB integration test (F2/6), HTTP-level tests (F4/5), reviewer-queue terminal exclusion (F7).
- DONE (commit 36ae8a3e): adversarial review of grades write + GPA/transcript read chain -> 15, 11 confirmed (4 refuted -> tenant scoping SOUND). 2 HIGH: (A) calculate_student_gpa / get_student_transcript / TranscriptService._load_enrollments had NO enrollment-status filter, yet grade_code/grade_points are RETAINED on drop/withdraw -> a graded-then-dropped enrollment corrupted GPA + transcript; (B) change_grade enforced NEITHER the term-window NOR section-cancelled guard that submit_grade does -> a regrade could rewrite a closed-term/cancelled-section grade. Fix: _NON_CREDIT_BEARING_STATUSES=(DROPPED,WITHDRAWN) NOT IN filter on all 3 aggregations; change_grade now calls _check_section_not_cancelled + _check_term_submission_window_open. + 3 new tests, 2 updated. ALSO fixed a pre-existing RED test (test_get_student_transcript_records_read_usage, failing on clean HEAD: stale execute.side_effect ordering). grades 11/11 + transcripts 7/7 pass. Deferred (documented): idempotent-replay skips new guards F4/11, transcript-GET-writes F7, create_grading_scale no test F9, ABAC binding F10.
- 5 adversarial reviews this session, ALL found real bugs conventional tests missed: capacity R1 (15/23: inf->500, prod-access RBAC gap), resource R2 (3/3: NaN->500 reintroduced, overflow->500), finance REF-R1 (8/13: acknowledge 100% broken 500 + empty ledger), hardship HSP-R1 (9/16: human-review gate bypassable), grades GRD-R1 (11/15: dropped grades corrupt GPA/transcript + change_grade bypasses census lock). Reusable loop: build/inspect -> review-workflow (dims -> adversarial verify, default-refute) -> remediate + negative tests -> commit. THE recurring lesson: structure/happy-path tests give false green; every write/state-machine AND read aggregation needs positive-success AND negative (out-of-order/edge/post-mutation) tests.

## DONE — P2 remaining + C-02 (commit 2adbd818 + docs) ✅
- R-P2-04 DDC timeline: REAL gap (component never rendered) — wired. 6 tests pass.
- R-P2-05 quality self-assessment: REAL gap (anti-fake boundary label dropped) — restored. 39 quality tests pass.
- ALL 6 structural frontend regression failures now green.
- C-02: 5 stale index docs (ACTIVE_WAVE/ROADMAP/COMPLETED_WAVES/MODULE_INVENTORY/EVIDENCE_INDEX) got dated RECOVERY CORRECTION markers → authoritative sources; history preserved.

## DONE — P2 partial (commit c9270408) ✅
- Fixed 4 latent frontend failures (locale-independent, real): quality 19→27, quality audit-findings brittle matcher, security permission-denied testid drift, campus permission-denied missing module testid. 20 tests pass.
- Remaining (queued, classified): R-P2-04 DDC timeline (REAL — unrendered component), R-P2-05 quality self-assessment (brittle/async). Locale-only host failures = NOT defects (docker-only).

## DONE — P1 (git-state reconciliation) ✅
- R-P1-01 Admissions CRM (commit **7777b4f8**): root cause = missing include_router in main.py. Wired + committed module+migration+5 tests. Evidence: 75 pass (was 73/2); app-surface 9 pass/3 skip.
- R-P1-02 Innovation (commit **6a6b0374**): committed main.py imported an UNTRACKED module = **broken bootstrap P0**. Committed shell module+frontend to restore import integrity. Keep-vs-retire = product decision (C-04 still open as product, not integrity).
- R-P1-03 systematic check: ALL `from app.modules.X` imports in main.py now resolve in git (verified). No other broken-bootstrap remain.

## R-P1-01 finding (Admissions CRM)

- admissions_crm is FULLY implemented, module tests pass: **73 passed / 2 failed**.
- The 2 fails = `test_route_inventory_exact_12`, `test_route_methods_distribution` → KeyError on `/api/admin/admissions-crm/leads` because the router is NOT mounted in main.py (no import/include_router anywhere; verified by grep + app.routes probe).
- Prefix `/api/admin/admissions-crm` (distinct from old `admissions` — no collision). Migration `acrm0452rt01` chains from tracked `cfht0442rt01` (A-044) — chain intact.
- Frontend `admissions-crm` module is TRACKED (committed) but backend was not → split-brain. Root cause = missing main.py wiring.

## Completed (this recovery)

- TASK 0 snapshot → `SBS_UB_FULL_RECOVERY_SOURCE_SNAPSHOT.md`
- TASK 1 canonical docs → folded into evidence inventory §A
- TASK 2 evidence inventory → `SBS_UB_AUTHORITATIVE_SYSTEM_EVIDENCE_INVENTORY.md`
- TASK 4 duplication+contradiction register → `SBS_UB_DUPLICATION_AND_CONTRADICTION_REGISTER.md`

## Proposed recovery queue (draft — for Phase B/C)

- P1: C-01 Admissions CRM git reconciliation (untracked vertical) · C-04 innovation untracked decision
- P2: C-03 stale-test re-verification per vertical (quality FE 19→27, security/campus/ddc missing testids) · C-02 tracker normalization
- P3: D-01..D-09 duplication consolidation (staged, compatibility-first) — defer, register only
- P0: none found yet (app builds; finance green; no detected leakage/RBAC bypass) — to be confirmed when backend boots in Phase C

## Verified facts (carry forward — do NOT re-derive)

- Branch `main`, HEAD `1bbea518` (A-055.29). Only 3 modified tracked files = junk (`.coverage` x2, `.vscode/tasks.json`).
- Frontend tests = **vitest, docker-only**. Host vitest gives FALSE failures on locale (ru host: `950 000` vs `950,000`). Real failures = structural only.
- Backend tests via `backend/.venv/bin/pytest`, slow (~2min/file), no background-pipe output (run to a file).
- Full host vitest (2026-06-19): 291 files / 1716 tests, 14 fails — ALL in non-A-055 modules (locale + pre-existing drift). A-055 tree is green.
- Latent test debt pattern: prior waves committed WITHOUT running tests. Confirmed red-on-commit: finance `_models.py` + `_audit_evidence_security.py` (route 53/perm 48 stale) — FIXED in A-055.29. Quality route 19→27 drift, security/campus missing testids — NOT yet fixed (other verticals).
- **Untracked whole-vertical code (git ≠ reality):** `backend/app/modules/admissions_crm/` (V12) + migration `acrm0452rt01` + 5 tests; `backend/app/modules/innovation_commercialization/` (A-053); frontend `academic-terms`, `innovation-commercialization`. These are NOT junk.

## do_not_repeat

- Don't re-run full git status discovery (done, see snapshot).
- Don't re-build module inventory (241 backend / 81 frontend — see memory `sbs-ub-module-inventory-gaps`).
- Don't re-read the whole NATIONAL_UNIVERSITY_OS_TREE / SBS_UB.md control block (already mapped: 9/20 strong, A-055 tree active).
- Don't run host vitest expecting locale-number tests to pass.

## Commits created (this recovery)

- none yet (Phase A is read-only).

## documents_to_read_before_continuation

- This file → `SBS_UB_FULL_RECOVERY_SOURCE_SNAPSHOT.md` → `SBS_UB_AUTHORITATIVE_SYSTEM_EVIDENCE_INVENTORY.md` (in progress).
- Memory: `project-sbs-ub-overview`, `sbs-ub-current-focus-tree`, `sbs-ub-module-inventory-gaps`, `sbs-ub-doc-source-of-truth`.
