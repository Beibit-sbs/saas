import { expect, test, type Browser, type Page, type Route } from '@playwright/test';

const API_BASE = '/api/admin/student-services';
const BFF_BASE = '/api/bff/admin/student-services';
const BASE_URL = process.env.E2E_BASE_URL ?? 'https://nginx';

const FULL_PERMISSIONS = [
  'platform.admin.read',
  'admin.student_services.read',
  'admin.student_services.write',
  'admin.student_services.assign',
  'admin.student_services.escalate',
  'admin.student_services.dashboard.read',
  'admin.student_services.audit.read',
] as const;

const RESTRICTED_PERMISSIONS = ['platform.admin.read', 'admin.student_services.read'] as const;

const REQUIRED_POSITIVE_ASSERTIONS = [
  'Human review required',
  'Readiness only',
  'Evidence metadata only',
  'No automatic approval',
  'No medical diagnosis',
  'No hidden score',
  'No fake metrics',
  'No provider/live sync',
  'No autonomous decision',
  'fake_metrics=false',
  'data_source=computed_from_student_services_support_records',
  'incomplete_data supported',
] as const;

const FORBIDDEN_DOM_LABELS = [
  'Approve hardship automatically',
  'Approve accommodation automatically',
  'Resolve complaint automatically',
  'Diagnose student',
  'Publish hidden score',
  'Submit to government/provider',
  'Generate fake evidence',
  'Mark fake service completed',
  'Brain/autonomous decision execution',
  'production-ready',
  'sales-ready',
  'GCC-ready',
  'L5/L6 ready',
] as const;

const FORBIDDEN_EXACT_TEXT_PATTERNS = [
  /^Approve hardship automatically$/i,
  /^Approve accommodation automatically$/i,
  /^Resolve complaint automatically$/i,
  /^Diagnose student$/i,
  /^Publish hidden score$/i,
  /^Submit to government\/provider$/i,
  /^Generate fake evidence$/i,
  /^Mark fake service completed$/i,
  /^Brain\/autonomous decision execution$/i,
  /^production-ready$/i,
  /^sales-ready$/i,
  /^GCC-ready$/i,
  /^L5\/L6 ready$/i,
] as const;

type RouteSpec = {
  path: string;
  routeKey:
    | 'overview'
    | 'requests'
    | 'request-detail'
    | 'cases'
    | 'case-detail'
    | 'hardship'
    | 'accommodations'
    | 'complaints'
    | 'escalations'
    | 'dashboard';
  title: string;
  requiredPermission: string;
  expectedBoundaryLabels: readonly string[];
};

const SSS_ROUTES: readonly RouteSpec[] = [
  {
    path: '/console/student-services-support',
    routeKey: 'overview',
    title: 'Student Services / Welfare / Support',
    requiredPermission: 'admin.student_services.read',
    expectedBoundaryLabels: [
      'Human review required',
      'Readiness only',
      'Evidence metadata only',
      'No automatic approval',
      'No medical diagnosis',
      'No hidden score',
      'No fake metrics',
      'No provider/live sync',
      'No autonomous decision',
      'incomplete_data supported',
    ],
  },
  {
    path: '/console/student-services-support/requests',
    routeKey: 'requests',
    title: 'Service Requests',
    requiredPermission: 'admin.student_services.read',
    expectedBoundaryLabels: ['Human review required', 'Evidence metadata only', 'No automatic approval'],
  },
  {
    path: '/console/student-services-support/requests/demo-request-001',
    routeKey: 'request-detail',
    title: 'Service Request Detail',
    requiredPermission: 'admin.student_services.read',
    expectedBoundaryLabels: ['Human review required', 'Evidence metadata only', 'No automatic approval'],
  },
  {
    path: '/console/student-services-support/cases',
    routeKey: 'cases',
    title: 'Support Cases',
    requiredPermission: 'admin.student_services.read',
    expectedBoundaryLabels: ['Human review required', 'Evidence metadata only', 'No autonomous decision'],
  },
  {
    path: '/console/student-services-support/cases/demo-case-001',
    routeKey: 'case-detail',
    title: 'Support Case Detail',
    requiredPermission: 'admin.student_services.read',
    expectedBoundaryLabels: ['Human review required', 'Evidence metadata only', 'No autonomous decision'],
  },
  {
    path: '/console/student-services-support/hardship',
    routeKey: 'hardship',
    title: 'Hardship Readiness',
    requiredPermission: 'admin.student_services.write',
    expectedBoundaryLabels: ['Human review required', 'Readiness only', 'No automatic approval'],
  },
  {
    path: '/console/student-services-support/accommodations',
    routeKey: 'accommodations',
    title: 'Accommodation Readiness',
    requiredPermission: 'admin.student_services.write',
    expectedBoundaryLabels: ['Human review required', 'Readiness only', 'No medical diagnosis'],
  },
  {
    path: '/console/student-services-support/complaints',
    routeKey: 'complaints',
    title: 'Complaints Routing',
    requiredPermission: 'admin.student_services.write',
    expectedBoundaryLabels: ['Human review required', 'Evidence metadata only', 'No autonomous decision'],
  },
  {
    path: '/console/student-services-support/escalations',
    routeKey: 'escalations',
    title: 'Escalations',
    requiredPermission: 'admin.student_services.escalate',
    expectedBoundaryLabels: ['Human review required', 'Evidence metadata only', 'No autonomous decision'],
  },
  {
    path: '/console/student-services-support/dashboard',
    routeKey: 'dashboard',
    title: 'Student Support Dashboard',
    requiredPermission: 'admin.student_services.dashboard.read',
    expectedBoundaryLabels: [
      'fake_metrics=false',
      'provider_live_enabled=false',
      'autonomous_decision_enabled=false',
      'hidden_score_present=false',
      'incomplete_data supported',
    ],
  },
] as const;

const BASE_FLAGS = {
  fake_metrics: false,
  provider_live_enabled: false,
  autonomous_decision_enabled: false,
  hidden_score_present: false,
  human_review_required: true,
  incomplete_data: true,
  data_source: 'computed_from_student_services_support_records',
} as const;

const fullAccessFixture = {
  id: 'sss-admin-01',
  sub: 'sss-admin-01',
  tenantId: 1,
  email: 'sss-admin@example.edu',
  displayName: 'Student Services Admin',
  role: 'admin',
  roles: ['admin'],
  permissions: [...FULL_PERMISSIONS],
};

const restrictedFixture = {
  id: 'sss-restricted-01',
  sub: 'sss-restricted-01',
  tenantId: 1,
  email: 'sss-restricted@example.edu',
  displayName: 'Student Services Restricted User',
  role: 'viewer',
  roles: ['viewer'],
  permissions: [...RESTRICTED_PERMISSIONS],
};

function pageUrl(path: string) {
  return new URL(path, BASE_URL).toString();
}

function makeRecord(id: number, extra: Record<string, unknown> = {}) {
  return {
    id,
    tenant_id: 1,
    ...BASE_FLAGS,
    ...extra,
  };
}

const SSS_FIXTURES = {
  health: { ok: true, module: 'student_services_support', ...BASE_FLAGS },
  requests: {
    items: [
      makeRecord(1, {
        request_type: 'general_support',
        status: 'submitted',
        support_priority: 'medium',
        student_id: 'DEMO-STUDENT-001',
        subject: 'Support request',
        description: 'Metadata-only support request.',
      }),
    ],
  },
  requestById: {
    item: makeRecord(1, {
      request_type: 'general_support',
      status: 'submitted',
      support_priority: 'medium',
      student_id: 'DEMO-STUDENT-001',
      subject: 'Support request detail',
      description: 'Evidence metadata only.',
    }),
  },
  cases: {
    items: [
      makeRecord(1, {
        case_type: 'support_case',
        status: 'under_review',
        request_id: 1,
        title: 'Support case',
      }),
    ],
  },
  caseById: {
    item: makeRecord(1, {
      case_type: 'support_case',
      status: 'under_review',
      request_id: 1,
      title: 'Support case detail',
    }),
  },
  caseNotes: {
    items: [
      makeRecord(1, {
        case_id: 1,
        note: 'Case note metadata entry.',
      }),
    ],
  },
  caseEvidence: {
    items: [
      makeRecord(1, {
        case_id: 1,
        evidence_type: 'document_metadata',
        source_available: false,
        limitations: 'Evidence metadata only.',
      }),
    ],
  },
  hardship: {
    item: makeRecord(1, {
      request_id: 1,
      readiness_status: 'ready_for_human_review',
      missing_evidence: ['supporting_document_metadata'],
      recommended_next_step: 'Human reviewer confirms evidence sufficiency.',
    }),
  },
  accommodations: {
    item: makeRecord(1, {
      request_id: 1,
      readiness_status: 'ready_for_human_review',
      missing_evidence: ['supporting_document_metadata'],
      recommended_next_step: 'Human reviewer confirms evidence sufficiency.',
    }),
  },
  complaints: {
    item: makeRecord(1, {
      request_id: 1,
      status: 'routed',
      routed_to: 'Student Affairs',
      complaint_summary: 'Complaint metadata summary.',
    }),
  },
  escalations: {
    item: makeRecord(1, {
      case_id: 1,
      escalation_status: 'pending',
      reason: 'Human escalation metadata reason.',
    }),
  },
  dashboard: {
    tenant_id: 1,
    module: 'student_services_support',
    contract_version: 'A-042.4-E2E',
    runtime_mode: 'METADATA_EVIDENCE_READINESS_HUMAN_REVIEW_ONLY',
    ...BASE_FLAGS,
    open_requests: 1,
    open_support_cases: 1,
    escalated_cases: 1,
    hardship_readiness_counts: { ready_for_human_review: 1 },
    accommodation_readiness_counts: { ready_for_human_review: 1 },
    complaint_counts: { routed: 1 },
  },
};

function parsePath(input: string) {
  try {
    return new URL(input).pathname;
  } catch {
    return input;
  }
}

function matchSssFixture(pathname: string) {
  if (pathname === `${API_BASE}/health` || pathname === `${BFF_BASE}/health`) return SSS_FIXTURES.health;
  if (pathname === `${API_BASE}/requests` || pathname === `${BFF_BASE}/requests`) return SSS_FIXTURES.requests;
  if (/^\/(api|api\/bff)\/admin\/student-services\/requests\/[^/]+$/.test(pathname)) return SSS_FIXTURES.requestById;
  if (pathname === `${API_BASE}/cases` || pathname === `${BFF_BASE}/cases`) return SSS_FIXTURES.cases;
  if (/^\/(api|api\/bff)\/admin\/student-services\/cases\/[^/]+$/.test(pathname)) return SSS_FIXTURES.caseById;
  if (/^\/(api|api\/bff)\/admin\/student-services\/cases\/[^/]+\/notes$/.test(pathname)) return SSS_FIXTURES.caseNotes;
  if (/^\/(api|api\/bff)\/admin\/student-services\/cases\/[^/]+\/evidence$/.test(pathname)) return SSS_FIXTURES.caseEvidence;
  if (pathname === `${API_BASE}/hardship` || pathname === `${BFF_BASE}/hardship`) return SSS_FIXTURES.hardship;
  if (pathname === `${API_BASE}/accommodations` || pathname === `${BFF_BASE}/accommodations`) return SSS_FIXTURES.accommodations;
  if (pathname === `${API_BASE}/complaints` || pathname === `${BFF_BASE}/complaints`) return SSS_FIXTURES.complaints;
  if (pathname === `${API_BASE}/escalations` || pathname === `${BFF_BASE}/escalations`) return SSS_FIXTURES.escalations;
  if (pathname === `${API_BASE}/dashboard/summary` || pathname === `${BFF_BASE}/dashboard/summary`) return SSS_FIXTURES.dashboard;
  return null;
}

async function forceEnglishLocale(page: Page) {
  const parsedUrl = new URL(BASE_URL);
  const cookieOrigins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  await page.context().addCookies(
    Array.from(cookieOrigins).map((origin) => ({
      name: 'app.locale',
      value: 'en',
      url: origin,
      httpOnly: false,
      secure: new URL(origin).protocol === 'https:',
      sameSite: 'Lax' as const,
    })),
  );

  await page.addInitScript(() => {
    document.cookie = 'app.locale=en; Path=/; SameSite=Lax';
    window.localStorage.setItem('app.language', 'en');
  });
}

async function stubSharedBootstrap(page: Page) {
  await page.route('**/api/auth/csrf*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ csrfToken: 'student-services-support-csrf-token' }),
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
            tenantCode: 'student-services-support-demo',
            tenantName: 'Student Services Support Demo Tenant',
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

async function stubAuth(page: Page, userFixture: typeof fullAccessFixture | typeof restrictedFixture) {
  const parsedUrl = new URL(BASE_URL);
  const cookieOrigins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  const payloadJson = JSON.stringify({
    sub: userFixture.sub,
    display_name: userFixture.displayName,
    roles: userFixture.roles,
    permissions: userFixture.permissions,
    tenant_id: userFixture.tenantId,
    exp: Math.floor(Date.now() / 1000) + 3600,
  });
  const payload = Buffer.from(payloadJson).toString('base64url');
  const fakeToken = `fakeheader.${payload}.fakesig`;

  await page.context().addCookies(
    Array.from(cookieOrigins).flatMap((origin) => {
      const secure = new URL(origin).protocol === 'https:';
      return [
        { name: 'admin_token', value: fakeToken, url: origin, httpOnly: true, secure, sameSite: 'Lax' as const },
        { name: 'app_access_token', value: fakeToken, url: origin, httpOnly: true, secure, sameSite: 'Lax' as const },
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
          user: userFixture,
        }),
      });
    });
  }
}

async function stubStudentServicesApi(page: Page) {
  const fulfillRoute = async (route: Route) => {
    const request = route.request();
    const pathname = parsePath(request.url());
    const payload = matchSssFixture(pathname);

    const respond = async (body: unknown, status = 200) => {
      await route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(body),
      });
    };

    if (payload) {
      await respond(payload);
      return;
    }

    if (request.method() === 'POST' || request.method() === 'PATCH') {
      await respond({
        ok: true,
        accepted: true,
        mutation_applied: false,
        mode: 'metadata_evidence_readiness_only',
        ...BASE_FLAGS,
      });
      return;
    }

    await respond({ detail: `Unhandled Student Services stub path: ${pathname}` }, 404);
  };

  await page.route(`**${API_BASE}**`, fulfillRoute);
  await page.route(`**${BFF_BASE}**`, fulfillRoute);
}

async function setAuthenticatedAdmin(page: Page) {
  await forceEnglishLocale(page);
  await stubSharedBootstrap(page);
  await stubAuth(page, fullAccessFixture);
  await stubStudentServicesApi(page);
}

async function setRestrictedUser(page: Page) {
  await forceEnglishLocale(page);
  await stubSharedBootstrap(page);
  await stubAuth(page, restrictedFixture);
  await stubStudentServicesApi(page);
}

async function gotoSssRoute(page: Page, path: string) {
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      await page.goto(pageUrl(path), { waitUntil: 'domcontentloaded' });
      return;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const transient = /ERR_ABORTED|frame was detached/i.test(message);
      if (!transient || attempt === 2) {
        throw error;
      }
    }
  }
}

async function expectForbiddenDomAbsent(page: Page) {
  for (const label of FORBIDDEN_DOM_LABELS) {
    const exact = new RegExp(`^${label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}$`, 'i');
    await expect(page.getByRole('button', { name: exact })).toHaveCount(0);
    await expect(page.getByRole('link', { name: exact })).toHaveCount(0);
    await expect(page.getByText(exact)).toHaveCount(0);
  }

  for (const pattern of FORBIDDEN_EXACT_TEXT_PATTERNS) {
    await expect(page.getByText(pattern)).toHaveCount(0);
  }
}

async function expectRouteShell(page: Page, route: RouteSpec) {
  await expect(page.getByTestId('sss-page-shell')).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('heading', { level: 1, name: route.title })).toBeVisible({ timeout: 15_000 });
  await expect(page.locator('nav[aria-label="Student services support navigation"] a')).toHaveCount(10, { timeout: 15_000 });
  await expect(page.getByTestId(`sss-page-${route.routeKey}`)).toBeVisible({ timeout: 15_000 });
  await expect(page.getByTestId('sss-route-contract-panel')).toContainText(route.requiredPermission);
}

async function openAndAssertRoute(page: Page, route: RouteSpec) {
  await gotoSssRoute(page, route.path);
  await expectRouteShell(page, route);

  for (const label of route.expectedBoundaryLabels) {
    await expect(page.locator('body')).toContainText(label);
  }

  await expect(page.getByTestId('sss-incomplete-data-state')).toContainText('incomplete_data supported');
  await expect(page.getByTestId('sss-tenant-fail-closed-state')).toContainText('Tenant fail-closed / not found boundary active.');
  await expect(page.getByTestId('sss-no-overclaim-footer')).toContainText('No production/sales/GCC/L5/L6 claim.');

  await expectForbiddenDomAbsent(page);
}

async function visitRouteWithFreshPage(browser: Browser, route: RouteSpec) {
  const page = await browser.newPage({ ignoreHTTPSErrors: true });

  try {
    page.setDefaultTimeout(15_000);
    page.setDefaultNavigationTimeout(15_000);
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, route);
  } finally {
    await page.close();
  }
}

async function expectPermissionDeniedOrSafeFallback(page: Page) {
  const deniedState = page.getByTestId('sss-permission-denied-state');
  const accessDeniedHeading = page.getByRole('heading', { name: /Access Denied/i });

  if (await deniedState.count()) {
    await expect(deniedState).toBeVisible();
  } else if (await accessDeniedHeading.count()) {
    await expect(accessDeniedHeading).toBeVisible();
    await expect(page.locator('body')).toContainText(/fail-closed|permission|available only to platform administrators/i);
  } else {
    await expect(page.locator('body')).toContainText(/fail-closed|permission|available only to platform administrators/i);
  }

  await expect(page.getByTestId('sss-dashboard-summary')).toHaveCount(0);
  await expect(page.getByTestId('sss-hardship-panel')).toHaveCount(0);
  await expect(page.getByTestId('sss-accommodation-panel')).toHaveCount(0);
  await expect(page.getByTestId('sss-escalation-panel')).toHaveCount(0);
  await expectForbiddenDomAbsent(page);
}

test.describe('A-042.4 Student Services / Welfare / Support route coverage', () => {
  test.describe.configure({ timeout: 220_000 });

  test('SSS-E2E-GROUP-00 route inventory has exactly 10 routes', async () => {
    expect(SSS_ROUTES).toHaveLength(10);
  });

  test('SSS-E2E-GROUP-01 full-access admin can visit all 10 routes', async ({ browser }) => {
    for (const route of SSS_ROUTES) {
      await test.step(`full-access ${route.routeKey} ${route.path} -> ${route.title}`, async () => {
        await visitRouteWithFreshPage(browser, route);
      });
    }
  });
});

test.describe('A-042.4 Student Services / Welfare / Support scenario groups', () => {
  test.describe.configure({ timeout: 220_000 });

  test.beforeEach(async ({ page }) => {
    page.setDefaultTimeout(15_000);
    page.setDefaultNavigationTimeout(15_000);
    await setAuthenticatedAdmin(page);
  });

  test('SSS-E2E-GROUP-02 shell loads with boundary banner', async ({ page }) => {
    await gotoSssRoute(page, SSS_ROUTES[0].path);
    await expect(page.getByTestId('sss-page-shell')).toBeVisible();
    await expect(page.getByTestId('sss-boundary-banner')).toBeVisible();
    await expect(page.locator('body')).toContainText('Student Services / Welfare / Support Suite');
    await expect(page.locator('body')).toContainText('Human review required');
  });

  test('SSS-E2E-GROUP-03 requests page loads', async ({ page }) => {
    await gotoSssRoute(page, SSS_ROUTES[1].path);
    await expect(page.getByTestId('sss-request-list')).toBeVisible();
    await expect(page.locator('body')).toContainText('Service Requests');
  });

  test('SSS-E2E-GROUP-04 request detail page loads', async ({ page }) => {
    await gotoSssRoute(page, SSS_ROUTES[2].path);
    await expect(page.getByTestId('sss-request-detail')).toBeVisible();
    await expect(page.getByTestId('sss-assignment-panel')).toBeVisible();
  });

  test('SSS-E2E-GROUP-05 case list page loads', async ({ page }) => {
    await gotoSssRoute(page, SSS_ROUTES[3].path);
    await expect(page.getByTestId('sss-case-list')).toBeVisible();
    await expect(page.locator('body')).toContainText('Support Cases');
  });

  test('SSS-E2E-GROUP-06 case detail page loads', async ({ page }) => {
    await gotoSssRoute(page, SSS_ROUTES[4].path);
    await expect(page.getByTestId('sss-case-detail')).toBeVisible();
    await expect(page.getByTestId('sss-note-timeline')).toBeVisible();
    await expect(page.getByTestId('sss-evidence-panel')).toBeVisible();
  });

  test('SSS-E2E-GROUP-07 hardship readiness page loads', async ({ page }) => {
    await gotoSssRoute(page, SSS_ROUTES[5].path);
    await expect(page.getByTestId('sss-hardship-panel')).toBeVisible();
    await expect(page.locator('body')).toContainText('Readiness only');
  });

  test('SSS-E2E-GROUP-08 accommodation readiness page loads', async ({ page }) => {
    await gotoSssRoute(page, SSS_ROUTES[6].path);
    await expect(page.getByTestId('sss-accommodation-panel')).toBeVisible();
    await expect(page.locator('body')).toContainText('No medical diagnosis');
  });

  test('SSS-E2E-GROUP-09 complaint routing page loads', async ({ page }) => {
    await gotoSssRoute(page, SSS_ROUTES[7].path);
    await expect(page.getByTestId('sss-complaint-panel')).toBeVisible();
    await expect(page.locator('body')).toContainText('Evidence metadata only');
  });

  test('SSS-E2E-GROUP-10 escalation page loads', async ({ page }) => {
    await gotoSssRoute(page, SSS_ROUTES[8].path);
    await expect(page.getByTestId('sss-escalation-panel')).toBeVisible();
    await expect(page.locator('body')).toContainText('No autonomous decision');
  });

  test('SSS-E2E-GROUP-11 dashboard page loads', async ({ page }) => {
    await gotoSssRoute(page, SSS_ROUTES[9].path);
    await expect(page.getByTestId('sss-dashboard-summary')).toBeVisible();
    await expect(page.locator('body')).toContainText('Student Support Dashboard');
  });

  test('SSS-E2E-GROUP-12 loading/empty/error states contract markers', async ({ page }) => {
    await gotoSssRoute(page, SSS_ROUTES[0].path);
    await expect(page.getByTestId('sss-incomplete-data-state')).toBeVisible();
    await expect(page.getByTestId('sss-loading-state')).toHaveCount(0);
    await expect(page.getByTestId('sss-error-state')).toHaveCount(0);
    await expect(page.getByTestId('sss-requests-empty')).toHaveCount(0);
    await expect(page.getByTestId('sss-cases-empty')).toHaveCount(0);
  });

  test('SSS-E2E-GROUP-13 dashboard contract labels', async ({ page }) => {
    await gotoSssRoute(page, SSS_ROUTES[9].path);
    await expect(page.locator('body')).toContainText('fake_metrics=false');
    await expect(page.locator('body')).toContainText('data_source=computed_from_student_services_support_records');
    await expect(page.locator('body')).toContainText('incomplete_data supported');
    await expect(page.locator('body')).toContainText('No hidden student score. No discriminatory risk score.');
  });

  test('SSS-E2E-GROUP-14 no-overclaim and forbidden UI assertions', async ({ page }) => {
    await gotoSssRoute(page, SSS_ROUTES[0].path);

    for (const label of REQUIRED_POSITIVE_ASSERTIONS) {
      const targetPath = label === 'fake_metrics=false' || label === 'data_source=computed_from_student_services_support_records'
        ? SSS_ROUTES[9].path
        : SSS_ROUTES[0].path;
      if (page.url() !== pageUrl(targetPath)) {
        await gotoSssRoute(page, targetPath);
      }
      await expect(page.locator('body')).toContainText(label);
    }

    await expect(page.getByTestId('sss-no-overclaim-footer')).toContainText('No automatic hardship approval UI.');
    await expect(page.getByTestId('sss-no-overclaim-footer')).toContainText('No automatic accommodation approval UI.');
    await expect(page.getByTestId('sss-no-overclaim-footer')).toContainText('No automatic complaint resolution UI.');
    await expect(page.getByTestId('sss-no-overclaim-footer')).toContainText('No diagnosis UI.');
    await expectForbiddenDomAbsent(page);
  });

  test('SSS-E2E-GROUP-15 BFF stubbing behavior', async ({ page }) => {
    await gotoSssRoute(page, SSS_ROUTES[0].path);

    const dashboardData = await page.evaluate(async () => {
      const res = await fetch('/api/admin/student-services/dashboard/summary');
      return res.json();
    });

    expect(dashboardData.fake_metrics).toBe(false);
    expect(dashboardData.data_source).toBe('computed_from_student_services_support_records');
    expect(dashboardData.incomplete_data).toBe(true);
  });
});

test.describe('A-042.4 Student Services / Welfare / Support permission-denied', () => {
  test('SSS-E2E-GROUP-16 permission-denied state for restricted user', async ({ page }) => {
    page.setDefaultTimeout(15_000);
    page.setDefaultNavigationTimeout(15_000);
    await setRestrictedUser(page);

    const protectedPaths = [
      '/console/student-services-support/hardship',
      '/console/student-services-support/accommodations',
      '/console/student-services-support/complaints',
      '/console/student-services-support/escalations',
      '/console/student-services-support/dashboard',
    ];

    for (const path of protectedPaths) {
      await test.step(`restricted-user ${path}`, async () => {
        await gotoSssRoute(page, path);
        await expectPermissionDeniedOrSafeFallback(page);
      });
    }
  });
});
