import { test, expect, type Page, type Route } from "@playwright/test";
import { createHmac, randomUUID } from "node:crypto";

/**
 * F3 Intervention Effectiveness — E2E Spec (Design Skeleton)
 *
 * Status: FROZEN until F3.3 unfreeze (2026-04-21 after F2.10 PASS)
 *
 * Scenario: Program Manager views cohort analysis for Q1-2026 dropout
 * intervention. API responses are fully mocked — no live backend required
 * during the design phase.
 *
 * Covered flows:
 *  1. Program Manager navigates to effectiveness dashboard
 *  2. Cohort summary card renders correct student count + completeness
 *  3. Outcome metrics display 4pp dropout-rate uplift
 *  4. Segment breakdown (year:1 vs year:2) renders without error
 *  5. Frozen endpoints return graceful "not available yet" message (pre-F3.3)
 */

// ---------------------------------------------------------------------------
// Auth helpers (same pattern as interventions.spec.ts)
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
  const secure = new URL(baseUrl).protocol === "https:";

  await page.context().addCookies([
    {
      name: "e2e_bypass_session",
      value: "1",
      url: baseUrl,
      httpOnly: true,
      secure,
      sameSite: "Lax",
    },
    {
      name: "app_access_token",
      value: makeSignedAccessToken(),
      url: baseUrl,
      httpOnly: true,
      secure,
      sameSite: "Lax",
    },
  ]);

  await page.route("**/api/auth/me", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        user_id: "program_manager@example.com",
        email: "program_manager@example.com",
        roles: ["admin"],
        tenant_id: 1,
      }),
    })
  );
}

// ---------------------------------------------------------------------------
// Mock API response data (50-student cohort, 4pp dropout uplift)
// ---------------------------------------------------------------------------

const MOCK_COHORT = {
  id: 42,
  tenant_id: 1,
  playbook_id: 10,
  cohort_name: "Q1-2026-dropout-intervention",
  analysis_window_start: "2025-09-01",
  analysis_window_end: "2026-01-31",
  student_count: 50,
  data_completeness_pct: "94.00",
  created_by: "program_manager@example.com",
  created_at: "2026-02-01T00:00:00Z",
};

const MOCK_OUTCOMES = {
  items: [
    {
      id: 200,
      tenant_id: 1,
      cohort_id: 42,
      outcome_type: "dropout_rate",
      segment_name: null,
      outcome_value_treated: "0.1400",
      outcome_value_control: "0.1800",
      uplift_pp: "-4.000",
      uplift_confidence_p5: "-5.000",
      uplift_confidence_p95: "-3.000",
      measurement_completeness_pct: "94.00",
      measured_at: "2026-02-01T00:00:00Z",
      notes: null,
    },
    {
      id: 201,
      tenant_id: 1,
      cohort_id: 42,
      outcome_type: "gpa_improvement",
      segment_name: null,
      outcome_value_treated: "3.1200",
      outcome_value_control: "3.0500",
      uplift_pp: "0.070",
      uplift_confidence_p5: "0.020",
      uplift_confidence_p95: "0.120",
      measurement_completeness_pct: "94.00",
      measured_at: "2026-02-01T00:00:00Z",
      notes: null,
    },
  ],
  total: 2,
};

const FROZEN_ANALYZE_RESPONSE = {
  cohort_id: 42,
  status: "frozen",
  detail: "F3 analyze_cohort is frozen until F3.3 delivery is officially unfrozen.",
  requested_at: "2026-02-01T00:00:00Z",
};

// ---------------------------------------------------------------------------
// Route stubs
// ---------------------------------------------------------------------------

async function stubEffectivenessRoutes(page: Page): Promise<void> {
  // Latest cohort by playbook
  await page.route(
    "**/api/v1/effectiveness/cohorts/latest*",
    (route: Route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_COHORT),
      })
  );

  // Outcomes list
  await page.route(
    "**/api/v1/effectiveness/cohorts/*/outcomes",
    (route: Route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_OUTCOMES),
      })
  );

  // Analyze — frozen response (pre-F3.3)
  await page.route(
    "**/api/v1/effectiveness/cohorts/*/analyze",
    (route: Route) =>
      route.fulfill({
        status: 422,
        contentType: "application/json",
        body: JSON.stringify({ detail: FROZEN_ANALYZE_RESPONSE.detail }),
      })
  );

  // Finalize — frozen response (pre-F3.3)
  await page.route(
    "**/api/v1/effectiveness/cohorts/finalize",
    (route: Route) =>
      route.fulfill({
        status: 422,
        contentType: "application/json",
        body: JSON.stringify({ detail: "F3 finalize_cohort is frozen until F3.3 delivery is officially unfrozen." }),
      })
  );
}

// ---------------------------------------------------------------------------
// Tests
// NOTE: These tests target the F3 UI that will be built in F3.4 (after F3.3 unfreeze).
//       Until then they are SKIPPED (test.skip) to preserve the spec as a design contract.
// ---------------------------------------------------------------------------

const BASE_URL = process.env.E2E_BASE_URL ?? "https://nginx";
const EFFECTIVENESS_URL = `${BASE_URL}/console/effectiveness`;

test.describe("F3 Intervention Effectiveness Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await stubAuthSession(page);
    await stubEffectivenessRoutes(page);
  });

  // Skip until F3.4 UI is built
  test.skip(
    true,
    "F3 UI frozen until F3.3 unfreeze (2026-04-21). Unskip when /console/effectiveness route exists."
  );

  test("PM navigates to effectiveness dashboard", async ({ page }) => {
    await page.goto(EFFECTIVENESS_URL);
    await expect(page).toHaveURL(/effectiveness/);
    await expect(page.getByRole("heading", { name: /effectiveness/i })).toBeVisible();
  });

  test("Cohort summary card shows correct student count", async ({ page }) => {
    await page.goto(EFFECTIVENESS_URL);
    await expect(page.getByTestId("cohort-student-count")).toContainText("50");
    await expect(page.getByTestId("cohort-completeness")).toContainText("94");
  });

  test("Outcome metrics show 4pp dropout-rate reduction", async ({ page }) => {
    await page.goto(EFFECTIVENESS_URL);
    // Expect the dropout uplift card to show −4pp
    await expect(page.getByTestId("outcome-dropout_rate-uplift")).toContainText("-4");
    // Confidence interval rendered
    await expect(page.getByTestId("outcome-dropout_rate-ci")).toContainText("-5");
  });

  test("GPA improvement metric is visible", async ({ page }) => {
    await page.goto(EFFECTIVENESS_URL);
    await expect(page.getByTestId("outcome-gpa_improvement-uplift")).toContainText("0.07");
  });

  test("Frozen analyze endpoint shows graceful message in UI", async ({ page }) => {
    await page.goto(EFFECTIVENESS_URL);
    await page.getByRole("button", { name: /analyze/i }).click();
    // Expect graceful "not available yet" rather than a raw error
    await expect(page.getByTestId("analyze-frozen-notice")).toBeVisible();
    await expect(page.getByTestId("analyze-frozen-notice")).toContainText(/frozen|not available/i);
  });

  test("Data completeness below threshold shows warning", async ({ page }) => {
    // Override with low-completeness mock
    await page.route("**/api/v1/effectiveness/cohorts/*/outcomes", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ...MOCK_OUTCOMES,
          items: MOCK_OUTCOMES.items.map((i) => ({
            ...i,
            measurement_completeness_pct: "59.00",
          })),
        }),
      })
    );
    await page.goto(EFFECTIVENESS_URL);
    await expect(page.getByTestId("completeness-warning")).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Smoke test: frozen API endpoints return expected HTTP status (no UI needed)
// ---------------------------------------------------------------------------

test.describe("F3 API frozen endpoints — smoke (mock stubs)", () => {
  test("GET /api/v1/effectiveness/cohorts/latest returns 200 (mock)", async ({ page }) => {
    await stubEffectivenessRoutes(page);
    const resp = await page.request.get(`${BASE_URL}/api/v1/effectiveness/cohorts/latest?playbook_id=10`);
    // Mock returns 200 with cohort data
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body.student_count).toBe(50);
  });

  test("POST /api/v1/effectiveness/cohorts/finalize returns 422 (frozen)", async ({ page }) => {
    await stubEffectivenessRoutes(page);
    const resp = await page.request.post(`${BASE_URL}/api/v1/effectiveness/cohorts/finalize`, {
      data: {
        playbook_id: 10,
        cohort_name: "test",
        analysis_window_start: "2026-01-01",
        analysis_window_end: "2026-03-31",
      },
    });
    expect(resp.status()).toBe(422);
    const body = await resp.json();
    expect(body.detail).toMatch(/frozen/i);
  });
});
