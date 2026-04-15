# F3.3 Unfreeze — Quick Reference Card (2026-04-21)

**Execution Date:** 2026-04-21 (10:00 UTC)  
**Duration:** 30–45 minutes  
**Critical Path:** 8 sequential steps  
**Rollback Exit:** Revert commit + `alembic downgrade -1`

---

## Command Quick Reference

### Gate 0: F3.2 Schema Approval (must PASS before Step 1)
```bash
cd /home/sbs/AI

# 1) Generate sign-off artifact (fill real signer names)
bash scripts/f3_schema_review_signoff.sh --approved \
  --backend-lead "<Backend Lead Name>" \
  --dba "<DBA/Platform Engineer Name>" \
  --security "<Security/Compliance Rep Name>" \
  --product-owner "<Product Owner Name>"

# 2) Verify blocking gate
bash scripts/f3_schema_review_gate.sh

# Expected: F3.2_GATE=PASS
```

### Step 1: Final Verification (before wiring)
```bash
# Check all tests pass
cd /home/sbs/AI
docker compose exec backend python -m pytest \
  tests/modules/interventions/test_f3_*.py -v --tb=short

# Verify alembic is at latest
docker compose exec backend alembic current

# Verify docker is running
docker compose ps | grep -E "backend|db|frontend"
```

### Step 2: Remove Freeze Guards (2 locations in effectiveness_service.py)

**Location 1 (finalize_cohort):** Line ~42–44
```python
# ❌ REMOVE THIS:
if not self.config.F3_COHORT_FINALIZATION_ENABLED:
    raise NotImplementedError("F3 finalize frozen")

# ✅ KEEP THIS (uncomment if needed):
# Implementation code here...
```

**Location 2 (analyze_cohort):** Line ~114–116
```python
# ❌ REMOVE THIS:
if not self.config.F3_COHORT_ANALYSIS_ENABLED:
    raise NotImplementedError("F3 analyze frozen")

# ✅ KEEP THIS:
# Implementation code here...
```

### Step 3: Wire Router into main.py

**Add import at top** (line ~73):
```python
from app.modules.interventions.effectiveness_router import router as effectiveness_router
```

**Add include_router** (after line 230, with other intervention routers):
```python
app.include_router(effectiveness_router, prefix="/api/admin/interventions/cohorts", tags=["interventions"])
```

### Step 4: Apply Alembic Migration
```bash
cd /home/sbs/AI/infra
docker compose exec backend alembic upgrade head
# Expected: 3 tables created (app_intervention_cohorts, app_intervention_cohort_outcomes, app_intervention_cohort_members)

# Verify tables exist
docker compose exec db-1 psql -U app -d app -c \
  "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;"
```

### Step 5: Rebuild Backend Container
```bash
cd /home/sbs/AI/infra
docker compose build --no-cache backend
docker compose up -d backend

# Wait for health check
sleep 15
docker compose exec backend curl http://localhost:8000/health/live
```

### Step 6: Run F3 Tests (Update 2 post-unfreeze cases)

```bash
# Run all 40 F3 tests
docker compose exec backend python -m pytest \
  tests/modules/interventions/test_f3_*.py -v --tb=short

# Expected: 38/40 pass (2 will fail: freeze-guard negative tests)
# This is EXPECTED — these tests checked that freezing worked

# Update 2 tests: Remove freeze-guard assertions, add positive assertions instead
# Files to update:
#   - tests/modules/interventions/test_f3_service_negative_cases.py (2 test cases)
```

### Step 7: Platform Regression Gate Verify
```bash
cd /home/sbs/AI
DOCKER_ONLY_GUARD_SKIP_PROCESS_CHECK=1 bash scripts/release_check.sh
# Expected: 7/7 architecture guards pass ✅
```

### Step 8: Update Tracking Docs
```bash
# Update F3_EXECUTION_PLAN.md:
#   - F3.3 wiring: ✅ COMPLETE (2026-04-21)
#   - F3.4 Frontend: ⏳ IN PROGRESS (unfreeze day+)
#   - F3.5 Observability: ⏳ IN PROGRESS (unfreeze day+)

# Update AUDIT_SBS_2026.md ACTIVE FOCUS:
#   - Changed from "F2.10 PASS APPROVED" → "F3.3 Unfreeze COMPLETE"
#   - Add: F3.4/F3.5 delivery phases now active
```

---

## Success Criteria Checklist

**Before wiring:**
- [ ] F2.10 PASS gate approved ✅
- [ ] 40/40 skeleton tests passing ✅
- [ ] All 9 services healthy (docker compose ps) ✅
- [ ] Database backup exists ✅
- [ ] Deployment crew on standby ✅

**After wiring (same day):**
- [ ] 4 F3 API endpoints accessible (finalize, analyze, outcomes, latest) ✅
- [ ] 38/40 tests passing (2 freeze-guard tests expected to fail post-unfreeze) ✅
- [ ] Platform regression gate: 7/7 ✅
- [ ] No P0 incidents - 2 hours post-deployment monitoring ✅
- [ ] Frontend repo notified F3 API is live ✅

---

## Rollback Triggers (execute immediately if any occur)

| Trigger | Command | Recovery Time |
|---------|---------|----------------|
| API returns 5xx on F3 endpoints | Feature flag disable | < 5 min |
| Tests fail (>2 failures) | `git revert`, `alembic downgrade -1` | 10–15 min |
| Database migration fails | Restore from backup | 10–30 min |
| Prometheus alerts fire | Check logs, troubleshoot | 15–30 min |

**Rollback:**
```bash
# Kill F3 feature flag
kubectl set env deployment/backend F3_COHORT_FINALIZATION=false
# OR
git revert <commit-hash>
alembic downgrade -1
docker restart ai-backend-1
```

---

## Communication Timeline

| Time | Action | Owner |
|------|--------|-------|
| T-1h | All crews ready, final checks | DevOps Lead |
| T-0  | Begin Step 1, Slack notify #f3-unfreeze | Backend Lead |
| T+5m | Steps 1–3 complete, code committed | Backend Lead |
| T+15m | Step 4–5 complete, API restarting | DevOps |
| T+20m | Step 6 tests running | QA |
| T+35m | Step 7–8 complete, docs updated | Backend Lead |
| T+40m | All good? Gate PASS, notify #f3-complete | DevOps Lead |
| T+2h | Monitoring window, no issues = unfreeze SUCCESS | SRE on-call |

---

## Frequently Asked Questions (Day-of)

**Q: Test failure — what to do?**  
A: If > 1 test fails (besides the 2 freeze-guard negatives), roll back immediately. Check logs for SQL errors or missing schema.

**Q: API endpoint returns 404?**  
A: Router not wired correctly. Verify `include_router` added to main.py. Rebuild container.

**Q: Database migration timeout?**  
A: Run with `alembic upgrade head --timeout 300` (5 min timeout). If still fails, restore from backup + retry.

**Q: Should we do this on a Friday?**  
A: **NO.** If issues arise, need support available Mon–Fri business hours. Schedule for Monday–Thursday only.

---

## References

- **Full wiring checklist:** `docs/runbooks/artifacts/f3_wiring_checklist_20260421.md`
- **F3 execution plan:** `docs/F3_EXECUTION_PLAN.md`
- **Incident response (if needed):** `docs/runbooks/F3_DATA_BREACH_RESPONSE.md`, `docs/runbooks/F3_OUTAGE_RESPONSE.md`
- **Feature flags:** LaunchDarkly (F3_COHORT_FINALIZATION, F3_COHORT_ANALYSIS, based on flags in security spec)

---

## Sign-Off

**This card is valid starting:** 2026-04-21 09:00 UTC  
**Execution window:** 2026-04-21 10:00–11:00 UTC (30–45 min SLA)  
**Created by:** Agent (automated preparation)  
**Approved by:** [TBD — Backend Lead @ T-1h]
