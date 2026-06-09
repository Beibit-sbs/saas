import { expect, test, type Page, type Route } from "@playwright/test";

async function setSessionCookies(page: Page, baseUrl: string) {
  const parsedUrl = new URL(baseUrl);
  const cookieOrigins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  const payloadJson = JSON.stringify({
    sub: "a0463-admin",
    exp: Math.floor(Date.now() / 1000) + 3600,
  });
  const payload = Buffer.from(payloadJson).toString("base64url");
  const token = `fakeheader.${payload}.fakesig`;

  await page.context().addCookies(
    Array.from(cookieOrigins).flatMap((origin) => {
      const secure = new URL(origin).protocol === "https:";
      return [
        { name: "admin_token", value: token, url: origin, httpOnly: true, secure, sameSite: "Lax" as const },
        { name: "app_access_token", value: token, url: origin, httpOnly: true, secure, sameSite: "Lax" as const },
      ];
    }),
  );
}

async function stubAuthFlow(page: Page, baseUrl: string) {
  let isAuthenticated = false;

  await page.route("**/api/auth/csrf*", async (route: Route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ csrf_token: "a0463-csrf" }) });
  });

  await page.route("**/api/public/tenants/login-directory*", async (route: Route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ items: [] }) });
  });

  await page.route("**/api/auth/login", async (route: Route) => {
    isAuthenticated = true;
    await setSessionCookies(page, baseUrl);
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true }) });
  });

  await page.route("**/api/auth/me", async (route: Route) => {
    const hasSessionCookie = (await page.context().cookies()).some(
      (cookie) => cookie.name === "admin_token" || cookie.name === "app_access_token",
    );

    if (!isAuthenticated && !hasSessionCookie) {
      await route.fulfill({ status: 401, contentType: "application/json", body: JSON.stringify({ authenticated: false, user: null }) });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        authenticated: true,
        user: {
          sub: "a0463-admin",
          displayName: "A0463 Admin",
          roles: ["admin"],
          tenantId: 1,
          permissions: ["admin.integrations.manage", "platform.admin.read"],
        },
      }),
    });
  });

  await page.route("**/api/auth/me/preferences*", async (route: Route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ language: "en" }) });
  });
}

test.describe("A-046.3 integration provider readiness shell", () => {
  test("root integrations page exposes provider readiness inventory and boundaries", async ({ page }) => {
    const baseUrl = process.env.E2E_BASE_URL;
    expect(baseUrl).toBeTruthy();

    await stubAuthFlow(page, baseUrl!);
    await setSessionCookies(page, baseUrl!);

    await page.goto(`${baseUrl}/console/integrations`);

    await expect(page.getByTestId("integrations-root-page")).toBeVisible();
    await expect(page.getByTestId("integrations-provider-readiness-card")).toBeVisible();
    await expect(page.getByTestId("integrations-boundary-labels")).toContainText("No live provider calls");
    await expect(page.getByTestId("integrations-workflow-sections")).toContainText("W12 Dashboard publication workflow");
    await expect(page.getByTestId("integrations-dashboard-cards")).toContainText("Evidence Dashboard");
  });

  test("provider readiness page shows read-only workflow and anti-fake posture", async ({ page }) => {
    const baseUrl = process.env.E2E_BASE_URL;
    expect(baseUrl).toBeTruthy();

    await stubAuthFlow(page, baseUrl!);
    await setSessionCookies(page, baseUrl!);

    await page.goto(`${baseUrl}/console/integrations/provider-readiness`);

    await expect(page.getByTestId("ipr-page-shell")).toBeVisible();
    await expect(page.getByTestId("ipr-boundary-labels")).toContainText("No external submission");
    await expect(page.getByTestId("ipr-workflow-sections")).toContainText("W4 Readiness Assessment Workflow");
    await expect(page.getByTestId("ipr-dashboard-cards")).toContainText("Provider Readiness Dashboard");
    await expect(page.getByTestId("ipr-readiness-indicators")).toContainText("Status: NON_LIVE_READINESS");
    await expect(page.locator("body")).not.toContainText(/sync now|connect provider|live telemetry/i);
  });
});
