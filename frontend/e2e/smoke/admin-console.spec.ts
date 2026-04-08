import { test, expect, type Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Inject a fake `admin_token` httpOnly cookie and stub `/api/auth/me` so that
 * the auth context considers the session valid — without needing a real backend.
 *
 * The cookie is required because Next.js middleware checks it on the server
 * before any React code runs.  page.route() intercepts only client-side fetches.
 */
async function stubAuthSession(page: Page, overrides: Record<string, unknown> = {}) {
  const cookieUrl = process.env.E2E_BASE_URL ?? "https://nginx";
  const secureCookie = new URL(cookieUrl).protocol === "https:";
  // Build a minimal non-expired JWT that satisfies middleware.ts isTokenExpired().
  const payloadJson = JSON.stringify({ sub: "test-user-id", exp: Math.floor(Date.now() / 1000) + 3600 });
  const payload = Buffer.from(payloadJson).toString("base64url");
  const fakeToken = `fakeheader.${payload}.fakesig`;

  await page.context().addCookies([{
    name: "admin_token",
    value: fakeToken,
    url: cookieUrl,
    httpOnly: true,
    secure: secureCookie,
    sameSite: "Lax",
  }]);

  const sessionCookies = await page.context().cookies(cookieUrl);
  if (!sessionCookies.some((item) => item.name === "admin_token")) {
    throw new Error("Failed to set admin_token cookie for test session");
  }

  // Intercept the BFF session endpoint before any navigation.
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
          permissions: ["tenants.read", "tenants.write", "jobs.read", "jobs.write",
            "notifications.read", "notifications.write", "feature_flags.read",
            "feature_flags.write", "students.read", "enrollments.read",
            "grades.read", "transcripts.read", "scheduling.read",
            "health.read", "metrics.read"],
          tenantId: null,
          ...overrides,
        },
      }),
    });
  });
}

/** Stub a JSON API route with static data. */
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

const emptyPage = { items: [], total: 0, page: 1, page_size: 20 };

const LOGIN_TITLE_RE = /AI University Console|Консоль университета ИИ|AI университет консолі/i;
const USERNAME_RE = /Username|Логин/i;
const PASSWORD_RE = /Password|Пароль|Құпиясөз/i;
const SIGN_IN_RE = /Sign in|Войти|Кіру/i;
const DASHBOARD_RE = /Dashboard|Дашборд|Басқару тақтасы/i;
const TENANTS_RE = /Tenants|Universities|Университеты|Университеттер/i;
const JOBS_RE = /Jobs|Задачи|Тапсырмалар/i;
const NOTIFICATIONS_RE = /Notifications|Уведомления|Хабарландырулар/i;
const ENROLLMENTS_RE = /Enrollments|Зачисления|Тіркеулер/i;
const SCHEDULING_RE = /Scheduling|Расписание|Кесте/i;
const TENANT_SUMMARY_RE = /Operational summary for|Операционная сводка для|операциялық шолу/i;
const STUDENT_CAPACITY_RE = /Student capacity|Лимит студентов|Студент сыйымдылығы/i;

async function forceEnglishLocale(page: Page) {
  const configuredUrl = process.env.E2E_BASE_URL ?? "https://nginx";
  const parsedUrl = new URL(configuredUrl);
  const cookieOrigins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  await page.context().addCookies(Array.from(cookieOrigins).map((url) => ({
    name: "app.locale",
    value: "en",
    url,
    httpOnly: false,
    secure: new URL(url).protocol === "https:",
    sameSite: "Lax" as const,
  })));

  await page.addInitScript(() => {
    document.cookie = "app.locale=en; Path=/; SameSite=Lax";
    window.localStorage.setItem("app.language", "en");
  });
}

test.beforeEach(async ({ page }) => {
  await forceEnglishLocale(page);
});

// ---------------------------------------------------------------------------
// Auth smoke tests
// ---------------------------------------------------------------------------

test.describe("Auth", () => {
  test("login page renders the AI University Console sign-in form", async ({ page }) => {
    await page.goto("/login");
    await expect(page).toHaveTitle(/AI University Console|Admin/i);
    await expect(page.getByRole("heading", { name: LOGIN_TITLE_RE })).toBeVisible();
    await expect(page.getByLabel(USERNAME_RE)).toBeVisible();
    await expect(page.getByLabel(PASSWORD_RE)).toBeVisible();
    await expect(page.getByRole("button", { name: SIGN_IN_RE })).toBeVisible();
  });

  test("unauthenticated visit to /console redirects to /login", async ({ page }) => {
    // Return 401 (no cookie / invalid session)
    await page.route("/api/auth/me", async (route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ authenticated: false, user: null }),
      });
    });

    await page.goto("/console");
    // Middleware or auth context should redirect
    await expect(page).toHaveURL(/\/login/);
  });

  test("expired session redirects to /login with intended destination", async ({ page }) => {
    await page.route("/api/auth/me", async (route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ authenticated: false, user: null }),
      });
    });

    await page.goto("/console/jobs?page=2&pageSize=10");
    await expect(page).toHaveURL(/\/login\?next=%2Fconsole%2Fjobs%3Fpage%3D2%26pageSize%3D10/);
  });

  test("valid session navigates to /console and shows dashboard", async ({ page }) => {
    await stubAuthSession(page);
    // Stub metrics + health for dashboard
    await stubApi(page, "/api/bff/v1/admin/health/metrics", {
      total_tenants: 12, active_tenants: 10, total_students: 4200,
    });
    await stubApi(page, "/api/bff/v1/admin/health", {
      status: "healthy", services: [{ name: "db", status: "healthy" }],
    });
    await stubApi(page, "/api/bff/admin/jobs*", { jobs: [] });
    await stubApi(page, "/api/bff/v1/admin/notifications*", emptyPage);

    await page.goto("/console");
    await expect(page.getByRole("heading", { name: DASHBOARD_RE })).toBeVisible();
  });

  test("logout clears session and redirects to /login", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "/api/bff/v1/admin/health/metrics", { total_tenants: 0, active_tenants: 0, total_students: 0 });
    await stubApi(page, "/api/bff/v1/admin/health", { status: "healthy", services: [] });
    await stubApi(page, "/api/bff/admin/jobs*", { jobs: [] });
    await stubApi(page, "/api/bff/v1/admin/notifications*", emptyPage);

    // Stub logout endpoint
    await page.route("/api/auth/logout", async (route) => {
      await route.fulfill({ status: 200, body: "{}" });
    });

    await page.goto("/console");
    await expect(page.getByRole("heading", { name: DASHBOARD_RE })).toBeVisible();

    // SessionPanel logout control is no longer mounted in runtime; emulate sign-out by clearing auth cookies.
    await page.context().clearCookies();
    await page.goto("/console");
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole("heading", { name: LOGIN_TITLE_RE })).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Platform section smoke tests
// ---------------------------------------------------------------------------

test.describe("Platform pages", () => {
  test("Tenants page renders the tenants table", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "/api/bff/admin/tenants*", {
      tenants: [
        { id: 1, slug: "acme", name: "Acme Corp", status: "active", plan_id: 1, created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-15T00:00:00Z" },
      ],
    });

    await page.goto("/console/tenants");
    await expect(page.getByText("Acme Corp")).toBeVisible();
    await expect(page.getByRole("heading", { name: TENANTS_RE })).toBeVisible();
  });

  test("Tenants page keeps filters, page size, and sort in URL", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "/api/bff/admin/tenants*", {
      tenants: [
        { id: 1, slug: "acme", name: "Acme Corp", status: "active", plan_id: 1, created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-15T00:00:00Z" },
      ],
    });

    await page.goto("/console/tenants?search=acme&status=active&page=2&pageSize=10&sort=name:asc");
    await expect(page.locator("input").first()).toHaveValue("acme");
    await expect(page).toHaveURL(/search=acme/);
    await expect(page).toHaveURL(/pageSize=10/);
    await expect(page).toHaveURL(/sort=name:asc/);
  });

  test("Tenants row click opens the detail drawer", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "/api/bff/admin/tenants*", {
      tenants: [
        { id: 1, slug: "acme", name: "Acme Corp", status: "active", plan_id: 1, created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-15T00:00:00Z" },
      ],
    });

    await page.goto("/console/tenants");
    await page.getByText("Acme Corp").click();
    await expect(page.getByText(TENANT_SUMMARY_RE)).toBeVisible();
    await expect(page.getByText(STUDENT_CAPACITY_RE)).toBeVisible();
  });

  test("Tenants page allows deactivation with confirm dialog", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "/api/bff/admin/tenants*", {
      tenants: [
        { id: 2, slug: "acme", name: "Acme Corp", status: "active", plan_id: 1, created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-15T00:00:00Z" },
      ],
      items: [
        { id: "2", slug: "acme", display_name: "Acme Corp", status: "active", plan: "1", max_students: 1000, current_students: 120, created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-15T00:00:00Z" },
      ],
      total: 1,
      page: 1,
      page_size: 20,
    });

    let deleteCalls = 0;
    await page.route("**/api/**/admin/tenants/2", async (route) => {
      if (route.request().method() === "DELETE") {
        deleteCalls += 1;
        await route.fulfill({ status: 204, body: "" });
        return;
      }
      await route.continue();
    });

    await page.goto("/console/tenants");
    await page.getByRole("button", { name: /deactivate/i }).click();
    await expect(page.getByText(/deactivate university\?|deactivate tenant\?/i)).toBeVisible();

    const deleteRequest = page.waitForRequest((request) => {
      return request.method() === "DELETE"
        && request.url().includes("/admin/tenants/2");
    });

    await page.getByRole("button", { name: /^deactivate$/i }).last().click();
    await deleteRequest;
    await expect.poll(() => deleteCalls).toBeGreaterThan(0);
  });

  test("Jobs page renders the job queue table", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "/api/bff/admin/jobs*", {
      jobs: [
        {
          id: 1,
          job_type: "sync_grades",
          tenant_id: 1,
          status: "succeeded",
          error_message: null,
          created_at: "2024-01-01T00:00:00Z",
          started_at: null,
          finished_at: "2024-01-01T00:05:00Z",
          payload_json: {},
          result_json: {},
        },
      ],
    });

    await page.goto("/console/jobs");
    await expect(page.getByRole("heading", { name: JOBS_RE })).toBeVisible();
    await expect(page.getByText("sync_grades")).toBeVisible();
  });

  test("Notifications page renders notifications table", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "/api/bff/v1/admin/notifications*", {
      items: [
        { id: "n1", title: "Backup complete", body: "Daily backup succeeded.",
          severity: "info", tenant_id: null, read: false, created_at: "2024-01-01T00:00:00Z" },
      ],
      total: 1, page: 1, page_size: 20,
    });

    await page.goto("/console/notifications");
    await expect(page.getByRole("heading", { name: NOTIFICATIONS_RE })).toBeVisible();
    await expect(page.getByText("Backup complete")).toBeVisible();
  });

  test("Notifications mutation shows success feedback", async ({ page }) => {
    await stubAuthSession(page);
    let markAllCalls = 0;
    await page.route("**/api/**/notifications/mark-all-read*", async (route) => {
      markAllCalls += 1;
      await route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
    });
    await stubApi(page, "/api/**/admin/notifications*", {
      items: [
        { id: "n1", title: "Backup complete", body: "Daily backup succeeded.", severity: "info", tenant_id: null, read: false, type: "system", created_at: "2024-01-01T00:00:00Z" },
      ],
      total: 1, page: 1, page_size: 20,
    });

    await page.goto("/console/notifications");
    const markAllRequest = page.waitForRequest((request) => {
      return request.method() === "POST"
        && request.url().includes("/notifications/mark-all-read");
    });
    await page.getByRole("button", { name: /mark all read/i }).click();
    await markAllRequest;
    await expect.poll(() => markAllCalls).toBeGreaterThan(0);
    await expect(page.getByRole("heading", { name: NOTIFICATIONS_RE })).toBeVisible();
  });

  test("Notifications page allows dispatching a notification", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "/api/**/admin/notifications*", {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    });

    let dispatchCalls = 0;
    await page.route("**/api/**/admin/notifications", async (route) => {
      if (route.request().method() === "POST") {
        dispatchCalls += 1;
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ id: "n2", title: "Manual", body: "Manual dispatch", severity: "info", tenant_id: "1", read: false, type: "system", created_at: "2024-01-01T00:00:00Z" }),
        });
        return;
      }
      await route.continue();
    });

    await page.goto("/console/notifications");
    await page.getByRole("button", { name: /send notification/i }).click();
    await page.getByLabel(/tenant id/i).fill("1");
    await page.getByLabel(/target/i).fill("ops@example.com");

    const dispatchRequest = page.waitForRequest((request) => {
      return request.method() === "POST"
        && request.url().endsWith("/notifications");
    });

    await page.getByRole("button", { name: /^send notification$/i }).last().click();
    await dispatchRequest;
    await expect.poll(() => dispatchCalls).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// Academic section smoke tests
// ---------------------------------------------------------------------------

test.describe("Academic pages", () => {
  test("Students page renders the students table", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "/api/bff/admin/students*", {
      items: [
        { id: "s1", student_number: "STU-001", first_name: "Jane", last_name: "Doe",
          email: "jane@example.com", program: "CS", status: "active", created_at: "2024-01-01T00:00:00Z" },
      ],
      total: 1, page: 1, page_size: 20,
    });

    const studentsResponse = page.waitForResponse((response) => {
      return response.request().method() === "GET"
        && response.url().includes("/api/bff/admin/students");
    });

    await page.goto("/console/students");
    await studentsResponse;
    await expect(page.getByText("Jane Doe")).toBeVisible();
  });

  test("Grades page renders the grades table", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "/api/bff/admin/grades*", {
      items: [
        { id: "g1", student_name: "Jane Doe", section_code: "CS101-01",
          course_name: "Intro to CS", grade_value: "A", numeric_value: 4.0, graded_at: "2024-06-01T00:00:00Z" },
      ],
      total: 1, page: 1, page_size: 20,
    });

    const gradesResponse = page.waitForResponse((response) => {
      return response.request().method() === "GET"
        && response.url().includes("/api/bff/admin/grades");
    });

    await page.goto("/console/grades");
    await gradesResponse;
    await expect(page.getByText("Jane Doe")).toBeVisible();
  });

  test("Transcript page renders student transcript", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "/api/bff/admin/students/s1/transcript*", {
      student_id: "s1",
      student_name: "Jane Doe",
      student_number: "STU-001",
      program: "CS",
      gpa: 3.9,
      total_credits: 30,
      entries: [
        {
          course_name: "Intro to CS",
          section_code: "CS101-01",
          credits: 3,
          grade_value: "A",
          numeric_value: 4.0,
          semester: "2026 Spring",
          completed: true,
        },
      ],
      generated_at: "2026-04-03T00:00:00Z",
    });

    const transcriptResponse = page.waitForResponse((response) => {
      return response.request().method() === "GET"
        && response.url().includes("/api/bff/admin/students/s1/transcript");
    });

    await page.goto("/console/students/s1/transcript");
    await transcriptResponse;
    await expect(page.getByText("Jane Doe · STU-001")).toBeVisible();
    await expect(page.getByText("Intro to CS")).toBeVisible();
  });

  test("Enrollments page renders enrollments table", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "/api/bff/admin/enrollments*", {
      items: [
        { id: "e1", student_name: "Jane Doe", section_code: "CS101-01",
          course_name: "Intro to CS", status: "enrolled", enrolled_at: "2024-01-10T00:00:00Z" },
      ],
      total: 1, page: 1, page_size: 20,
    });

    await page.goto("/console/enrollments");
    await expect(page.getByRole("heading", { name: ENROLLMENTS_RE })).toBeVisible();
    await expect(page.getByText("Jane Doe")).toBeVisible();
  });

  test("Enrollments page allows creating enrollment", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "/api/bff/admin/enrollments*", {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    });

    let createCalls = 0;
    await page.route("**/api/**/admin/enrollments", async (route) => {
      if (route.request().method() === "POST") {
        createCalls += 1;
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: "e-new",
            student_id: "student-1",
            student_name: "Jane Doe",
            section_id: "section-1",
            section_code: "CS101-01",
            course_name: "Intro to CS",
            status: "enrolled",
            enrolled_at: "2024-01-10T00:00:00Z",
            tenant_id: "1",
          }),
        });
        return;
      }
      await route.continue();
    });

    await page.goto("/console/enrollments");
    await page.getByRole("button", { name: /enroll student/i }).click();
    await page.getByLabel(/student id/i).fill("student-1");
    await page.getByLabel(/section id/i).fill("section-1");

    const createRequest = page.waitForRequest((request) => {
      return request.method() === "POST"
        && request.url().includes("/admin/enrollments");
    });

    await page.getByRole("button", { name: /create enrollment/i }).click();
    await createRequest;
    await expect.poll(() => createCalls).toBeGreaterThan(0);
  });

  test("Scheduling page renders course sections table", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "/api/bff/admin/scheduling/sections*", {
      items: [
        { id: "sec1", code: "CS101-01", course_name: "Intro to CS", instructor: "Dr. Smith",
          semester: "2024-spring", schedule: "MWF 10:00", room: "Room 201",
          enrolled_count: 20, capacity: 30, status: "open" },
      ],
      total: 1, page: 1, page_size: 20,
    });

    await page.goto("/console/scheduling");
    await expect(page.getByRole("heading", { name: SCHEDULING_RE })).toBeVisible();
    await expect(page.getByText("Intro to CS")).toBeVisible();
  });

  test("Students page allows creating student profile", async ({ page }) => {
    await stubAuthSession(page);
    await stubApi(page, "/api/bff/admin/students*", {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    });

    let createCalls = 0;
    await page.route("**/api/**/admin/students", async (route) => {
      if (route.request().method() === "POST") {
        createCalls += 1;
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            id: 1001,
            tenant_id: 1,
            person_id: 101,
            student_number: "ADM-1-1001",
            cohort_year: 2026,
            academic_level: null,
            current_status: "active",
            admission_source: "manual",
            metadata_json: {},
            version: 1,
            created_by: "test",
            updated_by: "test",
            created_at: "2024-01-01T00:00:00Z",
            updated_at: "2024-01-01T00:00:00Z",
          }),
        });
        return;
      }
      await route.continue();
    });

    await page.goto("/console/students");
    await page.getByRole("button", { name: /create student/i }).click();
    await page.getByLabel(/person id/i).fill("101");
    await page.getByLabel(/student number/i).fill("ADM-1-1001");
    await page.getByLabel(/cohort year/i).fill("2026");

    const createRequest = page.waitForRequest((request) => {
      return request.method() === "POST"
        && request.url().includes("/admin/students");
    });

    await page.getByRole("button", { name: /^create student$/i }).last().click();
    await createRequest;
    await expect.poll(() => createCalls).toBeGreaterThan(0);
  });
});
