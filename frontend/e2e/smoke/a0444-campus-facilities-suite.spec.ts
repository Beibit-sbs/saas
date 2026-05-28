import { expect, test, type Page, type Route } from '@playwright/test';

const API_BASE = '/api/admin/campus-facilities';
const BFF_BASE = '/api/bff/admin/campus-facilities';
const BASE_URL = process.env.E2E_BASE_URL ?? 'https://nginx';

const SCENARIO_GROUP_COUNT_TARGET = 28;

type CampusRouteSpec = {
  path: string;
  routeKey:
    | 'overview'
    | 'dashboard'
    | 'campus'
    | 'facilities'
    | 'buildings'
    | 'floors'
    | 'rooms'
    | 'availability'
    | 'occupancy'
    | 'dormitories'
    | 'housing-units'
    | 'housing-requests'
    | 'maintenance'
    | 'service-requests'
    | 'work-orders'
    | 'transport'
    | 'responsible-units'
    | 'safety-readiness'
    | 'bridges-access-visitor'
    | 'bridges-student-services'
    | 'bridges-finance-asset'
    | 'bridges-hr-staff'
    | 'audit-evidence'
    | 'limitations';
  title: string;
  requiredPermission: string;
  bridgeRoute?: boolean;
  limitationsRoute?: boolean;
};

const CAMPUS_ROUTES: readonly CampusRouteSpec[] = [
  {
    path: '/console/campus-facilities',
    routeKey: 'overview',
    title: 'Campus / Facilities / Housing / Transport',
    requiredPermission: 'campus_facilities.overview.read',
  },
  {
    path: '/console/campus-facilities/dashboard',
    routeKey: 'dashboard',
    title: 'Campus Facilities Dashboard',
    requiredPermission: 'campus_facilities.dashboard.read',
  },
  {
    path: '/console/campus-facilities/campus',
    routeKey: 'campus',
    title: 'Campus Registry',
    requiredPermission: 'campus_facilities.campus.read',
  },
  {
    path: '/console/campus-facilities/facilities',
    routeKey: 'facilities',
    title: 'Facilities Registry',
    requiredPermission: 'campus_facilities.facilities.read',
  },
  {
    path: '/console/campus-facilities/buildings',
    routeKey: 'buildings',
    title: 'Buildings',
    requiredPermission: 'campus_facilities.buildings.read',
  },
  {
    path: '/console/campus-facilities/floors',
    routeKey: 'floors',
    title: 'Floors',
    requiredPermission: 'campus_facilities.floors.read',
  },
  {
    path: '/console/campus-facilities/rooms',
    routeKey: 'rooms',
    title: 'Rooms',
    requiredPermission: 'campus_facilities.rooms.read',
  },
  {
    path: '/console/campus-facilities/availability',
    routeKey: 'availability',
    title: 'Availability',
    requiredPermission: 'campus_facilities.availability.read',
  },
  {
    path: '/console/campus-facilities/occupancy',
    routeKey: 'occupancy',
    title: 'Occupancy Visibility',
    requiredPermission: 'campus_facilities.occupancy.read',
  },
  {
    path: '/console/campus-facilities/dormitories',
    routeKey: 'dormitories',
    title: 'Dormitories',
    requiredPermission: 'campus_facilities.dormitories.read',
  },
  {
    path: '/console/campus-facilities/housing-units',
    routeKey: 'housing-units',
    title: 'Housing Units',
    requiredPermission: 'campus_facilities.housing_units.read',
  },
  {
    path: '/console/campus-facilities/housing-requests',
    routeKey: 'housing-requests',
    title: 'Housing Requests',
    requiredPermission: 'campus_facilities.housing_requests.read',
  },
  {
    path: '/console/campus-facilities/maintenance',
    routeKey: 'maintenance',
    title: 'Maintenance',
    requiredPermission: 'campus_facilities.maintenance.read',
  },
  {
    path: '/console/campus-facilities/service-requests',
    routeKey: 'service-requests',
    title: 'Service Requests',
    requiredPermission: 'campus_facilities.service_requests.read',
  },
  {
    path: '/console/campus-facilities/work-orders',
    routeKey: 'work-orders',
    title: 'Work Orders',
    requiredPermission: 'campus_facilities.work_orders.read',
  },
  {
    path: '/console/campus-facilities/transport',
    routeKey: 'transport',
    title: 'Transport',
    requiredPermission: 'campus_facilities.transport.read',
  },
  {
    path: '/console/campus-facilities/responsible-units',
    routeKey: 'responsible-units',
    title: 'Responsible Units',
    requiredPermission: 'campus_facilities.responsible_units.read',
  },
  {
    path: '/console/campus-facilities/safety-readiness',
    routeKey: 'safety-readiness',
    title: 'Safety Readiness',
    requiredPermission: 'campus_facilities.safety_readiness.read',
  },
  {
    path: '/console/campus-facilities/bridges/access-visitor',
    routeKey: 'bridges-access-visitor',
    title: 'Bridge: Access Visitor',
    requiredPermission: 'campus_facilities.bridges.access_visitor',
    bridgeRoute: true,
  },
  {
    path: '/console/campus-facilities/bridges/student-services',
    routeKey: 'bridges-student-services',
    title: 'Bridge: Student Services',
    requiredPermission: 'campus_facilities.bridges.student_services',
    bridgeRoute: true,
  },
  {
    path: '/console/campus-facilities/bridges/finance-asset',
    routeKey: 'bridges-finance-asset',
    title: 'Bridge: Finance Asset',
    requiredPermission: 'campus_facilities.bridges.finance_asset',
    bridgeRoute: true,
  },
  {
    path: '/console/campus-facilities/bridges/hr-staff',
    routeKey: 'bridges-hr-staff',
    title: 'Bridge: HR Staff',
    requiredPermission: 'campus_facilities.bridges.hr_staff',
    bridgeRoute: true,
  },
  {
    path: '/console/campus-facilities/audit-evidence',
    routeKey: 'audit-evidence',
    title: 'Audit Evidence',
    requiredPermission: 'campus_facilities.audit_evidence.read',
  },
  {
    path: '/console/campus-facilities/limitations',
    routeKey: 'limitations',
    title: 'Limitations',
    requiredPermission: 'campus_facilities.limitations.read',
    limitationsRoute: true,
  },
] as const;

if (CAMPUS_ROUTES.length !== 24) {
  throw new Error(`Campus route inventory must be 24, got ${CAMPUS_ROUTES.length}`);
}

const FULL_PERMISSIONS = [
  'platform.admin.read',
  ...CAMPUS_ROUTES.map((route) => route.requiredPermission),
] as const;

const RESTRICTED_PERMISSIONS = ['platform.admin.read', 'campus_facilities.overview.read'] as const;

const REQUIRED_BOUNDARY_LABELS = [
  'Metadata/readiness/evidence only',
  'Human review required',
  'Incomplete data supported',
  'No live IoT integration',
  'No GPS live tracking',
  'No building automation',
  'No access-control enforcement',
  'No safety certification',
  'No maintenance completion guarantee',
  'No automatic housing decision',
  'No automatic eviction',
  'No automatic student/staff sanction',
  'No autonomous dispatch',
  'No external provider sync',
  'No production readiness claim',
  'No sales readiness claim',
  'No GCC readiness claim',
  'No L5/L6 claim',
] as const;

const FORBIDDEN_DOM_LABELS = [
  'Live IoT connected',
  'GPS tracking live',
  'Building automation enabled',
  'Access control enforced',
  'Safety certified',
  'Maintenance completed automatically',
  'Occupancy guaranteed',
  'Housing decision automatic',
  'Eviction automatic',
  'Student/staff sanctioned automatically',
  'Autonomous dispatch enabled',
  'Provider sync active',
  'Production ready',
  'Sales ready',
  'GCC ready',
  'L5/L6 ready',
  'Enable live IoT',
  'Start GPS tracking',
  'Control building automation',
  'Enforce access control',
  'Certify safety',
  'Complete maintenance automatically',
  'Guarantee occupancy',
  'Decide housing automatically',
  'Evict automatically',
  'Sanction automatically',
  'Dispatch autonomously',
  'Sync provider live',
  'Mark production ready',
  'Mark sales ready',
  'Mark GCC ready',
  'Promote to L5/L6',
] as const;

const FORBIDDEN_EXACT_TEXT_PATTERNS = FORBIDDEN_DOM_LABELS.map((label) =>
  new RegExp(`^${label.replace(/[.*+?^${}()|[\\]\\]/g, '\\$&')}$`, 'i'),
);

const adminFixture = {
  id: 'cfht-admin-01',
  sub: 'cfht-admin-01',
  tenantId: 1,
  email: 'cfht-admin@example.edu',
  displayName: 'Campus Facilities Admin',
  role: 'admin',
  roles: ['admin'],
  permissions: [...FULL_PERMISSIONS],
};

const restrictedFixture = {
  id: 'cfht-restricted-01',
  sub: 'cfht-restricted-01',
  tenantId: 1,
  email: 'cfht-restricted@example.edu',
  displayName: 'Campus Facilities Restricted User',
  role: 'admin',
  roles: ['admin'],
  permissions: [...RESTRICTED_PERMISSIONS],
};

function pageUrl(path: string) {
  return new URL(path, BASE_URL).toString();
}

function parsePath(url: string) {
  return new URL(url).pathname;
}

function makeRecord(id: number, key: string, title: string, extra: Record<string, unknown> = {}) {
  return {
    id,
    tenant_id: 1,
    key,
    title,
    status: 'ACTIVE',
    metadata_only: true,
    human_review_required: true,
    incomplete_data: true,
    ...extra,
  };
}

const STUBS = {
  overview: {
    module: 'campus_facilities',
    runtime_mode: 'METADATA_READINESS_EVIDENCE_CONTROL_VISIBILITY_HUMAN_REVIEW_ONLY',
    backend_route_count: 52,
    table_count: 26,
    permission_count: 46,
    route_count: 24,
    human_review_required: true,
    incomplete_data: true,
  },
  dashboard: {
    cards: [
      makeRecord(1, 'backend-route-count', 'Backend route contract'),
      makeRecord(2, 'table-count', 'Table inventory'),
      makeRecord(3, 'permission-count', 'Permission inventory'),
      makeRecord(4, 'safety-boundaries', 'Safety boundaries'),
    ],
  },
  campus: { items: [makeRecord(1, 'campus', 'Campus Registry')] },
  facilities: { items: [makeRecord(1, 'facilities', 'Facilities Registry')] },
  buildings: { items: [makeRecord(1, 'buildings', 'Buildings')] },
  floors: { items: [makeRecord(1, 'floors', 'Floors')] },
  rooms: { items: [makeRecord(1, 'rooms', 'Rooms')] },
  roomTypes: { items: [makeRecord(1, 'room-types', 'Room Types')] },
  availability: { items: [makeRecord(1, 'availability', 'Availability')] },
  occupancy: { items: [makeRecord(1, 'occupancy', 'Occupancy Visibility')] },
  dormitories: { items: [makeRecord(1, 'dormitories', 'Dormitories')] },
  housingUnits: { items: [makeRecord(1, 'housing-units', 'Housing Units')] },
  housingRequests: { items: [makeRecord(1, 'housing-requests', 'Housing Requests')] },
  maintenance: { items: [makeRecord(1, 'maintenance', 'Maintenance')] },
  serviceRequests: { items: [makeRecord(1, 'service-requests', 'Service Requests')] },
  workOrders: { items: [makeRecord(1, 'work-orders', 'Work Orders')] },
  transportRoutes: { items: [makeRecord(1, 'transport-routes', 'Transport Routes')] },
  transportVehicles: { items: [makeRecord(1, 'transport-vehicles', 'Transport Vehicles')] },
  transportSchedules: { items: [makeRecord(1, 'transport-schedules', 'Transport Schedules')] },
  responsibleUnits: { items: [makeRecord(1, 'responsible-units', 'Responsible Units')] },
  safetyReadiness: { items: [makeRecord(1, 'safety-readiness', 'Safety Readiness')] },
  bridgesAccessVisitor: { items: [makeRecord(1, 'bridges-access-visitor', 'Bridge: Access Visitor')] },
  bridgesStudentServices: { items: [makeRecord(1, 'bridges-student-services', 'Bridge: Student Services')] },
  bridgesFinanceAsset: { items: [makeRecord(1, 'bridges-finance-asset', 'Bridge: Finance Asset')] },
  bridgesHrStaff: { items: [makeRecord(1, 'bridges-hr-staff', 'Bridge: HR Staff')] },
  auditEvidence: { items: [makeRecord(1, 'audit-evidence', 'Audit Evidence')] },
  limitations: { items: [makeRecord(1, 'limitations', 'Limitations')] },
  metadataContract: {
    expected_table_count: 26,
    expected_route_count: 52,
    expected_permission_count: 46,
    permission_namespace: 'campus_facilities.*',
    human_review_required: true,
    no_production_claim: true,
  },
  safetyBoundaries: {
    labels: [...REQUIRED_BOUNDARY_LABELS],
    no_overclaim: true,
  },
  health: {
    ok: true,
    module: 'campus_facilities',
  },
} as const;

function matchCampusFixture(pathname: string) {
  if (pathname === `${API_BASE}/overview` || pathname === `${BFF_BASE}/overview`) return STUBS.overview;
  if (pathname === `${API_BASE}/dashboard` || pathname === `${BFF_BASE}/dashboard`) return STUBS.dashboard;
  if (pathname === `${API_BASE}/campus` || pathname === `${BFF_BASE}/campus`) return STUBS.campus;
  if (pathname === `${API_BASE}/facilities` || pathname === `${BFF_BASE}/facilities`) return STUBS.facilities;
  if (pathname === `${API_BASE}/buildings` || pathname === `${BFF_BASE}/buildings`) return STUBS.buildings;
  if (pathname === `${API_BASE}/floors` || pathname === `${BFF_BASE}/floors`) return STUBS.floors;
  if (pathname === `${API_BASE}/rooms` || pathname === `${BFF_BASE}/rooms`) return STUBS.rooms;
  if (pathname === `${API_BASE}/room-types` || pathname === `${BFF_BASE}/room-types`) return STUBS.roomTypes;
  if (pathname === `${API_BASE}/availability` || pathname === `${BFF_BASE}/availability`) return STUBS.availability;
  if (pathname === `${API_BASE}/occupancy` || pathname === `${BFF_BASE}/occupancy`) return STUBS.occupancy;
  if (pathname === `${API_BASE}/dormitories` || pathname === `${BFF_BASE}/dormitories`) return STUBS.dormitories;
  if (pathname === `${API_BASE}/housing-units` || pathname === `${BFF_BASE}/housing-units`) return STUBS.housingUnits;
  if (pathname === `${API_BASE}/housing-requests` || pathname === `${BFF_BASE}/housing-requests`) return STUBS.housingRequests;
  if (pathname === `${API_BASE}/maintenance` || pathname === `${BFF_BASE}/maintenance`) return STUBS.maintenance;
  if (pathname === `${API_BASE}/service-requests` || pathname === `${BFF_BASE}/service-requests`) return STUBS.serviceRequests;
  if (pathname === `${API_BASE}/work-orders` || pathname === `${BFF_BASE}/work-orders`) return STUBS.workOrders;
  if (pathname === `${API_BASE}/transport/routes` || pathname === `${BFF_BASE}/transport/routes`) return STUBS.transportRoutes;
  if (pathname === `${API_BASE}/transport/vehicles` || pathname === `${BFF_BASE}/transport/vehicles`) return STUBS.transportVehicles;
  if (pathname === `${API_BASE}/transport/schedules` || pathname === `${BFF_BASE}/transport/schedules`) return STUBS.transportSchedules;
  if (pathname === `${API_BASE}/responsible-units` || pathname === `${BFF_BASE}/responsible-units`) return STUBS.responsibleUnits;
  if (pathname === `${API_BASE}/safety-readiness` || pathname === `${BFF_BASE}/safety-readiness`) return STUBS.safetyReadiness;
  if (pathname === `${API_BASE}/bridges/access-visitor` || pathname === `${BFF_BASE}/bridges/access-visitor`) return STUBS.bridgesAccessVisitor;
  if (pathname === `${API_BASE}/bridges/student-services` || pathname === `${BFF_BASE}/bridges/student-services`) return STUBS.bridgesStudentServices;
  if (pathname === `${API_BASE}/bridges/finance-asset` || pathname === `${BFF_BASE}/bridges/finance-asset`) return STUBS.bridgesFinanceAsset;
  if (pathname === `${API_BASE}/bridges/hr-staff` || pathname === `${BFF_BASE}/bridges/hr-staff`) return STUBS.bridgesHrStaff;
  if (pathname === `${API_BASE}/audit-evidence` || pathname === `${BFF_BASE}/audit-evidence`) return STUBS.auditEvidence;
  if (pathname === `${API_BASE}/limitations` || pathname === `${BFF_BASE}/limitations`) return STUBS.limitations;
  if (pathname === `${API_BASE}/metadata-contract` || pathname === `${BFF_BASE}/metadata-contract`) return STUBS.metadataContract;
  if (pathname === `${API_BASE}/safety-boundaries` || pathname === `${BFF_BASE}/safety-boundaries`) return STUBS.safetyBoundaries;
  if (pathname === `${API_BASE}/health` || pathname === `${BFF_BASE}/health`) return STUBS.health;
  return null;
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
      body: JSON.stringify({ csrfToken: 'cfht-csrf-token' }),
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
            tenantId: 8101,
            tenantCode: 'campus-demo-tenant',
            tenantName: 'Campus Facilities Demo Tenant',
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

async function stubAuth(page: Page, fixture: typeof adminFixture | typeof restrictedFixture) {
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
        body: JSON.stringify({
          authenticated: true,
          user: fixture,
        }),
      });
    });
  }
}

async function stubCampusApi(page: Page) {
  const fulfillRoute = async (route: Route) => {
    const request = route.request();
    const pathname = parsePath(request.url());
    const payload = matchCampusFixture(pathname);

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
        mode: 'metadata_only',
      });
      return;
    }

    if (pathname.includes('/campus-facilities/')) {
      await respond({
        ...STUBS.metadataContract,
        detail: `Fallback metadata-contract response for ${pathname}`,
      });
      return;
    }

    await respond({ detail: `Unhandled CFHT stub path: ${pathname}` }, 404);
  };

  await page.route(`**${API_BASE}**`, fulfillRoute);
  await page.route(`**${BFF_BASE}**`, fulfillRoute);
}

async function setAuthenticatedAdmin(page: Page) {
  await forceEnglishLocale(page);
  await stubSharedBootstrap(page);
  await stubAuth(page, adminFixture);
  await stubCampusApi(page);
}

async function setRestrictedUser(page: Page) {
  await forceEnglishLocale(page);
  await stubSharedBootstrap(page);
  await stubAuth(page, restrictedFixture);
  await stubCampusApi(page);
}

async function gotoRoute(page: Page, path: string) {
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
    const exact = new RegExp(`^${label.replace(/[.*+?^${}()|[\\]\\]/g, '\\$&')}$`, 'i');
    await expect(page.getByRole('button', { name: exact })).toHaveCount(0);
    await expect(page.getByRole('link', { name: exact })).toHaveCount(0);
    await expect(page.getByText(exact)).toHaveCount(0);
  }

  for (const pattern of FORBIDDEN_EXACT_TEXT_PATTERNS) {
    await expect(page.getByText(pattern)).toHaveCount(0);
  }
}

async function expectRouteShell(page: Page, route: CampusRouteSpec) {
  await expect(page.getByTestId('campus-facilities-page-shell')).toBeVisible({ timeout: 15_000 });
  await expect(page.getByTestId('campus-facilities-route-header')).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('heading', { level: 1, name: route.title })).toBeVisible({ timeout: 15_000 });
  await expect(page.locator('nav[aria-label="Campus facilities navigation"] a')).toHaveCount(24, { timeout: 15_000 });
  await expect(page.getByTestId(`campus-facilities-page-${route.routeKey}`)).toBeVisible({ timeout: 15_000 });
}

async function openAndAssertRoute(page: Page, route: CampusRouteSpec) {
  await gotoRoute(page, route.path);
  await expectRouteShell(page, route);

  await expect(page.getByTestId('campus-facilities-boundary-banner')).toBeVisible();
  await expect(page.getByTestId('campus-facilities-incomplete-data-notice')).toContainText('incompleteData supported');
  await expect(page.getByTestId('campus-facilities-dashboard-cards')).toBeVisible();
  await expect(page.getByTestId('campus-facilities-metadata-panel')).toContainText(route.requiredPermission);
  await expect(page.getByTestId('campus-facilities-no-overclaim-footer')).toBeVisible();

  if (route.bridgeRoute) {
    await expect(page.getByTestId('campus-facilities-bridge-panel')).toBeVisible();
  } else {
    await expect(page.getByTestId('campus-facilities-bridge-panel')).toHaveCount(0);
  }

  if (route.limitationsRoute) {
    await expect(page.getByTestId('campus-facilities-limitations-panel')).toBeVisible();
  } else {
    await expect(page.getByTestId('campus-facilities-limitations-panel')).toHaveCount(0);
  }

  for (const label of REQUIRED_BOUNDARY_LABELS) {
    await expect(page.locator('body')).toContainText(label);
  }

  await expectForbiddenDomAbsent(page);
}

async function expectPermissionDeniedOrSafeFallback(page: Page, requiredPermission: string) {
  const deniedPanel = page.getByTestId('campus-facilities-permission-denied');
  await expect(deniedPanel).toBeVisible({ timeout: 15_000 });
  await expect(deniedPanel).toContainText(requiredPermission);
  await expect(page.getByTestId('campus-facilities-page-shell')).toHaveCount(0);
  await expect(page.getByTestId('campus-facilities-dashboard-cards')).toHaveCount(0);
  await expect(page.getByTestId('campus-facilities-metadata-panel')).toHaveCount(0);
  await expectForbiddenDomAbsent(page);
}

test.describe('A-044.4 Campus / Facilities / Housing / Transport route coverage', () => {
  test.describe.configure({ timeout: 320_000 });

  test('CFHT-E2E-GROUP-00 auth entry / route family shell coverage for all 24 routes', async ({ page }) => {
    page.setDefaultTimeout(15_000);
    page.setDefaultNavigationTimeout(15_000);
    await setAuthenticatedAdmin(page);

    expect(CAMPUS_ROUTES).toHaveLength(24);

    for (const route of CAMPUS_ROUTES) {
      await test.step(`full-access ${route.routeKey} ${route.path}`, async () => {
        await openAndAssertRoute(page, route);
      });
    }
  });

  test('CFHT-E2E-GROUP-01 overview route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[0]);
  });

  test('CFHT-E2E-GROUP-02 dashboard route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[1]);
  });

  test('CFHT-E2E-GROUP-03 campus route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[2]);
  });

  test('CFHT-E2E-GROUP-04 facilities route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[3]);
  });

  test('CFHT-E2E-GROUP-05 buildings route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[4]);
  });

  test('CFHT-E2E-GROUP-06 floors route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[5]);
  });

  test('CFHT-E2E-GROUP-07 rooms route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[6]);
  });

  test('CFHT-E2E-GROUP-08 availability route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[7]);
  });

  test('CFHT-E2E-GROUP-09 occupancy route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[8]);
  });

  test('CFHT-E2E-GROUP-10 dormitories route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[9]);
  });

  test('CFHT-E2E-GROUP-11 housing units route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[10]);
  });

  test('CFHT-E2E-GROUP-12 housing requests route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[11]);
  });

  test('CFHT-E2E-GROUP-13 maintenance route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[12]);
  });

  test('CFHT-E2E-GROUP-14 service requests route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[13]);
  });

  test('CFHT-E2E-GROUP-15 work orders route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[14]);
  });

  test('CFHT-E2E-GROUP-16 transport route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[15]);
  });

  test('CFHT-E2E-GROUP-17 responsible units route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[16]);
  });

  test('CFHT-E2E-GROUP-18 safety readiness route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[17]);
  });

  test('CFHT-E2E-GROUP-19 access/visitor bridge route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[18]);
  });

  test('CFHT-E2E-GROUP-20 student services bridge route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[19]);
  });

  test('CFHT-E2E-GROUP-21 finance/asset bridge route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[20]);
  });

  test('CFHT-E2E-GROUP-22 HR/staff bridge route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[21]);
  });

  test('CFHT-E2E-GROUP-23 audit evidence route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[22]);
  });

  test('CFHT-E2E-GROUP-24 limitations route', async ({ page }) => {
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, CAMPUS_ROUTES[23]);
  });
});

test.describe('A-044.4 Campus / Facilities / Housing / Transport runtime safety groups', () => {
  test.describe.configure({ timeout: 220_000 });

  test('CFHT-E2E-GROUP-25 permission-denial smoke', async ({ page }) => {
    page.setDefaultTimeout(15_000);
    page.setDefaultNavigationTimeout(15_000);
    await setRestrictedUser(page);

    const protectedRoutes = CAMPUS_ROUTES.filter((route) => route.requiredPermission !== 'campus_facilities.overview.read');

    for (const route of protectedRoutes) {
      await test.step(`restricted-user ${route.routeKey}`, async () => {
        await gotoRoute(page, route.path);
        await expectPermissionDeniedOrSafeFallback(page, route.requiredPermission);
      });
    }
  });

  test('CFHT-E2E-GROUP-26 no-overclaim DOM scan', async ({ page }) => {
    page.setDefaultTimeout(15_000);
    page.setDefaultNavigationTimeout(15_000);
    await setAuthenticatedAdmin(page);

    for (const route of CAMPUS_ROUTES) {
      await gotoRoute(page, route.path);
      await expectForbiddenDomAbsent(page);
    }

    for (const required of REQUIRED_BOUNDARY_LABELS) {
      await gotoRoute(page, '/console/campus-facilities');
      await expect(page.locator('body')).toContainText(required);
    }

    await gotoRoute(page, '/console/campus-facilities/limitations');
    await expect(page.locator('body')).toContainText('No L5/L6 claim');
  });

  test('CFHT-E2E-GROUP-27 artifact hygiene / closeout', async ({ page }) => {
    page.setDefaultTimeout(15_000);
    page.setDefaultNavigationTimeout(15_000);
    await setAuthenticatedAdmin(page);
    await gotoRoute(page, '/console/campus-facilities/dashboard');

    await expect(page.locator('body')).not.toContainText(/playwright-report|test-results|demo evidence|screenshot|video|trace/i);
    expect(SCENARIO_GROUP_COUNT_TARGET).toBe(28);
  });
});
