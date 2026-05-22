import { expect, test, type Page } from '@playwright/test';

const BFF_BASE = '/api/bff/admin/academic-operations';
const BASE_URL = process.env.E2E_BASE_URL ?? 'https://nginx';

const FULL_PERMISSIONS = [
  'platform.admin.read',
  'academic_operations.overview.read',
  'academic_operations.dashboard.read',
  'academic_operations.health.read',
  'academic_operations.audit.read',
  'academic_operations.evidence.read',
  'academic_operations.evidence.attach',
  'academic_operations.academic_groups.read',
  'academic_operations.academic_groups.create',
  'academic_operations.academic_groups.update',
  'academic_operations.cohorts.read',
  'academic_operations.cohorts.create',
  'academic_operations.cohorts.update',
  'academic_operations.gradebook_metadata.read',
  'academic_operations.gradebook_metadata.create',
  'academic_operations.gradebook_metadata.update',
  'academic_operations.retake_management.read',
  'academic_operations.retake_management.create',
  'academic_operations.retake_management.update',
  'academic_operations.summer_semester.read',
  'academic_operations.summer_semester.create',
  'academic_operations.summer_semester.update',
  'academic_operations.advisor_tutor.read',
  'academic_operations.advisor_tutor.create',
  'academic_operations.advisor_tutor.update',
  'academic_operations.canonical_bridge.read',
  'academic_operations.canonical_bridge.create',
  'academic_operations.canonical_bridge.update',
  'academic_operations.student_lifecycle_bridge.read',
  'academic_operations.document_workflow_bridge.read',
  'academic_operations.executive_governance_bridge.read',
  'academic_operations.quality_accreditation_bridge.read',
  'academic_operations.course_catalog_bridge.read',
  'academic_operations.elective_selection_bridge.read',
  'academic_operations.committee_decision_bridge.read',
  'academic_operations.prerequisite_bridge.read',
  'academic_operations.teaching_load_bridge.read',
  'academic_operations.thesis_bridge.read',
  'academic_operations.degree_audit_bridge.read',
  'academic_operations.admin.read',
  'academic_operations.admin.configure',
] as const;

const DASHBOARD_FIXTURE = {
  tenant_id: 1,
  fake_metrics: false,
  data_source: 'computed_from_academic_operations_metadata',
  master_matrix_commit: 'c79cc31',
  master_matrix_rows: 467,
  incomplete_data: true,
  limitations: [
    'Metadata-only foundation',
    'No official grade publication',
    'Full 467-row runtime is not implemented.',
  ],
  counts: {
    academic_groups: 1,
    cohorts: 1,
    course_registration: 1,
    gradebook_metadata: 1,
    retakes: 1,
    summer_semesters: 1,
    advisor_tutor: 1,
  },
  canonical_bridge_counts: {
    course_catalog: 1,
    student_lifecycle: 1,
    document_workflow: 1,
    executive_governance: 1,
    quality_accreditation: 1,
  },
};

const HEALTH_FIXTURE = {
  tenant_id: 1,
  module: 'academic_operations',
  target_level: 'L4',
  foundation_status: 'IMPLEMENTED_RUNTIME',
  duplicate_module_policy: 'canonical_reuse_required',
  provider_integration_enabled: false,
  platonus_sync_enabled: false,
  sis_sync_enabled: false,
  hidden_score_present: false,
  fake_metrics: false,
  incomplete_data: true,
  limitations: ['Metadata-only foundation'],
  route_count: 40,
  table_count: 19,
};

const MATRIX_SUMMARY_FIXTURE = {
  master_matrix_commit: 'c79cc31',
  master_matrix_rows: 467,
  contract_version: 'A-036.4-E2E',
  target_level: 'L4',
  duplicate_module_policy: 'canonical_reuse_required',
  true_new_modules: ['academic_operations'],
  canonical_reuse_map: {
    course_catalog: 'course_catalog_management',
    committee_decisions: 'committee_decision_registry',
  },
  bridge_map: {
    student_lifecycle: 'academic_operations_to_student_lifecycle_bridge',
    document_workflow: 'academic_operations_to_document_workflow_bridge',
    executive_governance: 'academic_operations_to_executive_governance_bridge',
    quality_accreditation: 'academic_operations_to_quality_accreditation_bridge',
  },
  forbidden_runtime_claims: [
    'Publish official grade',
    'Approve grade',
    'Calculate grade',
    'Provider dispatch',
  ],
  required_limitations: [
    'Matrix-guided: 467 planning rows',
    'Full 467-row runtime is not implemented.',
    'Optional detail routes remain deferred.',
  ],
};

const CANONICAL_REUSE_FIXTURE = {
  duplicate_module_policy: 'canonical_reuse_required',
  canonical_reuse_map: {
    course_catalog: 'course_catalog_management',
    elective_selection: 'existing canonical',
    committee_decisions: 'committee_decision_registry',
  },
  bridge_map: {
    student_lifecycle: 'academic_operations_to_student_lifecycle_bridge',
    document_workflow: 'academic_operations_to_document_workflow_bridge',
    executive_governance: 'academic_operations_to_executive_governance_bridge',
    quality_accreditation: 'academic_operations_to_quality_accreditation_bridge',
  },
  true_new_modules: ['academic_operations'],
  required_limitations: ['Canonical reuse / no duplicate modules'],
  forbidden_runtime_claims: ['No provider sync'],
};

const BASE_FLAGS = {
  human_review_required: true,
  automated_decision: false,
  provider_integration_enabled: false,
  platonus_sync_enabled: false,
  sis_sync_enabled: false,
  hidden_score_present: false,
  fake_metrics: false,
  official_grade_publication_enabled: false,
  automated_grading_enabled: false,
  automatic_sanction_enabled: false,
  incomplete_data: true,
  limitations: ['Metadata-only foundation'],
  source_matrix_row_id: 'AO-001',
  source_capability_id: 'AO-CAP-001',
};

const REGISTRY_FIXTURES = {
  academicGroups: {
    items: [
      {
        id: 1,
        tenant_id: 1,
        status: 'ACTIVE',
        created_at: '2026-05-22T10:00:00Z',
        updated_at: '2026-05-22T10:05:00Z',
        archived_at: null,
        ...BASE_FLAGS,
        group_code: 'AG-2026',
        group_name: 'Academic Group 2026',
        external_ref: null,
        notes: 'Opaque metadata only.',
      },
    ],
  },
  cohorts: {
    items: [
      {
        id: 2,
        tenant_id: 1,
        status: 'ACTIVE',
        created_at: '2026-05-22T10:10:00Z',
        updated_at: '2026-05-22T10:12:00Z',
        archived_at: null,
        ...BASE_FLAGS,
        cohort_code: 'CO-2026',
        cohort_name: 'Cohort 2026',
        academic_group_ref: 'AG-2026',
        notes: 'Metadata only.',
      },
    ],
  },
  courseRegistration: {
    items: [
      {
        id: 3,
        tenant_id: 1,
        status: 'ACTIVE',
        created_at: '2026-05-22T10:20:00Z',
        updated_at: '2026-05-22T10:25:00Z',
        archived_at: null,
        ...BASE_FLAGS,
        student_ref: 'opaque-student-ref',
        course_ref: 'COURSE-101',
        canonical_module_ref: 'course_catalog_management',
        metadata: { registration_window: '2026-FALL' },
        notes: 'Metadata-only registration surface.',
      },
    ],
  },
  gradebook: {
    items: [
      {
        id: 4,
        tenant_id: 1,
        status: 'ACTIVE',
        created_at: '2026-05-22T10:30:00Z',
        updated_at: '2026-05-22T10:35:00Z',
        archived_at: null,
        ...BASE_FLAGS,
        gradebook_key: 'GB-2026-01',
        student_ref: 'opaque-student-ref',
        course_ref: 'COURSE-101',
        metadata: { grading_schema: 'metadata-only' },
      },
    ],
  },
  retakes: {
    items: [
      {
        id: 5,
        tenant_id: 1,
        status: 'ACTIVE',
        created_at: '2026-05-22T10:40:00Z',
        updated_at: '2026-05-22T10:45:00Z',
        archived_at: null,
        ...BASE_FLAGS,
        plan_code: 'RET-2026-01',
        student_ref: 'opaque-student-ref',
        course_ref: 'COURSE-101',
        retake_window: '2026-08',
      },
    ],
  },
  summerSemesters: {
    items: [
      {
        id: 6,
        tenant_id: 1,
        status: 'ACTIVE',
        created_at: '2026-05-22T10:50:00Z',
        updated_at: '2026-05-22T10:55:00Z',
        archived_at: null,
        ...BASE_FLAGS,
        term_code: 'SUMMER-2026',
        display_name: 'Summer 2026',
        calendar_ref: 'CAL-2026-SUMMER',
      },
    ],
  },
  advisorTutor: {
    items: [
      {
        id: 7,
        tenant_id: 1,
        status: 'ACTIVE',
        created_at: '2026-05-22T11:00:00Z',
        updated_at: '2026-05-22T11:05:00Z',
        archived_at: null,
        ...BASE_FLAGS,
        assignment_code: 'AT-2026-01',
        student_ref: 'opaque-student-ref',
        faculty_ref: 'opaque-faculty-ref',
        notes: 'Human support framing only.',
      },
    ],
  },
};

const BRIDGE_FIXTURE = {
  items: [
    {
      id: 8,
      tenant_id: 1,
      status: 'ACTIVE',
      created_at: '2026-05-22T11:10:00Z',
      updated_at: '2026-05-22T11:15:00Z',
      archived_at: null,
      ...BASE_FLAGS,
      bridge_type: 'course_catalog',
      canonical_module_ref: 'course_catalog_management',
      external_ref: null,
      metadata: { read_only_first: true },
    },
    {
      id: 9,
      tenant_id: 1,
      status: 'ACTIVE',
      created_at: '2026-05-22T11:16:00Z',
      updated_at: '2026-05-22T11:17:00Z',
      archived_at: null,
      ...BASE_FLAGS,
      bridge_type: 'elective_selection',
      canonical_module_ref: 'existing canonical',
      external_ref: null,
      metadata: { read_only_first: true },
    },
  ],
  studentLifecycle: [
    {
      id: 10,
      tenant_id: 1,
      status: 'ACTIVE',
      created_at: '2026-05-22T11:20:00Z',
      updated_at: '2026-05-22T11:21:00Z',
      archived_at: null,
      ...BASE_FLAGS,
      bridge_key: 'student_lifecycle_bridge',
      student_ref: 'opaque-student-ref',
      external_ref: 'student-lifecycle',
      metadata: { read_only_first: true },
    },
  ],
  documentWorkflow: [
    {
      id: 11,
      tenant_id: 1,
      status: 'ACTIVE',
      created_at: '2026-05-22T11:22:00Z',
      updated_at: '2026-05-22T11:23:00Z',
      archived_at: null,
      ...BASE_FLAGS,
      bridge_key: 'document_workflow_bridge',
      student_ref: null,
      external_ref: 'document-workflow',
      metadata: { read_only_first: true },
    },
  ],
  executiveGovernance: [
    {
      id: 12,
      tenant_id: 1,
      status: 'ACTIVE',
      created_at: '2026-05-22T11:24:00Z',
      updated_at: '2026-05-22T11:25:00Z',
      archived_at: null,
      ...BASE_FLAGS,
      bridge_key: 'executive_governance_bridge',
      student_ref: null,
      external_ref: 'executive-governance',
      metadata: { read_only_first: true },
    },
  ],
  qualityAccreditation: [
    {
      id: 13,
      tenant_id: 1,
      status: 'ACTIVE',
      created_at: '2026-05-22T11:26:00Z',
      updated_at: '2026-05-22T11:27:00Z',
      archived_at: null,
      ...BASE_FLAGS,
      bridge_key: 'quality_accreditation_bridge',
      student_ref: null,
      external_ref: 'quality-accreditation',
      metadata: { read_only_first: true },
    },
  ],
};

const AUDIT_FIXTURE = [
  {
    id: 14,
    tenant_id: 1,
    entity_type: 'retake_plan',
    entity_id: 5,
    event_type: 'RETAKE_PLAN_REVIEWED',
    action: 'review_metadata',
    actor_user_id: 'reviewer-1',
    previous_status: 'PENDING',
    new_status: 'ACTIVE',
    human_review_required: true,
    automated_decision: false,
    provider_integration_enabled: false,
    payload: {},
    created_at: '2026-05-22T11:30:00Z',
  },
];

const EVIDENCE_FIXTURE = {
  items: [
    {
      id: 15,
      tenant_id: 1,
      status: 'ACTIVE',
      created_at: '2026-05-22T11:31:00Z',
      updated_at: '2026-05-22T11:32:00Z',
      archived_at: null,
      ...BASE_FLAGS,
      entity_type: 'retake_plan',
      entity_id: 5,
      evidence_kind: 'NOTE',
      external_ref: 'AO-EV-001',
      metadata: { metadata_only: true },
    },
  ],
};

const ROUTE_EXPECTATIONS = [
  { path: '/console/academic-operations', heading: 'Academic Operations Suite', boundary: 'Metadata-only foundation' },
  { path: '/console/academic-operations/dashboard', heading: 'Academic Operations Suite', boundary: 'fake_metrics=false. Data source: computed_from_academic_operations_metadata.' },
  { path: '/console/academic-operations/matrix', heading: 'Matrix Summary', boundary: 'Matrix-guided: 467 planning rows' },
  { path: '/console/academic-operations/academic-groups', heading: 'Academic Groups', boundary: 'Human review required' },
  { path: '/console/academic-operations/cohorts', heading: 'Cohorts', boundary: 'No automatic sanction' },
  { path: '/console/academic-operations/course-registration', heading: 'Course Registration Metadata', boundary: 'No Platonus/SIS integration' },
  { path: '/console/academic-operations/gradebook-metadata', heading: 'Gradebook Metadata', boundary: 'This page manages gradebook metadata only.' },
  { path: '/console/academic-operations/retakes', heading: 'Retake Plans', boundary: 'Retake metadata requires human review.' },
  { path: '/console/academic-operations/summer-semesters', heading: 'Summer Semester Terms', boundary: 'No provider sync' },
  { path: '/console/academic-operations/advisor-tutor', heading: 'Advisor / Tutor Assignments', boundary: 'No hidden score' },
  { path: '/console/academic-operations/bridges', heading: 'Canonical Bridges', boundary: 'Read-only-first bridge' },
  { path: '/console/academic-operations/audit-evidence', heading: 'Audit / Evidence', boundary: 'No fake evidence' },
  { path: '/console/academic-operations/limitations', heading: 'Limitations', boundary: 'Official transcript update is not implemented.' },
] as const;

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

async function stubAuthSession(page: Page, permissions: readonly string[] = FULL_PERMISSIONS) {
  const parsedUrl = new URL(BASE_URL);
  const cookieOrigins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  const payloadJson = JSON.stringify({
    sub: 'academic-operations-admin',
    exp: Math.floor(Date.now() / 1000) + 3600,
  });
  const payload = Buffer.from(payloadJson).toString('base64url');
  const fakeToken = `fakeheader.${payload}.fakesig`;

  await page.context().addCookies(
    Array.from(cookieOrigins).flatMap((url) => {
      const secure = new URL(url).protocol === 'https:';
      return [
        {
          name: 'admin_token',
          value: fakeToken,
          url,
          httpOnly: true,
          secure,
          sameSite: 'Lax' as const,
        },
        {
          name: 'app_access_token',
          value: fakeToken,
          url,
          httpOnly: true,
          secure,
          sameSite: 'Lax' as const,
        },
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
            sub: 'academic-operations-admin',
            displayName: 'Academic Operations E2E Admin',
            roles: ['admin'],
            permissions,
            tenantId: 1,
          },
        }),
      });
    });
  }
}

async function stubAcademicOperationsApis(page: Page) {
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
    if (path === `${BFF_BASE}/canonical-reuse-summary`) return ok(CANONICAL_REUSE_FIXTURE);
    if (path === `${BFF_BASE}/academic-groups`) return ok(REGISTRY_FIXTURES.academicGroups);
    if (path === `${BFF_BASE}/cohorts`) return ok(REGISTRY_FIXTURES.cohorts);
    if (path === `${BFF_BASE}/course-registration`) return ok(REGISTRY_FIXTURES.courseRegistration);
    if (path === `${BFF_BASE}/gradebook-metadata`) return ok(REGISTRY_FIXTURES.gradebook);
    if (path === `${BFF_BASE}/retakes`) return ok(REGISTRY_FIXTURES.retakes);
    if (path === `${BFF_BASE}/summer-semesters`) return ok(REGISTRY_FIXTURES.summerSemesters);
    if (path === `${BFF_BASE}/advisor-tutor`) return ok(REGISTRY_FIXTURES.advisorTutor);
    if (path === `${BFF_BASE}/bridges`) return ok({ items: BRIDGE_FIXTURE.items });
    if (path === `${BFF_BASE}/bridges/canonical`) return ok(CANONICAL_REUSE_FIXTURE);
    if (path === `${BFF_BASE}/bridges/student-lifecycle`) return ok(BRIDGE_FIXTURE.studentLifecycle);
    if (path === `${BFF_BASE}/bridges/document-workflow`) return ok(BRIDGE_FIXTURE.documentWorkflow);
    if (path === `${BFF_BASE}/bridges/executive-governance`) return ok(BRIDGE_FIXTURE.executiveGovernance);
    if (path === `${BFF_BASE}/bridges/quality-accreditation`) return ok(BRIDGE_FIXTURE.qualityAccreditation);
    if (path === `${BFF_BASE}/audit`) return ok(AUDIT_FIXTURE);
    if (path === `${BFF_BASE}/evidence`) return ok(EVIDENCE_FIXTURE);

    return ok({ detail: `Unhandled Academic Operations stub path: ${path}` }, 404);
  });
}

async function bootAcademicOperations(page: Page, permissions: readonly string[] = FULL_PERMISSIONS) {
  await forceEnglishLocale(page);
  await stubAuthSession(page, permissions);
  await stubAcademicOperationsApis(page);
}

async function expectShellNav(page: Page) {
  const nav = page
    .getByTestId('academic-operations-page')
    .getByRole('navigation', { name: 'Academic Operations navigation' });

  await expect(nav).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Dashboard' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Matrix' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Academic Groups' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Cohorts' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Course Registration' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Gradebook Metadata' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Retakes' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Summer Semesters' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Advisor / Tutor' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Bridges' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Audit / Evidence' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Limitations' })).toBeVisible();
}

async function expectNoForbiddenActionUi(page: Page) {
  const forbiddenButtonNames = [
    /Publish official grade/i,
    /Approve grade/i,
    /Calculate grade/i,
    /Sanction student/i,
    /Dismiss student/i,
    /Sync with Platonus/i,
    /Sync with SIS/i,
    /Provider dispatch/i,
    /Generate official transcript/i,
    /Generate official order/i,
  ];

  for (const name of forbiddenButtonNames) {
    await expect(page.getByRole('button', { name })).toHaveCount(0);
    await expect(page.getByRole('link', { name })).toHaveCount(0);
  }

  await expect(page.getByText(/^Production-ready$/i)).toHaveCount(0);
  await expect(page.getByText(/^Sales-ready$/i)).toHaveCount(0);
  await expect(page.getByText(/^GCC-ready$/i)).toHaveCount(0);
  await expect(page.getByText(/^L5$/i)).toHaveCount(0);
  await expect(page.getByText(/^L6$/i)).toHaveCount(0);
}

test.describe('A-036.4 — Academic Operations Suite browser validation', () => {
  test('Scenario 1 — Entry / overview', async ({ page }) => {
    await bootAcademicOperations(page);

    await page.goto(pageUrl('/console/academic-operations'));

    await expect(page.getByRole('heading', { name: 'Academic Operations Suite', level: 1 })).toBeVisible();
    await expectShellNav(page);
    await expect(page.getByTestId('academic-operations-boundary-banner')).toContainText('Metadata-only foundation');
    await expect(page.getByTestId('academic-operations-boundary-banner')).toContainText('No provider sync');
    await expect(page.getByTestId('academic-operations-boundary-banner')).toContainText('fake_metrics=false');
    await expectNoForbiddenActionUi(page);
  });

  test('Scenario 2 — Dashboard / matrix', async ({ page }) => {
    await bootAcademicOperations(page);

    await page.goto(pageUrl('/console/academic-operations/dashboard'));

    await expect(page.getByRole('heading', { name: 'Academic Operations Suite', level: 1 })).toBeVisible();
    await expect(page.getByTestId('academic-operations-boundary-banner')).toContainText('fake_metrics=false');
    await expect(page.getByTestId('academic-operations-dashboard')).toContainText('467');
    await expect(page.locator('body')).toContainText('Tracked metadata records');
    await expect(page.locator('body')).toContainText('Human review required');
    await expect(page.locator('body')).toContainText('Full 467-row runtime is not implemented.');

    await page.goto(pageUrl('/console/academic-operations/matrix'));

    await expect(page.getByRole('heading', { name: 'Matrix Summary', level: 1 })).toBeVisible();
    await expect(page.getByTestId('academic-operations-boundary-banner')).toContainText('Matrix-guided: 467 planning rows');
    await expect(page.getByTestId('academic-operations-matrix-summary-panel')).toContainText('c79cc31');
    await expect(page.locator('body')).toContainText('capability rows do not equal backend packages');
    await expectNoForbiddenActionUi(page);
  });

  test('Scenario 3 — Academic groups / cohorts', async ({ page }) => {
    await bootAcademicOperations(page);

    await page.goto(pageUrl('/console/academic-operations/academic-groups'));

    await expect(page.getByRole('heading', { name: 'Academic Groups', level: 1 })).toBeVisible();
    await expect(page.getByTestId('academic-operations-boundary-banner')).toContainText('Human review required');
    await expect(page.getByTestId('academic-operations-boundary-banner')).toContainText('Metadata-only foundation');
    await expect(page.locator('body')).toContainText('Academic Group 2026');

    await page.goto(pageUrl('/console/academic-operations/cohorts'));

    await expect(page.getByRole('heading', { name: 'Cohorts', level: 1 })).toBeVisible();
    await expect(page.locator('body')).toContainText('Cohort metadata only. No official graduation or degree decisions are made here.');
    await expect(page.locator('body')).toContainText('Cohort 2026');
    await expectNoForbiddenActionUi(page);
  });

  test('Scenario 4 — Course registration metadata', async ({ page }) => {
    await bootAcademicOperations(page);

    await page.goto(pageUrl('/console/academic-operations/course-registration'));

    await expect(page.getByRole('heading', { name: 'Course Registration Metadata', level: 1 })).toBeVisible();
    await expect(page.getByTestId('academic-operations-boundary-banner')).toContainText('No provider sync');
    await expect(page.getByTestId('academic-operations-boundary-banner')).toContainText('No Platonus/SIS integration');
    await expect(page.getByTestId('course-registration-metadata-registry')).toContainText('Course registration metadata');
    await expect(page.locator('body')).not.toContainText(/automatic enrollment/i);
    await expectNoForbiddenActionUi(page);
  });

  test('Scenario 5 — Gradebook metadata', async ({ page }) => {
    await bootAcademicOperations(page);

    await page.goto(pageUrl('/console/academic-operations/gradebook-metadata'));

    await expect(page.getByRole('heading', { name: 'Gradebook Metadata', level: 1 })).toBeVisible();
    await expect(page.getByTestId('academic-operations-boundary-banner')).toContainText('No official grade publication');
    await expect(page.getByTestId('academic-operations-boundary-banner')).toContainText('No automated grading');
    await expect(page.getByTestId('gradebook-metadata-registry')).toContainText('This page manages gradebook metadata only');
    await expect(page.getByTestId('gradebook-metadata-registry')).toContainText('No official grade publication');
    await expectNoForbiddenActionUi(page);
  });

  test('Scenario 6 — Retakes / summer semesters', async ({ page }) => {
    await bootAcademicOperations(page);

    await page.goto(pageUrl('/console/academic-operations/retakes'));

    await expect(page.getByRole('heading', { name: 'Retake Plans', level: 1 })).toBeVisible();
    await expect(page.getByTestId('academic-operations-boundary-banner')).toContainText('Human review required');
    await expect(page.getByTestId('retake-plans-registry')).toContainText('No automatic retake denial, sanction, or dismissal is performed');
    await expectNoForbiddenActionUi(page);

    await page.goto(pageUrl('/console/academic-operations/summer-semesters'));

    await expect(page.getByRole('heading', { name: 'Summer Semester Terms', level: 1 })).toBeVisible();
    await expect(page.getByTestId('academic-operations-boundary-banner')).toContainText('Metadata-only foundation');
    await expect(page.locator('body')).toContainText('Summer 2026');
    await expect(page.locator('body')).not.toContainText(/official billing|payment/i);
    await expectNoForbiddenActionUi(page);
  });

  test('Scenario 7 — Advisor / tutor', async ({ page }) => {
    await bootAcademicOperations(page);

    await page.goto(pageUrl('/console/academic-operations/advisor-tutor'));

    await expect(page.getByRole('heading', { name: 'Advisor / Tutor Assignments', level: 1 })).toBeVisible();
    await expect(page.getByTestId('academic-operations-boundary-banner')).toContainText('Human review required');
    await expect(page.getByTestId('academic-operations-boundary-banner')).toContainText('No hidden score');
    await expect(page.getByTestId('advisor-tutor-registry')).toContainText('Advisor / tutor assignments');
    await expect(page.locator('body')).not.toContainText(/faculty performance score/i);
    await expectNoForbiddenActionUi(page);
  });

  test('Scenario 8 — Bridges', async ({ page }) => {
    await bootAcademicOperations(page);

    await page.goto(pageUrl('/console/academic-operations/bridges'));

    await expect(page.getByRole('heading', { name: 'Canonical Bridges', level: 1 })).toBeVisible();
    await expect(page.getByTestId('academic-operations-boundary-banner')).toContainText('Read-only-first bridge');
    await expect(page.getByTestId('bridge-metadata-panel')).toContainText('Canonical reuse / no duplicate modules');
    await expect(page.getByTestId('bridge-metadata-panel')).toContainText('No cross-suite mutation is allowed by default');
    await expect(page.getByTestId('bridge-metadata-panel')).toContainText('Student lifecycle bridge');
    await expect(page.getByTestId('bridge-metadata-panel')).toContainText('Document workflow bridge');
    await expect(page.getByTestId('bridge-metadata-panel')).toContainText('Executive governance bridge');
    await expect(page.getByTestId('bridge-metadata-panel')).toContainText('Quality accreditation bridge');
    await expectNoForbiddenActionUi(page);
  });

  test('Scenario 9 — Audit / evidence', async ({ page }) => {
    await bootAcademicOperations(page);

    await page.goto(pageUrl('/console/academic-operations/audit-evidence'));

    await expect(page.getByRole('heading', { name: 'Audit / Evidence', level: 1 })).toBeVisible();
    await expect(page.getByTestId('academic-operations-boundary-banner')).toContainText('No fake evidence');
    await expect(page.getByTestId('academic-operations-boundary-banner')).toContainText('No official legal document claim');
    await expect(page.getByTestId('audit-evidence-panel')).toContainText('Audit events');
    await expect(page.getByTestId('audit-evidence-panel')).toContainText('Evidence metadata');
    await expectNoForbiddenActionUi(page);
  });

  test('Scenario 10 — Limitations', async ({ page }) => {
    await bootAcademicOperations(page);

    await page.goto(pageUrl('/console/academic-operations/limitations'));

    await expect(page.getByRole('heading', { name: 'Limitations', level: 1 })).toBeVisible();
    await expect(page.getByTestId('academic-operations-limitations-panel')).toContainText('Provider, Platonus, and SIS integrations are not implemented.');
    await expect(page.getByTestId('academic-operations-limitations-panel')).toContainText('Official grade publication is not implemented.');
    await expect(page.getByTestId('academic-operations-limitations-panel')).toContainText('Official transcript update is not implemented.');
    await expect(page.getByTestId('academic-operations-limitations-panel')).toContainText('Full 467-row runtime is not implemented.');
    await expect(page.getByTestId('academic-operations-limitations-panel')).toContainText('Optional detail routes remain deferred.');
    await expect(page.getByTestId('academic-operations-limitations-panel')).toContainText('Complex create and update forms remain hidden or disabled in the first runtime.');
    await expectNoForbiddenActionUi(page);
  });

  test('Scenario 11 — Permission / guard smoke', async ({ page }) => {
    const limitedPermissions = FULL_PERMISSIONS.filter((permission) => permission !== 'academic_operations.overview.read');
    await bootAcademicOperations(page, limitedPermissions);

    await page.goto(pageUrl('/console/academic-operations'));

    await expect(page.getByRole('heading', { name: /Access Denied/i })).toBeVisible();
    await expect(page.getByText("You don't have permission to view this content.")).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Academic Operations Suite' })).toHaveCount(0);
  });

  test('Scenario 12 — No-overclaim browser scan', async ({ page }) => {
    test.setTimeout(120000);
    await bootAcademicOperations(page);

    for (const route of ROUTE_EXPECTATIONS) {
      await page.goto(pageUrl(route.path));
      await expect(page.getByRole('heading', { name: route.heading, level: 1 })).toBeVisible();
      await expect(page.locator('body')).toContainText(route.boundary);
      await expect(page.getByTestId('academic-operations-page')).toBeVisible();
      await expectNoForbiddenActionUi(page);
    }

    await page.goto(pageUrl('/console/academic-operations/gradebook-metadata'));
    await expect(page.locator('body')).not.toContainText(/official transcript updated/i);
    await page.goto(pageUrl('/console/academic-operations/retakes'));
    await expect(page.locator('body')).not.toContainText(/automatic sanction enabled|dismiss student/i);
  });
});