import type { StudentServicesSupportRouteKey } from './types';

export const STUDENT_SERVICES_BOUNDARY_LABELS = {
  humanReviewRequired: 'Human review required',
  readinessOnly: 'Readiness only',
  evidenceMetadataOnly: 'Evidence metadata only',
  noAutomaticApproval: 'No automatic approval',
  noMedicalDiagnosis: 'No medical diagnosis',
  noHiddenScore: 'No hidden score',
  noFakeMetrics: 'No fake metrics',
  noProviderLiveSync: 'No provider/live sync',
  noAutonomousDecision: 'No autonomous decision',
  incompleteDataSupported: 'Incomplete data supported',
  fakeMetricsFalse: 'fake_metrics=false',
  providerLiveEnabledFalse: 'provider_live_enabled=false',
  autonomousDecisionEnabledFalse: 'autonomous_decision_enabled=false',
  hiddenScorePresentFalse: 'hidden_score_present=false',
} as const;

export const STUDENT_SERVICES_BOUNDARY_COPY = [
  STUDENT_SERVICES_BOUNDARY_LABELS.humanReviewRequired,
  STUDENT_SERVICES_BOUNDARY_LABELS.readinessOnly,
  STUDENT_SERVICES_BOUNDARY_LABELS.evidenceMetadataOnly,
  STUDENT_SERVICES_BOUNDARY_LABELS.noAutomaticApproval,
  STUDENT_SERVICES_BOUNDARY_LABELS.noMedicalDiagnosis,
  STUDENT_SERVICES_BOUNDARY_LABELS.noHiddenScore,
  STUDENT_SERVICES_BOUNDARY_LABELS.noFakeMetrics,
  STUDENT_SERVICES_BOUNDARY_LABELS.noProviderLiveSync,
  STUDENT_SERVICES_BOUNDARY_LABELS.noAutonomousDecision,
  STUDENT_SERVICES_BOUNDARY_LABELS.incompleteDataSupported,
] as const;

export const STUDENT_SERVICES_FORBIDDEN_LABELS = [
  'Approve hardship automatically',
  'Approve accommodation automatically',
  'Resolve complaint automatically',
  'Diagnose student',
  'Publish hidden score',
  'Submit to government/provider',
  'Generate fake evidence',
  'Mark fake service completed',
  'Brain/autonomous decision execution',
  'Production ready',
  'Sales ready',
  'GCC ready',
  'L5/L6 ready',
] as const;

export const STUDENT_SERVICES_PAGE_BOUNDARY_LABELS: Record<StudentServicesSupportRouteKey, string[]> = {
  overview: [...STUDENT_SERVICES_BOUNDARY_COPY],
  requests: [
    STUDENT_SERVICES_BOUNDARY_LABELS.humanReviewRequired,
    STUDENT_SERVICES_BOUNDARY_LABELS.evidenceMetadataOnly,
    STUDENT_SERVICES_BOUNDARY_LABELS.noAutomaticApproval,
  ],
  'request-detail': [
    STUDENT_SERVICES_BOUNDARY_LABELS.humanReviewRequired,
    STUDENT_SERVICES_BOUNDARY_LABELS.evidenceMetadataOnly,
    STUDENT_SERVICES_BOUNDARY_LABELS.noAutomaticApproval,
  ],
  cases: [
    STUDENT_SERVICES_BOUNDARY_LABELS.humanReviewRequired,
    STUDENT_SERVICES_BOUNDARY_LABELS.evidenceMetadataOnly,
    STUDENT_SERVICES_BOUNDARY_LABELS.noAutonomousDecision,
  ],
  'case-detail': [
    STUDENT_SERVICES_BOUNDARY_LABELS.humanReviewRequired,
    STUDENT_SERVICES_BOUNDARY_LABELS.evidenceMetadataOnly,
    STUDENT_SERVICES_BOUNDARY_LABELS.noAutonomousDecision,
  ],
  hardship: [
    STUDENT_SERVICES_BOUNDARY_LABELS.humanReviewRequired,
    STUDENT_SERVICES_BOUNDARY_LABELS.readinessOnly,
    STUDENT_SERVICES_BOUNDARY_LABELS.noAutomaticApproval,
  ],
  accommodations: [
    STUDENT_SERVICES_BOUNDARY_LABELS.humanReviewRequired,
    STUDENT_SERVICES_BOUNDARY_LABELS.readinessOnly,
    STUDENT_SERVICES_BOUNDARY_LABELS.noMedicalDiagnosis,
  ],
  complaints: [
    STUDENT_SERVICES_BOUNDARY_LABELS.humanReviewRequired,
    STUDENT_SERVICES_BOUNDARY_LABELS.evidenceMetadataOnly,
    STUDENT_SERVICES_BOUNDARY_LABELS.noAutonomousDecision,
  ],
  escalations: [
    STUDENT_SERVICES_BOUNDARY_LABELS.humanReviewRequired,
    STUDENT_SERVICES_BOUNDARY_LABELS.evidenceMetadataOnly,
    STUDENT_SERVICES_BOUNDARY_LABELS.noAutonomousDecision,
  ],
  dashboard: [
    STUDENT_SERVICES_BOUNDARY_LABELS.fakeMetricsFalse,
    STUDENT_SERVICES_BOUNDARY_LABELS.providerLiveEnabledFalse,
    STUDENT_SERVICES_BOUNDARY_LABELS.autonomousDecisionEnabledFalse,
    STUDENT_SERVICES_BOUNDARY_LABELS.hiddenScorePresentFalse,
    STUDENT_SERVICES_BOUNDARY_LABELS.incompleteDataSupported,
  ],
};

export function getStudentServicesBoundaryLabels(routeKey: StudentServicesSupportRouteKey) {
  return STUDENT_SERVICES_PAGE_BOUNDARY_LABELS[routeKey];
}
