# SBS UB — FULL RECOVERY VERIFICATION REPORT

Date: 2026-06-19 · Branch `main` · Mode: phased recovery (read-only analysis → P0/P1/P2 execution → tracker normalization).

## 1. Initial state

- Branch `main`, HEAD at A-055.29 (`1bbea518`). 3 modified tracked files = junk only (`.coverage` x2, `.vscode/tasks.json`); 150 untracked.
- Known fragmentation: stale index docs (A-026), 755 root `.md`, 241 backend / 81 frontend modules, latent test debt suspected, whole verticals' code uncommitted.

## 2. Documents reviewed (canonical)

- `SBS_UB.md` (authoritative control center), `GLOBAL-ROADMAP-R1/R2/R3` (post-A-053, 9/20 strong), `NATIONAL_UNIVERSITY_OS_TREE.md` (24-layer target), `SBS_UB_STRATEGIC_EXECUTION_POLICY_…` (20-verticals policy). Stale/superseded: ACTIVE_WAVE/COMPLETED_WAVES/ROADMAP/MODULE_INVENTORY/EVIDENCE_INDEX (now corrected).

## 3. Problems found

- **P0 — broken bootstrap:** committed `main.py` imported the UNTRACKED `innovation_commercialization` module → clean checkout would fail to import `app.main`.
- **P1 — git ≠ reality:** Admissions CRM (V12) full backend vertical (module + migration + 5 tests) UNTRACKED and not mounted in `main.py`, despite a closure report and committed frontend.
- **P2 — latent test debt (locale-independent, real):** quality route contract 19→27; quality "audit findings" brittle matcher; security permission-denied testid drift; campus permission-denied missing module testid; **DDC audit timeline never rendered (real)**; **quality self-assessment anti-fake boundary label dropped (real)**.
- **Docs:** 5 index trackers stale (A-026 vs A-055).
- **Duplication (registered, not fixed):** notification ×5, identity ×6, research ×6, accreditation ×4, two academic_operations, two student_services, document_workflow ×2.
- **Environment (not defects):** host-only locale false-positives in number/date tests (frontend is docker-only).

## 4. Problems fixed (with evidence)

| Problem | Root cause | Fix | Verification | Commit |
|---|---|---|---|---|
| Admissions CRM untracked+unmounted | missing `include_router` in main.py | wired + committed module/migration/5 tests | 75 backend tests pass (was 73/2); app-surface 9 pass/3 skip | 7777b4f8 |
| Broken bootstrap | committed main.py imports untracked module | committed innovation shell module+frontend | app.main imports; all main.py module imports resolve in git | 6a6b0374 |
| quality 19→27 / audit-findings / security testid / campus testid | stale assertions + 1 missing testid | corrected tests + added campus testid wrapper | 4 suites, 20 tests pass | c9270408 |
| DDC timeline never rendered | exported component never invoked | wired `<DdcAuditTimeline items={model.workflows}/>` | DDC suite 6 pass | 2adbd818 |
| quality self-assessment boundary dropped | boundary array used runtime label, omitted page label | added `selfAssessmentPage` label | quality 10 files / 39 pass | 2adbd818 |
| 5 stale index trackers | A-026 content never superseded | dated RECOVERY CORRECTION markers → authoritative sources | docs only; history preserved | (docs commit) |

## 5. Duplicates consolidated

None merged (correct: structural dup needs staged, compatibility-first consolidation). All registered in `SBS_UB_DUPLICATION_AND_CONTRADICTION_REGISTER.md`. Notification family consolidation is already in progress via the A-054 wave.

## 6. Unified Brain architecture status

- Identity/tenant/RBAC: single auth/rbac/identity core + adapters (registered as D-08; not refactored — high risk, deferred).
- Cross-vertical wiring: the **A-055 end-to-end tree** is the live cross-vertical integration effort (student lifecycle → finance → student services, with metadata-only human-gated bridges). Verified green for finance + student-services this recovery.
- Brain Core: present, human-gated; not bypassing RBAC/tenant/audit in the surfaces inspected.
- This recovery did NOT build a new unification layer (correctly — that would violate "don't rewrite working parts"); it restored integrity and registered the consolidation backlog.

## 7. Verification commands and results (real)

```text
backend (finance, A-055.29 prior):   52 passed                      (4 files)
backend admissions_crm:              75 passed (was 73 / 2 failed)  (5 files)
backend app-surface regression:       9 passed, 3 skipped           (3 files)
frontend quality suites:             39 passed                      (10 files)
frontend DDC workflows:               6 passed                      (1 file)
frontend security/campus/(quality):  20 passed                      (4 files)
app import probe:                    app.main imports; all main.py module imports resolve in git
```
Environment: backend `backend/.venv` pytest (host); frontend host vitest (locale caveat noted). Exit codes 0 on the runs above.

## 8. Remaining limitations (honest)

- Docker runtime / Playwright E2E / full `npm run build` / `npm run lint`: **NOT run here** (frontend docker-only; environment cannot host the canonical docker test harness reliably) → BLOCKED_EXTERNAL for operational/E2E verification.
- Host vitest locale false-positives remain for number/date tests (pass in docker) — not defects.
- Full backend regression (thousands of tests) NOT re-run wholesale; only targeted/affected suites verified.
- Duplication families D-01..D-09 NOT consolidated (deferred, registered).
- C-04 (keep vs retire innovation_commercialization) is an open product decision.
- Security deep checks (IDOR/privilege-escalation/secret-leak) NOT performed this pass.

## 9. Coverage vs maturity

| Dimension | State |
|---|---|
| Functional coverage | high (241/81 modules) |
| Runtime verification (this recovery) | finance + admissions_crm + affected frontend verticals re-verified; rest historical |
| Security verification | not performed |
| Operational readiness (Docker/E2E) | BLOCKED_EXTERNAL here |
| Production readiness | NO (9/20 strong; deferred dup + ops gaps) |
| Git integrity | RESTORED (no broken-bootstrap; all main.py imports resolve) |

## 10. Final verdict

**PASS_WITH_NOTES.** All P0/P1 integrity problems and all locale-independent P2 test-debt found this pass are fixed and verified by real targeted tests; git no longer diverges from runtime at bootstrap. Remaining items are honestly registered: Docker/E2E (BLOCKED_EXTERNAL in this environment), duplication consolidation (P3, deferred), and one product decision (C-04). No production-ready or fully-complete claim is made.
