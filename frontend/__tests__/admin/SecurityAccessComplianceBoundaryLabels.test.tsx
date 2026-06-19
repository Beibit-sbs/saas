import React from 'react';
import { render, screen } from '@testing-library/react';
import { within } from '@testing-library/dom';
import { describe, expect, it } from 'vitest';
import {
  SECURITY_ACCESS_COMPLIANCE_BOUNDARY_LABELS,
  SECURITY_ACCESS_COMPLIANCE_ROUTE_BOUNDARY_LABELS,
} from '@/modules/security-access-compliance/boundaryLabels';
import { SecurityAccessCompliancePage } from '@/modules/security-access-compliance/pages';

describe('Security / Access / Compliance boundary labels', () => {
  it('renders overview boundary labels', () => {
    render(<SecurityAccessCompliancePage routeKey="overview" userPermissions={['security_access_compliance.overview.read']} />);

    const banner = screen.getByTestId('sac-boundary-banner');
    for (const label of SECURITY_ACCESS_COMPLIANCE_ROUTE_BOUNDARY_LABELS.overview) {
      expect(within(banner).getByText(label)).toBeInTheDocument();
    }
    expect(banner).toBeInTheDocument();
  });

  it('renders dashboard boundary labels', () => {
    render(<SecurityAccessCompliancePage routeKey="dashboard" userPermissions={['security_access_compliance.dashboard.read']} />);

    const banner = screen.getByTestId('sac-boundary-banner');
    expect(within(banner).getByText(SECURITY_ACCESS_COMPLIANCE_BOUNDARY_LABELS.incompleteDataSupported)).toBeInTheDocument();
    expect(within(banner).getByText(SECURITY_ACCESS_COMPLIANCE_BOUNDARY_LABELS.noHiddenUserRiskScore)).toBeInTheDocument();
  });

  it('renders permission denied panel when permission is missing', () => {
    render(<SecurityAccessCompliancePage routeKey="incidents" userPermissions={[]} />);

    expect(screen.getByTestId('sac-permission-denied-panel-wrap')).toBeInTheDocument();
  });

  it('renders no-overclaim footer text', () => {
    render(<SecurityAccessCompliancePage routeKey="overview" userPermissions={['security_access_compliance.overview.read']} />);

    const footer = screen.getByTestId('sac-no-overclaim-footer');
    expect(footer).toBeInTheDocument();
    expect(within(footer).getByText('No fake security certification')).toBeInTheDocument();
    expect(within(footer).getByText('No production-ready security claim')).toBeInTheDocument();
  });

  it('renders the human review badge', () => {
    render(<SecurityAccessCompliancePage routeKey="overview" userPermissions={['security_access_compliance.overview.read']} />);

    expect(screen.getByTestId('sac-human-review-badge')).toBeInTheDocument();
  });

  it('renders the compliance readiness badge', () => {
    render(<SecurityAccessCompliancePage routeKey="dashboard" userPermissions={['security_access_compliance.dashboard.read']} />);

    expect(screen.getByTestId('sac-compliance-readiness-badge')).toBeInTheDocument();
  });

  it('renders the incident metadata badge', () => {
    render(<SecurityAccessCompliancePage routeKey="incidents" userPermissions={['security_access_compliance.incidents.read']} />);

    expect(screen.getByTestId('sac-incident-metadata-badge')).toBeInTheDocument();
  });

  it('renders the incomplete data notice', () => {
    render(<SecurityAccessCompliancePage routeKey="overview" userPermissions={['security_access_compliance.overview.read']} />);

    expect(screen.getByTestId('sac-incomplete-data-notice')).toBeInTheDocument();
  });
});
