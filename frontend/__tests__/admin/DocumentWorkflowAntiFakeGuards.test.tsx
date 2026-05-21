import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { assertTrustedDocumentDashboard } from '@/modules/document-workflow/guards';
import { DocumentWorkflowDashboardCards } from '@/modules/document-workflow/components/pages';
import type { DashboardSummary } from '@/modules/document-workflow/types';

const DASHBOARD: DashboardSummary = {
  tenant_id: 1,
  total_documents: 10,
  registered_documents: 4,
  under_review_count: 2,
  returned_for_revision_count: 1,
  approved_count: 3,
  signed_count: 2,
  archived_count: 1,
  incoming_correspondence_count: 5,
  outgoing_correspondence_count: 7,
  overdue_document_reviews: 1,
  documents_linked_to_assignments: 4,
  decrees_pending_signature: 2,
  average_review_cycle_days: undefined,
  data_source: 'computed_from_documents',
  fake_metrics: false,
  generated_at: '2026-05-21T00:00:00Z',
  incomplete_data: false,
};

describe('document workflow anti-fake guards', () => {
  it('throws when fake_metrics is true', () => {
    expect(() => assertTrustedDocumentDashboard({ ...DASHBOARD, fake_metrics: true })).toThrow(/fake_metrics=true/i);
  });

  it('throws when data_source is not computed_from_documents', () => {
    expect(() => assertTrustedDocumentDashboard({ ...DASHBOARD, data_source: 'hardcoded' })).toThrow(/data source mismatch/i);
  });

  it('renders computed-from-documents label and unavailable optional metrics', () => {
    render(<DocumentWorkflowDashboardCards dashboard={DASHBOARD} />);
    expect(screen.getByTestId('computed-from-documents-label').textContent).toMatch(/computed from documents/i);
    expect(screen.getByTestId('kpi-average-review-cycle').textContent).toMatch(/unavailable/i);
    expect(screen.getByTestId('kpi-total-documents').textContent).toMatch(/10/);
  });

  it('renders incomplete-data notice only when backend reports it', () => {
    const { rerender } = render(<DocumentWorkflowDashboardCards dashboard={DASHBOARD} />);
    expect(screen.queryByTestId('incomplete-dashboard-notice')).toBeNull();

    rerender(<DocumentWorkflowDashboardCards dashboard={{ ...DASHBOARD, incomplete_data: true }} />);
    expect(screen.getByTestId('incomplete-dashboard-notice').textContent).toMatch(/incomplete dashboard data/i);
  });
});