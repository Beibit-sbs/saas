# SBS UB — FULL RECOVERY EXECUTION QUEUE (TASK 6 + continuation)

Date: 2026-06-19 · Branch `main`. The short focus spine is `SBS_UB_RECOVERY_CONTROL.md`; this file is the prioritized work list + continuation state.

## Continuation state

- current_recovery_action: recovery CLOSED (PASS_WITH_NOTES). Post-recovery: A-056.G1 canonical runtime+governance gate OPENED; slice **G1.1 executed 2026-06-20** (see evidence section at bottom).
- completed_actions: Phase A (snapshot/inventory/dup register); P1 (R-P1-01/02/03); P2 (R-P2-01..06 all DONE — c9270408 + 2adbd818); C-02 tracker normalization (c290b467); then A-055.30/.31, full A-056.* arc + R1/R2, A-055 REF/HSP/GRD-R1; then A-056.G1.1.
- commits_created (recovery): 7777b4f8 · 6a6b0374 · c9270408 · 2adbd818 · c290b467.
- next_exact_action: **A-056.G1.2** — controlled served-bootstrap + RBAC-denied AND authorized-success on critical write endpoints + Digital Twin capacity/resource flow smoke. (SUPERSEDED prior pointer: "decide R-P2-04/R-P2-05" — both already DONE per the verification report.)
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

## A-056.G1.1 — Canonical System Runtime & Governance Gate (slice 1 evidence) · 2026-06-20

Mode: single main agent, host-safe + bounded LOCAL docker (no `make up` build, no host-killing guard, no fresh-volume migrate). Environment: host venv Python 3.13.13; canonical container runtime Python 3.12; canonical command `cd infra && docker compose --env-file .env …` (infra/.env present, 2511 B).

| Check | Command (abridged) | Result | Exit |
|---|---|---|---|
| Commit integrity | `git cat-file -e <sha>^{commit}` ×25 | 25/25 present, 0 missing | 0 |
| HEAD | `git rev-parse HEAD` | `d88c158b` (branch `main`) | 0 |
| Compose validity | `docker compose --env-file .env config` | exit 0; 12 services valid (backend, backend-tests, db, frontend, frontend-tests, ldap, nginx, pgbouncer, prometheus, redis, scheduler, worker) | 0 |
| Backend bootstrap | `.venv/bin/python -c "from app.main import app"` | imports clean; **1695** routes | 0 |
| Digital Twin routes | route introspection | **9** registered (state, safety-boundaries, simulate/{capacity,resource}, early-warning/{capacity,resource}, scenarios/{capacity,decision,decisions}) | 0 |
| Admissions CRM routes | route introspection | **9** registered (applicants, applications, leads, …) | 0 |
| Migration heads | `alembic -c alembic.ini heads` | single head `ipr0462rt01` (count=1) — no multiple heads | 0 |
| Migration current | `docker compose run --rm backend alembic current` (db+pgbouncer+redis up) | `ipr0462rt01 (head)` — live DB at head | 0 |
| Base data plane | `docker compose --env-file .env up -d db redis` + pgbouncer | db `pg_isready` accepting; redis `PONG`; all healthy (local images) | 0 |
| Health endpoints | TestClient GET module `/health` | mounted; **401** auth-gated (route present, middleware active) | 0 |
| Innovation bootstrap | `git ls-files …/innovation_commercialization`; status | 5 tracked, 0 uncommitted; main.py import resolves | 0 |

Defects found: NONE (G1.1 is read-only integrity; zero code changes → docs-only normalization).

BLOCKED_EXTERNAL / deferred to G1.2+ (NOT run this slice): full `make up` image build of all services; fresh-volume migration `upgrade`; frontend `npm run build` + `npm run lint` (docker-only, host-blocked by `scripts/docker_only_guard.sh`); Playwright E2E (`npm run test:e2e`); full/controlled backend regression; security deep checks (IDOR/priv-esc/secret-leak).

next_exact_action: **A-056.G1.2** — served backend bootstrap + RBAC-denied AND authorized-success on critical write endpoints + Digital Twin capacity/resource flow smoke.

## A-056.G1.2 — Critical write endpoints + transitions + Digital Twin flow smoke (slice 2 evidence) · 2026-06-20

Mode: multi-agent workflow `woriamlme` (5 domains, each really ran pytest via `.venv/bin/python -m pytest <files> -p no:cacheprovider -o addopts="" -q`), then a gate synthesis. In-process FastAPI TestClient = served ASGI stack incl. auth middleware (no container needed). Aggregate **226 passed / 0 failed** after remediation.

| Domain | Files | Result | authorized-success | denial | transitions / flow | 500? |
|---|---|---|---|---|---|---|
| Digital Twin | test_a0561_digital_twin_shell_api.py | **110/0 PASS** | simulate/capacity + simulate/resource (deterministic, evidence-lineage) | viewer→403 on all write/read routes | capacity+resource+early-warning+scenarios+decision; non-finite→**400 not 500**; tenant fail-closed | none |
| Finance acknowledge | test_a0402_*_api.py + _services.py | **38/0 PASS** | admin acknowledge→201, anti-fake flags, FinanceBridgeRecord persisted | viewer→403 | tenant fail-closed (generic) | **none (explicit)** |
| Grades | test_grade_lifecycle_service.py + test_router_grades_phase3.py + test_service_hardening_lxxxiv.py | **20/0 PASS** (was 18/2) | submit_grade + change_grade success | window-close + section guards reject | valid/out-of-order/terminal/tenant covered | none |
| Enrollments | tests/modules/enrollments/* + test_enrollments.py | **37/0 PASS_WITH_NOTES** | service-level enroll/change/drop | viewer/tenant | valid/terminal/tenant; **out-of-order absent** | none |
| Hardship (student-services) | test_a0422_*_services.py | **23/0 PASS_WITH_NOTES** | in-order transitions + 3 rejections | **RBAC denial absent** | valid/out-of-order/terminal; **tenant absent** | none |

Defect FOUND and FIXED this slice: 2 red grades tests = stale fixtures broken by census-lock fix `36ae8a3e` (change_grade gained two guards the tests didn't stub) → **fixed in commit `6f13c27e`** (separate code commit). The gate did its job: a regression that shipped green (full grades set never re-run after 36ae8a3e) was caught.

Effective gate verdict: **PASS_WITH_NOTES** (all 5 domains green post-fix; no 500 anywhere; remaining items are evidence gaps, not failures). No production-readiness claim.

G1.3 backlog (next): enrollments HTTP-route authorized-success for change-status + drop (+ create_academic_term); out-of-order (non-terminal) enrollment transition rejection test; hardship RBAC-denial + tenant-fail-closed tests; (non-blocking) real-DB tenant cross-read isolation for DT decisions + acknowledge invalid-tenant test.

next_exact_action: **A-056.G1.3** — remediate the backlog above (HTTP-route success/denial + transition/tenant gaps).
