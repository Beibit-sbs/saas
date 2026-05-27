import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { SECURITY_ACCESS_COMPLIANCE_ROUTE_DEFINITIONS } from '@/modules/security-access-compliance/constants';
import { buildSacPageModel, SecurityAccessCompliancePage } from '@/modules/security-access-compliance/pages';

describe('Security / Access / Compliance dashboard', () => {
  it('renders the dashboard shell and route contract panel', () => {
    render(<SecurityAccessCompliancePage routeKey="dashboard" userPermissions={['security_access_compliance.dashboard.read']} />);

    expect(screen.getByTestId('sac-page-dashboard')).toBeInTheDocument();
    expect(screen.getByTestId('sac-route-contract-panel')).toBeInTheDocument();
    expect(screen.getByText('Backend API base: /api/admin/security-access-compliance')).toBeInTheDocument();
  });

  it('renders dashboard metrics', () => {
    render(<SecurityAccessCompliancePage routeKey="dashboard" userPermissions={['security_access_compliance.dashboard.read']} />);

    expect(screen.getByTestId('sac-metric-backend-route-count')).toBeInTheDocument();
    expect(screen.getByText('47')).toBeInTheDocument();
    expect(screen.getByText('24')).toBeInTheDocument();
    expect(screen.getByText('23')).toBeInTheDocument();
  });

  it('renders dashboard widgets', () => {
    render(<SecurityAccessCompliancePage routeKey="dashboard" userPermissions={['security_access_compliance.dashboard.read']} />);

    expect(screen.getByTestId('sac-dashboard-grid')).toBeInTheDocument();
    expect(screen.getByTestId('sac-widget-dashboard-0')).toBeInTheDocument();
  });

  it('includes the safety checklist', () => {
    render(<SecurityAccessCompliancePage routeKey="dashboard" userPermissions={['security_access_compliance.dashboard.read']} />);

    expect(screen.getByTestId('sac-safety-checklist')).toBeInTheDocument();
    expect(screen.getByText('fakeSecurityCertification=false')).toBeInTheDocument();
    expect(screen.getByText('humanReviewRequired=true')).toBeInTheDocument();
  });

  it('keeps the no-overclaim footer visible', () => {
    render(<SecurityAccessCompliancePage routeKey="dashboard" userPermissions={['security_access_compliance.dashboard.read']} />);

    expect(screen.getByText('No sales-ready claim')).toBeInTheDocument();
    expect(screen.getByText('No GCC-ready claim')).toBeInTheDocument();
  });

  it('mirrors the route model for the dashboard entry', () => {
    const model = buildSacPageModel('dashboard');
    expect(model.route).toBe('/console/security-access-compliance/dashboard');
    expect(model.backendEndpoints).toContain('GET /api/admin/security-access-compliance/dashboard');
  });

  it('keeps the route inventory at 23', () => {
    expect(SECURITY_ACCESS_COMPLIANCE_ROUTE_DEFINITIONS).toHaveLength(23);
  });

  it('renders the human review and compliance badges', () => {
    render(<SecurityAccessCompliancePage routeKey="dashboard" userPermissions={['security_access_compliance.dashboard.read']} />);

    expect(screen.getByTestId('sac-human-review-badge')).toBeInTheDocument();
    expect(screen.getByTestId('sac-compliance-readiness-badge')).toBeInTheDocument();
  });
});
