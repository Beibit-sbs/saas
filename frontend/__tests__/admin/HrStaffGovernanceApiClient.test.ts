import { beforeEach, describe, expect, it, vi } from 'vitest';

const client = vi.hoisted(() => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
}));

vi.mock('@/shared/api/client', () => client);

import { hrStaffGovernanceApi } from '@/modules/hr-staff-governance/api';
import { HR_STAFF_GOVERNANCE_API_PATHS } from '@/modules/hr-staff-governance/constants';

describe('HR Staff Governance API client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    client.apiGet.mockResolvedValue(undefined);
    client.apiPost.mockResolvedValue(undefined);
    client.apiPatch.mockResolvedValue(undefined);
  });

  it('maps overview, safety, dashboard, and health reads', async () => {
    await hrStaffGovernanceApi.getHrOverview();
    await hrStaffGovernanceApi.getHrSafetyBoundaries();
    await hrStaffGovernanceApi.getHrDashboard();
    await hrStaffGovernanceApi.getHealth();

    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.overview);
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.safetyBoundaries);
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.dashboard);
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.health);
  });

  it('maps staff profile and employee record CRUD calls', async () => {
    await hrStaffGovernanceApi.getStaffProfiles();
    await hrStaffGovernanceApi.getStaffProfile(7);
    await hrStaffGovernanceApi.createStaffProfile({ title: 'A' });
    await hrStaffGovernanceApi.updateStaffProfile(7, { title: 'B' });
    await hrStaffGovernanceApi.getEmployeeRecords();
    await hrStaffGovernanceApi.createEmployeeRecord({ title: 'C' });
    await hrStaffGovernanceApi.updateEmployeeRecord(8, { title: 'D' });

    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.staffProfiles);
    expect(client.apiGet).toHaveBeenCalledWith(`${HR_STAFF_GOVERNANCE_API_PATHS.staffProfiles}/7`);
    expect(client.apiPost).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.staffProfiles, { title: 'A' });
    expect(client.apiPatch).toHaveBeenCalledWith(`${HR_STAFF_GOVERNANCE_API_PATHS.staffProfiles}/7`, { title: 'B' });
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.employeeRecords);
    expect(client.apiPost).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.employeeRecords, { title: 'C' });
    expect(client.apiPatch).toHaveBeenCalledWith(`${HR_STAFF_GOVERNANCE_API_PATHS.employeeRecords}/8`, { title: 'D' });
  });

  it('maps recruitment, onboarding, and probation calls', async () => {
    await hrStaffGovernanceApi.getRecruitment();
    await hrStaffGovernanceApi.createRecruitmentRequest({ title: 'Recruitment' });
    await hrStaffGovernanceApi.reviewRecruitmentRequest(2, { status: 'reviewed' });
    await hrStaffGovernanceApi.createHiringEvidence({ title: 'Evidence' });
    await hrStaffGovernanceApi.getOnboarding();
    await hrStaffGovernanceApi.createOnboardingCase({ title: 'Onboarding' });
    await hrStaffGovernanceApi.updateOnboardingCase(3, { notes: 'Updated' });
    await hrStaffGovernanceApi.createProbationReview({ title: 'Probation' });

    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.recruitmentRequests);
    expect(client.apiPost).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.recruitmentRequests, { title: 'Recruitment' });
    expect(client.apiPost).toHaveBeenCalledWith(`${HR_STAFF_GOVERNANCE_API_PATHS.recruitmentRequests}/2/review`, { status: 'reviewed' });
    expect(client.apiPost).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.hiringEvidence, { title: 'Evidence' });
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.onboardingCases);
    expect(client.apiPost).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.onboardingCases, { title: 'Onboarding' });
    expect(client.apiPatch).toHaveBeenCalledWith(`${HR_STAFF_GOVERNANCE_API_PATHS.onboardingCases}/3`, { notes: 'Updated' });
    expect(client.apiPost).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.probationReviews, { title: 'Probation' });
  });

  it('maps leave, appraisal, and training calls', async () => {
    await hrStaffGovernanceApi.getLeave();
    await hrStaffGovernanceApi.createLeaveRequest({ title: 'Leave' });
    await hrStaffGovernanceApi.reviewLeaveRequest(4, { status: 'reviewed' });
    await hrStaffGovernanceApi.getAppraisals();
    await hrStaffGovernanceApi.createAppraisalCycle({ title: 'Cycle' });
    await hrStaffGovernanceApi.reviewAppraisal(5, { status: 'reviewed' });
    await hrStaffGovernanceApi.getTraining();
    await hrStaffGovernanceApi.createTrainingCertification({ title: 'Training' });
    await hrStaffGovernanceApi.updateTrainingCertification(6, { notes: 'Renewed' });

    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.leaveRequests);
    expect(client.apiPost).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.leaveRequests, { title: 'Leave' });
    expect(client.apiPost).toHaveBeenCalledWith(`${HR_STAFF_GOVERNANCE_API_PATHS.leaveRequests}/4/review`, { status: 'reviewed' });
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.appraisals);
    expect(client.apiPost).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.appraisals, { title: 'Cycle' });
    expect(client.apiPost).toHaveBeenCalledWith(`${HR_STAFF_GOVERNANCE_API_PATHS.appraisals}/5/review`, { status: 'reviewed' });
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.trainingCertifications);
    expect(client.apiPost).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.trainingCertifications, { title: 'Training' });
    expect(client.apiPatch).toHaveBeenCalledWith(`${HR_STAFF_GOVERNANCE_API_PATHS.trainingCertifications}/6`, { notes: 'Renewed' });
  });

  it('maps requests, appeals, policy exceptions, and disciplinary calls', async () => {
    await hrStaffGovernanceApi.getStaffRequests();
    await hrStaffGovernanceApi.reviewStaffRequest(1, { status: 'reviewed' });
    await hrStaffGovernanceApi.getStaffAppeals();
    await hrStaffGovernanceApi.reviewStaffAppeal(2, { status: 'reviewed' });
    await hrStaffGovernanceApi.getPolicyExceptions();
    await hrStaffGovernanceApi.reviewPolicyException(3, { status: 'reviewed' });
    await hrStaffGovernanceApi.getDisciplinaryCases();
    await hrStaffGovernanceApi.reviewDisciplinaryCase(4, { status: 'reviewed' });

    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.staffRequests);
    expect(client.apiPost).toHaveBeenCalledWith(`${HR_STAFF_GOVERNANCE_API_PATHS.staffRequests}/1/review`, { status: 'reviewed' });
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.staffAppeals);
    expect(client.apiPost).toHaveBeenCalledWith(`${HR_STAFF_GOVERNANCE_API_PATHS.staffAppeals}/2/review`, { status: 'reviewed' });
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.policyExceptions);
    expect(client.apiPost).toHaveBeenCalledWith(`${HR_STAFF_GOVERNANCE_API_PATHS.policyExceptions}/3/review`, { status: 'reviewed' });
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.disciplinaryCases);
    expect(client.apiPost).toHaveBeenCalledWith(`${HR_STAFF_GOVERNANCE_API_PATHS.disciplinaryCases}/4/review`, { status: 'reviewed' });
  });

  it('maps offboarding, access lifecycle, workload, payroll, and provider calls', async () => {
    await hrStaffGovernanceApi.getOffboarding();
    await hrStaffGovernanceApi.updateOffboardingCase(5, { status: 'REVIEW' });
    await hrStaffGovernanceApi.reviewAccessLifecycle({ title: 'Access' });
    await hrStaffGovernanceApi.getWorkloadBridge();
    await hrStaffGovernanceApi.createWorkloadBridgeRecord({ title: 'Bridge' });
    await hrStaffGovernanceApi.getPayrollReadiness();
    await hrStaffGovernanceApi.createPayrollReadinessProfile({ title: 'Payroll' });
    await hrStaffGovernanceApi.getProviderReadiness();
    await hrStaffGovernanceApi.createProviderReadinessEvidence({ title: 'Provider' });

    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.offboardingCases);
    expect(client.apiPatch).toHaveBeenCalledWith(`${HR_STAFF_GOVERNANCE_API_PATHS.offboardingCases}/5`, { status: 'REVIEW' });
    expect(client.apiPost).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.accessLifecycleReviews, { title: 'Access' });
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.workloadBridgeRecords);
    expect(client.apiPost).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.workloadBridgeRecords, { title: 'Bridge' });
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.payrollReadinessProfiles);
    expect(client.apiPost).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.payrollReadinessProfiles, { title: 'Payroll' });
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.providerReadinessEvidence);
    expect(client.apiPost).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.providerReadinessEvidence, { title: 'Provider' });
  });

  it('maps bridge, audit, readiness, roles, permissions, and metadata helpers', async () => {
    await hrStaffGovernanceApi.getBridgeAcademicOperations();
    await hrStaffGovernanceApi.getBridgeIamAccess();
    await hrStaffGovernanceApi.getBridgeFinancePayroll();
    await hrStaffGovernanceApi.getBridgeDocumentContracts();
    await hrStaffGovernanceApi.getHrAuditEvents();
    await hrStaffGovernanceApi.getBrainSignals();
    await hrStaffGovernanceApi.getLimitations();
    await hrStaffGovernanceApi.getRoles();
    await hrStaffGovernanceApi.getPermissions();
    await hrStaffGovernanceApi.getMetadataContract();
    await hrStaffGovernanceApi.getReadiness();

    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.bridgeSummary('academic-operations'));
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.bridgeSummary('iam-access'));
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.bridgeSummary('finance-payroll'));
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.bridgeSummary('document-contracts'));
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.audit);
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.brainSignals);
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.limitations);
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.roles);
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.permissions);
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.metadataContract);
    expect(client.apiGet).toHaveBeenCalledWith(HR_STAFF_GOVERNANCE_API_PATHS.readiness);
  });

  it('does not expose forbidden executor helpers', () => {
    expect('executePayroll' in hrStaffGovernanceApi).toBe(false);
    expect('connectProviderLive' in hrStaffGovernanceApi).toBe(false);
    expect('autoHire' in hrStaffGovernanceApi).toBe(false);
    expect('hiddenEmployeeScore' in hrStaffGovernanceApi).toBe(false);
  });
});