export const MODULE_NAME = 'student-lifecycle';
export const API_BASE_PATH = '/api/admin/student-lifecycle';
export const UI_BASE_PATH = '/console/student-lifecycle';
export const EXPECTED_DATA_SOURCE = 'computed_from_student_lifecycle_metadata';

export const PROVIDER_INTEGRATION_ENABLED = false;
export const PLATONUS_LIVE_INTEGRATION_ENABLED = false;
export const SIS_SYNC_ENABLED = false;
export const OFFICIAL_TRANSCRIPT_ISSUING_ENABLED = false;
export const AUTONOMOUS_DECISION_ENABLED = false;
export const HIDDEN_SCORE_ENABLED = false;
export const FAKE_METRICS_ENABLED = false;

export const STUDENT_LIFECYCLE_BOUNDARY_LABELS = {
  humanReviewRequired: 'Human review required',
  noAutomatedDecision: 'No automated decision is made',
  providerNotEnabled: 'Provider integration not enabled',
  metadataOnly: 'Metadata only',
  incompleteData: 'Incomplete data',
  sourceUnavailable: 'Source unavailable',
  unofficialPreview: 'Unofficial preview',
  officialDocumentNotIssued: 'Official document not issued',
  digitalSignatureNotEnabled: 'Digital signature not enabled',
  noHiddenRiskScore: 'No hidden risk score',
  supportVisibilityOnly: 'Support visibility only',
  noAutomaticGraduationDecision: 'No automatic graduation eligibility decision',
  noAutonomousAppealDecision: 'No autonomous appeal decision',
  auditBackedTransition: 'Audit-backed transition',
  noHardDelete: 'No hard delete',
} as const;

export const STUDENT_LIFECYCLE_BOUNDARY_COPY = [
  STUDENT_LIFECYCLE_BOUNDARY_LABELS.humanReviewRequired,
  STUDENT_LIFECYCLE_BOUNDARY_LABELS.noAutomatedDecision,
  STUDENT_LIFECYCLE_BOUNDARY_LABELS.providerNotEnabled,
  STUDENT_LIFECYCLE_BOUNDARY_LABELS.metadataOnly,
  STUDENT_LIFECYCLE_BOUNDARY_LABELS.incompleteData,
  STUDENT_LIFECYCLE_BOUNDARY_LABELS.sourceUnavailable,
  STUDENT_LIFECYCLE_BOUNDARY_LABELS.unofficialPreview,
  STUDENT_LIFECYCLE_BOUNDARY_LABELS.officialDocumentNotIssued,
  STUDENT_LIFECYCLE_BOUNDARY_LABELS.digitalSignatureNotEnabled,
  STUDENT_LIFECYCLE_BOUNDARY_LABELS.noHiddenRiskScore,
  STUDENT_LIFECYCLE_BOUNDARY_LABELS.supportVisibilityOnly,
] as const;

export const STUDENT_LIFECYCLE_RUNTIME_ROUTES = [
  UI_BASE_PATH,
  `${UI_BASE_PATH}/applicants`,
  `${UI_BASE_PATH}/students`,
  `${UI_BASE_PATH}/enrollment`,
  `${UI_BASE_PATH}/academic-records`,
  `${UI_BASE_PATH}/transcripts`,
  `${UI_BASE_PATH}/degree-progress`,
  `${UI_BASE_PATH}/requests`,
  `${UI_BASE_PATH}/appeals`,
  `${UI_BASE_PATH}/interventions`,
  `${UI_BASE_PATH}/audit`,
] as const;

export const STUDENT_LIFECYCLE_DEFAULT_LIMITATIONS = [
  STUDENT_LIFECYCLE_BOUNDARY_LABELS.humanReviewRequired,
  STUDENT_LIFECYCLE_BOUNDARY_LABELS.noAutomatedDecision,
  STUDENT_LIFECYCLE_BOUNDARY_LABELS.providerNotEnabled,
] as const;