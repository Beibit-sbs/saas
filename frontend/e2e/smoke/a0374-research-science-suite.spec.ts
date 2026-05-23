import { expect, test, type Page } from '@playwright/test';

const BFF_BASE = '/api/bff/admin/research-science';
const BASE_URL = process.env.E2E_BASE_URL ?? 'https://nginx';

const FULL_PERMISSIONS = [
  'platform.admin.read',
  'research_science.overview.read',
  'research_science.dashboard.read',
  'research_science.health.read',
  'research_science.matrix.read',
  'research_science.limitations.read',
  'research_science.projects.read',
  'research_science.student_research.read',
  'research_science.supervision.read',
  'research_science.publications.read',
  'research_science.conferences.read',
  'research_science.grants.read',
  'research_science.ethics.read',
  'research_science.evidence.read',
  'research_science.audit.read',
  'research_science.bridges.read',
  'research_science.admin.read',
] as const;

const RESEARCH_SCIENCE_ROUTES = [
  {
    path: '/console/research-science',
    heading: 'Research / Science Suite',
    boundary: 'Metadata-only research foundation',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('research-science-overview')).toContainText('15');
      await expect(page.getByTestId('research-science-overview')).toContainText('43');
      await expect(page.getByTestId('research-science-overview')).toContainText('40');
      await expect(page.getByTestId('research-science-overview')).toContainText('c79cc31');
      await expect(page.getByTestId('research-science-overview')).toContainText('467');
      await expect(page.getByTestId('research-science-overview')).toContainText('Evidence metadata only');
      await expect(page.getByTestId('research-science-route-navigation')).toContainText('/console/research-science/dashboard');
      for (const label of REQUIRED_BOUNDARY_TEXTS) {
        await expect(page.locator('body')).toContainText(label);
      }
    },
  },
  {
    path: '/console/research-science/dashboard',
    heading: 'Dashboard',
    boundary: 'fake_metrics=false. Data source: computed_from_research_science_metadata.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('research-science-dashboard')).toContainText('fake_metrics');
      await expect(page.getByTestId('research-science-dashboard')).toContainText('computed_from_research_science_metadata');
      await expect(page.getByTestId('research-science-dashboard')).toContainText('Hidden score present');
      await expect(page.getByTestId('research-science-dashboard')).toContainText('Official verification enabled');
      await expect(page.locator('body')).not.toContainText(/hidden score present\s*true/i);
      await expect(page.locator('body')).not.toContainText(/official verification enabled\s*true/i);
      await expect(page.getByTestId('research-science-boundary-banner')).toContainText('incomplete_data supported');
    },
  },
  {
    path: '/console/research-science/projects',
    heading: 'Research Projects',
    boundary: 'Human review required',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('research-projects-page')).toContainText('Research project registry');
      await expect(page.getByTestId('research-projects-page')).toContainText('Project Atlas');
      await expect(page.getByTestId('research-projects-page')).toContainText('Metadata registry');
      await expect(page.locator('body')).not.toContainText(/officially verified/i);
    },
  },
  {
    path: '/console/research-science/student-research',
    heading: 'Student Research Work',
    boundary: 'No hidden student research score',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('student-research-page')).toContainText('Topic Alpha');
      await expect(page.getByTestId('student-research-page')).toContainText('Student research metadata');
      await expect(page.getByTestId('student-research-page')).toContainText('SUP-FAC-1');
      await expect(page.getByTestId('student-research-page')).toContainText('PUB-1');
    },
  },
  {
    path: '/console/research-science/supervision',
    heading: 'Scientific Supervision',
    boundary: 'Human review required',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('scientific-supervision-page')).toContainText('SUP-1');
      await expect(page.getByTestId('scientific-supervision-page')).toContainText('Supervision metadata');
      await expect(page.locator('body')).toContainText('no autonomous evaluation');
    },
  },
  {
    path: '/console/research-science/publications',
    heading: 'Publication Registry',
    boundary: 'This page stores publication metadata only. It does not verify publications officially, calculate citation scores, or create fake publications.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('publication-registry-page')).toContainText('Publication One');
      await expect(page.getByTestId('publication-registry-page')).toContainText('Publication metadata only');
      await expect(page.getByTestId('publication-registry-page')).toContainText('false');
    },
  },
  {
    path: '/console/research-science/conferences',
    heading: 'Conference Participation',
    boundary: 'This page stores conference participation metadata only. It does not create or validate official certificates.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('conference-participation-page')).toContainText('Conference One');
      await expect(page.getByTestId('conference-participation-page')).toContainText('Conference participation metadata');
      await expect(page.getByTestId('conference-participation-page')).toContainText('CONF-1');
    },
  },
  {
    path: '/console/research-science/grants',
    heading: 'Grant Applications and Deliverables',
    boundary: 'This page tracks grant metadata only. It does not submit grant applications or confirm official awards.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('grant-application-page')).toContainText('Grant One');
      await expect(page.getByTestId('grant-deliverables-page')).toContainText('Deliverable One');
      await expect(page.getByTestId('grant-application-page')).toContainText('autonomous_grant_submission_enabled');
      await expect(page.getByTestId('grant-deliverables-page')).toContainText('fake_grant_evidence');
      await expect(page.locator('body')).not.toContainText(/financial approval automation/i);
    },
  },
  {
    path: '/console/research-science/ethics',
    heading: 'Research Ethics',
    boundary: 'Ethics requests require human committee review. No autonomous ethics approval is performed.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('research-ethics-page')).toContainText('Ethics One');
      await expect(page.getByTestId('research-ethics-amendments-page')).toContainText('Amendment One');
      await expect(page.locator('body')).toContainText('human committee review');
    },
  },
  {
    path: '/console/research-science/evidence',
    heading: 'Evidence Metadata',
    boundary: 'Evidence records are metadata-only unless reviewed by humans. No external/provider verification is claimed.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('research-evidence-page')).toContainText('Evidence One');
      await expect(page.getByTestId('research-evidence-page')).toContainText('NOTE');
      await expect(page.getByTestId('research-evidence-page')).toContainText('METADATA_ONLY');
      await expect(page.getByTestId('research-evidence-page')).toContainText('Official external verification');
    },
  },
  {
    path: '/console/research-science/audit',
    heading: 'Audit and Status History',
    boundary: 'No official verification',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('research-audit-page')).toContainText('PROJECT_CREATED');
      await expect(page.getByTestId('research-audit-page')).toContainText('Audit event metadata');
      await expect(page.getByTestId('research-audit-page')).toContainText('autonomous_decision');
      await expect(page.getByTestId('research-audit-page')).toContainText('false');
    },
  },
  {
    path: '/console/research-science/bridges',
    heading: 'Bridge Summaries',
    boundary: 'Read-only-first bridge. No cross-suite mutation or provider sync is allowed by default.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('research-bridges-page')).toContainText('Executive Governance');
      await expect(page.getByTestId('research-bridges-page')).toContainText('Accreditation');
      await expect(page.getByTestId('research-bridges-page')).toContainText('Student Lifecycle');
      await expect(page.getByTestId('research-bridges-page')).toContainText('Academic Operations');
      await expect(page.getByTestId('research-bridges-page')).toContainText('Library / Repository');
      await expect(page.getByTestId('research-bridges-page')).toContainText('Document Workflow');
      await expect(page.getByTestId('research-bridges-page')).toContainText('Finance / Procurement');
      await expect(page.getByTestId('research-bridges-page')).toContainText('Integration / Provider Readiness');
      await expect(page.getByTestId('research-bridge-registry')).toContainText('AO-1');
    },
  },
  {
    path: '/console/research-science/limitations',
    heading: 'Limitations',
    boundary: 'Frontend runtime is not production-ready. Provider integrations, official verification, and the full Research / Science vertical remain deferred.',
    assertions: async (page: Page) => {
      await expect(page.getByTestId('research-science-limitations-panel')).toContainText('Provider, Scopus, WoS, ORCID, and ministry integrations are not implemented.');
      await expect(page.getByTestId('research-science-limitations-panel')).toContainText('Official publication verification is not implemented.');
      await expect(page.getByTestId('research-science-limitations-panel')).toContainText('Full Research / Science vertical closure remains pending.');
      await expect(page.getByTestId('research-science-limitations-panel')).toContainText('No L5 or L6 claim is made in this runtime.');
    },
  },
] as const;

if (RESEARCH_SCIENCE_ROUTES.length !== 13) {
  throw new Error(`Research Science route flow must stay at 13, received ${RESEARCH_SCIENCE_ROUTES.length}`);
}

const REQUIRED_BOUNDARY_TEXTS = [
  'Metadata-only research foundation',
  'Evidence metadata only',
  'Human review required',
  'No fake publications',
  'No fake conference certificates',
  'No fake grant evidence',
  'No autonomous ethics approval',
  'No autonomous grant submission',
  'No autonomous publication verification',
  'No hidden researcher score',
  'No provider sync',
  'No external database sync',
  'No official verification',
  'fake_metrics=false',
  'Read-only-first bridge',
] as const;

const FORBIDDEN_ACTIONS = [
  'Create fake publication',
  'Fake publication',
  'Generate fake certificate',
  'Fake conference certificate',
  'Create fake grant evidence',
  'Auto approve ethics',
  'Approve ethics automatically',
  'Auto submit grant',
  'Submit grant automatically',
  'Auto verify publication',
  'Verify publication officially',
  'Sync Scopus',
  'Sync Web of Science',
  'Sync WoS',
  'Sync ORCID',
  'Sync ministry',
] as const;

const FORBIDDEN_EXACT_TEXTS = [
  /^Production ready$/i,
  /^Sales ready$/i,
  /^GCC ready$/i,
  /^Citation score$/i,
  /^Researcher score$/i,
  /^L5$/i,
  /^L6$/i,
  /^Official ranking enabled$/i,
] as const;

const BASE_FLAGS = {
  human_review_required: true,
  autonomous_decision: false,
  provider_integration_enabled: false,
  external_database_sync_enabled: false,
  official_verification_enabled: false,
  hidden_score_present: false,
  incomplete_data: true,
  limitations: ['Metadata-only research foundation'],
  metadata: {},
  created_at: '2026-05-23T00:00:00Z',
  updated_at: '2026-05-23T00:00:00Z',
  archived_at: null,
} as const;

const HEALTH_FIXTURE = {
  tenant_id: 1,
  module: 'research_science',
  target_level: 'L4',
  foundation_status: 'READY',
  runtime_mode: 'METADATA_EVIDENCE_ONLY',
  contract_version: 'A-037.4-E2E',
  provider_integration_enabled: false,
  external_database_sync_enabled: false,
  official_verification_enabled: false,
  hidden_score_present: false,
  fake_metrics: false,
  incomplete_data: true,
  limitations: ['Metadata-only research foundation'],
  route_count: 43,
  table_count: 15,
};

const DASHBOARD_FIXTURE = {
  tenant_id: 1,
  human_review_required: true,
  autonomous_decision: false,
  provider_integration_enabled: false,
  external_database_sync_enabled: false,
  official_verification_enabled: false,
  hidden_score_present: false,
  fake_metrics: false,
  incomplete_data: true,
  limitations: ['Evidence metadata only'],
  generated_at: '2026-05-23T00:00:00Z',
  contract_version: 'A-037.4-E2E',
  source_spec_commit: '0d85d8b',
  master_matrix_commit: 'c79cc31',
  master_matrix_rows: 467,
  capability_count: 60,
  data_source: 'computed_from_research_science_metadata',
  projects_summary: { ACTIVE: 2 },
  student_research_summary: { ACTIVE: 1 },
  supervision_summary: { ACTIVE: 1 },
  publications_summary: { ACTIVE: 3 },
  conferences_summary: { ACTIVE: 1 },
  grants_summary: { ACTIVE: 2 },
  ethics_summary: { ACTIVE: 1 },
  evidence_summary: { ACTIVE: 4 },
  bridge_summary: { academic_operations: 1, student_lifecycle: 1 },
  brain_readiness_summary: { review: 1 },
  boundary_summary: { fake_metrics: false },
};

const MATRIX_SUMMARY_FIXTURE = {
  contract_version: 'A-037.4-E2E',
  source_spec_commit: '0d85d8b',
  source_product_map_commit: '10d833e',
  master_matrix_commit: 'c79cc31',
  master_matrix_rows: 467,
  capability_count: 60,
  runtime_mode: 'METADATA_EVIDENCE_ONLY',
  autonomy_mode: 'HUMAN_REVIEW_REQUIRED',
  route_count_expected: '13 routes expected',
  table_count_expected: 15,
};

const LIMITATIONS_FIXTURE = {
  items: [
    'Provider integrations not implemented.',
    'Official verification not implemented.',
    'Full Research / Science vertical not closed.',
  ],
};

const PROJECTS_FIXTURE = {
  items: [
    {
      id: 1,
      tenant_id: 1,
      status: 'ACTIVE',
      ...BASE_FLAGS,
      project_ref: 'RP-1',
      department_ref: 'DEP-1',
      program_ref: 'PRG-1',
      external_ref: null,
      title: 'Project Atlas',
      notes: 'Deliverable and evidence summary only.',
    },
  ],
};

const STUDENT_RESEARCH_FIXTURE = {
  items: [
    {
      id: 2,
      tenant_id: 1,
      status: 'ACTIVE',
      ...BASE_FLAGS,
      student_ref: 'STU-1',
      faculty_ref: 'SUP-FAC-1',
      project_ref: 'RP-1',
      publication_ref: 'PUB-1',
      conference_ref: 'CONF-1',
      topic_title: 'Topic Alpha',
      notes: 'Milestone metadata only.',
    },
  ],
};

const SUPERVISION_FIXTURE = {
  items: [
    {
      id: 3,
      tenant_id: 1,
      status: 'ACTIVE',
      ...BASE_FLAGS,
      student_ref: 'STU-1',
      faculty_ref: 'SUP-FAC-1',
      project_ref: 'RP-1',
      supervision_ref: 'SUP-1',
      notes: 'Review status visible.',
    },
  ],
};

const PUBLICATIONS_FIXTURE = {
  items: [
    {
      id: 4,
      tenant_id: 1,
      status: 'ACTIVE',
      ...BASE_FLAGS,
      publication_ref: 'PUB-1',
      faculty_ref: 'SUP-FAC-1',
      student_ref: 'STU-1',
      project_ref: 'RP-1',
      external_ref: null,
      title: 'Publication One',
      fake_publication: false,
      autonomous_publication_verification_enabled: false,
    },
  ],
};

const CONFERENCES_FIXTURE = {
  items: [
    {
      id: 5,
      tenant_id: 1,
      status: 'ACTIVE',
      ...BASE_FLAGS,
      conference_ref: 'CONF-1',
      faculty_ref: 'SUP-FAC-1',
      student_ref: 'STU-1',
      project_ref: 'RP-1',
      external_ref: null,
      title: 'Conference One',
      fake_certificate: false,
    },
  ],
};

const GRANTS_FIXTURE = {
  items: [
    {
      id: 6,
      tenant_id: 1,
      status: 'ACTIVE',
      ...BASE_FLAGS,
      grant_ref: 'GR-1',
      project_ref: 'RP-1',
      department_ref: 'DEP-1',
      faculty_ref: 'SUP-FAC-1',
      external_ref: null,
      title: 'Grant One',
      fake_grant_evidence: false,
      autonomous_grant_submission_enabled: false,
    },
  ],
};

const GRANT_DELIVERABLES_FIXTURE = {
  items: [
    {
      id: 7,
      tenant_id: 1,
      status: 'ACTIVE',
      ...BASE_FLAGS,
      grant_ref: 'GR-1',
      project_ref: 'RP-1',
      external_ref: null,
      deliverable_ref: 'DEL-1',
      title: 'Deliverable One',
      fake_grant_evidence: false,
      autonomous_grant_submission_enabled: false,
    },
  ],
};

const ETHICS_FIXTURE = {
  items: [
    {
      id: 8,
      tenant_id: 1,
      status: 'ACTIVE',
      ...BASE_FLAGS,
      ethics_ref: 'ETH-1',
      project_ref: 'RP-1',
      faculty_ref: 'SUP-FAC-1',
      student_ref: 'STU-1',
      title: 'Ethics One',
      autonomous_ethics_approval_enabled: false,
    },
  ],
};

const ETHICS_AMENDMENTS_FIXTURE = {
  items: [
    {
      id: 9,
      tenant_id: 1,
      status: 'ACTIVE',
      ...BASE_FLAGS,
      ethics_ref: 'ETH-1',
      project_ref: 'RP-1',
      external_ref: null,
      amendment_ref: 'AMD-1',
      title: 'Amendment One',
    },
  ],
};

const EVIDENCE_FIXTURE = {
  items: [
    {
      id: 10,
      tenant_id: 1,
      status: 'ACTIVE',
      ...BASE_FLAGS,
      source_entity_type: 'research_project',
      source_entity_id: 1,
      evidence_type: 'NOTE',
      title: 'Evidence One',
      description: null,
      reference_uri: null,
      storage_ref: null,
      submitted_by_user_id: 'admin',
      submitted_at: '2026-05-23T00:00:00Z',
      verification_status: 'METADATA_ONLY',
      verified_by_user_id: null,
      reviewed_at: null,
      provider_verified: false,
      official_external_verification: false,
      fake_evidence: false,
    },
  ],
};

const AUDIT_FIXTURE = {
  items: [
    {
      id: 11,
      tenant_id: 1,
      event_type: 'PROJECT_CREATED',
      source_entity_type: 'research_project',
      source_entity_id: 1,
      actor_user_id: 'admin',
      previous_status: null,
      new_status: 'DRAFT',
      payload: {},
      request_id: null,
      created_at: '2026-05-23T00:00:00Z',
      human_review_required: true,
      autonomous_decision: false,
      provider_integration_enabled: false,
      hidden_score_present: false,
    },
  ],
};

const BRIDGES_FIXTURE = {
  items: [
    {
      id: 12,
      tenant_id: 1,
      status: 'ACTIVE',
      ...BASE_FLAGS,
      bridge_target: 'academic_operations',
      source_entity_type: 'research_project',
      source_entity_id: 1,
      target_reference: 'AO-1',
      bridge_status: 'ACTIVE',
      bridge_ref: 'BR-1',
      read_only_first: true,
      mutation_allowed: false,
      provider_sync_enabled: false,
      external_submission_enabled: false,
    },
  ],
};

const BRIDGE_SUMMARY_FIXTURE = {
  tenant_id: 1,
  bridge_counts: {
    executive_governance: 1,
    accreditation: 1,
    student_lifecycle: 2,
    academic_operations: 1,
    library_repository: 1,
    document_workflow: 1,
    finance_procurement: 1,
    integration_provider: 1,
  },
  read_only_first: true,
  mutation_allowed: false,
  provider_sync_enabled: false,
  external_submission_enabled: false,
};

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
    sub: 'research-science-admin',
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
            sub: 'research-science-admin',
            displayName: 'Research Science E2E Admin',
            roles: ['admin'],
            permissions,
            tenantId: 1,
          },
        }),
      });
    });
  }
}

async function stubResearchScienceApi(page: Page) {
  await page.route(`**${BFF_BASE}**`, async (route) => {
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

    if (path === `${BFF_BASE}/health`) return ok(HEALTH_FIXTURE);
    if (path === `${BFF_BASE}/dashboard`) return ok(DASHBOARD_FIXTURE);
    if (path === `${BFF_BASE}/matrix-summary`) return ok(MATRIX_SUMMARY_FIXTURE);
    if (path === `${BFF_BASE}/limitations`) return ok(LIMITATIONS_FIXTURE);
    if (path === `${BFF_BASE}/projects`) return ok(PROJECTS_FIXTURE);
    if (path === `${BFF_BASE}/student-research`) return ok(STUDENT_RESEARCH_FIXTURE);
    if (path === `${BFF_BASE}/supervision`) return ok(SUPERVISION_FIXTURE);
    if (path === `${BFF_BASE}/publications`) return ok(PUBLICATIONS_FIXTURE);
    if (path === `${BFF_BASE}/conferences`) return ok(CONFERENCES_FIXTURE);
    if (path === `${BFF_BASE}/grants`) return ok(GRANTS_FIXTURE);
    if (path === `${BFF_BASE}/grant-deliverables`) return ok(GRANT_DELIVERABLES_FIXTURE);
    if (path === `${BFF_BASE}/ethics`) return ok(ETHICS_FIXTURE);
    if (path === `${BFF_BASE}/ethics-amendments`) return ok(ETHICS_AMENDMENTS_FIXTURE);
    if (path === `${BFF_BASE}/evidence`) return ok(EVIDENCE_FIXTURE);
    if (path === `${BFF_BASE}/audit`) return ok(AUDIT_FIXTURE);
    if (path === `${BFF_BASE}/bridges`) return ok(BRIDGES_FIXTURE);
    if (path === `${BFF_BASE}/bridges/summary`) return ok(BRIDGE_SUMMARY_FIXTURE);

    return ok({ detail: `Unhandled Research Science stub path: ${path}` }, 404);
  });
}

async function bootResearchScience(page: Page, permissions: readonly string[] = FULL_PERMISSIONS) {
  await forceEnglishLocale(page);
  await installFakeAdminAuth(page, permissions);
  await stubResearchScienceApi(page);
}

async function expectResearchScienceShell(page: Page, heading: string) {
  await expect(page.getByRole('heading', { name: heading, level: 1 })).toBeVisible();
  await expect(page.getByTestId('research-science-page')).toBeVisible();
  await expect(page.getByTestId('research-science-boundary-banner')).toBeVisible();

  const nav = page
    .getByTestId('research-science-page')
    .getByRole('navigation', { name: 'Research Science navigation' });

  await expect(nav).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Dashboard' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Projects' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Student Research' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Supervision' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Publications' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Conferences' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Grants' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Ethics' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Evidence' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Audit' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Bridges' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Limitations' })).toBeVisible();
}

async function expectNoForbiddenResearchScienceActions(page: Page) {
  for (const name of FORBIDDEN_ACTIONS) {
    await expect(page.getByRole('button', { name: new RegExp(`^${name}$`, 'i') })).toHaveCount(0);
    await expect(page.getByRole('link', { name: new RegExp(`^${name}$`, 'i') })).toHaveCount(0);
    await expect(page.getByText(new RegExp(`^${name}$`, 'i'))).toHaveCount(0);
  }

  for (const name of FORBIDDEN_EXACT_TEXTS) {
    await expect(page.getByText(name)).toHaveCount(0);
  }

  await expect(page.locator('body')).not.toContainText(/official verification enabled\s*true/i);
  await expect(page.locator('body')).not.toContainText(/provider sync enabled\s*true/i);
  await expect(page.locator('body')).not.toContainText(/external database sync enabled\s*true/i);
  await expect(page.locator('body')).not.toContainText(/hidden score present\s*true/i);
  await expect(page.locator('body')).not.toContainText(/mutation allowed\s*true/i);
  await expect(page.locator('body')).not.toContainText(/external submission enabled\s*true/i);
}

async function gotoResearchScienceRoute(page: Page, path: string) {
  await page.goto(pageUrl(path));
}

test.describe('A-037.4 Research / Science Suite browser validation', () => {
  for (const [index, route] of RESEARCH_SCIENCE_ROUTES.entries()) {
    test(`Scenario ${index + 1} — ${route.path}`, async ({ page }) => {
      await bootResearchScience(page);

      await gotoResearchScienceRoute(page, route.path);

      await expectResearchScienceShell(page, route.heading);
      await expect(page.locator('body')).toContainText(route.boundary);
      await route.assertions(page);
      await expectNoForbiddenResearchScienceActions(page);
    });
  }
});