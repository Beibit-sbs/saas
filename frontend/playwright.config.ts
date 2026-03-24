import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright E2E configuration.
 * Smoke tests only – runs against a locally started dev server.
 *
 * To run:
 *   npx playwright test --project=chromium
 *
 * Requires:
 *   API_BASE_URL env var (defaults to http://localhost:8000)
 *   Frontend served at http://localhost:3000 (started by webServer below)
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: process.env.CI ? "github" : "list",

  use: {
    baseURL: "http://localhost:3000",
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

  // Uncomment to auto-start the dev server before tests:
  // webServer: {
  //   command: "npm run dev",
  //   url: "http://localhost:3000",
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 60_000,
  // },
});
