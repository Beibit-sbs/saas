import { expect, test } from "@playwright/test";

test.describe("i18n runtime smoke", () => {
  test("login/console/platform locale flow is stable", async ({ page, context }) => {
    const baseUrl = process.env.E2E_BASE_URL;
    expect(baseUrl).toBeTruthy();
    const creds = {
      username: process.env.E2E_SMOKE_USERNAME || "smoke-admin",
      password: process.env.E2E_SMOKE_PASSWORD || "change_me_smoke_password",
    };
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
      const select = page.getByLabel(/language|язык|тіл/i).first();
      await expect(select).toBeVisible();
      const current = await select.inputValue();
      if (current !== code) {
        await select.selectOption(code);
        const applyButton = page.getByRole("button", { name: /(apply|применить|қолдану)/i }).first();
        await expect(applyButton).toBeEnabled();
        await applyButton.click();
      }
    };

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

    // Login and go to console
    await page.locator("#username").fill(creds.username);
    await page.locator("#password").fill(creds.password);
    await page.locator("button[type='submit']").click();
    await page.waitForURL(/\/console(\/|$)/);

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
    await page.getByRole("button", { name: /(sign out|выйти|шығу|logout)/i }).first().click();
    await page.waitForURL(/\/login/);

    await expect(page.locator("button[type='submit']")).toHaveText(/кіру/i);

    await page.locator("#username").fill(creds.username);
    await page.locator("#password").fill(creds.password);
    await page.locator("button[type='submit']").click();
    await page.waitForURL(/\/console(\/|$)/);

    const cookieAfterRelogin = (await context.cookies()).find((c) => c.name === "app.locale")?.value;
    const storageAfterRelogin = await page.evaluate(() => localStorage.getItem("app.language"));
    expect(cookieAfterRelogin).toBe("kk");
    expect(storageAfterRelogin).toBe("kk");

    const actionableJsErrors = jsErrors.filter(
      (line) => !/text content does not match server-rendered html|there was an error while hydrating/i.test(line),
    );
    expect(actionableJsErrors).toEqual([]);
    expect(consoleErrors.filter((line) => /typeerror|referenceerror|cannot read|hydration failed/i.test(line))).toEqual([]);
  });
});
