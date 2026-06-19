# SBS UB — FULL RECOVERY SOURCE SNAPSHOT (TASK 0)

Date: 2026-06-19
Mode: read-only snapshot. Nothing deleted, nothing reset, nothing auto-staged.

## 1. Git position

- repo root: `/home/sbs/AI`
- branch: `main` (the project's only working branch; all wave history is linear on main)
- HEAD: `1bbea518` feat(wave45): A-055.29 finance-office referral acknowledgement note
- recent: `1bbea518` A-055.29 → `ca744e21` A-055.28 → `00fb60be` A-055 tree (.0-.27) → `782fb5c3` A-054.9 …
- working tree: 3 modified tracked, 0 staged, 150 untracked.

## 2. Working-tree classification (A/B/C/D)

### A — changes belonging to current recovery
- None yet (recovery just started; Phase A is read-only).

### B — pre-existing user/project content not yet committed (DO NOT discard)
- **Untracked whole-vertical CODE (git history ≠ actual codebase — major):**
  - `backend/app/modules/admissions_crm/` (Admissions CRM, vertical V12)
  - `backend/alembic/versions/acrm0452rt01_a0452_admissions_crm_batch1_tables.py`
  - `backend/tests/test_a0452_admissions_crm_{api,models,services,dependencies,audit_security}.py`
  - `backend/app/modules/innovation_commercialization/` (A-053 extension)
  - `backend/tests/test_superadmin_cross_tenant_policy.py`
  - frontend: `frontend/modules/academic-terms/`, `frontend/modules/innovation-commercialization/`, `frontend/app/(admin)/console/innovation-commercialization/`
- **Untracked project documents (real, never committed):** 41 `A-*.md` reports, `NATIONAL_UNIVERSITY_OS_TREE.md`, `SAAS_ENTRYPOINT_TREE_AND_VERTICAL_MAP.md`, `SBS_UB_STRATEGIC_EXECUTION_POLICY_20_STRONG_VERTICALS_BEFORE_PRODUCTION.md`, and this recovery's new `.md` files.

### C — generated / junk artifacts (safe to ignore; candidate for .gitignore, NOT this recovery's job to commit)
- modified tracked: `.coverage`, `backend/.coverage`, `.vscode/tasks.json`
- untracked: 72 × `backend/.r1[7-9]_*.txt` (diagnostic logs), `backend/tests/.r10_shards/`, `backend/coverage.json`, `backend/.a0515_backend_test.rc`, `artifacts/` (13 coverage-audit files), `.gate-logs/`, `.~lock.*.md#` (LibreOffice locks)

### D — unknown, cannot safely classify (touch nothing)
- `docs/project-control/` (untracked dir; contents not yet inspected — leave as-is)

## 3. Immediate observations feeding the recovery

1. **Git ≠ reality:** at least two whole verticals' code (`admissions_crm` V12, `innovation_commercialization`) and their tests/migrations exist on disk but are NOT in git history. Any "closed vertical" claim for Admissions CRM is undermined by its code being uncommitted. → recovery queue P1 candidate (git-state reconciliation, evidence-gated).
2. **Latent test debt:** prior waves were committed without full test runs (confirmed: finance models/security tests were red-on-commit, fixed in A-055.29; quality route count 19→27 and security/campus missing testids remain). → recovery queue P2.
3. **Doc sprawl + staleness:** 755 `.md` in root; index docs (ACTIVE_WAVE/ROADMAP/MODULE_INVENTORY) describe May A-026 while reality is A-055. → tracker normalization (TASK 10).
4. **Junk in tree:** tracked binary `.coverage`, 72 diagnostic txts, locks. → hygiene (separate from recovery; .gitignore recommendation only).

## 4. Safety constraints honored
- No `git reset`, no `git add .`, no deletion, no overwrite of category B/D.
- Recovery work will be evidence-gated and committed in scoped slices only after Phase A review.
