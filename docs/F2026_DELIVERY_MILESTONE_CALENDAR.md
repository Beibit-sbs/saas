# F2026 Product Delivery Milestone Calendar

**Baseline Date:** 2026-04-18 (Friday)  
**Phase:** F1/F2 post-release governance → F3 expansion → F4 preparation  
**Status:** ✅ Ready for execution  

---

## 🎯 Critical Path (April-May 2026)

### Week 1: F1/F2 Day-7 Review Cycle

| Date | Phase | Action | Artifact | Owner | Status |
|------|-------|--------|----------|-------|--------|
| **2026-04-18 (Fri)** | F1/F2 post-release | Pre-delivery prep complete: day7 checklist, pre-commit hooks, pre-validation script ready | ERP-QA-66, 67, 68 | DevOps/QA | ✅ DONE |
| **2026-04-19 (Sat)** | F1/F2 pre-execution | `make day7-f1f2-pre-validation` — dry-run all gates/scripts without side effects | Validation report | DevOps | ⏳ Scheduled |
| **2026-04-20 (Sun)** | **F1/F2 Day-7 Due** | `make day7-f1f2-one-shot` — official F1/F2 review, gates, DoD sign-off (fail-closed until today) | F1.9/F2.9 final artifacts | QA/Product | ⏳ Scheduled |

**Expected Timeline:** ~1 hour (review 30min + gates 15min + sign-off 15min)

**Gate Sequence:**
1. F1 day7 review + risk baseline snapshot
2. F2 day7 review + playbook application snapshot
3. F1.9 gate validation → PASS/FAIL
4. F2.9 gate validation → PASS/FAIL
5. F1.10 DoD sign-off artifact generation
6. F2.10 DoD sign-off artifact generation

**Sign-off Criteria:**
- ✓ All 1950 backend tests PASS, coverage 83.99%
- ✓ Risk data persisted (baseline snapshot)
- ✓ Playbook recommendations generated
- ✓ No breaking API changes
- ✓ No data loss vs day-1

---

### Week 2: F3 Phase 1 Kickoff (Data + Observability Parallel)

| Date | Phase | Action | Artifact | Owner | Status |
|------|-------|--------|----------|-------|--------|
| **2026-04-21 (Mon)** | **F3.3/F3.4/F3.5 Readiness** | `make f3-kickoff-readiness` — unified gate for F3.3 unfreeze + F3.4 API health + F3.5 alerts | F3 readiness report | DevOps | ⏳ Scheduled |
| **2026-04-21 (Mon) 11:30 UTC** | **F3.4/F3.5 Phase 1 Start** | Start F3.4 (data layer) + F3.5 (metrics) **in parallel** (independent streams) | F3.4 branch, F3.5 branch | Backend/Observability | ⏳ Scheduled |
| **2026-04-25 (Fri)** | F3 Weekly Check-1 | Gate: F3.4/F3.5 progress snapshot, no blockers | Weekly report | QA | ⏳ Scheduled |
| **2026-05-05 (Mon)** | **F3.4/F3.5 Phase 1 Target** | F3.4 data layer complete + F3.5 metrics complete (ready for Phase 2) | F3.4 Phase 1 DoD, F3.5 Phase 1 DoD | Backend/Observability | ⏳ Scheduled |

**Timeline:** 14 days (2 weeks) for Phase 1 parallel work  
**Parallel Streams:**
- F3.4: Effectiveness score dataflow (independent DB writes)
- F3.5: Metrics instrumentation (independent metric emission)

---

### Week 3+: F3 Security & F4 Preparation

| Date | Phase | Action | Artifact | Owner | Status |
|------|-------|--------|----------|-------|--------|
| **2026-05-10 (Sat)** | **F3.6 Security Start** | Begin F3.6 compliance delivery (audit prep, encryption, data privacy) | F3.6 branchg | Security | ⏳ Scheduled |
| **2026-05-22 (Thu)** | **F3.10 DoD + F4 Unfreeze** | Complete F3.6 security, finalize all F3 artifacts, sign-off **enables F4 development** | F3 final DoD artifacts | Product | ⏳ Scheduled |

**Timeline:** 12 days (May 10-22) for F3.6 security phase

---

### Week 4+: F4 Kickoff (After F3 DoD)

| Date | Phase | Action | Artifact | Owner | Status |
|------|-------|--------|----------|-------|--------|
| **2026-04-20 (Sun)** | F4 Phase A Check | Status check only: verify F1.9/F2.9 PASS, F3 on track (no code changes) | F4 status report | PM | ⏳ Scheduled |
| **2026-05-23 (Fri)** | **F4 Phase B Kickoff** | (After F3.10 DoD confirmed) `make f4-kickoff-readiness` → F4 development unfrozen → Phase 1 start | F4 branch, F4 Phase 1 start | Backend/Product | ⏳ Scheduled |
| **2026-06-20 (Fri)** | **F4 Phase 1-5 Target** | F4 estimated completion (4 weeks, similar to F3.4 cycle) | F4 DoD artifacts | Backend | ⏳ Estimated |

**Freeze Policy:** ⚠️ NO F4 development code before 2026-05-22 (mandatory, F3 dependency)

---

## 📋 Sequential Feature Chain (F5-F20)

All F5-F20 features **strictly sequential** — each feature blocks until prior feature DoD sign-off.

| Feature | Blocked Until | Est. Start | Est. Duration | Est. End |
|---------|------------------|------------|--------|---------|
| **F5: Degree Autopilot** | F4 DoD | 2026-06-21 | 4 weeks | 2026-07-18 |
| **F6: Smart Timetable** | F5 DoD | 2026-07-19 | 4 weeks | 2026-08-15 |
| **F7: Workload Copilot** | F6 DoD | 2026-08-16 | 4 weeks | 2026-09-12 |
| **F8-F20: Rest of features** | Sequential on prior | 2026-09-13+ | ? weeks | TBD |

**No parallel development in F5-F20.** Each feature must wait for prior DoD sign-off before kickoff.

---

## 🔐 Mandatory Gates & Freeze Points

| Gate | Trigger | Effect | Policy |
|------|---------|--------|--------|
| **F1.9/F2.9 fail-closed pre-day7** | day < 2026-04-20 | Block F1/F2 sign-off (fail-closed) | Cannot sign-off early |
| **F3.4/F3.5 readiness** | 2026-04-21 morning | Gate F3 Phase 1 execution | Pre-condition check |
| **F3.10 DoD sign-off** | Must complete by 2026-05-22 | Gate F4 development unfreeze | Mandatory dependency |
| **F4 code freeze** | Until 2026-05-22 | Block F4 development PR merges | Development paused |
| **F5-F20 sequential block** | Prior feature DoD | Block next feature start | No parallel lanes |

---

## 📊 Success Metrics

✓ **F1/F2 Day-7 PASS:** All gates green, sign-off artifacts generated  
✓ **F3.4/F3.5 Phase 1 Complete:** Data layer + metrics ready by 2026-05-05  
✓ **F3.6 Security Complete:** Compliance artifacts ready by 2026-05-22  
✓ **F4 Kickoff Ready:** Phase B starts 2026-05-23 on-schedule  
✓ **Zero cascading delays:** Each phase on-time unblocks next

---

## 🚀 Quick Reference Commands

```bash
# One-time setup (already done)
make day7-f1f2-pre-validation      # 2026-04-19 evening

# Day-7 execution (2026-04-20)
make day7-f1f2-one-shot            # F1/F2 official review + sign-off

# F3 kickoff (2026-04-21)
make f3-kickoff-readiness          # Unified F3.3/F3.4/F3.5 validation
# Then start F3.4 Phase 1 (data)
# And start F3.5 Phase 1 (metrics)

# F4 preparation (2026-05-22 after F3.10 DoD)
make f4-kickoff-readiness          # Entry criteria check

# Weekly status check (every Friday)
grep -E "F[1-4]\.[0-9].*Status|Weekly" docs/AUDIT_SBS_2026.md
```

---

## 📝 Notes

- All dates are **UTC** (align with international team)
- Gate scripts are **fail-closed** (block on any error)
- All automation is **docker-only** (no host-side processes)
- Timeline assumes on-schedule execution; catches slips by ~1 week
- F5-F20 start dates scale based on actual F4 completion

---

**Last Updated:** 2026-04-18  
**Next Review:** 2026-04-20 (post day-7 sign-off)
