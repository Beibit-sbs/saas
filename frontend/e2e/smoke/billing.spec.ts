import { test, expect, type Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Helpers — mirrors admin-console.spec.ts helpers
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
    sub: "test-user-id",
    exp: Math.floor(Date.now() / 1000) + 3600,
  });
  const payload = Buffer.from(payloadJson).toString("base64url");
  const fakeToken = `fakeheader.${payload}.fakesig`;

  await page.context().addCookies(
    Array.from(cookieOrigins).flatMap((url) => {
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
    }),
  );

  await page.route("**/api/auth/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        authenticated: true,
        user: {
          sub: "test-user-id",
          displayName: "Test Admin",
          roles: ["admin"],
          permissions: [
            "platform.admin.read",
            "platform.admin.write",
            "admin.tenants.read",
            "billing.read",
            "billing.write",
          ],
          tenantId: null,
          ...overrides,
        },
      }),
    });
  });
}

async function stubApi(page: Page, path: string, body: unknown, status = 200) {
  const pattern = path.startsWith("**/") ? path : `**${path}`;
  const patterns = new Set<string>([pattern]);

  // The frontend API client rewrites many paths to /api/bff/*.
  if (pattern.includes("/api/admin/")) {
    patterns.add(pattern.replace("/api/admin/", "/api/bff/admin/"));
  }
  if (pattern.includes("/api/v1/admin/")) {
    patterns.add(pattern.replace("/api/v1/admin/", "/api/bff/v1/admin/"));
  }
  if (pattern.includes("/platform/")) {
    patterns.add(pattern.replace("/platform/", "/api/bff/platform/"));
  }

  for (const currentPattern of patterns) {
    await page.route(currentPattern, async (route) => {
      await route.fulfill({
        status,
        contentType: "application/json",
        body: JSON.stringify(body),
      });
    });
  }
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

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const TENANTS_STUB = {
  tenants: [
    {
      id: 1,
      slug: "acme-university",
      name: "Acme University",
      status: "active",
      plan_id: 1,
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-15T00:00:00Z",
    },
    {
      id: 2,
      slug: "test-college",
      name: "Test College",
      status: "active",
      plan_id: 2,
      created_at: "2024-02-01T00:00:00Z",
      updated_at: "2024-02-15T00:00:00Z",
    },
  ],
};

const PLANS_STUB = [
  {
    id: 1,
    code: "starter",
    name: "Starter",
    price_cents: 9900,
    features: {
      analytics: false,
      sso: false,
    },
    limits: {
      students: 500,
      faculty: 50,
      courses: 100,
      storage_gb: 10,
    },
    active: true,
    created_at: "2024-01-01T00:00:00Z",
  },
  {
    id: 2,
    code: "professional",
    name: "Professional",
    price_cents: 29900,
    features: {
      analytics: true,
      sso: true,
    },
    limits: {
      students: 5000,
      faculty: 500,
      courses: 1000,
      storage_gb: 100,
    },
    active: true,
    created_at: "2024-01-01T00:00:00Z",
  },
];

const BILLING_STATE_STUB = {
  tenant_id: 1,
  plan_code: "starter",
  plan_id: 1,
  next_plan_code: null,
  subscription_status: "active",
  billing_state: "current",
  period_start: "2026-04-01T00:00:00Z",
  period_end: "2026-04-30T23:59:59Z",
  limits: {
    students: 500,
    faculty: 50,
    courses: 100,
    storage_gb: 10,
  },
  usage: {
    students: 120,
    faculty: 15,
    courses: 45,
    storage_gb: 3,
  },
  subscription: {
    tenant_id: 1,
    plan_id: 1,
    plan_code: "starter",
    status: "active",
    started_at: "2024-01-01T00:00:00Z",
    trial_ends_at: null,
    current_period_start: "2026-04-01T00:00:00Z",
    current_period_end: "2026-04-30T23:59:59Z",
    next_plan_id: null,
    next_plan_code: null,
    updated_at: "2026-04-01T00:00:00Z",
  },
};

const DELINQUENCY_DASHBOARD_STUB = {
  total: 2,
  open_total: 2,
  total_overdue_cents: 150000,
  by_status: {
    open: 2,
    escalated: 0,
    resolved: 0,
  },
};

const DELINQUENCY_RECORDS_STUB = {
  items: [
    {
      id: 1,
      tenant_id: 1,
      invoice_id: "INV-2026-001",
      status: "open",
      opened_at: "2026-04-11T00:00:00Z",
      last_reminder_at: null,
      reminder_count: 1,
      escalated_at: null,
      resolved_at: null,
      resolution: null,
      notes: null,
      amount_cents: 75000,
      events: [],
    },
    {
      id: 2,
      tenant_id: 1,
      invoice_id: "INV-2026-002",
      status: "open",
      opened_at: "2026-04-12T00:00:00Z",
      last_reminder_at: null,
      reminder_count: 0,
      escalated_at: null,
      resolved_at: null,
      resolution: null,
      notes: null,
      amount_cents: 75000,
      events: [],
    },
  ],
  total: 2,
};

const DUNNING_POLICY_STUB = {
  grace_period_days: 7,
  overdue_period_days: 15,
  suspension_period_days: 30,
  auto_cancel_after_days: 60,
  reminder_schedule: [3, 7, 14],
  require_approval_for_reactivation: false,
};

// ---------------------------------------------------------------------------
// Test setup
// ---------------------------------------------------------------------------

test.beforeEach(async ({ page }) => {
  await forceEnglishLocale(page);
});

// ---------------------------------------------------------------------------
// Billing Dashboard
// ---------------------------------------------------------------------------

test.describe("Billing Dashboard", () => {
  test("billing dashboard page renders navigation cards", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "**/api/admin/billing/plans*", PLANS_STUB);

    await page.goto("/console/billing");
    await expect(
      page.getByRole("heading", { name: "Billing", exact: true }),
    ).toBeVisible();
    // Navigation cards to sub-pages
    await expect(page.locator('a[href="/console/billing/plans"]')).toBeVisible();
    await expect(
      page.locator('a[href="/console/billing/subscriptions"]'),
    ).toBeVisible();
  });

  test("billing dashboard shows stat cards", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "**/api/admin/billing/plans*", PLANS_STUB);

    await page.goto("/console/billing");
    await expect(page.getByText("Active Plans", { exact: true })).toBeVisible();
    await expect(page.getByText("Monthly Revenue", { exact: true })).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Billing Plans
// ---------------------------------------------------------------------------

test.describe("Billing Plans", () => {
  test("plans page lists current subscription and plan catalog", async ({
    page,
  }) => {
    await stubAuthSession(page);
    await stubApi(page, "**/api/admin/tenants*", TENANTS_STUB);
    await stubApi(page, "**/platform/plans*", { plans: PLANS_STUB });
    await stubApi(page, "**/platform/tenants/1/billing*", BILLING_STATE_STUB);

    await page.goto("/console/billing/plans");
    await expect(page.getByText("Current Subscription")).toBeVisible();
    await expect(page.getByText("Plan Catalog")).toBeVisible();
    await expect(page.getByText("starter (Starter)")).toBeVisible();
    await expect(page.getByText("professional (Professional)")).toBeVisible();
  });

  test("plans page allows transitioning to another plan", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "**/api/admin/tenants*", TENANTS_STUB);
    await stubApi(page, "**/platform/plans*", { plans: PLANS_STUB });
    await stubApi(page, "**/platform/tenants/1/billing*", BILLING_STATE_STUB);

    let changeCalls = 0;
    await page.route(
      "**/platform/tenants/1/billing/subscription/plan-change*",
      async (route) => {
        if (route.request().method() === "POST") {
          changeCalls += 1;
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify(BILLING_STATE_STUB),
          });
          return;
        }
        await route.continue();
      },
    );

    await page.goto("/console/billing/plans");
    await page.getByRole("button", { name: /transition to professional/i }).click();

    await expect.poll(() => changeCalls).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// Billing Subscriptions
// ---------------------------------------------------------------------------

test.describe("Billing Subscriptions", () => {
  test("subscriptions page renders tenant selector", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "**/api/admin/tenants*", TENANTS_STUB);
    await stubApi(page, "**/api/admin/billing/plans*", PLANS_STUB);

    await page.goto("/console/billing/subscriptions");
    await expect(
      page.getByRole("heading", { name: /subscriptions/i }),
    ).toBeVisible();
    await expect(page.getByText("Select Tenant")).toBeVisible();
    await expect(
      page.getByRole("button", { name: /Acme University|Acme Corp/i }),
    ).toBeVisible();
    await expect(page.getByRole("button", { name: "Test College" })).toBeVisible();
  });

  test("subscriptions page shows billing state after tenant selection", async ({
    page,
  }) => {
    await stubAuthSession(page);
    await stubApi(page, "**/api/admin/tenants*", TENANTS_STUB);
    await stubApi(page, "**/api/admin/billing/plans*", PLANS_STUB);
    await stubApi(
      page,
      "**/api/admin/billing/tenants/1/state*",
      BILLING_STATE_STUB,
    );

    await page.goto("/console/billing/subscriptions");
    await page.getByRole("button", { name: /Acme University|Acme Corp/i }).click();

    await expect(page.getByText("Current Subscription")).toBeVisible();
    await expect(page.getByText("Billing State")).toBeVisible();
    await expect(page.getByText("Starter")).toBeVisible();
  });

  test("subscriptions page shows usage progress bars after tenant selection", async ({
    page,
  }) => {
    await stubAuthSession(page);
    await stubApi(page, "**/api/admin/tenants*", TENANTS_STUB);
    await stubApi(page, "**/api/admin/billing/plans*", PLANS_STUB);
    await stubApi(
      page,
      "**/api/admin/billing/tenants/1/state*",
      BILLING_STATE_STUB,
    );

    await page.goto("/console/billing/subscriptions");
    await page.getByRole("button", { name: /Acme University|Acme Corp/i }).click();

    await expect(page.getByText("Usage / Limits")).toBeVisible();
    // 120 of 500 students
    await expect(page.getByText(/120\s*\/\s*500|students/i)).toBeVisible();
  });

  test("subscriptions page allows assigning subscription plan", async ({
    page,
  }) => {
    await stubAuthSession(page);
    await stubApi(page, "**/api/admin/tenants*", TENANTS_STUB);
    await stubApi(page, "**/api/admin/billing/plans*", PLANS_STUB);
    await stubApi(
      page,
      "**/api/admin/billing/tenants/1/state*",
      BILLING_STATE_STUB,
    );

    let assignCalls = 0;
    await page.route(
      "**/billing/tenants/1/subscription*",
      async (route) => {
        if (route.request().method() === "PUT") {
          assignCalls += 1;
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify(BILLING_STATE_STUB),
          });
          return;
        }
        await route.continue();
      },
    );

    await page.goto("/console/billing/subscriptions");
    await page.getByRole("button", { name: /Acme University|Acme Corp/i }).click();

    await expect(page.getByText(/change plan/i)).toBeVisible();

    const assignRequest = page.waitForRequest(
      (req) =>
        req.method() === "PUT" &&
        req.url().includes("/billing/tenants/1/subscription"),
    );
    await page.getByRole("button", { name: /^assign$/i }).click();
    await assignRequest;
    await expect.poll(() => assignCalls).toBeGreaterThan(0);
  });

  test("subscriptions page shows transition status section", async ({
    page,
  }) => {
    await stubAuthSession(page);
    await stubApi(page, "**/api/admin/tenants*", TENANTS_STUB);
    await stubApi(page, "**/api/admin/billing/plans*", PLANS_STUB);
    await stubApi(
      page,
      "**/api/admin/billing/tenants/1/state*",
      BILLING_STATE_STUB,
    );

    await page.goto("/console/billing/subscriptions");
    await page.getByRole("button", { name: /Acme University|Acme Corp/i }).click();

    await expect(page.getByText("Transition Status")).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Billing Delinquency
// ---------------------------------------------------------------------------

test.describe("Billing Delinquency", () => {
  test("delinquency page renders tenant selector", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "**/api/admin/tenants*", TENANTS_STUB);

    await page.goto("/console/billing/delinquency");
    await expect(
      page.getByRole("heading", { name: /delinquency/i }),
    ).toBeVisible();
    await expect(page.getByText("Select Tenant")).toBeVisible();
    await expect(
      page.getByRole("button", { name: /Acme University|Acme Corp/i }),
    ).toBeVisible();
  });

  test("delinquency page shows dashboard summary after tenant selection", async ({
    page,
  }) => {
    await stubAuthSession(page);
    await stubApi(page, "**/api/admin/tenants*", TENANTS_STUB);
    await stubApi(
      page,
      "**/api/admin/billing/tenants/1/delinquency/dashboard*",
      DELINQUENCY_DASHBOARD_STUB,
    );
    await stubApi(
      page,
      "**/api/admin/billing/tenants/1/delinquency*",
      DELINQUENCY_RECORDS_STUB,
    );
    await stubApi(
      page,
      "**/api/admin/billing/tenants/1/delinquency/policy*",
      DUNNING_POLICY_STUB,
    );

    await page.goto("/console/billing/delinquency");
    await page.getByRole("button", { name: /Acme University|Acme Corp/i }).click();

    await expect(page.getByText("Total Records")).toBeVisible();
    await expect(page.getByText("Total Overdue")).toBeVisible();
  });

  test("delinquency page shows records list after tenant selection", async ({
    page,
  }) => {
    await stubAuthSession(page);
    await stubApi(page, "**/api/admin/tenants*", TENANTS_STUB);
    await stubApi(
      page,
      "**/api/admin/billing/tenants/1/delinquency/dashboard*",
      DELINQUENCY_DASHBOARD_STUB,
    );
    await stubApi(
      page,
      "**/api/admin/billing/tenants/1/delinquency*",
      DELINQUENCY_RECORDS_STUB,
    );
    await stubApi(
      page,
      "**/api/admin/billing/tenants/1/delinquency/policy*",
      DUNNING_POLICY_STUB,
    );

    await page.goto("/console/billing/delinquency");
    await page.getByRole("button", { name: /Acme University|Acme Corp/i }).click();

    // Invoice refs from stub
    await expect(page.getByText("INV-2026-001")).toBeVisible();
    await expect(page.getByText("INV-2026-002")).toBeVisible();
  });

  test("delinquency page shows dunning policy", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "**/api/admin/tenants*", TENANTS_STUB);
    await stubApi(
      page,
      "**/api/admin/billing/tenants/1/delinquency/dashboard*",
      DELINQUENCY_DASHBOARD_STUB,
    );
    await stubApi(
      page,
      "**/api/admin/billing/tenants/1/delinquency*",
      DELINQUENCY_RECORDS_STUB,
    );
    await stubApi(
      page,
      "**/api/admin/billing/tenants/1/delinquency/policy*",
      DUNNING_POLICY_STUB,
    );

    await page.goto("/console/billing/delinquency");
    await page.getByRole("button", { name: /Acme University|Acme Corp/i }).click();

    await expect(page.getByText("Dunning Policy")).toBeVisible();
    // Grace period days from stub
    await expect(page.getByText(/7/)).toBeVisible();
  });

  test("delinquency page allows resolving a record", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "**/api/admin/tenants*", TENANTS_STUB);
    await stubApi(
      page,
      "**/api/admin/billing/tenants/1/delinquency/dashboard*",
      DELINQUENCY_DASHBOARD_STUB,
    );
    await stubApi(
      page,
      "**/api/admin/billing/tenants/1/delinquency*",
      DELINQUENCY_RECORDS_STUB,
    );
    await stubApi(
      page,
      "**/api/admin/billing/tenants/1/delinquency/policy*",
      DUNNING_POLICY_STUB,
    );

    let resolveCalls = 0;
    await page.route(
      "**/api/admin/billing/tenants/1/delinquency/1/resolve",
      async (route) => {
        if (route.request().method() === "POST") {
          resolveCalls += 1;
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({ ...DELINQUENCY_RECORDS_STUB.items[0], status: "resolved", resolved_at: "2026-04-24T10:00:00Z" }),
          });
          return;
        }
        await route.continue();
      },
    );

    await page.goto("/console/billing/delinquency");
    await page.getByRole("button", { name: /Acme University|Acme Corp/i }).click();

    // Click resolve button for the first record
    await page.locator('button[title="Resolve"]').first().click();
    // Modal with resolution selector
    await expect(page.getByText(/Resolve Record #/i)).toBeVisible();

    const resolveRequest = page.waitForRequest(
      (req) =>
        req.method() === "POST" &&
        req.url().includes("/delinquency/1/resolve"),
    );
    await page
      .getByRole("button", { name: /^resolve$/i })
      .last()
      .click();
    await resolveRequest;
    await expect.poll(() => resolveCalls).toBeGreaterThan(0);
  });
});
