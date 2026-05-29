import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import {
  DOCUMENT_DECREE_CORRESPONDENCE_DASHBOARD_WIDGETS,
  DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES,
} from '@/modules/document-decree-correspondence/constants';
import {
  DocumentDecreeCorrespondencePage,
  DdcDashboardGrid,
  DdcMetricCard,
  DdcSafetyChecklist,
} from '@/modules/document-decree-correspondence/pages';

describe('Document Decree Correspondence dashboard runtime', () => {
  it('renders dashboard page title', () => {
    render(<DocumentDecreeCorrespondencePage routeKey="dashboard" userPermissions={[DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.dashboardRead]} />);
    expect(screen.getByRole('heading', { level: 1, name: 'Document Dashboard' })).toBeInTheDocument();
  });

  it('renders dashboard grid with known widgets', () => {
    render(<DdcDashboardGrid widgets={DOCUMENT_DECREE_CORRESPONDENCE_DASHBOARD_WIDGETS.slice(0, 2)} />);
    expect(screen.getByTestId('ddc-dashboard-grid')).toBeInTheDocument();
    expect(screen.getByTestId('ddc-widget-document-intake')).toBeInTheDocument();
    expect(screen.getByTestId('ddc-widget-document-routing')).toBeInTheDocument();
  });

  it('renders metric cards with deterministic test ids', () => {
    render(<DdcMetricCard label="fakeDocuments" value="false" helperText="No fake docs" />);
    expect(screen.getByTestId('ddc-metric-fakedocuments')).toBeInTheDocument();
  });

  it('renders safety checklist entries', () => {
    render(<DdcSafetyChecklist />);
    expect(screen.getByText('fakeDocuments=false')).toBeInTheDocument();
    expect(screen.getByText('officialLegalEffect=false')).toBeInTheDocument();
    expect(screen.getByText('humanReviewRequired=true')).toBeInTheDocument();
  });

  it('includes boundary banner and no-overclaim footer on overview page', () => {
    render(<DocumentDecreeCorrespondencePage routeKey="overview" userPermissions={[DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.overviewRead]} />);
    expect(screen.getByTestId('ddc-boundary-banner')).toBeInTheDocument();
    expect(screen.getByTestId('ddc-registry-table')).toBeInTheDocument();
    expect(screen.getByTestId('ui-framework-audit-trail-panel')).toBeInTheDocument();
    expect(screen.getByTestId('ddc-no-overclaim-footer')).toBeInTheDocument();
  });

  it('shows permission panel for missing permission', () => {
    render(<DocumentDecreeCorrespondencePage routeKey="dashboard" userPermissions={[DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.overviewRead]} />);
    expect(screen.getByTestId('ddc-permission-denied-panel')).toBeInTheDocument();
  });
});
