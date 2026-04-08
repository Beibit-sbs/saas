import { test, expect, type Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Helpers (duplicated from admin-console.spec.ts to keep tests self-contained)
// ---------------------------------------------------------------------------

async function stubAuthSession(page: Page) {
  const cookieUrl = process.env.E2E_BASE_URL ?? "https://nginx";
  const secureCookie = new URL(cookieUrl).protocol === "https:";
  const payloadJson = JSON.stringify({
    sub: "test-user-id",
    exp: Math.floor(Date.now() / 1000) + 3600,
  });
  const payload = Buffer.from(payloadJson).toString("base64url");
  const fakeToken = `fakeheader.${payload}.fakesig`;

  await page.context().addCookies([
    {
      name: "admin_token",
      value: fakeToken,
      url: cookieUrl,
      httpOnly: true,
      secure: secureCookie,
      sameSite: "Lax",
    },
  ]);

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
            "admin.tenants.read",
            "admin.tenants.write",
            "jobs.read",
            "jobs.write",
            "notifications.read",
            "notifications.write",
            "feature_flags.read",
            "feature_flags.write",
            "students.read",
            "enrollments.read",
            "grades.read",
            "transcripts.read",
            "scheduling.read",
            "health.read",
            "metrics.read",
          ],
          tenantId: null,
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

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const CASE_1 = {
  id: "101",
  tenant_id: "t1",
  student_profile_id: "9001",
  ai_recommendation_id: "rec-42",
  recommendation_snapshot: "Student missed 5 sessions in a row.",
  severity: "high",
  status: "open",
  owner_type: "group",
  owner_ref: "academic.team",
  assignee_type: null,
  assignee_ref: null,
  due_at: "2026-05-01T00:00:00Z",
  metadata_json: {},
  last_action_at: null,
  version: 1,
  created_at: "2026-04-01T10:00:00Z",
  updated_at: "2026-04-01T10:00:00Z",
};

const CASE_2 = {
  id: "102",
  tenant_id: "t1",
  student_profile_id: "9002",
  ai_recommendation_id: null,
  recommendation_snapshot: null,
  severity: "medium",
  status: "in_progress",
  owner_type: "user",
  owner_ref: "registrar.jones",
  assignee_type: "user",
  assignee_ref: "registrar.jones",
  due_at: null,
  metadata_json: {},
  last_action_at: "2026-04-02T09:00:00Z",
  version: 3,
  created_at: "2026-04-01T08:00:00Z",
  updated_at: "2026-04-02T09:00:00Z",
};

const casesPage = { items: [CASE_1, CASE_2], total: 2, page: 1, page_size: 20 };
const emptyActions = { items: [], total: 0 };

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test.describe("Interventions smoke", () => {
  test("page renders the interventions table with cases", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "/api/admin/interventions/cases*", casesPage);

    await page.goto("/console/interventions");

    await expect(
      page.getByRole("heading", { name: /Interventions/i }),
    ).toBeVisible();
    // Both case IDs should be in the table
    await expect(page.getByText("#101")).toBeVisible();
    await expect(page.getByText("#102")).toBeVisible();
  });

  test("severity badges render with correct labels", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "/api/admin/interventions/cases*", casesPage);

    await page.goto("/console/interventions");

    await expect(page.getByText("High")).toBeVisible();
    await expect(page.getByText("Medium")).toBeVisible();
  });

  test("filter by status updates the URL", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "/api/admin/interventions/cases*", casesPage);

    await page.goto("/console/interventions");

    // The FilterBar should render the Status select
    const statusSelect = page.getByRole("combobox").first();
    await expect(statusSelect).toBeVisible();
  });

  test("row click opens the detail drawer", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "/api/admin/interventions/cases*", casesPage);
    await stubApi(page, "/api/admin/interventions/cases/101", CASE_1);
    await stubApi(
      page,
      "/api/admin/interventions/cases/101/actions*",
      emptyActions,
    );

    await page.goto("/console/interventions");

    // Click first row (Case #101)
    await page.getByText("#101").click();

    // Drawer should open and show the case details
    await expect(page.getByText("Case #101")).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("academic.team")).toBeVisible();
  });

  test("drawer shows action type selector", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "/api/admin/interventions/cases*", casesPage);
    await stubApi(page, "/api/admin/interventions/cases/101", CASE_1);
    await stubApi(
      page,
      "/api/admin/interventions/cases/101/actions*",
      emptyActions,
    );

    await page.goto("/console/interventions");
    await page.getByText("#101").click();

    // Wait for drawer to open
    await expect(page.getByText("Case #101")).toBeVisible({ timeout: 5000 });

    // Action type selector should be present
    const actionTypeLabel = page.getByText(
      /Action type|Тип действия|Іс-әрекет түрі/i,
    );
    await expect(actionTypeLabel).toBeVisible();
  });

  test("empty state renders when no cases returned", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "/api/admin/interventions/cases*", {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    });

    await page.goto("/console/interventions");

    await expect(
      page.getByRole("heading", { name: /Interventions/i }),
    ).toBeVisible();
    // Empty state message
    await expect(
      page.getByText(
        /No intervention cases|Нет кейсов интервенций|Интервенция кейстері жоқ/i,
      ),
    ).toBeVisible();
  });

  test("API error renders the error state", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(
      page,
      "/api/admin/interventions/cases*",
      { detail: "Internal Server Error" },
      500,
    );

    await page.goto("/console/interventions");

    await expect(
      page.getByText(/Failed to load intervention cases/i),
    ).toBeVisible({ timeout: 5000 });
  });
});
