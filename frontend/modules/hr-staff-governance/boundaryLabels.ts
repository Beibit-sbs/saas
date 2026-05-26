import type { HrRouteKey } from './types';

export const HR_STAFF_GOVERNANCE_BOUNDARY_LABELS = {
  metadataEvidenceOnlyHrFoundation: 'Metadata/evidence-only HR foundation',
  humanReviewRequired: 'Human review required',
  noAutomaticHiringFiring: 'No automatic hiring/firing',
  noAutomaticDisciplinaryDecision: 'No automatic disciplinary decision',
  noAutomaticLeaveApprovalRejection: 'No automatic leave approval/rejection',
  noPayrollExecution: 'No payroll execution',
  noProviderLiveSync: 'No provider live sync',
  noHiddenEmployeeFacultyScore: 'No hidden employee/faculty score',
  noProductionReadyClaim: 'No production-ready claim',
  noSalesReadyClaim: 'No sales-ready claim',
  noGccReadyClaim: 'No GCC-ready claim',
  incompleteDataSupported: 'Incomplete data supported',
  providerReadinessOnly: 'Provider readiness only',
  payrollReadinessOnly: 'Payroll readiness only',
  accessLifecycleReviewOnly: 'Access lifecycle review only',
  bridgeFirstReadOnlyFirst: 'Bridge-first / read-only-first',
  fakeMetricsFalse: 'fakeMetrics=false',
  fakeHrDataFalse: 'fakeHrData=false',
  providerConnectedFalse: 'providerConnected=false',
  liveProviderSyncFalse: 'liveProviderSync=false',
  payrollExecutionEnabledFalse: 'payrollExecutionEnabled=false',
  automaticDecisionEnabledFalse: 'automaticDecisionEnabled=false',
  hiddenScorePresentFalse: 'hiddenScorePresent=false',
} as const;

export const HR_STAFF_GOVERNANCE_BOUNDARY_COPY = [
  HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.metadataEvidenceOnlyHrFoundation,
  HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.humanReviewRequired,
  HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noAutomaticHiringFiring,
  HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noAutomaticDisciplinaryDecision,
  HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noAutomaticLeaveApprovalRejection,
  HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noPayrollExecution,
  HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noProviderLiveSync,
  HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noHiddenEmployeeFacultyScore,
  HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noProductionReadyClaim,
  HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noSalesReadyClaim,
  HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noGccReadyClaim,
  HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.incompleteDataSupported,
  HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.providerReadinessOnly,
  HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.payrollReadinessOnly,
  HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.accessLifecycleReviewOnly,
  HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.bridgeFirstReadOnlyFirst,
] as const;

export const HR_STAFF_GOVERNANCE_FORBIDDEN_LABELS = [
  'Auto hire',
  'Auto fire',
  'Auto approve leave',
  'Auto reject leave',
  'Auto discipline',
  'Execute payroll',
  'Sync 1C now',
  'Connect provider live',
  'Publish employee score',
  'Hidden faculty score',
  'Production ready',
  'Sales ready',
  'GCC ready',
  'L5/L6 ready',
] as const;

export const HR_STAFF_GOVERNANCE_PAGE_BOUNDARY_LABELS: Record<HrRouteKey, string[]> = {
  overview: [...HR_STAFF_GOVERNANCE_BOUNDARY_COPY, HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.fakeMetricsFalse, HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.fakeHrDataFalse],
  dashboard: [
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.metadataEvidenceOnlyHrFoundation,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.fakeMetricsFalse,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.fakeHrDataFalse,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.incompleteDataSupported,
  ],
  recruitment: [
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.metadataEvidenceOnlyHrFoundation,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.humanReviewRequired,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noAutomaticHiringFiring,
  ],
  onboarding: [
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.metadataEvidenceOnlyHrFoundation,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.humanReviewRequired,
  ],
  'employee-records': [
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.metadataEvidenceOnlyHrFoundation,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noHiddenEmployeeFacultyScore,
  ],
  'staff-profiles': [
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.metadataEvidenceOnlyHrFoundation,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noHiddenEmployeeFacultyScore,
  ],
  'faculty-profile': [
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.metadataEvidenceOnlyHrFoundation,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.bridgeFirstReadOnlyFirst,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noHiddenEmployeeFacultyScore,
  ],
  leave: [
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.humanReviewRequired,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noAutomaticLeaveApprovalRejection,
  ],
  performance: [
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.humanReviewRequired,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noHiddenEmployeeFacultyScore,
  ],
  training: [
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.metadataEvidenceOnlyHrFoundation,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.incompleteDataSupported,
  ],
  requests: [
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.humanReviewRequired,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.metadataEvidenceOnlyHrFoundation,
  ],
  appeals: [
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.humanReviewRequired,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.metadataEvidenceOnlyHrFoundation,
  ],
  'policy-exceptions': [
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.humanReviewRequired,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.metadataEvidenceOnlyHrFoundation,
  ],
  disciplinary: [
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.humanReviewRequired,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noAutomaticDisciplinaryDecision,
  ],
  offboarding: [
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.humanReviewRequired,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.accessLifecycleReviewOnly,
  ],
  'access-lifecycle': [
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.accessLifecycleReviewOnly,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.bridgeFirstReadOnlyFirst,
  ],
  'workload-bridge': [
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.bridgeFirstReadOnlyFirst,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noProviderLiveSync,
  ],
  'payroll-readiness': [
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.payrollReadinessOnly,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noPayrollExecution,
  ],
  'provider-readiness': [
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.providerReadinessOnly,
    HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noProviderLiveSync,
  ],
  limitations: [...HR_STAFF_GOVERNANCE_BOUNDARY_COPY],
};

export function getHrBoundaryLabels(routeKey: HrRouteKey) {
  return HR_STAFF_GOVERNANCE_PAGE_BOUNDARY_LABELS[routeKey];
}