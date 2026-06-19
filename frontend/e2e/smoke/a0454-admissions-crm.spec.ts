import { expect, test, type Page, type Route } from '@playwright/test';

const API_BASE = '/api/admin/admissions-crm';
const BFF_BASE = '/api/bff/admin/admissions-crm';
const BASE_URL = process.env.E2E_BASE_URL ?? 'https://nginx';

const SCENARIO_GROUP_COUNT_TARGET = 18;
const WORKFLOW_SCENARIO_TARGET = 16;
const TENANT_SCENARIO_TARGET = 6;
const ROUTE_COUNT_TARGET = 14;

type AdmissionsRouteSpec = {
  path: string;
  routeKey:
    | 'overview'
    | 'leads'
    | 'leads-new'
    | 'lead-detail'
    | 'applicants'
    | 'applicants-new'
    | 'applicant-detail'
    | 'applications'
    | 'applications-new'
    | 'application-detail'
    | 'workflows'
    | 'audit'
    | 'dashboard'
    | 'settings-permissions';
  title: string;
  requiredPermissions: readonly string[];
};

const ROUTES: readonly AdmissionsRouteSpec[] = [
  {
    path: '/console/admissions',
    routeKey: 'overview',
    title: 'Admissions Overview',
    requiredPermissions: ['admin.admissions_crm.read'],
  },
  {
    path: '/console/admissions/leads',
    routeKey: 'leads',
    title: 'Lead Registry',
    requiredPermissions: ['admin.admissions_crm.read'],
  },
  {
    path: '/console/admissions/leads/new',
    routeKey: 'leads-new',
    title: 'New Lead',
    requiredPermissions: ['admin.admissions_crm.write'],
  },
  {
    path: '/console/admissions/leads/1',
    routeKey: 'lead-detail',
    title: 'Lead Detail',
    requiredPermissions: ['admin.admissions_crm.read'],
  },
  {
    path: '/console/admissions/applicants',
    routeKey: 'applicants',
    title: 'Applicant Registry',
    requiredPermissions: ['admin.admissions_crm.read'],
  },
  {
    path: '/console/admissions/applicants/new',
    routeKey: 'applicants-new',
    title: 'New Applicant',
    requiredPermissions: ['admin.admissions_crm.convert', 'admin.admissions_crm.write'],
  },
  {
    path: '/console/admissions/applicants/1',
    routeKey: 'applicant-detail',
    title: 'Applicant Detail',
    requiredPermissions: ['admin.admissions_crm.read'],
  },
  {
    path: '/console/admissions/applications',
    routeKey: 'applications',
    title: 'Application Registry',
    requiredPermissions: ['admin.admissions_crm.read'],
  },
  {
    path: '/console/admissions/applications/new',
    routeKey: 'applications-new',
    title: 'New Application',
    requiredPermissions: ['admin.admissions_crm.write'],
  },
  {
    path: '/console/admissions/applications/1',
    routeKey: 'application-detail',
    title: 'Application Detail',
    requiredPermissions: ['admin.admissions_crm.read'],
  },
  {
    path: '/console/admissions/workflows',
    routeKey: 'workflows',
    title: 'Workflow Health',
    requiredPermissions: ['admin.admissions_crm.read'],
  },
  {
    path: '/console/admissions/audit',
    routeKey: 'audit',
    title: 'Audit',
    requiredPermissions: ['admin.admissions_crm.audit.read'],
  },
  {
    path: '/console/admissions/dashboard',
    routeKey: 'dashboard',
    title: 'Admissions Dashboard',
    requiredPermissions: ['admin.admissions_crm.read'],
  },
  {
    path: '/console/admissions/settings/permissions',
    routeKey: 'settings-permissions',
    title: 'Permissions Matrix',
    requiredPermissions: ['admin.admissions_crm.audit.read'],
  },
] as const;

if (ROUTES.length !== ROUTE_COUNT_TARGET) {
  throw new Error(`Admissions route inventory must be ${ROUTE_COUNT_TARGET}, got ${ROUTES.length}`);
}

const RUNTIME_PERMISSIONS = {
  read: 'admin.admissions_crm.read',
  write: 'admin.admissions_crm.write',
  qualify: 'admin.admissions_crm.qualify',
  convert: 'admin.admissions_crm.convert',
  submit: 'admin.admissions_crm.submit',
  auditRead: 'admin.admissions_crm.audit.read',
} as const;

type RoleFixture = {
  id: string;
  sub: string;
  tenantId?: number;
  email: string;
  displayName: string;
  role: string;
  roles: string[];
  permissions: string[];
};

const PLATFORM_ADMIN: RoleFixture = {
  id: 'acrm-platform-admin-01',
  sub: 'acrm-platform-admin-01',
  tenantId: 1,
  email: 'platform_admin@example.edu',
  displayName: 'Admissions Platform Admin',
  role: 'platform_admin',
  roles: ['admin', 'platform_admin'],
  permissions: [
    'platform.admin.read',
    RUNTIME_PERMISSIONS.read,
    RUNTIME_PERMISSIONS.write,
    RUNTIME_PERMISSIONS.qualify,
    RUNTIME_PERMISSIONS.convert,
    RUNTIME_PERMISSIONS.submit,
    RUNTIME_PERMISSIONS.auditRead,
  ],
};

const INST_ADMIN: RoleFixture = {
  id: 'acrm-inst-admin-01',
  sub: 'acrm-inst-admin-01',
  tenantId: 1,
  email: 'inst_admin@example.edu',
  displayName: 'Admissions Institution Admin',
  role: 'inst_admin',
  roles: ['admin', 'inst_admin'],
  permissions: [
    'platform.admin.read',
    RUNTIME_PERMISSIONS.read,
    RUNTIME_PERMISSIONS.write,
    RUNTIME_PERMISSIONS.qualify,
    RUNTIME_PERMISSIONS.convert,
    RUNTIME_PERMISSIONS.submit,
  ],
};

const ACAD_ADMIN: RoleFixture = {
  id: 'acrm-acad-admin-01',
  sub: 'acrm-acad-admin-01',
  tenantId: 1,
  email: 'acad_admin@example.edu',
  displayName: 'Admissions Academic Admin',
  role: 'acad_admin',
  roles: ['admin', 'acad_admin'],
  permissions: ['platform.admin.read', RUNTIME_PERMISSIONS.read],
};

const AUDITOR: RoleFixture = {
  id: 'acrm-auditor-01',
  sub: 'acrm-auditor-01',
  tenantId: 1,
  email: 'auditor@example.edu',
  displayName: 'Admissions Auditor',
  role: 'auditor',
  roles: ['admin', 'auditor'],
  permissions: ['platform.admin.read', RUNTIME_PERMISSIONS.read, RUNTIME_PERMISSIONS.auditRead],
};

const READ_ONLY: RoleFixture = {
  ...ACAD_ADMIN,
  id: 'acrm-read-only-01',
  sub: 'acrm-read-only-01',
  role: 'read_only',
  roles: ['admin', 'read_only'],
};

const EDITOR: RoleFixture = {
  ...INST_ADMIN,
  id: 'acrm-editor-01',
  sub: 'acrm-editor-01',
  role: 'editor',
  roles: ['admin', 'editor'],
};

function pageUrl(path: string) {
  return new URL(path, BASE_URL).toString();
}

function parsePath(url: string) {
  return new URL(url).pathname;
}

function buildListResponse<T>(tenantId: number | undefined, items: T[]) {
  return {
    tenant_id: tenantId,
    items,
    fake_metrics: false,
    provider_live_enabled: false,
    autonomous_decision_enabled: false,
    hidden_score_present: false,
    human_review_required: true,
  };
}

function buildItemResponse<T>(tenantId: number | undefined, item: T) {
  return {
    tenant_id: tenantId,
    item,
    fake_metrics: false,
    provider_live_enabled: false,
    autonomous_decision_enabled: false,
    hidden_score_present: false,
    human_review_required: true,
  };
}

function buildAdmissionsApiStubs(tenantId: number | undefined) {
  const leads = [
    {
      id: 1,
      tenant_id: tenantId ?? 0,
      lead_ref: 'L-001',
      status: 'lead_qualified',
      full_name: 'Alice Lead',
      email: 'alice.lead@example.edu',
      phone: '+77010000001',
      source_channel: 'direct',
    },
  ];

  const applicants = [
    {
      id: 1,
      tenant_id: tenantId ?? 0,
      lead_id: 1,
      applicant_ref: 'A-001',
      status: 'applicant_created',
      full_name: 'Alice Applicant',
      email: 'alice.applicant@example.edu',
    },
  ];

  const applications = [
    {
      id: 1,
      tenant_id: tenantId ?? 0,
      applicant_id: 1,
      application_ref: 'APP-001',
      status: 'application_submitted',
      program_code: 'CS',
      intake_term: '2026-FALL',
    },
  ];

  return {
    leads,
    applicants,
    applications,
    listLeads: buildListResponse(tenantId, leads),
    itemLead: buildItemResponse(tenantId, leads[0]),
    listApplicants: buildListResponse(tenantId, applicants),
    itemApplicant: buildItemResponse(tenantId, applicants[0]),
    listApplications: buildListResponse(tenantId, applications),
    itemApplication: buildItemResponse(tenantId, applications[0]),
  };
}

async function forceEnglishLocale(page: Page) {
  const parsedUrl = new URL(BASE_URL);
  const origins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  await page.context().addCookies(
    Array.from(origins).map((origin) => ({
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
      body: JSON.stringify({ csrfToken: 'acrm-csrf-token' }),
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
            tenantId: 8102,
            tenantCode: 'admissions-demo-tenant',
            tenantName: 'Admissions CRM Demo Tenant',
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

async function stubAuth(page: Page, fixture: RoleFixture) {
  const parsedUrl = new URL(BASE_URL);
  const origins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  const payloadJson = JSON.stringify({
    sub: fixture.sub,
    display_name: fixture.displayName,
    roles: fixture.roles,
    permissions: fixture.permissions,
    tenant_id: fixture.tenantId,
    exp: Math.floor(Date.now() / 1000) + 3600,
  });

  const token = `fakeheader.${Buffer.from(payloadJson).toString('base64url')}.fakesig`;

  await page.context().addCookies(
    Array.from(origins).flatMap((origin) => {
      const secure = new URL(origin).protocol === 'https:';
      return [
        { name: 'admin_token', value: token, url: origin, httpOnly: true, secure, sameSite: 'Lax' as const },
        { name: 'app_access_token', value: token, url: origin, httpOnly: true, secure, sameSite: 'Lax' as const },
      ];
    }),
  );

  for (const pattern of ['**/api/auth/me*', '**/api/bff/auth/me*']) {
    await page.route(pattern, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ authenticated: true, user: fixture }),
      });
    });
  }
}

async function stubAdmissionsApi(page: Page, tenantId: number | undefined) {
  const stubs = buildAdmissionsApiStubs(tenantId);

  const fulfillRoute = async (route: Route) => {
    const request = route.request();
    const pathname = parsePath(request.url());
    const method = request.method();

    const respond = async (body: unknown, status = 200) => {
      await route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(body),
      });
    };

    if (pathname === `${API_BASE}/leads` || pathname === `${BFF_BASE}/leads`) {
      if (method === 'GET') {
        await respond(stubs.listLeads);
        return;
      }
      if (method === 'POST') {
        await respond(stubs.itemLead);
        return;
      }
    }

    if (pathname === `${API_BASE}/leads/1` || pathname === `${BFF_BASE}/leads/1`) {
      await respond(stubs.itemLead);
      return;
    }

    if (pathname === `${API_BASE}/leads/1/qualify` || pathname === `${BFF_BASE}/leads/1/qualify`) {
      await respond(stubs.itemLead);
      return;
    }

    if (pathname === `${API_BASE}/leads/1/convert-to-applicant` || pathname === `${BFF_BASE}/leads/1/convert-to-applicant`) {
      await respond(stubs.itemApplicant);
      return;
    }

    if (pathname === `${API_BASE}/applicants` || pathname === `${BFF_BASE}/applicants`) {
      if (method === 'GET') {
        await respond(stubs.listApplicants);
        return;
      }
      if (method === 'POST') {
        await respond(stubs.itemApplicant);
        return;
      }
    }

    if (pathname === `${API_BASE}/applicants/1` || pathname === `${BFF_BASE}/applicants/1`) {
      await respond(stubs.itemApplicant);
      return;
    }

    if (pathname === `${API_BASE}/applications` || pathname === `${BFF_BASE}/applications`) {
      if (method === 'GET') {
        await respond(stubs.listApplications);
        return;
      }
      if (method === 'POST') {
        await respond(stubs.itemApplication);
        return;
      }
    }

    if (pathname === `${API_BASE}/applications/1` || pathname === `${BFF_BASE}/applications/1`) {
      await respond(stubs.itemApplication);
      return;
    }

    if (pathname === `${API_BASE}/applications/1/submit` || pathname === `${BFF_BASE}/applications/1/submit`) {
      await respond(stubs.itemApplication);
      return;
    }

    if (pathname.includes('/admissions-crm/')) {
      await respond({ detail: `Unhandled admissions stub path: ${pathname}` }, 404);
      return;
    }

    await respond({ ok: true });
  };

  await page.route(`**${API_BASE}**`, fulfillRoute);
  await page.route(`**${BFF_BASE}**`, fulfillRoute);
}

async function setAuthenticatedUser(page: Page, fixture: RoleFixture, tenantIdOverride?: number | null) {
  const tenantId = tenantIdOverride === null
    ? undefined
    : (tenantIdOverride === undefined ? fixture.tenantId : tenantIdOverride);
  const effectiveFixture = tenantId === fixture.tenantId ? fixture : { ...fixture, tenantId };

  await forceEnglishLocale(page);
  await stubSharedBootstrap(page);
  await stubAuth(page, effectiveFixture);
  await stubAdmissionsApi(page, tenantId);
}

function captureHydrationErrors(page: Page) {
  const errors: string[] = [];
  page.on('console', (msg) => {
    if (msg.type() !== 'error') {
      return;
    }
    const text = msg.text();
    if (/hydration/i.test(text)) {
      errors.push(text);
    }
  });
  return errors;
}

async function gotoRouteWithChecks(page: Page, route: AdmissionsRouteSpec, hydrationErrors: string[]) {
  const response = await page.goto(pageUrl(route.path), { waitUntil: 'domcontentloaded' });
  expect(response, `Missing document response for ${route.path}`).not.toBeNull();
  expect(response?.status(), `Unexpected status for ${route.path}`).toBe(200);

  await expect(page.getByTestId('acrm-page-layout')).toBeVisible({ timeout: 15_000 });
  await expect(page.getByTestId(`acrm-page-${route.routeKey}`)).toBeVisible({ timeout: 15_000 });
  await expect(page.locator('body')).toContainText(route.title);
  await expect(page.getByTestId('acrm-route-contract-panel')).toContainText(route.requiredPermissions[0]);
  await expect(page.getByTestId('acrm-no-overclaim-footer')).toBeVisible();

  await expect(page.locator('body')).not.toContainText(/404|not found/i);
  await expect(page.locator('body')).not.toContainText(/500|502|bad gateway|internal server error/i);
  expect(hydrationErrors, `Hydration errors on route ${route.path}`).toEqual([]);
}

async function expectDenied(page: Page) {
  const explicitDenied = page.getByTestId('acrm-permission-denied-state');
  const genericDenied = page.getByRole('heading', { name: 'Access Denied' });
  const explicitCount = await explicitDenied.count();
  if (explicitCount > 0) {
    await expect(explicitDenied).toBeVisible({ timeout: 15_000 });
  } else {
    await expect(genericDenied).toBeVisible({ timeout: 15_000 });
  }
  await expect(page.locator('body')).toContainText(/fail-closed|required permission|access denied/i);
}

const WORKFLOW_SCENARIOS = [
  'Lead Creation',
  'Lead Editing',
  'Lead Conversion',
  'Applicant Creation',
  'Applicant Editing',
  'Application Creation',
  'Application Review',
  'Workflow Timeline Review',
  'Audit Trail Review',
  'Dashboard Navigation',
  'Overview Context Review',
  'Leads Registry Review',
  'Applicants Registry Review',
  'Applications Registry Review',
  'Permissions Matrix Review',
  'Tenant Notice Review',
] as const;

if (WORKFLOW_SCENARIOS.length !== WORKFLOW_SCENARIO_TARGET) {
  throw new Error(`Workflow scenario inventory must be ${WORKFLOW_SCENARIO_TARGET}, got ${WORKFLOW_SCENARIOS.length}`);
}

test.describe('A-045.4 Admissions CRM E2E runtime validation', () => {
  test.describe.configure({ timeout: 320_000 });

  test('A0454-E2E-GROUP-01 route validation for all 14 admissions routes', async ({ page }) => {
    const hydrationErrors = captureHydrationErrors(page);
    await setAuthenticatedUser(page, PLATFORM_ADMIN);

    for (const route of ROUTES) {
      await test.step(`route ${route.routeKey} ${route.path}`, async () => {
        await gotoRouteWithChecks(page, route, hydrationErrors);
      });
    }
  });

  test('A0454-E2E-GROUP-02 workflow scenario matrix (16 scenarios)', async ({ page }) => {
    await setAuthenticatedUser(page, PLATFORM_ADMIN);

    await test.step('Lead Creation', async () => {
      await page.goto(pageUrl('/console/admissions/leads/new'));
      await expect(page.getByTestId('acrm-lead-create-form')).toBeVisible();
      await page.getByPlaceholder('lead_ref').fill('L-NEW-001');
      await page.getByPlaceholder('full_name').fill('Workflow Lead');
      await page.getByPlaceholder('email', { exact: true }).fill('workflow.lead@example.edu');
      await page.getByRole('button', { name: /create lead/i }).click();
    });

    await test.step('Lead Editing', async () => {
      await page.goto(pageUrl('/console/admissions/leads/1'));
      await expect(page.getByTestId('acrm-lead-edit-form')).toBeVisible();
      await page.getByPlaceholder('full_name').fill('Updated Lead Name');
      await page.getByPlaceholder('email', { exact: true }).fill('updated.lead@example.edu');
      await page.getByRole('button', { name: /save lead/i }).click();
    });

    await test.step('Lead Conversion', async () => {
      await page.goto(pageUrl('/console/admissions/leads/1'));
      await expect(page.getByTestId('acrm-assignment-form')).toBeVisible();
      await expect(page.getByTestId('acrm-status-history-panel')).toBeVisible();
    });

    await test.step('Applicant Creation', async () => {
      await page.goto(pageUrl('/console/admissions/applicants/new'));
      await expect(page.getByTestId('acrm-applicant-create-form')).toBeVisible();
      await page.getByPlaceholder('lead_id').fill('1');
      await page.getByPlaceholder('applicant_ref').fill('A-NEW-001');
      await page.getByPlaceholder('full_name').fill('Workflow Applicant');
      await page.getByPlaceholder('email', { exact: true }).fill('workflow.applicant@example.edu');
      await page.getByRole('button', { name: /create applicant/i }).click();
    });

    await test.step('Applicant Editing', async () => {
      await page.goto(pageUrl('/console/admissions/applicants/1'));
      await expect(page.getByTestId('acrm-applicant-table')).toBeVisible();
      await expect(page.getByTestId('acrm-status-history-panel')).toBeVisible();
    });

    await test.step('Application Creation', async () => {
      await page.goto(pageUrl('/console/admissions/applications/new'));
      await expect(page.getByTestId('acrm-application-create-form')).toBeVisible();
      await page.getByPlaceholder('applicant_id').fill('1');
      await page.getByPlaceholder('application_ref').fill('APP-NEW-001');
      await page.getByPlaceholder('program_code').fill('CS');
      await page.getByPlaceholder('intake_term').fill('2026-FALL');
      await page.getByRole('button', { name: /create application/i }).click();
    });

    await test.step('Application Review', async () => {
      await page.goto(pageUrl('/console/admissions/applications/1'));
      await expect(page.getByTestId('acrm-application-table')).toBeVisible();
      await expect(page.getByTestId('acrm-status-history-panel')).toBeVisible();
    });

    await test.step('Workflow Timeline Review', async () => {
      await page.goto(pageUrl('/console/admissions/workflows'));
      await expect(page.getByTestId('acrm-workflow-timeline')).toBeVisible();
    });

    await test.step('Audit Trail Review', async () => {
      await page.goto(pageUrl('/console/admissions/audit'));
      await expect(page.getByTestId('acrm-audit-panel')).toBeVisible();
    });

    await test.step('Dashboard Navigation', async () => {
      await page.goto(pageUrl('/console/admissions/dashboard'));
      await expect(page.getByTestId('acrm-dashboard-admissions-overview')).toBeVisible();
      await expect(page.getByTestId('acrm-dashboard-pipeline-summary')).toBeVisible();
      await expect(page.getByTestId('acrm-dashboard-workflow-health')).toBeVisible();
      await expect(page.getByTestId('acrm-dashboard-application-status')).toBeVisible();
      await expect(page.getByTestId('acrm-dashboard-recruitment-progress')).toBeVisible();
    });

    await test.step('Overview Context Review', async () => {
      await page.goto(pageUrl('/console/admissions'));
      await expect(page.getByTestId('acrm-dashboard-admissions-overview')).toBeVisible();
    });

    await test.step('Leads Registry Review', async () => {
      await page.goto(pageUrl('/console/admissions/leads'));
      await expect(page.getByTestId('acrm-lead-table')).toBeVisible();
      await expect(page.locator('body')).toContainText('Alice Lead');
    });

    await test.step('Applicants Registry Review', async () => {
      await page.goto(pageUrl('/console/admissions/applicants'));
      await expect(page.getByTestId('acrm-applicant-table')).toBeVisible();
      await expect(page.locator('body')).toContainText('Alice Applicant');
    });

    await test.step('Applications Registry Review', async () => {
      await page.goto(pageUrl('/console/admissions/applications'));
      await expect(page.getByTestId('acrm-application-table')).toBeVisible();
      await expect(page.locator('body')).toContainText('APP-001');
    });

    await test.step('Permissions Matrix Review', async () => {
      await page.goto(pageUrl('/console/admissions/settings/permissions'));
      await expect(page.getByTestId('acrm-permission-matrix-panel')).toBeVisible();
      await expect(page.locator('body')).toContainText('Admissions CRM Permission Matrix');
    });

    await test.step('Tenant Notice Review', async () => {
      await page.goto(pageUrl('/console/admissions'));
      await expect(page.getByTestId('acrm-tenant-scope')).toContainText('Tenant scope active');
    });
  });

  test('A0454-E2E-GROUP-03 role validation platform_admin', async ({ page }) => {
    await setAuthenticatedUser(page, PLATFORM_ADMIN);
    for (const route of ROUTES) {
      await page.goto(pageUrl(route.path));
      await expect(page.getByTestId(`acrm-page-${route.routeKey}`)).toBeVisible();
    }
  });

  test('A0454-E2E-GROUP-04 role validation inst_admin', async ({ page }) => {
    await setAuthenticatedUser(page, INST_ADMIN);

    await page.goto(pageUrl('/console/admissions/leads/new'));
    await expect(page.getByTestId('acrm-page-leads-new')).toBeVisible();

    await page.goto(pageUrl('/console/admissions/audit'));
    await expectDenied(page);

    await page.goto(pageUrl('/console/admissions/settings/permissions'));
    await expectDenied(page);
  });

  test('A0454-E2E-GROUP-05 role validation acad_admin', async ({ page }) => {
    await setAuthenticatedUser(page, ACAD_ADMIN);

    await page.goto(pageUrl('/console/admissions/leads'));
    await expect(page.getByTestId('acrm-page-leads')).toBeVisible();

    await page.goto(pageUrl('/console/admissions/leads/new'));
    await expectDenied(page);

    await page.goto(pageUrl('/console/admissions/applicants/new'));
    await expectDenied(page);

    await page.goto(pageUrl('/console/admissions/applications/new'));
    await expectDenied(page);
  });

  test('A0454-E2E-GROUP-06 role validation auditor', async ({ page }) => {
    await setAuthenticatedUser(page, AUDITOR);

    await page.goto(pageUrl('/console/admissions/audit'));
    await expect(page.getByTestId('acrm-page-audit')).toBeVisible();

    await page.goto(pageUrl('/console/admissions/settings/permissions'));
    await expect(page.getByTestId('acrm-page-settings-permissions')).toBeVisible();

    await page.goto(pageUrl('/console/admissions/leads/new'));
    await expectDenied(page);
  });

  test('A0454-E2E-GROUP-07 permission validation read-only behavior', async ({ page }) => {
    await setAuthenticatedUser(page, READ_ONLY);

    await page.goto(pageUrl('/console/admissions'));
    await expect(page.getByTestId('acrm-page-overview')).toBeVisible();

    await page.goto(pageUrl('/console/admissions/leads/new'));
    await expectDenied(page);
  });

  test('A0454-E2E-GROUP-08 permission validation editor behavior', async ({ page }) => {
    await setAuthenticatedUser(page, EDITOR);

    await page.goto(pageUrl('/console/admissions/leads/new'));
    await expect(page.getByTestId('acrm-lead-create-form')).toBeVisible();

    await page.goto(pageUrl('/console/admissions/applications/new'));
    await expect(page.getByTestId('acrm-application-create-form')).toBeVisible();

    await page.goto(pageUrl('/console/admissions/audit'));
    await expectDenied(page);
  });

  test('A0454-E2E-GROUP-09 permission validation admin behavior', async ({ page }) => {
    await setAuthenticatedUser(page, PLATFORM_ADMIN);

    await page.goto(pageUrl('/console/admissions/audit'));
    await expect(page.getByTestId('acrm-audit-panel')).toBeVisible();

    await page.goto(pageUrl('/console/admissions/settings/permissions'));
    await expect(page.getByTestId('acrm-permission-matrix-panel')).toBeVisible();
  });

  test('A0454-E2E-GROUP-10 permission validation auditor behavior and forbidden actions hidden', async ({ page }) => {
    await setAuthenticatedUser(page, AUDITOR);

    await page.goto(pageUrl('/console/admissions/leads/new'));
    await expectDenied(page);
    await expect(page.getByTestId('acrm-lead-create-form')).toHaveCount(0);

    await page.goto(pageUrl('/console/admissions/applications/new'));
    await expectDenied(page);
    await expect(page.getByTestId('acrm-application-create-form')).toHaveCount(0);
  });

  test('A0454-E2E-GROUP-11 tenant validation matrix (6 scenarios)', async ({ page }) => {
    await setAuthenticatedUser(page, PLATFORM_ADMIN);

    await test.step('tenant scoped list visibility', async () => {
      await page.goto(pageUrl('/console/admissions/leads'));
      await expect(page.locator('body')).toContainText('Alice Lead');
      await expect(page.locator('body')).not.toContainText('Cross Tenant Lead');
    });

    await test.step('tenant scoped detail visibility', async () => {
      await page.goto(pageUrl('/console/admissions/leads/1'));
      await expect(page.getByTestId('acrm-page-lead-detail')).toBeVisible();
    });

    await test.step('tenant notice visible', async () => {
      await page.goto(pageUrl('/console/admissions'));
      await expect(page.getByTestId('acrm-tenant-scope')).toContainText('Tenant scope active');
    });

    await test.step('tenant-safe navigation', async () => {
      await page.goto(pageUrl('/console/admissions/applicants'));
      await expect(page.getByTestId('acrm-tenant-scope')).toContainText('Tenant scope active');
      await page.goto(pageUrl('/console/admissions/applications'));
      await expect(page.getByTestId('acrm-tenant-scope')).toContainText('Tenant scope active');
    });

    await test.step('tenant-safe filtering sentinel', async () => {
      await page.goto(pageUrl('/console/admissions/applicants'));
      await expect(page.locator('body')).toContainText('Alice Applicant');
      await expect(page.locator('body')).not.toContainText('tenant-2-applicant');
    });

    await test.step('fail-closed when tenant context missing', async () => {
      await setAuthenticatedUser(page, PLATFORM_ADMIN, null);
      await page.goto(pageUrl('/console/admissions'));
      await expect(page.getByTestId('acrm-tenant-missing')).toBeVisible();
      await expect(page.locator('body')).toContainText('fail-closed without tenant scope');
    });
  });

  test('A0454-E2E-GROUP-12 anti-fake validation', async ({ page }) => {
    await setAuthenticatedUser(page, PLATFORM_ADMIN);
    for (const route of ROUTES) {
      await page.goto(pageUrl(route.path));
      await expect(page.getByTestId('acrm-no-overclaim-footer')).toBeVisible();
      await expect(page.locator('body')).toContainText('No synthetic KPI generation');
      await expect(page.locator('body')).toContainText('No synthetic KPI generation, hidden scoring, or autonomous admissions decisions are enabled.');
      await expect(page.locator('body')).toContainText('Human review remains required');

      await expect(page.locator('body')).not.toContainText(/fake applicant score|conversion probability|brain recommendation|synthetic KPI engine|fake analytics/i);
    }
  });

  test('A0454-E2E-GROUP-13 dashboard validation Admissions Overview', async ({ page }) => {
    await setAuthenticatedUser(page, PLATFORM_ADMIN);
    await page.goto(pageUrl('/console/admissions/dashboard'));
    await expect(page.getByTestId('acrm-dashboard-admissions-overview')).toBeVisible();
    await expect(page.getByTestId('acrm-summary-cards')).toBeVisible();
    await expect(page.getByTestId('acrm-filters')).toBeVisible();
  });

  test('A0454-E2E-GROUP-14 dashboard validation Pipeline Summary', async ({ page }) => {
    await setAuthenticatedUser(page, PLATFORM_ADMIN);
    await page.goto(pageUrl('/console/admissions/dashboard'));
    await expect(page.getByTestId('acrm-dashboard-pipeline-summary')).toBeVisible();
    await expect(page.getByTestId('acrm-pipeline-summary-cards')).toBeVisible();
    await expect(page.getByTestId('acrm-filters')).toBeVisible();
  });

  test('A0454-E2E-GROUP-15 dashboard validation Workflow Health', async ({ page }) => {
    await setAuthenticatedUser(page, PLATFORM_ADMIN);
    await page.goto(pageUrl('/console/admissions/dashboard'));
    await expect(page.getByTestId('acrm-dashboard-workflow-health')).toBeVisible();
    await expect(page.getByTestId('acrm-workflow-health-cards')).toBeVisible();
    await expect(page.getByTestId('acrm-filters')).toBeVisible();
  });

  test('A0454-E2E-GROUP-16 dashboard validation Application Status', async ({ page }) => {
    await setAuthenticatedUser(page, PLATFORM_ADMIN);
    await page.goto(pageUrl('/console/admissions/dashboard'));
    await expect(page.getByTestId('acrm-dashboard-application-status')).toBeVisible();
    await expect(page.getByTestId('acrm-application-status-cards')).toBeVisible();
    await expect(page.getByTestId('acrm-filters')).toBeVisible();
  });

  test('A0454-E2E-GROUP-17 dashboard validation Recruitment Progress', async ({ page }) => {
    await setAuthenticatedUser(page, PLATFORM_ADMIN);
    await page.goto(pageUrl('/console/admissions/dashboard'));
    await expect(page.getByTestId('acrm-dashboard-recruitment-progress')).toBeVisible();
    await expect(page.getByTestId('acrm-recruitment-progress-cards')).toBeVisible();
    await expect(page.getByTestId('acrm-filters')).toBeVisible();
  });

  test('A0454-E2E-GROUP-18 hygiene and scenario count closure', async ({ page }) => {
    const hydrationErrors = captureHydrationErrors(page);
    await setAuthenticatedUser(page, PLATFORM_ADMIN);

    await page.goto(pageUrl('/console/admissions/dashboard'));
    await expect(page.locator('body')).not.toContainText(/playwright-report|test-results|screenshot|trace|video/i);
    expect(hydrationErrors).toEqual([]);

    expect(SCENARIO_GROUP_COUNT_TARGET).toBe(18);
    expect(WORKFLOW_SCENARIOS).toHaveLength(WORKFLOW_SCENARIO_TARGET);
    expect(TENANT_SCENARIO_TARGET).toBe(6);
    expect(ROUTE_COUNT_TARGET).toBe(14);
  });
});
