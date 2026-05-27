import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { buildSacPageModel, SecurityAccessCompliancePage } from '@/modules/security-access-compliance/pages';

const routes = [
  ['sessions', 'security_access_compliance.sessions.read', 'sac-page-sessions'],
  ['login-events', 'security_access_compliance.login_events.read', 'sac-page-login-events'],
  ['mfa-readiness', 'security_access_compliance.mfa_readiness.read', 'sac-page-mfa-readiness'],
  ['tenant-isolation', 'security_access_compliance.tenant_isolation.read', 'sac-page-tenant-isolation'],
  ['data-protection', 'security_access_compliance.data_protection.read', 'sac-page-data-protection'],
  ['privacy-readiness', 'security_access_compliance.privacy_readiness.read', 'sac-page-privacy-readiness'],
  ['visitor-access', 'security_access_compliance.visitor_access.read', 'sac-page-visitor-access'],
  ['bridges', 'security_access_compliance.bridges.hr', 'sac-page-bridges'],
] as const;

describe('Security / Access / Compliance readiness and bridges', () => {
  it.each(routes)('renders %s readiness surface', (routeKey, permission, testId) => {
    render(<SecurityAccessCompliancePage routeKey={routeKey} userPermissions={[permission]} />);
    expect(screen.getByTestId(testId)).toBeInTheDocument();
  });

  it('renders the session visibility evidence table', () => {
    render(<SecurityAccessCompliancePage routeKey="sessions" userPermissions={['security_access_compliance.sessions.read']} />);

    expect(screen.getByTestId('sac-evidence-table')).toBeInTheDocument();
  });

  it('renders the MFA readiness evidence table', () => {
    render(<SecurityAccessCompliancePage routeKey="mfa-readiness" userPermissions={['security_access_compliance.mfa_readiness.read']} />);

    expect(screen.getByTestId('sac-evidence-table')).toBeInTheDocument();
  });

  it('renders the tenant isolation evidence table', () => {
    render(<SecurityAccessCompliancePage routeKey="tenant-isolation" userPermissions={['security_access_compliance.tenant_isolation.read']} />);

    expect(screen.getByTestId('sac-evidence-table')).toBeInTheDocument();
  });

  it('renders the bridge cards for all bridge families', () => {
    render(<SecurityAccessCompliancePage routeKey="bridges" userPermissions={['security_access_compliance.bridges.hr']} />);

    expect(screen.getByTestId('sac-bridge-hr')).toBeInTheDocument();
    expect(screen.getByTestId('sac-bridge-finance')).toBeInTheDocument();
    expect(screen.getByTestId('sac-bridge-documents')).toBeInTheDocument();
    expect(screen.getByTestId('sac-bridge-student-services')).toBeInTheDocument();
  });

  it('renders the visitor access form shell', () => {
    render(<SecurityAccessCompliancePage routeKey="visitor-access" userPermissions={['security_access_compliance.visitor_access.read']} />);

    expect(screen.getByTestId('sac-form-shell-visitor-access')).toBeInTheDocument();
  });

  it('renders the readiness notice and badges', () => {
    render(<SecurityAccessCompliancePage routeKey="privacy-readiness" userPermissions={['security_access_compliance.privacy_readiness.read']} />);

    expect(screen.getByTestId('sac-incomplete-data-notice')).toBeInTheDocument();
    expect(screen.getByTestId('sac-human-review-badge')).toBeInTheDocument();
  });

  it('mirrors bridge and readiness route models', () => {
    expect(buildSacPageModel('bridges').backendEndpoints).toContain('GET /api/admin/security-access-compliance/bridges/hr');
    expect(buildSacPageModel('privacy-readiness').backendEndpoints).toContain('POST /api/admin/security-access-compliance/privacy-readiness/evidence');
  });
});
