import {
  RESEARCH_SCIENCE_BOUNDARY_COPY,
  RESEARCH_SCIENCE_BOUNDARY_LABELS,
} from './boundaryLabels';

export const MODULE_NAME = 'research-science';
export const API_PREFIX = '/api/admin/research-science';
export const UI_BASE_PATH = '/console/research-science';

export const RESEARCH_SCIENCE_BACKEND_ROUTE_COUNT = 43;
export const RESEARCH_SCIENCE_BACKEND_PERMISSION_COUNT = 40;
export const RESEARCH_SCIENCE_TABLE_COUNT = 15;
export const MASTER_MATRIX_COMMIT = 'c79cc31';
export const MASTER_MATRIX_ROW_COUNT = 467;
export const SOURCE_BACKEND_RUNTIME_COMMIT = 'a149c36';
export const SOURCE_BACKEND_B1_R1_COMMIT = 'da12c7d';
export const SOURCE_FRONTEND_SPEC_COMMIT = '0d85d8b';
export const RUNTIME_MODE = 'METADATA_EVIDENCE_ONLY';
export const EXPECTED_DATA_SOURCE = 'computed_from_research_science_metadata';

export const RESEARCH_SCIENCE_ROUTES = {
  overview: UI_BASE_PATH,
  dashboard: `${UI_BASE_PATH}/dashboard`,
  projects: `${UI_BASE_PATH}/projects`,
  studentResearch: `${UI_BASE_PATH}/student-research`,
  supervision: `${UI_BASE_PATH}/supervision`,
  publications: `${UI_BASE_PATH}/publications`,
  conferences: `${UI_BASE_PATH}/conferences`,
  grants: `${UI_BASE_PATH}/grants`,
  ethics: `${UI_BASE_PATH}/ethics`,
  evidence: `${UI_BASE_PATH}/evidence`,
  audit: `${UI_BASE_PATH}/audit`,
  bridges: `${UI_BASE_PATH}/bridges`,
  limitations: `${UI_BASE_PATH}/limitations`,
} as const;

export const RESEARCH_SCIENCE_API_PATHS = {
  health: `${API_PREFIX}/health`,
  dashboard: `${API_PREFIX}/dashboard`,
  matrixSummary: `${API_PREFIX}/matrix-summary`,
  limitations: `${API_PREFIX}/limitations`,
  projects: `${API_PREFIX}/projects`,
  studentResearch: `${API_PREFIX}/student-research`,
  supervision: `${API_PREFIX}/supervision`,
  publications: `${API_PREFIX}/publications`,
  conferences: `${API_PREFIX}/conferences`,
  grants: `${API_PREFIX}/grants`,
  grantDeliverables: `${API_PREFIX}/grant-deliverables`,
  ethics: `${API_PREFIX}/ethics`,
  ethicsAmendments: `${API_PREFIX}/ethics-amendments`,
  evidence: `${API_PREFIX}/evidence`,
  audit: `${API_PREFIX}/audit`,
  bridges: `${API_PREFIX}/bridges`,
  bridgesSummary: `${API_PREFIX}/bridges/summary`,
} as const;

export const RESEARCH_SCIENCE_PAGE_TITLES = {
  overview: 'Research / Science Suite',
  dashboard: 'Dashboard',
  projects: 'Research Projects',
  studentResearch: 'Student Research Work',
  supervision: 'Scientific Supervision',
  publications: 'Publication Registry',
  conferences: 'Conference Participation',
  grants: 'Grant Applications and Deliverables',
  ethics: 'Research Ethics',
  evidence: 'Evidence Metadata',
  audit: 'Audit and Status History',
  bridges: 'Bridge Summaries',
  limitations: 'Limitations',
} as const;

export const RESEARCH_SCIENCE_NAV_ITEMS = [
  { key: 'overview', title: 'Overview', href: RESEARCH_SCIENCE_ROUTES.overview },
  { key: 'dashboard', title: 'Dashboard', href: RESEARCH_SCIENCE_ROUTES.dashboard },
  { key: 'projects', title: 'Projects', href: RESEARCH_SCIENCE_ROUTES.projects },
  { key: 'studentResearch', title: 'Student Research', href: RESEARCH_SCIENCE_ROUTES.studentResearch },
  { key: 'supervision', title: 'Supervision', href: RESEARCH_SCIENCE_ROUTES.supervision },
  { key: 'publications', title: 'Publications', href: RESEARCH_SCIENCE_ROUTES.publications },
  { key: 'conferences', title: 'Conferences', href: RESEARCH_SCIENCE_ROUTES.conferences },
  { key: 'grants', title: 'Grants', href: RESEARCH_SCIENCE_ROUTES.grants },
  { key: 'ethics', title: 'Ethics', href: RESEARCH_SCIENCE_ROUTES.ethics },
  { key: 'evidence', title: 'Evidence', href: RESEARCH_SCIENCE_ROUTES.evidence },
  { key: 'audit', title: 'Audit', href: RESEARCH_SCIENCE_ROUTES.audit },
  { key: 'bridges', title: 'Bridges', href: RESEARCH_SCIENCE_ROUTES.bridges },
  { key: 'limitations', title: 'Limitations', href: RESEARCH_SCIENCE_ROUTES.limitations },
] as const;

export const RESEARCH_SCIENCE_FORBIDDEN_ACTIONS = [
  'auto_approve_ethics',
  'auto_submit_grant',
  'auto_verify_publication',
  'sync_scopus',
  'sync_wos',
  'sync_orcid',
  'sync_ministry',
  'sync_provider',
  'external_database_sync',
  'calculate_citation_score',
  'calculate_researcher_score',
  'generate_official_ranking',
  'create_fake_publication',
  'create_fake_certificate',
  'create_fake_grant_evidence',
  'hidden_score',
] as const;

export const RESEARCH_SCIENCE_LIMITATIONS = [
  'Frontend runtime is not production-ready.',
  'Provider, Scopus, WoS, ORCID, and ministry integrations are not implemented.',
  'Official publication verification is not implemented.',
  'Official grant submission is not implemented.',
  'Official ethics approval automation is not implemented.',
  'Full Research / Science vertical closure remains pending.',
  'No L5 or L6 claim is made in this runtime.',
] as const;

export const RESEARCH_SCIENCE_BRIDGE_TARGETS = [
  { key: 'executive_governance', title: 'Executive Governance', description: 'Governance visibility only.' },
  { key: 'accreditation', title: 'Accreditation', description: 'Accreditation readiness metadata only.' },
  { key: 'student_lifecycle', title: 'Student Lifecycle', description: 'Read-only student research context bridge.' },
  { key: 'academic_operations', title: 'Academic Operations', description: 'Curriculum and scheduling references only.' },
  { key: 'library_repository', title: 'Library / Repository', description: 'Repository linkage readiness only.' },
  { key: 'document_workflow', title: 'Document Workflow', description: 'Document references only.' },
  { key: 'finance_procurement', title: 'Finance / Procurement', description: 'Grant cost and purchase references only.' },
  { key: 'integration_provider', title: 'Integration / Provider Readiness', description: 'Readiness only. No provider sync.' },
] as const;

export const RESEARCH_SCIENCE_DASHBOARD_SECTIONS = [
  'projects_summary',
  'student_research_summary',
  'supervision_summary',
  'publications_summary',
  'conferences_summary',
  'grants_summary',
  'ethics_summary',
  'evidence_summary',
  'bridge_summary',
  'brain_readiness_summary',
  'boundary_summary',
] as const;

export { RESEARCH_SCIENCE_BOUNDARY_COPY, RESEARCH_SCIENCE_BOUNDARY_LABELS };