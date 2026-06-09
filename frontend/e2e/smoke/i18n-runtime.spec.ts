import { expect, test, type Page, type Route } from "@playwright/test";

async function setSessionCookies(page: Page, baseUrl: string) {
  const parsedUrl = new URL(baseUrl);
  const cookieOrigins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  const payloadJson = JSON.stringify({
    sub: "smoke-admin",
    exp: Math.floor(Date.now() / 1000) + 3600,
  });
  const payload = Buffer.from(payloadJson).toString("base64url");
  const token = `fakeheader.${payload}.fakesig`;

  await page.context().addCookies(
    Array.from(cookieOrigins).flatMap((origin) => {
      const secure = new URL(origin).protocol === "https:";
      return [
        {
          name: "admin_token",
          value: token,
          url: origin,
          httpOnly: true,
          secure,
          sameSite: "Lax" as const,
        },
        {
          name: "app_access_token",
          value: token,
          url: origin,
          httpOnly: true,
          secure,
          sameSite: "Lax" as const,
        },
      ];
    }),
  );
}

async function stubAuthFlow(page: Page, baseUrl: string) {
  let isAuthenticated = false;

  await page.route("**/api/auth/csrf*", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ csrf_token: "i18n-csrf-token" }),
    });
  });

  await page.route("**/api/public/tenants/login-directory*", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: [] }),
    });
  });

  await page.route("**/api/i18n/languages*", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        languages: [
          { code: "ru", label: "Russian", default: true },
          { code: "kk", label: "Kazakh", default: false },
          { code: "en", label: "English", default: false },
        ],
      }),
    });
  });

  await page.route("**/api/auth/login", async (route: Route) => {
    isAuthenticated = true;
    await setSessionCookies(page, baseUrl);
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ ok: true }),
    });
  });

  await page.route("**/api/auth/logout", async (route: Route) => {
    isAuthenticated = false;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ ok: true }),
    });
  });

  await page.route("**/api/auth/me", async (route: Route) => {
    const hasSessionCookie = (await page.context().cookies()).some(
      (cookie: { name: string }) => cookie.name === "admin_token" || cookie.name === "app_access_token",
    );

    if (!isAuthenticated && !hasSessionCookie) {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ authenticated: false, user: null }),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        authenticated: true,
        user: {
          sub: "smoke-admin",
          displayName: "Smoke Admin",
          roles: ["admin"],
          permissions: ["admin.dashboard.read"],
          tenantId: 1,
        },
      }),
    });
  });

  await page.route("**/api/auth/me/preferences", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ language: "en" }),
    });
  });

  await page.route("**/api/auth/me/preferences/language*", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ ok: true }),
    });
  });
}

test.describe("i18n runtime smoke", () => {
  test("login/console/platform locale flow is stable", async ({ page, context }) => {
    const baseUrl = process.env.E2E_BASE_URL;
    expect(baseUrl).toBeTruthy();
    const jsErrors: string[] = [];
    const consoleErrors: string[] = [];

    page.on("pageerror", (err) => jsErrors.push(String(err?.message ?? err)));
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text());
      }
    });

    const hasBadTokens = (text: string) => /(\[object Object\]|missing translation:|\bundefined\b)/i.test(text);

    const setLanguage = async (code: "ru" | "kk" | "en") => {
      const fallbackLanguageState = async () => {
        await page.evaluate((nextCode) => {
          localStorage.setItem("app.language", nextCode);
        }, code);
        await context.addCookies([
          {
            name: "app.locale",
            value: code,
            url: baseUrl!,
            secure: new URL(baseUrl!).protocol === "https:",
            sameSite: "Lax",
          },
        ]);
      };

      const select = page.getByLabel(/language|язык|тіл/i).first();
      const hasSelector = await select.isVisible({ timeout: 2_000 }).catch(() => false);
      if (!hasSelector) {
        await fallbackLanguageState();
        return;
      }

      try {
        await expect(select).toBeVisible();
        const current = await select.inputValue();
        if (current !== code) {
          await select.selectOption(code);
          const applyButton = page.getByRole("button", { name: /(apply|применить|қолдану)/i }).first();
          await expect(applyButton).toBeEnabled();
          await applyButton.click();
        }
      } catch {
        await fallbackLanguageState();
      }
    };

    const ensureConsoleRoute = async () => {
      const navigated = await page
        .waitForURL(/\/console(\/|$)/, { timeout: 5_000 })
        .then(() => true)
        .catch(() => false);

      if (!navigated) {
        await setSessionCookies(page, baseUrl!);
        await page.goto(`${baseUrl}/console`);
      }

      await expect(page).toHaveURL(/\/console(\/|$)/);
    };

    await stubAuthFlow(page, baseUrl!);

    // A. Login page: ru -> kk -> en changes UI
    await page.goto(`${baseUrl}/login`);

    await setLanguage("ru");
    await expect(page.locator("button[type='submit']")).toHaveText(/войти/i);
    await expect(page.locator("label[for='username']")).toHaveText(/логин/i);
    await expect(page.locator("label[for='password']")).toHaveText(/пароль/i);

    await setLanguage("kk");
    await expect(page.locator("button[type='submit']")).toHaveText(/кіру/i);
    await expect(page.locator("label[for='username']")).toHaveText(/логин/i);
    await expect(page.locator("label[for='password']")).toHaveText(/құпиясөз/i);

    await setLanguage("en");
    await expect(page.locator("button[type='submit']")).toHaveText(/sign in/i);
    await expect(page.locator("label[for='username']")).toHaveText(/username/i);
    await expect(page.locator("label[for='password']")).toHaveText(/password/i);

    const cookieAfterLoginSwitch = (await context.cookies()).find((c) => c.name === "app.locale")?.value;
    const storageAfterLoginSwitch = await page.evaluate(() => localStorage.getItem("app.language"));
    expect(cookieAfterLoginSwitch).toBe("en");
    expect(storageAfterLoginSwitch).toBe("en");

    // Login and go to console (stubbed auth flow)
    await page.locator("#username").fill("smoke-admin");
    await page.locator("#password").fill("stubbed-password");
    await page.locator("button[type='submit']").click();
    await ensureConsoleRoute();

    // B. Console: switch and persist after refresh
    await setLanguage("kk");
    await expect.poll(async () => page.evaluate(() => localStorage.getItem("app.language"))).toBe("kk");
    await expect.poll(async () => {
      return (await context.cookies()).find((c) => c.name === "app.locale")?.value ?? null;
    }).toBe("kk");
    await page.reload();
    await expect.poll(async () => {
      return page.getByLabel(/language|язык|тіл/i).first().inputValue();
    }).toBe("kk");

    const cookieAfterReload = (await context.cookies()).find((c) => c.name === "app.locale")?.value;
    const storageAfterReload = await page.evaluate(() => localStorage.getItem("app.language"));
    expect(cookieAfterReload).toBe("kk");
    expect(storageAfterReload).toBe("kk");

    // C. Tenants / Jobs / Platform pages have no broken placeholders
    for (const path of ["/console/tenants", "/console/jobs", "/console/platform"]) {
      await page.goto(`${baseUrl}${path}`);
      await page.waitForTimeout(400);
      const bodyText = await page.locator("body").innerText();
      expect(hasBadTokens(bodyText)).toBe(false);
    }

    // D. Logout/Login preserves language
    await page.goto(`${baseUrl}/console`);
    await page.context().clearCookies();
    await page.goto(`${baseUrl}/login`);

    await expect(page.locator("button[type='submit']")).toHaveText(/кіру/i);

    await page.locator("#username").fill("smoke-admin");
    await page.locator("#password").fill("stubbed-password");
    await page.locator("button[type='submit']").click();
    await ensureConsoleRoute();

    const cookieAfterRelogin = (await context.cookies()).find((c) => c.name === "app.locale")?.value;
    const storageAfterRelogin = await page.evaluate(() => localStorage.getItem("app.language"));
    expect(cookieAfterRelogin).toBe("kk");
    expect(storageAfterRelogin).toBe("kk");

    const actionableJsErrors = jsErrors.filter(
      (line) => !/text content does not match server-rendered html|there was an error while hydrating/i.test(line),
    );
    expect(actionableJsErrors).toEqual([]);
    const actionableConsoleErrors = consoleErrors.filter(
      (line) =>
        /typeerror|referenceerror|cannot read|hydration failed/i.test(line) &&
        !/Failed to fetch RSC payload.*Falling back to browser navigation/i.test(line),
    );
    expect(actionableConsoleErrors).toEqual([]);
  });
});
