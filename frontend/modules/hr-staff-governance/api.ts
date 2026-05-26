import { apiGet, apiPatch, apiPost } from '@/shared/api/client';
import { HR_STAFF_GOVERNANCE_API_PATHS } from './constants';
import type {
  HrAccessLifecycleReview,
  HrAppraisal,
  HrAuditEvent,
  HrBrainSignal,
  HrBridgeSummary,
  HrDashboardSummary,
  HrDisciplinaryCase,
  HrEmployeeRecord,
  HrEvidenceItem,
  HrFoundationSummary,
  HrLimitation,
  HrOffboardingCase,
  HrOnboardingCase,
  HrPayrollReadinessProfile,
  HrPermission,
  HrPolicyException,
  HrProbationReview,
  HrProviderReadinessEvidence,
  HrReadiness,
  HrRecruitmentRequest,
  HrRole,
  HrSafetyBoundary,
  HrStaffAppeal,
  HrStaffProfile,
  HrStaffRequest,
  HrTrainingCertification,
  HrWorkloadBridgeRecord,
  HrLeaveRequest,
} from './types';

type PatchPayload<T> = Partial<T> & Record<string, unknown>;

export const hrStaffGovernanceApi = {
  getHrOverview: () => apiGet<HrFoundationSummary>(HR_STAFF_GOVERNANCE_API_PATHS.overview),
  getHrSafetyBoundaries: () => apiGet<HrSafetyBoundary>(HR_STAFF_GOVERNANCE_API_PATHS.safetyBoundaries),
  getHrDashboard: () => apiGet<HrDashboardSummary>(HR_STAFF_GOVERNANCE_API_PATHS.dashboard),
  getHrAuditEvents: () => apiGet<HrAuditEvent[]>(HR_STAFF_GOVERNANCE_API_PATHS.audit),
  getHrEvidence: () => apiGet<HrEvidenceItem[]>(HR_STAFF_GOVERNANCE_API_PATHS.hiringEvidence),

  getStaffProfiles: () => apiGet<HrStaffProfile[]>(HR_STAFF_GOVERNANCE_API_PATHS.staffProfiles),
  getStaffProfile: (id: number | string) => apiGet<HrStaffProfile>(`${HR_STAFF_GOVERNANCE_API_PATHS.staffProfiles}/${id}`),
  createStaffProfile: (payload: PatchPayload<HrStaffProfile>) => apiPost<HrStaffProfile>(HR_STAFF_GOVERNANCE_API_PATHS.staffProfiles, payload),
  updateStaffProfile: (id: number | string, payload: PatchPayload<HrStaffProfile>) => apiPatch<HrStaffProfile>(`${HR_STAFF_GOVERNANCE_API_PATHS.staffProfiles}/${id}`, payload),

  getEmployeeRecords: () => apiGet<HrEmployeeRecord[]>(HR_STAFF_GOVERNANCE_API_PATHS.employeeRecords),
  createEmployeeRecord: (payload: PatchPayload<HrEmployeeRecord>) => apiPost<HrEmployeeRecord>(HR_STAFF_GOVERNANCE_API_PATHS.employeeRecords, payload),
  updateEmployeeRecord: (id: number | string, payload: PatchPayload<HrEmployeeRecord>) => apiPatch<HrEmployeeRecord>(`${HR_STAFF_GOVERNANCE_API_PATHS.employeeRecords}/${id}`, payload),

  getRecruitment: () => apiGet<HrRecruitmentRequest[]>(HR_STAFF_GOVERNANCE_API_PATHS.recruitmentRequests),
  createRecruitmentRequest: (payload: PatchPayload<HrRecruitmentRequest>) => apiPost<HrRecruitmentRequest>(HR_STAFF_GOVERNANCE_API_PATHS.recruitmentRequests, payload),
  reviewRecruitmentRequest: (id: number | string, payload: PatchPayload<HrRecruitmentRequest>) => apiPost<HrRecruitmentRequest>(`${HR_STAFF_GOVERNANCE_API_PATHS.recruitmentRequests}/${id}/review`, payload),
  createHiringEvidence: (payload: PatchPayload<HrEvidenceItem>) => apiPost<HrEvidenceItem>(HR_STAFF_GOVERNANCE_API_PATHS.hiringEvidence, payload),

  getOnboarding: () => apiGet<HrOnboardingCase[]>(HR_STAFF_GOVERNANCE_API_PATHS.onboardingCases),
  createOnboardingCase: (payload: PatchPayload<HrOnboardingCase>) => apiPost<HrOnboardingCase>(HR_STAFF_GOVERNANCE_API_PATHS.onboardingCases, payload),
  updateOnboardingCase: (id: number | string, payload: PatchPayload<HrOnboardingCase>) => apiPatch<HrOnboardingCase>(`${HR_STAFF_GOVERNANCE_API_PATHS.onboardingCases}/${id}`, payload),
  createProbationReview: (payload: PatchPayload<HrProbationReview>) => apiPost<HrProbationReview>(HR_STAFF_GOVERNANCE_API_PATHS.probationReviews, payload),

  getLeave: () => apiGet<HrLeaveRequest[]>(HR_STAFF_GOVERNANCE_API_PATHS.leaveRequests),
  createLeaveRequest: (payload: PatchPayload<HrLeaveRequest>) => apiPost<HrLeaveRequest>(HR_STAFF_GOVERNANCE_API_PATHS.leaveRequests, payload),
  reviewLeaveRequest: (id: number | string, payload: PatchPayload<HrLeaveRequest>) => apiPost<HrLeaveRequest>(`${HR_STAFF_GOVERNANCE_API_PATHS.leaveRequests}/${id}/review`, payload),

  getAppraisals: () => apiGet<HrAppraisal[]>(HR_STAFF_GOVERNANCE_API_PATHS.appraisals),
  createAppraisalCycle: (payload: PatchPayload<HrAppraisal>) => apiPost<HrAppraisal>(HR_STAFF_GOVERNANCE_API_PATHS.appraisals, payload),
  reviewAppraisal: (id: number | string, payload: PatchPayload<HrAppraisal>) => apiPost<HrAppraisal>(`${HR_STAFF_GOVERNANCE_API_PATHS.appraisals}/${id}/review`, payload),

  getTraining: () => apiGet<HrTrainingCertification[]>(HR_STAFF_GOVERNANCE_API_PATHS.trainingCertifications),
  createTrainingCertification: (payload: PatchPayload<HrTrainingCertification>) => apiPost<HrTrainingCertification>(HR_STAFF_GOVERNANCE_API_PATHS.trainingCertifications, payload),
  updateTrainingCertification: (id: number | string, payload: PatchPayload<HrTrainingCertification>) => apiPatch<HrTrainingCertification>(`${HR_STAFF_GOVERNANCE_API_PATHS.trainingCertifications}/${id}`, payload),

  getStaffRequests: () => apiGet<HrStaffRequest[]>(HR_STAFF_GOVERNANCE_API_PATHS.staffRequests),
  createStaffRequest: (payload: PatchPayload<HrStaffRequest>) => apiPost<HrStaffRequest>(HR_STAFF_GOVERNANCE_API_PATHS.staffRequests, payload),
  reviewStaffRequest: (id: number | string, payload: PatchPayload<HrStaffRequest>) => apiPost<HrStaffRequest>(`${HR_STAFF_GOVERNANCE_API_PATHS.staffRequests}/${id}/review`, payload),

  getStaffAppeals: () => apiGet<HrStaffAppeal[]>(HR_STAFF_GOVERNANCE_API_PATHS.staffAppeals),
  createStaffAppeal: (payload: PatchPayload<HrStaffAppeal>) => apiPost<HrStaffAppeal>(HR_STAFF_GOVERNANCE_API_PATHS.staffAppeals, payload),
  reviewStaffAppeal: (id: number | string, payload: PatchPayload<HrStaffAppeal>) => apiPost<HrStaffAppeal>(`${HR_STAFF_GOVERNANCE_API_PATHS.staffAppeals}/${id}/review`, payload),

  getPolicyExceptions: () => apiGet<HrPolicyException[]>(HR_STAFF_GOVERNANCE_API_PATHS.policyExceptions),
  createPolicyException: (payload: PatchPayload<HrPolicyException>) => apiPost<HrPolicyException>(HR_STAFF_GOVERNANCE_API_PATHS.policyExceptions, payload),
  reviewPolicyException: (id: number | string, payload: PatchPayload<HrPolicyException>) => apiPost<HrPolicyException>(`${HR_STAFF_GOVERNANCE_API_PATHS.policyExceptions}/${id}/review`, payload),

  getDisciplinaryCases: () => apiGet<HrDisciplinaryCase[]>(HR_STAFF_GOVERNANCE_API_PATHS.disciplinaryCases),
  createDisciplinaryCase: (payload: PatchPayload<HrDisciplinaryCase>) => apiPost<HrDisciplinaryCase>(HR_STAFF_GOVERNANCE_API_PATHS.disciplinaryCases, payload),
  reviewDisciplinaryCase: (id: number | string, payload: PatchPayload<HrDisciplinaryCase>) => apiPost<HrDisciplinaryCase>(`${HR_STAFF_GOVERNANCE_API_PATHS.disciplinaryCases}/${id}/review`, payload),

  getOffboarding: () => apiGet<HrOffboardingCase[]>(HR_STAFF_GOVERNANCE_API_PATHS.offboardingCases),
  createOffboardingCase: (payload: PatchPayload<HrOffboardingCase>) => apiPost<HrOffboardingCase>(HR_STAFF_GOVERNANCE_API_PATHS.offboardingCases, payload),
  updateOffboardingCase: (id: number | string, payload: PatchPayload<HrOffboardingCase>) => apiPatch<HrOffboardingCase>(`${HR_STAFF_GOVERNANCE_API_PATHS.offboardingCases}/${id}`, payload),

  reviewAccessLifecycle: (payload: PatchPayload<HrAccessLifecycleReview>) => apiPost<HrAccessLifecycleReview>(HR_STAFF_GOVERNANCE_API_PATHS.accessLifecycleReviews, payload),
  getWorkloadBridge: () => apiGet<HrWorkloadBridgeRecord[]>(HR_STAFF_GOVERNANCE_API_PATHS.workloadBridgeRecords),
  createWorkloadBridgeRecord: (payload: PatchPayload<HrWorkloadBridgeRecord>) => apiPost<HrWorkloadBridgeRecord>(HR_STAFF_GOVERNANCE_API_PATHS.workloadBridgeRecords, payload),

  getPayrollReadiness: () => apiGet<HrPayrollReadinessProfile[]>(HR_STAFF_GOVERNANCE_API_PATHS.payrollReadinessProfiles),
  createPayrollReadinessProfile: (payload: PatchPayload<HrPayrollReadinessProfile>) => apiPost<HrPayrollReadinessProfile>(HR_STAFF_GOVERNANCE_API_PATHS.payrollReadinessProfiles, payload),
  getProviderReadiness: () => apiGet<HrProviderReadinessEvidence[]>(HR_STAFF_GOVERNANCE_API_PATHS.providerReadinessEvidence),
  createProviderReadinessEvidence: (payload: PatchPayload<HrProviderReadinessEvidence>) => apiPost<HrProviderReadinessEvidence>(HR_STAFF_GOVERNANCE_API_PATHS.providerReadinessEvidence, payload),

  getBridgeAcademicOperations: () => apiGet<HrBridgeSummary>(HR_STAFF_GOVERNANCE_API_PATHS.bridgeSummary('academic-operations')),
  getBridgeIamAccess: () => apiGet<HrBridgeSummary>(HR_STAFF_GOVERNANCE_API_PATHS.bridgeSummary('iam-access')),
  getBridgeFinancePayroll: () => apiGet<HrBridgeSummary>(HR_STAFF_GOVERNANCE_API_PATHS.bridgeSummary('finance-payroll')),
  getBridgeDocumentContracts: () => apiGet<HrBridgeSummary>(HR_STAFF_GOVERNANCE_API_PATHS.bridgeSummary('document-contracts')),
  getBrainSignals: () => apiGet<HrBrainSignal[]>(HR_STAFF_GOVERNANCE_API_PATHS.brainSignals),
  getLimitations: () => apiGet<HrLimitation[]>(HR_STAFF_GOVERNANCE_API_PATHS.limitations),
  getHealth: () => apiGet<Record<string, unknown>>(HR_STAFF_GOVERNANCE_API_PATHS.health),
  getRoles: () => apiGet<HrRole[]>(HR_STAFF_GOVERNANCE_API_PATHS.roles),
  getPermissions: () => apiGet<HrPermission[]>(HR_STAFF_GOVERNANCE_API_PATHS.permissions),
  getMetadataContract: () => apiGet<Record<string, unknown>>(HR_STAFF_GOVERNANCE_API_PATHS.metadataContract),
  getReadiness: () => apiGet<HrReadiness>(HR_STAFF_GOVERNANCE_API_PATHS.readiness),
};