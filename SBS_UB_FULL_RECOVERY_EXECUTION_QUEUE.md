# SBS UB — FULL RECOVERY EXECUTION QUEUE (TASK 6 + continuation)

Date: 2026-06-19 · Branch `main`. The short focus spine is `SBS_UB_RECOVERY_CONTROL.md`; this file is the prioritized work list + continuation state.

## Continuation state

- current_recovery_action: P2 partially done; at checkpoint with user.
- completed_actions: Phase A (snapshot/inventory/dup register); P1 (R-P1-01/02/03); P2 partial (4 frontend suites stabilized).
- commits_created: 7777b4f8 (Admissions CRM wire+commit) · 6a6b0374 (innovation bootstrap fix) · c9270408 (P2 frontend test stabilization).
- next_exact_action: decide R-P2-04 (DDC audit timeline — real gap) and R-P2-05 (quality self-assessment boundary — brittle/async) below; then C-02 tracker normalization.
- external_blockers: Docker / Playwright E2E / full `npm run build` not run in this env (frontend docker-only; host vitest locale-false-positives). Full PASS verdict not achievable here → final will be PASS_WITH_NOTES / BLOCKED_EXTERNAL for ops/E2E.
- do_not_repeat: Phase A discovery; P1 fixes; the 4 stabilized suites. See spine `do_not_repeat`.

## P0 — System integrity

| ID | Item | Status |
|---|---|---|
| R-P1-02 | Broken bootstrap: committed main.py imported UNTRACKED innovation_commercialization | **DONE** (6a6b0374) |
| R-P1-03 | Verify all main.py module imports resolve in git | **DONE** (no others) |
| — | App boot / migration head / RBAC-bypass / tenant-leak deep checks | DEFERRED to Phase C runtime (needs backend boot; not yet run) |

## P1 — Cross-system consistency (git ≠ reality)

| ID | Item | Status |
|---|---|---|
| R-P1-01 | Admissions CRM (V12) untracked + unmounted vertical | **DONE** (7777b4f8; 75 tests pass) |
| C-04 | Innovation: keep-vs-retire as a product vertical (code now committed) | OPEN (product decision, not integrity) |

## P2 — Vertical correctness / latent test debt

| ID | Item | Classification | Status |
|---|---|---|---|
| R-P2-01 | quality route contract 19→27 | stale assertion | **DONE** (c9270408) |
| R-P2-02 | quality "audit findings" multiple-match | brittle matcher | **DONE** (c9270408) |
| R-P2-03 | security permission-denied testid drift (`-wrap`) | stale testid | **DONE** (c9270408) |
| R-P2-06 | campus permission-denied missing module testid | real (testid added) | **DONE** (c9270408) |
| R-P2-04 | **DDC audit timeline never rendered** — `DdcAuditTimeline` is exported but invoked nowhere; `ddc-audit-timeline` testid never mounts | **REAL gap** (component defined, not wired into any route) | OPEN — needs placement decision (which route + items source) |
| R-P2-05 | quality self-assessment boundary text not found by test | likely brittle/async (banner IS wired: pages.tsx:544 + boundaryPage selfAssessment) | OPEN — needs matcher/timing check |
| — | locale-only host failures (Budget/Procurement/Quotas/ContractsLegal/Cohorts/RolePortal numbers/dates) | FALSE positives outside docker | NOT a defect — verify in docker only |

## P3 — Quality / maintainability (register only; do NOT force-merge)

- D-01..D-09 duplication families (notification ×5, identity ×6, research ×6, accreditation ×4, two academic_operations, two student_services, document_workflow ×2). See `SBS_UB_DUPLICATION_AND_CONTRADICTION_REGISTER.md`. Staged consolidation, later, compatibility-first.
- C-02 tracker normalization: stale index docs (ACTIVE_WAVE/ROADMAP/MODULE_INVENTORY on A-026) → point to SBS_UB.md + GLOBAL-ROADMAP-R3.

## exact_commands_to_continue

```bash
cd /home/sbs/AI
# DDC gap (R-P2-04): find intended placement
grep -n "DdcAuditTimeline\|routeKey" frontend/modules/document-decree-correspondence/pages.tsx
# quality self-assessment (R-P2-05): inspect banner render on selfAssessment route
node_modules/.bin/vitest run __tests__/admin/QualityAccreditationReadinessReports
# backend boot + targeted regression when entering deeper Phase C
backend/.venv/bin/python -c "from app.main import app; print(len(app.routes))"
```
