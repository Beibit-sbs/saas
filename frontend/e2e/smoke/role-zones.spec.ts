import { expect, test, type Page } from "@playwright/test";
import { createHmac, randomUUID } from "node:crypto";

function b64url(value: object) {
  return Buffer.from(JSON.stringify(value)).toString("base64url");
}

function makeSignedAccessToken(role: string) {
  const secret = process.env.JWT_SECRET;
  if (!secret) {
    throw new Error("JWT_SECRET is required for authenticated role-zone e2e");
  }

  const now = Math.floor(Date.now() / 1000);
  const header = b64url({ alg: "HS256", typ: "JWT" });
  const payload = b64url({
    sub: `e2e.${role}`,
    roles: [role],
    scp: ["students.read", "grades.read"],
    src: "ldap",
    tid: 42,
    jti: randomUUID(),
    pg: false,
    iat: now,
    exp: now + 3600,
    token_type: "access",
    ver: 1,
  });
  const signingInput = `${header}.${payload}`;
  const signature = createHmac("sha256", secret).update(signingInput).digest("base64url");
  return `${signingInput}.${signature}`;
}

async function seedSessionCookie(page: Page, role: string) {
  const cookieUrl = process.env.E2E_BASE_URL ?? "https://nginx";
  const parsed = new URL(cookieUrl);
  const token = makeSignedAccessToken(role);

  await page.context().addCookies([
    {
      name: "admin_token",
      value: token,
      domain: parsed.hostname,
      path: "/",
      httpOnly: true,
      sameSite: "Lax",
      secure: parsed.protocol === "https:",
    },
  ]);
}

async function stubStudentRiskData(page: Page) {

  await page.route("**/api/auth/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        authenticated: true,
        user: {
          sub: "student-user-id",
          displayName: "Test Student",
          roles: ["student"],
          permissions: ["students.read", "grades.read"],
          tenantId: 42,
        },
      }),
    });
  });

  await page.route("**/api/bff/analytics/kpis?timeRange=30d", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        totalStudents: 1,
        attendanceRate: 91,
        completionRate: 82,
        avgGrade: 58,
        satisfactionRate: 74,
      }),
    });
  });

  await page.route("**/api/bff/analytics/kpis", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        generated_at: "2026-04-05T00:00:00Z",
        snapshot_date: "2026-04-05",
        kpis: [
          { key: "total_students", value: 1, title: "Total Students", source_status: "ok" },
          { key: "total_enrollments", value: 1, title: "Total Enrollments", source_status: "ok" },
          { key: "total_grades_submitted", value: 1, title: "Total Grades Submitted", source_status: "ok" },
        ],
      }),
    });
  });

  await page.route("**/api/bff/admin/platform/ai/copilot/ask", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        insights: [
          {
            title: "At-Risk Students",
            value: "3",
          },
          {
            title: "High Expulsion Risk Students",
            value: "1",
          },
        ],
        warnings: ["expulsion_risk_detected"],
        recommendations: [
          {
            recommendation_type: "expulsion_risk_escalation",
            title: "Escalate expulsion-risk cases to academic committee",
            reason: "High-risk students detected (grade < 50).",
          },
        ],
      }),
    });
  });
}

async function stubRoleSessionAndKpis(page: Page, role: string, tenantId = 42) {
  await page.route("**/api/auth/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        authenticated: true,
        user: {
          sub: `${role}-user-id`,
          displayName: `Test ${role}`,
          roles: [role],
          permissions: ["students.read", "grades.read"],
          tenantId,
        },
      }),
    });
  });

  await page.route("**/api/bff/analytics/kpis", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        generated_at: "2026-04-05T00:00:00Z",
        snapshot_date: "2026-04-05",
        kpis: [
          { key: "total_students", value: 10, title: "Total Students", source_status: "ok" },
          { key: "total_enrollments", value: 12, title: "Total Enrollments", source_status: "ok" },
          { key: "total_grades_submitted", value: 8, title: "Total Grades Submitted", source_status: "ok" },
          { key: "analytics_events_ingested_total", value: 24, title: "Events", source_status: "ok" },
          { key: "analytics_kpi_reads_total", value: 9, title: "Reads", source_status: "ok" },
          { key: "total_failed_jobs", value: 1, title: "Failed Jobs", source_status: "ok" },
        ],
      }),
    });
  });
}

test.describe("Role zones", () => {
  test("unauthenticated user is redirected to /login for /student", async ({ page }) => {
    await page.goto("/student");
    await expect(page).toHaveURL(/\/login/);
  });

  test("unauthenticated user is redirected to /login for /faculty", async ({ page }) => {
    await page.goto("/faculty");
    await expect(page).toHaveURL(/\/login/);
  });

  test("unauthenticated user is redirected to /login for /registrar", async ({ page }) => {
    await page.goto("/registrar");
    await expect(page).toHaveURL(/\/login/);
  });

  test("student sees academic risk banner with expulsion warning and recommendation", async ({ page }) => {
    test.skip(!process.env.JWT_SECRET, "Provide JWT_SECRET to run authenticated role-zone flows.");
    await seedSessionCookie(page, "student");
    await stubStudentRiskData(page);
    await page.goto("/student");
    await expect(page).toHaveURL(/\/student(\/|$)/);

    await expect(page.getByText("Academic Risk Watch")).toBeVisible();
    await expect(page.getByText("Severity: high", { exact: false })).toBeVisible();
    await expect(page.getByText("At-risk students: 3", { exact: false })).toBeVisible();
    await expect(page.getByText("High expulsion risk: 1", { exact: false })).toBeVisible();
    await expect(page.getByText("expulsion_risk_detected")).toBeVisible();
    await expect(page.getByText("Escalate expulsion-risk cases to academic committee")).toBeVisible();
  });

  test("faculty can access /faculty and sees faculty portal cards", async ({ page }) => {
    test.skip(!process.env.JWT_SECRET, "Provide JWT_SECRET to run authenticated role-zone flows.");
    await seedSessionCookie(page, "faculty");
    await stubRoleSessionAndKpis(page, "faculty");

    await page.goto("/faculty");
    await expect(page).toHaveURL(/\/faculty(\/|$)/);
    await expect(page.getByText("Faculty Portal")).toBeVisible();
    await expect(page.getByText("Class Roster")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Grading Cycle" })).toBeVisible();
  });

  test("registrar can access /registrar and sees registrar portal cards", async ({ page }) => {
    test.skip(!process.env.JWT_SECRET, "Provide JWT_SECRET to run authenticated role-zone flows.");
    await seedSessionCookie(page, "registrar");
    await stubRoleSessionAndKpis(page, "registrar");

    await page.goto("/registrar");
    await expect(page).toHaveURL(/\/registrar(\/|$)/);
    await expect(page.getByText("Registrar and Dean Office")).toBeVisible();
    await expect(page.getByText("Admissions Pipeline")).toBeVisible();
    await expect(page.getByText("Institution Governance")).toBeVisible();
  });
});
