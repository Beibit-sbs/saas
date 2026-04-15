# F3 Intervention Effectiveness Lab — Master Delivery Calendar (2026-04-14 → 2026-05-22)

**Document Purpose:** Comprehensive timeline showing all F3 phases, critical dates, parallel work streams, and dependencies  
**Owner:** Product Manager (coordination), Technical Lead (execution)  
**Last Updated:** 2026-04-14  
**Status:** Ready for team distribution

---

## Executive Summary - Critical Dates

| Event | Date | Duration | Blocker | Owner | Status |
|-------|------|----------|---------|-------|--------|
| **F3.2 Schema Review** | 2026-04-17 | 3 days | ✅ None (review guide provided) | Backend Lead | ⏳ Pending |
| **F3.3 Unfreeze Execution** | 2026-04-21 | 1 day (30-45 min) | F3.2 approval | DevOps Lead | ✅ Ready |
| **F3.4 + F3.5 Delivery** | 2026-04-21 → 2026-05-05 | 15 days | F3.3 unfreeze | Frontend + DevOps | ✅ Ready |
| **F3.6 Security Delivery** | 2026-05-10 → 2026-05-22 | 13 days | F3.4/F3.5 (optional, can start week before) | Security + Backend | ✅ Ready |
| **F3.8 Release Begin** | 2026-05-15 | 18 days | F3.6 security sign-off (can start w/o) | Product + DevOps | ✅ Ready |
| **F3.10 DoD Sign-Off** | 2026-05-22 | 1 day (4h) | All phases complete | Compliance | 🟡 Final gate |

---

## Week-by-Week Roadmap

### Week 1: Pre-Unfreeze Preparation (2026-04-14 → 2026-04-20)

**Week Start: Monday 2026-04-15**

| Day | Activity | Owner | Deliverable | Status |
|-----|----------|-------|-------------|--------|
| Mon 2026-04-15 | **Distribute Pre-Flight Docs** | DevOps Lead | Notify teams of F3.3 unfreeze (2026-04-21) | 🟢 Ready |
| | → F3_3_UNFREEZE_PREFLIGHT_20260414.md | | Email teams: schedule + requirements | |
| | → F3_3_UNFREEZE_QUICK_REFERENCE.md | | | |
| | → F3_2_SCHEMA_REVIEW_GUIDE.md to backend | | | |
| Tue 2026-04-16 | **Backend Schema Review** (Day 1 of 3) | Backend Lead | Read + evaluate schema guide | 🔵 In Progress |
| | Optional: Q&A with SBS on schema | Backend + SBS | Clarify FERPA/GDPR implications | |
| Wed 2026-04-17 | **Backend Schema Review** (Day 2 & 3) | Backend Lead | **SCHEMA APPROVAL DUE EOD** | ⏳ Blocking |
| | | | Confirm no conflicts, performance OK, indexes ready | |
| | **Post-Approval Steps** | | | |
| | → Notify DevOps schema approved | | Go/no-go for F3.3 unfreeze | |
| Thu 2026-04-18 | **Final Checklist: F3.3 Unfreeze** | DevOps Lead | Database backup confirmed | 🟢 Ready |
| | | | All 9/9 services healthy | |
| | | | Crew on-call assigned (backend, QA, DevOps) | |
| | | | Communication channel created (#f3-unfreeze) | |
| Fri 2026-04-19 | **Distribute Implementation Guides** | DevOps Lead | F3.4 guide → Frontend team | 🟢 Ready |
| | | | F3.5 guide → DevOps/SRE team | |
| | | | F3.6 guide → Security team | |
| | **Team Kickoff (Optional)** | Product Manager | 30-min overview of post-unfreeze execution | 🟢 Ready |
| | | | Parallel work streams (F3.4, F3.5) explained | |
| | | | Dependencies clarified | |
| Sat 2026-04-20 | **Weekend Wait** (no work expected) | N/A | Teams review guides | 🟢 Ready |
| Sun 2026-04-20 | **Final Verification** (AM early birds only) | DevOps Lead | Confirm all prerequisites still met | 🟢 Ready |
| | | | Last infra health check (9/9 services) | |

**Week 1 Success Criteria:**
- [ ] F3.2 schema approved (2026-04-17 EOD) ← **CRITICAL GATE**
- [ ] All teams notified of F3.3 unfreeze (2026-04-21, 10:00 UTC)
- [ ] On-call crew assigned + available
- [ ] Database backup confirmed
- [ ] Implementation guides distributed

---

### Week 2: F3.3 Unfreeze + F3.4/F3.5 Kickoff (2026-04-21 → 2026-04-27)

**Week Start: Monday 2026-04-21** (Unfreeze Day)

| Day | Activity | Owner | Timeline | Status |
|-----|----------|-------|----------|--------|
| **Mon 2026-04-21** | **🎯 F3.3 UNFREEZE EXECUTION** | DevOps Lead | 09:00–11:00 UTC | ✅ Ready |
| T+00:00 | Pre-unfreeze verification (Step 1) | DevOps | 9:00 UTC: All tests pass, alembic current | |
| T+00:20 | Remove freeze guards (Step 2) | Backend Lead | 9:20 UTC: 2 locations removed |  |
| T+00:35 | Wire router (Step 3) | Backend Lead | 9:35 UTC: import + include_router in main.py | |
| T+00:40 | Alembic migration (Step 4) | DevOps | 9:40 UTC: alembic upgrade head (3 tables created) | |
| T+00:50 | Rebuild backend (Step 5) | DevOps | 9:50 UTC: docker compose up -d backend | |
| T+01:00 | Run F3 tests (Step 6) | QA | 10:00 UTC: 40 tests (38 pass, 2 freeze-guard fail expected) | |
| T+01:10 | Regression gate (Step 7) | DevOps | 10:10 UTC: 7/7 architecture guards pass | |
| T+01:20 | Update docs (Step 8) | Backend Lead | 10:20 UTC: F3_EXECUTION_PLAN.md marked F3.3 ✅ | |
| T+01:30 | **F3.3 ✅ COMPLETE** | DevOps Lead | 10:30 UTC: Gate decision signed | |
| **Mon 2026-04-21 afternoon** | **F3.4 Frontend Phase 1 Kickoff** | Frontend Lead | 11:30 UTC: Start data layer (React Query hooks) | ✅ Ready |
| | → Pull latest API specs (30 sec) | Frontend | Generate TypeScript types | |
| | → Create feature branch (2 min) | Frontend | Branch: f3-cohort-analysis-dashboard | |
| | → Start Phase 1: Data fetching (3 days) | Frontend | Target: 63 unit tests by Wed | |
| **Mon 2026-04-21 afternoon** | **F3.5 Observability Phase 1 Kickoff** | DevOps Lead | 11:30 UTC: Start metrics definition | ✅ Ready |
| | → Define Prometheus metrics (2 days) | Backend + DevOps | 4 metrics: cohort_ops, latency, guardrails, queue | |
| | Target: Metrics emit on finalize/analyze by Wed | | | |
| **Tue 2026-04-22** | **F3.4 Phase 1 Progress** | Frontend | Data layer implementation | 🔵 In Prog |
| | + **F3.5 Phase 1 Progress** | Backend + DevOps | Metrics instrumentation | |
| **Wed 2026-04-23** | **F3.4 Phase 2 Kickoff** | Frontend | Page skeleton + routing (3 days: Wed-Fri) | 🟢 Ready |
| | **F3.5 Phase 2 Kickoff** | Backend + DevOps | OpenTelemetry spans (3 days: Wed-Fri) | 🟢 Ready |
| **Thu 2026-04-24** | Mid-week standup | All teams | 15-min sync (F3.4 + F3.5 progress) | 🟢 Ready |
| | | | Any blockers? Parallel execution OK? | |
| **Fri 2026-04-25** | Phase gate review (F3.4) | Frontend Lead | Phase 1 + Phase 2 done? 63+0 tests pass? | 📊 TBD |
| | Phase gate review (F3.5) | DevOps Lead | Phases 1 + 2 done? Metrics + spans OK? | |

**Week 2 Success Criteria:**
- [ ] F3.3 unfreeze completed (2026-04-21, 30–45 min SLA)
- [ ] All 40 F3 tests pass (38 pass, 2 expected failures updated)
- [ ] F3.4 Phase 1 + Phase 2 complete (63 tests done)
- [ ] F3.5 Phase 1 + Phase 2 complete (metrics + spans instrumented)
- [ ] No regressions in F2 playbooks or F1 risk engine
- [ ] Parallel execution smooth (no cross-team blockers)

---

### Week 3–4: F3.4/F3.5 Main Implementation (2026-04-28 → 2026-05-11)

**Week 3: Mon 2026-04-28 → Fri 2026-05-02**

| Day | F3.4 Frontend | F3.5 Observability | Sync | Status |
|-----|-------|------|------|--------|
| Mon | Phase 3 (table) | Phase 3 (dashboard) | Standup | 🔵 In Progress |
| | 30 tests | 0 tests (infra phase) | 15 min | |
| Tue | Phase 3 (table) | Phase 3 (dashboard) | — | 🔵 In Progress |
| | Sorting/filtering | 8 panels (KPIs, latency, errors, queue) | | |
| Wed | Phase 4 kickoff (detail page) | Phase 4 (alert rules) | Standup | 🟢 On Track |
| | Chart visualization | 4 alert rules (latency, error, pass rate, queue) | 15 min | |
| Thu | Phase 4 (outcomes panel) | Phase 4 → Phase 5 | — | 🟢 On Track |
| | Confidence bands | SLO targets + recording rules | | |
| | 63 tests | 0 tests (infra phase) | | |
| Fri | Phase 5 kickoff (wizard) | Phase 5 (SLO + Load test prep) | Phase gates | 📊 TBD |
| | Form validation | Planning load test scenarios | 30 min review | |

**Week 3 Gate Criteria:** F3.4 must complete phases 1–4 by Fri (table + detail done, wizard starting)

**Week 4: Mon 2026-05-05 → Fri 2026-05-09** (Overlap with F3.5 → F3.6)

| Day | F3.4 Frontend | F3.5 Observability | F3.6 Security | Sync |
|-----|-------|------|------|------|
| Mon | Phase 5 (wizard) | Phase 6 (load test) | Prep (Phase 1-2 planning) | Standup |
| | 40 tests | 8 test scenarios running | Team divide: FERPA/GDPR | 15 min |
| Tue | Phase 6 (E2E tests) | Phase 6 (ongoing) | Phase 1 (FERPA validators) | — |
| | 25 Playwright E2E | Metrics validated under load | ~15 tests | |
| Wed | Phase 7 (accessibility) | Phase 7 (documentation) | Phase 2 (GDPR retention cleanup) | Standup |
| | axe-core scan + fixes | SLO runbook, troubleshooting | ~18 tests | 15 min |
| Thu | Phase 8 (performance) | Phase 7 (continuing) | Phase 3 (RBAC enforcement) | — |
| | LCP < 2.5s, CLS < 0.1 | All 14 documentation tests | ~20 tests | |
| **Fri 2026-05-05** | **→ Phase 9 + 10 (final QA)** | **→ DELIVERY COMPLETE** | Phase 4 (audit logging) | **Gate Review** |
| | Type-check + code review | 0 failures, all SLO ready | ~14 tests | |
| | **→ F3.4 DELIVERY COMPLETE** | **→ F3.5 DELIVERY COMPLETE** | F3.6 ~40% done | |

**F3.4 & F3.5 Delivery Target: 2026-05-05 EOD** ✅ **CRITICAL GATE**

---

### Week 5: F3.6 Security Delivery (2026-05-10 → 2026-05-22)

**Timing: Overlaps with F3.8 release prep (but security sign-off gates go-live)**

| Week | Phase | Duration | Tests | Owner | Status |
|-----|-------|----------|-------|-------|--------|
| W5: Mon 2026-05-10 | Phase 1: FERPA validators | 3 days | 15 | Backend | On time |
| | Phase 2: GDPR retention | 2 days | 18 | Backend + DPA | On time |
| W5-6: Wed 2026-05-12 | Phase 3: RBAC enforcement | 2 days | 20 | Backend + Security | On time |
| W6: Fri 2026-05-14 | Phase 4: Audit logging | 3 days | 14 | Backend + DevOps | On time |
| | Phase 5: Encryption (pgcrypto) | 2 days | 12 | Security + Backend | On time |
| W7: Mon 2026-05-17 | Phase 6: Security testing (SAST/DAST/pen-test) | 3 days | 25 | Security + Pen-tester | On time |
| W7-8: Wed 2026-05-19 | Phase 7: Compliance sign-off | 4 days | 15 | Compliance + Security | Final gate |

**F3.6 Delivery Target: 2026-05-22 EOD** ✅ **DELIVERY COMPLETE + SIGN-OFF**

---

### Week 5: F3.8 Release Begins (2026-05-15 → ongoing)

**Timing: Starts before F3.6 complete (can parallelize), but security sign-off gates final release**

| Stage | Duration | Start Date | Gate | Status |
|-------|----------|-----------|------|---------|
| **Stage 1: Internal Canary** | 24h | 2026-05-15 (or post F3.6 sign-off) | Internal staff; P95 latency ≤ 2s | ✅ Ready |
| **Stage 2: Partner Canary** | 72h | 2026-05-16 (or +1 day) | 2 pilot institutions; guardrail pass > 80% | ✅ Ready |
| **Stage 3: Staged Rollout** | 2 weeks | +4 days | 5% → 25% → 50% → 75% by phase | ✅ Ready |
| **Stage 4: GA** | — | 2026-06-02 | 100% of tenants enabled | ✅ Ready |

**Release Coordination:**
- F3.8 deployment can start **2026-05-15**, but feature flag starts **disabled**
- F3.6 security sign-off (2026-05-22) **gates feature flag flip to enabled**
- Stage 1 internal canary only after compliance approval

---

##Critical Dependencies Map

```
┌────────────────────────────────────────────────────────┐
│                 F3 Delivery Timeline Map                │
└────────────────────────────────────────────────────────┘

2026-04-14 (NOW)
    ↓
2026-04-17 (GATE: F3.2 Schema Approval)
    ↓ [Blocking]
2026-04-21 (F3.3 Unfreeze: 30-45 min)
    ├─→ ✅ Router wired + freeze guards removed
    ├─→ ✅ 40 F3 tests still passing (2 expected updates)
    ├─→ ✅ All 9/9 services healthy
    └─→ Parallel Execution Begins:
        │
        ├─ F3.4 Frontend ········· 2026-04-21 → 2026-05-05 (15 days)
        │  Phase 1: Data layer
        │  Phase 2: Page skeleton
        │  Phase 3: Table component
        │  Phase 4: Detail + chart
        │  Phase 5: Create wizard
        │  Phase 6: E2E tests (25)
        │  Phase 7: Accessibility
        │  Phase 8: Performance
        │  Phase 9: Type safety
        │  Phase 10: Final QA
        │  └─→ Target: 221 tests, delivery 2026-05-05
        │
        ├─ F3.5 Observability ··· 2026-04-21 → 2026-05-05 (15 days)
        │  Phase 1: Prometheus metrics (4)
        │  Phase 2: OpenTelemetry spans
        │  Phase 3: Grafana dashboard (8 panels)
        │  Phase 4: Alert rules (4)
        │  Phase 5: SLO targets
        │  Phase 6: Load testing (8 scenarios)
        │  Phase 7: Documentation + sign-off
        │  └─→ Target: 8 dashboard + SLO ready, delivery 2026-05-05
        │
        └─ [WAIT for F3.4/F3.5 delivery before starting F3.6 full-steam]
            (Can start prep/planning 2026-05-05)

2026-05-05 (GATE: F3.4 Frontend + F3.5 Observability Delivery)
    ├─→ ✅ Frontend: 3 pages live, 221 tests pass
    ├─→ ✅ Observability: Dashboard + alerts operational
    └─→ Parallel Execution Continues:
        │
        ├─ F3.6 Security ········· 2026-05-10 → 2026-05-22 (13 days)
        │  Phase 1: FERPA validators
        │  Phase 2: GDPR retention cleanup
        │  Phase 3: RBAC enforcement
        │  Phase 4: Audit logging (ELK)
        │  Phase 5: Encryption at rest (pgcrypto)
        │  Phase 6: Security testing (SAST/DAST/pen-test)
        │  Phase 7: Compliance sign-off
        │  └─→ Target: 119 tests + 4 sign-offs, delivery + approval 2026-05-22
        │
        └─ [F3.8 Release prep ongoing, but gates on F3.6 security approval]
            F3.8 Stage 1 can start 2026-05-15 in internal canary mode
            (Feature flag: disabled until F3.6 approved)

2026-05-22 (GATE: F3.6 Security Sign-Off + F3.10 DoD Approval)
    ├─→ ✅ F3.6: All compliance officers sign-off
    ├─→ ✅ F3.10: Definition-of-Done gate approval
    └─→ F3.8 Release progression:
        Stage 1: ✅ Internal (already done 2026-05-15, waiting approval)
        Stage 2: → Partner canary (24-72h post-approval)
        Stage 3: → Staged rollout (2 weeks)
        Stage 4: → GA (target 2026-06-02)

2026-06-02
    └─→ F3 Complete: 100% of tenants enabled
```

---

## Team Assignments & On-Call

### Frontend Team (F3.4: 2026-04-21 → 2026-05-05)

**Lead:** [TBD] (Frontend Team Lead)  
**Team:** 1–2 frontend engineers  
**Effort:** 21 person-days (full-time, 15 calendar days)  
**On-Call:** 2026-04-21 (post-unfreeze support)

**Daily Standup:** 09:00 UTC (30 min)  
**Phase Gates:** Every Fri (~1h review with backend/DevOps)

### DevOps/SRE Team (F3.5: 2026-04-21 → 2026-05-05)

**Lead:** [TBD] (DevOps Lead)  
**Team:** 1 backend engineer (metrics) + 1 DevOps engineer (infra)  
**Effort:** 42 person-days (21 per person, 15 calendar days)  
**On-Call:** 2026-04-21 (unfreeze execution)

**Daily Standup:** 09:00 UTC (shared with frontend)  
**Load Testing:** 2026-05-03 to 2026-05-04

### Security Team (F3.6: 2026-05-10 → 2026-05-22)

**Lead:** [TBD] (Security Officer)  
**Team:** 1 security engineer + 1 backend engineer (validators) + 1 compliance officer  
**Effort:** 160 person-hours (13 calendar days)  
**On-Call:** 2026-05-19 to 2026-05-22 (pen-test + sign-off)

**Phase Gates:** Weekly (Mon, Wed, Fri)  
**Pen-Test Window:** 2026-05-17 to 2026-05-19 (3 consecutive days)

### DevOps/Release Team (F3.8: 2026-05-15 → 2026-06-02)

**Lead:** [TBD] (Release Manager)  
**Team:** 1 DevOps engineer + 1 product manager (feature flag monitoring)  
**Effort:** 40 person-hours (6 weeks, part-time)  
**On-Call:** Throughout 4-stage rollout

**Daily Checks:** 10:00 UTC + 22:00 UTC (each stage) — 30 min each  
**Escalation:** If error rate > 0.5% → pause rollout, investigate

---

## Roles & Responsibilities

| Role | Task | Phase | Approval? |
|------|------|-------|-----------|
| **Product Manager** | F3 roadmap coordination, updates | All | — |
| **Backend Lead** | Schema review, RBAC, security | F3.2/F3.3/F3.6 | Schema ✅, Security ✅ |
| **Frontend Lead** | F3.4 execution, E2E testing | F3.4 | Delivery ✅ |
| **DevOps Lead** | F3.3 unfreeze, F3.5 metrics/dashboard | F3.3/F3.5 | Unfreeze ✅, Observability ✅ |
| **Security Officer** | SAST/DAST/pen-test, FERPA/GDPR | F3.6 | Security sign-off ✅ |
| **DPA (Data Protection Officer)** | GDPR review, data handling | F3.6 | GDPR sign-off ✅ |
| **Compliance Officer** | Audit trail, documentation | F3.6 | Compliance sign-off ✅ |
| **QA Lead** | F3.3 test updates, F3.4/F3.5/F3.6 test plans | All | Testing ✅ |

---

## Communication Plan

### Standup Meetings

**Daily Standup:** 09:00 UTC (30 min)  
- Attendees: Frontend Lead, DevOps Lead, Backend Lead, QA Lead
- Format: What done | What next | Blockers?
- Frequency: Mon–Fri (2026-04-21 → 2026-05-22)
- Channel: Slack #f3-standup + optional Zoom

**Weekly Sync:** Fri 14:00 UTC (1h)  
- Attendees: Product Manager, all team leads, compliance officer
- Agenda: Phase gate review, next week plan, escalations
- Frequency: Fri (2026-04-18 → 2026-05-22)
- Channel: Zoom + recording

### Work Streams

**#f3-unfreeze** (2026-04-21 only, 1 day)
- Unfreeze execution coordination
- Real-time updates (every 10 min during execution)
- Post-unfreeze debrief

**#f3-frontend** (2026-04-21 → 2026-05-05)
- F3.4 component updates, code review, blockers
- Phase gate discussions

**#f3-observability** (2026-04-21 → 2026-05-05)
- F3.5 metrics, dashboard, SLO discussions
- Load test results, alert validation

**#f3-security** (2026-05-10 → 2026-05-22)
- F3.6 FERPA/GDPR/RBAC implementation
- Pen-test coordination, findings remediation
- Sign-off tracking

**#f3-release** (2026-05-15 → 2026-06-02)
- F3.8 release coordination
- 4-stage rollout monitoring
- Feature flag status

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation | Owner |
|------|------------|--------|-----------|-------|
| F3.2 schema approval delayed past 2026-04-17 | Low | High (blocks F3.3) | Review guide clear, escalate if needed | Backend Lead |
| F3.4 frontend behind schedule (Phase 1-2 slip) | Medium | Medium (can still deliver 2026-05-05?) | Daily standups, phase gates, scope cuts if needed | Frontend Lead |
| F3.5 observability data quality issues (metrics missing) | Medium | Medium (dashboard incomplete) | Load testing early (phase 6), data quality tests | DevOps Lead |
| F3.6 pen-test finds critical vulnerability | Medium | Critical (blocks release) | Known risk, 3-day remediation time slots, escalation path | Security Officer |
| F3.8 release error rate spike (> 0.5%) | Low | Critical (user impact) | Gradual rollout (5%/24h), rollback every 30 min, on-call ready | Release Manager |

---

## Success Criteria by Phase

### F3.3 Unfreeze (2026-04-21)
- [ ] 8-step wiring checklist executed in ≤ 45 min
- [ ] All 40 F3 tests pass (38 pass, 2 expected freeze-guard updates)
- [ ] 7/7 platform regression gates pass
- [ ] Zero P0 incidents during/after unfreeze
- [ ] Documentation updated (F3_EXECUTION_PLAN.md)

### F3.4 Frontend (2026-05-05)
- [ ] 3 pages live (list, detail, create wizard)
- [ ] 221 tests passing (196 unit + 25 E2E)
- [ ] WCAG 2.1 A compliance (accessibility audit pass)
- [ ] LCP < 2.5s, CLS < 0.1 (performance gates)
- [ ] No console errors (production build)
- [ ] Code review approved
- [ ] Deployed to staging

### F3.5 Observability (2026-05-05)
- [ ] 4 Prometheus metrics emitting data
- [ ] OpenTelemetry spans visible in Jaeger (10% sampling)
- [ ] 8-panel Grafana dashboard operational
- [ ] 4 alert rules firing on threshold breaches
- [ ] SLO targets documented + baselined
- [ ] 8/8 load test scenarios pass
- [ ] On-call runbook complete

### F3.6 Security (2026-05-22)
- [ ] 119 security + compliance tests passing
- [ ] SAST scan: 0 critical/high severity
- [ ] DAST/Pen-test: All scenarios tested, no exploits found
- [ ] FERPA validators enforced (cohort min 20)
- [ ] GDPR cleanup automated (7-year retention)
- [ ] RBAC enforced on all endpoints
- [ ] Audit logging to ELK (Kibana dashboard visible)
- [ ] Encryption at rest (pgcrypto) verified
- [ ] All 4 sign-offs obtained (FERPA, GDPR, Security, Compliance)

### F3.10 DoD (2026-05-22)
- [ ] All deliverables complete (F3.1 → F3.9)
- [ ] All gates passed (F3.3, F3.4/F3.5, F3.6)
- [ ] Compliance checklist signed
- [ ] Release readiness confirmed
- [ ] **F3 DELIVERY COMPLETE** ✅

---

## Post-Delivery: F3.8 Release (2026-05-15 → 2026-06-02)

### 4-Stage Rollout

| Stage | Duration | Start | Gate | Scope | KPI Target |
|-------|----------|-------|------|-------|-----------|
| **1: Internal** | 24h | 2026-05-15* | Feature flag enabled (internal team) | Staging → 10 internal users | P95 ≤ 2s, error rate < 1% |
| **2: Partner** | 72h | 2026-05-16* | Feature flag enabled (2 pilot tenants) | Production: 2 institutions (~5% of users) | Guardrail pass > 80%, P95 ≤ 2s |
| **3: Rollout** | 2 weeks | +4 days | Feature flag enabled (5% → 75% gradual) | Production: 5% → 25% → 50% → 75% | Error rate < 0.5%, SLO maintained |
| **4: GA** | — | 2026-06-02 | Feature flag enabled (100%) | Production: All tenants | Full SLO envelope (99.5% availability) |

*Stage 1 can start 2026-05-15, but only progresses post F3.6 security sign-off (2026-05-22)

### Monitoring During Rollout

| Metric | Normal | Caution | Critical |
|--------|--------|---------|----------|
| Error Rate | < 0.5% | 0.5–1.0% | > 1.0% → **PAUSE** |
| P95 Latency | ≤ 2.0s | 2.0–3.0s | > 3.0s → **PAUSE** |
| Guardrail Pass | > 80% | 70–80% | < 70% → **PAUSE** |
| Queue Depth | < 10 | 10–50 | > 50 → INVESTIGATE |

**Pause Criteria:** If any "Critical" metric triggered, pause rollout to next stage for 24h investigation.  
**Rollback Criteria:** If issue unresolved after 24h, roll back to prior stage (feature flag: disabled).

---

## Document Summary

This calendar coordinates:
- ✅ F3.3 unfreeze (2026-04-21): 30-min router wiring
- ✅ F3.4 frontend (2026-04-21→2026-05-05): 10-phase, 221 tests
- ✅ F3.5 observability (2026-04-21→2026-05-05): 7-phase, 4 metrics, 8 dashboard
- ✅ F3.6 security (2026-05-10→2026-05-22): 7-phase, 119 tests, 4 sign-offs
- ✅ F3.8 release (2026-05-15→2026-06-02): 4-stage rollout (internal→partner→staged→GA)
- ✅ F3.10 DoD (2026-05-22): Final approval gate

**Total Delivery Timeline:** 2026-04-14 (now) → 2026-06-02 (F3 GA)  
**Effort:** ~400+ person-hours across 5 teams

**Status:** All preparation complete. F3.3 unfreeze ready for 2026-04-21 execution. Teams can begin post-unfreeze work immediately (F3.4, F3.5 parallel).

---

## Next Actions

**Immediate (before 2026-04-17):**
1. Distribute this calendar to all teams
2. Confirm F3.2 schema approval review (backend lead + DPA)
3. Schedule team kickoff (optional, 15-30 min overview)
4. Verify database backup exists + on-call crew assigned

**Before 2026-04-21:**
1. All crew on-call + notifications ready
2. Slack channels created (#f3-unfreeze, #f3-standup, #f3-frontend, #f3-observability, #f3-security, #f3-release)
3. Implementation guides reviewed by team leads
4. Zoom/meeting links prepared for daily standups

**On 2026-04-21 (Unfreeze Day):**
1. Execute F3.3 8-step wiring checklist (09:00–11:00 UTC)
2. Backend team updates 2 freeze-guard test cases (post-unfreeze)
3. Frontend + DevOps teams start Phase 1 work (11:30 UTC)

**Ongoing (2026-04-21 → 2026-05-22):**
1. Daily standups (09:00 UTC)
2. Weekly phase gate reviews (Fri 14:00 UTC)
3. Real-time blockers reported in Slack
4. Critical gates tracked (F3.2 approval, F3.3 unfreeze, F3.4/F3.5 delivery, F3.6 sign-off)
