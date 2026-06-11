import {
  QUALITY_ACCREDITATION_BOUNDARY_COPY,
  QUALITY_ACCREDITATION_BOUNDARY_LABELS,
} from './boundaryLabels';

export const MODULE_NAME = 'quality-accreditation';
export const API_PREFIX = '/api/admin/quality-accreditation';
export const UI_BASE_PATH = '/console/quality-accreditation';

export const QUALITY_ACCREDITATION_BACKEND_TABLE_COUNT = 32;
export const QUALITY_ACCREDITATION_BACKEND_ROUTE_COUNT = 70;
export const QUALITY_ACCREDITATION_BACKEND_PERMISSION_COUNT = 55;
export const SOURCE_BACKEND_RUNTIME_COMMIT = 'f97ce31';
export const SOURCE_BACKEND_B1_COMMIT = 'fb2734c';
export const SOURCE_BACKEND_SPEC_COMMIT = 'ad2cad9';
export const SOURCE_PRODUCT_MAP_COMMIT = '1253e19';
export const SOURCE_VERTICAL_SELECTION_COMMIT = '7da0c70';
export const RUNTIME_MODE = 'METADATA_EVIDENCE_ONLY';
export const DATA_SOURCE = 'computed_from_quality_accreditation_metadata';

export const OFFICIAL_ACCREDITATION_APPROVAL_ENABLED = false;
export const OFFICIAL_MINISTRY_SUBMISSION_ENABLED = false;
export const OFFICIAL_RANKING_CLAIM_ENABLED = false;
export const AUTOMATIC_ACCREDITATION_DECISION_ENABLED = false;
export const PROVIDER_INTEGRATION_ENABLED = false;
export const EXTERNAL_DATABASE_SYNC_ENABLED = false;
export const HIDDEN_SCORE_PRESENT = false;
export const FAKE_METRICS = false;
export const FAKE_EVIDENCE = false;
export const HUMAN_REVIEW_REQUIRED = true;

export const QUALITY_ACCREDITATION_ROUTES = {
  runtimeShell: `${UI_BASE_PATH}/runtime-shell`,
  accreditationRegistry: `${UI_BASE_PATH}/accreditation-registry`,
  accreditationEvidence: `${UI_BASE_PATH}/accreditation-evidence`,
  correctiveActions: `${UI_BASE_PATH}/corrective-actions`,
  overview: UI_BASE_PATH,
  dashboard: `${UI_BASE_PATH}/dashboard`,
  standards: `${UI_BASE_PATH}/standards`,
  evidence: `${UI_BASE_PATH}/evidence`,
  programReadiness: `${UI_BASE_PATH}/program-readiness`,
  institutionalReadiness: `${UI_BASE_PATH}/institutional-readiness`,
  selfAssessment: `${UI_BASE_PATH}/self-assessment`,
  improvementPlanRuntime: `${UI_BASE_PATH}/improvement-plan`,
  auditFindingsRuntime: `${UI_BASE_PATH}/audit-findings`,
  readinessMonitoringRuntime: `${UI_BASE_PATH}/readiness-monitoring`,
  improvementPlans: `${UI_BASE_PATH}/improvement-plans`,
  internalAudits: `${UI_BASE_PATH}/internal-audits`,
  programReview: `${UI_BASE_PATH}/program-review`,
  learningOutcomes: `${UI_BASE_PATH}/learning-outcomes`,
  stakeholderFeedback: `${UI_BASE_PATH}/stakeholder-feedback`,
  committee: `${UI_BASE_PATH}/committee`,
  externalReview: `${UI_BASE_PATH}/external-review`,
  gapAnalysis: `${UI_BASE_PATH}/gap-analysis`,
  calendar: `${UI_BASE_PATH}/calendar`,
  riskRegister: `${UI_BASE_PATH}/risk-register`,
  bridges: `${UI_BASE_PATH}/bridges`,
  limitations: `${UI_BASE_PATH}/limitations`,
} as const;

export const QUALITY_ACCREDITATION_API_PATHS = {
  runtimeShell: '/api/v1/quality-accreditation/runtime-shell',
  accreditationRegistry: '/api/v1/quality-accreditation/accreditation-registry',
  accreditationEvidence: '/api/v1/quality-accreditation/accreditation-evidence',
  selfAssessmentRuntime: '/api/v1/quality-accreditation/self-assessment',
  correctiveActionRuntime: '/api/v1/quality-accreditation/corrective-actions',
  improvementPlanRuntime: '/api/v1/quality-accreditation/improvement-plan-runtime',
  auditFindingsRuntime: '/api/v1/quality-accreditation/audit-findings-runtime',
  readinessMonitoringRuntime: '/api/v1/quality-accreditation/readiness-monitoring-runtime',
  health: `${API_PREFIX}/health`,
  overview: `${API_PREFIX}/overview`,
  dashboard: `${API_PREFIX}/dashboard`,
  matrixSummary: `${API_PREFIX}/matrix-summary`,
  limitations: `${API_PREFIX}/limitations`,
  frameworks: `${API_PREFIX}/frameworks`,
  standards: `${API_PREFIX}/standards`,
  criteria: `${API_PREFIX}/criteria`,
  standardsEvidenceRequirements: `${API_PREFIX}/standards-evidence-requirements`,
  evidence: `${API_PREFIX}/evidence`,
  evidenceLimitations: `${API_PREFIX}/evidence-limitations`,
  programReadiness: `${API_PREFIX}/program-readiness`,
  institutionalReadiness: `${API_PREFIX}/institutional-readiness`,
  selfAssessment: `${API_PREFIX}/self-assessment`,
  selfAssessmentSections: `${API_PREFIX}/self-assessment-sections`,
  improvementPlans: `${API_PREFIX}/improvement-plans`,
  improvementActions: `${API_PREFIX}/improvement-actions`,
  internalAudits: `${API_PREFIX}/internal-audits`,
  auditFindings: `${API_PREFIX}/audit-findings`,
  programReview: `${API_PREFIX}/program-review`,
  learningOutcomes: `${API_PREFIX}/learning-outcomes`,
  stakeholderFeedback: `${API_PREFIX}/stakeholder-feedback`,
  surveyQualityMetadata: `${API_PREFIX}/stakeholder-feedback`,
  committee: `${API_PREFIX}/committee`,
  externalReview: `${API_PREFIX}/external-review`,
  expertResponsePlans: `${API_PREFIX}/expert-response-plans`,
  gapAnalysis: `${API_PREFIX}/gap-analysis`,
  calendar: `${API_PREFIX}/calendar`,
  riskRegister: `${API_PREFIX}/risk-register`,
  bridges: `${API_PREFIX}/bridges`,
  brainSignals: `${API_PREFIX}/brain-signals`,
  audit: `${API_PREFIX}/audit`,
  statusHistory: `${API_PREFIX}/status-history`,
} as const;

export const QUALITY_ACCREDITATION_PAGE_TITLES = {
  runtimeShell: 'Runtime Shell',
  accreditationRegistry: 'Accreditation Registry',
  accreditationEvidence: 'Accreditation Evidence Runtime',
  correctiveActions: 'Corrective Action Runtime',
  overview: 'Quality / Accreditation Suite',
  dashboard: 'Dashboard',
  standards: 'Standards and Frameworks',
  evidence: 'Evidence Registry',
  programReadiness: 'Program Readiness',
  institutionalReadiness: 'Institutional Readiness',
  selfAssessment: 'Self Assessment Runtime',
  improvementPlanRuntime: 'Improvement Plan Runtime',
  auditFindingsRuntime: 'Audit Findings Runtime',
  readinessMonitoringRuntime: 'Readiness Monitoring Runtime',
  improvementPlans: 'Improvement Plans',
  internalAudits: 'Internal Audits',
  programReview: 'Program Review',
  learningOutcomes: 'Learning Outcomes',
  stakeholderFeedback: 'Stakeholder Feedback',
  committee: 'Committee Workflow',
  externalReview: 'External Review',
  gapAnalysis: 'Gap Analysis',
  calendar: 'Accreditation Calendar',
  riskRegister: 'Risk Register',
  bridges: 'Bridges and Brain Signals',
  limitations: 'Limitations',
} as const;

export const QUALITY_ACCREDITATION_NAV_ITEMS = [
  { key: 'runtimeShell', title: 'Runtime Shell', href: QUALITY_ACCREDITATION_ROUTES.runtimeShell },
  { key: 'accreditationRegistry', title: 'Accreditation Registry', href: QUALITY_ACCREDITATION_ROUTES.accreditationRegistry },
  { key: 'accreditationEvidence', title: 'Accreditation Evidence Runtime', href: QUALITY_ACCREDITATION_ROUTES.accreditationEvidence },
  { key: 'correctiveActions', title: 'Corrective Action Runtime', href: QUALITY_ACCREDITATION_ROUTES.correctiveActions },
  { key: 'overview', title: 'Overview', href: QUALITY_ACCREDITATION_ROUTES.overview },
  { key: 'dashboard', title: 'Dashboard', href: QUALITY_ACCREDITATION_ROUTES.dashboard },
  { key: 'standards', title: 'Standards', href: QUALITY_ACCREDITATION_ROUTES.standards },
  { key: 'evidence', title: 'Evidence', href: QUALITY_ACCREDITATION_ROUTES.evidence },
  { key: 'programReadiness', title: 'Program Readiness', href: QUALITY_ACCREDITATION_ROUTES.programReadiness },
  { key: 'institutionalReadiness', title: 'Institutional Readiness', href: QUALITY_ACCREDITATION_ROUTES.institutionalReadiness },
  { key: 'selfAssessment', title: 'Self Assessment Runtime', href: QUALITY_ACCREDITATION_ROUTES.selfAssessment },
  { key: 'improvementPlanRuntime', title: 'Improvement Plan Runtime', href: QUALITY_ACCREDITATION_ROUTES.improvementPlanRuntime },
  { key: 'auditFindingsRuntime', title: 'Audit Findings Runtime', href: QUALITY_ACCREDITATION_ROUTES.auditFindingsRuntime },
  { key: 'readinessMonitoringRuntime', title: 'Readiness Monitoring Runtime', href: QUALITY_ACCREDITATION_ROUTES.readinessMonitoringRuntime },
  { key: 'improvementPlans', title: 'Improvement Plans', href: QUALITY_ACCREDITATION_ROUTES.improvementPlans },
  { key: 'internalAudits', title: 'Internal Audits', href: QUALITY_ACCREDITATION_ROUTES.internalAudits },
  { key: 'programReview', title: 'Program Review', href: QUALITY_ACCREDITATION_ROUTES.programReview },
  { key: 'learningOutcomes', title: 'Learning Outcomes', href: QUALITY_ACCREDITATION_ROUTES.learningOutcomes },
  { key: 'stakeholderFeedback', title: 'Stakeholder Feedback', href: QUALITY_ACCREDITATION_ROUTES.stakeholderFeedback },
  { key: 'committee', title: 'Committee', href: QUALITY_ACCREDITATION_ROUTES.committee },
  { key: 'externalReview', title: 'External Review', href: QUALITY_ACCREDITATION_ROUTES.externalReview },
  { key: 'gapAnalysis', title: 'Gap Analysis', href: QUALITY_ACCREDITATION_ROUTES.gapAnalysis },
  { key: 'calendar', title: 'Calendar', href: QUALITY_ACCREDITATION_ROUTES.calendar },
  { key: 'riskRegister', title: 'Risk Register', href: QUALITY_ACCREDITATION_ROUTES.riskRegister },
  { key: 'bridges', title: 'Bridges', href: QUALITY_ACCREDITATION_ROUTES.bridges },
  { key: 'limitations', title: 'Limitations', href: QUALITY_ACCREDITATION_ROUTES.limitations },
] as const;

export const QUALITY_ACCREDITATION_FORBIDDEN_ACTIONS = [
  'official_accreditation_approval',
  'automatic_accreditation_decision',
  'official_ministry_submission',
  'official_ranking_improvement_claim',
  'fake_accreditation_evidence',
  'fake_quality_score',
  'fake_survey_results',
  'hidden_program_score',
  'hidden_faculty_score',
  'hidden_student_score',
  'autonomous_quality_sanction',
  'automatic_program_closure',
  'provider_sync_without_provider',
  'external_database_sync',
  'production_ready_claim',
  'sales_ready_claim',
  'gcc_ready_claim',
  'l5_l6_claim',
] as const;

export const QUALITY_ACCREDITATION_LIMITATIONS = [
  'Frontend runtime is not production-ready.',
  'Provider integrations are not implemented.',
  'Official accreditation approval is not implemented.',
  'Official ministry submission is not implemented.',
  'Official ranking improvement claims are not implemented.',
  'Full Quality / Accreditation vertical closure remains pending.',
  'No L5 or L6 claim is made in this runtime.',
] as const;

export const QUALITY_ACCREDITATION_BRIDGE_TARGETS = [
  { key: 'executive_governance', title: 'Executive Governance', description: 'Read-only governance readiness bridge.' },
  { key: 'student_lifecycle', title: 'Student Lifecycle', description: 'Read-only student evidence context bridge.' },
  { key: 'academic_operations', title: 'Academic Operations', description: 'Read-only curriculum and delivery bridge.' },
  { key: 'research_science', title: 'Research / Science', description: 'Read-only research evidence bridge.' },
  { key: 'document_workflow', title: 'Document Workflow', description: 'Read-only document reference bridge.' },
  { key: 'future_hr', title: 'Future HR', description: 'Deferred staff-readiness bridge only.' },
  { key: 'future_finance', title: 'Future Finance', description: 'Deferred finance-readiness bridge only.' },
] as const;

export const QUALITY_ACCREDITATION_DASHBOARD_SECTIONS = [
  'frameworks_summary',
  'standards_summary',
  'evidence_summary',
  'readiness_summary',
  'self_assessment_summary',
  'improvement_summary',
  'audit_summary',
  'program_review_summary',
  'bridge_summary',
  'brain_signal_summary',
  'boundary_summary',
] as const;

export { QUALITY_ACCREDITATION_BOUNDARY_COPY, QUALITY_ACCREDITATION_BOUNDARY_LABELS };