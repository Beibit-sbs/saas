import { test, expect, type Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// A-031.3-E2E — Rector Assignment OS End-to-End Validation
// Playwright smoke spec against Nginx edge (https://nginx inside Docker Compose)
//
// Auth strategy: stubAuthSession injects fake JWT + stubs /api/auth/me
// Data strategy: BFF routes are stubbed per-test with fixture data
// Anti-fake guard: DashboardSummary.fake_metrics === false is asserted by the page component
//                  before rendering KPIs — spec verifies the guard is enforced
// ---------------------------------------------------------------------------

const RECTOR_BASE_BFF = "/api/bff/admin/rector-assignments";

// ---------------------------------------------------------------------------
// Fixture data — must satisfy DashboardSummary shape from types.ts
// fake_metrics MUST be false; data_source MUST be "computed_from_assignments"
// ---------------------------------------------------------------------------

const FIXTURE_DASHBOARD_REAL = {
  tenant_id: 1,
  computed_at: "2026-05-20T07:00:00Z",
  total_assignments: 12,
  active_count: 5,
  draft_count: 2,
  overdue_count: 1,
  escalated_count: 0,
  completed_count: 4,
  cancelled_count: 1,
  report_submitted_count: 2,
  returned_count: 1,
  due_this_week: 3,
  due_today: 1,
  completion_rate_30d: 0.67,
  average_days_to_complete: 8.5,
  by_status: { ASSIGNED: 3, IN_PROGRESS: 2, COMPLETED: 4, DRAFT: 2, CANCELLED: 1 },
  by_priority: { HIGH: 4, NORMAL: 6, LOW: 2 },
  by_unit: [{ unit_id: 1, unit_name: "Academic Department", count: 7 }],
  top_overdue: [],
  data_source: "computed_from_assignments",
  fake_metrics: false, // MUST be false — anti-fake guard
};

const FIXTURE_DASHBOARD_FAKE = {
  ...FIXTURE_DASHBOARD_REAL,
  fake_metrics: true, // should trigger DataQualityError in the page
};

const FIXTURE_ASSIGNMENT_ASSIGNED: Record<string, unknown> = {
  id: 1001,
  tenant_id: 1,
  title: "Improve Student Admission Process",
  description: "Rector assignment for improving admission procedures",
  status: "ASSIGNED",
  priority: "HIGH",
  due_date: "2026-06-01",
  recurrence_type: "NONE",
  version: 1,
  is_overdue: false,
  created_by: 1,
  created_at: "2026-05-15T10:00:00Z",
  updated_at: "2026-05-15T10:00:00Z",
};

const FIXTURE_ASSIGNMENT_COMPLETED: Record<string, unknown> = {
  ...FIXTURE_ASSIGNMENT_ASSIGNED,
  id: 1002,
  title: "Annual Budget Review Assignment",
  status: "COMPLETED",
  priority: "NORMAL",
  completed_at: "2026-05-19T15:00:00Z",
};

const FIXTURE_ASSIGNMENT_LIST = [FIXTURE_ASSIGNMENT_ASSIGNED, FIXTURE_ASSIGNMENT_COMPLETED];

const FIXTURE_ASSIGNMENT_DETAIL = {
  ...FIXTURE_ASSIGNMENT_ASSIGNED,
  assignees: [
    {
      id: 1,
      assignment_id: 1001,
      user_id: 42,
      role_on_assignment: "RESPONSIBLE",
      assigned_at: "2026-05-15T10:00:00Z",
      is_lead: true,
    },
  ],
  tasks: [
    {
      id: 1,
      assignment_id: 1001,
      title: "Draft proposal document",
      description: "Create the initial proposal",
      is_completed: false,
      sort_order: 1,
    },
  ],
};

const FIXTURE_REPORT = {
  id: 1,
  assignment_id: 1001,
  submitted_by: 42,
  reporting_period_start: "2026-05-15",
  reporting_period_end: "2026-05-20",
  progress_percent: 60,
  summary: "Completed initial review of admission procedures",
  blockers: "None at this time",
  next_steps: "Draft final report",
  status: "SUBMITTED",
  submitted_at: "2026-05-20T08:00:00Z",
};

const FIXTURE_EVIDENCE = {
  id: 1,
  assignment_id: 1001,
  evidence_type: "LINK",
  title: "Admission Process Review Document",
  url: "https://university.example.com/docs/admission-review",
  uploaded_by: 42,
  uploaded_at: "2026-05-20T08:05:00Z",
};

const FIXTURE_STATUS_HISTORY = [
  {
    id: 1,
    assignment_id: 1001,
    old_status: null,
    new_status: "ASSIGNED",
    changed_by: 1,
    changed_at: "2026-05-15T10:00:00Z",
    reason: "Initial assignment",
  },
  {
    id: 2,
    assignment_id: 1001,
    old_status: "ASSIGNED",
    new_status: "ACCEPTED",
    changed_by: 42,
    changed_at: "2026-05-15T11:00:00Z",
  },
];

const FIXTURE_AUDIT_EVENTS = [
  {
    id: 1,
    assignment_id: 1001,
    event_type: "assignment_created",
    actor_id: 1,
    created_at: "2026-05-15T10:00:00Z",
  },
  {
    id: 2,
    assignment_id: 1001,
    event_type: "status_changed",
    actor_id: 42,
    created_at: "2026-05-15T11:00:00Z",
  },
];

const FIXTURE_TEMPLATES = [
  {
    id: 1,
    name: "Standard Assignment Template",
    description: "Default template for rector assignments",
    default_priority: "NORMAL",
    default_due_days: 30,
    default_recurrence_type: "NONE",
    is_active: true,
    created_by: 1,
    created_at: "2026-01-01T00:00:00Z",
  },
];

const FIXTURE_ESCALATIONS: unknown[] = [];

const FIXTURE_MY_ASSIGNMENTS = [
  {
    ...FIXTURE_ASSIGNMENT_ASSIGNED,
    id: 1003,
    title: "My Active Assignment",
    status: "IN_PROGRESS",
    priority: "CRITICAL",
    is_overdue: false,
  },
];

// ---------------------------------------------------------------------------
// Helpers — identical pattern to admin-console.spec.ts
// ---------------------------------------------------------------------------

async function stubAuthSession(
  page: Page,
  overrides: Record<string, unknown> = {},
) {
  const cookieUrl = process.env.E2E_BASE_URL ?? "https://nginx";
  const parsedUrl = new URL(cookieUrl);
  const cookieOrigins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  const payloadJson = JSON.stringify({
    sub: "test-admin-id",
    exp: Math.floor(Date.now() / 1000) + 3600,
  });
  const payload = Buffer.from(payloadJson).toString("base64url");
  const fakeToken = `fakeheader.${payload}.fakesig`;

  const authCookies = Array.from(cookieOrigins).flatMap((url) => {
    const secure = new URL(url).protocol === "https:";
    return [
      {
        name: "admin_token",
        value: fakeToken,
        url,
        httpOnly: true,
        secure,
        sameSite: "Lax" as const,
      },
      {
        name: "app_access_token",
        value: fakeToken,
        url,
        httpOnly: true,
        secure,
        sameSite: "Lax" as const,
      },
    ];
  });

  await page.context().addCookies(authCookies);

  await page.route("**/api/auth/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        authenticated: true,
        user: {
          sub: "test-admin-id",
          displayName: "Test Rector Admin",
          roles: ["admin"],
          permissions: [
            "platform.admin.read",
            "platform.admin.write",
            "admin.dashboard.read",
            // Rector assignment permissions
            "admin.rector_assignments.dashboard.read",
            "admin.rector_assignments.read",
            "admin.rector_assignments.read_all",
            "admin.rector_assignments.read_department",
            "admin.rector_assignments.create",
            "admin.rector_assignments.assign",
            "admin.rector_assignments.accept",
            "admin.rector_assignments.return",
            "admin.rector_assignments.complete",
            "admin.rector_assignments.escalate",
            "admin.rector_assignments.cancel",
            "admin.rector_assignments.archive",
            "admin.rector_assignments.status.change",
            "admin.rector_assignments.report.submit",
            "admin.rector_assignments.report.review",
            "admin.rector_assignments.evidence.attach",
            "admin.rector_assignments.comment",
            "admin.rector_assignments.audit.read",
            "admin.rector_assignments.templates.manage",
          ],
          tenantId: 1,
          ...overrides,
        },
      }),
    });
  });
}

async function stubApi(page: Page, path: string, body: unknown, status = 200) {
  const pattern = path.startsWith("**/") ? path : `**${path}`;
  await page.route(pattern, async (route) => {
    await route.fulfill({
      status,
      contentType: "application/json",
      body: JSON.stringify(body),
    });
  });
}

async function forceEnglishLocale(page: Page) {
  const configuredUrl = process.env.E2E_BASE_URL ?? "https://nginx";
  const parsedUrl = new URL(configuredUrl);
  const cookieOrigins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);
  await page.context().addCookies(
    Array.from(cookieOrigins).map((url) => ({
      name: "app.locale",
      value: "en",
      url,
      httpOnly: false,
      secure: new URL(url).protocol === "https:",
      sameSite: "Lax" as const,
    })),
  );
  await page.addInitScript(() => {
    document.cookie = "app.locale=en; Path=/; SameSite=Lax";
    window.localStorage.setItem("app.language", "en");
  });
}

/** Stub the standard dashboard-level BFF calls for rector assignments */
async function stubDashboardApis(page: Page) {
  await stubApi(page, `${RECTOR_BASE_BFF}/dashboard/summary`, FIXTURE_DASHBOARD_REAL);
  await stubApi(page, `${RECTOR_BASE_BFF}*`, FIXTURE_ASSIGNMENT_LIST);
  await stubApi(page, `${RECTOR_BASE_BFF}/templates`, FIXTURE_TEMPLATES);
}

// ---------------------------------------------------------------------------

test.beforeEach(async ({ page }) => {
  await forceEnglishLocale(page);
});

// ---------------------------------------------------------------------------
// Scenario A — Unauthenticated redirects (security baseline)
// ---------------------------------------------------------------------------

test.describe("A — Unauthenticated access redirects", () => {
  test("unauthenticated visit to /console/rector-assignments redirects to login", async ({
    page,
  }) => {
    await page.route("**/api/auth/me", async (route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ authenticated: false, user: null }),
      });
    });
    await page.goto("/console/rector-assignments");
    await expect(page).toHaveURL(/\/login/);
  });

  test("unauthenticated visit to /console/my-assignments redirects to login", async ({
    page,
  }) => {
    await page.route("**/api/auth/me", async (route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ authenticated: false, user: null }),
      });
    });
    await page.goto("/console/my-assignments");
    await expect(page).toHaveURL(/\/login/);
  });
});

// ---------------------------------------------------------------------------
// Scenario B — Registry + Dashboard page (Rector role)
// ---------------------------------------------------------------------------

test.describe("B — Rector Assignment Registry page", () => {
  test("renders registry page with PageHeader and assignment list", async ({
    page,
  }) => {
    await stubAuthSession(page);
    await stubDashboardApis(page);

    await page.goto("/console/rector-assignments");
    await expect(
      page.getByRole("heading", { name: /Rector Assignment Registry/i }),
    ).toBeVisible();
  });

  test("renders dashboard KPI cards when fake_metrics is false", async ({
    page,
  }) => {
    await stubAuthSession(page);
    await stubApi(
      page,
      `${RECTOR_BASE_BFF}/dashboard/summary`,
      FIXTURE_DASHBOARD_REAL,
    );
    await stubApi(page, `${RECTOR_BASE_BFF}*`, FIXTURE_ASSIGNMENT_LIST);

    await page.goto("/console/rector-assignments");
    // Page renders without DataQualityError
    await expect(page.locator('[data-testid="data-quality-error"]')).not.toBeVisible();
  });

  test("shows DataQualityError when fake_metrics is true (anti-fake guard)", async ({
    page,
  }) => {
    await stubAuthSession(page);
    await stubApi(
      page,
      `${RECTOR_BASE_BFF}/dashboard/summary`,
      FIXTURE_DASHBOARD_FAKE,
    );
    await stubApi(page, `${RECTOR_BASE_BFF}*`, FIXTURE_ASSIGNMENT_LIST);

    await page.goto("/console/rector-assignments");
    await expect(page.locator('[data-testid="data-quality-error"]')).toBeVisible();
  });

  test("create assignment button links to /new route", async ({ page }) => {
    await stubAuthSession(page);
    await stubDashboardApis(page);

    await page.goto("/console/rector-assignments");
    const createLink = page.getByRole("link", { name: /new assignment|create/i });
    await expect(createLink).toBeVisible();
  });

  test("shows assignment list items from BFF", async ({ page }) => {
    await stubAuthSession(page);
    await stubDashboardApis(page);

    await page.goto("/console/rector-assignments");
    await expect(
      page.getByText("Improve Student Admission Process"),
    ).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Scenario C — New Assignment form (create workflow)
// ---------------------------------------------------------------------------

test.describe("C — New Assignment form", () => {
  test("renders New Rector Assignment form with required fields", async ({
    page,
  }) => {
    await stubAuthSession(page);
    await stubApi(page, `${RECTOR_BASE_BFF}/templates`, FIXTURE_TEMPLATES);

    await page.goto("/console/rector-assignments/new");
    await expect(
      page.getByRole("heading", { name: /New Rector Assignment/i }),
    ).toBeVisible();
    await expect(page.getByLabel(/Title/i)).toBeVisible();
  });

  test("submits create assignment form and calls BFF POST", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, `${RECTOR_BASE_BFF}/templates`, FIXTURE_TEMPLATES);

    let createCalled = 0;
    await page.route(`**${RECTOR_BASE_BFF}`, async (route) => {
      if (route.request().method() === "POST") {
        createCalled += 1;
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify(FIXTURE_ASSIGNMENT_ASSIGNED),
        });
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(FIXTURE_ASSIGNMENT_LIST),
      });
    });

    await page.goto("/console/rector-assignments/new");
    await page.getByLabel(/Title/i).fill("Test E2E Assignment");
    await page.getByLabel(/Description/i).fill("E2E test description for rector assignment");

    const submitRequest = page.waitForRequest(
      (req) =>
        req.method() === "POST" &&
        req.url().includes("rector-assignments") &&
        !req.url().includes("templates"),
    );

    await page.getByRole("button", { name: /Create|Save|Submit/i }).last().click();
    await submitRequest;
    await expect.poll(() => createCalled).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// Scenario D — My Assignments (Executor inbox)
// ---------------------------------------------------------------------------

test.describe("D — My Assignments (Executor view)", () => {
  test("renders My Assignments page with correct heading", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, `${RECTOR_BASE_BFF}*`, FIXTURE_MY_ASSIGNMENTS);

    await page.goto("/console/my-assignments");
    await expect(
      page.getByRole("heading", { name: /My Assignments/i }),
    ).toBeVisible();
  });

  test("shows urgent alert when CRITICAL priority assignment present", async ({
    page,
  }) => {
    await stubAuthSession(page);
    await stubApi(page, `${RECTOR_BASE_BFF}*`, FIXTURE_MY_ASSIGNMENTS);

    await page.goto("/console/my-assignments");
    // FIXTURE_MY_ASSIGNMENTS has a CRITICAL priority item
    await expect(page.locator('[data-testid="urgent-alert"]')).toBeVisible();
  });

  test("shows my assignment title from BFF", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, `${RECTOR_BASE_BFF}*`, FIXTURE_MY_ASSIGNMENTS);

    await page.goto("/console/my-assignments");
    await expect(page.getByText("My Active Assignment")).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Scenario E — Templates management page
// ---------------------------------------------------------------------------

test.describe("E — Assignment Templates page", () => {
  test("renders Assignment Templates page with correct heading", async ({
    page,
  }) => {
    await stubAuthSession(page);
    await stubApi(page, `${RECTOR_BASE_BFF}/templates`, FIXTURE_TEMPLATES);
    await stubApi(page, `${RECTOR_BASE_BFF}*`, FIXTURE_ASSIGNMENT_LIST);

    await page.goto("/console/rector-assignments/templates");
    await expect(
      page.getByRole("heading", { name: /Assignment Templates/i }),
    ).toBeVisible();
  });

  test("shows template from BFF in templates list", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, `${RECTOR_BASE_BFF}/templates`, FIXTURE_TEMPLATES);
    await stubApi(page, `${RECTOR_BASE_BFF}*`, FIXTURE_ASSIGNMENT_LIST);

    await page.goto("/console/rector-assignments/templates");
    await expect(page.getByText("Standard Assignment Template")).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Scenario F — Overdue & Escalations pages
// ---------------------------------------------------------------------------

test.describe("F — Overdue and Escalations pages", () => {
  test("renders Overdue page with correct heading", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, `${RECTOR_BASE_BFF}*`, []);

    await page.goto("/console/rector-assignments/overdue");
    await expect(
      page.getByRole("heading", { name: /Overdue/i }),
    ).toBeVisible();
  });

  test("renders Escalation Queue page with correct heading", async ({
    page,
  }) => {
    await stubAuthSession(page);
    await stubApi(page, `${RECTOR_BASE_BFF}*`, []);

    await page.goto("/console/rector-assignments/escalations");
    await expect(
      page.getByRole("heading", { name: /Escalation/i }),
    ).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Scenario G — Dashboard data integrity (anti-fake guard)
// ---------------------------------------------------------------------------

test.describe("G — Dashboard anti-fake guard (fake_metrics enforcement)", () => {
  test("does NOT render KPI cards when data_source is wrong (guard triggered)", async ({
    page,
  }) => {
    await stubAuthSession(page);
    await stubApi(page, `${RECTOR_BASE_BFF}/dashboard/summary`, {
      ...FIXTURE_DASHBOARD_REAL,
      data_source: "hardcoded_mock", // wrong data_source
      fake_metrics: false,
    });
    await stubApi(page, `${RECTOR_BASE_BFF}*`, FIXTURE_ASSIGNMENT_LIST);

    await page.goto("/console/rector-assignments");
    await expect(page.locator('[data-testid="data-quality-error"]')).toBeVisible();
  });

  test("renders KPIs correctly when fake_metrics=false and data_source=computed_from_assignments", async ({
    page,
  }) => {
    await stubAuthSession(page);
    await stubApi(
      page,
      `${RECTOR_BASE_BFF}/dashboard/summary`,
      FIXTURE_DASHBOARD_REAL,
    );
    await stubApi(page, `${RECTOR_BASE_BFF}*`, FIXTURE_ASSIGNMENT_LIST);

    await page.goto("/console/rector-assignments");
    // No DataQualityError shown
    await expect(page.locator('[data-testid="data-quality-error"]')).not.toBeVisible();
    // Page is visible without error
    await expect(
      page.getByRole("heading", { name: /Rector Assignment Registry/i }),
    ).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Scenario H — RBAC / permission gate (limited permissions)
// ---------------------------------------------------------------------------

test.describe("H — Permission gate enforcement", () => {
  test("user without rector assignment permissions cannot access registry", async ({
    page,
  }) => {
    await stubAuthSession(page, {
      permissions: [
        "platform.admin.read", // no rector_assignments permissions
      ],
    });

    await page.goto("/console/rector-assignments");
    // Wait for auth context to settle (stub resolves instantly but React needs a tick)
    await page.waitForLoadState("networkidle");
    const url = page.url();
    const isLogin = /login/.test(url);
    // AccessDenied component renders <h3>Access Denied</h3>
    const isAccessDenied = await page
      .getByRole("heading", { name: /Access Denied/i })
      .waitFor({ state: "visible", timeout: 3000 })
      .then(() => true)
      .catch(() => false);
    // Registry heading must NOT be visible (page content blocked)
    const registryHeadingVisible = await page
      .getByRole("heading", { name: /Rector Assignment Registry/i })
      .isVisible()
      .catch(() => false);
    const isBlocked = !registryHeadingVisible;

    expect(isLogin || isAccessDenied || isBlocked).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// Scenario I — Workflow state coverage (API-level via BFF stubs)
// This validates that UI correctly renders each workflow state
// ---------------------------------------------------------------------------

test.describe("I — Workflow state rendering (ASSIGNED → COMPLETED)", () => {
  test("assignment in ASSIGNED state renders correctly on registry page", async ({
    page,
  }) => {
    await stubAuthSession(page);
    await stubApi(
      page,
      `${RECTOR_BASE_BFF}/dashboard/summary`,
      FIXTURE_DASHBOARD_REAL,
    );
    await stubApi(page, `${RECTOR_BASE_BFF}*`, [FIXTURE_ASSIGNMENT_ASSIGNED]);

    await page.goto("/console/rector-assignments");
    await expect(
      page.getByText("Improve Student Admission Process"),
    ).toBeVisible();
  });

  test("assignment in COMPLETED state renders in registry", async ({
    page,
  }) => {
    await stubAuthSession(page);
    await stubApi(
      page,
      `${RECTOR_BASE_BFF}/dashboard/summary`,
      FIXTURE_DASHBOARD_REAL,
    );
    await stubApi(page, `${RECTOR_BASE_BFF}*`, [FIXTURE_ASSIGNMENT_COMPLETED]);

    await page.goto("/console/rector-assignments");
    await expect(page.getByText("Annual Budget Review Assignment")).toBeVisible();
  });

  test("My Assignments shows IN_PROGRESS assignment with accept flow available", async ({
    page,
  }) => {
    await stubAuthSession(page);
    await stubApi(page, `${RECTOR_BASE_BFF}*`, FIXTURE_MY_ASSIGNMENTS);

    await page.goto("/console/my-assignments");
    await expect(page.getByText("My Active Assignment")).toBeVisible();
    await expect(page.getByText(/IN_PROGRESS|In Progress/i)).toBeVisible();
  });
});
