import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StudentLifecycleOverviewDashboard } from '@/modules/student-lifecycle/components';
import { EXPECTED_DATA_SOURCE } from '@/modules/student-lifecycle/constants';
import type { StudentLifecycleDashboardResponse, StudentLifecycleHealthResponse } from '@/modules/student-lifecycle/types';

const dashboard: StudentLifecycleDashboardResponse = {
  tenant_id: 1,
  generated_at: '2026-05-22T00:00:00Z',
  fake_metrics: false,
  data_source: EXPECTED_DATA_SOURCE,
  incomplete_data: true,
  limitations: ['Human review required', 'Metadata only'],
  applicant_counts_by_status: { DRAFT: 3, UNDER_REVIEW: 2 },
  student_counts_by_status: { ACTIVE: 6 },
  enrollment_counts_by_status: { ENROLLED: 4 },
  transcript_preview_counts: { GENERATED_UNOFFICIAL_PREVIEW: 2 },
  degree_progress_counts: { HUMAN_REVIEW_REQUIRED: 2 },
  request_counts_by_status: { SUBMITTED: 1 },
  appeal_counts_by_status: { REVIEWER_REVIEW: 1 },
  intervention_counts_by_status: { SIGNAL_REGISTERED: 2 },
  human_review_required_count: 5,
  provider_integration_enabled: false,
  automated_decision_count: 0,
  hidden_score_present: false,
};

const health: StudentLifecycleHealthResponse = {
  tenant_id: 1,
  generated_at: '2026-05-22T00:00:00Z',
  module_name: 'student_lifecycle',
  route_count: 44,
  table_count: 14,
  fake_metrics: false,
  data_source: EXPECTED_DATA_SOURCE,
  incomplete_data: true,
  limitations: ['Metadata only'],
  provider_integration_enabled: false,
  automated_decision_count: 0,
  hidden_score_present: false,
};

describe('Student Lifecycle overview dashboard', () => {
  it('renders dashboard widgets and trust labels', () => {
    render(<StudentLifecycleOverviewDashboard dashboard={dashboard} health={health} />);

    expect(screen.getByTestId('student-lifecycle-overview-dashboard')).toBeInTheDocument();
    expect(screen.getByTestId('fake-metrics-label').textContent).toContain('fake_metrics=false');
    expect(screen.getByTestId('data-source-label').textContent).toContain(EXPECTED_DATA_SOURCE);
    expect(screen.getByText(/human review queue/i)).toBeInTheDocument();
    expect(screen.getByText(/applicants tracked/i)).toBeInTheDocument();
  });

  it('renders incomplete data and limitations explicitly', () => {
    render(<StudentLifecycleOverviewDashboard dashboard={dashboard} health={health} />);

    expect(screen.getByText(/incomplete data/i)).toBeInTheDocument();
    expect(screen.getByTestId('metadata-only-label')).toBeInTheDocument();
    expect(screen.getByText(/route count 44/i)).toBeInTheDocument();
  });
});