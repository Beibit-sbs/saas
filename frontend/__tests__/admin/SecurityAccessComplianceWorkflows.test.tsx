import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { buildSacPageModel, SecurityAccessCompliancePage } from '@/modules/security-access-compliance/pages';

const routes = [
  ['incidents', 'security_access_compliance.incidents.read', 'sac-page-incidents'],
  ['incident-review', 'security_access_compliance.incident_review.read', 'sac-page-incident-review'],
  ['remediation', 'security_access_compliance.remediation.read', 'sac-page-remediation'],
  ['risks', 'security_access_compliance.risks.read', 'sac-page-risks'],
  ['compliance-controls', 'security_access_compliance.compliance_controls.read', 'sac-page-compliance-controls'],
  ['policy-controls', 'security_access_compliance.policy_controls.read', 'sac-page-policy-controls'],
  ['audit-events', 'security_access_compliance.audit_events.read', 'sac-page-audit-events'],
  ['sensitive-actions', 'security_access_compliance.sensitive_actions.read', 'sac-page-sensitive-actions'],
] as const;

describe('Security / Access / Compliance workflows', () => {
  it.each(routes)('renders %s workflow surface', (routeKey, permission, testId) => {
    render(<SecurityAccessCompliancePage routeKey={routeKey} userPermissions={[permission]} />);
    expect(screen.getByTestId(testId)).toBeInTheDocument();
  });

  it('renders incidents metadata shell', () => {
    render(<SecurityAccessCompliancePage routeKey="incidents" userPermissions={['security_access_compliance.incidents.read']} />);

    expect(screen.getByTestId('sac-form-shell-incidents')).toBeInTheDocument();
    expect(screen.getByText('No fake incident resolution')).toBeInTheDocument();
  });

  it('renders incident review metadata shell', () => {
    render(<SecurityAccessCompliancePage routeKey="incident-review" userPermissions={['security_access_compliance.incident_review.read']} />);

    expect(screen.getByTestId('sac-form-shell-incident-review')).toBeInTheDocument();
  });

  it('renders remediation metadata shell', () => {
    render(<SecurityAccessCompliancePage routeKey="remediation" userPermissions={['security_access_compliance.remediation.read']} />);

    expect(screen.getByTestId('sac-form-shell-remediation')).toBeInTheDocument();
  });

  it('renders risks metadata shell', () => {
    render(<SecurityAccessCompliancePage routeKey="risks" userPermissions={['security_access_compliance.risks.read']} />);

    expect(screen.getByTestId('sac-form-shell-risks')).toBeInTheDocument();
  });

  it('renders compliance controls metadata shell', () => {
    render(<SecurityAccessCompliancePage routeKey="compliance-controls" userPermissions={['security_access_compliance.compliance_controls.read']} />);

    expect(screen.getByTestId('sac-form-shell-compliance-controls')).toBeInTheDocument();
  });

  it('renders policy controls metadata shell', () => {
    render(<SecurityAccessCompliancePage routeKey="policy-controls" userPermissions={['security_access_compliance.policy_controls.read']} />);

    expect(screen.getByTestId('sac-form-shell-policy-controls')).toBeInTheDocument();
  });

  it('renders audit events metadata shell', () => {
    render(<SecurityAccessCompliancePage routeKey="audit-events" userPermissions={['security_access_compliance.audit_events.read']} />);

    expect(screen.getByTestId('sac-form-shell-audit-events')).toBeInTheDocument();
  });

  it('renders sensitive actions review shell', () => {
    render(<SecurityAccessCompliancePage routeKey="sensitive-actions" userPermissions={['security_access_compliance.sensitive_actions.read']} />);

    expect(screen.getByTestId('sac-form-shell-sensitive-actions')).toBeInTheDocument();
  });

  it('mirrors workflow route models', () => {
    expect(buildSacPageModel('incidents').backendEndpoints).toContain('POST /api/admin/security-access-compliance/incidents/metadata');
    expect(buildSacPageModel('sensitive-actions').backendEndpoints).toContain('POST /api/admin/security-access-compliance/sensitive-actions/review');
  });
});
