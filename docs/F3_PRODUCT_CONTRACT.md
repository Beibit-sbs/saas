# F3.1 Product Contract — Intervention Effectiveness Analysis

**Version:** v1.0  
**Status:** Ready for PM/Dean Review & Sign-Off  
**Created:** 2026-04-13  
**Target Sign-Off:** 2026-04-14

---

## Executive Summary

F3 is a system that answers: **"Did this intervention improve student outcomes?"**

F3 accepts an **intervention cohort** (group of students receiving the same intervention, e.g., "Academic coaching for at-risk freshmen in Fall 2025") and compares their outcomes against a control group to quantify intervention effectiveness and confidence in that effect.

**Primary users:** Program Managers, Deans, Institutional Researchers  
**Decision object:** Intervention effectiveness report (per-cohort, per-outcome metric)

---

## Problem Statement

Today, institutions cannot reliably measure whether specific interventions (academic coaching, tutoring, mentoring) actually improve student outcomes. Without this data:

- Program managers cannot justify cohort budgets or staffing
- Deans cannot identify which interventions drive institutional KPIs (graduation, retention, GPA)
- Institutional researchers cannot conduct evidence-based program improvement
- Resource allocation is based on intuition, not evidence

---

## Solution Scope

### What F3 Does ✅

1. **Accepts a finalized cohort:** "These 50 students received academic coaching; 45 completed the program."
2. **Compares outcomes:** Compares treated outcomes (academic coaching group) against control outcomes (similar students without coaching).
3. **Quantifies impact:**
   - **Primary KPI:** `intervention_cohort_uplift_percent` = $ \frac{\text{treated_outcome} - \text{control_outcome}}{\text{control_outcome}} \times 100 $
   - Examples: −4pp dropout reduction, +0.07pp GPA improvement
4. **Reports confidence:** Confidence interval (95%) around the uplift estimate
5. **Guards against unreliability:** Three guardrail checks before reporting:
   - Confidence band is valid (lower < upper, width ≤ threshold)
   - Outcome distribution is uniform across student segments (e.g., by risk band, major)
   - Outcome data completeness ≥ 90%

### What F3 Does NOT Do ❌

- **Does not design experiments:** F3 assumes cohort is already defined; it does not randomize or match control groups.
- **Does not conduct causal inference:** F3 reports correlation, not proven causation. The institution is responsible for control group selection rigor.
- **Does not store individual student IDs or outcomes:** F3 reports
 only aggregated cohort-level statistics (e.g., "50 treated, 48 control, 4pp uplift").
- **Does not integrate with external research tools:** F3 is standalone microservice; external researchers must export data to SAS/R/Python for advanced analysis.

---

## User Personas & Decision Flows

### Persona 1: Program Manager (Tactical)

**Goal:** Justify continued funding for academic coaching cohort.  
**Decision:** "Can we continue this program?"

**F3 flow:**
1. After cohort completes: "Academic Coaching Fall 2025 — 50 treated, 48 control"
2. F3 analyzes: "Dropout uplift: −4pp (95% CI: −7pp to −1pp)"
3. Manager decision: "Control group effect is strong and credible → funding approved"

### Persona 2: Dean (Strategic)

**Goal:** Rank interventions by ROI to inform reallocation.  
**Decision:** "Which interventions drive most graduation/retention improvement?"

**F3 flow:**
1. Portfolio view: List all completed intervention cohorts for the current year
2. Sort by impact: "Academic coaching: −4pp dropout" ranks higher than "Peer mentoring: −1pp dropout"
3. Dean decision: "Expand academic coaching budget; deprioritize peer mentoring"

### Persona 3: Institutional Researcher (Analytical)

**Goal:** Publish or present evidence of program effectiveness.  
**Decision:** "Is this program evidence-based and defensible?"

**F3 flow:**
1. Generate detailed report: Cohort metadata, control group description, outcome data completeness, confidence intervals, guardrail checks
2. Export to markdown/PDF for institutional board review
3. Researcher decision: "All guardrails pass → safe to publish"

---

## Outcomes Tracked (v1 Scope)

F3.1 supports two outcome metrics. Additional metrics can be added post-pilot.

| Outcome | Definition | Unit | F3.1 Support |
|---------|-----------|------|--------------|
| **Dropout Rate** | % of students who did not re-enroll following cohort year | percentage point (pp) | ✅ Primary |
| **GPA Improvement** | Average term GPA post-intervention vs baseline | GPA scale (0–4.0) | ✅ Primary |
| Retention Rate | % re-enrolled | pp | ⏳ Future |
| Graduation Rate | % degree awarded within 4 years | pp | ⏳ Future |
| Course Completion | % courses completed (not dropped) | pp | ⏳ Future |

---

## Guardrail KPIs — Reliability Checks

F3 reports are only valid if all three guardrails pass.

### Guardrail 1: Confidence Band Validity

**Definition:** 95% confidence interval around uplift must be valid and sufficiently tight.

**Rules:**
- Lower bound < Upper bound (interval is not inverted)
- Interval width (upper − lower) ≤ 8pp (precision threshold; too-wide intervals are unreliable)

**Example:**
- ✅ Valid: uplift −4pp, CI [−7pp, −1pp] → width 6pp → pass
- ❌ Invalid: uplift −2pp, CI [−15pp, +10pp] → width 25pp → fail (too uncertain)

### Guardrail 2: Outcome Distribution Uniformity

**Definition:** Uplift should be consistent across student segments (risk bands, enrollment status, major).

**Rules:**
- Segment-level uplift variance (coefficient of variation) ≤ 1.5
- No single segment has uplift ≥ |15pp| different from cohort-level (outlier detection)

**Example:**
- ✅ Pass: Low-risk uplift −3pp, High-risk uplift −5pp → variance 0.4 → pass
- ❌ Fail: Low-risk uplift −1pp, High-risk uplift +8pp → variance 2.1 → fail (heterogeneous effect, suspicious)

### Guardrail 3: Data Completeness

**Definition:** Outcome data must be available for sufficient portion of cohort.

**Rules:**
- Treated group completeness (outcome data / cohort size) ≥ 90%
- Control group completeness ≥ 90%
- Combined (treated + control with outcome) ≥ 85%

**Example:**
- ✅ Pass: 48/50 treated outcomes (96%), 46/48 control (96%), 94/98 combined → pass
- ❌ Fail: 40/50 treated (80%) → fail (missing 10 treated outcomes)

---

## API Contract (v1.0)

F3 is accessed via admin API (requires `effectiveness.read` / `effectiveness.write` scope).

### Endpoint 1: Create/Finalize Cohort

```
POST /api/admin/interventions/cohorts/finalize
Authorization: Bearer <token with effectiveness.write>
Content-Type: application/json

{
  "playbook_id": 42,                       // FK to F2 playbook
  "cohort_name": "Academic Coaching Fall 2025",
  "analysis_window_start": "2025-08-01",   // When intervention started
  "analysis_window_end": "2026-05-15",     // When intervention ended
  "treated_count": 50,                     // Students in intervention group
  "control_count": 48                      // Students in control group
}

Response 201:
{
  "id": 999,
  "cohort_name": "Academic Coaching Fall 2025",
  "status": "finalized",
  "finalized_at": "2026-04-14T18:32:00Z",
  "finalized_by": "program_mgr_001"
}
```

### Endpoint 2: Get Latest Cohort for Playbook

```
GET /api/admin/interventions/cohorts/latest?playbook_id=42
Authorization: Bearer <token with effectiveness.read>

Response 200:
{
  "id": 999,
  "cohort_name": "Academic Coaching Fall 2025",
  "playbook_id": 42,
  "treated_count": 50,
  "control_count": 48,
  "status": "analyzed",
  "created_at": "2026-04-10T...",
  "analysis_window_end": "2026-05-15"
}
```

### Endpoint 3: Analyze Cohort & Get Outcomes

```
POST /api/admin/interventions/cohorts/{cohort_id}/analyze
Authorization: Bearer <token with effectiveness.read>
Content-Type: application/json

{
  // This endpoint aggregates stored outcomes for the cohort
  // and returns effectiveness report
}

Response 200:
{
  "cohort_id": 999,
  "outcomes": [
    {
      "type": "dropout_rate",
      "segment_name": "all",
      "treated_rate": 14.0,
      "control_rate": 18.0,
      "uplift_percent": -4.0,
      "confidence_lower": -7.0,
      "confidence_upper": -1.0
    },
    {
      "type": "gpa_improvement",
      "segment_name": "all",
      "treated_improvement": 2.95,
      "control_improvement": 2.88,
      "uplift_gpa": 0.07,
      "confidence_lower": 0.01,
      "confidence_upper": 0.13
    }
  ],
  "guardrails": {
    "confidence_band_valid": true,
    "distribution_uniform": true,
    "data_complete": true,
    "overall_pass": true
  },
  "report_ready": true
}
```

### Endpoint 4: Get Outcomes List

```
GET /api/admin/interventions/cohorts/{cohort_id}/outcomes
Authorization: Bearer <token with effectiveness.read>

Response 200: [
  { "id": 1, "type": "dropout_rate", "segment": "all", "treated": 14, "control": 18, ... },
  { "id": 2, "type": "gpa_improvement", "segment": "all", "treated": 2.95, "control": 2.88, ... }
]
```

---

## Limitations & Assumptions

1. **F3 assumes control groups are well-matched:** F3 does not validate whether control groups are truly comparable to treated groups. The institution must ensure control selection is rigorous (propensity matching, randomization, or natural experiment design).

2. **F3 does not adjust for confounders:** If treatment group differs from control group on factors that affect outcomes (e.g., prior GPA, motivation), F3 cannot account for this. Institutions should pre-match or use F3 results as starting point for deeper analysis.

3. **F3 outcome measures are institution-specific:** F3 supports "dropout rate" and "GPA improvement" in v1. Other metrics (graduation, retention, job placement) require custom outcome tracking SQL.

4. **F3 results represent correlation, not causation:** Even if guardrails pass, the uplift may be due to confounding. F3 is evidence generator, not causal proof. Institutions must interpret results in context of their control design rigor.

5. **Small sample sizes have wide confidence bands:** If cohort size < 30, confidence bands will be very wide, often failing Guardrail 1. Institutions should batch smaller cohorts or use pilot data cautiously.

---

## Success Criteria (go/no-go)

F3.1 is **production-ready** when:

- [ ] **Schema approved by backend team:** Data schema, FK constraints, indexing reviewed. No conflicts with F2.2.
- [ ] **API contract documented and reviewed:** All 4 endpoints, request/response shapes, error cases, auth reviewed.
- [ ] **Guardrail logic implemented and tested:** All 3 guardrails compute correctly; test examples pass.
- [ ] **Testing skeleton complete:** 40+ tests across schema, service layer, E2E (before/after decision logic).
- [ ] **Zero security gaps:** Input validation (cohort_name length, date ranges), RBAC (only `effectiveness.write` for finalize), tenant isolation verified.
- [ ] **Documentation ready:** Product contract, data contract, observability spec, runbook for PM usage.

---

## Sign-Off

**For PM/Dean Review:**

I agree that this product contract accurately represents the F3 intervention effectiveness analysis system and commit to proceeding with F3.1–F3.2 design (frozen delivery until F2.10 PASS).

- [ ] PM/Dean name: ________________     Date: ________
- [ ] No objections raised during review period (2026-04-13 to 2026-04-14)

---

## References

- **Product Design:** [docs/F3_EXECUTION_PLAN.md](F3_EXECUTION_PLAN.md)
- **Data Contract:** [backend/app/modules/interventions/effectiveness_models.py](../backend/app/modules/interventions/effectiveness_models.py)
- **Testing Plan:** [docs/F3_EXECUTION_PLAN.md#testing-skeleton](F3_EXECUTION_PLAN.md#testing-skeleton)
