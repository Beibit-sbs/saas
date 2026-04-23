import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';

import { CohortDetailsCard } from '@/app/(admin)/console/interventions/cohorts/components/CohortDetailsCard';
import { CohortOutcomesPanel } from '@/app/(admin)/console/interventions/cohorts/components/CohortOutcomesPanel';
import type { CohortReadSchema } from '@/shared/hooks/useInterventionCohorts';
import type { CohortOutcomeReadSchema } from '@/shared/hooks/useCohortOutcomes';

const cohort: CohortReadSchema = {
  id: 42,
  tenant_id: 100,
  playbook_id: 5,
  cohort_name: 'Spring 2026 Cohort A',
  analysis_window_start: '2026-01-15',
  analysis_window_end: '2026-05-15',
  student_count: 100,
  data_completeness_pct: 95.5,
  status: 'analyzed',
  created_by: 'system@example.com',
  created_at: '2026-04-01T10:00:00Z',
};

const outcome: CohortOutcomeReadSchema = {
  id: 1,
  tenant_id: 100,
  cohort_id: 42,
  outcome_type: 'dropout_rate' as CohortOutcomeReadSchema['outcome_type'],
  segment_name: null,
  outcome_value_treated: 0.14,
  outcome_value_control: 0.18,
  uplift_pp: -0.04,
  uplift_confidence_p5: null,
  uplift_confidence_p95: null,
  measurement_completeness_pct: 0.95,
  measured_at: '2026-04-15T10:00:00Z',
  notes: null,
};

describe('Intervention Cohorts Phase 4 Components', () => {
  it('renders cohort details metadata', () => {
    render(<CohortDetailsCard cohort={cohort} />);

    expect(screen.getByText('Student Count')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
    expect(screen.getByText('Data Completeness')).toBeInTheDocument();
    expect(screen.getByText('95.5%')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Analyzed')).toBeInTheDocument();
    expect(screen.getByText('Created By')).toBeInTheDocument();
    expect(screen.getByText('system@example.com')).toBeInTheDocument();
  });

  it('renders fallback completeness when value is null', () => {
    render(<CohortDetailsCard cohort={{ ...cohort, data_completeness_pct: null }} />);
    expect(screen.getByText('N/A')).toBeInTheDocument();
  });

  it('renders outcomes loading state', () => {
    render(
      <CohortOutcomesPanel
        isLoading={true}
        status="analyzing"
        outcomes={[]}
        onRefresh={() => {}}
        onRerun={() => {}}
        onRetry={() => {}}
      />,
    );

    expect(screen.getByTestId('outcomes-loading')).toBeInTheDocument();
  });

  it('renders outcomes empty state', () => {
    render(
      <CohortOutcomesPanel
        isLoading={false}
        status="no_analysis_yet"
        outcomes={[]}
        onRefresh={() => {}}
        onRerun={() => {}}
        onRetry={() => {}}
      />,
    );

    expect(screen.getByText('No outcomes available yet.')).toBeInTheDocument();
  });

  it('locks outcomes analysis action for draft cohorts', () => {
    render(
      <CohortOutcomesPanel
        isLoading={false}
        status="no_analysis_yet"
        outcomes={[]}
        onRefresh={() => {}}
        onRerun={() => {}}
        onRetry={() => {}}
        analysisLocked={true}
      />,
    );

    expect(screen.getByText('Finalize cohort before analysis becomes available.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Run outcomes analysis for this cohort' })).toBeDisabled();
  });

  it('renders outcomes error state', () => {
    render(
      <CohortOutcomesPanel
        isLoading={false}
        status="analysis_failed"
        error={new Error('failed')}
        outcomes={[]}
        onRefresh={() => {}}
        onRerun={() => {}}
        onRetry={() => {}}
      />,
    );

    expect(screen.getByText('Failed to load analysis results')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('renders outcomes list and values', () => {
    render(
      <CohortOutcomesPanel
        isLoading={false}
        status="analyzed"
        outcomes={[outcome]}
        onRefresh={() => {}}
        onRerun={() => {}}
        onRetry={() => {}}
      />,
    );

    expect(screen.getAllByText('Improved').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Unchanged').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Worse').length).toBeGreaterThan(0);
    expect(screen.getByText('Confidence')).toBeInTheDocument();
    expect(screen.getByText('No meaningful improvement detected')).toBeInTheDocument();
    expect(screen.getByTestId('outcome-distribution-chart')).toBeInTheDocument();
    expect(screen.getByText('Refresh results')).toBeInTheDocument();
    expect(screen.getByText('Re-run analysis')).toBeInTheDocument();
  });

  it('renders analysis_queued status in panel', () => {
    render(
      <CohortOutcomesPanel
        isLoading={false}
        status="analysis_queued"
        outcomes={[]}
        onRefresh={() => {}}
        onRerun={() => {}}
        onRetry={() => {}}
      />,
    );

    expect(screen.getByText('Analysis started')).toBeInTheDocument();
  });

  it('renders draft cohort details with correct status badge', () => {
    render(<CohortDetailsCard cohort={{ ...cohort, status: 'draft', student_count: 0, data_completeness_pct: null }} />);
    expect(screen.getByText('Draft')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('renders finalized cohort details with correct status badge', () => {
    render(<CohortDetailsCard cohort={{ ...cohort, status: 'finalized', data_completeness_pct: null }} />);
    expect(screen.getByText('Finalized')).toBeInTheDocument();
  });
});
