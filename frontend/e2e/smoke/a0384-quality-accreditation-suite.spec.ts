import { expect, test, type Page } from '@playwright/test';

const API_BASE = '/api/bff/admin/quality-accreditation';
const BASE_URL = process.env.E2E_BASE_URL ?? 'https://nginx';

const FULL_PERMISSIONS = [
  'platform.admin.read',
  'quality_accreditation.overview.read',
  'quality_accreditation.dashboard.read',
  'quality_accreditation.health.read',
  'quality_accreditation.matrix.read',
  'quality_accreditation.limitations.read',
  'quality_accreditation.standards.read',
  'quality_accreditation.criteria.read',
  'quality_accreditation.evidence.read',
  'quality_accreditation.program_readiness.read',
  'quality_accreditation.institutional_readiness.read',
  'quality_accreditation.self_assessment.read',
  'quality_accreditation.improvement_plans.read',
  'quality_accreditation.internal_audits.read',
  'quality_accreditation.audit_findings.read',
  'quality_accreditation.program_review.read',
  'quality_accreditation.learning_outcomes.read',
  'quality_accreditation.feedback.read',
  'quality_accreditation.committee.read',
  'quality_accreditation.external_review.read',
  'quality_accreditation.gap_analysis.read',
  'quality_accreditation.calendar.read',
  'quality_accreditation.risk_register.read',
  'quality_accreditation.bridges.read',
  'quality_accreditation.brain_signals.read',
  'quality_accreditation.audit.read',
  'quality_accreditation.status_history.read',
  'quality_accreditation.admin.read',
] as const;

const REQUIRED_BOUNDARY_TEXTS = [
  'Metadata/evidence-only quality foundation',
  'Accreditation readiness, not accreditation approval',
  'Evidence metadata only',
  'Human review required',
  'No official accreditation approval',
  'No official ministry submission',
  'No official ranking claim',
  'No automatic accreditation decision',
  'No fake accreditation evidence',
  'No fake quality score',
  'No fake survey results',
  'No hidden program score',
  'No hidden faculty score',
  'No hidden student score',
  'No provider sync',
  'No external database sync',
  'fake_metrics=false',
  'fake_evidence=false',
  'incomplete_data supported',
  'Read-only-first bridge',
] as const;

const FORBIDDEN_ACTIONS = [
  'Official accreditation approved',
  'Submit to ministry',
  'Ministry submitted',
  'Official ranking improved',
  'Auto approve accreditation',
  'Automatic accreditation decision completed',
  'Create fake accreditation evidence',
  'Create fake quality score',
  'Create fake survey result',
  'Sync provider',
  'Auto close program',
  'Autonomous quality sanction',
] as const;

const FORBIDDEN_EXACT_TEXTS = [
  /^Production-ready$/i,
  /^Sales-ready$/i,
  /^GCC-ready$/i,
  /^L5 ready$/i,
  /^L6 ready$/i,
  /^Official ranking improved$/i,
] as const;

const BASE_FLAGS = {
  human_review_required: true,
  fake_metrics: false,
  fake_evidence: false,
  official_accreditation_approval_enabled: false,
  official_ministry_submission_enabled: false,
  official_ranking_claim_enabled: false,
  automatic_accreditation_decision_enabled: false,
  provider_integration_enabled: false,
  external_database_sync_enabled: false,
  hidden_score_present: false,
  autonomous_decision: false,
  incomplete_data: true,
  limitations: ['Metadata/evidence-only quality foundation'],
  source_capability_id: 'QA-CAP-001',
  source_family_id: 'QA-FAM-001',
} as const;

function makeEntity(id: number, referenceKey: string, referenceValue: string, title: string, description: string, extra: Record<string, unknown> = {}) {
  return {
    id,
    tenant_id: 1,
    status: 'ACTIVE',
    metadata: extra,
    created_at: '2026-05-26T00:00:00Z',
    updated_at: '2026-05-26T00:00:00Z',
    archived_at: null,
    title,
    description,
    notes: description,
    read_only_first: true,
    mutation_allowed: false,
    ...BASE_FLAGS,
    [referenceKey]: referenceValue,
  };
}

const OVERVIEW_FIXTURE = {
  tenant_id: 1,
  module: 'quality_accreditation',
  product_vertical: 'Quality / Accreditation Suite',
  contract_version: 'A-038.4-E2E',
  runtime_mode: 'METADATA_EVIDENCE_ONLY',
  table_count: 32,
  route_count: 70,
  readiness_items: 5,
  evidence_items: 6,
  bridge_items: 7,
  limitations: ['Accreditation readiness, not accreditation approval'],
  boundary_summary: {
    fake_metrics: false,
    fake_evidence: false,
    no_official_approval: true,
    no_official_ministry_submission: true,
    no_official_ranking_claim: true,
  },
};

const HEALTH_FIXTURE = {
  tenant_id: 1,
  module: 'quality_accreditation',
  target_level: 'L4',
  foundation_status: 'IMPLEMENTED_RUNTIME',
  runtime_mode: 'METADATA_EVIDENCE_ONLY',
  contract_version: 'A-038.4-E2E',
  provider_integration_enabled: false,
  external_database_sync_enabled: false,
  official_accreditation_approval_enabled: false,
  official_ministry_submission_enabled: false,
  official_ranking_claim_enabled: false,
  hidden_score_present: false,
  fake_metrics: false,
  incomplete_data: true,
  limitations: ['Metadata/evidence-only quality foundation'],
  route_count: 70,
  table_count: 32,
};

const DASHBOARD_FIXTURE = {
  tenant_id: 1,
  generated_at: '2026-05-26T00:00:00Z',
  contract_version: 'A-038.4-E2E',
  source_spec_commit: 'ad2cad9',
  source_product_map_commit: '1253e19',
  source_vertical_selection_commit: '7da0c70',
  master_matrix_commit: 'ad2cad9',
  master_matrix_rows: 44,
  detailed_capability_count: 44,
  capability_family_count: 10,
  data_source: 'computed_from_quality_accreditation_metadata',
  frameworks_summary: { frameworks: 1, standards: 2 },
  standards_summary: { criteria: 2, evidence_requirements: 2 },
  evidence_summary: { evidence_records: 1, limitations: 1 },
  readiness_summary: { program: 1, institutional: 1 },
  self_assessment_summary: { reports: 1, sections: 1 },
  improvement_summary: { plans: 1, actions: 1 },
  audit_summary: { audits: 1, findings: 1 },
  program_review_summary: { cycles: 1, outcomes: 1 },
  bridge_summary: { bridge_records: 1, bridge_targets: 5 },
  brain_signal_summary: { signals: 1 },
  boundary_summary: { fake_metrics: false, fake_evidence: false },
  ...BASE_FLAGS,
};

const MATRIX_SUMMARY_FIXTURE = {
  contract_version: 'A-038.4-E2E',
  source_spec_commit: 'ad2cad9',
  source_product_map_commit: '1253e19',
  source_vertical_selection_commit: '7da0c70',
  master_matrix_commit: 'ad2cad9',
  master_matrix_rows: 44,
  detailed_capability_count: 44,
  capability_family_count: 10,
  runtime_mode: 'METADATA_EVIDENCE_ONLY',
  route_count_expected: '55-70',
  table_count_expected: 32,
  permission_count_expected: 55,
};

const LIMITATIONS_FIXTURE = {
  items: [
    'Provider integrations not implemented.',
    'Official approval/submission/ranking not implemented.',
    'Full Quality / Accreditation vertical not closed.',
    'No L5/L6 claim.',
  ],
};

const FRAMEWORKS_FIXTURE = {
  items: [makeEntity(1, 'framework_ref', 'QF-2026', 'Institutional framework', 'Framework metadata for internal readiness only.', { criteria: 'Framework / criteria / evidence requirements' })],
};

const STANDARDS_FIXTURE = {
  items: [makeEntity(2, 'standard_ref', 'STD-1', 'Accreditation Standard 1', 'Internal readiness metadata only. No official compliance approval claim.', { framework: 'National framework' })],
};

const CRITERIA_FIXTURE = {
  items: [makeEntity(3, 'criterion_ref', 'CRIT-1', 'Criterion 1', 'Criteria and evidence requirements for internal review.', { requirements: 'Evidence requirements visible' })],
};

const REQUIREMENTS_FIXTURE = {
  items: [makeEntity(4, 'requirement_ref', 'REQ-1', 'Evidence requirement', 'Evidence requirement metadata only.', { requirement_type: 'Evidence metadata only' })],
};

const EVIDENCE_FIXTURE = {
  items: [makeEntity(5, 'evidence_ref', 'EVD-1', 'Evidence registry item', 'Evidence metadata only. No fake accreditation evidence.', { review: 'Evidence review', limitations: 'Evidence limitations' })],
};

const EVIDENCE_LIMITATIONS_FIXTURE = {
  items: [makeEntity(6, 'limitation_ref', 'LIM-1', 'Evidence limitation', 'Evidence limitations visible for internal review.', { limitation_text: 'Evidence limitations visible' })],
};

const PROGRAM_READINESS_FIXTURE = {
  items: [makeEntity(7, 'readiness_ref', 'PR-1', 'Program readiness item', 'Missing evidence and gap context for accreditation readiness only.', { program_ref: 'PRG-1', gap: 'Missing evidence gap context' })],
};

const INSTITUTIONAL_READINESS_FIXTURE = {
  items: [makeEntity(8, 'readiness_ref', 'IR-1', 'Institutional readiness item', 'Governance, student, academic, research, and document evidence context.', { governance: 'governance', student: 'student', academic: 'academic', research: 'research', document: 'document' })],
};

const SELF_ASSESSMENT_FIXTURE = {
  items: [makeEntity(9, 'report_ref', 'SAR-1', 'Self-assessment draft', 'Draft internal review report with owners and review statuses.', { owner_ref: 'QA-OWNER-1', review_status: 'INTERNAL_REVIEW' })],
};

const SELF_ASSESSMENT_SECTIONS_FIXTURE = {
  items: [makeEntity(10, 'section_ref', 'SEC-1', 'Self-assessment section', 'Report sections, owners, and review statuses.', { owner: 'Owner A', review_status: 'DRAFT' })],
};

const IMPROVEMENT_PLANS_FIXTURE = {
  items: [makeEntity(11, 'plan_ref', 'PLAN-1', 'Improvement plan', 'Actions, owners, deadlines, and status tracking only.', { owner_ref: 'QA-OWNER-2', deadline: '2026-09-01', status: 'OPEN' })],
};

const IMPROVEMENT_ACTIONS_FIXTURE = {
  items: [makeEntity(12, 'action_ref', 'ACT-1', 'Improvement action', 'Human-owned action only. No autonomous sanctions.', { deadline: '2026-09-15', status: 'IN_PROGRESS' })],
};

const INTERNAL_AUDITS_FIXTURE = {
  items: [makeEntity(13, 'audit_ref', 'AUD-1', 'Internal audit', 'Audit plans and internal review metadata only.', { findings: 'Audit plans / findings / corrective actions' })],
};

const AUDIT_FINDINGS_FIXTURE = {
  items: [makeEntity(14, 'finding_ref', 'FND-1', 'Audit finding', 'Corrective actions visible for human review artifacts.', { corrective_action: 'Corrective actions' })],
};

const AUDIT_EVENTS_FIXTURE = {
  items: [makeEntity(15, 'source_entity_ref', 'EVT-1', 'Audit event', 'Human-review artifact only.', { event_type: 'AUDIT_PLAN_CREATED' })],
};

const STATUS_HISTORY_FIXTURE = {
  items: [makeEntity(16, 'source_entity_ref', 'STS-1', 'Status history', 'Append-only status transitions for human review.', { status_from: 'DRAFT', status_to: 'REVIEW' })],
};

const PROGRAM_REVIEW_FIXTURE = {
  items: [makeEntity(17, 'cycle_ref', 'REV-1', 'Program review cycle', 'Review cycle, outcomes, and feedback evidence linkage only.', { outcomes: 'Review cycle / outcomes / feedback evidence' })],
};

const LEARNING_OUTCOMES_FIXTURE = {
  items: [makeEntity(18, 'assessment_ref', 'LO-1', 'Learning outcomes assessment', 'Outcome evidence and assessment cycle metadata only.', { cycle: 'Assessment cycle metadata' })],
};

const STAKEHOLDER_FEEDBACK_FIXTURE = {
  items: [makeEntity(19, 'feedback_ref', 'FB-1', 'Stakeholder feedback metadata', 'Survey metadata only. No fake survey results.', { survey: 'Survey metadata' })],
};

const COMMITTEE_FIXTURE = {
  items: [makeEntity(20, 'workflow_ref', 'COM-1', 'Committee workflow', 'Human decision context only. No automatic accreditation approval.', { committee_ref: 'QA-COMMITTEE', decision_context: 'Human decision context' })],
};

const EXTERNAL_REVIEW_FIXTURE = {
  items: [makeEntity(21, 'review_ref', 'ER-1', 'External expert review', 'External expert review metadata, recommendations, and response plans.', { expert: 'External expert review', recommendations: 'Recommendations / response plans' })],
};

const EXPERT_RESPONSE_PLANS_FIXTURE = {
  items: [makeEntity(22, 'response_plan_ref', 'RP-1', 'Response plan', 'Recommendations and response plans only.', { response: 'Response plan' })],
};

const GAP_ANALYSIS_FIXTURE = {
  items: [makeEntity(23, 'gap_ref', 'GAP-1', 'Gap analysis item', 'Risk band and missing evidence metadata for human review required.', { risk_band: 'AMBER', missing_evidence: 'Missing evidence' })],
};

const CALENDAR_FIXTURE = {
  items: [makeEntity(24, 'calendar_ref', 'CAL-1', 'Accreditation calendar', 'Milestones and responsible units only.', { milestone: 'Milestones', owner_ref: 'Unit A' })],
};

const RISK_REGISTER_FIXTURE = {
  items: [makeEntity(25, 'risk_ref', 'RISK-1', 'Risk register item', 'Quality and accreditation risks, mitigation, and owners.', { mitigation: 'Mitigation', owner_ref: 'Risk Owner' })],
};

const BRIDGES_FIXTURE = {
  items: [makeEntity(26, 'bridge_ref', 'BR-1', 'Quality bridge metadata', 'Read-only-first bridge metadata without provider sync.', { targets: 'Executive Governance / Student Lifecycle / Academic Operations / Research / Science / Document Workflow' })],
};

const BRAIN_SIGNALS_FIXTURE = {
  items: [makeEntity(27, 'signal_ref', 'SIG-1', 'Quality brain signal', 'Brain-signal metadata only. Human review required.', { signal_type: 'READINESS' })],
};

const ROUTES = [
  {
    path: '/console/quality-accreditation',
    heading: 'Quality / Accreditation Suite',
    boundary: 'Metadata/evidence-only quality foundation',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('quality-accreditation-overview')).toContainText('32');
      await expect(page.getByTestId('quality-accreditation-overview')).toContainText('70');
      await expect(page.getByTestId('quality-accreditation-overview')).toContainText('55');
      await expect(page.getByTestId('quality-accreditation-overview')).toContainText('fb2734c');
      await expect(page.getByTestId('quality-accreditation-overview')).toContainText('computed_from_quality_accreditation_metadata');
      await expect(page.locator('body')).toContainText('Accreditation readiness, not accreditation approval');
    },
  },
  {
    path: '/console/quality-accreditation/dashboard',
    heading: 'Dashboard',
    boundary: 'fake_metrics=false. Data source: computed_from_quality_accreditation_metadata. Readiness is metadata-only and requires human review.',
    assertions: async (page: Page) => {
      const dashboard = page.getByTestId('quality-accreditation-dashboard');
      await expect(dashboard).toContainText('fake_metrics');
      await expect(dashboard).toContainText('computed_from_quality_accreditation_metadata');
      await expect(dashboard).toContainText('Bridge coverage summary');
      await expect(dashboard).toContainText('Readiness summary');
      await expect(dashboard).toContainText('Evidence completeness summary');
      await expect(page.locator('body')).toContainText('incomplete_data supported');
    },
  },
  {
    path: '/console/quality-accreditation/standards',
    heading: 'Standards and Frameworks',
    boundary: 'Standards mapping is internal readiness metadata only. It does not approve accreditation or confirm official compliance.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('quality-frameworks-panel')).toContainText('Institutional framework');
      await expect(page.getByTestId('accreditation-standards-panel')).toContainText('Accreditation Standard 1');
      await expect(page.getByTestId('standard-criteria-panel')).toContainText('Criterion 1');
      await expect(page.getByTestId('standards-evidence-requirements-panel')).toContainText('Evidence requirement');
    },
  },
  {
    path: '/console/quality-accreditation/evidence',
    heading: 'Evidence Registry',
    boundary: 'Evidence records are metadata-only unless reviewed by humans. No external/provider verification or official submission is claimed.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('quality-evidence-registry-panel')).toContainText('Evidence registry item');
      await expect(page.getByTestId('quality-evidence-registry-panel')).toContainText('Evidence metadata only');
      await expect(page.getByTestId('evidence-limitations-panel')).toContainText('Evidence limitation');
      await expect(page.locator('body')).toContainText('No fake accreditation evidence');
    },
  },
  {
    path: '/console/quality-accreditation/program-readiness',
    heading: 'Program Readiness',
    boundary: 'Program readiness is an internal review signal, not an official accreditation decision or hidden program score.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('program-readiness-panel')).toContainText('Program readiness item');
      await expect(page.getByTestId('program-readiness-panel')).toContainText('Missing evidence');
      await expect(page.locator('body')).toContainText('No hidden program score');
    },
  },
  {
    path: '/console/quality-accreditation/institutional-readiness',
    heading: 'Institutional Readiness',
    boundary: 'Institutional readiness is evidence-backed metadata for internal review. No official ministry submission is performed.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('institutional-readiness-panel')).toContainText('Institutional readiness item');
      await expect(page.getByTestId('institutional-readiness-panel')).toContainText(/governance/i);
      await expect(page.getByTestId('institutional-readiness-panel')).toContainText(/research/i);
      await expect(page.locator('body')).toContainText('No official ministry submission');
    },
  },
  {
    path: '/console/quality-accreditation/self-assessment',
    heading: 'Self-Assessment',
    boundary: 'Self-assessment reports are draft/internal review artifacts only. No official submission is performed.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('self-assessment-report-panel')).toContainText('Self-assessment draft');
      await expect(page.getByTestId('self-assessment-sections-panel')).toContainText('Self-assessment section');
      await expect(page.locator('body')).toContainText('Human review required');
      await expect(page.locator('body')).toContainText('No official ministry submission');
      await expect(page.locator('body')).not.toContainText(/official submission completed/i);
    },
  },
  {
    path: '/console/quality-accreditation/improvement-plans',
    heading: 'Improvement Plans',
    boundary: 'Improvement plans track human-owned actions. No autonomous sanction or automatic program closure is performed.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('quality-improvement-plans-panel')).toContainText('Improvement plan');
      await expect(page.getByTestId('quality-improvement-actions-panel')).toContainText('Improvement action');
      await expect(page.locator('body')).toContainText('deadlines');
    },
  },
  {
    path: '/console/quality-accreditation/internal-audits',
    heading: 'Internal Audits',
    boundary: 'Internal quality audit records are human-review artifacts. No automatic penalty or hidden score is created.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('internal-quality-audits-panel')).toContainText('Internal audit');
      await expect(page.getByTestId('quality-audit-findings-panel')).toContainText('Audit finding');
      await expect(page.getByTestId('quality-audit-panel')).toContainText('Audit event');
      await expect(page.getByTestId('quality-status-history-panel')).toContainText('Status history');
    },
  },
  {
    path: '/console/quality-accreditation/program-review',
    heading: 'Program Review',
    boundary: 'Program review remains metadata-only. No automatic program closure or official accreditation approval is performed.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('program-review-cycle-panel')).toContainText('Program review cycle');
      await expect(page.getByTestId('program-review-cycle-panel')).toContainText('feedback evidence');
      await expect(page.locator('body')).not.toContainText(/automatic program closure completed/i);
    },
  },
  {
    path: '/console/quality-accreditation/learning-outcomes',
    heading: 'Learning Outcomes',
    boundary: 'Learning outcomes evidence remains metadata-only. No automatic grading or hidden scoring is performed.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('learning-outcomes-assessment-panel')).toContainText('Learning outcomes assessment');
      await expect(page.getByTestId('learning-outcomes-assessment-panel')).toContainText('Assessment cycle metadata');
      await expect(page.locator('body')).toContainText('No hidden program score');
      await expect(page.locator('body')).toContainText('Human review required');
    },
  },
  {
    path: '/console/quality-accreditation/stakeholder-feedback',
    heading: 'Stakeholder Feedback',
    boundary: 'Feedback metadata does not create fake survey results or hidden student/faculty/program scores.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('stakeholder-feedback-panel')).toContainText('Stakeholder feedback metadata');
      await expect(page.getByTestId('survey-quality-metadata-panel')).toContainText('Survey metadata');
      await expect(page.locator('body')).toContainText('No fake survey results');
      await expect(page.locator('body')).toContainText('No hidden student score');
    },
  },
  {
    path: '/console/quality-accreditation/committee',
    heading: 'Committee Workflow',
    boundary: 'Committee workflow records human decisions only. No automatic accreditation approval is performed.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('accreditation-committee-workflow-panel')).toContainText('Committee workflow');
      await expect(page.getByTestId('accreditation-committee-workflow-panel')).toContainText('Human decision context');
      await expect(page.locator('body')).toContainText('No automatic accreditation decision');
    },
  },
  {
    path: '/console/quality-accreditation/external-review',
    heading: 'External Review',
    boundary: 'External review metadata does not claim fake expert approval or official external verification.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('external-expert-review-panel')).toContainText('External expert review');
      await expect(page.getByTestId('expert-response-plan-panel')).toContainText('Response plan');
      await expect(page.locator('body')).not.toContainText(/official external verification enabled/i);
    },
  },
  {
    path: '/console/quality-accreditation/gap-analysis',
    heading: 'Gap Analysis',
    boundary: 'Gap analysis is deterministic metadata for human review. It is not a hidden quality score.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('compliance-gap-analysis-panel')).toContainText('Gap analysis item');
      await expect(page.getByTestId('compliance-gap-analysis-panel')).toContainText('Risk band');
      await expect(page.getByTestId('compliance-gap-analysis-panel')).toContainText('Missing evidence');
      await expect(page.locator('body')).toContainText('Human review required');
    },
  },
  {
    path: '/console/quality-accreditation/calendar',
    heading: 'Accreditation Calendar',
    boundary: 'Calendar items track internal milestones only. No official deadline submission or provider sync is performed.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('accreditation-calendar-panel')).toContainText('Accreditation calendar');
      await expect(page.getByTestId('accreditation-calendar-panel')).toContainText('Milestones');
      await expect(page.getByTestId('accreditation-calendar-panel')).toContainText('responsible units');
    },
  },
  {
    path: '/console/quality-accreditation/risk-register',
    heading: 'Risk Register',
    boundary: 'Risk register entries track human-owned mitigations only. No automated sanction or automatic closure is performed.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('quality-risk-register-panel')).toContainText('Risk register item');
      await expect(page.getByTestId('quality-risk-register-panel')).toContainText('Mitigation');
      await expect(page.getByTestId('quality-risk-register-panel')).toContainText('owners');
    },
  },
  {
    path: '/console/quality-accreditation/bridges',
    heading: 'Bridges and Brain Signals',
    boundary: 'Read-only-first bridge. No cross-suite mutation or provider sync is allowed by default.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('quality-bridge-panel')).toContainText('Quality bridge metadata');
      await expect(page.getByTestId('quality-brain-signals-panel')).toContainText('Quality brain signal');
      await expect(page.locator('body')).toContainText('Executive Governance');
      await expect(page.locator('body')).toContainText('Student Lifecycle');
      await expect(page.locator('body')).toContainText('Academic Operations');
      await expect(page.locator('body')).toContainText('Research / Science');
      await expect(page.locator('body')).toContainText('Document Workflow');
      await expect(page.locator('body')).toContainText('Read-only-first bridge');
      await expect(page.locator('body')).toContainText('No provider sync');
    },
  },
  {
    path: '/console/quality-accreditation/limitations',
    heading: 'Limitations',
    boundary: 'Frontend runtime is not production-ready. Provider integrations, official approval, ministry submission, ranking claims, and L5/L6 readiness are not implemented.',
    assertions: async (page: Page) => {
      const limitations = page.getByTestId('quality-accreditation-limitations-panel');
      await expect(limitations).toContainText('Provider integrations are not implemented.');
      await expect(limitations).toContainText('Official accreditation approval is not implemented.');
      await expect(limitations).toContainText('Official ministry submission is not implemented.');
      await expect(limitations).toContainText('Official ranking improvement claims are not implemented.');
      await expect(limitations).toContainText('Full Quality / Accreditation vertical closure remains pending.');
      await expect(limitations).toContainText('No L5 or L6 claim is made in this runtime.');
    },
  },
] as const;

if (ROUTES.length !== 19) {
  throw new Error(`Quality Accreditation route flow must stay at 19, received ${ROUTES.length}`);
}

function pageUrl(path: string) {
  return new URL(path, BASE_URL).toString();
}

async function forceEnglishLocale(page: Page) {
  const parsedUrl = new URL(BASE_URL);
  const cookieOrigins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  await page.context().addCookies(
    Array.from(cookieOrigins).map((url) => ({
      name: 'app.locale',
      value: 'en',
      url,
      httpOnly: false,
      secure: new URL(url).protocol === 'https:',
      sameSite: 'Lax' as const,
    })),
  );

  await page.addInitScript(() => {
    document.cookie = 'app.locale=en; Path=/; SameSite=Lax';
    window.localStorage.setItem('app.language', 'en');
  });
}

async function installFakeAdminAuth(page: Page, permissions: readonly string[] = FULL_PERMISSIONS) {
  const parsedUrl = new URL(BASE_URL);
  const cookieOrigins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  const payloadJson = JSON.stringify({
    sub: 'quality-accreditation-admin',
    exp: Math.floor(Date.now() / 1000) + 3600,
  });
  const payload = Buffer.from(payloadJson).toString('base64url');
  const fakeToken = `fakeheader.${payload}.fakesig`;

  await page.context().addCookies(
    Array.from(cookieOrigins).flatMap((url) => {
      const secure = new URL(url).protocol === 'https:';
      return [
        { name: 'admin_token', value: fakeToken, url, httpOnly: true, secure, sameSite: 'Lax' as const },
        { name: 'app_access_token', value: fakeToken, url, httpOnly: true, secure, sameSite: 'Lax' as const },
      ];
    }),
  );

  for (const pattern of ['**/api/auth/me*', '**/api/bff/auth/me*']) {
    await page.route(pattern, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: true,
          user: {
            sub: 'quality-accreditation-admin',
            displayName: 'Quality Accreditation E2E Admin',
            roles: ['admin'],
            permissions,
            tenantId: 1,
          },
        }),
      });
    });
  }

  await page.route('**/api/auth/csrf*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ csrfToken: 'quality-accreditation-csrf-token' }),
    });
  });

  await page.route('**/api/auth/me/preferences/language*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ ok: true, language: 'en' }),
    });
  });

  await page.route('**/api/public/tenants/login-directory*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            tenantId: 1,
            tenantCode: 'quality-accreditation-demo',
            tenantName: 'Quality Accreditation Demo Tenant',
            authMethods: ['password'],
          },
        ],
      }),
    });
  });

  await page.route('**/api/i18n/languages*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        languages: [
          { code: 'en', label: 'English', default: true },
          { code: 'ru', label: 'Russian', default: false },
        ],
      }),
    });
  });
}

async function stubQualityAccreditationApi(page: Page) {
  await page.route(`**${API_BASE}**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;

    const ok = async (body: unknown, status = 200) => {
      await route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(body),
      });
    };

    if (request.method() !== 'GET') {
      await ok({ detail: 'Mutation not used in smoke E2E.' }, 405);
      return;
    }

    if (path === `${API_BASE}/health`) return ok(HEALTH_FIXTURE);
    if (path === `${API_BASE}/overview`) return ok(OVERVIEW_FIXTURE);
    if (path === `${API_BASE}/dashboard`) return ok(DASHBOARD_FIXTURE);
    if (path === `${API_BASE}/matrix-summary`) return ok(MATRIX_SUMMARY_FIXTURE);
    if (path === `${API_BASE}/limitations`) return ok(LIMITATIONS_FIXTURE);
    if (path === `${API_BASE}/frameworks`) return ok(FRAMEWORKS_FIXTURE);
    if (path === `${API_BASE}/standards`) return ok(STANDARDS_FIXTURE);
    if (path === `${API_BASE}/criteria`) return ok(CRITERIA_FIXTURE);
    if (path === `${API_BASE}/standards-evidence-requirements`) return ok(REQUIREMENTS_FIXTURE);
    if (path === `${API_BASE}/evidence`) return ok(EVIDENCE_FIXTURE);
    if (path === `${API_BASE}/evidence-limitations`) return ok(EVIDENCE_LIMITATIONS_FIXTURE);
    if (path === `${API_BASE}/program-readiness`) return ok(PROGRAM_READINESS_FIXTURE);
    if (path === `${API_BASE}/institutional-readiness`) return ok(INSTITUTIONAL_READINESS_FIXTURE);
    if (path === `${API_BASE}/self-assessment`) return ok(SELF_ASSESSMENT_FIXTURE);
    if (path === `${API_BASE}/self-assessment-sections`) return ok(SELF_ASSESSMENT_SECTIONS_FIXTURE);
    if (path === `${API_BASE}/improvement-plans`) return ok(IMPROVEMENT_PLANS_FIXTURE);
    if (path === `${API_BASE}/improvement-actions`) return ok(IMPROVEMENT_ACTIONS_FIXTURE);
    if (path === `${API_BASE}/internal-audits`) return ok(INTERNAL_AUDITS_FIXTURE);
    if (path === `${API_BASE}/audit-findings`) return ok(AUDIT_FINDINGS_FIXTURE);
    if (path === `${API_BASE}/audit`) return ok(AUDIT_EVENTS_FIXTURE);
    if (path === `${API_BASE}/status-history`) return ok(STATUS_HISTORY_FIXTURE);
    if (path === `${API_BASE}/program-review`) return ok(PROGRAM_REVIEW_FIXTURE);
    if (path === `${API_BASE}/learning-outcomes`) return ok(LEARNING_OUTCOMES_FIXTURE);
    if (path === `${API_BASE}/stakeholder-feedback`) return ok(STAKEHOLDER_FEEDBACK_FIXTURE);
    if (path === `${API_BASE}/committee`) return ok(COMMITTEE_FIXTURE);
    if (path === `${API_BASE}/external-review`) return ok(EXTERNAL_REVIEW_FIXTURE);
    if (path === `${API_BASE}/expert-response-plans`) return ok(EXPERT_RESPONSE_PLANS_FIXTURE);
    if (path === `${API_BASE}/gap-analysis`) return ok(GAP_ANALYSIS_FIXTURE);
    if (path === `${API_BASE}/calendar`) return ok(CALENDAR_FIXTURE);
    if (path === `${API_BASE}/risk-register`) return ok(RISK_REGISTER_FIXTURE);
    if (path === `${API_BASE}/bridges`) return ok(BRIDGES_FIXTURE);
    if (path === `${API_BASE}/brain-signals`) return ok(BRAIN_SIGNALS_FIXTURE);

    return ok({ detail: `Unhandled Quality Accreditation stub path: ${path}` }, 404);
  });
}

async function bootQualityAccreditation(page: Page, permissions: readonly string[] = FULL_PERMISSIONS) {
  await forceEnglishLocale(page);
  await installFakeAdminAuth(page, permissions);
  await stubQualityAccreditationApi(page);
}

async function expectQualityAccreditationShell(page: Page, heading: string, path: string) {
  const shell = page.getByTestId('quality-accreditation-shell');
  await expect(shell).toBeVisible();
  await expect(page.getByRole('heading', { name: heading, level: 1 })).toBeVisible();
  await expect(page.getByTestId('quality-accreditation-boundary-banner')).toBeVisible();
  await expect(shell).toContainText(`Current path: ${path}`);
  await expect(shell.getByRole('link', { name: /^Dashboard\b/i })).toBeVisible();
  await expect(shell.getByRole('link', { name: /^Standards\b/i })).toBeVisible();
  await expect(shell.getByRole('link', { name: /^Evidence\b/i })).toBeVisible();
  await expect(shell.getByRole('link', { name: /^Bridges\b/i })).toBeVisible();
  await expect(shell.getByRole('link', { name: /^Limitations\b/i })).toBeVisible();
}

async function expectNoForbiddenQualityAccreditationActions(page: Page) {
  for (const name of FORBIDDEN_ACTIONS) {
    await expect(page.getByRole('button', { name: new RegExp(`^${name}$`, 'i') })).toHaveCount(0);
    await expect(page.getByRole('link', { name: new RegExp(`^${name}$`, 'i') })).toHaveCount(0);
    await expect(page.getByText(new RegExp(`^${name}$`, 'i'))).toHaveCount(0);
  }

  for (const name of FORBIDDEN_EXACT_TEXTS) {
    await expect(page.getByText(name)).toHaveCount(0);
  }

  await expect(page.locator('body')).not.toContainText(/official accreditation approved/i);
  await expect(page.locator('body')).not.toContainText(/ministry submitted/i);
  await expect(page.locator('body')).not.toContainText(/official ranking improved/i);
  await expect(page.locator('body')).not.toContainText(/automatic accreditation decision completed/i);
  await expect(page.locator('body')).not.toContainText(/hidden program score:\s*true/i);
  await expect(page.locator('body')).not.toContainText(/hidden faculty score:\s*true/i);
  await expect(page.locator('body')).not.toContainText(/hidden student score:\s*true/i);
  await expect(page.locator('body')).not.toContainText(/provider sync enabled\s*true/i);
  await expect(page.locator('body')).not.toContainText(/external database sync enabled\s*true/i);
}

async function gotoQualityAccreditationRoute(page: Page, path: string) {
  await page.goto(pageUrl(path));
}

test.describe('A-038.4 Quality / Accreditation Suite browser validation', () => {
  for (const [index, route] of ROUTES.entries()) {
    test(`Scenario ${index + 1} — ${route.path}`, async ({ page }) => {
      await bootQualityAccreditation(page);

      await gotoQualityAccreditationRoute(page, route.path);

      await expectQualityAccreditationShell(page, route.heading, route.path);
      await expect(page.locator('body')).toContainText(route.boundary);
      await route.assertions(page);
      await expectNoForbiddenQualityAccreditationActions(page);
    });
  }

  test('boundary coverage across the route flow remains explicit and negative-only', async ({ page }) => {
    await bootQualityAccreditation(page);
    await gotoQualityAccreditationRoute(page, '/console/quality-accreditation/limitations');

    for (const boundary of REQUIRED_BOUNDARY_TEXTS) {
      await expect(page.locator('body')).toContainText(boundary);
    }
  });
});