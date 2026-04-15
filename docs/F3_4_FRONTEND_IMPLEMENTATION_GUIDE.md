# F3.4 Frontend Implementation Guide — Start Post-Unfreeze (2026-04-21)

**Released:** 2026-04-14 (pre-unfreeze preparation)  
**Execution Start:** 2026-04-21 (post F3.3 unfreeze)  
**Target Delivery:** 2026-05-05 (15 days)  
**Status:** Preparation phase (ready to execute on unfreeze day)

---

## Quick Start (For Frontend Team Lead - 2026-04-21)

After F3.3 unfreeze completes (~11:00 UTC 2026-04-21):

1. **Verify API is live** (30 seconds)
   ```bash
   # Check all 4 F3 endpoints exist
   curl http://localhost:8000/api/admin/interventions/cohorts/health
   
   # Verify framework works (should return 200 or 401 if auth required)
   curl -X POST http://localhost:8000/api/admin/interventions/cohorts/finalize \
     -H "Content-Type: application/json" \
     -d '{}' 2>&1 | head -3
   ```

2. **Pull latest F3 API specs** (1 minute)
   ```bash
   cd /home/sbs/AI/frontend
   npm run generate:openapi-types  # Auto-generate TypeScript types from backend
   ```

3. **Create F3 feature branch** (2 minutes)
   ```bash
   git checkout -b f3-cohort-analysis-dashboard
   git pull origin main
   ```

4. **Start Phase 1: Data Fetching Layer** (Today, 2026-04-21)
   - See detailed roadmap below

---

## Full 10-Phase Implementation Roadmap

### Phase 1: Data Fetching & API Client (2026-04-21 to 2026-04-23, 3 days)

**Objective:** Create React Query hooks for all 4 F3 API endpoints

**UI Deliverables:** None (data layer only)

**Files to Create:**
- `frontend/shared/api/hooks/useInterventionCohorts.ts` — Query hooks (24 lines)
- `frontend/shared/api/hooks/useCohortOutcomes.ts` — Outcome queries (18 lines)
- `frontend/shared/api/hooks/useCohortAnalysis.ts` — Analysis mutations (15 lines)
- `frontend/shared/api/types/cohort.ts` — Generated types from auto-schema (auto-generated)

**Code Template (useInterventionCohorts.ts):**
```typescript
import { useQuery, useMutation } from '@tanstack/react-query';
import { bffProxy } from '@/shared/server/bff-proxy';
import type { CohortFinalizeRequest, CohortReadSchema } from '@/shared/api/types/cohort';

export const useCohortsQuery = (tenantId: number) =>
  useQuery({
    queryKey: ['cohorts', tenantId],
    queryFn: async () => {
      const res = await bffProxy.get(`/api/admin/interventions/cohorts`, {
        headers: { 'X-Tenant-ID': String(tenantId) },
      });
      return res.json() as Promise<CohortReadSchema[]>;
    },
  });

export const useFinalizeCohortMutation = () =>
  useMutation({
    mutationFn: async (payload: CohortFinalizeRequest) => {
      const res = await bffProxy.post(`/api/admin/interventions/cohorts/finalize`, payload);
      return res.json() as Promise<CohortReadSchema>;
    },
  });

export const useCohortOutcomesQuery = (cohortId: number, tenantId: number) =>
  useQuery({
    queryKey: ['cohort-outcomes', cohortId],
    queryFn: async () => {
      const res = await bffProxy.get(
        `/api/admin/interventions/cohorts/${cohortId}/outcomes`,
        { headers: { 'X-Tenant-ID': String(tenantId) } }
      );
      return res.json() as Promise<CohortOutcomeListResponse>;
    },
  });
```

**Test Deliverables (3 files):**
- `frontend/__tests__/api/hooks/useInterventionCohorts.test.ts` — Mock API + query tests (25 assertions)
- `frontend/__tests__/api/hooks/useCohortOutcomes.test.ts` — Outcome hook tests (20 assertions)
- `frontend/__tests__/api/hooks/useCohortAnalysis.test.ts` — Mutation tests (18 assertions)

**Exit Criteria:**
- [ ] All 3 hooks export correctly
- [ ] TypeScript types auto-generated from backend
- [ ] All 63 unit tests pass (25+20+18)
- [ ] No console.error or missing return types
- [ ] Ready for Phase 2 (UI components can use these)

---

### Phase 2: Page Skeleton & Navigation (2026-04-23 to 2026-04-25, 3 days)

**Objective:** Create routing + page shell for 3-page dashboard

**Files to Create:**
- `frontend/app/(admin)/console/interventions/cohorts/page.tsx` — List page shell (40 lines)
- `frontend/app/(admin)/console/interventions/cohorts/[id]/page.tsx` — Detail page shell (35 lines)
- `frontend/app/(admin)/console/interventions/cohorts/create/page.tsx` — Create page shell (30 lines)
- `frontend/shared/config/navigation.ts` — Add F3 nav items (3 lines)

**Navigation Tree (after phase 2):**
```
/console/interventions/
  ├─ cohorts/ (List page)
  ├─ cohorts/[id]/ (Detail page)
  └─ cohorts/create/ (Create wizard)
```

**Code Template (List page shell):**
```typescript
// frontend/app/(admin)/console/interventions/cohorts/page.tsx
'use client';

import { Suspense } from 'react';
import Link from 'next/link';
import { useCohortsQuery } from '@/shared/api/hooks/useInterventionCohorts';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';

export default function CohortsListPage() {
  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Cohorts</h1>
        <Link href="/console/interventions/cohorts/create" className="btn btn-primary">
          Create Cohort
        </Link>
      </div>

      <Suspense fallback={<LoadingState />}>
        <CohortsList />
      </Suspense>
    </div>
  );
}

function CohortsList() {
  const { data: cohorts, isLoading, error } = useCohortsQuery(/* tenantId */);
  
  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;
  
  return (
    <div className="space-y-4">
      {/* Phase 3: Table component will replace this */}
      <p className="text-gray-600">List view (table component coming Phase 3)</p>
      {cohorts?.map(cohort => (
        <div key={cohort.id}>{cohort.cohort_name}</div>
      ))}
    </div>
  );
}
```

**Exit Criteria:**
- [ ] All 3 routes accessible (`/cohorts`, `/cohorts/[id]`, `/cohorts/create`)
- [ ] Navigation items visible in sidebar
- [ ] Pages render without errors (shell + skeleton only)
- [ ] Ready for Phase 3 (table + form components)

---

### Phase 3: List Page Table Component (2026-04-25 to 2026-04-27, 3 days)

**Objective:** Build data table with filtering & sorting

**Files to Create:**
- `frontend/app/(admin)/console/interventions/cohorts/components/CohortsTable.tsx` (120 lines)
- `frontend/__tests__/admin/interventions/CohortsTable.test.tsx` (30 assertions)

**Features:**
- Display: ID, Name, Size, Status (4 columns)
- Sorting: By Name, By Date Created (2 directions)
- Filtering: By Status (dropdown: draft/finalized/analyzed)
- Actions: View Button → `/cohorts/[id]`

**Code Template:**
```typescript
'use client';

import { useState } from 'react';
import { DataTable } from '@/shared/ui/data-table';
import { useCohortsQuery } from '@/shared/api/hooks/useInterventionCohorts';

export function CohortsTable() {
  const [status, setStatus] = useState<'draft' | 'finalized' | 'analyzed' | undefined>();
  const { data: cohorts } = useCohortsQuery(/* tenantId */);

  const filtered = cohorts?.filter(c => !status || c.status === status) ?? [];

  const columns = [
    { header: 'Name', accessorKey: 'cohort_name', sortable: true },
    { header: 'Size', accessorKey: 'cohort_size', cell: (row) => `${row.cohort_size} students` },
    { header: 'Status', accessorKey: 'status', cell: (row) => <Badge variant={row.status} /> },
    {
      header: 'Actions',
      cell: (row) => <Link href={`/cohorts/${row.id}`}>View</Link>,
    },
  ];

  return (
    <div>
      <StatusFilter value={status} onChange={setStatus} />
      <DataTable columns={columns} data={filtered} />
    </div>
  );
}
```

**Exit Criteria:**
- [ ] Table displays cohorts with 4 columns
- [ ] Sorting works (click header)
- [ ] Filtering by status works
- [ ] No loading loops, all data renders correctly
- [ ] 30 unit tests passing
- [ ] Ready for Phase 4 (detail page)

---

### Phase 4: Detail Page & Outcomes Display (2026-04-27 to 2026-05-01, 5 days)

**Objective:** Show cohort details + analysis outcomes with confidence bands visualization

**Files to Create:**
- `frontend/app/(admin)/console/interventions/cohorts/[id]/components/CohortDetails.tsx` (80 lines)
- `frontend/app/(admin)/console/interventions/cohorts/[id]/components/OutcomesPanel.tsx` (100 lines)
- `frontend/app/(admin)/console/interventions/cohorts/[id]/components/ConfidenceBandChart.tsx` (70 lines, Recharts)
- `frontend/__tests__/admin/interventions/CohortDetail.test.tsx` (35 assertions)
- `frontend/__tests__/admin/interventions/OutcomeViz.test.tsx` (28 assertions)

**Features:**
- Display cohort metadata (name, size, treatment/control split, date range)
- Show all outcomes in a list
- Chart: Confidence band visualization (treatment vs control vs confidence band range)
- WCAG A11y: aria-labels, contrast ≥ 4.5:1, keyboard navigation

**Chart Example (Recharts):**
```typescript
<LineChart data={outcomes}>
  <CartesianGrid />
  <XAxis dataKey="outcome_type" />
  <YAxis />
  <Tooltip />
  <Line 
    type="monotone" 
    dataKey="treatment_metric" 
    stroke="#3b82f6" 
    name="Treatment Group"
  />
  <Line 
    type="monotone" 
    dataKey="control_metric" 
    stroke="#9ca3af" 
    name="Control Group"
  />
  {/* Confidence band area */}
  <Area 
    type="monotone" 
    dataKey="confidence_lower" 
    fill="#dbeafe" 
    stroke="transparent"
  />
</LineChart>
```

**Exit Criteria:**
- [ ] Cohort details display correctly
- [ ] All outcomes rendered in a table/list
- [ ] Confidence band chart renders without errors
- [ ] 63 unit tests passing (35+28)
- [ ] Chart accessible to screen readers (aria-label)
- [ ] Mobile responsive (tablet/mobile view tested)
- [ ] Ready for Phase 5 (create wizard)

---

### Phase 5: Create Wizard UI (2026-05-01 to 2026-05-03, 3 days)

**Objective:** Multi-step form for creating new cohorts

**Files to Create:**
- `frontend/app/(admin)/console/interventions/cohorts/create/page.tsx` (160 lines, 4 steps)
- `frontend/app/(admin)/console/interventions/cohorts/create/components/WizardSteps.tsx` (120 lines)
- `frontend/__tests__/admin/interventions/CohortWizard.test.tsx` (40 assertions)

**4 Steps:**
1. **Basic Info** — Name, outcome type, date range (text + date inputs)
2. **Groups** — Size, treatment/control split (number inputs, validation: min 20 total)
3. **Confirmation** — Review all fields, warnings if any
4. **Submit** — Call API, show success/error, redirect to detail page

**Form State Management (useFormState):**
```typescript
const [step, setStep] = useState(0);
const [formData, setFormData] = useState({
  cohortName: '',
  outcomeType: '',
  analysisWindowStart: null,
  analysisWindowEnd: null,
  cohortSize: 0,
  treatmentSize: 0,
  controlSize: 0,
});

const validateStep = (stepNum) => {
  // Step 1: name + outcome_type not empty
  // Step 2: cohortSize >= 20, treatment + control = total
  // Step 3: confirm data
  // Step 4: submit
};
```

**Exit Criteria:**
- [ ] All 4 wizard steps render
- [ ] Form validation works (min 20 cohort size, math checks)
- [ ] Submit calls `useFinalizeCohortMutation()`
- [ ] Success redirects to `/cohorts/[id]`
- [ ] Error shows toast notification
- [ ] 40 unit tests passing
- [ ] Ready for Phase 6 (E2E tests)

---

### Phase 6: End-to-End Test Scenarios (2026-05-03 to 2026-05-04, 2 days)

**Objective:** 25 Playwright E2E scenarios covering happy path + error cases

**Files to Create:**
- `frontend/e2e/interventions-cohorts.spec.ts` (300+ lines, 25 scenarios)

**E2E Test Coverage:**

| Scenario | Category | Test |
|----------|----------|------|
| 1 | Happy path | Create cohort → finalize → view detail |
| 2 | Happy path | Filter cohorts by status → sort by name |
| 3 | Happy path | View outcomes chart on detail page |
| 4 | Validation | Reject cohort < 20 students |
| 5 | Validation | Reject wizard if treatment + control ≠ total |
| 6 | Validation | Reject empty cohort name |
| 7 | Error handling | Server error (500) → show toast |
| 8 | Error handling | Network timeout → retry button works |
| 9 | Error handling | Unauthorized → redirect to login |
| 10 | Loading states | Table loading spinner shows/hides |
| 11 | Loading states | Wizard submit loading state (button disabled) |
| 12 | Loading states | Detail page content loads after cohort loads |
| 13 | Accessibility | Tab navigation works through form |
| 14 | Accessibility | Screen reader can read chart labels |
| 15 | Accessibility | Contrast ratios meet WCAG AA |
| 16 | Mobile | List page responsive on 375px width |
| 17 | Mobile | Detail page chart scales on tablet |
| 18 | Mobile | Create wizard steps readable on mobile |
| 19 | Pagination | List page shows 50+ cohorts (if exists) |
| 20 | Drag & sort | Table column resize (if applicable) |
| 21 | Browser compat | Works on Chrome + Firefox + Safari |
| 22 | Performance | List page loads < 2s (with 100 cohorts) |
| 23 | Performance | LCP < 2.5s, CLS < 0.1 |
| 24 | State mgmt | Browser back/forward navigates without losing form data |
| 25 | Concurrency | Two users create cohorts simultaneously (no conflicts) |

**Example E2E Test (Playwright):**
```typescript
test('Create cohort → finalize → view detail', async ({ page }) => {
  // Navigate to create page
  await page.goto('/console/interventions/cohorts/create');
  
  // Step 1: Fill basic info
  await page.fill('input[name="cohortName"]', 'Spring 2026 Cohort A');
  await page.selectOption('select[name="outcomeType"]', 'completion_rate');
  
  // Step 2: Fill groups
  await page.fill('input[name="cohortSize"]', '100');
  await page.fill('input[name="treatmentSize"]', '50');
  // controlSize auto-calculated to 50
  
  // Step 3: Confirm & submit
  await page.click('button:has-text("Submit")');
  
  // Expect redirect to detail page
  await expect(page).toHaveURL(/\/cohorts\/\d+/);
  
  // Verify detail page shows cohort
  await expect(page.locator('text=Spring 2026 Cohort A')).toBeVisible();
  await expect(page.locator('text=100 students')).toBeVisible();
});
```

**Exit Criteria:**
- [ ] All 25 E2E tests pass (0 failures)
- [ ] Tests run in parallel without race conditions
- [ ] Performance assertions pass (LCP < 2.5s, CLS < 0.1)
- [ ] Ready for Phase 7 (accessibility audit)

---

### Phase 7: Accessibility Audit & Remediation (2026-05-04, 1 day)

**Objective:** WCAG 2.1 Level A compliance + remediate any issues

**Tools:**
- `axe-core` (automated scan)
- Manual keyboard navigation testing
- Screen reader testing (VoiceOver on Mac/macOS)

**Scan Commands:**
```bash
npm run test:a11y  # axe-core scan on all pages

# Manual testing checklist:
# - Tab through list/detail/create pages
# - Read back form labels with screen reader
# - Check color contrast (use eyedropper)
# - Verify all images have alt text
```

**Common Issues Fixed:**
- Missing `aria-label` on charts
- Color-only status indicators (add text labels)
- Form inputs missing associated `<label>`
- Button text too generic ("Click here" → "View Cohort Details")

**Exit Criteria:**
- [ ] Zero automated accessibility violations (axe-core scan)
- [ ] Manual keyboard navigation works across all pages
- [ ] Color contrast ≥ 4.5:1 on all text
- [ ] All form inputs have labels
- [ ] Ready for Phase 8 (performance optimization)

---

### Phase 8: Performance Optimization (2026-05-04 to 2026-05-05, 2 days)

**Objective:** LCP < 2.5s, FID < 100ms, CLS < 0.1 (Web Vitals)

**Optimizations:**
1. **Code Splitting:** Lazy load detail page + wizard
   ```typescript
   const CohortDetail = dynamic(() => import('./CohortDetail'), { loading: () => <Skeleton /> });
   ```

2. **Image Optimization:** Use `next/image` + WebP format
3. **Bundle Analysis:** `npm run analyze:bundle` → identify large chunks
4. **React Query:** Enable `staleTime` caching (10 min for cohort list)
   ```typescript
   useCohortsQuery({ staleTime: 10 * 60 * 1000 })
   ```

5. **Database Query Optimization:** Ensure `/api/admin/interventions/cohorts` returns paginated results (limit 50 per page)

**Exit Criteria:**
- [ ] LCP < 2.5s on list page (measure with Lighthouse)
- [ ] CLS < 0.1 (no layout shifts when content loads)
- [ ] Zero 3p script blocking (CSS/JS inline where possible)
- [ ] Ready for Phase 9 (type safety)

---

### Phase 9: Type Safety & Documentation (2026-05-05, 1 day)

**Objective:** 100% TypeScript coverage, no `any` types

**Tasks:**
1. Run `npm run type-check` across F3 files
2. Document API response types (generated from OpenAPI)
3. Add JSDoc comments to all React components
4. Update README with F3.4 feature overview

**Example JSDoc:**
```typescript
/**
 * Renders a cohort detail page with outcomes visualization.
 * 
 * @param {Object} props
 * @param {number} props.cohortId - ID of cohort to display
 * 
 * @returns {React.ReactElement} Detail page with chart + table
 * 
 * @example
 * <CohortDetail cohortId={123} />
 */
export function CohortDetail({ cohortId }: CohortDetailProps) {
  // ...
}
```

**Exit Criteria:**
- [ ] `npm run type-check` passes (0 errors)
- [ ] No `any` types in F3 files
- [ ] All components have JSDoc
- [ ] All API types documented
- [ ] Ready for Phase 10 (final QA + delivery)

---

### Phase 10: Final QA & Code Review (2026-05-05, 1 day)

**Objective:** Code review + final test pass before 2026-05-05 delivery

**Checklist:**
- [ ] PR created with F3.4 changes, linked to F3 issue
- [ ] All CI checks pass (lint, test, type-check, accessibility)
- [ ] Code review approved by another frontend engineer
- [ ] Test coverage ≥ 80% on F3 files
- [ ] Manual testing on all 3 pages (list, detail, create)
- [ ] Mobile testing on iOS/Android devices (or simulator)
- [ ] Merge to main + deploy to staging

**Exit Criteria:**
- [ ] F3.4 Frontend delivery COMPLETE
- [ ] All 3 pages live on `/console/interventions/cohorts/*`
- [ ] 25 E2E tests passing
- [ ] No console errors in production mode
- [ ] Ready for F3.5 observability + F3.6 security delivery (2026-05-10)

---

## Development Environment Setup (2026-04-21)

```bash
# 1. After F3.3 unfreeze, pull latest backend API specs
cd /home/sbs/AI/frontend
git pull origin main

# 2. Generate TypeScript types from backend OpenAPI schema
npm run generate:openapi-types

# 3. Install any new dependencies
npm install

# 4. Run tests to ensure setup works
npm run test:frontend

# 5. Start development server
npm run dev  # localhost:3000
```

---

## Testing Requirements Summary

| Phase | Unit Tests | Integration | E2E | Total |
|-------|-----------|-------------|-----|-------|
| 1 | 63 | 0 | 0 | 63 |
| 2 | 0 | 0 | 0 | 0 |
| 3 | 30 | 0 | 0 | 30 |
| 4 | 63 | 0 | 0 | 63 |
| 5 | 40 | 0 | 0 | 40 |
| 6 | 0 | 0 | 25 | 25 |
| 7 | 0 | 0 | 0 | 0 (a11y scan) |
| 8 | 0 | 0 | 0 | 0 (Lighthouse) |
| 9 | 0 | 0 | 0 | 0 (type-check) |
| 10 | 0 | 0 | 0 | 0 (manual QA) |
| **Total** | **196** | **0** | **25** | **221 tests** |

---

## Dependency Versions (as of 2026-04-14)

```json
{
  "react": "18.x",
  "next": "14.2",
  "@tanstack/react-query": "^5.x",
  "recharts": "^2.x",
  "@testing-library/react": "^14.x",
  "playwright": "^1.x",
  "typescript": "^5.x"
}
```

---

## Deployment & Rollout (After 2026-05-05 Delivery)

F3.4 frontend goes live as **Stage 1** of F3.8 release (internal canary, 2026-05-15 start):
- Feature flag: `F3_COHORT_DASHBOARD_ENABLED`
- Canary rollout: Internal staff first (24h)
- Then partner institutions (72h)
- Then graduated rollout to all tenants

See `docs/F3_RELEASE_ADOPTION.md` for 4-stage rollout plan.

---

## Contacts & Escalation

- **Frontend Lead:** [TBD]
- **Backend API Contact:** [TBD]
- **Accessibility Reviewer:** [TBD]
- **Performance Reviewer:** [TBD]

Questions? Raise issue with label `F3.4-frontend` in project board.

---

## Post-Implementation Checklist (2026-05-05)

- [ ] All 221 tests passing
- [ ] Zero console errors
- [ ] Mobile responsive (375px–1920px)
- [ ] Accessibility audit passes (WCAG 2.1 A)
- [ ] Performance: LCP < 2.5s, CLS < 0.1
- [ ] Code review approved
- [ ] Deployed to staging
- [ ] Product team validates UX
- [ ] Ready for F3.8 rollout (2026-05-15)
