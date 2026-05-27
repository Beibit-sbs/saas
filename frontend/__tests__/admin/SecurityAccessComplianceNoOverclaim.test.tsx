import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { securityAccessComplianceApi } from '@/modules/security-access-compliance/api';
import { SECURITY_ACCESS_COMPLIANCE_NO_OVERCLAIM_COPY } from '@/modules/security-access-compliance/boundaryLabels';
import { SECURITY_ACCESS_COMPLIANCE_ROUTE_DEFINITIONS } from '@/modules/security-access-compliance/constants';
import { buildSacPageModel, SecurityAccessCompliancePage } from '@/modules/security-access-compliance/pages';

const forbiddenLabels = [
  'Certify security',
  'Certify compliance',
  'Legal compliance certified',
  'SOC/SIEM replacement',
  'Resolve incident officially',
  'Generate audit proof',
  'Generate penetration-test result',
  'Generate vulnerability-scan result',
  'Generate risk score',
  'Hidden user risk score',
  'Block user automatically',
  'Sanction user automatically',
  'Delete data automatically',
  'Submit to regulator',
  'Production-ready security',
  'Sales ready',
  'GCC ready',
  'L5/L6 ready',
] as const;

describe('Security / Access / Compliance no-overclaim contract', () => {
  it('does not render forbidden positive labels on overview', () => {
    render(<SecurityAccessCompliancePage routeKey="overview" userPermissions={['security_access_compliance.overview.read']} />);

    for (const label of forbiddenLabels) {
      expect(screen.queryByText(label)).not.toBeInTheDocument();
    }
  });

  it('does not render forbidden positive labels on dashboard', () => {
    render(<SecurityAccessCompliancePage routeKey="dashboard" userPermissions={['security_access_compliance.dashboard.read']} />);

    for (const label of forbiddenLabels) {
      expect(screen.queryByText(label)).not.toBeInTheDocument();
    }
  });

  it('keeps the API surface free of forbidden executor names', () => {
    expect('certifySecurity' in securityAccessComplianceApi).toBe(false);
    expect('resolveIncidentOfficially' in securityAccessComplianceApi).toBe(false);
    expect('generateAuditProof' in securityAccessComplianceApi).toBe(false);
    expect('generateRiskScore' in securityAccessComplianceApi).toBe(false);
    expect('submitToRegulator' in securityAccessComplianceApi).toBe(false);
  });

  it('keeps route models on the negative boundary copy', () => {
    const model = buildSacPageModel('overview');
    for (const line of SECURITY_ACCESS_COMPLIANCE_NO_OVERCLAIM_COPY) {
      expect(model.noOverclaimFooter).toContain(line);
    }
    expect(model.noForbiddenUiActions).toContain('No certification action');
    expect(model.noForbiddenUiActions).not.toContain('Certify security');
  });

  it('keeps the route inventory fixed at 23', () => {
    expect(SECURITY_ACCESS_COMPLIANCE_ROUTE_DEFINITIONS).toHaveLength(23);
  });

  it('does not show production/sales/GCC/L5/L6 claims', () => {
    render(<SecurityAccessCompliancePage routeKey="limitations" userPermissions={['security_access_compliance.limitations.read']} />);

    expect(screen.getByText('No production-ready security claim')).toBeInTheDocument();
    expect(screen.getByText('No sales-ready claim')).toBeInTheDocument();
    expect(screen.getByText('No GCC-ready claim')).toBeInTheDocument();
    expect(screen.getByText('No L5/L6 ready claim.')).toBeInTheDocument();
  });
});
