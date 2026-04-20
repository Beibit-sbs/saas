# F3 Intervention Effectiveness Lab — Design Phase (2026-04-13)

## Executive Summary

F3 is the **measurement layer** for F1/F2. While F1 detects risks and F2 automates interventions, F3 answers: **"Did the interventions actually work?"**

This document captures F3.1 (Product Contract) and F3.2 (Data Contract) — **design-only phase** running parallel to F1.9/F2.9 validation timebox (2026-04-14 to 2026-04-20).

**Constraint:** F3.3-F3.10 delivery **frozen until F2.10 PASS (2026-04-21)**.

---

## F3.1 Product Contract

### Problem Statement

Post-intervention outcomes are currently **opaque**:
- Advisors don't know if their interventions actually improved student outcomes
- Deans can't measure intervention ROI by program/cohort
- No feedback loop to refine playbooks based on success/failure patterns
- Cannot justify continued investment in AI-driven interventions without evidence

### Primary Users

1. **Program Managers** — measure ROI per intervention type/playbook
2. **Deans/Registrars** — cohort-level effectiveness, drill-down by risk band
3. **Data Analysts** — build custom cohort uplift analyses
4. **Platform Admin** — monitor quality of intervention system (precision/recall of assigned interventions)

### Decision Cadence & Object

| Element | Detail |
|---------|--------|
| **Trigger** | Manual: "Analyze these 2 playbooks across Q1 cohort" / "Model: weekly automated cohort uplift report" |
| **Decision object** | `intervention_cohort_analysis` — group of 50+ students who received playbook X; compare their outcome trajectory vs. control cohort (no playbook) |
| **Output** | `cohort_uplift_report`: north-star metric delta (e.g., "dropout_rate went from 18% → 14% = 4 pp impact"), confidence band, segment breakdown (by risk band / program / demographic) |
| **Action** | Scale playbook? Refine playbook steps? Retrain model? Disable playbook? |

### Key Characteristics

- **Cohort-scoped analysis** — not individual-level (cohorts = 50+ students who got same playbook in same week)
- **Control selection** — historical matched cohorts (no playbook) vs. current (with playbook) using propensity matching
- **Outcome measurement** — end-of-term dropout rate, GPA improvement, course completion %, persistence to next term
- **Explainability** — segment breakdown (is uplift uniform or concentrated in high-risk band?)
- **Observability** — confidence band, sample size, selection bias controls (documented limitations)

### Explicit Non-Goals

❌ Individual treatment effect (ITE) — too noisy for pre-pilot, no causal modeling infrastructure  
❌ Real-time feedback to playbook execution — F2 runs autonomously, F3 is post-hoc analysis layer  
❌ Fairness/equity algorithms — tracking, not optimization (yet)  
❌ A/B testing framework — no random assignment in pre-pilot

### KPI Definitions (North-Star + Guardrails)

**North-Star KPI:**
```
intervention_cohort_uplift_percent = 
  (outcome_rate_with_intervention - outcome_rate_without_intervention) 
  / outcome_rate_without_intervention * 100
```

Example: If control cohort had 18% dropout and treated cohort had 14% dropout:
```
uplift = (14 - 18) / 18 * 100 = -22% (good: 4 percentage points reduction)
```

**Guardrail KPI 1: Confidence Band Width**
```
confidence_band_width = p95_uplift - p5_uplift (must be < 15 pp for reliable insights)
```

If report shows "uplift = 4pp ± 20pp", that's too noisy; scale down playbook or collect more cohorts.

**Guardrail KPI 2: Segment Uniformity**
```
segment_uplift_diversity = max(segment_uplifts) - min(segment_uplifts)
```

If high-risk band shows +8pp but low-risk band shows -2pp, playbook may be misaligned; trigger review.

**Guardrail KPI 3: Outcome Measurement Completeness**
```
outcome_measurement_rate = students_with_outcome_recorded / cohort_size
```

Must be ≥ 85% for reliable analysis; flag as "incomplete" if < 85%.

---

## F3.2 Data Contract v1

### Entities (in dependency order)

#### Input Tables (from F1/F2)

| Table | Key Fields | Source | Usage |
|-------|-----------|--------|-------|
| `app_student_risk_snapshots` | `id`, `tenant_id`, `student_id`, `risk_band`, `scored_at` | F1.2 schema | Filter initial cohort by risk band |
| `app_playbook_executions` | `id`, `tenant_id`, `playbook_id`, `student_id`, `case_id`, `triggered_by`, `status`, `started_at`, `completed_at` | F2.2 schema | **Primary cohort definition** |
| `app_playbook_step_executions` | `id`, `execution_id`, `step_id`, `status`, `performed_at`, `outcome_note` | F2.2 schema | Playbook completion % (guard: was execution actually done?) |
| `app_students` | `id`, `tenant_id`, `student_profile_id`, `program_id`, `cohort_id_at_enrollment`, `enrollment_status`, `created_at` | Existing core | Cohort stratification (by program, by demo) |
| `app_courses` | `id`, `course_code`, `credits`, `gpa_factor` | Existing core | Calculate GPA impact |
| `app_grades` | `id`, `student_id`, `course_id`, `grade_letter`, `gpa_points`, `earned_at` | Existing core | **Outcome measurement** (GPA) |
| `app_enrollments` | `id`, `student_id`, `term_id`, `status`, `enrolled_at`, `dropout_at` | Existing core | **Outcome measurement** (dropout) |

#### F3 Specific Tables (new)

**`app_intervention_cohorts`** — immutable snapshots of cohorts for analysis

| Column | Type | Constraint | Purpose |
|--------|------|-----------|---------|
| `id` | uuid | PK | Cohort ID |
| `tenant_id` | uuid | FK(tenants) | Tenant isolation |
| `playbook_id` | uuid | FK(playbooks) | Which playbook treated this cohort |
| `cohort_name` | text | — | E.g. "Q1 2026 Retention Playbook Cohort" |
| `created_at_utc` | timestamp | NOT NULL | When cohort was finalized (end-of-period) |
| `analysis_window_start` | date | — | First day of intervention period |
| `analysis_window_end` | date | — | Last day of intervention period (outcome measurement starts after) |
| `student_count` | int | — | Denominator for rates |
| `data_completeness_pct` | numeric | — | % of students with outcome data |
| `created_at` | timestamp | NOT NULL | Record creation timestamp |

**`app_intervention_cohort_members`** — individual students in cohort

| Column | Type | Constraint | Purpose |
|--------|------|-----------|---------|
| `id` | uuid | PK | — |
| `cohort_id` | uuid | FK(app_intervention_cohorts) | — |
| `tenant_id` | uuid | FK(tenants) | Tenant isolation |
| `student_id` | uuid | FK(students) | Which student |
| `playbook_execution_id` | uuid | FK(playbook_executions) | Link to F2 |
| `risk_band_at_intervention` | enum | — | Risk band when playbook triggered (from F1 snapshot) |
| `program_id` | uuid | FK(programs) | Segmentation |
| `demographic_cohort` | text | — | E.g. "first_gen" / "low_income" (for segmentation) |
| `added_at` | timestamp | — | — |

**`app_intervention_cohort_outcomes`** — measured outcomes per cohort

| Column | Type | Constraint | Purpose |
|--------|------|-----------|---------|
| `id` | uuid | PK | — |
| `cohort_id` | uuid | FK(app_intervention_cohorts) | — |
| `tenant_id` | uuid | FK(tenants) | — |
| `outcome_type` | enum | `dropout_rate`, `gpa_improvement`, `course_completion_pct`, `persistence_pct` | Which outcome |
| `outcome_value_treated` | numeric | — | E.g. 0.14 for 14% dropout |
| `outcome_value_control` | numeric | — | Historical matched cohort value |
| `uplift_pp` | numeric(5,2) | — | Percentage point difference |
| `uplift_confidence_p5` | numeric(5,2) | — | 5th percentile uplift (monte carlo or bootstrap) |
| `uplift_confidence_p95` | numeric(5,2) | — | 95th percentile uplift |
| `measurement_completeness_pct` | numeric | — | % of students with outcome recorded |
| `segment_name` | text | NULL | E.g. "high_risk_band", NULL for overall |
| `measured_at_utc` | timestamp | — | When outcome was finalized |

**Indexes:**
```sql
CREATE INDEX idx_intervention_cohorts_tenant_id ON app_intervention_cohorts(tenant_id);
CREATE INDEX idx_intervention_cohorts_playbook_id ON app_intervention_cohorts(playbook_id);
CREATE INDEX idx_cohort_members_cohort_id ON app_intervention_cohort_members(cohort_id);
CREATE INDEX idx_cohort_outcomes_cohort_id ON app_intervention_cohort_outcomes(cohort_id);
CREATE INDEX idx_cohort_outcomes_outcome_type ON app_intervention_cohort_outcomes(outcome_type);
```

---

## F3 API Contract (skeleton)

### Endpoints (to be implemented F3.3+)

```
POST /api/v1/interventions/cohorts/finalize
  Input: playbook_id, analysis_window_start, analysis_window_end
  Output: cohort_id, member_count, data_completeness_pct
  
GET /api/v1/interventions/cohorts/{cohort_id}/outcomes
  Output: { cohort_id, outcomes: [ { outcome_type, uplift_pp, confidence_p5, confidence_p95, segments: [...] } ] }
  
GET /api/v1/interventions/cohorts/latest/by-playbook/{playbook_id}
  Output: List[cohort_summary]
  
POST /api/v1/interventions/cohorts/{cohort_id}/analyze
  Input: optional control_cohort_id (override historical), propensity_score_adjustments
  Output: detailed_analysis_report (JSON)
```

---

## F3 Testing Strategy (skeleton phase)

### Unit Tests (mock data)

**File:** `backend/tests/modules/interventions/test_intervention_cohort_models.py`

```python
def test_intervention_cohort_creation():
    """Cohort with 50+ members can be created."""
    assert cohort.student_count == 50

def test_outcome_measurement_completeness_guard():
    """Reject cohort outcomes if completeness < 85%."""
    with pytest.raises(ValidationError):
        OutcomeRecord(measurement_completeness_pct=0.84, ...)

def test_uplift_calculation_formula():
    """Verify uplift = (treated - control) / control * 100."""
    assert uplift_pp == pytest.approx(4.0, abs=0.1)  # 14% vs 18% → -4pp

def test_segment_uniformity_check():
    """Flag if segment uplifts diverge > 15pp."""
    assert report.flags.segment_uniformity_warning == True
```

### Integration Tests (mock F1/F2 data)

**File:** `backend/tests/modules/interventions/test_intervention_cohort_service.py`

```python
def test_finalize_cohort_from_playbook_executions():
    """Cohort builder pulls from F2 playbook_executions + F1 risk_snapshots."""
    # Mock 50 F2 playbook_executions + 50 F1 risk_snapshots
    cohort = CohortService.finalize_cohort(playbook_id=..., window_start=..., window_end=...)
    assert cohort.student_count == 50

def test_propensity_matched_control_selection():
    """Select historical cohort using propensity score matching."""
    # Mock: treated cohort avg risk_score=0.72, control cohort avg risk_score=0.70 (matched)
    assert abs(treated.avg_risk - control.avg_risk) < 0.05

def test_outcome_aggregation_by_segment():
    """Outcome measured per segment (risk_band, program) separately."""
    outcomes = CohortService.get_outcomes(cohort_id=..., segments=['risk_band', 'program_id'])
    assert len(outcomes) == num_risk_bands * num_programs  # cartesian product
```

### E2E Smoke (design-only)

**File:** `frontend/e2e/smoke/f3-intervention-cohort-analysis.spec.ts`

```typescript
test("F3 Cohort Analysis page loads and displays mock uplift report", async ({ page }) => {
    // 1. Navigate to /console/interventions/cohort-analysis
    await page.goto("/console/interventions/cohort-analysis");
    
    // 2. Select playbook "Q1 Retention Playbook"
    await page.selectOption('select[name="playbook"]', 'q1-retention');
    
    // 3. Mock API response: /api/v1/interventions/cohorts/latest/by-playbook/q1-retention
    // Returns: cohort_id=..., student_count=50, uplift=4pp ± 2pp
    
    // 4. Assert UI renders: "Uplift: 4pp (95% CI: 2pp - 6pp)"
    expect(page.locator("text=Uplift: 4pp")).toBeDefined();
});
```

---

## Dependency Constraints

### Hard Dependencies (F3 blocks on F2)

| F3 Requirement | F2 Provides | Blocker if Missing |
|---|---|---|
| Playbook execution events (start/complete) | `app_playbook_executions` table | Cannot create cohorts |
| Outcome tracking linked to executions | `app_intervention_outcome_tracking.playbook_execution_id` FK | Cannot join treatment to outcome |
| Playbook metadata (name, trigger) | `app_playbooks.name, trigger_threshold_id` | Hard-code in F3 tests |

### Soft Dependencies (F3 can mock)

| F3 Requirement | F1/F2 Provides | F3 Workaround |
|---|---|---|
| Real risk_snapshots at intervention time | F1 `app_student_risk_snapshots` | Mock: random risk_band per student |
| Real playbook execution latency profile | F2 `playbook_step_executions.performed_at - execution.started_at` | Mock: P95 = 3 days (hardcoded) |
| Real outcome data (grades, enrollments) | Existing `app_grades`, `app_enrollments` | Mock: synthetic grades/dropouts |

---

## Timeline & Acceptance Criteria

### Current Phase: F3.1-F3.2 Design (2026-04-13 to 2026-04-20)

✅ **Deliverables:**
- [ ] Product Contract (this document) — DONE
- [ ] Data Contract v1 (tables, schema, FK) — DONE
- [ ] API Contract (endpoints, request/response shapes) — DONE
- [ ] Testing skeleton (3-5 mock tests per layer: unit/integration/e2e) — PENDING (F3.2 deliverable)
- [ ] Alembic migration script (schema creation, no backfill) — PENDING (F3.2 deliverable)
- [ ] Django models (ORM definition for 3 F3 tables) — PENDING (F3.2 deliverable)

❌ **NOT in scope:**
- Actual cohort finalization logic
- Real propensity matching (will implement F3.3)
- UI build-out beyond wireframes

### Unblock Conditions for F3.3+ Delivery

✅ **PASS Condition:**
```
F2.10_GATE = PASS  # All F2.9 day-1/3/7 reviews done
AND
F3.1_PRODUCT_CONTRACT = APPROVED  # PMs/Deans sign off on KPIs
AND
F3.2_DATA_CONTRACT = AVAILABLE  # No schema conflicts with F2
```

❌ **FAIL Condition:**
```
F2.9 discovers: "playbook_execution_latency_p95 > 7 days"
  → Cannot measure outcome in pre-pilot (term ends in 6 weeks)
  → F3 needs redesign (outcome_measurement_window must shift)
  → F3.3 delivery delayed pending F2 remediation
```

---

## Handoff Plan (F3.1 → F3.2)

**Input from F3.1:**
- Product Contract (north-star: `intervention_cohort_uplift_percent`)
- KPI thresholds (guardrails: confidence < 15pp, uniformity < 10pp)

**Output to F3.2:**
- Data/API Contract (ready for backend team to build schema)
- Test skeletons (ready for mock-data population)

**Blockers for F3.3 to unblock:**
- F2.10 PASS (date: 2026-04-21)
- Schema migration (date: 2026-04-22)
- First real cohort finalized (date: 2026-05-15, end of Q1)

---

## Document History

| Date | Author | Change |
|------|--------|--------|
| 2026-04-13 | Agent | Initial F3.1+F3.2 design (parallel to F1.9/F2.9 validation) |
