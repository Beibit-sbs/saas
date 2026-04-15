# F3.4 Frontend Specification — Intervention Cohort Analysis Dashboard

**Version:** v0.5 (Skeleton, unfrozen post-delivery)  
**Status:** Spec Ready (implementation unfrozen after 2026-04-21)  
**Target Implementation:** 2026-05-05 (after F3.3 backend wiring)  
**Technology Stack:** Next.js 14.2, React 18, TypeScript, Tailwind CSS, TanStack Query

---

## Overview

F3 Frontend provides institutional administrators with a dashboard to:
1. **View past intervention cohorts** — filter by playbook, date, outcome type
2. **Analyze effectiveness** — drill into cohort outcomes, guardrail status, confidence bands
3. **Generate reports** — export cohort analysis as PDF/markdown for institutional review

**Access:** `/admin/interventions/cohorts` (requires `effectiveness.read` scope)

---

## Page Structure

### Page 1: Cohorts List (default route)

**Route:** `/admin/interventions/cohorts`

**Purpose:** Browse all intervention cohorts for the tenant.

**Layout:**

```
┌─────────────────────────────────────────────────────────────────┐
│ F3: Intervention Cohort Analysis                         [Filter] │
├─────────────────────────────────────────────────────────────────┤
│ Filters: [Playbook ▾] [Status ▾] [Date range ▾] [Clear all]    │
├─────────────────────────────────────────────────────────────────┤
│ Icon │ Cohort Name           │ Playbook │ Outcomes │ Status     │
├──────┼───────────────────────┼──────────┼──────────┼────────────┤
│ 📊   │ Academic Coaching     │ RiskMit  │ 2/2 ✅   │ Analyzed   │
│      │ Fall 2025 (50 treated)│          │          │            │
│      │ _____________________│ ________│________│____________│
│      │ Created: 2026-04-10   │ Latest:  │ Dropout: │              │
│      │ Analyst: prog_mgr_001 │ Analyzed │ −4pp ✅   │              │
├──────┼───────────────────────┼──────────┼──────────┼────────────┤
│ 📊   │ Tutoring Program      │ CoacAccel│ 1/2 ⏳   │ Finalized  │
│      │ Fall 2025 (35 treated)│          │ (waiting │              │
│      │                       │          │  outcomes)             │
│ ...                                                               │
└─────────────────────────────────────────────────────────────────┘
[< Previous] [Page 1 of 3] [Next >]
```

**Features:**
- **Pagination:** 10 cohorts per page
- **Sort:** By name, date, outcome count, status
- **Filter widgets:**
  - Playbook (multi-select dropdown)
  - Status (multi-select: Finalized | Analyzed | Error)
  - Date range (calendar picker: analysis_window_end)
  - Search text (matches cohort_name, playbook_name)
- **Row click:** Navigate to [Cohort Detail](#page-2-cohort-detail)

**Data source:**
```
GET /api/admin/interventions/cohorts/list?
  page=1&
  limit=10&
  playbook_ids=1,2&
  status=analyzed&
  date_min=2026-01-01&
  date_max=2026-12-31&
  search=academic
```

---

### Page 2: Cohort Detail \ Analysis

**Route:** `/admin/interventions/cohorts/[cohort_id]`

**Purpose:** View detailed analysis for a specific cohort, including outcomes and guardrail status.

**Layout (two-column):**

```
┌──────────────────────────────────────────────────────────────────┐
│ Academic Coaching Fall 2025  [← Back to List] [Share] [Export]   │
├──────────────────────────────────────────────────────────────────┤
│ Left (60%)              │ Right (40%)                             │
├─────────────────────────┼──────────────────────────────────────────┤
│ COHORT SUMMARY          │ GUARDRAIL STATUS                          │
│ ─────────────────────   │ ──────────────────────                    │
│ Playbook: RiskMitigation│ ✅ Confidence Band Valid                 │
│ Status: Analyzed (2026) │ ✅ Distribution Uniform                  │
│ Created: 2026-04-10     │ ✅ Data Complete (93%)                   │
│ Analysis date: 2026...  │                                           │
│ Analyzed by: prog...    │ Report Status: READY                     │
│                         │ (All guardrails passed)                  │
│ Treated: 50 students    │                                           │
│ Control: 48 students    │                                           │
├─────────────────────────┼──────────────────────────────────────────┤
│ OUTCOMES (Sorted by     │ OUTCOME DETAILS                           │
│ type & segment)         │ ─────────────────                         │
│                         │                                           │
│ [Dropdown: All Segments]│ Metric: Dropout Rate (all students)      │
│ ─────────────────────── │ ──────────────────────────────────────   │
│ Dropout Rate (all):     │ Treated: 14.0%  |  Control: 18.0%       │
│   Uplift: −4.0pp ✅     │                                           │
│   CI: [−7.0, −1.0]      │ Uplift: −4.0 percentage points           │
│   Data complete: 96%    │                                           │
│                         │ 95% Confidence Interval:                 │
│ GPA Improvement (all):  │ [−7.0pp, −1.0pp]                         │
│   Uplift: +0.07 GPA ✅  │                                           │
│   CI: [0.01, 0.13]      │ Interpretation:                          │
│   Data complete: 95%    │ • Intervention reduces dropout           │
│                         │   by 1–7 percentage points               │
│ [+ Show by segment]     │ • Effect is statistically significant    │
│ ─────────────────────── │ • Guardian checks pass → report ready    │
│                         │                                           │
│ [Visualizations]        │ [Chart: Uplift by segment if available]  │
│ • Uplift chart (bar)    │                                           │
│ • Confidence band       │ [Export button]                           │
│   (error bars)          │                                           │
└─────────────────────────┴──────────────────────────────────────────┘
```

**Features:**

1. **COHORT SUMMARY (top-left):**
   - Metadata: playbook, status, created date, analyst name
   - Cohort sizes: treated, control

2. **GUARDRAIL STATUS (top-right):**
   - Three checkboxes: Confidence Band Valid ✅/❌, Distribution Uniform ✅/❌, Data Complete ✅/❌
   - Color coding: Green (pass) / Red (fail)
   - **If any fail:** Red warning banner "Report not ready for publication"

3. **OUTCOMES LIST (center-left):**
   - Sortable by outcome type (Dropout Rate, GPA Improvement, ...)
   - Segment filter dropdown (All Students, Low Risk, High Risk, ...)
   - Card layout for each outcome:
     - Outcome name + segment
     - Uplift value (large, color-coded: green for negative dropout, blue for GPA)
     - Confidence interval [lower, upper]
     - Data completeness %

4. **OUTCOME DETAIL (right panel):**
   - Drill-in when user clicks an outcome card
   - Shows:
     - Treated vs Control rates (side-by-side)
     - Uplift calculation
     - 95% CI with interpretation
     - Data completeness per group
     - Chart: Uplift bar chart with confidence error bars

5. **Visualization:**
   - Bar chart: Treated vs Control across outcomes
   - Confidence band + point estimate (scatter + error bars)
   - Segmentation view (if available): Uplift by risk band

**Data source:**
```
GET /api/admin/interventions/cohorts/{cohort_id}
GET /api/admin/interventions/cohorts/{cohort_id}/analyze
GET /api/admin/interventions/cohorts/{cohort_id}/outcomes
```

---

### Page 3: Cohort Create (Wizard)

**Route:** `/admin/interventions/cohorts/create`

**Purpose:** Initiate a new cohort analysis.

**Flow (3-step wizard):**

```
Step 1: Select Playbook
┌──────────────────────────────────────────┐
│ Which playbook did you use?              │
│ [Search: _______________________]        │
│ └─ RiskMitigation                        │
│    └─ Academic Coaching                  │
│       └─ Tutoring Program                │
│       └─ Peer Mentoring                  │
│ [Next >]                                 │
└──────────────────────────────────────────┘

Step 2: Cohort Metadata
┌──────────────────────────────────────────┐
│ Cohort Details                           │
│ Cohort name: [Academic Coaching Fall 25] │
│ Start date:  [2025-08-01]                │
│ End date:    [2026-05-15]                │
│ Treated:     [50]                        │
│ Control:     [48]                        │
│ [< Back] [Next >]                        │
└──────────────────────────────────────────┘

Step 3: Review & Confirm
┌──────────────────────────────────────────┐
│ Ready to finalize cohort?                │
│ ✓ Academic Coaching Fall 2025            │
│ ✓ 50 treated, 48 control                 │
│ ✓ Window: 2025-08-01 to 2026-... │
│ [< Back] [Create Cohort] [Cancel]        │
└──────────────────────────────────────────┘
```

**Data source:**
```
POST /api/admin/interventions/cohorts/finalize
  { playbook_id, cohort_name, analysis_window_start, 
    analysis_window_end, treated_count, control_count }
```

---

## Authentication & Authorization

**Scope required:** `effectiveness.read` (list/view) + `effectiveness.write` (create/finalize)

**Per-tenant isolation:** Users see only cohorts from their assigned tenant (via `X-Tenant-ID` header)

---

## Error Handling

### Custom Error Pages

| Error | Message | Action |
|-------|---------|-------|
| Cohort not found | "Cohort does not exist. [← Back to list]" | 404 page |
| Permission denied | "You don't have access to this analysis. Contact your admin." | 403 page |
| Guardrail fail | "⚠️ Report is not ready for publication (guardrails failed). See details." | Warning card + details |
| API error | "Failed to load cohort. [Retry] [← Back]" | Retry button + fallback |

---

## Responsive Design

- **Desktop (1024px+):** Two-column detail layout
- **Tablet (768–1023px):** Stacked layout (summary on top, outcomes below)
- **Mobile (< 768px):** List view only; detail view is full-screen; chart rendering disabled

---

## Performance Targets

| Metric | Target |
|--------|--------|
| List page load (FCP) | < 1.5s |
| Detail page load (FCP) | < 2s |
| Sort/filter reaction | < 300ms |
| Chart render (50 outcomes) | < 500ms |
| Accessibility (Lighthouse A11y) | ≥ 90 |

---

## Accessibility (WCAG 2.1 AA)

- [ ] Keyboard navigation (Tab, Enter, Esc)
- [ ] Screen reader labels (`<label>`, ARIA `aria-label`)
- [ ] Contrast ratio ≥ 4.5:1
- [ ] No focus trap
- [ ] Landmark navigation (`<main>`, `<nav>`)

---

## Testing Plan (E2E Playwright)

| Scenario | Location. |
|----------|----------|
| Load list page, filter by playbook, sort | `frontend/e2e/smoke/f3-intervention-cohort-analysis.spec.ts` |
| Click cohort → view detail, verify guardrails render | Same file |
| Create new cohort via wizard | Same file |
| Verify 404 when cohort missing | Same file |

---

## Implementation Order (post-unfreeze 2026-04-21)

| Phase | Task | Deps |
|-------|------|------|
| 1 | Pages scaffold (routes, layout, basic HTML) | None |
| 2 | List page: table + filter + pagination | API endpoints live |
| 3 | Detail page: summary + outcomes + charts | API endpoints live |
| 4 | Create wizard: 3-step form + submission | Finalize API endpoint |
| 5 | Charts: uplift bars, confidence bands | Chart library (Chart.js / Recharts) |
| 6 | Error handling + custom error pages | Full |
| 7 | Accessibility audit + fixes | Full |
| 8 | E2E Playwright tests + CI | Full |
| 9 | Responsive design fixes + mobile testing | Full |
| 10 | Performance optimization (bundle, lazy load) | Full |

---

## Success Criteria

F3.4 Frontend is **complete** when:

- [ ] All 3 pages (List, Detail, Create) functional and tested
- [ ] All API endpoints correctly wired
- [ ] Guardrail status displays correctly (all pass → green, any fail → red)
- [ ] Charts render confidently (no blank axes)
- [ ] Mobile responsive (≥ 90 Lighthouse performance score)
- [ ] Accessibility audit ≥ 90 (Lighthouse)
- [ ] E2E tests + CI passing
- [ ] Documentation for PM/Dean end-user is written

---

## References

- **Backend API spec:** [F3_EXECUTION_PLAN.md#api-contract](F3_EXECUTION_PLAN.md)
- **Styles guide:** `frontend/tailwind.config.ts`
- **Component library:** `frontend/shared/components/`
- **Testing:** Playwright + Vitest
