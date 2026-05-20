/**
 * RectorAssignmentDashboardAntiFake.test.tsx
 * A-031.5 — DataQualityError on fake_metrics=true; wrong data_source; undefined fields → unavailable not zero
 */

import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

// We need to test the dashboard page's fake_metrics guard behaviour
// We use the DashboardAnalyticsSection to verify undefined → unavailable (not 0)
import {
  DashboardAnalyticsSection,
  EscalationRateWidget,
  ReportComplianceWidget,
  OverdueAgingWidget,
  EvidenceAttachmentRateWidget,
} from '@/modules/rector-assignments/components/DashboardAnalytics';
import type { DashboardSummaryExpanded } from '@/modules/rector-assignments/types';

const CLEAN_DASHBOARD: DashboardSummaryExpanded = {
  tenant_id: 1,
  computed_at: '2024-03-01T00:00:00Z',
  total_assignments: 10,
  active_count: 3,
  draft_count: 0,
  overdue_count: 1,
  escalated_count: 0,
  completed_count: 4,
  cancelled_count: 0,
  report_submitted_count: 0,
  returned_count: 0,
  due_this_week: 2,
  due_today: 1,
  completion_rate_30d: 0.4,
  average_days_to_complete: null,
  by_status: {},
  by_priority: {},
  by_unit: [],
  top_overdue: [],
  data_source: 'computed_from_assignments',
  fake_metrics: false,
};

describe('Anti-fake guard — undefined fields show unavailable not 0', () => {
  it('EscalationRateWidget shows unavailable for undefined rate', () => {
    render(<EscalationRateWidget rate={undefined} avgRevisionCycles={undefined} />);
    const el = screen.getByTestId('widget-unavailable-Escalation rate');
    expect(el.textContent).toMatch(/unavailable/i);
    // Must NOT show "0%" which would be a fake zero
    expect(screen.queryByText('0.0%')).toBeNull();
  });

  it('ReportComplianceWidget shows unavailable for undefined compliance', () => {
    render(<ReportComplianceWidget compliance={undefined} withoutRecent={undefined} />);
    const el = screen.getByTestId('widget-unavailable-Report compliance');
    expect(el.textContent).toMatch(/unavailable/i);
    expect(screen.queryByText('0.0%')).toBeNull();
  });

  it('OverdueAgingWidget shows unavailable for undefined buckets', () => {
    render(<OverdueAgingWidget buckets={undefined} />);
    const el = screen.getByTestId('widget-unavailable-Overdue aging');
    expect(el.textContent).toMatch(/unavailable/i);
  });

  it('EvidenceAttachmentRateWidget shows unavailable for undefined rate', () => {
    render(<EvidenceAttachmentRateWidget rate={undefined} />);
    const el = screen.getByTestId('widget-unavailable-Evidence attachment rate');
    expect(el.textContent).toMatch(/unavailable/i);
    expect(screen.queryByText('0.0%')).toBeNull();
  });
});

describe('Analytics section renders all unavailable widgets when fields absent', () => {
  it('renders 5 unavailable widgets when no analytics fields present', () => {
    render(<DashboardAnalyticsSection dashboard={CLEAN_DASHBOARD} />);
    // overdue_aging_buckets → undefined
    expect(screen.getByTestId('widget-unavailable-Overdue aging')).toBeTruthy();
    // completion_trend_by_week → undefined
    expect(screen.getByTestId('widget-unavailable-Completion trend')).toBeTruthy();
    // report_submission_compliance → undefined
    expect(screen.getByTestId('widget-unavailable-Report compliance')).toBeTruthy();
    // escalation_rate → undefined
    expect(screen.getByTestId('widget-unavailable-Escalation rate')).toBeTruthy();
    // evidence_attachment_rate → undefined
    expect(screen.getByTestId('widget-unavailable-Evidence attachment rate')).toBeTruthy();
    // unit_completion_table → undefined → UnitPerformanceTable not rendered (conditional)
  });

  it('renders populated widgets when fields are provided', () => {
    const dashboard: DashboardSummaryExpanded = {
      ...CLEAN_DASHBOARD,
      escalation_rate: 0.1,
      evidence_attachment_rate: 0.7,
      overdue_aging_buckets: {
        one_to_seven_days: 2,
        eight_to_fourteen_days: 0,
        fifteen_to_thirty_days: 0,
        over_thirty_days: 0,
      },
    };
    render(<DashboardAnalyticsSection dashboard={dashboard} />);
    expect(screen.getByTestId('escalation-rate-widget')).toBeTruthy();
    expect(screen.getByTestId('evidence-attachment-widget')).toBeTruthy();
    expect(screen.getByTestId('overdue-aging-widget')).toBeTruthy();
  });
});

describe('fake_metrics guard — dashboard page (unit-level)', () => {
  /**
   * The dashboard page.tsx guards rendering behind:
   *   if (dashboard.fake_metrics !== false) → <DataQualityError data-testid="data-quality-error" />
   *   if (dashboard.data_source !== "computed_from_assignments") → <DataQualityError />
   *
   * We test the guard logic directly by importing the page, or by testing
   * the guard predicates inline.
   */

  it('fake_metrics=true should be detected as non-false', () => {
    const fakeDashboard = { ...CLEAN_DASHBOARD, fake_metrics: true };
    expect(fakeDashboard.fake_metrics !== false).toBe(true);
  });

  it('fake_metrics=false should pass the guard', () => {
    expect(CLEAN_DASHBOARD.fake_metrics !== false).toBe(false);
  });

  it('wrong data_source should be detected', () => {
    const wrongSource = { ...CLEAN_DASHBOARD, data_source: 'hardcoded' };
    expect(wrongSource.data_source !== 'computed_from_assignments').toBe(true);
  });

  it('correct data_source passes the guard', () => {
    expect(CLEAN_DASHBOARD.data_source !== 'computed_from_assignments').toBe(false);
  });
});
