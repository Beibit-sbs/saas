import { defineConfig, devices } from "@playwright/test";

const e2eBaseUrl = process.env.E2E_BASE_URL?.trim();

if (!e2eBaseUrl) {
  throw new Error("E2E_BASE_URL is required");
}

/**
 * Playwright E2E configuration.
 * Smoke tests only – runs against the nginx edge inside Docker Compose.
 *
 * To run:
 *   docker compose --env-file .env run --rm frontend-tests npm run test:e2e
 *
 * Requires:
 *   E2E_BASE_URL env var set to the nginx edge URL
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: process.env.CI ? "github" : "list",

  use: {
    baseURL: e2eBaseUrl,
    ignoreHTTPSErrors: true,
    // Persist httpOnly cookies between requests in the same test
    // by using a storageState file for authenticated tests.
    headless: true,
    viewport: { width: 1280, height: 800 },
    actionTimeout: 10_000,
    navigationTimeout: 15_000,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  webServer: undefined,
});
