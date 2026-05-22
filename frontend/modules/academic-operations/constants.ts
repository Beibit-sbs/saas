import { ACADEMIC_OPERATIONS_BOUNDARY_COPY as ACADEMIC_OPERATIONS_BOUNDARY_LABEL_SET, ACADEMIC_OPERATIONS_BOUNDARY_LABELS } from './boundaryLabels';

export const MODULE_NAME = 'academic-operations';
export const API_BASE_PATH = '/api/admin/academic-operations';
export const UI_BASE_PATH = '/console/academic-operations';

export const MASTER_MATRIX_COMMIT = 'c79cc31';
export const MASTER_MATRIX_ROW_COUNT = 467;
export const ACADEMIC_OPERATIONS_BACKEND_ROUTE_COUNT = 40;
export const ACADEMIC_OPERATIONS_BACKEND_PERMISSION_COUNT = 40;

export const EXPECTED_DATA_SOURCE = 'computed_from_academic_operations_metadata';

export const ACADEMIC_OPERATIONS_ROUTES = {
  overview: UI_BASE_PATH,
  dashboard: `${UI_BASE_PATH}/dashboard`,
  matrix: `${UI_BASE_PATH}/matrix`,
  academicGroups: `${UI_BASE_PATH}/academic-groups`,
  cohorts: `${UI_BASE_PATH}/cohorts`,
  courseRegistration: `${UI_BASE_PATH}/course-registration`,
  gradebookMetadata: `${UI_BASE_PATH}/gradebook-metadata`,
  retakes: `${UI_BASE_PATH}/retakes`,
  summerSemesters: `${UI_BASE_PATH}/summer-semesters`,
  advisorTutor: `${UI_BASE_PATH}/advisor-tutor`,
  bridges: `${UI_BASE_PATH}/bridges`,
  auditEvidence: `${UI_BASE_PATH}/audit-evidence`,
  limitations: `${UI_BASE_PATH}/limitations`,
} as const;

export const ACADEMIC_OPERATIONS_API_PATHS = {
  health: `${API_BASE_PATH}/health`,
  dashboard: `${API_BASE_PATH}/dashboard`,
  matrixSummary: `${API_BASE_PATH}/matrix-summary`,
  canonicalReuseSummary: `${API_BASE_PATH}/canonical-reuse-summary`,
  academicGroups: `${API_BASE_PATH}/academic-groups`,
  cohorts: `${API_BASE_PATH}/cohorts`,
  courseRegistration: `${API_BASE_PATH}/course-registration`,
  gradebookMetadata: `${API_BASE_PATH}/gradebook-metadata`,
  retakes: `${API_BASE_PATH}/retakes`,
  summerSemesters: `${API_BASE_PATH}/summer-semesters`,
  advisorTutor: `${API_BASE_PATH}/advisor-tutor`,
  bridges: `${API_BASE_PATH}/bridges`,
  bridgeCanonical: `${API_BASE_PATH}/bridges/canonical`,
  bridgeStudentLifecycle: `${API_BASE_PATH}/bridges/student-lifecycle`,
  bridgeDocumentWorkflow: `${API_BASE_PATH}/bridges/document-workflow`,
  bridgeExecutiveGovernance: `${API_BASE_PATH}/bridges/executive-governance`,
  bridgeQualityAccreditation: `${API_BASE_PATH}/bridges/quality-accreditation`,
  audit: `${API_BASE_PATH}/audit`,
  evidence: `${API_BASE_PATH}/evidence`,
} as const;

export const ACADEMIC_OPERATIONS_PAGE_TITLES = {
  overview: 'Academic Operations Suite',
  dashboard: 'Dashboard',
  matrix: 'Matrix Summary',
  academicGroups: 'Academic Groups',
  cohorts: 'Cohorts',
  courseRegistration: 'Course Registration Metadata',
  gradebookMetadata: 'Gradebook Metadata',
  retakes: 'Retake Plans',
  summerSemesters: 'Summer Semester Terms',
  advisorTutor: 'Advisor / Tutor Assignments',
  bridges: 'Canonical Bridges',
  auditEvidence: 'Audit / Evidence',
  limitations: 'Limitations',
} as const;

export const ACADEMIC_OPERATIONS_NAV_ITEMS = [
  { key: 'overview', title: 'Overview', href: ACADEMIC_OPERATIONS_ROUTES.overview },
  { key: 'dashboard', title: 'Dashboard', href: ACADEMIC_OPERATIONS_ROUTES.dashboard },
  { key: 'matrix', title: 'Matrix', href: ACADEMIC_OPERATIONS_ROUTES.matrix },
  { key: 'academicGroups', title: 'Academic Groups', href: ACADEMIC_OPERATIONS_ROUTES.academicGroups },
  { key: 'cohorts', title: 'Cohorts', href: ACADEMIC_OPERATIONS_ROUTES.cohorts },
  { key: 'courseRegistration', title: 'Course Registration', href: ACADEMIC_OPERATIONS_ROUTES.courseRegistration },
  { key: 'gradebookMetadata', title: 'Gradebook Metadata', href: ACADEMIC_OPERATIONS_ROUTES.gradebookMetadata },
  { key: 'retakes', title: 'Retakes', href: ACADEMIC_OPERATIONS_ROUTES.retakes },
  { key: 'summerSemesters', title: 'Summer Semesters', href: ACADEMIC_OPERATIONS_ROUTES.summerSemesters },
  { key: 'advisorTutor', title: 'Advisor / Tutor', href: ACADEMIC_OPERATIONS_ROUTES.advisorTutor },
  { key: 'bridges', title: 'Bridges', href: ACADEMIC_OPERATIONS_ROUTES.bridges },
  { key: 'auditEvidence', title: 'Audit / Evidence', href: ACADEMIC_OPERATIONS_ROUTES.auditEvidence },
  { key: 'limitations', title: 'Limitations', href: ACADEMIC_OPERATIONS_ROUTES.limitations },
] as const;

export const ACADEMIC_OPERATIONS_LIMITATIONS = [
  'Frontend runtime is not production-ready.',
  'Provider, Platonus, and SIS integrations are not implemented.',
  'Official grade publication is not implemented.',
  'Official transcript update is not implemented.',
  'Full 467-row runtime is not implemented.',
  'Optional detail routes remain deferred.',
  'Complex create and update forms remain hidden or disabled in the first runtime.',
] as const;

export const ACADEMIC_OPERATIONS_CANONICAL_REUSE_MAP = {
  course_catalog: 'course_catalog_management',
  elective_course_selection: 'existing canonical',
  academic_committee_decisions: 'committee_decision_registry',
  student_lifecycle: 'student_lifecycle',
  document_workflow: 'document_workflow_os',
  executive_governance: 'executive_governance',
  quality_accreditation: 'quality_accreditation',
} as const;

export const ACADEMIC_OPERATIONS_BRIDGE_MAP = {
  studentLifecycle: 'academic_operations_to_student_lifecycle_bridge',
  documentWorkflow: 'academic_operations_to_document_workflow_bridge',
  executiveGovernance: 'academic_operations_to_executive_governance_bridge',
  qualityAccreditation: 'academic_operations_to_quality_accreditation_bridge',
} as const;

export const ACADEMIC_OPERATIONS_FORBIDDEN_UI_ACTIONS = [
  'delete',
  'publish official grade',
  'calculate official grade',
  'approve grade',
  'sanction student',
  'dismiss student',
  'sync with Platonus',
  'sync with SIS',
  'provider dispatch',
  'generate official transcript',
  'generate official order/decree',
  'hidden scoring',
] as const;

export const ACADEMIC_OPERATIONS_DEFAULT_LIMITATIONS = [
  ACADEMIC_OPERATIONS_BOUNDARY_LABELS.metadataOnlyFoundation,
  ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noOfficialGradePublication,
  ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noAutomatedGrading,
  ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noHiddenScore,
  ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noProviderSync,
] as const;