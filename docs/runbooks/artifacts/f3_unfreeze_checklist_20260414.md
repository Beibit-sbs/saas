# F3.3 Unfreeze Day Checklist

**Purpose:** One-time gate checklist to confirm all prerequisites are met before activating F3.3 backend delivery.

**Target unfreeze date:** 2026-04-21 (after F2.10 PASS confirmed)

**Prepared at:** 2026-04-14 (local) / 2026-04-13T19:xx UTC

---

## Section 1 — F2.10 Gate (Hard Blocker)

All F2.9 scheduled reviews must be PASS before this gate unlocks.

| Review | Due Date | Artifact | Status |
|--------|----------|---------|--------|
| F2.9 Day-0 baseline | 2026-04-13 | `f2_playbooks_day0_baseline_20260413_115942.md` | ✅ PASS |
| F2.9 Day-1 review | 2026-04-14 | `f2_playbooks_day1_review_20260413_190642.md` | ✅ PASS |
| F2.9 Day-3 review | 2026-04-16 | TBD | ⏳ PENDING |
| F2.9 Day-7 (F2.10 PASS) | 2026-04-20 | TBD | ⏳ PENDING |

**Gate:** `F2.10_GATE = PASS` when Day-7 review is signed off.

---

## Section 2 — F1.9 Stability Gate (Hard Blocker)

F1 risk pipeline must remain stable throughout F3.3 delivery window.

| Review | Due Date | Artifact | Status |
|--------|----------|---------|--------|
| F1.9 Day-0 baseline | 2026-04-13 | `f1_risk_day0_baseline_20260413_120021.md` | ✅ PASS |
| F1.9 Day-1 review | 2026-04-14 | `f1_risk_day1_review_20260413_190818.md` | ✅ PASS |
| F1.9 Day-3 review | 2026-04-16 | TBD | ⏳ PENDING |
| F1.9 Day-7 | 2026-04-20 | TBD | ⏳ PENDING |

**Gate:** No active P1/P2 regressions in risk pipeline on unfreeze day.

---

## Section 3 — F3 Design Gates

| Item | Status | Evidence |
|------|--------|---------|
| F3.2 schema design complete | ✅ DONE | `F3_EXECUTION_PLAN.md` §F3.2 — 3 tables, FK constraints, indexes |
| F3 Alembic migration merged | ✅ DONE | Revision `f8c1d2e3a4b5` — single head confirmed |
| F3 contract skeleton tests pass | ✅ DONE | `test_f3_effectiveness_contract_skeleton.py` (3 tests) |
| F3 schema compatibility with F2 | ✅ DONE | `test_f3_schema_compatibility_with_f2.py` |
| F3 service-level negative tests pass | ✅ DONE | `test_f3_service_negative_cases.py` (7/7 tests green) |
| F3.2 schema approved by backend team | ⏳ PENDING | Requires human review sign-off |
| F3.1 no objections from PMs/Deans | ⏳ PENDING | Pre-pilot — implicit if no red flags raised |

---

## Section 4 — Infrastructure Readiness

| Check | Command | Expected | Status |
|-------|---------|---------|--------|
| Docker stack healthy (all 9 svc) | `docker compose ps` | All `healthy` | ✅ PASS (verified 2026-04-13) |
| Single Alembic head | `alembic heads` | Exactly 1 head | ✅ PASS (`f8c1d2e3a4b5`) |
| DB migrations clean | `alembic current` | Same as head | Verify on day-of |
| Redis healthy | `docker compose ps redis` | `healthy` | ✅ PASS |
| No alert noise | Prometheus `/alerts` | 0 firing rules | ✅ PASS (verified 2026-04-13) |

---

## Section 5 — Unfreeze Day Runbook (2026-04-21)

Execute in order:

```bash
# 1. Verify F2.10 day-7 review PASS artifact exists
ls docs/runbooks/artifacts/f2_playbooks_day7_review_*.md

# 2. Confirm single alembic head
docker compose --env-file infra/.env exec backend alembic heads

# 3. Run full backend test suite (must pass)
docker compose --env-file infra/.env run --rm backend-tests pytest -q

# 4. Run F3-specific negative tests (must pass)
docker compose --env-file infra/.env run --rm backend-tests python -m pytest \
  /project/backend/tests/modules/interventions/ -v --override-ini="addopts="

# 5. Remove freeze guard from effectiveness_service.py
#    - finalize_cohort: replace DomainValidationError raise with actual implementation
#    - analyze_cohort: replace DomainValidationError raise with actual analysis logic

# 6. Wire F3 router into main app (app/main.py)
#    app.include_router(effectiveness_router, prefix="/api/v1/effectiveness", tags=["effectiveness"])

# 7. Run full test suite again post-wiring
docker compose --env-file infra/.env run --rm backend-tests pytest -q

# 8. Update F3_EXECUTION_PLAN.md: F3.3 status → IN PROGRESS
```

---

## Section 6 — Go / No-Go Decision

On 2026-04-21, before starting any F3.3 implementation:

| Condition | Required | Self-check |
|-----------|---------|-----------|
| F2.10_GATE = PASS | **YES** | `[ ]` |
| F1.9 Day-7 = PASS | **YES** | `[ ]` |
| F3.2_SCHEMA_APPROVED | **YES** | `[ ]` |
| Full backend test suite green | **YES** | `[ ]` |
| 0 open P1/P2 bugs in F1 or F2 on release tracker | **YES** | `[ ]` |
| F3.1 no objections | **Best effort** | `[ ]` |

**Decision protocol:**
- All **YES** items checked → `GO: F3.3 delivery begins 2026-04-21`
- Any **YES** item missing → `NO-GO: delay to 2026-04-28, re-evaluate`

---

## Section 7 — Post-Unfreeze Monitoring (first 24h)

After F3.3 routes are wired into main app:

- Monitor backend error rate: `POST /api/v1/effectiveness/cohorts/finalize` → expect 0 errors for first 24h (no pilot users yet)
- Check Prometheus `ai_http_requests_total` for any unexpected 5xx on `/effectiveness/` prefix
- Confirm no cross-tenant queries in DB slow log (`pg_stat_activity` on `ai-db-1`)
- Confirm F1 risk pipeline still healthy (run `tests/modules/interventions/test_f3_service_negative_cases.py` daily for first 3 days)

---

*Checklist prepared by: Agent (autonomous) — 2026-04-14 local*
*Review before 2026-04-21 unfreeze decision*
