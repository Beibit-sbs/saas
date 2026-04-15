# F3.3 Unfreeze Wiring Checklist — 2026-04-21

**Author:** Agent  
**Precondition gate:** `f3_unfreeze_checklist_20260414.md` GO decision  
**Estimated execution time:** ~30 min

---

## Pre-Wiring Verification (run first)

```bash
# 1. All gates must be PASS before starting
# F2.10 gate: F2.9 day-7 review must have produced PASS verdict
grep -l "day7" docs/runbooks/artifacts/f2_playbooks_day7*

# 2. F3.2 schema approval must exist
grep -l "F3.2_SCHEMA_APPROVED" docs/runbooks/artifacts/

# 3. Full test suite green (baked container)
docker exec ai-backend-1 python -m pytest tests/ -q 2>&1 | tail -5

# 4. Alembic head must be f8c1d2e3a4b5 (F3 merge)
docker exec ai-backend-1 alembic current
```

**Do not proceed if any of these fail.**

---

## Step 1 — Remove freeze guards from `effectiveness_service.py`

File: `backend/app/modules/interventions/effectiveness_service.py`

### 1a. `finalize_cohort` — remove freeze guard + implement body

**Current (lines 34–44):**
```python
def finalize_cohort(
    self,
    *,
    tenant_id: int,
    actor: str,
    payload: CohortFinalizeRequestSchema,
) -> InterventionCohortModel:
    validate_tenant_id_provided(tenant_id)
    raise DomainValidationError(
        "F3 finalize_cohort is frozen until F3.3 delivery is officially unfrozen."
    )
```

**Replace with:**
```python
def finalize_cohort(
    self,
    *,
    tenant_id: int,
    actor: str,
    payload: CohortFinalizeRequestSchema,
) -> InterventionCohortModel:
    validate_tenant_id_provided(tenant_id)
    cohort = InterventionCohortModel(
        tenant_id=tenant_id,
        playbook_id=payload.playbook_id,
        cohort_name=payload.cohort_name,
        analysis_window_start=payload.analysis_window_start,
        analysis_window_end=payload.analysis_window_end,
        treated_count=payload.treated_count,
        control_count=payload.control_count,
        status="finalized",
        finalized_by=actor,
        finalized_at=_utc_now(),
    )
    self._db.add(cohort)
    self._db.flush()
    return cohort
```

### 1b. `analyze_cohort` — remove freeze guard + implement return

**Current (lines 114–116):**
```python
        raise DomainValidationError(
            "F3 analyze_cohort is frozen until F3.3 delivery is officially unfrozen."
        )
```

**Replace with (after the `assert_resource_belongs_to_tenant` call):**
```python
        outcomes = self.get_outcomes(tenant_id=tenant_id, cohort_id=cohort_id)
        return {
            "cohort_id": cohort.id,
            "tenant_id": cohort.tenant_id,
            "cohort_name": cohort.cohort_name,
            "status": cohort.status,
            "outcomes": [
                {
                    "outcome_type": o.outcome_type.value,
                    "segment_name": o.segment_name,
                    "treated_rate": float(o.treated_rate),
                    "control_rate": float(o.control_rate),
                    "uplift_percent": float(o.uplift_percent),
                    "confidence_lower": float(o.confidence_lower),
                    "confidence_upper": float(o.confidence_upper),
                }
                for o in outcomes
            ],
            "analyzed_at": _utc_now().isoformat(),
        }
```

---

## Step 2 — Wire router into `app/main.py`

File: `backend/app/main.py`

### 2a. Add import (after line 73, with other interventions imports)

```python
# After:
from app.modules.interventions.playbook_router import router as interventions_playbook_router
# Add:
from app.modules.interventions.effectiveness_router import router as interventions_effectiveness_router
```

### 2b. Add include_router (after line 230, with other interventions routers)

```python
# After:
app.include_router(interventions_playbook_router)
# Add:
app.include_router(interventions_effectiveness_router)
```

---

## Step 3 — Apply Alembic migration

```bash
# Verify current head (should be f8c1d2e3a4b5 already if test DB was migrated)
docker exec ai-backend-1 alembic current

# Apply if not yet at f8c1d2e3a4b5
docker exec ai-backend-1 alembic upgrade head

# Verify tables created
docker exec ai-db-1 psql -U "${POSTGRES_USER:-app}" -d "${POSTGRES_DB:-app}" \
  -c "\dt app_intervention_cohorts app_intervention_cohort_outcomes app_intervention_cohort_members"
```

**Expected:** 3 tables present — `app_intervention_cohorts`, `app_intervention_cohort_outcomes`, `app_intervention_cohort_members`

---

## Step 4 — Rebuild backend container

```bash
cd /home/sbs/AI/infra
docker compose --env-file .env up -d --build backend
# Wait for health
sleep 10
docker compose --env-file .env ps backend
```

**Expected:** `ai-backend-1` status `Up N seconds (healthy)`

---

## Step 5 — Run F3 tests

```bash
# Remove --override-ini after rebuild; new container has new code baked
docker exec ai-backend-1 python -m pytest \
  tests/modules/interventions/test_f3_service_negative_cases.py \
  tests/modules/interventions/test_f3_intervention_cohort_models.py \
  tests/modules/interventions/test_f3_intervention_cohort_service.py \
  -v 2>&1 | tail -20
```

**Expected:** 40 tests pass (7 + 20 + 13)

> **Note:** After unfreeze, `test_f3_service_negative_cases.py` tests for frozen behavior will
> fail — they test that `finalize_cohort` raises `DomainValidationError`. Update those 2 tests:
> - `test_finalize_cohort_raises_domain_validation_error` → should now succeed, not raise
> - `test_analyze_cohort_raises_domain_validation_error_after_404_check` → same

See **Step 5b** for test updates.

### Step 5b — Update post-freeze test expectations

In `tests/modules/interventions/test_f3_service_negative_cases.py`:

- Rename `test_finalize_cohort_raises_domain_validation_error` →
  `test_finalize_cohort_persists_cohort` and assert `result` is not `None`
- Rename `test_analyze_cohort_raises_domain_validation_error_after_404_check` →
  `test_analyze_cohort_returns_analysis_dict` and assert `isinstance(result, dict)`

---

## Step 6 — Platform regression gate

```bash
docker exec ai-backend-1 python -m pytest tests/platform/ -q 2>&1 | tail -5
```

**Expected:** same pass count as baseline `≥ 439` passed

---

## Step 7 — Smoke check live API

```bash
# Check router is registered
curl -s http://localhost:8000/openapi.json | python3 -m json.tool | grep "cohorts"
```

**Expected:** Path `/api/admin/interventions/cohorts/...` appears in OpenAPI spec

---

## Step 8 — Update tracking documents

- [ ] `docs/F3_EXECUTION_PLAN.md` → F3.3 status: `🟡 SKELETON READY` → `✅ WIRED`
- [ ] `docs/F3_EXECUTION_PLAN.md` → Approval Gate: `[ ] F3.2_SCHEMA_APPROVED` → `[x]`
- [ ] `docs/F3_EXECUTION_PLAN.md` → Approval Gate: `[x] F2.10_GATE = PASS` confirm filled
- [ ] `docs/AUDIT_SBS_2026.md` → ACTIVE FOCUS update: F3.3 wired
- [ ] `docs/RELEASE_GATE.md` → update baseline test counts

---

## Rollback

If anything fails after Step 4 (container rebuild):

```bash
cd /home/sbs/AI/infra
# Revert main.py include_router line + import (git revert or manual)
git diff backend/app/main.py backend/app/modules/interventions/effectiveness_service.py

# Rebuild with reverted code
docker compose --env-file .env up -d --build backend
```

Alembic migration rollback (if tables must be dropped):
```bash
docker exec ai-backend-1 alembic downgrade f8c1d2e3a4b5~1
```
> This drops the 3 F3 tables. Only do if migration is broken — no production data yet at unfreeze.

---

## Checklist Summary

- [ ] Pre-wiring verification passes (F2.10 PASS + schema approved + tests green)
- [ ] Step 1a: `finalize_cohort` freeze guard removed + body implemented
- [ ] Step 1b: `analyze_cohort` freeze guard removed + return implemented
- [ ] Step 2: import + include_router added in `main.py`
- [ ] Step 3: Alembic migration applied, 3 tables present
- [ ] Step 4: Backend container rebuilt and healthy
- [ ] Step 5: 38 F3 tests pass (2 freeze-guard tests updated in 5b, 38 remaining green)
- [ ] Step 6: Platform regression gate ≥ 439 passed
- [ ] Step 7: OpenAPI spec shows `/api/admin/interventions/cohorts` paths
- [ ] Step 8: Tracking docs updated
