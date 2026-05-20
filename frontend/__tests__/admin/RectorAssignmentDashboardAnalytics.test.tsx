/**
 * RectorAssignmentDashboardAnalytics.test.tsx
 * A-031.5 — Dashboard analytics widgets render from backend data
 */

import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  OverdueAgingWidget,
  CompletionTrendWidget,
  ReportComplianceWidget,
  UnitPerformanceTable,
  EscalationRateWidget,
  EvidenceAttachmentRateWidget,
  DashboardAnalyticsSection,
} from '@/modules/rector-assignments/components/DashboardAnalytics';
import type { DashboardSummaryExpanded } from '@/modules/rector-assignments/types';

// ── helpers ────────────────────────────────────────────────────────────────

const BASE_DASHBOARD: DashboardSummaryExpanded = {
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

// ── OverdueAgingWidget ─────────────────────────────────────────────────────

describe('OverdueAgingWidget', () => {
  it('shows unavailable when buckets is undefined', () => {
    render(<OverdueAgingWidget buckets={undefined} />);
    expect(screen.getByTestId('widget-unavailable-Overdue aging')).toBeTruthy();
    expect(screen.queryByTestId('overdue-aging-widget')).toBeNull();
  });

  it('renders 4 buckets from backend data', () => {
    render(
      <OverdueAgingWidget
        buckets={{
          one_to_seven_days: 3,
          eight_to_fourteen_days: 2,
          fifteen_to_thirty_days: 1,
          over_thirty_days: 5,
        }}
      />,
    );
    expect(screen.getByTestId('overdue-aging-widget')).toBeTruthy();
    expect(screen.getByTestId('aging-bucket-1–7-days').textContent).toBe('3');
    expect(screen.getByTestId('aging-bucket-30+-days').textContent).toBe('5');
  });

  it('shows no overdue message when all buckets are 0', () => {
    render(
      <OverdueAgingWidget
        buckets={{
          one_to_seven_days: 0,
          eight_to_fourteen_days: 0,
          fifteen_to_thirty_days: 0,
          over_thirty_days: 0,
        }}
      />,
    );
    expect(screen.getByText('No overdue assignments.')).toBeTruthy();
  });
});

// ── CompletionTrendWidget ──────────────────────────────────────────────────

describe('CompletionTrendWidget', () => {
  it('shows unavailable when trend is undefined', () => {
    render(<CompletionTrendWidget trend={undefined} />);
    expect(screen.getByTestId('widget-unavailable-Completion trend')).toBeTruthy();
  });

  it('shows insufficient notice with < 2 points', () => {
    render(<CompletionTrendWidget trend={[{ week_start: '2024-01-01', completed_count: 5 }]} />);
    expect(screen.getByTestId('completion-trend-insufficient')).toBeTruthy();
  });

  it('renders bars when trend has ≥ 2 points', () => {
    const trend = [
      { week_start: '2024-01-01', completed_count: 3 },
      { week_start: '2024-01-08', completed_count: 7 },
    ];
    render(<CompletionTrendWidget trend={trend} />);
    expect(screen.getByTestId('completion-trend-widget')).toBeTruthy();
    expect(screen.getByTestId('trend-bar-2024-01-01')).toBeTruthy();
    expect(screen.getByTestId('trend-bar-2024-01-08')).toBeTruthy();
  });
});

// ── ReportComplianceWidget ─────────────────────────────────────────────────

describe('ReportComplianceWidget', () => {
  it('shows unavailable when compliance is undefined', () => {
    render(<ReportComplianceWidget compliance={undefined} withoutRecent={undefined} />);
    expect(screen.getByTestId('widget-unavailable-Report compliance')).toBeTruthy();
  });

  it('renders compliance rate as percentage', () => {
    render(<ReportComplianceWidget compliance={0.75} withoutRecent={4} />);
    expect(screen.getByTestId('compliance-rate').textContent).toBe('75.0%');
    expect(screen.getByText(/4 assignments without a recent report/i)).toBeTruthy();
  });
});

// ── UnitPerformanceTable ───────────────────────────────────────────────────

describe('UnitPerformanceTable', () => {
  it('shows unavailable when units is undefined', () => {
    render(<UnitPerformanceTable units={undefined} />);
    expect(screen.getByTestId('widget-unavailable-Unit performance')).toBeTruthy();
  });

  it('renders unit rows', () => {
    render(
      <UnitPerformanceTable
        units={[
          { unit_id: 1, unit_name: 'Finance', total: 10, completed: 8, overdue: 1, completion_rate: 0.8 },
        ]}
      />,
    );
    expect(screen.getByTestId('unit-performance-table')).toBeTruthy();
    expect(screen.getByTestId('unit-row-1')).toBeTruthy();
    expect(screen.getByText('Finance')).toBeTruthy();
  });
});

// ── EscalationRateWidget ───────────────────────────────────────────────────

describe('EscalationRateWidget', () => {
  it('shows unavailable when rate is undefined', () => {
    render(<EscalationRateWidget rate={undefined} avgRevisionCycles={undefined} />);
    expect(screen.getByTestId('widget-unavailable-Escalation rate')).toBeTruthy();
  });

  it('renders rate and manual confirmation label', () => {
    render(<EscalationRateWidget rate={0.12} avgRevisionCycles={1.3} />);
    expect(screen.getByTestId('escalation-rate-value').textContent).toBe('12.0%');
    expect(screen.getByTestId('escalation-manual-label').textContent).toMatch(
      /Manual confirmation required/i,
    );
  });
});

// ── EvidenceAttachmentRateWidget ───────────────────────────────────────────

describe('EvidenceAttachmentRateWidget', () => {
  it('shows unavailable when rate is undefined', () => {
    render(<EvidenceAttachmentRateWidget rate={undefined} />);
    expect(screen.getByTestId('widget-unavailable-Evidence attachment rate')).toBeTruthy();
  });

  it('renders evidence rate as percentage', () => {
    render(<EvidenceAttachmentRateWidget rate={0.9} />);
    expect(screen.getByTestId('evidence-attachment-rate').textContent).toBe('90.0%');
  });
});

// ── DashboardAnalyticsSection — missing fields → unavailable not zero ──────

describe('DashboardAnalyticsSection — missing fields', () => {
  it('shows all widgets in unavailable state when no analytics fields present', () => {
    render(<DashboardAnalyticsSection dashboard={BASE_DASHBOARD} />);
    expect(screen.getByTestId('widget-unavailable-Overdue aging')).toBeTruthy();
    expect(screen.getByTestId('widget-unavailable-Completion trend')).toBeTruthy();
    expect(screen.getByTestId('widget-unavailable-Report compliance')).toBeTruthy();
    expect(screen.getByTestId('widget-unavailable-Escalation rate')).toBeTruthy();
    expect(screen.getByTestId('widget-unavailable-Evidence attachment rate')).toBeTruthy();
  });

  it('renders populated widgets when analytics fields present', () => {
    const dashboard: DashboardSummaryExpanded = {
      ...BASE_DASHBOARD,
      escalation_rate: 0.05,
      evidence_attachment_rate: 0.8,
      report_submission_compliance: 0.9,
      overdue_aging_buckets: {
        one_to_seven_days: 1,
        eight_to_fourteen_days: 0,
        fifteen_to_thirty_days: 0,
        over_thirty_days: 0,
      },
    };
    render(<DashboardAnalyticsSection dashboard={dashboard} />);
    expect(screen.getByTestId('overdue-aging-widget')).toBeTruthy();
    expect(screen.getByTestId('escalation-rate-widget')).toBeTruthy();
    expect(screen.getByTestId('evidence-attachment-widget')).toBeTruthy();
  });
});
