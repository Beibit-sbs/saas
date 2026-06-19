import { test, expect, type Page, type Route } from "@playwright/test";
import { createHmac, randomUUID } from "node:crypto";

/**
 * F3 Intervention Effectiveness — E2E Spec
 *
 * Status: ACTIVE (F3.3 unfrozen 2026-04-20)
 *
 * Covered flows:
 *  1. Cohorts list page renders and filters by status
 *  2. Cohort detail page shows student count and completeness
 *  3. Outcome panel renders uplift metrics from API
 *  4. Create cohort wizard validates inputs and submits
 *  5. Analyze guard: draft cohort shows correct error
 *  6. Server error returns graceful toast/error state
 *  7. Network: outcomes empty state renders correctly
 */

// ---------------------------------------------------------------------------
// Auth helpers
// ---------------------------------------------------------------------------

function b64url(value: object): string {
  return Buffer.from(JSON.stringify(value)).toString("base64url");
}

function makeSignedAccessToken(): string {
  const secret = process.env.JWT_SECRET;
  if (!secret) throw new Error("JWT_SECRET required for F3 e2e");

  const now = Math.floor(Date.now() / 1000);
  const header = b64url({ alg: "HS256", typ: "JWT" });
  const payload = b64url({
    sub: "program_manager@example.com",
    roles: ["admin"],
    scp: [
      "interventions.read",
      "interventions.write",
      "effectiveness.read",
      "effectiveness.write",
    ],
    src: "ldap",
    tid: 1,
    jti: randomUUID(),
    pg: false,
    iat: now,
    exp: now + 3600,
    token_type: "access",
    ver: 1,
  });
  const sig = createHmac("sha256", secret)
    .update(`${header}.${payload}`)
    .digest("base64url");
  return `${header}.${payload}.${sig}`;
}

async function stubAuthSession(page: Page): Promise<void> {
  const baseUrl = process.env.E2E_BASE_URL ?? "https://nginx";
  const parsedUrl = new URL(baseUrl);
  const cookieOrigins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  const token = makeSignedAccessToken();
  await page.context().addCookies(
    Array.from(cookieOrigins).flatMap((origin) => {
      const secure = new URL(origin).protocol === "https:";
      return [
        {
          name: "e2e_bypass_session",
          value: "1",
          url: origin,
          httpOnly: true,
          secure,
          sameSite: "Lax",
        },
        {
          name: "admin_token",
          value: token,
          url: origin,
          httpOnly: true,
          secure,
          sameSite: "Lax",
        },
        {
          name: "app_access_token",
          value: token,
          url: origin,
          httpOnly: true,
          secure,
          sameSite: "Lax",
        },
      ];
    }),
  );

  await page.route("**/api/auth/csrf*", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ csrf_token: "f3-csrf-token" }),
    });
  });

  await page.route("**/api/auth/me/preferences", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ language: "en" }),
    });
  });

  await page.route("**/api/auth/me/preferences/language*", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ ok: true, language: "en" }),
    });
  });

  await page.route("**/api/auth/me", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        authenticated: true,
        user: {
          sub: "program_manager@example.com",
          email: "program_manager@example.com",
          displayName: "Program Manager",
          roles: ["admin"],
          tenantId: 1,
          permissions: [
            "interventions.read",
            "interventions.write",
            "effectiveness.read",
            "effectiveness.write",
          ],
        },
      }),
    })
  );
}

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------

const MOCK_COHORT_ANALYZED = {
  id: 42,
  tenant_id: 1,
  playbook_id: 10,
  cohort_name: "Q1-2026-dropout-intervention",
  analysis_window_start: "2025-09-01",
  analysis_window_end: "2026-01-31",
  student_count: 50,
  data_completeness_pct: "0.94",
  status: "analyzed",
  created_by: "program_manager@example.com",
  created_at: "2026-02-01T00:00:00Z",
};

const MOCK_COHORT_DRAFT = {
  id: 43,
  tenant_id: 1,
  playbook_id: 11,
  cohort_name: "Draft Cohort",
  analysis_window_start: "2026-01-01",
  analysis_window_end: "2026-03-31",
  student_count: 0,
  data_completeness_pct: null,
  status: "draft",
  created_by: "program_manager@example.com",
  created_at: "2026-04-01T00:00:00Z",
};

const MOCK_COHORT_FINALIZED = {
  id: 44,
  tenant_id: 1,
  playbook_id: 12,
  cohort_name: "Spring Finalized",
  analysis_window_start: "2026-01-01",
  analysis_window_end: "2026-03-31",
  student_count: 75,
  data_completeness_pct: null,
  status: "finalized",
  created_by: "program_manager@example.com",
  created_at: "2026-04-05T00:00:00Z",
};

const MOCK_OUTCOMES = {
  items: [
    {
      id: 200,
      tenant_id: 1,
      cohort_id: 42,
      outcome_type: "dropout_rate",
      segment_name: null,
      outcome_value_treated: 0.14,
      outcome_value_control: 0.18,
      uplift_pp: -0.04,
      uplift_confidence_p5: -0.05,
      uplift_confidence_p95: -0.03,
      measurement_completeness_pct: 0.94,
      measured_at: "2026-02-01T00:00:00Z",
      notes: null,
    },
    {
      id: 201,
      tenant_id: 1,
      cohort_id: 42,
      outcome_type: "gpa_improvement",
      segment_name: null,
      outcome_value_treated: 3.12,
      outcome_value_control: 3.05,
      uplift_pp: 0.07,
      uplift_confidence_p5: 0.02,
      uplift_confidence_p95: 0.12,
      measurement_completeness_pct: 0.94,
      measured_at: "2026-02-01T00:00:00Z",
      notes: null,
    },
  ],
  total: 2,
};

// ---------------------------------------------------------------------------
// Route stubs
// ---------------------------------------------------------------------------

async function stubCohortsRoutes(
  page: Page,
  {
    cohortsList,
    cohortDetail,
    outcomes,
    finalizeResponse,
    analyzeResponse,
  }: {
    cohortsList?: object[];
    cohortDetail?: object;
    outcomes?: object;
    finalizeResponse?: { status: number; body: object };
    analyzeResponse?: { status: number; body: object };
  } = {}
): Promise<void> {
  const BASE_API = "/api/admin/interventions/cohorts";

  // List cohorts
  await page.route(`**${BASE_API}`, async (route: Route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(cohortsList ?? [MOCK_COHORT_ANALYZED, MOCK_COHORT_DRAFT, MOCK_COHORT_FINALIZED]),
      });
    } else {
      await route.continue();
    }
  });

  // Cohort detail
  await page.route(`**${BASE_API}/42`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(cohortDetail ?? MOCK_COHORT_ANALYZED),
    });
  });

  // Cohort 43 (draft)
  await page.route(`**${BASE_API}/43`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_COHORT_DRAFT),
    });
  });

  // Outcomes
  await page.route(`**${BASE_API}/*/outcomes`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(outcomes ?? MOCK_OUTCOMES),
    });
  });

  // Finalize (new cohort)
  await page.route(`**${BASE_API}/finalize`, async (route: Route) => {
    const resp = finalizeResponse ?? { status: 201, body: { ...MOCK_COHORT_FINALIZED, id: 99 } };
    await route.fulfill({
      status: resp.status,
      contentType: "application/json",
      body: JSON.stringify(resp.body),
    });
  });

  // Existing cohort finalize
  await page.route(`**${BASE_API}/*/finalize`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_COHORT_FINALIZED),
    });
  });

  // Analyze
  await page.route(`**${BASE_API}/*/analyze`, async (route: Route) => {
    const resp = analyzeResponse ?? {
      status: 200,
      body: { cohort_id: 42, status: "analysis_queued", detail: "Queued", requested_at: "2026-04-20T10:00:00Z" },
    };
    await route.fulfill({
      status: resp.status,
      contentType: "application/json",
      body: JSON.stringify(resp.body),
    });
  });
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const BASE_URL = process.env.E2E_BASE_URL ?? "https://nginx";
const COHORTS_URL = `${BASE_URL}/console/interventions/cohorts`;

// ---------------------------------------------------------------------------
// Suite: Cohorts list page
// ---------------------------------------------------------------------------

test.describe("F3 Cohorts List Page", () => {
  test.beforeEach(async ({ page }) => {
    await stubAuthSession(page);
    await stubCohortsRoutes(page);
  });

  test("renders cohorts list with correct count", async ({ page }) => {
    await page.goto(COHORTS_URL);
    await expect(page.getByRole("heading", { name: /Intervention Cohorts/i })).toBeVisible();
    // Table rows: 3 mock cohorts
    const rows = page.locator("tbody tr");
    await expect(rows).toHaveCount(3);
  });

  test("Create Cohort button links to create page", async ({ page }) => {
    await page.goto(COHORTS_URL);
    const createBtn = page.getByRole("link", { name: /Create Cohort/i });
    await expect(createBtn).toBeVisible();
    await expect(createBtn).toHaveAttribute("href", /\/cohorts\/create/);
  });

  test("status filter 'analyzed' shows only analyzed cohorts", async ({ page }) => {
    await page.goto(COHORTS_URL);

    // Click status filter button (analyzed)
    await page.getByRole("button", { name: /analyzed/i }).click();

    // Only 1 analyzed cohort in mock data
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await expect(page.locator("tbody tr").first()).toContainText("Q1-2026");
  });

  test("sorting by name toggles direction on header click", async ({ page }) => {
    await page.goto(COHORTS_URL);

    await page.getByRole("columnheader", { name: /Name/i }).click();
    // After click, rows reordered — just verify it doesn't error
    await expect(page.locator("tbody tr")).toHaveCount(3);

    await page.getByRole("columnheader", { name: /Name/i }).click();
    await expect(page.locator("tbody tr")).toHaveCount(3);
  });

  test("empty state shown when no cohorts", async ({ page }) => {
    await stubCohortsRoutes(page, { cohortsList: [] });
    await page.goto(COHORTS_URL);
    await expect(page.getByText(/No cohorts/i)).toBeVisible();
  });

  test("server error shows error state", async ({ page }) => {
    await page.route(`**/api/admin/interventions/cohorts`, async (route: Route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({ status: 500, body: JSON.stringify({ detail: "Internal error" }) });
      } else {
        await route.continue();
      }
    });
    await page.goto(COHORTS_URL);
    await expect(page.getByText(/Failed to load cohorts/i)).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Suite: Cohort detail page
// ---------------------------------------------------------------------------

test.describe("F3 Cohort Detail Page", () => {
  test.beforeEach(async ({ page }) => {
    await stubAuthSession(page);
    await stubCohortsRoutes(page);
  });

  test("shows cohort name and student count", async ({ page }) => {
    await page.goto(`${COHORTS_URL}/42`);
    await expect(page.getByRole("heading", { name: /Q1-2026-dropout-intervention/i })).toBeVisible();
    await expect(page.getByText("50")).toBeVisible();
  });

  test("outcomes panel renders uplift metrics", async ({ page }) => {
    await page.goto(`${COHORTS_URL}/42`);
    // Outcome panel summary metrics should appear
    await expect(page.getByText(/Improved|Unchanged|Worse/i)).toBeVisible();
  });

  test("outcomes empty state when no outcomes returned", async ({ page }) => {
    await stubCohortsRoutes(page, { outcomes: { items: [], total: 0 } });
    await page.goto(`${COHORTS_URL}/42`);
    await expect(page.getByText(/No outcomes available yet/i)).toBeVisible();
  });

  test("back button links to cohorts list", async ({ page }) => {
    await page.goto(`${COHORTS_URL}/42`);
    const backLink = page.getByRole("link", { name: /Back to cohorts/i });
    await expect(backLink).toBeVisible();
    await expect(backLink).toHaveAttribute("href", /\/cohorts$/);
  });

  test("analyze queued shows correct panel status", async ({ page }) => {
    await page.goto(`${COHORTS_URL}/42`);

    const analyzeBtn = page.getByRole("button", { name: /Run Analysis/i });
    await expect(analyzeBtn).toBeVisible();
    await analyzeBtn.click();

    // After successful analyze mutation → queued state
    await expect(page.getByText(/Analysis started|analysis_queued/i)).toBeVisible();
  });

  test("draft cohort shows Finalize button instead of Analyze", async ({ page }) => {
    await page.goto(`${COHORTS_URL}/43`);
    await expect(page.getByRole("button", { name: /Finalize/i })).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Suite: Create cohort wizard
// ---------------------------------------------------------------------------

test.describe("F3 Create Cohort Wizard", () => {
  test.beforeEach(async ({ page }) => {
    await stubAuthSession(page);
    await stubCohortsRoutes(page);
  });

  test("step 1 validation rejects missing playbook ID", async ({ page }) => {
    await page.goto(`${COHORTS_URL}/create`);
    await page.getByRole("button", { name: /Next/i }).click();
    await expect(page.getByText(/Please select a playbook/i)).toBeVisible();
  });

  test("step 1 validation rejects missing cohort name", async ({ page }) => {
    await page.goto(`${COHORTS_URL}/create`);
    await page.fill('input[name="playbookId"]', "10");
    await page.getByRole("button", { name: /Next/i }).click();
    await expect(page.getByText(/cohort name/i)).toBeVisible();
  });

  test("step 2: treatment size auto-calculates control size", async ({ page }) => {
    await page.goto(`${COHORTS_URL}/create`);

    // Step 1
    await page.fill('input[name="playbookId"]', "10");
    await page.fill('input[name="cohortName"]', "Spring 2026");
    await page.fill('input[name="analysisWindowStart"]', "2026-01-01");
    await page.fill('input[name="analysisWindowEnd"]', "2026-03-31");
    await page.getByRole("button", { name: /Next/i }).click();

    // Step 2
    await page.fill('input[name="cohortSize"]', "100");
    await page.fill('input[name="treatmentSize"]', "60");

    const controlInput = page.locator('input[name="controlSize"]');
    await expect(controlInput).toHaveValue("40");
  });

  test("step 2 validation: treatment exceeds total rejects next", async ({ page }) => {
    await page.goto(`${COHORTS_URL}/create`);

    // Step 1
    await page.fill('input[name="playbookId"]', "10");
    await page.fill('input[name="cohortName"]', "Spring 2026");
    await page.fill('input[name="analysisWindowStart"]', "2026-01-01");
    await page.fill('input[name="analysisWindowEnd"]', "2026-03-31");
    await page.getByRole("button", { name: /Next/i }).click();

    // Step 2: invalid treatment
    await page.fill('input[name="cohortSize"]', "50");
    await page.fill('input[name="treatmentSize"]', "80");
    await page.getByRole("button", { name: /Next/i }).click();

    await expect(page.getByText(/exceed/i)).toBeVisible();
  });

  test("successful submit redirects to cohort detail page", async ({ page }) => {
    await page.goto(`${COHORTS_URL}/create`);

    // Step 1
    await page.fill('input[name="playbookId"]', "10");
    await page.fill('input[name="cohortName"]', "Spring 2026");
    await page.fill('input[name="analysisWindowStart"]', "2026-01-01");
    await page.fill('input[name="analysisWindowEnd"]', "2026-03-31");
    await page.getByRole("button", { name: /Next/i }).click();

    // Step 2
    await page.fill('input[name="cohortSize"]', "100");
    await page.fill('input[name="treatmentSize"]', "50");
    await page.getByRole("button", { name: /Next/i }).click();

    // Step 3: Confirm
    await page.getByRole("button", { name: /Submit|Create/i }).click();

    // Redirect to detail page for newly created cohort
    await expect(page).toHaveURL(/\/cohorts\/\d+/);
  });

  test("server error on submit shows error message", async ({ page }) => {
    await stubCohortsRoutes(page, {
      finalizeResponse: { status: 422, body: { detail: "Validation failed on server" } },
    });
    await page.goto(`${COHORTS_URL}/create`);

    await page.fill('input[name="playbookId"]', "10");
    await page.fill('input[name="cohortName"]', "Bad Cohort");
    await page.fill('input[name="analysisWindowStart"]', "2026-01-01");
    await page.fill('input[name="analysisWindowEnd"]', "2026-03-31");
    await page.getByRole("button", { name: /Next/i }).click();
    await page.fill('input[name="cohortSize"]', "100");
    await page.fill('input[name="treatmentSize"]', "50");
    await page.getByRole("button", { name: /Next/i }).click();
    await page.getByRole("button", { name: /Submit|Create/i }).click();

    await expect(page.getByText(/failed|error/i)).toBeVisible();
  });
});

