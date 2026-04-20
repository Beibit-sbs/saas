# F3.3-F3.5 Readiness & Kickoff Sequence

**Target Execution:** 2026-04-21 onwards (F3.3 already unfrozen as of 2026-04-18)

## Pre-Kickoff Validation (Can execute now: 2026-04-18+)

Three sequential fail-closed gates validate that F3.3-F3.5 infrastructure is ready:

### Gate 1: F3.3 Post-Unfreeze Validation
```bash
make f3-unfreeze-validation
# or
bash scripts/f3_unfreeze_validation.sh
```

**Checks:**
- Router wired in main.py ✅
- Freeze guards removed ✅
- DB migration exists ✅
- Skeleton tests present ✅

**Expected Output:**
```
F3.3_VALIDATION=PASS
NEXT_STEP=proceed_with_f3_4_f3_5_kickoff_ready
```

### Gate 2: F3.5 Observability Readiness
```bash
make f3-5-observability-kickoff
# or
bash scripts/f3_5_observability_kickoff_readiness.sh
```

**Checks:**
- Alert rules valid (22 rules found) ✅
- Metrics module instrumented ✅
- Service code instrumented ✅

**Expected Output:**
```
F3.5_KICKOFF_READY=PASS
RULES_FOUND=22
```

### Gate 3: F3.4 Frontend Readiness (requires running backend)
```bash
make f3-4-frontend-kickoff
# or
bash scripts/f3_4_frontend_kickoff_readiness.sh
```

**Checks:**
- Backend API is live ✅
- Frontend dependencies installed ✅
- Type generation ready ✅

**Expected Output:**
```
F3.4_KICKOFF_READY=PASS
API_HEALTH=PASS
TYPE_GENERATION=READY
```

## Kickoff Day (2026-04-21)

### Morning: Stack Preparation
```bash
# Ensure docker stack is running
make up

# Verify all pre-kickoff gates still pass
make f3-unfreeze-validation
make f3-5-observability-kickoff
make f3-4-frontend-kickoff
```

### Afternoon: Parallel Phase 1 Start

**F3.4 Frontend (Team Lead at 11:30 UTC):**
1. Pull latest F3 API specs: `npm run generate:openapi-types`
2. Create feature branch: `git checkout -b f3-cohort-analysis-dashboard`
3. Start Phase 1: Data Fetching Layer (see [F3.4 Implementation Guide](../F3_4_FRONTEND_IMPLEMENTATION_GUIDE.md))

**F3.5 Observability (DevOps Lead at 11:30 UTC):**
1. Verify metrics are being collected
2. Check Prometheus scrape targets
3. Start Phase 1: Metrics emission validation (per [F3.5 Implementation Guide](../F3_5_OBSERVABILITY_IMPLEMENTATION_GUIDE.md))

## Weekly Gate Checkpoints

| Date | Gate | Owner | Target |
|------|------|-------|--------|
| 2026-04-25 | F3.4 Phase 1+2 Progress (63 tests) | Frontend | 63/63 tests PASS |
| 2026-04-25 | F3.5 Phase 1+2 Progress (metrics+spans) | DevOps | Instrumentation complete |
| 2026-05-05 | F3.4/F3.5 Delivery Complete | All | Full phase 1-5 done for F3.4; 1-2 done for F3.5 |
| 2026-05-10 | F3.6 Security Phase 1 Kickoff | Security | FERPA validators ready |
| 2026-05-22 | F3.6/F3.10 DoD Sign-Off | Compliance | All phases complete + sign-off |

## Recovery Actions

If any pre-kickoff gate fails, corresponding recovery action:

| Gate | Failure Reason | Recovery |
|------|---|----------|
| F3.3 Validation | Router not wired | Manual: wire effectiveness_router in main.py |
| F3.3 Validation | Freeze guards still present | Manual: remove `raise DomainValidationError` from service |
| F3.5 Observability | Alert rules invalid | `bash scripts/f3_observability_alerts_gate.sh` for details |
| F3.4 Frontend | API not responding | `make up && docker compose exec backend pytest` for health check |
| F3.4 Frontend | Types not generatable | `cd frontend && npm install && npm run generate:openapi-types` |

## Key Dates & Immovable Deadlines

- **2026-04-21:** F3.3 Unfreeze completion + F3.4/F3.5 Phase 1 kickoff (currently: already unfrozen as of 2026-04-17)
- **2026-05-05:** F3.4 Frontend + F3.5 Observability delivery deadline (end-of-day)
- **2026-05-10:** F3.6 Security Phase 1 begins (can overlap with F3.5 final phases)
- **2026-05-22:** F3.6 Security complete + F3.10 DoD sign-off (final gate)

## References

- [F3 Master Delivery Calendar](../F3_MASTER_DELIVERY_CALENDAR_20260414.md)
- [F3.4 Frontend Implementation Guide](../F3_4_FRONTEND_IMPLEMENTATION_GUIDE.md)
- [F3.5 Observability Implementation Guide](../F3_5_OBSERVABILITY_IMPLEMENTATION_GUIDE.md)
- [F3.6 Security & Compliance Guide](../F3_6_SECURITY_COMPLIANCE_IMPLEMENTATION_GUIDE.md)
