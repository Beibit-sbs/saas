# SBS UB — RECOVERY CONTROL (focus spine)

> This is the SHORT always-current control file. Re-read this first to reorient.
> Detailed outputs live in the other SBS_UB_FULL_RECOVERY_*.md artifacts.
> Update this after EVERY slice. Keep it short.

## Continuation state

- current_phase: **Phase C — P1+P2 done, C-02 done; writing final report**
- current_recovery_action: final verification report + docs commit
- next_exact_action: commit recovery docs; remaining open = D-01..D-09 dup consolidation (P3, deferred) + C-04 product decision + Docker/E2E (BLOCKED_EXTERNAL here). Loop back to A-055 tree (A-055.30) when recovery paused.
- mode_gate: evidence-gated commits only; no `git add .`.

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
