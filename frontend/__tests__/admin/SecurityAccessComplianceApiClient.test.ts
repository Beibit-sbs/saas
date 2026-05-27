import { beforeEach, describe, expect, it, vi } from 'vitest';

const client = vi.hoisted(() => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
}));

vi.mock('@/shared/api/client', () => client);

import { securityAccessComplianceApi, SECURITY_ACCESS_COMPLIANCE_API_PATHS } from '@/modules/security-access-compliance/api';

describe('Security / Access / Compliance API client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    client.apiGet.mockResolvedValue(undefined);
    client.apiPost.mockResolvedValue(undefined);
  });

  it('maps core read endpoints', async () => {
    await securityAccessComplianceApi.getSacOverview();
    await securityAccessComplianceApi.getSacReadiness();
    await securityAccessComplianceApi.getSacDashboard();
    await securityAccessComplianceApi.getSacLimitations();
    await securityAccessComplianceApi.getSacMetadataContract();
    await securityAccessComplianceApi.getSacHealth();

    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.overview);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.readiness);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.dashboard);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.limitations);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.metadataContract);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.health);
  });

  it('maps governance and evidence endpoints', async () => {
    await securityAccessComplianceApi.getSacRoles();
    await securityAccessComplianceApi.getSacPermissions();
    await securityAccessComplianceApi.getSacAccessGovernance();
    await securityAccessComplianceApi.getSacRbacEvidence();
    await securityAccessComplianceApi.getSacAbacEvidence();
    await securityAccessComplianceApi.getSacSessions();
    await securityAccessComplianceApi.getSacLoginEvents();

    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.roles);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.permissions);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.accessGovernance);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.rbacEvidence);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.abacEvidence);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.sessions);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.loginEvents);
  });

  it('maps readiness and bridge endpoints', async () => {
    await securityAccessComplianceApi.getSacMfaReadiness();
    await securityAccessComplianceApi.getSacTenantIsolation();
    await securityAccessComplianceApi.getSacIncidents();
    await securityAccessComplianceApi.getSacIncidentReview();
    await securityAccessComplianceApi.getSacRemediation();
    await securityAccessComplianceApi.getSacRisks();
    await securityAccessComplianceApi.getSacComplianceControls();
    await securityAccessComplianceApi.getSacPolicyControls();
    await securityAccessComplianceApi.getSacAuditEvents();
    await securityAccessComplianceApi.getSacSensitiveActions();
    await securityAccessComplianceApi.getSacDataProtection();
    await securityAccessComplianceApi.getSacPrivacyReadiness();
    await securityAccessComplianceApi.getSacExceptions();
    await securityAccessComplianceApi.getSacVisitorAccess();

    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.mfaReadiness);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.tenantIsolation);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.incidents);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.incidentReview);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.remediation);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.risks);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.complianceControls);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.policyControls);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.auditEvents);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.sensitiveActions);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.dataProtection);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.privacyReadiness);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.exceptions);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.visitorAccess);
  });

  it('maps bridge read endpoints', async () => {
    await securityAccessComplianceApi.getSacBridgeHr();
    await securityAccessComplianceApi.getSacBridgeFinance();
    await securityAccessComplianceApi.getSacBridgeDocuments();
    await securityAccessComplianceApi.getSacBridgeStudentServices();

    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.bridgeHr);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.bridgeFinance);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.bridgeDocuments);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.bridgeStudentServices);
  });

  it('maps metadata write endpoints', async () => {
    await securityAccessComplianceApi.createSacIncidentMetadata({ note: 'a' });
    await securityAccessComplianceApi.createSacIncidentReviewMetadata({ note: 'b' });
    await securityAccessComplianceApi.createSacRemediationMetadata({ note: 'c' });
    await securityAccessComplianceApi.createSacRiskMetadata({ note: 'd' });
    await securityAccessComplianceApi.createSacComplianceControlMetadata({ note: 'e' });
    await securityAccessComplianceApi.createSacPolicyControlMetadata({ note: 'f' });
    await securityAccessComplianceApi.createSacAuditEventMetadata({ note: 'g' });
    await securityAccessComplianceApi.createSacSensitiveActionReview({ note: 'h' });

    expect(client.apiPost).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.incidentMetadata, { note: 'a' });
    expect(client.apiPost).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.incidentReviewMetadata, { note: 'b' });
    expect(client.apiPost).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.remediationMetadata, { note: 'c' });
    expect(client.apiPost).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.risksMetadata, { note: 'd' });
    expect(client.apiPost).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.complianceControlsMetadata, { note: 'e' });
    expect(client.apiPost).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.policyControlsMetadata, { note: 'f' });
    expect(client.apiPost).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.auditEventsMetadata, { note: 'g' });
    expect(client.apiPost).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.sensitiveActionsReview, { note: 'h' });
  });

  it('maps evidence write endpoints', async () => {
    await securityAccessComplianceApi.createSacDataProtectionEvidence({ evidence: 'i' });
    await securityAccessComplianceApi.createSacPrivacyReadinessEvidence({ evidence: 'j' });
    await securityAccessComplianceApi.createSacExceptionMetadata({ evidence: 'k' });
    await securityAccessComplianceApi.createSacVisitorAccessMetadata({ evidence: 'l' });
    await securityAccessComplianceApi.createSacBridgeHr({ evidence: 'm' });
    await securityAccessComplianceApi.createSacBridgeFinance({ evidence: 'n' });
    await securityAccessComplianceApi.createSacBridgeDocuments({ evidence: 'o' });
    await securityAccessComplianceApi.createSacBridgeStudentServices({ evidence: 'p' });
    await securityAccessComplianceApi.createSacLimitation({ evidence: 'q' });

    expect(client.apiPost).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.dataProtectionEvidence, { evidence: 'i' });
    expect(client.apiPost).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.privacyReadinessEvidence, { evidence: 'j' });
    expect(client.apiPost).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.exceptionsMetadata, { evidence: 'k' });
    expect(client.apiPost).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.visitorAccessMetadata, { evidence: 'l' });
    expect(client.apiPost).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.bridgeHr, { evidence: 'm' });
    expect(client.apiPost).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.bridgeFinance, { evidence: 'n' });
    expect(client.apiPost).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.bridgeDocuments, { evidence: 'o' });
    expect(client.apiPost).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.bridgeStudentServices, { evidence: 'p' });
    expect(client.apiPost).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.limitation, { evidence: 'q' });
  });

  it('maps safety boundaries and health aliases', async () => {
    await securityAccessComplianceApi.getSacSafetyBoundaries();
    await securityAccessComplianceApi.getSacHealth();

    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.safetyBoundaries);
    expect(client.apiGet).toHaveBeenCalledWith(SECURITY_ACCESS_COMPLIANCE_API_PATHS.health);
  });

  it('does not expose forbidden helper names', () => {
    expect('certifySecurity' in securityAccessComplianceApi).toBe(false);
    expect('certifyCompliance' in securityAccessComplianceApi).toBe(false);
    expect('claimLegalRegulatoryCompliance' in securityAccessComplianceApi).toBe(false);
    expect('replaceSocSiem' in securityAccessComplianceApi).toBe(false);
    expect('generateRiskScore' in securityAccessComplianceApi).toBe(false);
    expect('submitToRegulator' in securityAccessComplianceApi).toBe(false);
  });
});
