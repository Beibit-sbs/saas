import { test, type Page } from "@playwright/test";

type NetworkEvent = {
  kind: "request" | "response" | "failed";
  method?: string;
  url: string;
  status?: number;
  error?: string;
};

async function stubAuthSession(page: Page) {
  const cookieUrl = process.env.E2E_BASE_URL ?? "http://nginx";
  const secureCookie = new URL(cookieUrl).protocol === "https:";
  const payloadJson = JSON.stringify({ sub: "test-user-id", exp: Math.floor(Date.now() / 1000) + 3600 });
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
            "students.read",
            "grades.read",
            "transcripts.read",
            "enrollments.read",
            "scheduling.read",
            "tenants.read",
            "jobs.read",
            "notifications.read",
            "feature_flags.read",
            "health.read",
            "metrics.read",
          ],
          tenantId: null,
        },
      }),
    });
  });
}

async function runForensics(page: Page, pagePath: string, expectedPathPart: string, label: string) {
  const events: NetworkEvent[] = [];

  page.on("request", (request) => {
    const url = request.url();
    if (url.includes("/api/") || request.isNavigationRequest()) {
      events.push({ kind: "request", method: request.method(), url });
    }
  });

  page.on("response", (response) => {
    const url = response.url();
    if (url.includes("/api/") || response.request().isNavigationRequest()) {
      events.push({
        kind: "response",
        method: response.request().method(),
        url,
        status: response.status(),
      });
    }
  });

  page.on("requestfailed", (request) => {
    const url = request.url();
    if (url.includes("/api/") || request.isNavigationRequest()) {
      events.push({
        kind: "failed",
        method: request.method(),
        url,
        error: request.failure()?.errorText ?? "unknown",
      });
    }
  });

  const cookieUrl = process.env.E2E_BASE_URL ?? "http://nginx";
  const cookiesBefore = await page.context().cookies(cookieUrl);

  let gotoError: string | null = null;
  try {
    await page.goto(pagePath, { waitUntil: "domcontentloaded", timeout: 20000 });
  } catch (error) {
    gotoError = error instanceof Error ? error.message : String(error);
  }

  await page.waitForTimeout(3000);

  const cookiesAfter = await page.context().cookies(cookieUrl);
  const finalUrl = page.url();
  const hasLoginHeading = (await page.getByRole("heading", { name: /AI University Console/i }).count()) > 0;

  let authProbe: { status: number; body: unknown } | { error: string };
  try {
    const result = await page.evaluate(async () => {
      const res = await fetch("/api/auth/me", {
        credentials: "include",
        cache: "no-store",
      });
      let body: unknown = null;
      try {
        body = await res.json();
      } catch {
        body = null;
      }
      return { status: res.status, body };
    });
    authProbe = result;
  } catch (error) {
    authProbe = { error: error instanceof Error ? error.message : String(error) };
  }

  const expectedMatched = events.some((event) => event.url.includes(expectedPathPart));

  console.log(`\n=== FORENSICS ${label} ===`);
  console.log(`PATH: ${pagePath}`);
  console.log(`FINAL_URL: ${finalUrl}`);
  console.log(`GOTO_ERROR: ${gotoError ?? "none"}`);
  console.log(`LOGIN_HEADING_VISIBLE: ${hasLoginHeading}`);
  console.log(`COOKIE_BEFORE_COUNT: ${cookiesBefore.length}`);
  console.log(`COOKIE_AFTER_COUNT: ${cookiesAfter.length}`);
  console.log(`HAS_ADMIN_COOKIE_BEFORE: ${cookiesBefore.some((item) => item.name === "admin_token")}`);
  console.log(`HAS_ADMIN_COOKIE_AFTER: ${cookiesAfter.some((item) => item.name === "admin_token")}`);
  console.log(`AUTH_PROBE: ${JSON.stringify(authProbe)}`);
  console.log(`EXPECTED_PATH_PART: ${expectedPathPart}`);
  console.log(`EXPECTED_PATH_MATCHED: ${expectedMatched}`);
  console.log("NETWORK_EVENTS_START");
  for (const event of events) {
    if (event.kind === "response") {
      console.log(`RES ${event.method ?? "?"} ${event.status ?? "?"} ${event.url}`);
    } else if (event.kind === "failed") {
      console.log(`FAIL ${event.method ?? "?"} ${event.error ?? "?"} ${event.url}`);
    } else {
      console.log(`REQ ${event.method ?? "?"} ${event.url}`);
    }
  }
  console.log("NETWORK_EVENTS_END");
}

test.describe("PHASE 8 network forensics", () => {
  test("students page trace", async ({ page }) => {
    await stubAuthSession(page);
    await runForensics(page, "/console/students", "/api/bff/admin/students", "students");
  });

  test("grades page trace", async ({ page }) => {
    await stubAuthSession(page);
    await runForensics(page, "/console/grades", "/api/bff/admin/grades", "grades");
  });

  test("transcript page trace", async ({ page }) => {
    await stubAuthSession(page);
    await runForensics(page, "/console/students/s1/transcript", "/api/bff/admin/students/s1/transcript", "transcript");
  });
});
